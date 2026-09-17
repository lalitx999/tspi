import json
import os
from django.conf import settings

OFFICIAL_39_AXES = {
    1: "Systemic Inflammatory Load",
    2: "Immune Homeostasis",
    3: "Pathogen Defense",
    4: "Post-Infectious Persistence",
    5: "Glucose–Insulin Regulation",
    6: "Lipid–Lipotoxicity",
    7: "Nutrient Sensing (AMPK–mTOR)",
    8: "Mitochondrial Network",
    9: "Oxidative Stress & Redox Balance",
    10: "Proteostasis–Autophagy–Lysosome",
    11: "DNA Repair & Genomic Stability",
    12: "Epigenetic-Gene Regulation",
    13: "Longevity Signaling (SIRT–FOXO–IGF)",
    14: "Senescence & SASP",
    15: "Detoxification Capacity",
    16: "Digestive–Absorptive Function",
    17: "Microbiome Ecology",
    18: "Gut Barrier & Mucosal Integrity",
    19: "Colon Biofilm & Mucosal Burden",
    20: "Endothelial Function",
    21: "Vascular Remodeling & Microcirculation",
    22: "Thrombosis–Hemostasis",
    23: "Hemodynamics & Arterial Elasticity",
    24: "Wound Healing",
    25: "Fibrosis & ECM Remodeling",
    26: "Stem Cell & Hematopoiesis",
    27: "Glycation / Carbonyl Stress",
    28: "Muscle Protein Turnover",
    29: "Bone Remodeling",
    30: "Connective Tissue Integrity",
    31: "Female Hormone Network",
    32: "Male Androgen",
    33: "Thyroid–Adrenal–Growth",
    34: "Neuro–Sleep–Stress–Brain Clearance",
    35: "Visceral Organ Functional Reserve",
    36: "Oncology",
    37: "Oncologic Cell Fate",
    38: "Tumor Microenvironment & Metastatic Dynamics",
    39: "Genomic Regulation Homeostasis"
}

OFFICIAL_9_STEPS = [
    "Detoxification",
    "Microbiome Restoration",
    "Immune Regulation",
    "Redox Restoration",
    "Mitochondrial Restoration",
    "Autophagy",
    "Genomic Stability",
    "Genomic Regulation",
    "Prakati / Biological Normalization"
]

# domain_type: PRIMARY domains roll up into system_priorities (treatment-priority ranking).
# Canonical 12 Domains frozen from TSPI Master Data ONLY.
SYSTEM_DOMAINS = {
    "Domain 1 — Immune–Infection Governance": {"code": "D1", "canonical_name": "Immune–Infection Governance", "axes": [1, 2, 3, 4], "domain_type": "PRIMARY"},
    "Domain 2 — Metabolic–Energy Core": {"code": "D2", "canonical_name": "Metabolic–Energy Core", "axes": [5, 6, 7, 8, 9, 10], "domain_type": "PRIMARY"},
    "Domain 3 — Genomic Programming": {"code": "D3", "canonical_name": "Genomic Programming", "axes": [11, 12, 13, 14], "domain_type": "PRIMARY"},
    "Domain 4 — Detoxification & Cellular Defense": {"code": "D4", "canonical_name": "Detoxification & Cellular Defense", "axes": [15], "domain_type": "PRIMARY"},
    "Domain 5 — Digestive–Gut Ecosystem": {"code": "D5", "canonical_name": "Digestive–Gut Ecosystem", "axes": [16, 17, 18, 19], "domain_type": "PRIMARY"},
    "Domain 6 — Vascular–Circulation": {"code": "D6", "canonical_name": "Vascular–Circulation", "axes": [20, 21, 22, 23], "domain_type": "PRIMARY"},
    "Domain 7 — Repair–Regeneration": {"code": "D7", "canonical_name": "Repair–Regeneration", "axes": [24, 25, 26, 27], "domain_type": "PRIMARY"},
    "Domain 8 — Musculoskeletal & Structural Integrity": {"code": "D8", "canonical_name": "Musculoskeletal & Structural Integrity", "axes": [28, 29, 30], "domain_type": "PRIMARY"},
    "Domain 9 — Endocrine Network": {"code": "D9", "canonical_name": "Endocrine Network", "axes": [31, 32, 33], "domain_type": "PRIMARY"},
    "Domain 10 — Neurological Regulation": {"code": "D10", "canonical_name": "Neurological Regulation", "axes": [34], "domain_type": "PRIMARY"},
    "Domain 11 — Organ Resilience": {"code": "D11", "canonical_name": "Organ Resilience", "axes": [35], "domain_type": "PRIMARY"},
    "Domain 12 — Oncology & System-Level Regulation": {"code": "D12", "canonical_name": "Oncology & System-Level Regulation", "axes": [36, 37, 38, 39], "domain_type": "PRIMARY"},
}

# Module matching now reads from the DB-backed ModuleRegistryEntry
MASTER_DATA_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'last_dta', 'TSPI Modules Master Data + Training_Pairs.json')
NETWORK_REGISTRY_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'last_dta', '180_Network.json')

# ── ans.txt Section 12 "Canonical Lock" — evidence classification for the 39 axes ──────────
# P0-3: HYPOTHESIS never scores — hard invariant across ALL reports
# A8:  Mitochondrial Network — needs direct measurement (biopsy/respirometry)
# A16: Digestive-Absorptive — needs stool/functional GI test
# A17: Microbiome Ecology — needs 16S rRNA / stool analysis
# A19: Colon Biofilm — needs direct colonoscopy/stool analysis
# A25: Fibrosis & ECM Remodeling — needs direct FibroScan/biopsy/validated score; steatosis alone = HYPOTHESIS
# A28: Muscle Protein Turnover — needs direct measurement
# A30: Connective Tissue Integrity — ECM/tendon/ligament, NOT bone metastasis (→ A29)
# A34: Neuro-Sleep-Stress — self-reported symptoms not sufficient
HYPOTHESIS_AXES = {8, 16, 17, 19, 25, 28, 30, 34}

