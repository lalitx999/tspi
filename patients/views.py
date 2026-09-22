from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from patients.models import Patient, PatientBiologicalRecord, AuditLog, ClinicalKnowledge, TspiSettings, PatientHistory, Appointment, PdpaConsent, AutomationTask
from patients.permissions import IsClinicalStaffOrOwner
from patients.serializers import (
    PatientSerializer, 
    PatientBiologicalRecordSerializer, 
    AuditLogSerializer, 
    ClinicalKnowledgeSerializer,
    TspiSettingsSerializer,
    PatientHistorySerializer,
    AppointmentSerializer,
    PdpaConsentSerializer,
    AutomationTaskSerializer
)

from rest_framework.pagination import PageNumberPagination

class DynamicPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('no_pagination') == 'true' or request.query_params.get('page_size') == 'no':
            return None
        return super().paginate_queryset(queryset, request, view)


class PatientViewSet(viewsets.ModelViewSet):
    pagination_class = DynamicPageNumberPagination
    serializer_class = PatientSerializer
    permission_classes = [IsClinicalStaffOrOwner]

    def get_queryset(self):
        user = self.request.user
        if Patient.objects.count() == 0:
            try:
                from django.core.management import call_command
                call_command('import_patients_pg')
            except Exception as import_err:
                print("⚠️ Auto import patients error:", import_err)

        if user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists():
            return Patient.objects.all()
        return Patient.objects.filter(id_card=user.username)

    @action(detail=False, methods=['get'], url_path='list-lightweight')
    def list_lightweight(self, request):
        """
        Fast optimized endpoint to list minimal patient data (id, fname, lname, hn, gender, birth_date) for dropdowns and selectors.
        Prevents N+1 database queries of detailed nested structures.
        """
        patients = self.get_queryset().only('id', 'first_name', 'last_name', 'hn', 'gender', 'birth_date')
        data = [{
            'id': p.id,
            'fname': p.first_name,
            'lname': p.last_name,
            'hn': p.hn,
            'gender': 'male' if p.gender == 'M' else 'female' if p.gender == 'F' else 'other' if p.gender == 'O' else None,
            'age': p.age
        } for p in patients]
        return Response(data)

    @action(detail=False, methods=['get'], url_path='all-lab-results')
    def all_lab_results(self, request):
        """
        Fast optimized database lookup to compile EMR lab report entries across all patients.
        Avoids client-side iteration and reduces payload size.
        """
        patients = self.get_queryset().filter(extra_data__has_key='lab_results')
        all_results = []
        for p in patients:
            lab_results = p.extra_data.get('lab_results', [])
            if isinstance(lab_results, list):
                for lr in lab_results:
                    lr['patientId'] = p.id
                    lr['patientName'] = f"{p.first_name} {p.last_name}".strip()
                    lr['patientHn'] = p.hn
                    all_results.append(lr)
        return Response(all_results)

    def perform_update(self, serializer):
        instance = serializer.save()
        request_data = self.request.data

        # Intercept and log EMR Lab result updates for patient trend charts
        if 'labs' in request_data:
            labs_data = request_data['labs']
            if isinstance(labs_data, dict):
                fbs_v = labs_data.get('FBS') or labs_data.get('fbs')
                hba1c_v = labs_data.get('HbA1c') or labs_data.get('hba1c')
                ldl_v = labs_data.get('LDL') or labs_data.get('ldl')
                crp_v = labs_data.get('CRP') or labs_data.get('crp')
                
                if any(v is not None for v in [fbs_v, hba1c_v, ldl_v, crp_v]):
                    from patients.models import PatientHistory
                    PatientHistory.objects.create(
                        patient=instance,
                        type="Lab Result",
                        title="บันทึกผลแล็บทางการแพทย์ (แพทย์)",
                        content=f"ผลแล็บได้รับการอัปเดตเข้าระบบ EMR:\n- น้ำตาลในเลือด FBS: {fbs_v if fbs_v is not None else '--'} mg/dL\n- น้ำตาลสะสม HbA1c: {hba1c_v if hba1c_v is not None else '--'} %\n- ไขมันเลว LDL: {ldl_v if ldl_v is not None else '--'} mg/dL\n- ดัชนีการอักเสบ CRP: {crp_v if crp_v is not None else '--'} mg/L"
                    )

        if 'axes' in request_data:
            axes_data = request_data['axes']
            if isinstance(axes_data, dict):
                record = PatientBiologicalRecord(patient=instance)
                latest = instance.axes_records.all().order_by('-record_date').first()
                for i in range(1, 40):
                    axis_key = f"AXIS_{i}"
                    axis_payload = axes_data.get(axis_key) or axes_data.get(str(i))
                    score = None
                    if isinstance(axis_payload, dict):
                        score = axis_payload.get('score')
                    elif isinstance(axis_payload, (int, float)):
                        score = axis_payload
                    if score is not None:
                        setattr(record, f"axis_{i}", int(score))
                    elif latest:
                        setattr(record, f"axis_{i}", getattr(latest, f"axis_{i}"))
                    else:
                        setattr(record, f"axis_{i}", None)
                record.save()
                print(f"📈 Synced 39 Axes to PostgreSQL for patient HN: {instance.hn}")

        extra_fields = {}
        model_fields = [f.name for f in instance._meta.get_fields()]
        for key, value in request_data.items():
            if key not in model_fields and key != 'axes':
                extra_fields[key] = value
        if extra_fields:
            if not instance.extra_data:
                instance.extra_data = {}
            instance.extra_data.update(extra_fields)
            instance.save()

    @action(detail=True, methods=['get'], url_path='tspi-analysis')
    def tspi_analysis(self, request, pk=None):
        """Return the immutable ledger selected for this patient; never recompute here."""
        patient = self.get_object()
        requested_analysis_id = request.query_params.get("analysis_record_id")
        analysis_records = patient.analysis_records
        analysis_record = (
            analysis_records.filter(id=requested_analysis_id).first()
            if requested_analysis_id
            else analysis_records.order_by("-created_at").first()
        )
        if not analysis_record:
            return Response(
                {
                    "error": "ไม่พบ Analysis Record ที่ผ่านการตรวจสอบ กรุณารันการวิเคราะห์ก่อน",
                    "required_action": "RUN_VERIFIED_ANALYSIS",
                },
                status=status.HTTP_409_CONFLICT,
            )

        result = analysis_record.ledger.copy()
        result["patient_id"] = patient.id
        result["patient_name"] = f"{patient.first_name} {patient.last_name}"
        result["analysis_record_id"] = analysis_record.id

        if result.get("analysis_state") == "BLOCKED_DATA_RECONCILIATION":
            return Response(
                {
                    "analysis_record_id": analysis_record.id,
                    "patient_id": patient.id,
                    "analysis_state": "BLOCKED_DATA_RECONCILIATION",
                    "allowed_output": "DATA_RECONCILIATION_REPORT_ONLY",
                    "identity_validation": result.get("identity_validation", {}),
                    "conflict_details": result.get("identity_validation", {}).get("conflict_details", []),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result)

    @action(detail=True, methods=['get'], url_path='analysis-records/(?P<record_id>[^/.]+)')
    def get_analysis_record(self, request, pk=None, record_id=None):
        """
        Fetch one immutable AnalysisRecord ledger by id, so report generation / PDF export
        can render from the exact same analysis instead of recomputing (ans.txt problem #9).
        """
        patient = self.get_object()
        record = patient.analysis_records.filter(id=record_id).first()
        if not record:
            return Response({"error": "Analysis record not found"}, status=404)
        return Response({
            "analysis_record_id": record.id,
            "patient_id": patient.id,
            "created_at": record.created_at.isoformat(),
            "framework_version": record.framework_version,
            "is_valid": record.is_valid,
            "invariant_violations": record.invariant_violations,
            "analysis": record.ledger,
        })

    @action(detail=True, methods=['post'], url_path='calculate-precision-medicine')
    def calculate_precision_medicine(self, request, pk=None):
        import os
        import json
        import urllib.request
        
        patient = self.get_object()
        
        symptoms = request.data.get('symptoms', '')
        history = request.data.get('history', '')
        fbs = request.data.get('fbs', '')
        hba1c = request.data.get('hba1c', '')
        doppler = request.data.get('doppler', '')
        other_labs = request.data.get('otherLabs', '')
        bowel_status = request.data.get('bowelStatus', 'normal')
        
        # P0-1 Identity Validator Gate — check demographics and source
        # ownership before any biological record or AnalysisRecord is created.
        from .tspi_engine import validate_patient_identity
        identity_input = {
            "age": getattr(patient, "age", None),
            "gender": getattr(patient, "gender", None),
            "hn": getattr(patient, "hn", None),
            "symptoms": symptoms,
            "history": history,
            "soap_age": request.data.get("soap_age"),
            "soap_gender": request.data.get("soap_gender"),
            "soap_hn": request.data.get("soap_hn"),
            "lab_owner_hn": request.data.get("lab_owner_hn"),
            "lab_source_record_id": request.data.get("lab_source_record_id"),
            "source_document_owner_hn": request.data.get("source_document_owner_hn"),
            "source_document_id": request.data.get("source_document_id"),
            "clinical_history_owner_hn": request.data.get("clinical_history_owner_hn"),
            "clinical_history_source_id": request.data.get("clinical_history_source_id"),
            "source_ownership": request.data.get("source_ownership", []),
            "omics_clinical_question": request.data.get("omics_clinical_question"),
            "omics_actionability_plan": request.data.get("omics_actionability_plan"),
            "omics_informed_consent": request.data.get("omics_informed_consent"),
        }
        identity_check = validate_patient_identity(identity_input)
        if identity_check.get("identity_validation_status") == "CONFLICT":
            return Response({
                "identity_validation": identity_check,
                "analysis_state": "BLOCKED_DATA_RECONCILIATION",
                "allowed_output": "DATA_RECONCILIATION_REPORT_ONLY",
                "error": "Patient identity data conflict detected. Biological analysis blocked until data reconciliation.",
                "conflict_details": identity_check.get("conflict_details", [])
            }, status=400)

        # 1. Retrieve or create latest biological record
        latest_record = patient.axes_records.all().order_by('-record_date').first()
        
        def safe_max(a, b):
            if a is None:
                return b
            if b is None:
                return a
            return max(a, b)

        # Extract previous axis scores (default to None if none)
        updated_axes = {}
        for i in range(1, 40):
            val = getattr(latest_record, f"axis_{i}", None) if latest_record else None
            if val == 50:
                val = None
            updated_axes[i] = val


        # 1.5. TSPI Brain Local Self-Learning Prediction Branch
        use_brain_model = request.data.get('use_brain_model', False)
        brain_predicted = False
        if use_brain_model:
            import os
            import json
            tspi_data_dir = getattr(settings, 'TSPI_DATA_DIR', os.path.join(settings.BASE_DIR.parent, 'data'))
            weights_path = str(tspi_data_dir / "tspi_brain_weights.json")
            if os.path.exists(weights_path):
                try:
                    with open(weights_path, "r", encoding="utf-8") as f:
                        weights = json.load(f)
                    
                    # Extract lab values (parse from request or otherLabs)
                    simulated_labs = {
                        "fbs": fbs,
                        "hba1c": hba1c,
                        "crp": request.data.get("crp", ""),
                        "ldl": request.data.get("ldl", ""),
                        "alt": request.data.get("alt", ""),
                        "ggt": request.data.get("ggt", ""),
                    }
                    if other_labs:
                        for line in other_labs.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                simulated_labs[k.strip().lower()] = v.strip()

                    # Extract database values as fallback if empty
                    db_labs = patient.labs if isinstance(patient.labs, dict) else {}
                    
                    def get_float_val(key, fallback):
                        val = simulated_labs.get(key)
                        if val in (None, ""):
                            val = db_labs.get(key) or db_labs.get(key.upper())
                        if val in (None, ""):
                            if key == "fbs": val = db_labs.get("Fasting Glucose") or db_labs.get("fasting_glucose") or db_labs.get("FBS")
                            elif key == "crp": val = db_labs.get("hsCRP") or db_labs.get("hscrp") or db_labs.get("CRP") or db_labs.get("Crp")
                            elif key == "ldl": val = db_labs.get("LDL Cholesterol") or db_labs.get("cholesterol_ldl") or db_labs.get("LDL")
                            elif key == "alt": val = db_labs.get("sgpt") or db_labs.get("SGPT") or db_labs.get("ALT")
                            elif key == "ggt": val = db_labs.get("GGT")
                        
                        try:
                            if val not in (None, ""):
                                return float(val)
                        except ValueError:
                            pass
                        return fallback

                    fbs_v = get_float_val("fbs", 90.0)
                    hba1c_v = get_float_val("hba1c", 5.5)
                    crp_v = get_float_val("crp", 0.5)
                    ldl_v = get_float_val("ldl", 110.0)
                    alt_v = get_float_val("alt", 30.0)
                    ggt_v = get_float_val("ggt", 35.0)

                    # Compute outputs: score_i = bias_i + fbs*coef_fbs_i + ...
                    bias = weights["bias"]
                    coefs = weights["coefficients"]
                    
                    for i in range(1, 40):
                        idx = i - 1
                        pred_score = (
                            bias[idx] +
                            fbs_v * coefs["fbs"][idx] +
                            hba1c_v * coefs["hba1c"][idx] +
                            crp_v * coefs["crp"][idx] +
                            ldl_v * coefs["ldl"][idx] +
                            alt_v * coefs["alt"][idx] +
                            ggt_v * coefs["ggt"][idx]
                        )
                        updated_axes[i] = int(max(0, min(100, round(pred_score))))
                    
                    brain_predicted = True
                except Exception as brain_err:
                    print("⚠️ TSPI Brain prediction failed, falling back to deterministic rules:", brain_err)

        # 2. Deterministic Systemic Scoring Logic based on Biomarkers (Only run if Brain didn't predict)
        mentzer_index = None
        if not brain_predicted:
            det_labs = {
                "fbs": fbs,
                "hba1c": hba1c,
                "crp": request.data.get("crp", ""),
                "ldl": request.data.get("ldl", ""),
                "alt": request.data.get("alt", ""),
                "ggt": request.data.get("ggt", ""),
            }
            if other_labs:
                for line in other_labs.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        det_labs[k.strip().lower()] = v.strip()
            
            db_labs = patient.labs if isinstance(patient.labs, dict) else {}
            def get_det_val(key):
                val = det_labs.get(key)
                if val in (None, ""):
                    val = db_labs.get(key) or db_labs.get(key.upper())
                if val in (None, ""):
                    if key == "fbs": val = db_labs.get("Fasting Glucose") or db_labs.get("fasting_glucose") or db_labs.get("FBS")
                    elif key == "crp": val = db_labs.get("hsCRP") or db_labs.get("hscrp") or db_labs.get("CRP") or db_labs.get("Crp")
                    elif key == "ldl": val = db_labs.get("LDL Cholesterol") or db_labs.get("cholesterol_ldl") or db_labs.get("LDL")
                    elif key == "alt": val = db_labs.get("sgpt") or db_labs.get("SGPT") or db_labs.get("ALT")
                    elif key == "ggt": val = db_labs.get("GGT")
                    elif key == "hb": val = db_labs.get("HGB") or db_labs.get("Hb") or db_labs.get("Hemoglobin") or db_labs.get("hgb")
                    elif key == "hct": val = db_labs.get("HCT") or db_labs.get("Hct") or db_labs.get("Hematocrit") or db_labs.get("hct")
                    elif key == "mcv": val = db_labs.get("MCV") or db_labs.get("Mcv") or db_labs.get("mcv")
                    elif key == "rbc": val = db_labs.get("RBC") or db_labs.get("Rbc") or db_labs.get("Red Blood Cell") or db_labs.get("rbc")
                try:
                    if val not in (None, ""):
                        return float(val)
                except ValueError:
                    pass
                return None

            fbs_val = get_det_val("fbs")
            hba1c_val = get_det_val("hba1c")
            hb_val = get_det_val("hb")
            hct_val = get_det_val("hct")
            mcv_val = get_det_val("mcv")
            rbc_val = get_det_val("rbc")

            mentzer_index = None
            if mcv_val is not None and rbc_val is not None and rbc_val > 0:
                mentzer_index = round(mcv_val / rbc_val, 2)

            # P1-D: every marker->axis assignment below records which entry of
            # tspi_engine.MARKER_AXIS_RELATIONS justified it, so the response can show *why*
            # each axis got touched (relation type) instead of an unlabelled if/elif.
            from .tspi_engine import MARKER_AXIS_RELATIONS
            marker_provenance = []

            def record_provenance(marker_key, raw_value):
                for rel in MARKER_AXIS_RELATIONS.get(marker_key, []):
                    marker_provenance.append({**rel, "marker": marker_key, "raw_value": raw_value})

            # 🧪 Fasting Blood Sugar (FBS) -> Glycemic (5), Glycation (27)
            if fbs_val is not None:
                if fbs_val > 125:
                    updated_axes[5] = safe_max(updated_axes[5], 85)
                    updated_axes[27] = safe_max(updated_axes[27], 70)
                    record_provenance("fbs_high", fbs_val)
                elif fbs_val > 100:
                    updated_axes[5] = safe_max(updated_axes[5], 65)
                    record_provenance("fbs_prediabetic", fbs_val)
                elif fbs_val < 70:
                    updated_axes[5] = safe_max(updated_axes[5], 60)
                    record_provenance("fbs_low", fbs_val)

            # 🧪 HbA1c -> Glycemic (5), Glycation (27)
            if hba1c_val is not None:
                if hba1c_val > 6.5:
                    updated_axes[5] = safe_max(updated_axes[5], 85)
                    updated_axes[27] = safe_max(updated_axes[27], 70)
                    record_provenance("hba1c_high", hba1c_val)
                elif hba1c_val > 5.7:
                    updated_axes[5] = safe_max(updated_axes[5], 65)
                    record_provenance("hba1c_prediabetic", hba1c_val)

            # 🧪 Hematology (Anemia) -> Stem Cell & Hematopoiesis (26), Inflammatory Load (1)
            if hb_val is not None or hct_val is not None or mcv_val is not None:
                is_anemic = False
                if hb_val is not None and hb_val < 12.0:
                    is_anemic = True
                if hct_val is not None and hct_val < 36.0:
                    is_anemic = True
                if mcv_val is not None and mcv_val < 80.0:
                    is_anemic = True

                if is_anemic:
                    updated_axes[26] = safe_max(updated_axes[26], 85)
                    updated_axes[1] = safe_max(updated_axes[1], 65)
                    record_provenance("anemia", {"hb": hb_val, "hct": hct_val, "mcv": mcv_val})

            # 🧪 Doppler Assessment -> Endothelial (20), Microvascular (21), Hemodynamics (23)
            if doppler:
                doppler_lower = doppler.lower()
                if any(x in doppler_lower for x in ["plaque", "stenosis", "calcify", "calcification", "block", "narrow", "athero"]):
                    updated_axes[20] = safe_max(updated_axes[20], 80)
                    updated_axes[21] = safe_max(updated_axes[21], 80)
                    updated_axes[23] = safe_max(updated_axes[23], 85)
                    record_provenance("doppler_atherosclerotic", doppler)

            # 🦠 Symptoms extraction (Thai & English keyword mapping to Systems)
            symptoms_lower = symptoms.lower()
            # Tiredness/Fatigue -> Mitochondrial (8), Adrenal (33)
            if any(x in symptoms_lower for x in ["เหนื่อย", "เพลีย", "fatigue", "tired", "weak", "ไม่มีแรง"]):
                updated_axes[8] = safe_max(updated_axes[8], 75)
                updated_axes[33] = safe_max(updated_axes[33], 75)
                record_provenance("symptom_fatigue", symptoms)
            # Constipation/Gut issues -> Digestive (16), Microbiome (17), Colon Biofilm (19)
            if any(x in symptoms_lower for x in ["ท้องผูก", "constipat", "ถ่ายยาก", "อืด", "เหม็น"]):
                updated_axes[16] = safe_max(updated_axes[16], 70)
                updated_axes[17] = safe_max(updated_axes[17], 75)
                updated_axes[19] = safe_max(updated_axes[19], 70)
                record_provenance("symptom_constipation", symptoms)
            # Sleep issues / Stress -> Neuro-Sleep-Stress (34)
            if any(x in symptoms_lower for x in ["นอนไม่หลับ", "insomnia", "เครียด", "stress", "กังวล", "panic"]):
                updated_axes[34] = safe_max(updated_axes[34], 75)
                record_provenance("symptom_sleep_stress", symptoms)
            # Joint/Muscle pain -> Inflammation (1), Muscle Turnover (28), Connective Tissue (30)
            if any(x in symptoms_lower for x in ["ปวดข้อ", "อักเสบ", "inflam", "joint pain", "ปวดเมื่อย", "ปวดหลัง"]):
                updated_axes[1] = safe_max(updated_axes[1], 75)
                updated_axes[28] = safe_max(updated_axes[28], 70)
                updated_axes[30] = safe_max(updated_axes[30], 75)
                record_provenance("symptom_joint_pain", symptoms)
        else:
            marker_provenance = []

        # Create new record in Django PostgreSQL EMR
        from patients.models import PatientBiologicalRecord
        new_record = PatientBiologicalRecord(patient=patient)
        for i in range(1, 40):
            setattr(new_record, f"axis_{i}", updated_axes[i])
        new_record.save()

        # Run scoring mechanics via tspi_engine.py
        from .tspi_engine import calculate_tspi_analysis
        tspi_result = calculate_tspi_analysis(
            new_record,
            bowel_status=bowel_status,
            mentzer_index=mentzer_index,
            patient_data=identity_input,
        )
        # P1-D: attach marker->axis provenance to the persisted ledger too, not just the
        # immediate response, so it stays auditable alongside the AnalysisRecord it belongs to.
        tspi_result["marker_provenance"] = marker_provenance

        # Persist ONE immutable AnalysisRecord for this calculation (ans.txt problem #9 —
        # "หนึ่ง analysis record — หลาย views"). Physician/Patient/Multi-Omics report editions
        # generated later reference this same analysis_record_id instead of each recomputing
        # or caching their own copy, so they cannot silently diverge from one another.
        import hashlib
        from .models import AnalysisRecord
        from django.utils import timezone

        inputs_payload = json.dumps(
            {
                "axes": updated_axes,
                "bowel_status": bowel_status,
                "mentzer_index": mentzer_index,
                "source_ownership": identity_input["source_ownership"],
                "lab_owner_hn": identity_input["lab_owner_hn"],
                "source_document_owner_hn": identity_input["source_document_owner_hn"],
                "clinical_history_owner_hn": identity_input["clinical_history_owner_hn"],
            },
            sort_keys=True, default=str
        )
        inputs_hash = hashlib.sha256(inputs_payload.encode("utf-8")).hexdigest()

        analysis_record = AnalysisRecord.objects.filter(
            patient=patient, inputs_hash=inputs_hash, created_at__date=timezone.now().date()
        ).order_by('-created_at').first()
        if analysis_record is None:
            analysis_record = AnalysisRecord.objects.create(
                patient=patient,
                source_record=new_record,
                framework_version=tspi_result.get("framework_version", "39-axis-master-260715"),
                inputs_hash=inputs_hash,
                ledger=tspi_result,
                is_valid=tspi_result.get("is_valid", True),
                invariant_violations=tspi_result.get("invariant_violations", []),
                identity_snapshot=tspi_result.get("identity_validation", {}),
                evidence_provenance={
                    "source_ownership": identity_input["source_ownership"],
                    "lab_source_record_id": identity_input["lab_source_record_id"],
                    "source_document_id": identity_input["source_document_id"],
                    "clinical_history_source_id": identity_input["clinical_history_source_id"],
                    "marker_provenance": marker_provenance,
                },
                registry_versions={
                    "canonical_registry": tspi_result.get("canonical_registry", {}),
                    "framework_version": tspi_result.get("framework_version"),
                    "module_registry": tspi_result.get("module_registry_status", {}),
                    "network_registry": tspi_result.get("network_registry", {}),
                },
                created_by=request.user if request.user.is_authenticated else None,
            )

        # 2.5 Save timeline entry in patient_history for real EMR tracking
        from .models import PatientHistory
        PatientHistory.objects.create(
            patient=patient,
            type="AI Assessment",
            title="การประเมินสรีรวิทยาและเวชศาสตร์แม่นยำ (TSPI Precision Engine)",
            content=f"ประเมินแกนชีวภาพ 39 แกนสำเร็จ\n- รหัสวิเคราะห์: AnalysisRecord #{analysis_record.id}\n- สภาพลำไส้: {bowel_status or 'ปกติ'}"
        )

        # 3. Call the Local Deterministic Clinical Report Generator in Python (Zero API dependency)
        from .local_report_generator import generate_local_precision_report
        
        # Parse labs passed from request or fall back
        simulated_labs = {
            "fbs": fbs,
            "hba1c": hba1c,
            "crp": request.data.get("crp", "1.0"),
            "ldl": request.data.get("ldl", "100"),
            "alt": request.data.get("alt", "30"),
            "ggt": request.data.get("ggt", "35"),
        }
        if other_labs:
            try:
                for line in other_labs.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        simulated_labs[k.strip().lower()] = v.strip()
            except Exception:
                pass

        insight_summary = generate_local_precision_report(patient, tspi_result, simulated_labs)

        # Save to EMR metadata
        if not patient.extra_data:
            patient.extra_data = {}
        patient.extra_data["latest_precision_insight"] = insight_summary
        patient.save()

        return Response({
            "success": True,
            "patient_id": patient.id,
            "calculated_scores": {f"AXIS_{i}": updated_axes[i] for i in range(1, 40)},
            "analysis": tspi_result,
            "analysis_record_id": analysis_record.id,
            "is_valid": tspi_result.get("is_valid", True),
            "invariant_violations": tspi_result.get("invariant_violations", []),
            "insight": insight_summary,
            "mentzer_index": mentzer_index,
            "marker_provenance": marker_provenance
        })

    @action(detail=False, methods=['get'], url_path='active-intake-sessions')
    def active_intake_sessions(self, request):
        patients = Patient.objects.exclude(extra_data__intake_sessions={})
        results = []
        for p in patients:
            if p.extra_data and 'intake_sessions' in p.extra_data:
                for sid, sess in p.extra_data['intake_sessions'].items():
                    if sess.get('status') == 'active':
                        name = f"{p.first_name or ''} {p.last_name or ''}".strip() or "ไม่ทราบชื่อคนไข้"
                        results.append({
                            'id': sid,
                            'patientId': p.id,
                            'name': name,
                            'hn': p.hn,
                            'status': sess.get('status', 'active'),
                            'aiActive': sess.get('aiActive', True),
                            'messages': sess.get('messages', [])
                        })
        return Response(results)

    @action(detail=True, methods=['post'], url_path='save-intake-message')
    def save_intake_message(self, request, pk=None):
        patient = self.get_object()
        session_id = request.data.get('session_id')
        message = request.data.get('message')
        system_message = request.data.get('system_message')
        ai_active = request.data.get('ai_active')
        
        if not session_id or not message:
            return Response({"error": "session_id and message are required"}, status=400)
            
        if not patient.extra_data:
            patient.extra_data = {}
            
        if 'intake_sessions' not in patient.extra_data:
            patient.extra_data['intake_sessions'] = {}
            
        sessions = patient.extra_data['intake_sessions']
        sess = sessions.get(session_id)
        if not sess:
            sess = {"status": "active", "aiActive": True, "messages": []}
            
        sess['messages'] = sess.get('messages', [])
        
        # Save system message first if provided (auto-intervention log)
        if system_message:
            sess['messages'].append(system_message)
            
        sess['messages'].append(message)
        
        if ai_active is not None:
            sess['aiActive'] = ai_active
            
        sessions[session_id] = sess
        patient.extra_data['intake_sessions'] = sessions
        patient.save()
        
        return Response({"success": True, "session": sess})

    @action(detail=True, methods=['post'], url_path='update-intake-status')
    def update_intake_status(self, request, pk=None):
        patient = self.get_object()
        session_id = request.data.get('session_id')
        ai_active = request.data.get('ai_active')
        
        if not session_id or ai_active is None:
            return Response({"error": "session_id and ai_active are required"}, status=400)
            
        if not patient.extra_data or 'intake_sessions' not in patient.extra_data:
            return Response({"error": "No sessions found"}, status=404)
            
        sessions = patient.extra_data['intake_sessions']
        sess = sessions.get(session_id)
        if not sess:
            return Response({"error": "Session not found"}, status=404)
            
        sess['aiActive'] = ai_active
        sessions[session_id] = sess
        patient.extra_data['intake_sessions'] = sessions
        patient.save()
        
        return Response({"success": True, "aiActive": sess['aiActive']})


class PatientBiologicalRecordViewSet(viewsets.ModelViewSet):
    pagination_class = DynamicPageNumberPagination
    serializer_class = PatientBiologicalRecordSerializer
    permission_classes = [IsClinicalStaffOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists():
            return PatientBiologicalRecord.objects.all()
        return PatientBiologicalRecord.objects.filter(patient__id_card=user.username)

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

class ClinicalKnowledgeViewSet(viewsets.ModelViewSet):
    queryset = ClinicalKnowledge.objects.all()
    serializer_class = ClinicalKnowledgeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TspiSettingsViewSet(viewsets.ModelViewSet):
    queryset = TspiSettings.objects.all()
    serializer_class = TspiSettingsSerializer
    lookup_field = 'setting_key'

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def retrieve(self, request, *args, **kwargs):
        setting_key = self.kwargs.get('setting_key')
        if setting_key == 'ai_settings':
            import os, json
            google_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
            groq_key = os.environ.get("GROQ_API_KEY", "")
            deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
            deepseek_key_v2 = os.environ.get("DEEPSEEK_API_KEY_V2", "") or deepseek_key
            
            val = {}
            try:
                instance = TspiSettings.objects.get(setting_key=setting_key)
                if instance.setting_value:
                    val = json.loads(instance.setting_value) if isinstance(instance.setting_value, str) else instance.setting_value
            except Exception:
                pass
                
            val["google_api_key"] = google_key
            val["groq_api_key"] = groq_key
            val["deepseek_api_key"] = deepseek_key
            val["deepseek_api_key_v2"] = deepseek_key_v2
            val["model"] = "gemini-2.5-flash"
            if "provider" not in val:
                val["provider"] = "gemini"
                
            return Response({
                "setting_key": setting_key,
                "setting_value": val,
                "category": "AI"
            })

        try:
            instance = TspiSettings.objects.get(setting_key=setting_key)
        except TspiSettings.DoesNotExist:
            return Response({
                "setting_key": setting_key,
                "setting_value": "{}",
                "category": "General"
            })
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        setting_key = self.kwargs.get('setting_key')
        setting_value = request.data.get('setting_value', '{}')
        category = request.data.get('category', 'General')
        
        instance, created = TspiSettings.objects.get_or_create(
            setting_key=setting_key,
            defaults={'setting_value': setting_value, 'category': category}
        )
        if not created:
            instance.setting_value = setting_value
            instance.category = category
            instance.save()
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PatientHistoryViewSet(viewsets.ModelViewSet):
    pagination_class = DynamicPageNumberPagination
    serializer_class = PatientHistorySerializer
    permission_classes = [IsClinicalStaffOrOwner]

    def get_queryset(self):
        user = self.request.user
        queryset = PatientHistory.objects.all()
        if not (user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists()):
            queryset = queryset.filter(patient__id_card=user.username)
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        return queryset

class AppointmentViewSet(viewsets.ModelViewSet):
    pagination_class = DynamicPageNumberPagination
    serializer_class = AppointmentSerializer
    permission_classes = [IsClinicalStaffOrOwner]

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.all()
        if not (user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists()):
            patient = Patient.objects.filter(id_card=user.username).first()
            if patient:
                from django.db.models import Q
                queryset = queryset.filter(Q(userid=patient.legacy_id) | Q(userid=patient.hn) | Q(userid=patient.id_card) | Q(userid=patient.phone))
            else:
                queryset = queryset.filter(userid=user.username)
        userid = self.request.query_params.get('user')
        if userid:
            queryset = queryset.filter(userid=userid)
        return queryset


from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import date

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """
    Get clinical stats for the Doctor Dashboard
    """
    total_patients = Patient.objects.count()
    
    # Urgent count
    urgent_cases = Patient.objects.filter(status__in=['ด่วน', 'เคสด่วน']).count()
    
    # Active appointments today
    today = date.today()
    active_now = Appointment.objects.filter(date_meet=today).count()
    
    total_axes = 39
    total_modules = 271
    
    completion_rate = "100%" if total_patients > 0 else "0%"
    
    return Response({
        "total_patients": total_patients,
        "urgent_cases": urgent_cases,
        "active_now": active_now,
        "completion_rate": completion_rate,
        "total_axes": total_axes,
        "total_modules": total_modules
    })


class PdpaConsentViewSet(viewsets.ModelViewSet):
    serializer_class = PdpaConsentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists():
            return PdpaConsent.objects.all()
        return PdpaConsent.objects.filter(user=user)

    def perform_create(self, serializer):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
            
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        serializer.save(user=self.request.user, ip_address=ip, user_agent=user_agent)


class AutomationTaskViewSet(viewsets.ModelViewSet):
    pagination_class = DynamicPageNumberPagination
    serializer_class = AutomationTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists():
            return AutomationTask.objects.all()
        
        patient = Patient.objects.filter(id_card=user.username).first()
        if patient:
            from django.db.models import Q
            return AutomationTask.objects.filter(Q(patient_hn=patient.hn) | Q(patient_name=patient.full_name))
        return AutomationTask.objects.none()

    @action(detail=False, methods=['post'], url_path='run-workers')
    def run_workers(self, request):
        from django.utils import timezone
        import urllib.request
        import json
        import os
        
        now = timezone.now()
        pending_tasks = AutomationTask.objects.filter(status='pending', scheduled_for__lte=now)
        
        processed_count = 0
        for task in pending_tasks:
            task.status = 'processing'
            task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] เริ่มต้นประมวลผลงานรันคิวอัตโนมัติ...")
            task.save()
            
            try:
                # ค้นหาข้อมูลคนไข้ใน PostgreSQL EMR
                from patients.models import Patient
                patient = None
                if task.patient_hn:
                    patient = Patient.objects.filter(hn=task.patient_hn).first()
                if not patient and task.patient_name:
                    patient = Patient.objects.filter(full_name=task.patient_name).first()

                if patient:
                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ตรวจพบข้อมูลเวชระเบียนคนไข้ HN: {patient.hn} | ชื่อ: {patient.full_name}")
                else:
                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ไม่พบข้อมูลคนไข้ในระบบ EMR ดำเนินการส่งแบบจำลองทั่วไป...")

                message_text = ""
                if task.task_type == 'PRE_VISIT_REMINDER':
                    message_text = f"สวัสดีครับคุณ {task.patient_name} ขอแจ้งเตือนนัดหมายตรวจล่วงหน้าของท่านในวันพรุ่งนี้ กรุณางดน้ำและอาหาร 8-12 ชั่วโมงก่อนตรวจด้วยครับ"
                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] จัดเตรียมข้อความแจ้งเตือนก่อนวันนัดหมาย")
                    
                elif task.task_type == 'NO_SHOW_CHECK':
                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] เริ่มตรวจสอบบันทึกการเข้าตรวจ EMR...")
                    from django.db.models import Q
                    appts = Appointment.objects.filter(
                        Q(userid=task.patient_hn) | Q(symptom__icontains=task.patient_name)
                    ).order_by('-date_meet')
                    
                    if appts.exists() and appts.first().status.lower() in ['pending', 'รอหมอ', 'รอดำเนินการ']:
                        task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ผลการตรวจสอบ: ตรวจพบนัดตกหล่น (ไม่เข้าเช็คอินเข้าพบแพทย์)")
                        message_text = f"สวัสดีครับคุณ {task.patient_name} เนื่องจากระบบตรวจพบนัดตกหล่นของท่านในวันนี้ สะดวกทำแบบสอบถามเลื่อนนัดหมายใหม่ไหมครับ?"
                    else:
                        task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ผลการตรวจสอบ: เข้าเช็คอินปกติหรือไม่มีนัดหมายตกหล่น")
                        task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] สิ้นสุดกระบวนการ (Triage Clean)")
                        
                elif task.task_type == 'FOLLOW_UP':
                    message_text = f"สวัสดีครับคุณ {task.patient_name} หลังจากเข้ารับยาสมุนไพรฟื้นฟูแล้ว อาการคัดกรองหรือคุณภาพชีวิตดีขึ้นไหมครับ?"
                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] จัดเตรียมข้อความส่งคำถามติดตามผลผ่าน LINE/FCM")
                
                # ส่งการแจ้งเตือนสองช่องทางขนานกัน (LINE OA & FCM Push)
                if message_text:
                    # 1. FCM Web Push Notification
                    fcm_token = patient.extra_data.get('fcm_token') if patient and patient.extra_data else None
                    if fcm_token:
                        fcm_url = "http://127.0.0.1:3000/api/ai/send-fcm-notification"
                        fcm_headers = {"Content-Type": "application/json"}
                        fcm_body = {
                            "token": fcm_token,
                            "title": "แจ้งเตือนระบบสุขภาพ EMR",
                            "body": message_text
                        }
                        try:
                            fcm_req = urllib.request.Request(
                                fcm_url,
                                data=json.dumps(fcm_body).encode('utf-8'),
                                headers=fcm_headers,
                                method='POST'
                            )
                            with urllib.request.urlopen(fcm_req, timeout=5) as fcm_res:
                                fcm_res_data = json.loads(fcm_res.read().decode('utf-8'))
                                if fcm_res_data.get('success'):
                                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ✅ ส่งข้อความ FCM Web Push เด้งแจ้งเตือนบนเบราว์เซอร์คนไข้สำเร็จ")
                                else:
                                    task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ❌ ส่ง FCM ล้มเหลว: {fcm_res_data.get('error')}")
                        except Exception as fcm_err:
                            # ในสภาวะไม่มี Node.js server รันอยู่ หรือไม่มี credentials ให้ทำแบบจำลองความคืบหน้า
                            task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ⚙️ จำลองระบบส่ง FCM: '{message_text}' ไปยังโทเค็น [{fcm_token[:15]}...]")
                    else:
                        task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ℹ️ ไม่พบ FCM Token ของคนไข้ในระบบ EMR (ข้าม Web Push)")

                    # 2. LINE OA Message Push
                    line_user_id = patient.line_user_id if patient else None
                    if line_user_id:
                        from patients.views_line import push_line_message
                        channel_access_token = os.environ.get("LINE_DOCTORPATT_CHANNEL_ACCESS_TOKEN", "")
                        if channel_access_token:
                            try:
                                push_line_message(
                                    line_user_id,
                                    [{"type": "text", "text": message_text}],
                                    channel_access_token
                                )
                                task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ✅ ส่งข้อความ Line Push Notification ไปยังแชทส่วนตัวของคนไข้สำเร็จ")
                            except Exception as line_err:
                                task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ❌ ส่ง LINE ล้มเหลว: {str(line_err)}")
                        else:
                            task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ⚙️ จำลองระบบส่ง LINE OA: '{message_text}' ไปยังแชทคนไข้ [{line_user_id[:10]}...]")
                    else:
                        task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ℹ️ ไม่พบบัญชี LINE ที่ผูกไว้ของคนไข้ในระบบ EMR (ข้าม LINE Push)")
                
                task.status = 'completed'
                task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] ดำเนินภารกิจคิวงานเสร็จสมบูรณ์เรียบร้อย")
            except Exception as ex:
                task.status = 'failed'
                task.logs.append(f"[{timezone.now().strftime('%H:%M:%S')}] 🚨 เกิดข้อขัดข้องระหว่างดำเนินงาน: {str(ex)}")
                
            task.save()
            processed_count += 1
            
        return Response({
            "success": True,
            "processed": processed_count,
            "message": f"Successfully simulated running {processed_count} automation tasks."
        })
