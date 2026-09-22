from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

from patients.models import AnalysisRecord, Patient, PatientBiologicalRecord, TSPIBrainTrainingLog, ModuleRegistryEntry
from patients.tspi_engine import (
    calculate_tspi_analysis,
    validate_patient_identity,
    evaluate_omics_utility_gate,
    validate_analysis_record,
    HYPOTHESIS_AXES,
    OFFICIAL_9_STEPS,
)
from patients.serializers import PatientSerializer


class PatientRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "IDcard": "1234567890123",
            "password": "safe-test-password",
            "email": "patient@example.test",
            "fname": "Test",
            "lname": "Patient",
            "sex": "หญิง",
            "hn": "HN-REGISTRATION-TEST",
        }

    def test_registration_rolls_back_when_a_later_step_fails(self):
        """A failed audit write must not leave a usable login without an EMR profile."""
        with patch("accounts.views.AuditLog.objects.create", side_effect=RuntimeError("audit unavailable")):
            response = self.client.post("/api/auth/register/", self.payload, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"], "ระบบลงทะเบียนขัดข้องชั่วคราว กรุณาลองใหม่ภายหลังหรือติดต่อคลินิก")
        self.assertFalse(User.objects.filter(username=self.payload["IDcard"]).exists())
        self.assertFalse(Patient.objects.filter(id_card=self.payload["IDcard"]).exists())

    def test_serializer_accepts_birth_date_string_on_new_patient_instance(self):
        patient = Patient(
            legacy_id="TEST-BIRTHDATE-STRING",
            first_name="Test",
            last_name="Patient",
            phone="0000000000",
            birth_date="2000-01-31",
        )

        self.assertEqual(PatientSerializer(patient).data["birthday"], "2000-01-31")


def make_patient(**kwargs):
    defaults = dict(
        legacy_id="TEST-001",
        first_name="Test",
        last_name="Patient",
        phone="0000000000",
    )
    defaults.update(kwargs)
    return Patient.objects.create(**defaults)


class TspiEngineHypothesisTests(TestCase):
    """ans.txt P0-4.1: HYPOTHESIS axes must never carry a numeric severity_score."""

    def test_hypothesis_axis_has_no_severity_score(self):
        patient = make_patient()
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_8=75)
        result = calculate_tspi_analysis(record)

        axis_8 = result["thirty_nine_axes"]["AXIS_8"]
        self.assertEqual(axis_8["evidence_status"], "HYPOTHESIS")
        self.assertIsNone(axis_8["severity_score"])
        self.assertFalse(axis_8["eligible_for_priority"])
        self.assertFalse(axis_8["eligible_for_module_match"])
        # Legacy axesState shape must reflect the same nulled score.
        self.assertIsNone(result["axesState"]["AXIS_8"]["score"])

    def test_hypothesis_axis_excluded_from_nss(self):
        patient = make_patient(legacy_id="TEST-002")
        record_with_hypothesis = PatientBiologicalRecord.objects.create(patient=patient, axis_8=100)
        result_with = calculate_tspi_analysis(record_with_hypothesis)

        record_without = PatientBiologicalRecord.objects.create(patient=patient, axis_8=None)
        result_without = calculate_tspi_analysis(record_without)

        # A HYPOTHESIS-only axis contributes nothing, so both records should score identically
        # (None NSS — no other axis has data).
        self.assertEqual(result_with["nss"], result_without["nss"])
        self.assertIsNone(result_with["nss"])

    def test_all_hypothesis_axes_classified(self):
        patient = make_patient(legacy_id="TEST-003")
        kwargs = {f"axis_{i}": 80 for i in HYPOTHESIS_AXES}
        record = PatientBiologicalRecord.objects.create(patient=patient, **kwargs)
        result = calculate_tspi_analysis(record)
        for i in HYPOTHESIS_AXES:
            axis = result["thirty_nine_axes"][f"AXIS_{i}"]
            self.assertEqual(axis["evidence_status"], "HYPOTHESIS")
            self.assertIsNone(axis["severity_score"])


class IdentityConflictGateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="clinical-staff", password="test", is_staff=True)
        self.patient = make_patient(legacy_id="TEST-IDENTITY", hn="HN-IDENTITY", gender="F")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_source_owner_hn_mismatch_blocks_analysis(self):
        result = validate_patient_identity({
            "hn": "HN-IDENTITY",
            "lab_owner_hn": "HN-OTHER",
            "lab_source_record_id": "LAB-42",
        })

        self.assertEqual(result["identity_validation_status"], "CONFLICT")
        self.assertEqual(result["analysis_state"], "BLOCKED_DATA_RECONCILIATION")
        self.assertEqual(result["conflict_details"][0]["conflict_type"], "SOURCE_OWNERSHIP_MISMATCH")

    def test_conflicting_request_creates_no_record_or_analysis_snapshot(self):
        response = self.client.post(
            f"/api/patients/{self.patient.id}/calculate-precision-medicine/",
            {"lab_owner_hn": "HN-OTHER", "lab_source_record_id": "LAB-42"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["analysis_state"], "BLOCKED_DATA_RECONCILIATION")
        self.assertEqual(PatientBiologicalRecord.objects.filter(patient=self.patient).count(), 0)
        self.assertEqual(self.patient.analysis_records.count(), 0)

    def test_legacy_analysis_endpoint_returns_reconciliation_only_for_blocked_snapshot(self):
        source_record = PatientBiologicalRecord.objects.create(patient=self.patient)
        ledger = calculate_tspi_analysis(
            source_record,
            patient_data={"hn": "HN-IDENTITY", "lab_owner_hn": "HN-OTHER"},
        )
        record = AnalysisRecord.objects.create(
            patient=self.patient,
            source_record=source_record,
            inputs_hash="blocked-legacy-analysis",
            ledger=ledger,
        )

        response = self.client.get(
            f"/api/patients/{self.patient.id}/tspi-analysis/?analysis_record_id={record.id}"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["allowed_output"], "DATA_RECONCILIATION_REPORT_ONLY")
        self.assertNotIn("thirty_nine_axes", response.data)


class TspiEngineThreeKeysTests(TestCase):
    """ans.txt P0-4.2: Three Keys must always be DERIVED with formula_version/coverage."""

    def test_three_keys_are_derived_with_coverage(self):
        patient = make_patient(legacy_id="TEST-010")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_5=60, axis_6=70)
        result = calculate_tspi_analysis(record)

        for key_name in ("metabolic_energy", "biological_dynamic", "biointegrity"):
            key = result["three_keys"][key_name]
            self.assertEqual(key["evidence_status"], "DERIVED")
            self.assertIn("formula_version", key)
            self.assertIn("assessment_coverage", key)
            self.assertIn("contributing_axis_ids", key)

        # metabolic_energy = avg(5,6,7,8,9,10); axis_8 is HYPOTHESIS-classified so it never
        # contributes even if a raw value happened to be present.
        self.assertEqual(result["three_keys"]["metabolic_energy"]["assessed_axes_count"], 2)


class TspiEngineNineStepsTests(TestCase):
    """ans.txt P0-4.3: canonical_step_no/name must never move; only priority_rank is dynamic."""

    def test_canonical_order_is_fixed_regardless_of_input(self):
        patient = make_patient(legacy_id="TEST-020")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_8=90, axis_15=10)
        result = calculate_tspi_analysis(record)

        steps = result["nine_restoration_steps"]
        self.assertEqual(len(steps), 9)
        for idx, step in enumerate(steps):
            self.assertEqual(step["canonical_step_no"], idx + 1)
            self.assertEqual(step["canonical_step_name"], OFFICIAL_9_STEPS[idx])


class TspiEngineDomainTests(TestCase):
    """ans.txt problem #6: Domain 11 reuses Domain 6's axes — must not double-count priority."""

    def test_domain_11_is_cross_cutting_and_excluded_from_priorities(self):
        patient = make_patient(legacy_id="TEST-030")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_24=90, axis_25=90, axis_26=90)
        result = calculate_tspi_analysis(record)

        self.assertEqual(result["domain_types"]["Domain 11 — Regeneration & Repair System"], "CROSS_CUTTING")
        self.assertEqual(result["domain_types"]["Domain 6 — Repair–Fibrosis–Regeneration"], "PRIMARY")

        priority_systems = {p["system"] for p in result["system_priorities"]}
        self.assertNotIn("Domain 11 — Regeneration & Repair System", priority_systems)
        self.assertIn("Domain 6 — Repair–Fibrosis–Regeneration", priority_systems)

        # Still scored for display, just not in the priority ranking.
        self.assertIsNotNone(result["system_scores"]["Domain 11 — Regeneration & Repair System"])


