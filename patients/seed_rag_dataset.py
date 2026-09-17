import os
import sys
import json
import urllib.request
import ssl
import django

# Setup django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def load_env():
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        k, v = parts[0].strip(), parts[1].strip()
                        os.environ[k] = v

load_env()
django.setup()

from patients.models import ClinicalKnowledgeSegment

GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")

def get_gemini_embeddings_batch(texts, model="models/gemini-embedding-001"):
    """
    เรียกใช้ Gemini Batch Embedding API เพื่อดึงเวกเตอร์ของลิสต์ข้อความ (สูงสุด 100 ข้อความต่อครั้ง)
    """
    if not GOOGLE_AI_API_KEY:
        print("❌ ข้อผิดพลาด: ไม่พบ GOOGLE_AI_API_KEY ใน env")
        return []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={GOOGLE_AI_API_KEY}"
    
    requests_payload = []
    for text in texts:
        requests_payload.append({
            "model": model,
            "content": {"parts": [{"text": text}]}
        })
        
    payload = {"requests": requests_payload}
    headers = {"Content-Type": "application/json"}
    
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=context) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            embeddings_list = res_data.get('embeddings', [])
            return [emb.get('values', []) for emb in embeddings_list]
    except Exception as e:
        print(f"❌ Gemini Batch Embedding API call failed: {e}")
        return []