# P0-7: A33 (Thyroid-Adrenal-Growth) requires approved phenotype-scoring rule
# Na/K/BP in context of renal illness + critical illness = heavily confounded
# Treat as CLINICAL_INFERENCE (no scoring) until approved formula exists
# P0-8: A27 (Glycation/Carbonyl Stress) from disease history alone = confounded
# Requires current glycation markers (HbA1c elevation, AGE markers, fructosamine)
CLINICAL_INFERENCE_AXES = {27, 33}

# P0-5: A35/A37/A38 have clinical evidence present but no approved numeric scoring formula
# They are NOT "NOT_AVAILABLE" — they are EVIDENCE_PRESENT / NO_APPROVED_SCORING_RULE
# A35: Visceral Organ Reserve — BUN/Creatinine/eGFR/AST/ALT/Bilirubin all present
# A37: Oncologic Cell Fate — malignant cytology / NSCLC diagnosis = evidence present
# A38: Tumor Microenvironment — metastatic phenotype = evidence present
EVIDENCE_PRESENT_NO_SCORING_RULE_AXES = {35, 37, 38}

# P0-6: Bone evidence (bone metastasis/resorption/ALP) maps to A29 (Bone Remodeling)
# NOT A30 (Connective Tissue Integrity = tendon/ligament/ECM)
ONCOLOGY_CONTEXT_AXES = {36, 37, 38}

# ── P1-D: Marker → Axis relation-type registry (ans.txt problem #6) ────────────────────────
# Documents *why* each marker/symptom in views.py:calculate_precision_medicine touches a given
# axis, using the same DIRECT_SCORING/SUPPORTING/CONFOUNDED/NON_SCORING vocabulary as
# classify_axis(). This does not change scoring — classify_axis() already gates HYPOTHESIS/
# CONFOUNDED axes regardless of which marker set them — it makes the marker→axis link auditable
# (marker_provenance in the calculate-precision-medicine response) instead of an unlabelled
# if/elif. A lightweight code-level registry rather than a new DB model/table for this round.
MARKER_AXIS_RELATIONS = {
    "fbs_high": [
        {"axis": 5, "relation_type": "DIRECT_SCORING", "note": "FBS > 125 mg/dL"},
        {"axis": 27, "relation_type": "SUPPORTING", "note": "Hyperglycemia is glycation risk context, not a direct glycation marker"},
    ],
    "fbs_prediabetic": [
        {"axis": 5, "relation_type": "DIRECT_SCORING", "note": "FBS 100-125 mg/dL"},
    ],
    "fbs_low": [
        {"axis": 5, "relation_type": "DIRECT_SCORING", "note": "FBS < 70 mg/dL"},
    ],
    "hba1c_high": [
        {"axis": 5, "relation_type": "DIRECT_SCORING", "note": "HbA1c > 6.5%"},
        {"axis": 27, "relation_type": "SUPPORTING", "note": "Chronic hyperglycemia supports glycation risk context"},
    ],
    "hba1c_prediabetic": [
        {"axis": 5, "relation_type": "DIRECT_SCORING", "note": "HbA1c 5.7-6.5%"},
    ],
    "anemia": [
        {"axis": 26, "relation_type": "DIRECT_SCORING", "note": "Hb/Hct/MCV below threshold"},
        {"axis": 1, "relation_type": "SUPPORTING", "note": "Anemia workup often co-occurs with inflammatory load"},
    ],
    "doppler_atherosclerotic": [
        {"axis": 20, "relation_type": "DIRECT_SCORING", "note": "Doppler plaque/stenosis finding"},
        {"axis": 21, "relation_type": "DIRECT_SCORING", "note": "Doppler plaque/stenosis finding"},
        {"axis": 23, "relation_type": "SUPPORTING", "note": "Vascular finding supports hemodynamic context"},
    ],
    "symptom_fatigue": [
        {"axis": 8, "relation_type": "NON_SCORING", "note": "Fatigue is HYPOTHESIS-only context, not a direct mitochondrial measurement (ans.txt A8 lock)"},
        {"axis": 33, "relation_type": "CONFOUNDED", "note": "Fatigue is confounded by many systemic causes; non-scoring for A33 (ans.txt A33 lock)"},
    ],
    "symptom_constipation": [
        {"axis": 16, "relation_type": "SUPPORTING", "note": "Reported bowel symptom"},
        {"axis": 17, "relation_type": "NON_SCORING", "note": "Microbiome ecology needs stool analysis; symptom alone is HYPOTHESIS"},
        {"axis": 19, "relation_type": "NON_SCORING", "note": "Colon biofilm burden needs direct testing; symptom alone is HYPOTHESIS"},
    ],
    "symptom_sleep_stress": [
        {"axis": 34, "relation_type": "NON_SCORING", "note": "Self-reported sleep/stress symptom is HYPOTHESIS-only for this axis"},
    ],
    "symptom_joint_pain": [
        {"axis": 1, "relation_type": "SUPPORTING", "note": "Reported joint/muscle pain"},
        {"axis": 28, "relation_type": "NON_SCORING", "note": "Muscle protein turnover needs direct measurement; symptom alone is HYPOTHESIS"},
        {"axis": 30, "relation_type": "NON_SCORING", "note": "Connective tissue integrity needs direct evidence; symptom alone is HYPOTHESIS"},
    ],
    "symptom_bone_pain": [
        {"axis": 29, "relation_type": "SUPPORTING", "note": "Bone pain / bone metastasis → A29 Bone Remodeling (not A30)"},
    ],
    "bone_metastasis": [
        {"axis": 29, "relation_type": "SUPPORTING", "note": "Bone destruction/resorption → A29 Bone Remodeling per canonical mapping"},
    ],
    "alp_elevated": [
        {"axis": 29, "relation_type": "SUPPORTING", "note": "ALP elevation is osteoblast/bone marker → A29"},
    ],
    "disease_history_t2dm": [
        {"axis": 5, "relation_type": "CONFOUNDED",
         "note": "T2DM history = known_disease_context only; current A5 severity requires current FBS/HbA1c"},
        {"axis": 27, "relation_type": "CONFOUNDED",
         "note": "T2DM history ≠ current glycation severity; requires current HbA1c/AGE markers for A27"},
    ],
}


