# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)

# Dictionary containing professional Thai clinical impression segments per domain and severity
CLINICAL_IMPRESSIONS = {
    "Domain 1 — Immune–Infection Governance": {
        "severe": "พบภาวะอักเสบในระบบชีวภาพระดับรุนแรง (Severe Systemic Inflammatory Load) ร่วมกับการตึงตัวของกลไกต่อต้านเชื้อก่อโรค สมควรควบคุมกระบวนการอักเสบแดงร้อนอย่างเร่งด่วน",
        "moderate": "พบการทำงานของระบบภูมิคุ้มกันและความร้อนในเซลล์ตึงตัวปานกลาง (Moderate Inflammation) ควรระบายพิษความร้อนสะสมและปรับสมดุลภูมิคุ้มกัน",
        "healthy": "ระบบควบคุมการอักเสบและภูมิคุ้มกันพื้นฐานอยู่ในเกณฑ์สมบูรณ์ปกติ (Healthy/Stable Immune Control)"
    },
    "Domain 2 — Metabolic–Energy Core": {
        "severe": "ระบบควบคุมพลังงานและเผาผลาญระดับเซลล์บิดเบือนรุนแรง (Severe Metabolic Dysfunction) บ่งชี้สภาวะดื้อต่ออินซูลินระดับเซลล์ และความล้าสะสมของไมโตคอนเดรียในการสร้างพลังงาน (ATP)",
        "moderate": "ประสิทธิภาพการเผาผลาญอาหารและระดับน้ำตาลตึงตัวปานกลาง (Moderate Glycemic Imbalance) ควรระมัดระวังการสะสมคาร์โบไฮเดรตและสารเร่งแก่ระดับเนื้อเยื่อ (AGEs)",
        "healthy": "กระบวนการเผาผลาญอาหารและควบคุมระดับน้ำตาลระดับเซลล์มีความเสถียรดี (Balanced Metabolic Economy)"
    },
    "Domain 3 — Genomic–Longevity Programming": {
        "severe": "พบความเสียหายสะสมในระดับดีเอ็นเอและการทำงานของรหัสพันธุกรรม (Genomic Instability) มีแนวโน้มการแก่ตัวของเซลล์ระดับสูง (Cellular Senescence)",
        "moderate": "มีสัญญาณบ่งชี้ความเสื่อมถอยของการปกป้องดีเอ็นเอและรหัสเหนือพันธุกรรม (Epigenetic Burden)",
        "healthy": "เสถียรภาพของรหัสพันธุกรรมและการแบ่งตัวของเซลล์อยู่ในเกณฑ์ปกติ (Genomic Stability)"
    },
    "Domain 4 — Detox–Digestive–Gut Ecosystem": {
        "severe": "พบความเสียหายรุนแรงต่อเยื่อบุผนังลำไส้และระบบดีท็อกซ์ (Severe Detoxification & Gut Barrier Disruption) ร่วมกับการสะสมจุลชีพก่อโรคหรือไบโอฟิล์มเหนี่ยวนำสารพิษเข้าสู่ระบบไหลเวียนโลหิต",
        "moderate": "ประสิทธิภาพการย่อยและการล้างพิษขั้นที่ 1-2 ตึงตัวปานกลาง (Moderate Gut/Detox Stress) ร่วมกับความไม่สมดุลของประชากรจุลชีพที่เป็นมิตรในลำไส้",
        "healthy": "การขจัดสารพิษระดับเซลล์และระบบนิเวศน์ทางเดินอาหารทำงานราบรื่นปกติ (Healthy Detox & Gut Ecosystem)"
    },
    "Domain 5 — Vascular–Circulation–Stroke Prevention": {
        "severe": "มีความตึงตัวของแรงดันเลือดและผนังหลอดเลือดด้านในระดับสูง (Severe Endothelial & Microvascular Dysfunction) บ่งชี้ความหนืดของโลหิตและการไหลเวียนระดับฝอยชะงักงัน",
        "moderate": "ประสิทธิภาพความยืดหยุ่นของผนังหลอดเลือดและหัวใจแสดงความล้าปานกลาง (Mild Microvascular Flow Stasis) ควรจำกัดอาหารไขมันดัดแปลง",
        "healthy": "อัตราการไหลเวียนโลหิตของหลอดเลือดใหญ่และหลอดเลือดฝอยเป็นปกติ (Optimal Hemodynamics)"
    },
    "Domain 6 — Repair–Fibrosis–Regeneration": {
        "severe": "กระบวนการซ่อมแซมและสร้างเซลล์ใหม่ชะงักงันรุนแรง (Severe Repair-Regeneration Deficit) เนื้อเยื่อรอบข้างเสี่ยงต่อภาวะพังผืดเรื้อรังและการสะสมคราบไกลเคชั่น (AGEs)",
        "moderate": "พบสัญญาณการฟื้นตัวของเนื้อเยื่อช้ากว่าปกติ (Impaired Tissue Healing Rate) หรือพบการก่อตัวของพังผืดปานกลาง",
        "healthy": "การซ่อมแซมแผลและการสร้างเนื้อเยื่อใหม่มีความเสถียรปกติ (Optimal Healing & Regeneration)"
    },
    "Domain 7 — Musculoskeletal & Structural Integrity": {
        "severe": "พบความอ่อนแอและการเสื่อมสภาพของมวลกล้ามเนื้อและเนื้อเยื่อเกี่ยวพันระดับสูง (Severe Musculoskeletal Degeneration)",
        "moderate": "ความยืดหยุ่นของข้อต่อและโครงสร้างเนื้อเยื่อเกี่ยวพันตึงล้าสะสม (Mild Connective Tissue Laxity)",
        "healthy": "ความแข็งแรงของกล้ามเนื้อ โครงกระดูก และเนื้อเยื่อเกี่ยวพันเป็นปกติ (Balanced Structural Integrity)"
    },
    "Domain 8 — Endocrine Network": {
        "severe": "พบความแปรปรวนอย่างวิกฤตในแกนควบคุมฮอร์โมน (Thyroid-Adrenal-Sex Hormone Axis) ส่งผลลบโดยตรงต่อความทนทานและการใช้พลังงานของร่างกาย",
        "moderate": "มีสัญญาณความไม่สมดุลของฮอร์โมนต่อมไร้ท่อและแกนหมวกไตปานกลาง (Mild Hormone Dysregulation)",
        "healthy": "ระบบฮอร์โมนและจังหวะของแกนไร้ท่ออยู่ในเกณฑ์สมบูรณ์ดี (Balanced Endocrine Rhythm)"
    },
    "Domain 9 — Neuro–Sleep–Stress": {
        "severe": "ตรวจพบความล้าขั้นวิกฤตในวิถีสมดุลสารสื่อประสาทและการนอนหลับ (Severe Neuroendocrine Fatigue) ซึ่งมักสอดคล้องกับความเครียดลึกระดับเซลล์และวงจรนอนหลับแปรปรวนรุนแรง",
        "moderate": "ระดับสารสื่อประสาทและระบบนอนหลับแสดงสัญญาณตึงเครียดล้าสะสม (Adrenal & Sleep Burnout Tendency) ส่งผลต่อคุณภาพการนอนเพื่อการซ่อมแซมร่างกาย",
        "healthy": "วงจร Circadian และสมดุลสารเคมีสมองประสาททำงานได้อย่างมีประสิทธิภาพสูงสุด (Restorative Sleep & Nervous Health)"
    },
    "Domain 10 — Organ Axis + Oncology": {
        "severe": "ตรวจพบความล้าและภาระตึงเครียดระดับสูงของอวัยวะภายในหลัก (Severe Visceral Organ Burden) และมีความเสี่ยงต่อกลไกแบ่งเซลล์ผิดปกติ",
        "moderate": "พบการทำงานของอวัยวะสำคัญแสดงสัญญาณตึงเครียดปานกลาง (Mild Visceral Stress) หรือเริ่มมีความตึงตัวของรอยโรค",
        "healthy": "ประสิทธิภาพการทำงานและความทนทานของอวัยวะภายในอยู่ในเกณฑ์สมบูรณ์ (Healthy Organ Resilience)"
    },
    "Domain 11 — Regeneration & Repair System": {
        "severe": "ประสิทธิภาพความทนทานและการฟื้นตัวฟื้นฟูหลังความเครียดหรือการบาดเจ็บระดับเซลล์ล้มเหลวรุนแรง (Severe Systemic Regeneration Failure)",
        "moderate": "ความสามารถในการซ่อมสร้างตัวเองช้าลง (Impaired Autologous Repair Potential)",
        "healthy": "ร่างกายมีกำลังสำรองในการซ่อมสร้างตัวเองได้อย่างมีประสิทธิภาพสูงสุด (Robust Regenerative Potential)"
    },
    "Domain 12 — Proteostasis & Cellular Integrity": {
        "severe": "พบสภาวะเสี่ยงต่อการควบคุมคุณภาพโปรตีนและกลไกเซลล์ทำลายตนเองล้มเหลว (Severe Proteotoxicity & Oncologic Fate Risk) ควรได้รับการฟื้นฟูกลไกขจัดเซลล์แก่ชราเร่งด่วน",
        "moderate": "การตอบสนองต่อโปรตีนเสียและการกวาดขยะระดับเซลล์ (Autophagy/Lysosome System) ตึงตัวปานกลาง",
        "healthy": "ระบบป้องกันการก่อตัวของกลุ่มเซลล์แปลกปลอมและการกวาดขยะโปรตีนเสียทำงานปกติ (Stable Cellular Integrity)"
    }
}