class ValidateAnalysisRecordTests(TestCase):
    """ans.txt P0-4.13: invariant validator must catch a HYPOTHESIS axis with a leaked score."""

    def test_flags_hypothesis_axis_with_severity_score(self):
        bad_ledger = {
            "thirty_nine_axes": {
                "AXIS_8": {"evidence_status": "HYPOTHESIS", "severity_score": 75, "eligible_for_priority": False}
            },
            "three_keys": {},
            "nine_restoration_steps": [],
            "network_registry": {"registry_status": "LOADED_NOT_YET_APPROVED"},
            "module_registry": {"registry_status": "PROVISIONAL", "approved_modules": 0},
            "safety_gate": {"status": "PASS"},
        }
        violations = validate_analysis_record(bad_ledger)
        rule_ids = {v["rule_id"] for v in violations}
        self.assertIn("INV-001", rule_ids)

    def test_clean_ledger_from_engine_has_no_violations(self):
        patient = make_patient(legacy_id="TEST-040")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_5=60)
        result = calculate_tspi_analysis(record)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["invariant_violations"], [])

    def test_flags_canonical_axis_code_name_mismatch(self):
        bad_ledger = {
            "thirty_nine_axes": {
                **{
                    f"AXIS_{i}": {"code": f"A{i}", "name": f"Axis {i}"}
                    for i in range(1, 40)
                }
            },
            "three_keys": {},
            "nine_restoration_steps": [],
            "network_registry": {},
            "module_registry": {},
            "safety_gate": {},
        }
        bad_ledger["thirty_nine_axes"]["AXIS_5"]["name"] = "Wrong name"

        violations = validate_analysis_record(bad_ledger)

        self.assertIn("INV-008", {violation["rule_id"] for violation in violations})


class SerializerDefaultScoreTests(TestCase):
    """ans.txt "no default 50" rule — an axis with no record must read NOT_ASSESSED, not 50."""

    def test_get_axes_returns_none_when_no_record(self):
        patient = make_patient(legacy_id="TEST-050")
        serializer = PatientSerializer(patient)
        axes = serializer.data["axes"]
        self.assertIsNone(axes["AXIS_1"]["score"])
        self.assertEqual(axes["AXIS_1"]["status"], "NOT_ASSESSED")

    def test_get_axes_treats_legacy_50_as_not_assessed(self):
        patient = make_patient(legacy_id="TEST-051")
        PatientBiologicalRecord.objects.create(patient=patient, axis_1=50, axis_2=65)
        serializer = PatientSerializer(patient)
        axes = serializer.data["axes"]
        self.assertIsNone(axes["AXIS_1"]["score"])
        self.assertEqual(axes["AXIS_1"]["status"], "NOT_ASSESSED")
        self.assertEqual(axes["AXIS_2"]["score"], 65)
        self.assertEqual(axes["AXIS_2"]["status"], "ASSESSED")