import re

def detect_and_strip_prompt_leakage(text: str) -> str:
    """
    Scans generated text for system prompt / role leakage (e.g. 'I understand my role as TSPI Chief Medical Officer...')
    and strips it clean to prevent raw LLM system prompt echoing in clinical reports.
    """
    if not text or not isinstance(text, str):
        return text or ""

    leakage_patterns = [
        r"^.*?(?:ฉันเข้าใจบทบาทและหน้าที่|ในฐานะ TSPI Chief Medical Officer|as TSPI Chief Medical Officer|I understand my role|constitution says|system instructions|ONTOLOGY LOCK|CRITICAL CLINICAL SAFETY RULES).*?\n?",
        r"(?:ฉันเข้าใจบทบาทและหน้าที่|ในฐานะ TSPI Chief Medical Officer|as TSPI Chief Medical Officer|I understand my role|constitution says|system instructions|ONTOLOGY LOCK|CRITICAL CLINICAL SAFETY RULES)"
    ]

    cleaned = text
    for pattern in leakage_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# P0-1: IDENTITY VALIDATOR GATE
# Must run BEFORE calculate_tspi_analysis(). If CONFLICT → return
# DATA_RECONCILIATION_REPORT, block all clinical scoring.
# ═══════════════════════════════════════════════════════════════════════════════
def validate_patient_identity(patient_data: dict) -> dict:
    """
    Validates that all patient data fields are internally consistent.
    A CONFLICT means the system may be mixing data from different patients.
    When CONFLICT: analysis_state = BLOCKED_DATA_RECONCILIATION.
    All clinical analysis (Axis scores, Keys, NSS, Networks, Modules,
    Treatment suggestions, Patient Report) is BLOCKED until resolved.

    Args:
        patient_data: dict with keys like 'age', 'gender', 'hn',
                      'soap_age', 'soap_gender', 'birth_year', 'record_date', 'clinical_notes'
    Returns:
        dict with identity_validation_status, analysis_state, conflict_details
    """
    issues = []

    age_primary = patient_data.get('age')             # from patient record
    age_soap = patient_data.get('soap_age')           # from SOAP note or history
    gender_primary = (patient_data.get('gender') or '').lower()
    gender_soap = (patient_data.get('soap_gender') or '').lower()
    hn_primary = patient_data.get('hn')
    hn_soap = patient_data.get('soap_hn')
    notes = str(patient_data.get('clinical_notes') or patient_data.get('history') or '')

    # Parse clinical notes for demographic text conflicts (e.g. "ชาย 25 ปี" vs Female 52y)
    if notes:
        gender_matches = re.findall(r'(ชาย|หญิง|ผู้ป่วยชาย|ผู้ป่วยหญิง|male|female)', notes, re.IGNORECASE)
        age_matches = re.findall(r'(?:อายุ|age|\b)\s*(\d{1,3})\s*(?:ปี|yo|years|y/o|\b)', notes, re.IGNORECASE)

        if gender_matches and not gender_soap:
            first_g = gender_matches[0].lower()
            if first_g in ['ชาย', 'ผู้ป่วยชาย', 'male']:
                gender_soap = 'male'
            elif first_g in ['หญิง', 'ผู้ป่วยหญิง', 'female']:
                gender_soap = 'female'

        if age_matches and age_soap is None:
            try:
                for a_str in age_matches:
                    a_int = int(a_str)
                    if 1 <= a_int <= 120:
                        age_soap = a_int
                        break
            except ValueError:
                pass

    # Check 1: Age conflict > 10 years between record and SOAP note / clinical text
    if age_primary is not None and age_soap is not None:
        try:
            age_diff = abs(int(age_primary) - int(age_soap))
            if age_diff > 10:
                issues.append({
                    "field": "age",
                    "conflict_type": "AGE_MISMATCH",
                    "value_a": f"Patient record: {age_primary}",
                    "value_b": f"SOAP/history: {age_soap}",
                    "severity": "CRITICAL" if age_diff > 20 else "HIGH",
                    "note": f"Age difference of {age_diff} years exceeds threshold. Possible patient data mixing."
                })
        except (TypeError, ValueError):
            pass

    # Check 2: Gender conflict
    if gender_primary and gender_soap:
        gender_map = {'m': 'male', 'f': 'female', 'male': 'male', 'female': 'female',
                      'ชาย': 'male', 'หญิง': 'female', 'mr': 'male', 'mrs': 'female', 'ms': 'female'}
        g1 = gender_map.get(gender_primary, gender_primary)
        g2 = gender_map.get(gender_soap, gender_soap)
        if g1 and g2 and g1 != g2:
            issues.append({
                "field": "gender",
                "conflict_type": "GENDER_MISMATCH",
                "value_a": f"Patient record: {gender_primary}",
                "value_b": f"SOAP/history: {gender_soap}",
                "severity": "CRITICAL",
                "note": "Gender mismatch between patient record and clinical notes. Verify patient identity."
            })

    # Check 3: HN/patient_id mismatch
    if hn_primary and hn_soap:
        if str(hn_primary).strip() != str(hn_soap).strip():
            issues.append({
                "field": "hn",
                "conflict_type": "HN_MISMATCH",
                "value_a": f"Record HN: {hn_primary}",
                "value_b": f"SOAP HN: {hn_soap}",
                "severity": "CRITICAL",
                "note": "HN/patient ID mismatch. Do not proceed with analysis."
            })

    if issues:
        return {
            "identity_validation_status": "CONFLICT",
            "analysis_state": "BLOCKED_DATA_RECONCILIATION",
            "conflict_details": issues,
            "allowed_output": "DATA_RECONCILIATION_REPORT_ONLY",
            "blocked_outputs": [
                "axis_scores", "three_keys", "nss",
                "network_reasoning", "module_matching",
                "treatment_suggestions", "patient_report",
                "physician_report", "multi_omics_report"
            ],
            "physician_action_required": (
                "Verify DOB, HN, and source document ownership before proceeding. "
                "Do not generate clinical conclusions from potentially mixed patient data."
            )
        }

    return {
        "identity_validation_status": "VERIFIED",
        "analysis_state": "ANALYSIS_READY",
        "conflict_details": [],
    }