# Network Coupling Mechanisms (Coupled pathways)
COUPLING_MECHANISMS = [
    {
        "keys": ["Domain 2 — Metabolic–Energy Core", "Domain 1 — Immune–Infection Governance"],
        "text": "ภาวะเมแทบอลิซึมระดับเซลล์ที่ล้าสะสมเหนี่ยวนำให้เกิดกระบวนการอักเสบเรื้อรังระดับเซลล์ (Metaflammation) ส่งผลกระตุ้นทางเดินอักเสบข้ามระบบ รบกวนวิถีการสังเคราะห์พลังงานของไมโตคอนเดรีย"
    },
    {
        "keys": ["Domain 1 — Immune–Infection Governance", "Domain 5 — Vascular–Circulation–Stroke Prevention"],
        "text": "การสะสมสารสื่ออักเสบในกระแสโลหิตกระตุ้นให้เกิดการอักเสบที่ผนังหลอดเลือดส่วนปลาย (Endothelial Inflammation) ก่อให้เกิดแรงต้านทานการไหลเวียนและจำกัดการลำเลียงออกซิเจนสู่เนื้อเยื่อ"
    },
    {
        "keys": ["Domain 4 — Detox–Digestive–Gut Ecosystem", "Domain 9 — Neuro–Sleep–Stress"],
        "text": "ความเสียหายของเยื่อบุลำไส้ร่วมกับความแปรปรวนของจุลชีพส่งสัญญาณรบกวนแกนสมองและลำไส้ (Gut-Brain Axis Disruption) ส่งผลลบโดยตรงต่อการสังเคราะห์เซโรโทนินและเมลาโทนินเพื่อฟื้นฟูระบบประสาท"
    },
    {
        "keys": ["Domain 2 — Metabolic–Energy Core", "Domain 4 — Detox–Digestive–Gut Ecosystem"],
        "text": "การมีปริมาณจุลชีพก่อโรคสะสมในทางเดินอาหารเหนี่ยวนำให้ผนังลำไส้รั่วซึม เกิดภาวะเมแทบอลิกเอนโดท็อกซีเมีย (Metabolic Endotoxemia) ซึ่งขัดขวางการตอบสนองต่ออินซูลินและรบกวนวิถีการสลายกรดไขมัน"
    }
]