class TrainBrainModelReviewGateTests(TestCase):
    """ans.txt P1-C: LLM-invented axis severities must be physician-reviewed before training."""

    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="doctor1", password="x")
        self.client.force_authenticate(user=user)

    def test_rejects_when_no_logs_reviewed(self):
        TSPIBrainTrainingLog.objects.create(
            inputs={"labs": {"fbs": 130}},
            output_axes={"AXIS_5": 80},
            reviewed=False,
        )
        res = self.client.post("/api/ai/train-brain-model/")
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.data["success"])

    def test_trains_when_a_log_is_reviewed(self):
        TSPIBrainTrainingLog.objects.create(
            inputs={"labs": {"fbs": 130}},
            output_axes={f"AXIS_{i}": 50 for i in range(1, 40)},
            reviewed=True,
        )
        res = self.client.post("/api/ai/train-brain-model/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])


class GenerateClinicalPdfGatingTests(TestCase):
    """ans.txt P1-A: the legacy clinical-dossier endpoint must use the gated ledger too —
    a HYPOTHESIS axis must not show a numeric score/status here either."""

    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="doctor2", password="x")
        self.client.force_authenticate(user=user)

    def test_hypothesis_axis_not_scored_in_dossier_html(self):
        patient = make_patient(legacy_id="TEST-060")
        source_record = PatientBiologicalRecord.objects.create(patient=patient, axis_8=90)
        AnalysisRecord.objects.create(
            patient=patient,
            source_record=source_record,
            inputs_hash="test-hypothesis-pdf",
            ledger=calculate_tspi_analysis(source_record),
        )

        res = self.client.get(f"/api/ai/generate-clinical-pdf/?patient={patient.id}")
        self.assertEqual(res.status_code, 200)
        html = res.data["html"]
        self.assertIn("Hypothesis", html)
        self.assertNotIn("90/100", html)

    def test_identity_conflict_snapshot_blocks_dossier_generation(self):
        patient = make_patient(legacy_id="TEST-061", hn="HN-PDF-IDENTITY")
        source_record = PatientBiologicalRecord.objects.create(patient=patient)
        blocked_ledger = calculate_tspi_analysis(
            source_record,
            patient_data={
                "hn": "HN-PDF-IDENTITY",
                "lab_owner_hn": "HN-OTHER",
                "lab_source_record_id": "LAB-PDF-42",
            },
        )
        analysis_record = AnalysisRecord.objects.create(
            patient=patient,
            source_record=source_record,
            inputs_hash="test-blocked-pdf",
            ledger=blocked_ledger,
        )

        res = self.client.get(
            f"/api/ai/generate-clinical-pdf/?patient={patient.id}&analysis_record_id={analysis_record.id}"
        )

        self.assertEqual(res.status_code, 400)
        self.assertIn(b"REPORT GENERATION BLOCKED", res.content)
        self.assertIn(b"LAB-PDF-42", res.content)

    def test_legacy_text_analysis_record_id_does_not_cause_pdf_server_error(self):
        patient = make_patient(legacy_id="TEST-064")
        patient.extra_data = {
            "generated_reports": [{
                "id": "legacy-report",
                "reportType": "patient",
                "analysisRecordId": "TSPI-1790055558179",
                "report": [],
            }]
        }
        patient.save()

        res = self.client.get(f"/api/ai/patients/{patient.id}/reports/legacy-report/pdf/")

        self.assertEqual(res.status_code, 403)


class AnalysisRecordProvenanceTests(TestCase):
    def test_analysis_record_is_append_only(self):
        patient = make_patient(legacy_id="TEST-062")
        source_record = PatientBiologicalRecord.objects.create(patient=patient)
        record = AnalysisRecord.objects.create(
            patient=patient,
            source_record=source_record,
            inputs_hash="immutable-analysis-record",
            ledger={"analysis_state": "ANALYSIS_READY"},
            identity_snapshot={"identity_validation_status": "VERIFIED"},
            evidence_provenance={"source_ownership": []},
            registry_versions={"canonical_registry": {"version": "test"}},
        )

        self.assertIsNotNone(record.analysis_run_id)
        record.ledger = {"analysis_state": "tampered"}
        with self.assertRaises(ValidationError):
            record.save()


class OmicsUtilityGateTests(TestCase):
    def test_blocks_omics_without_question_plan_and_consent(self):
        result = evaluate_omics_utility_gate({})
        self.assertEqual(result["status"], "BLOCKED_NO_CLINICAL_UTILITY")
        self.assertIn("clinical_question", result["missing_requirements"])

    def test_allows_omics_only_after_utility_requirements_are_documented(self):
        result = evaluate_omics_utility_gate({
            "omics_clinical_question": "Clarify a treatment-resistant phenotype",
            "omics_actionability_plan": "Review result with physician before any intervention",
            "omics_informed_consent": True,
        })
        self.assertEqual(result["status"], "APPROVED_FOR_ORDERING")


class ScoringContractGateTests(TestCase):
    def test_unapproved_numeric_score_is_not_patient_release_eligible(self):
        patient = make_patient(legacy_id="TEST-063")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_5=85)
        ledger = calculate_tspi_analysis(record)

        self.assertFalse(ledger["scoring_contracts"]["patient_release_eligible"])
        self.assertEqual(ledger["scoring_contracts"]["numeric_score_axes"][0]["status"], "MISSING")