def classify_axis(axis_id, raw_score):
    """
    Evidence classification for one axis — single source of truth for ALL three reports.

    P0-3:  HYPOTHESIS never scores (severity_score = None always).
    P0-5:  Separates data_availability from score_status.
           Evidence PRESENT does not mean a numeric score is available.
    P0-6:  A29 = Bone Remodeling (bone metastasis/resorption maps here, NOT A30).
           A30 = Connective Tissue Integrity (tendon/ligament/ECM only).
    P0-7:  A33 = CLINICAL_INFERENCE (confounded by renal disease + critical illness).
    P0-8:  A5/A27 from disease history only = confounded; current labs required.
    P0-13: score_derivation = DERIVED always for Axis scores (raw labs = MEASURED,
           computed Axis = DERIVED — these are semantically different).
    """
    axis_role = "CANDIDATE"
    eligible_for_priority = True
    eligible_for_module_match = True
    marker_relation_type = "DIRECT_SCORING"
    source_type_note = "LAB"
    severity_score = raw_score

    # P0-13: Axis score is always DERIVED (computed from raw evidence)
    # Raw labs (BUN, Hb, etc.) are MEASURED — the Axis aggregate score is not.
    score_derivation = "DERIVED"

    if raw_score is None:
        # Distinguish: no data submitted vs evidence present but no scoring rule
        if axis_id in EVIDENCE_PRESENT_NO_SCORING_RULE_AXES:
            # P0-5: Clinical/pathology evidence exists, but no approved numeric formula yet
            data_availability = "EVIDENCE_PRESENT"
            score_status = "NO_APPROVED_SCORING_RULE"
            evidence_status = "EVIDENCE_PRESENT_NO_SCORE"
            assessment_status = "ASSESSED_CONTEXTUALLY"
            eligible_for_priority = False       # cannot rank without a score
            eligible_for_module_match = False   # cannot match without a score
        else:
            data_availability = "NOT_AVAILABLE"
            score_status = "NOT_SCORED_NO_DATA"
            evidence_status = "NOT_AVAILABLE"
            assessment_status = "NOT_ASSESSED"
            eligible_for_priority = False
            eligible_for_module_match = False
    elif axis_id in HYPOTHESIS_AXES:
        # P0-3: HYPOTHESIS never scores — hard invariant
        data_availability = "INDIRECT_EVIDENCE"
        score_status = "NOT_SCORED_HYPOTHESIS"
        evidence_status = "HYPOTHESIS"
        assessment_status = "AXIS_CANDIDATE"
        severity_score = None
        eligible_for_priority = False
        eligible_for_module_match = False
        marker_relation_type = "NON_SCORING"
    elif axis_id in CLINICAL_INFERENCE_AXES:
        # P0-7/P0-8: Score from confounded inference — keep for display but gate usage
        data_availability = "INDIRECT_EVIDENCE"
        score_status = "SCORED_CONFOUNDED_INFERENCE"
        evidence_status = "CLINICAL_INFERENCE"
        assessment_status = "ASSESSED_CONFOUNDED"
        marker_relation_type = "CONFOUNDED"
        eligible_for_module_match = False
        # NOTE: eligible_for_priority stays True so these appear in domain ranking
        # but downstream prompt must communicate the confounded nature
    elif axis_id in ONCOLOGY_CONTEXT_AXES:
        data_availability = "CLINICAL_PATHOLOGY_EVIDENCE"
        score_status = "SCORED_CONTEXTUAL"
        evidence_status = "CLINICAL_INFERENCE"
        assessment_status = "ASSESSED_CONTEXTUALLY"
        marker_relation_type = "SUPPORTING"
    else:
        data_availability = "LAB_EVIDENCE"
        score_status = "SCORED"
        evidence_status = "DERIVED"
        assessment_status = "ASSESSED"

    if severity_score is None:
        if assessment_status == "AXIS_CANDIDATE":
            severity_band = "NOT_SCORED_HYPOTHESIS"
        elif score_status == "NO_APPROVED_SCORING_RULE":
            severity_band = "EVIDENCE_PRESENT_NO_SCORE"
        else:
            severity_band = "NOT_ASSESSED"
    elif severity_score <= 15:
        severity_band = "Optimal"
    elif severity_score <= 30:
        severity_band = "Early Biological Disturbance"
    elif severity_score <= 60:
        severity_band = "Functional Disturbance"
    elif severity_score <= 80:
        severity_band = "Pathological Disturbance"
    else:
        severity_band = "Critical Value"

    return {
        # Core evidence fields
        "evidence_status": evidence_status,
        "assessment_status": assessment_status,
        # P0-5: Separate availability from scoring
        "data_availability": data_availability,
        "score_status": score_status,
        # P0-13: Axis score = always DERIVED
        "score_derivation": score_derivation,
        # Scores
        "severity_score": severity_score,
        "severity_band": severity_band,
        # Eligibility gates
        "axis_role": axis_role,
        "eligible_for_priority": eligible_for_priority,
        "eligible_for_module_match": eligible_for_module_match,
        "marker_relation_type": marker_relation_type,
        "source_type_note": source_type_note,
        "severity_score": severity_score,
        "severity_band": severity_band,
    }


def _load_network_registry_metadata():
    if not os.path.exists(NETWORK_REGISTRY_PATH):
        return {"total_networks": None, "source_version": None}
    try:
        with open(NETWORK_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            "total_networks": (data.get('metadata') or {}).get('total_networks'),
            "source_version": data.get('version'),
        }
    except Exception as e:
        print(f"Error loading network registry JSON: {e}")
        return {"total_networks": None, "source_version": None}