def generate_local_precision_report(patient, tspi_result, simulated_labs):
    """
    Generates a deterministic Systems Biology Medical Report purely using rule-based Python logic.
    Follows formatting rules: [Clinical Impression], [Mechanistic Pathophysiology Pathways], [Biomarker Burden Interlinkage]
    """
    # Extract calculated scores and priorities
    nss = tspi_result.get("nss")
    severity_label = tspi_result.get("severity_label", "Level 1: Functional Imbalance")
    system_priorities = tspi_result.get("system_priorities", [])
    recommended_modules = tspi_result.get("recommended_modules", [])
    dosing_rule = tspi_result.get("dosing_rule", "2 แคปซูล × 2 ครั้งต่อวัน")
    ks_dosing = tspi_result.get("ks_dosing", "ก่อนนอน 2 แคปซูล")

    # 1. COMPILE CLINICAL IMPRESSION
    impression_lines = []
    impression_lines.append(f"คนไข้: {patient.first_name} {patient.last_name} (HN: {patient.hn or 'N/A'})")
    nss_str = f"{nss:.1f}/100" if nss is not None else "ยังไม่ได้ประเมิน (Not Assessed)"
    impression_lines.append(f"ผลประเมินดัชนีความเสี่ยงรวมชีววิทยาเครือข่าย (NSS): {nss_str} - สภาวะสรีรวิทยาอยู่ในเกณฑ์: {severity_label}")
    impression_lines.append("\nการวิเคราะห์ระบบชีวภาพรายโดเมนหลัก:")
    
    # Check top domains and add templates
    added_domains = set()
    for item in system_priorities[:3]:
        domain = item.get("system")
        score = item.get("score")
        if score is None:
            impression_lines.append(f"• [ระบบ {domain}]: ยังไม่มีข้อมูลตรวจวัดประเมิน (Not Assessed)")
            continue
        added_domains.add(domain)
        
        severity_key = "severe" if score > 75 else "moderate" if score > 55 else "healthy"
        domain_template = CLINICAL_IMPRESSIONS.get(domain, {}).get(severity_key)
        
        if domain_template:
            impression_lines.append(f"• [ระบบ {domain} - คะแนนรุนแรง {score:.1f}%]: {domain_template}")
        else:
            status = "มีความรุนแรงสูง" if score > 75 else "มีความตึงเครียดสะสมปานกลาง" if score > 55 else "ปกติมีความเสถียรดี"
            impression_lines.append(f"• [ระบบ {domain} - คะแนนรุนแรง {score:.1f}%]: อยู่ในเกณฑ์{status} ตามเกณฑ์วัด 39 แกนมาตรฐาน")
            
    clinical_impression_text = "\n".join(impression_lines)

    # 2. COMPILE PATHOPHYSIOLOGY PATHWAYS (Coupling logic)
    pathway_lines = []
    coupling_found = False
    for coupling in COUPLING_MECHANISMS:
        keys = coupling["keys"]
        elevated = []
        for k in keys:
            domain_score = next((x.get("score") for x in system_priorities if x.get("system") == k), None)
            if domain_score is not None and domain_score > 55:
                elevated.append(k)
        if len(elevated) == len(keys):
            pathway_lines.append(f"🔗 [ทางเดิน {keys[0]} ↔️ {keys[1]}]: {coupling['text']}")
            coupling_found = True
            
    if not coupling_found:
        pathway_lines.append("🔬 การวิเคราะห์กลไกเครือข่ายไม่พบคู่การจับคู่ความผิดปกติแบบรบกวนรุนแรงข้ามวิถี (Network Coupling Normal) มีสัญญาณขัดขวางสมดุลสรีรวิทยาในลักษณะโดดเดี่ยวเฉพาะแกนเท่านั้น")

    pathway_lines.append(f"\n💡 [กลไกการสั่งใช้ยาบำบัดพิเศษ]: \n- ขนาดปริมาณการใช้สารอาหารตามระดับ NSS: {dosing_rule}\n- การปรับขนาดระบบขับถ่ายและการระบายความร้อนทางลำไส้ (KS): {ks_dosing}")
    pathway_text = "\n".join(pathway_lines)

    # 3. COMPILE BIOMARKER INTERLINKAGE
    db_labs = patient.labs if isinstance(patient.labs, dict) else {}
    labs = {}
    for key in ["fbs", "hba1c", "crp", "ldl", "alt", "ggt", "hb", "mcv", "hct"]:
        val = simulated_labs.get(key)
        if val in (None, ""):
            val = db_labs.get(key) or db_labs.get(key.upper())
        if val in (None, ""):
            if key == "fbs":
                val = db_labs.get("Fasting Glucose") or db_labs.get("fasting_glucose") or db_labs.get("FBS")
            elif key == "crp":
                val = db_labs.get("hsCRP") or db_labs.get("hscrp") or db_labs.get("CRP") or db_labs.get("Crp")
            elif key == "ldl":
                val = db_labs.get("LDL Cholesterol") or db_labs.get("cholesterol_ldl") or db_labs.get("LDL")
            elif key == "alt":
                val = db_labs.get("sgpt") or db_labs.get("SGPT") or db_labs.get("ALT")
            elif key == "ggt":
                val = db_labs.get("GGT")
            elif key == "hb":
                val = db_labs.get("HGB") or db_labs.get("Hb") or db_labs.get("Hemoglobin")
            elif key == "hct":
                val = db_labs.get("HCT") or db_labs.get("Hct") or db_labs.get("Hematocrit")
            elif key == "mcv":
                val = db_labs.get("MCV") or db_labs.get("Mcv")
        
        if val not in (None, ""):
            try:
                labs[key] = float(val)
            except ValueError:
                pass

    biomarker_lines = []
    
    # Process FBS
    fbs_val = labs.get("fbs")
    if fbs_val is not None:
        if fbs_val > 125:
            biomarker_lines.append(f"🩸 [FBS: {fbs_val:.1f} mg/dL]: บ่งชี้ภาวะน้ำตาลในเลือดเกินมาตรฐานระดับเบาหวานชัดเจน (Hyperglycemia) กระตุ้นการเกิดกระบวนการไกลเคชั่นสะสมสารเร่งเสื่อมระดับผนังเซลล์")
        elif fbs_val > 100:
            biomarker_lines.append(f"🩸 [FBS: {fbs_val:.1f} mg/dL]: อยู่ในเกณฑ์เสี่ยงก่อนเบาหวาน (Prediabetes) ร่างกายเริ่มหลั่งอินซูลินมากขึ้นเพื่อต้านทาน สัมพันธ์กับการอักเสบเรื้อรังระดับต่ำ")
        else:
            biomarker_lines.append(f"🩸 [FBS: {fbs_val:.1f} mg/dL]: ควบคุมน้ำตาลก่อนอาหารได้ดี (Normal Glycemia)")

    # Process HbA1c
    hba1c_val = labs.get("hba1c")
    if hba1c_val is not None:
        if hba1c_val > 6.5:
            biomarker_lines.append(f"🩸 [HbA1c: {hba1c_val:.1f}%]: ยืนยันสภาวะน้ำตาลเกาะเม็ดเลือดแดงสะสมสูงเฉียบพลัน ขัดขวางการลำเลียงออกซิเจนและการถ่ายเทประจุพลังงานในไมโตคอนเดรีย")
        elif hba1c_val > 5.7:
            biomarker_lines.append(f"🩸 [HbA1c: {hba1c_val:.1f}%]: อยู่ในกลุ่มเสี่ยงเผาผลาญคาร์โบไฮเดรตบกพร่องสะสม (Impaired Glycemia)")

    # Process Anemia
    hb_val = labs.get("hb")
    hct_val = labs.get("hct")
    mcv_val = labs.get("mcv")
    if hb_val is not None or hct_val is not None or mcv_val is not None:
        if (hb_val and hb_val < 12.0) or (hct_val and hct_val < 36.0) or (mcv_val and mcv_val < 80.0):
            h_str = f"Hb: {hb_val:.1f} g/dL " if hb_val else ""
            m_str = f"MCV: {mcv_val:.1f} fL " if mcv_val else ""
            biomarker_lines.append(f"🩸 [ภาวะโลหิตจางเม็ดเลือดแดงขนาดเล็ก - {h_str}{m_str}]: บ่งชี้ความผิดปกติของการสร้างฮีโมโกลบินและการสุกแก่ของเม็ดเลือดแดง (Impaired Hematopoiesis) จัดกลุ่มประเมินผลลัพธ์ภายใต้ Axis 26 และ Axis 1")

    # Process CRP
    crp_val = labs.get("crp")
    if crp_val is not None:
        if crp_val > 3.0:
            biomarker_lines.append(f"🛡️ [hs-CRP: {crp_val:.1f} mg/L]: อัตราการอักเสบเฉียบพลันระดับวิกฤต บ่งบอกสภาวะเสี่ยงต่อระบบหัวใจและเยื่อบุผิวผนังหลอดเลือดแดงถูกกระตุ้นการทำลาย")
        elif crp_val >= 1.0:
            biomarker_lines.append(f"🛡️ [hs-CRP: {crp_val:.1f} mg/L]: พบสัญญาณการอักเสบแฝงระดับต่ำอย่างต่อเนื่อง (Subclinical Chronic Inflammation) เหนี่ยวนำโดยเซลล์ภูมิคุ้มกันล้า")

    # Process Liver Enzymatic Stress (ALT & GGT)
    alt_val = labs.get("alt")
    ggt_val = labs.get("ggt")
    if alt_val is not None or ggt_val is not None:
        a_val = alt_val if alt_val is not None else 30
        g_val = ggt_val if ggt_val is not None else 35
        if a_val > 50 or g_val > 60:
            biomarker_lines.append(f"🧪 [เอนไซม์ตับ ALT: {a_val:.1f} U/L / GGT: {g_val:.1f} U/L]: ตรวจพบความเครียดสะสมทางชีวเคมีของตับ (Hepatic Cellular Stress) และการล้างพิษขั้นที่ 1-2 (Biotransformation Economy) เริ่มลดประสิทธิภาพลง")

    # Process LDL Cholesterol
    ldl_val = labs.get("ldl")
    if ldl_val is not None:
        if ldl_val > 160:
            biomarker_lines.append(f"📊 [LDL: {ldl_val:.1f} mg/dL]: ปริมาณไลโปโปรตีนนำส่งไขมันสูงผิดปกติ เสี่ยงต่อการเกิดออกซิไดซ์ไลโปโปรตีน (Oxidized LDL) เกาะผนังหลอดเลือดฝอย")
        elif ldl_val > 130:
            biomarker_lines.append(f"📊 [LDL: {ldl_val:.1f} mg/dL]: อยู่ในระดับสูงระดับปานกลาง ควรควบคุมประเภทไขมันพืชดัดแปลงทางอุตสาหกรรม")

    # Module references
    if recommended_modules:
        biomarker_lines.append("\n🌿 [โมดูลสมุนไพรฟื้นฟูแนะนำหลัก]:")
        for idx, mod in enumerate(recommended_modules[:3]):
            biomarker_lines.append(f"   {idx+1}. {mod.get('name')} ({mod.get('code')}) - คะแนนการจับคู่วิถีรักษา: {mod.get('match_score')}%")

    biomarker_text = "\n".join(biomarker_lines)

    # 4. WRAP IN THE FINAL OUTPUT SCHEMA USING HEADERS
    final_report = f"""[Clinical Impression]
{clinical_impression_text}

[Mechanistic Pathophysiology Pathways]
{pathway_text}

[Biomarker Burden Interlinkage]
{biomarker_text}"""

    return final_report