def main():
    print("🚀 เริ่มต้นระบบนำเข้าชุดข้อมูลเวกเตอร์ RAG (Seeding RAG Database)...")
    if not GOOGLE_AI_API_KEY:
        print("❌ ข้อผิดพลาด: GOOGLE_AI_API_KEY เป็นค่าว่าง กรุณาตรวจสอบไฟล์ backend/.env")
        return

    # ล้างตารางเดิมเพื่อให้ข้อมูลไม่ซ้ำซ้อน
    print("🧹 กำลังล้างข้อมูลตาราง ClinicalKnowledgeSegment เดิมทั้งหมด...")
    ClinicalKnowledgeSegment.objects.all().delete()
    print("✅ ล้างข้อมูลเรียบร้อย")

    # 1. โหลดข้อมูลจาก dataset.jsonl (10,510 แถว)
    from django.conf import settings
    tspi_data_dir = getattr(settings, 'TSPI_DATA_DIR', None)
    if tspi_data_dir and os.path.exists(tspi_data_dir / 'last_dta'):
        data_base = tspi_data_dir / 'last_dta'
    else:
        data_base = settings.BASE_DIR.parent / 'data' / 'last_dta'
    dataset_path = str(data_base / 'dataset.jsonl')
    qa_items = []
    
    if os.path.exists(dataset_path):
        print(f"📦 กำลังอ่านไฟล์ชุดข้อมูล: {dataset_path}")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    instruction = item.get("instruction", "").strip()
                    input_val = item.get("input", "").strip()
                    output = item.get("output", "").strip()
                    
                    if not instruction and not output:
                        continue
                        
                    # ประกอบข้อความ Context สำหรับทำ Embedding
                    text_parts = [f"คำถาม/คำชี้แจง: {instruction}"]
                    if input_val:
                        text_parts.append(f"ข้อมูลเพิ่มเติม: {input_val}")
                    text_parts.append(f"คำตอบ/คำอธิบาย: {output}")
                    
                    full_text = "\n".join(text_parts)
                    title = instruction[:150]
                    
                    qa_items.append({
                        "title": title,
                        "content": full_text,
                        "source": "dataset_qa"
                    })
                except Exception as e:
                    print(f"⚠️ บรรทัดที่ {idx+1} แปลง JSON ไม่สำเร็จ: {e}")
        print(f"✅ โหลด QA pairs สำเร็จจำนวน {len(qa_items)} รายการ")
    else:
        print(f"❌ ไม่พบไฟล์ชุดข้อมูล: {dataset_path}")

    # 2. โหลดข้อมูลจาก Foundational Medicine.json
    fm_path = str(data_base / 'Foundational Medicine.json')
    fm_items = []
    
    if os.path.exists(fm_path):
        print(f"📦 กำลังอ่านไฟล์เอกสารเวชศาสตร์รากฐาน: {fm_path}")
        with open(fm_path, 'r', encoding='utf-8') as f:
            # เป็นข้อความ Markdown ยาว
            text_content = f.read()
            
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        for idx, para in enumerate(paragraphs):
            if len(para) < 20: # ข้ามบรรทัดที่สั้นเกินไป
                continue
            
            title = f"Foundational Medicine - Section {idx+1}"
            fm_items.append({
                "title": title,
                "content": para,
                "source": "foundational_medicine"
            })
        print(f"✅ โหลดหัวข้อเวชศาสตร์รากฐานสำเร็จจำนวน {len(fm_items)} รายการ")
    else:
        print(f"❌ ไม่พบไฟล์เวชศาสตร์รากฐาน: {fm_path}")

    # รวมรายการทั้งหมดที่จะทำ embedding
    all_items = qa_items + fm_items
    total_count = len(all_items)
    print(f"📊 จำนวนข้อมูลทั้งหมดที่ต้องทำ Embedding: {total_count} รายการ")

    # เริ่มขั้นตอนการทำ Batch Embedding (ทีละ 100 รายการ)
    batch_size = 100
    db_records = []
    success_count = 0
    
    print("\n🔮 กำลังยิงทำ Batch Embedding กับ Gemini API...")
    
    for i in range(0, total_count, batch_size):
        batch = all_items[i:i + batch_size]
        texts_to_embed = [item["content"] for item in batch]
        
        # ดึง embeddings แบบ batch
        embeddings = get_gemini_embeddings_batch(texts_to_embed)
        
        if not embeddings or len(embeddings) != len(batch):
            print(f"⚠️ เกิดข้อผิดพลาดในการทำ Embedding ช่วงข้อมูลลำดับ {i} ถึง {i+len(batch)} (กำลังลองยิงรายตัวสำหรับ batch นี้)")
            # Fallback ยิงทีละตัวสำหรับ batch นี้หากเกิดปัญหา
            for item in batch:
                try:
                    # ฟังก์ชันยิงเดี่ยวแบบง่าย
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={GOOGLE_AI_API_KEY}"
                    payload = {
                        "model": "models/gemini-embedding-001",
                        "content": {"parts": [{"text": item["content"]}]}
                    }
                    headers = {"Content-Type": "application/json"}
                    context = ssl._create_unverified_context()
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                    with urllib.request.urlopen(req, context=context) as res:
                        res_data = json.loads(res.read().decode('utf-8'))
                        emb_val = res_data.get('embedding', {}).get('values', [])
                        if emb_val:
                            db_records.append(ClinicalKnowledgeSegment(
                                title=item["title"],
                                content=item["content"],
                                source=item["source"],
                                embedding=emb_val
                            ))
                            success_count += 1
                except Exception as ex:
                    print(f"❌ ทำ Embedding รายการ '{item['title'][:30]}' ล้มเหลว: {ex}")
        else:
            # นำ embeddings ใส่กลับเข้าไปในรายการ
            for idx, emb_val in enumerate(embeddings):
                item = batch[idx]
                db_records.append(ClinicalKnowledgeSegment(
                    title=item["title"],
                    content=item["content"],
                    source=item["source"],
                    embedding=emb_val
                ))
            success_count += len(batch)
            
        print(f"   Processed {success_count}/{total_count} items ({(success_count/total_count)*100:.1f}%)")

    # บันทึกข้อมูลลงฐานข้อมูลแบบ Bulk Create เพื่อความรวดเร็ว
    if db_records:
        print(f"\n💾 กำลังบันทึกข้อมูลเข้า PostgreSQL แบบ Bulk (จำนวน {len(db_records)} records)...")
        # แบ่งการ Bulk Create ทีละ 1000 เพื่อไม่ให้คำสั่ง SQL ยาวเกินไป
        records_batch_size = 1000
        for i in range(0, len(db_records), records_batch_size):
            chunk = db_records[i:i + records_batch_size]
            ClinicalKnowledgeSegment.objects.bulk_create(chunk)
        print("🎉 บันทึกข้อมูลทั้งหมดลง PostgreSQL สำเร็จเรียบร้อยแล้ว!")
        print(f"   จำนวนนำเข้าสำเร็จทั้งหมด: {ClinicalKnowledgeSegment.objects.count()} รายการ")
    else:
        print("❌ ไม่พบข้อมูลสำเร็จที่จะบันทึก")

if __name__ == '__main__':
    main()