def validate_analysis_record(ledger):
    """
    Cross-report invariant validator (ans.txt P0-4.13) — ports the 7 checks in
    frontend/src/app/api/ai/report/route.ts validateAnalysisRecord() (INV-001..007, route.ts:209-322)
    to Python so Django is the one place these are enforced instead of re-derived in TypeScript.
    Returns a list of violation dicts (empty = valid); does not raise — callers decide fail-open/closed.
    """
    violations = []

    axes = ledger.get("thirty_nine_axes", {}) or {}
    for key, a in axes.items():
        if a.get("evidence_status") == "HYPOTHESIS" and a.get("severity_score") is not None:
            violations.append({
                "rule_id": "INV-001",
                "axis_or_field": key,
                "message": f"{key} (HYPOTHESIS) must not have severity_score={a.get('severity_score')}. HYPOTHESIS never scores.",
            })
        if a.get("evidence_status") == "HYPOTHESIS" and a.get("eligible_for_priority") is True:
            violations.append({
                "rule_id": "INV-002",
                "axis_or_field": key,
                "message": f"{key} is HYPOTHESIS but eligible_for_priority=True. Must be False.",
            })

    keys = ledger.get("three_keys", {}) or {}
    for key_name, k in keys.items():
        if k.get("evidence_status") and k.get("evidence_status") != "DERIVED":
            violations.append({
                "rule_id": "INV-003",
                "axis_or_field": f"three_keys.{key_name}",
                "message": f'three_keys.{key_name}.evidence_status = "{k.get("evidence_status")}". Must be "DERIVED".',
            })

    steps = ledger.get("nine_restoration_steps", []) or []
    for idx, step in enumerate(steps):
        expected_no = idx + 1
        expected_name = OFFICIAL_9_STEPS[idx] if idx < len(OFFICIAL_9_STEPS) else None
        if step.get("canonical_step_no") != expected_no:
            violations.append({
                "rule_id": "INV-004",
                "axis_or_field": f"nine_restoration_steps[{idx}]",
                "message": f"Step at index {idx} has canonical_step_no={step.get('canonical_step_no')}, expected {expected_no}.",
            })
        if step.get("canonical_step_name") != expected_name:
            violations.append({
                "rule_id": "INV-004",
                "axis_or_field": f"nine_restoration_steps[{idx}].canonical_step_name",
                "message": f'Step {expected_no} has name="{step.get("canonical_step_name")}", expected "{expected_name}".',
            })

    net_reg = ledger.get("network_registry", {}) or {}
    if net_reg.get("registry_status") == "APPROVED":
        violations.append({
            "rule_id": "INV-005",
            "axis_or_field": "network_registry.registry_status",
            "message": "Network Registry is marked APPROVED but no clinical ratification has been recorded.",
        })

    mod_reg = ledger.get("module_registry", {}) or {}
    if (mod_reg.get("approved_modules") or 0) > 0 and mod_reg.get("registry_status") != "APPROVED":
        violations.append({
            "rule_id": "INV-006",
            "axis_or_field": "module_registry",
            "message": f'Module registry has {mod_reg.get("approved_modules")} approved modules but registry_status="{mod_reg.get("registry_status")}". Verify consistency.',
        })

    if (ledger.get("safety_gate") or {}).get("status") == "CONTRAINDICATED":
        violations.append({
            "rule_id": "INV-007",
            "axis_or_field": "safety_gate.status",
            "message": "Global CONTRAINDICATED is deprecated. Use intervention_eligibility[] with specific intervention statuses instead.",
        })

    return violations