def render_html_precision_report(patient, tspi_result, simulated_labs, symptoms=""):
    """
    Renders the beautiful HTML report using Jinja2 template file.
    """
    import os
    import json
    from jinja2 import Environment, FileSystemLoader

    # Load 39 axes config to map axis IDs to names
    from django.conf import settings
    tspi_data_dir = getattr(settings, 'TSPI_DATA_DIR', None)
    if tspi_data_dir and (tspi_data_dir / 'tspi_36_axes_v2.json').exists():
        axes_json_path = str(tspi_data_dir / 'tspi_36_axes_v2.json')
    else:
        axes_json_path = str(settings.BASE_DIR.parent / 'frontend' / 'src' / 'data' / 'tspi_36_axes_v2.json')
    axis_names_map = {}
    try:
        with open(axes_json_path, 'r', encoding='utf-8') as f:
            axes_data = json.load(f)
        for dom in axes_data['domains']:
            for ax in dom['axes']:
                num_id = int(ax['axis_id'].replace('AXIS_', ''))
                axis_names_map[num_id] = ax['name']
    except Exception as e:
        logger.error(f"Error loading axes names mapping for Jinja report: {e}")

    # Generate the text report content
    report_content = generate_local_precision_report(patient, tspi_result, simulated_labs)

    # Set up Jinja2 environment
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, 'templates', 'patients')
    
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('precision_medicine_report.html')

    # Render template
    html_report = template.render(
        patient=patient,
        tspi_result=tspi_result,
        simulated_labs=simulated_labs,
        symptoms=symptoms,
        report_content=report_content,
        axis_names_map=axis_names_map,
        range=range
    )
    return html_report