class MarkerProvenanceTests(TestCase):
    """ans.txt P1-D: marker->axis assignments in calculate_precision_medicine must be
    auditable with an explicit relation_type instead of an unlabelled if/elif."""

    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="doctor3", password="x", is_staff=True)
        self.client.force_authenticate(user=user)

    def test_fbs_marker_provenance_recorded(self):
        patient = make_patient(legacy_id="TEST-070")
        res = self.client.post(
            f"/api/patients/{patient.id}/calculate-precision-medicine/",
            {"fbs": "130"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        provenance = res.data["marker_provenance"]
        markers = {(p["marker"], p["axis"], p["relation_type"]) for p in provenance}
        self.assertIn(("fbs_high", 5, "DIRECT_SCORING"), markers)
        self.assertIn(("fbs_high", 27, "SUPPORTING"), markers)


class ModuleRegistryDbTests(TestCase):
    """roadmap 3-A/3-B: module matching reads ModuleRegistryEntry (DB), not the JSON file."""

    def test_import_migration_populated_92_modules(self):
        self.assertEqual(ModuleRegistryEntry.objects.count(), 92)
        self.assertTrue(all(m.mapping_status == "PROVISIONAL" for m in ModuleRegistryEntry.objects.all()))

    def test_module_matching_reads_from_db(self):
        ModuleRegistryEntry.objects.all().delete()
        ModuleRegistryEntry.objects.create(code="TESTMOD", name="Test Module", primary_axes=[5])
        patient = make_patient(legacy_id="TEST-080")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_5=80)
        result = calculate_tspi_analysis(record)
        codes = [m["code"] for m in result["recommended_modules"]]
        self.assertIn("TESTMOD", codes)


class SafetyLayer1Tests(TestCase):
    """roadmap 3-C: contraindication-aware intervention_eligibility, grounded in real module
    data (contraindications) plus evidence already computed in the ledger — no fabricated rule."""

    def test_cancer_contraindication_holds_when_oncology_axis_assessed(self):
        ModuleRegistryEntry.objects.all().delete()
        ModuleRegistryEntry.objects.create(
            code="ONCOMOD", name="Onco Module", primary_axes=[37],
            contraindications=["Hormone-sensitive cancer"]
        )
        patient = make_patient(legacy_id="TEST-090")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_37=60)
        result = calculate_tspi_analysis(record)
        entries = {e["intervention_id"]: e for e in result["safety_gate"]["intervention_eligibility"]}
        self.assertEqual(entries["ONCOMOD"]["status"], "HOLD")
        self.assertEqual(entries["ONCOMOD"]["reason_rule_id"], "MODULE_CONTRAINDICATION_ONCOLOGY")

    def test_unverifiable_contraindication_is_insufficient_data(self):
        ModuleRegistryEntry.objects.all().delete()
        ModuleRegistryEntry.objects.create(
            code="PREGMOD", name="Preg Module", primary_axes=[31],
            contraindications=["Pregnancy"]
        )
        patient = make_patient(legacy_id="TEST-091")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_31=70)
        result = calculate_tspi_analysis(record)
        entries = {e["intervention_id"]: e for e in result["safety_gate"]["intervention_eligibility"]}
        self.assertEqual(entries["PREGMOD"]["status"], "INSUFFICIENT_DATA")


class SafetyLayer2Tests(TestCase):
    """roadmap 3-D: overlapping target axis among simultaneously-recommended modules —
    a structural signal only, not a fabricated pharmacological interaction claim."""

    def test_two_modules_same_axis_flagged(self):
        ModuleRegistryEntry.objects.all().delete()
        ModuleRegistryEntry.objects.create(code="MODA", name="Module A", primary_axes=[5])
        ModuleRegistryEntry.objects.create(code="MODB", name="Module B", primary_axes=[5])
        patient = make_patient(legacy_id="TEST-092")
        record = PatientBiologicalRecord.objects.create(patient=patient, axis_5=80)
        result = calculate_tspi_analysis(record)
        overlap = result["safety_gate"]["regimen_overlap"]
        axis5_entries = [o for o in overlap if o["axis_code"] == "A5"]
        self.assertEqual(len(axis5_entries), 1)
        self.assertEqual(set(axis5_entries[0]["modules"]), {"MODA", "MODB"})


class ModuleRegistryApprovalEndpointTests(TestCase):
    """roadmap 3-E: approving a module updates mapping_status with an audit trail via API."""

    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="doctor4", password="x", is_staff=True)
        self.client.force_authenticate(user=user)

    def test_patch_approves_module(self):
        entry = ModuleRegistryEntry.objects.create(code="APPROVEME", name="Approve Me", primary_axes=[1])
        res = self.client.patch(
            f"/api/module-registry/{entry.id}/",
            {"mapping_status": "APPROVED", "approved_by": "dr.test"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.mapping_status, "APPROVED")
        self.assertEqual(entry.approved_by, "dr.test")