def calculate_tspi_analysis(record, bowel_status='normal', mentzer_index=None, patient_data=None):
    """
    Calculates weighted Network Severity Score (NSS), System Priority Score (SPS),
    module recommendations, and the full evidence-status ledger (three_keys,
    nine_restoration_steps, thirty_nine_axes, safety_gate, network_registry, module_registry)
    based on the 39 official biological axes.
    No default 50 score is permitted. Excluded/NOT_ASSESSED axes are marked as None.
    HYPOTHESIS-classified axes never carry a severity_score (ans.txt P0-4.1).
    """
    # 0. HARD-GATE Identity Validation Check
    id_validation = validate_patient_identity(patient_data or {})
    if id_validation.get("identity_validation_status") == "CONFLICT":
        return {
            "identity_validation": id_validation,
            "analysis_state": "BLOCKED_DATA_RECONCILIATION",
            "report_state": "BLOCKED_DATA_RECONCILIATION",
            "is_valid": False,
            "invariant_violations": [{
                "rule_id": "INV-000",
                "axis_or_field": "identity_validation",
                "message": "CRITICAL DATA CONFLICT: Patient demographics mismatch. All clinical analysis blocked pending reconciliation."
            }],
            "nss": None,
            "severity_level": None,
            "severity_label": "BLOCKED: Demographic Data Reconciliation Required",
            "dosing_rule": "N/A",
            "ks_dosing": "N/A",
            "system_scores": {},
            "domain_types": {},
            "system_priorities": [],
            "recommended_modules": [],
            "recommended_modules_clinical": [],
            "provisional_qa_modules": [],
            "axesState": {},
            "thirty_nine_axes": {},
            "three_keys": {},
            "nine_restoration_steps": [],
            "module_registry_status": {"status": "PROVISIONAL", "total_modules": 0, "approved_modules": 0},
            "safety_gate": {
                "status": "BLOCKED_DATA_RECONCILIATION",
                "global_alerts": ["CRITICAL: Demographic conflict detected. Clinical report generation blocked."],
                "intervention_eligibility": [],
                "regimen_overlap": []
            },
            "care_goal_mode": {"mode": "BLOCKED", "source": "identity_conflict"},
            "respiratory_state": {"classification": "BLOCKED"},
            "canonical_domains": [],
            "framework_version": "39-axis-master-260715",
        }

    # 1. Extract the 39 axis scores from the record (clean legacy 50s)
    axes_scores = {}
    for i in range(1, 40):
        val = getattr(record, f'axis_{i}', None)
        if val == 50:
            # Treat legacy default 50 as None (Not Assessed)
            val = None
        axes_scores[i] = val

    # 2. Evidence classification per axis — this determines the *effective* score used by
    #    every downstream aggregate (NSS, Three Keys, Domain roll-up, Module matching, Nine
    #    Steps) so HYPOTHESIS axes are excluded uniformly everywhere instead of only in the
    #    report-writing layer.
    axis_classification = {i: classify_axis(i, axes_scores[i]) for i in range(1, 40)}
    effective_scores = {i: axis_classification[i]["severity_score"] for i in range(1, 40)}

    def get_avg(axes_list):
        vals = [effective_scores[ax] for ax in axes_list if effective_scores.get(ax) is not None]
        return round(sum(vals) / len(vals)) if vals else None

    # 3. Calculate Weighted Network Severity Score (NSS)
    weighted_sum = 0.0
    weight_sum = 0.0

    for i in range(1, 40):
        val = effective_scores[i]
        if val is not None:
            if i in [1, 5, 20, 21, 23, 26, 27]:
                confidence = 0.9
                completeness = 0.9
                evidence_quality = 0.9
            else:
                confidence = 0.7
                completeness = 0.7
                evidence_quality = 0.6

            weight = confidence * completeness * evidence_quality
            weighted_sum += val * weight
            weight_sum += weight

    if weight_sum > 0:
        base_nss = weighted_sum / weight_sum

        # Network Factor modifier based on abnormal axes (score >= 65)
        abnormal_count = sum(1 for v in effective_scores.values() if v is not None and v >= 65)
        if abnormal_count >= 6:
            factor = 1.10
        elif abnormal_count >= 3:
            factor = 1.05
        else:
            factor = 1.0

        nss = min(100.0, base_nss * factor)
    else:
        nss = None

    # 4. Calculate Severity Level and dosing rules
    if nss is None:
        severity_level = None
        severity_label = "Not Assessed: Insufficient Data"
        dosing_rule = "N/A"
    elif nss <= 15:
        severity_level = 0
        severity_label = "Level 0: Preventive Longevity & Network Optimization"
        dosing_rule = "2 แคปซูล × 2 ครั้งต่อวัน (เช้า + เย็น) รวม 4 แคปซูล/วัน"
    elif nss <= 30:
        severity_level = 1
        severity_label = "Level 1: Functional Imbalance"
        dosing_rule = "2 แคปซูล × 3 ครั้งต่อวัน (เช้า, กลางวัน, เย็น) รวม 6 แคปซูล/วัน"
    elif nss <= 60:
        severity_level = 2
        severity_label = "Level 2: Systemic Dysfunction"
        dosing_rule = "3 แคปซูล × 3 ครั้งต่อวัน (เช้า, กลางวัน, เย็น) รวม 9 แคปซูล/วัน"
    else:
        severity_level = 3
        severity_label = "Level 3: Advanced Network Failure"
        dosing_rule = "3 แคปซูล × 5 ครั้งต่อวัน รวม 15 แคปซูล/วัน"

    # 5. Special KS Bowel Titration Logic
    if bowel_status == 'incomplete':
        ks_dosing = "ตื่นนอน 2 แคปซูล + ก่อนนอน 2 แคปซูล (เพิ่มครั้งละ 2 เม็ดทุกๆ 3-7 วันจนกว่าจะขับถ่ายได้อย่างน้อย 2 ครั้งต่อวัน สูงสุดไม่เกิน 12 แคปซูล/วัน)"
    elif bowel_status == 'constipated':
        ks_dosing = "ตื่นนอน 2 แคปซูล + ก่อนนอน 4 แคปซูล (เพิ่มครั้งละ 2 เม็ดทุกๆ 3-7 วันจนกว่าจะขับถ่ายได้อย่างน้อย 2 ครั้งต่อวัน สูงสุดไม่เกิน 12 แคปซูล/วัน)"
    else:
        ks_dosing = "ก่อนนอน 2 แคปซูล (เพิ่มครั้งละ 2 เม็ดทุกๆ 3-7 วันจนกว่าจะขับถ่ายได้อย่างน้อย 2 ครั้งต่อวัน สูงสุดไม่เกิน 12 แคปซูล/วัน)"

    # 6. Calculate System (Domain) Priority Scores — Canonical 12 Domains ONLY
    system_scores = {}
    domain_types = {}
    for system_name, domain_info in SYSTEM_DOMAINS.items():
        axes_list = domain_info["axes"]
        domain_types[system_name] = domain_info["domain_type"]
        sys_vals = [effective_scores[ax] for ax in axes_list if ax in effective_scores and effective_scores[ax] is not None]
        system_scores[system_name] = sum(sys_vals) / len(sys_vals) if sys_vals else None

    primary_domain_scores = {k: v for k, v in system_scores.items() if domain_types[k] == "PRIMARY"}
    system_priorities = sorted(
        [(k, v) for k, v in primary_domain_scores.items() if v is not None],
        key=lambda x: x[1],
        reverse=True
    )
    none_systems = [(k, None) for k, v in primary_domain_scores.items() if v is None]
    system_priorities_all = system_priorities + none_systems

    # 7. Load Modules and Score matching with Fail-Closed Registry check
    from .models import ModuleRegistryEntry

    matched_modules = []
    total_modules_in_registry = 0
    approved_modules_count = 0
    module_axis_map = {}
    try:
        modules_qs = list(ModuleRegistryEntry.objects.all())
        total_modules_in_registry = len(modules_qs)
        approved_modules_count = sum(1 for m in modules_qs if m.mapping_status == "APPROVED")

        for mod in modules_qs:
            primary_axes = mod.primary_axes or []
            if not primary_axes:
                continue

            valid_mod_vals = [
                effective_scores[ax] for ax in primary_axes
                if ax in effective_scores and effective_scores[ax] is not None
                and axis_classification[ax]["eligible_for_module_match"]
            ]
            if not valid_mod_vals:
                continue

            overlap_avg = sum(valid_mod_vals) / len(valid_mod_vals)
            match_score = min(100.0, overlap_avg)

            safety_status = "PASS"
            contraindications = mod.contraindications or []
            if contraindications:
                safety_status = "PASS_WITH_MONITORING"

            matched_modules.append({
                "code": mod.code,
                "name": mod.name,
                "category": mod.category,
                "primary_function": mod.primary_function,
                "mechanisms": mod.mechanisms,
                "primary_axes": primary_axes,
                "contraindications": contraindications,
                "clinical_indications": mod.clinical_indications,
                "synergy_with": mod.synergy_with,
                "match_score": round(match_score, 1),
                "safety_status": safety_status,
                "mapping_status": mod.mapping_status
            })
    except Exception as e:
        print(f"Error loading module registry: {e}")

    matched_modules = sorted(matched_modules, key=lambda x: x['match_score'], reverse=True)
    top_matched_modules = matched_modules[:12]

    # Fail-closed module separation: Clinical reports suppress candidates when approved_modules_count == 0
    recommended_modules_clinical = top_matched_modules if approved_modules_count > 0 else []
    provisional_qa_modules = top_matched_modules if approved_modules_count == 0 else []

    for mod in top_matched_modules:
        for ax in mod["primary_axes"]:
            module_axis_map.setdefault(ax, set()).add(mod["code"])
    regimen_overlap = [
        {
            "axis_code": f"A{ax}",
            "axis_name": OFFICIAL_39_AXES.get(ax, f"Axis {ax}"),
            "modules": sorted(codes),
            "note": "Multiple candidate modules target the same axis — review for pill burden / redundant mechanism before combining."
        }
        for ax, codes in sorted(module_axis_map.items()) if len(codes) >= 2
    ]

    module_registry_status = {
        "status": "APPROVED" if approved_modules_count > 0 else "PROVISIONAL",
        "total_modules": total_modules_in_registry,
        "approved_modules": approved_modules_count
    }
    module_registry = {
        "registry_status": module_registry_status["status"],
        "total_modules": total_modules_in_registry,
        "approved_modules": approved_modules_count,
        "blocker_reason": "Module Registry mapping_status is not APPROVED for any module yet.",
        "display_instruction": "PROVISIONAL CANDIDATE — NOT FOR CLINICAL USE. Hidden from Clinical Report until approved_modules > 0."
    }

    net_meta = _load_network_registry_metadata()
    network_registry = {
        "registry_status": "LOADED_NOT_YET_APPROVED",
        "total_networks": net_meta["total_networks"],
        "source_version": net_meta["source_version"],
        "blocker_reason": "Official 180-Network Registry data is loaded but has not been clinically APPROVED.",
        "display_instruction": "PROVISIONAL CANDIDATE — NOT FOR CLINICAL USE."
    }

    # ── Safety Gate — Global State vs Intervention Eligibility Separation ──
    safety_status = "PASS"
    global_alerts = []
    intervention_eligibility = []
    if mentzer_index is not None and mentzer_index < 13:
        safety_status = "PASS_WITH_MONITORING"
        global_alerts.append(
            f"Mentzer Index = {mentzer_index:.2f} (< 13). Pattern consistent with Thalassemia Trait. "
            "Iron supplementation is HOLD pending Hb Typing + Ferritin confirmation."
        )
        intervention_eligibility.append({
            "intervention_id": "IRON_SUPPLEMENTATION",
            "status": "HOLD_PENDING_CONFIRMATION",
            "reason_rule_id": "MENTZER_THAL_GATE_001",
            "reason": "suspected thalassemia-pattern microcytosis (Mentzer < 13)",
            "required_confirmation": ["Ferritin", "TIBC", "Transferrin Saturation", "Hb Typing"]
        })

    oncology_assessed = any(
        axis_classification[ax]["evidence_status"] != "NOT_AVAILABLE" for ax in (37, 38)
    )
    for mod in top_matched_modules:
        contraindications = mod.get("contraindications") or []
        if not contraindications:
            continue
        mentions_cancer = any("cancer" in c.lower() for c in contraindications)
        if mentions_cancer and oncology_assessed:
            intervention_eligibility.append({
                "intervention_id": mod["code"],
                "status": "HOLD_PENDING_CONFIRMATION",
                "reason_rule_id": "MODULE_CONTRAINDICATION_ONCOLOGY",
                "required_confirmation": contraindications
            })
        else:
            intervention_eligibility.append({
                "intervention_id": mod["code"],
                "status": "INSUFFICIENT_DATA",
                "reason_rule_id": "MODULE_CONTRAINDICATION_UNVERIFIED",
                "required_confirmation": contraindications
            })

    # 8. Format axesState and thirty_nine_axes
    axes_state = {}
    thirty_nine_axes = {}
    candidate_axes_requiring_confirmation = []

    for i in range(1, 40):
        cls = axis_classification[i]
        axis_name = OFFICIAL_39_AXES.get(i, f"Axis {i}")

        axes_state[f"AXIS_{i}"] = {
            "name": axis_name,
            "score": cls["severity_score"],
            "severity": cls["severity_band"],
            "value_source_type": cls["evidence_status"]
        }

        thirty_nine_axes[f"AXIS_{i}"] = {
            "code": f"A{i}",
            "name": axis_name,
            "severity_score": cls["severity_score"],
            "severity_band": cls["severity_band"],
            "scoring_formula_version": "axis-v1.0",
            "score_derivation": cls["score_derivation"],
            "data_availability": cls["data_availability"],
            "score_status": cls["score_status"],
            "evidence_status": cls["evidence_status"],
            "marker_relation_type": cls["marker_relation_type"],
            "source_type_note": cls["source_type_note"],
            "assessment_status": cls["assessment_status"],
            "axis_role": cls["axis_role"],
            "eligible_for_priority": cls["eligible_for_priority"],
            "eligible_for_module_match": cls["eligible_for_module_match"],
            "clinical_urgency": None,
            "causal_driver_probability": None,
            "restoration_priority_rank": None,
            "treatment_priority_rank": None,
        }

        if cls["assessment_status"] == "AXIS_CANDIDATE" or cls["evidence_status"] == "HYPOTHESIS":
            candidate_axes_requiring_confirmation.append({
                "code": f"A{i}",
                "name": axis_name,
                "evidence_status": "HYPOTHESIS",
                "assessment_status": "AXIS_CANDIDATE",
                "candidate_relevance": "HIGH" if axes_scores.get(i) and axes_scores.get(i) >= 70 else "MEDIUM",
                "required_confirmation": "Targeted functional / biomarker testing required before scoring"
            })

    # 9. Three Biological Keys with Uniform Crosswalk Coverage Rule
    KEY_AXIS_GROUPS = {
        "metabolic_energy": {
            "axes": [5, 6, 7, 8, 9, 10],
            "label": "Metabolic Energy",
            "confidence": 0.85,
            "min_count": 2,
            "min_ratio": 0.25
        },
        "biological_dynamic": {
            "axes": [20, 21, 22, 23, 31, 32, 33, 34],
            "label": "Biological Dynamic",
            "confidence": 0.80,
            "min_count": 2,
            "min_ratio": 0.25
        },
        "biointegrity": {
            "axes": [15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29, 30, 37, 38, 39],
            "label": "Biointegrity",
            "confidence": 0.90,
            "min_count": 3,
            "min_ratio": 0.20
        },
    }
    three_keys = {}
    for key, group in KEY_AXIS_GROUPS.items():
        assessed_axes = [ax for ax in group["axes"] if effective_scores.get(ax) is not None]
        coverage_ratio = len(assessed_axes) / len(group["axes"])

        if len(assessed_axes) < group["min_count"] or coverage_ratio < group["min_ratio"]:
            score = None
            key_status = "PARTIAL_NOT_SCORABLE"
        else:
            score = get_avg(group["axes"])
            key_status = "DERIVED"

        three_keys[key] = {
            "score": score,
            "confidence": group["confidence"] if score is not None else None,
            "calculation_version": "keys-v1.0",
            "evidence_status": key_status,
            "score_status": key_status,
            "formula_version": "keys-v1.0",
            "contributing_axis_ids": group["axes"],
            "assessed_axes_count": len(assessed_axes),
            "total_axes_in_group": len(group["axes"]),
            "assessment_coverage": f"{len(assessed_axes)}/{len(group['axes'])}",
            "key_uncertainty": "PARTIAL_NOT_SCORABLE" if score is None else ("PARTIAL_DATA" if len(assessed_axes) < len(group["axes"]) else "FULL_DATA"),
            "label": group["label"],
            "note": "Disturbance Score: higher = more disturbed (not health score)",
        }

    # 10. Nine Restoration Steps Priority
    step_score_values = [
        effective_scores.get(15),   # Step 1: Detoxification
        effective_scores.get(17),   # Step 2: Microbiome Restoration
        get_avg([1, 2, 3, 4]),      # Step 3: Immune Regulation
        effective_scores.get(9),    # Step 4: Redox Restoration
        effective_scores.get(8),    # Step 5: Mitochondrial Restoration
        effective_scores.get(10),   # Step 6: Autophagy
        get_avg([11, 12]),          # Step 7: Genomic Stability
        effective_scores.get(39),   # Step 8: Genomic Regulation
        effective_scores.get(35),   # Step 9: Prakati / Biological Normalization
    ]

    ranked_indices = sorted(
        [(idx, score) for idx, score in enumerate(step_score_values) if score is not None],
        key=lambda x: x[1],
        reverse=True
    )
    rank_map = {idx: rank + 1 for rank, (idx, _) in enumerate(ranked_indices)}

    nine_restoration_steps = [
        {
            "canonical_step_no": idx + 1,
            "canonical_step_name": name,
            "priority_rank": rank_map.get(idx),
            "status": "ASSESSED" if step_score_values[idx] is not None else "NOT_ASSESSED",
            "assessment_status": "ASSESSED" if step_score_values[idx] is not None else "NOT_ASSESSED"
        }
        for idx, name in enumerate(OFFICIAL_9_STEPS)
    ]

    ledger = {
        "identity_validation": id_validation,
        "analysis_state": "ANALYSIS_READY",
        "report_state": "AI_DRAFT",
        "nss": round(nss, 1) if nss is not None else None,
        "severity_level": severity_level,
        "severity_label": severity_label,
        "dosing_rule": dosing_rule,
        "ks_dosing": ks_dosing,
        "system_scores": {k: (round(v, 1) if v is not None else None) for k, v in system_scores.items()},
        "domain_types": domain_types,
        "system_priorities": [{"system": k, "score": (round(v, 1) if v is not None else None)} for k, v in system_priorities_all],
        "recommended_modules": top_matched_modules,
        "recommended_modules_clinical": recommended_modules_clinical,
        "provisional_qa_modules": provisional_qa_modules,
        "candidate_axes_requiring_confirmation": candidate_axes_requiring_confirmation,
        "axesState": axes_state,
        "restoration_steps": OFFICIAL_9_STEPS,
        "three_keys": three_keys,
        "nine_restoration_steps": nine_restoration_steps,
        "module_registry_status": module_registry_status,
        "thirty_nine_axes": thirty_nine_axes,
        "network_registry": network_registry,
        "module_registry": module_registry,
        "safety_gate": {
            "status": safety_status,
            "global_alerts": global_alerts,
            "intervention_eligibility": intervention_eligibility,
            "regimen_overlap": regimen_overlap,
        },
        "care_goal_mode": {
            "mode": "NOT_SET",
            "source": "default",
            "note": "Must be set by physician before report generation."
        },
        "respiratory_state": {
            "classification": "NOT_ASSESSED",
            "pO2": None,
            "pCO2": None,
            "classification_confidence": "INSUFFICIENT_DATA",
            "rule_id": None,
            "physician_review_required": True,
        },
        "canonical_domains": [
            {"code": info["code"], "name": info["canonical_name"], "full_title": title}
            for title, info in SYSTEM_DOMAINS.items()
        ],
        "framework_version": "39-axis-master-260715",
    }

    # Cross-Report Invariant Validator
    violations = validate_analysis_record(ledger)
    ledger["is_valid"] = len(violations) == 0
    ledger["invariant_violations"] = violations

    return ledger
