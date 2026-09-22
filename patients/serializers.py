from rest_framework import serializers
from patients.models import Patient, PatientBiologicalRecord, AuditLog, ClinicalKnowledge, TspiSettings, PatientHistory, Appointment, PdpaConsent, AutomationTask, ClinicalKnowledgeSegment, TSPIBrainTrainingLog, ModuleRegistryEntry

class PatientBiologicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientBiologicalRecord
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    # ดึงประวัติข้อมูลบันทึกชีวภาพแนบไปด้วย เรียงลำดับจากล่าสุด
    axes_records = serializers.SerializerMethodField()
    axes = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    idCard = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    sex = serializers.SerializerMethodField()
    disease = serializers.SerializerMethodField()
    allergy = serializers.SerializerMethodField()
    bmi_val = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()
    blood_pressure = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

    def get_axes_records(self, obj):
        records = obj.axes_records.all().order_by('-record_date')
        return PatientBiologicalRecordSerializer(records, many=True).data

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_idCard(self, obj):
        return obj.id_card

    def get_birthday(self, obj):
        if obj.birth_date:
            # Django normally returns a date instance, but a newly-created
            # model can still hold the JSON request string until it is
            # reloaded from PostgreSQL.  Do not turn a successful
            # registration into a 500 while serializing that response.
            if isinstance(obj.birth_date, str):
                return obj.birth_date
            return obj.birth_date.strftime("%Y-%m-%d")
        return None

    def get_sex(self, obj):
        if obj.gender == 'M':
            return 'ชาย'
        elif obj.gender == 'F':
            return 'หญิง'
        return 'อื่นๆ'

    def get_disease(self, obj):
        if obj.present_illness:
            return obj.present_illness
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('disease') or obj.extra_data.get('detail_disease')
        return None

    def get_allergy(self, obj):
        if obj.drug_allergy:
            return obj.drug_allergy
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('drug_allergy')
        return None

    def get_bmi_val(self, obj):
        if obj.extra_data and isinstance(obj.extra_data, dict):
            bmi = obj.extra_data.get('bmi') or obj.extra_data.get('bmi_val')
            if bmi:
                return bmi
            try:
                w = float(obj.extra_data.get('weight', 0))
                h = float(obj.extra_data.get('height', 0)) / 100.0
                if h > 0:
                    return round(w / (h * h), 1)
            except:
                pass
        return None

    def get_weight(self, obj):
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('weight')
        return None

    def get_height(self, obj):
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('height')
        return None

    def get_blood_pressure(self, obj):
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('blood_pressure') or obj.extra_data.get('bp')
        return None

    def get_progress(self, obj):
        if obj.extra_data and isinstance(obj.extra_data, dict):
            return obj.extra_data.get('progress') or 0
        return 0

    def get_age(self, obj):
        return obj.age

    def get_axes(self, obj):
        # No default 50: an unassessed axis must read as NOT_ASSESSED, never as a fabricated
        # mid-range score (ans.txt "no default 50" rule — see tspi_engine.py calculate_tspi_analysis).
        latest_record = obj.axes_records.all().order_by('-record_date').first()
        if not latest_record:
            return {
                f"AXIS_{i}": {"score": None, "axisId": i, "status": "NOT_ASSESSED"}
                for i in range(1, 40)
            }

        axes_dict = {}
        for i in range(1, 40):
            score = getattr(latest_record, f"axis_{i}", None)
            if score == 50:
                score = None
            axes_dict[f"AXIS_{i}"] = {
                "score": score,
                "axisId": i,
                "axisName": f"Axis {i}",
                "status": "NOT_ASSESSED" if score is None else "ASSESSED",
                "updatedAt": latest_record.record_date.isoformat() if latest_record.record_date else None
            }
        return axes_dict


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'

class ClinicalKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalKnowledge
        fields = '__all__'

class TspiSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TspiSettings
        fields = '__all__'


class PatientHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientHistory
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'


class PdpaConsentSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = PdpaConsent
        fields = ['id', 'username', 'terms_version', 'consent_treatment', 'consent_marketing', 'consent_research', 'ip_address', 'user_agent', 'signed_at']
        read_only_fields = ['id', 'username', 'ip_address', 'user_agent', 'signed_at']


class AutomationTaskSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='task_type')
    patientName = serializers.CharField(source='patient_name')
    patientHn = serializers.CharField(source='patient_hn', required=False, allow_null=True, allow_blank=True)
    scheduledFor = serializers.DateTimeField(source='scheduled_for')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = AutomationTask
        fields = ['id', 'type', 'status', 'patientName', 'patientHn', 'scheduledFor', 'createdAt', 'logs']


class ClinicalKnowledgeSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalKnowledgeSegment
        fields = ['id', 'title', 'content', 'source', 'axis_id', 'embedding', 'created_at']
        read_only_fields = ['id', 'embedding', 'created_at']


class TSPIBrainTrainingLogSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_hn = serializers.SerializerMethodField()

    class Meta:
        model = TSPIBrainTrainingLog
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return "N/A"

    def get_patient_hn(self, obj):
        if obj.patient:
            return obj.patient.hn
        return "N/A"


class ModuleRegistryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleRegistryEntry
        fields = '__all__'
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']

