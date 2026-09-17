import os
import sys
import json
import urllib.request

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

GOOGLE_AI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

def get_gemini_embedding(text):
    if not GOOGLE_AI_API_KEY:
        print("Warning: GOOGLE_AI_API_KEY not found in env.")
        return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={GOOGLE_AI_API_KEY}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    headers = {"Content-Type": "application/json"}
    try:
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=context) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            return res_data.get('embedding', {}).get('values', [])
    except Exception as e:
        print(f"❌ Gemini Embedding API call failed: {e}")
        return []

def main():
    print("🚀 Seeding RAG Knowledge Base...")
    if not GOOGLE_AI_API_KEY:
        print("Error: GOOGLE_AI_API_KEY is empty. Check your backend/.env file.")
        return
        
    # Clear existing RAG database for a clean seed
    ClinicalKnowledgeSegment.objects.all().delete()
    print("🧹 Cleared existing ClinicalKnowledgeSegment records.")
        
    # 1. Load key_39_file1.json QA pairs
    from django.conf import settings
    tspi_data_dir = getattr(settings, 'TSPI_DATA_DIR', None)
    if tspi_data_dir and os.path.exists(tspi_data_dir / 'last_dta'):
        data_base = tspi_data_dir / 'last_dta'
    else:
        data_base = settings.BASE_DIR.parent / 'data' / 'last_dta'
    path1 = str(data_base / 'key_39_file1.json')
    qa_count = 0
    if os.path.exists(path1):
        with open(path1, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        t_pairs = raw_data.get("data", {}).get("training_pairs", [])
        print(f"Found {len(t_pairs)} QA pairs in key_39_file1.json")
        for tp in t_pairs:
            q = tp.get("question")
            a = tp.get("answer")
            full_text = f"คำถาม: {q}\nคำตอบ: {a}"
            title = q[:100]
            
            # Check if exists
            if not ClinicalKnowledgeSegment.objects.filter(content=full_text).exists():
                emb = get_gemini_embedding(full_text)
                ClinicalKnowledgeSegment.objects.create(
                    title=title,
                    content=full_text,
                    source="key_39_file1_qa",
                    embedding=emb
                )
                qa_count += 1
                if qa_count % 10 == 0:
                    print(f"  Ingested {qa_count} QA pairs...")
    
    # 2. Load TSPI Modules Master Data QA pairs
    path2 = str(data_base / 'TSPI Modules Master Data + Training_Pairs.json')
    if os.path.exists(path2):
        with open(path2, 'r', encoding='utf-8') as f:
            data = json.load(f)
        t_pairs = data.get("training_pairs", [])
        print(f"Found {len(t_pairs)} QA pairs in TSPI Modules Master Data")
        for tp in t_pairs:
            q = tp.get("question")
            a = tp.get("answer")
            full_text = f"คำถาม: {q}\nคำตอบ: {a}"
            title = q[:100]
            
            if not ClinicalKnowledgeSegment.objects.filter(content=full_text).exists():
                emb = get_gemini_embedding(full_text)
                ClinicalKnowledgeSegment.objects.create(
                    title=title,
                    content=full_text,
                    source="tspi_modules_qa",
                    embedding=emb
                )
                qa_count += 1
                if qa_count % 10 == 0:
                    print(f"  Ingested {qa_count} QA pairs...")

    # 3. Load Foundational Medicine.json paragraphs (actually plain Markdown text)
    path3 = str(data_base / 'Foundational Medicine.json')
    fm_count = 0
    if os.path.exists(path3):
        with open(path3, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Split text by double newlines to get paragraphs of reasonable size
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        print(f"Found {len(paragraphs)} text paragraphs in Foundational Medicine.json")
        for idx, para in enumerate(paragraphs):
            if len(para) < 30: # Skip very short headers or lines
                continue
                
            title = f"Foundational Medicine - Section {idx+1}"
            if not ClinicalKnowledgeSegment.objects.filter(content=para).exists():
                emb = get_gemini_embedding(para)
                ClinicalKnowledgeSegment.objects.create(
                    title=title,
                    content=para,
                    source="foundational_medicine_essay",
                    embedding=emb
                )
                fm_count += 1
                if fm_count % 10 == 0:
                    print(f"  Ingested {fm_count} Foundational Medicine segments...")

    print(f"🎉 RAG Ingestion Complete! Successfully seeded {qa_count} QA pairs and {fm_count} Foundational Medicine segments.")

if __name__ == '__main__':
    main()
