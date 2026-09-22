import uuid

from django.core.exceptions import ValidationError
from django.db import models

class Patient(models.Model):
    """คนไข้จาก MariaDB/PostgreSQL table `user`"""
    
    # Identity
    legacy_id = models.CharField(max_length=50, unique=True, db_index=True)
    hn = models.CharField(max_length=50, unique=True, null=True, blank=True)
    id_card = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    
    # Personal info
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=30, db_index=True)
    email = models.EmailField(blank=True, null=True)
    line_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    line_user_id = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    line_display_name = models.CharField(max_length=200, blank=True, null=True)
    line_picture_url = models.URLField(max_length=500, blank=True, null=True)
    intake_status = models.CharField(max_length=50, default='pending', db_index=True)
    
    # Demographics
    GENDER_CHOICES = [('M', 'ชาย'), ('F', 'หญิง'), ('O', 'อื่นๆ')]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    subdistrict = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    
    # Clinical status
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('medicine', 'รับยา'),
        ('urgent', 'ด่วน'),
        ('wait_doctor', 'รอหมอ'),
        ('died', 'เสียชีวิต'),
        ('delete', 'ลบ'),
    ]
    status = models.CharField(max_length=50, default='pending', db_index=True)
    
    # Intake
    chief_complaint = models.TextField(blank=True, null=True)
    present_illness = models.TextField(blank=True, null=True)
    past_history = models.TextField(blank=True, null=True)
    drug_allergy = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    
    # Multi-Omics & AI Data (แทนที่ Firestore)
    case_summary = models.TextField(blank=True, null=True)
    labs = models.JSONField(default=dict, blank=True)
    genomics = models.JSONField(default=dict, blank=True)
    microbiome = models.JSONField(default=dict, blank=True)
    proteomics = models.JSONField(default=dict, blank=True)
    
    # Extra legacy fields
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
        ]
        verbose_name = "คนไข้"
        verbose_name_plural = "คนไข้ทั้งหมด"
    
    def __str__(self):
        return f"{self.hn or self.legacy_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        from datetime import date
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class PatientBiologicalRecord(models.Model):
    """บันทึกคะแนนชีวภาพ 39 แกนของคนไข้"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='axes_records')
    record_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    # 39 axes
    axis_1 = models.IntegerField(null=True, blank=True, default=None)
    axis_2 = models.IntegerField(null=True, blank=True, default=None)
    axis_3 = models.IntegerField(null=True, blank=True, default=None)
    axis_4 = models.IntegerField(null=True, blank=True, default=None)
    axis_5 = models.IntegerField(null=True, blank=True, default=None)
    axis_6 = models.IntegerField(null=True, blank=True, default=None)
    axis_7 = models.IntegerField(null=True, blank=True, default=None)
    axis_8 = models.IntegerField(null=True, blank=True, default=None)
    axis_9 = models.IntegerField(null=True, blank=True, default=None)
    axis_10 = models.IntegerField(null=True, blank=True, default=None)
    axis_11 = models.IntegerField(null=True, blank=True, default=None)
    axis_12 = models.IntegerField(null=True, blank=True, default=None)
    axis_13 = models.IntegerField(null=True, blank=True, default=None)
    axis_14 = models.IntegerField(null=True, blank=True, default=None)
    axis_15 = models.IntegerField(null=True, blank=True, default=None)
    axis_16 = models.IntegerField(null=True, blank=True, default=None)
    axis_17 = models.IntegerField(null=True, blank=True, default=None)
    axis_18 = models.IntegerField(null=True, blank=True, default=None)
    axis_19 = models.IntegerField(null=True, blank=True, default=None)
    axis_20 = models.IntegerField(null=True, blank=True, default=None)
    axis_21 = models.IntegerField(null=True, blank=True, default=None)
    axis_22 = models.IntegerField(null=True, blank=True, default=None)
    axis_23 = models.IntegerField(null=True, blank=True, default=None)
    axis_24 = models.IntegerField(null=True, blank=True, default=None)
    axis_25 = models.IntegerField(null=True, blank=True, default=None)
    axis_26 = models.IntegerField(null=True, blank=True, default=None)
    axis_27 = models.IntegerField(null=True, blank=True, default=None)
    axis_28 = models.IntegerField(null=True, blank=True, default=None)
    axis_29 = models.IntegerField(null=True, blank=True, default=None)
    axis_30 = models.IntegerField(null=True, blank=True, default=None)
    axis_31 = models.IntegerField(null=True, blank=True, default=None)
    axis_32 = models.IntegerField(null=True, blank=True, default=None)
    axis_33 = models.IntegerField(null=True, blank=True, default=None)
    axis_34 = models.IntegerField(null=True, blank=True, default=None)
    axis_35 = models.IntegerField(null=True, blank=True, default=None)
    axis_36 = models.IntegerField(null=True, blank=True, default=None)
    axis_37 = models.IntegerField(null=True, blank=True, default=None)
    axis_38 = models.IntegerField(null=True, blank=True, default=None)
    axis_39 = models.IntegerField(null=True, blank=True, default=None)
    
    class Meta:
        db_table = 'patient_biological_records'
        ordering = ['-record_date']
        
    def __str__(self):
        return f"Record for {self.patient} on {self.record_date.strftime('%Y-%m-%d %H:%M')}"


class AnalysisRecord(models.Model):
    """
    Immutable snapshot of one calculate_tspi_analysis() run (the "ledger" — three_keys,
    nine_restoration_steps, thirty_nine_axes, safety_gate, network_registry, module_registry).
    Physician/Patient/Multi-Omics report editions all reference the same AnalysisRecord id
    instead of each recomputing/re-deriving the analysis independently (ans.txt problem #9:
    "หนึ่ง analysis record — หลาย views").
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='analysis_records')
    analysis_run_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    source_record = models.ForeignKey(
        PatientBiologicalRecord, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analysis_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    framework_version = models.CharField(max_length=50, default="39-axis-master-260715")
    inputs_hash = models.CharField(max_length=64, db_index=True)
    ledger = models.JSONField(default=dict)
    is_valid = models.BooleanField(default=True)
    invariant_violations = models.JSONField(default=list, blank=True)
    # Evidence and identity are persisted alongside the ledger, never inferred
    # from the current patient profile when a historical report is rendered.
    identity_snapshot = models.JSONField(default=dict, blank=True)
    evidence_provenance = models.JSONField(default=dict, blank=True)
    registry_versions = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_analysis_records'
    )

    class Meta:
        db_table = 'patient_analysis_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'inputs_hash']),
        ]

    def __str__(self):
        return f"AnalysisRecord {self.id} for {self.patient} at {self.created_at}"

    def save(self, *args, **kwargs):
        """AnalysisRecord is append-only; create a new run instead of overwriting facts."""
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("AnalysisRecord is immutable. Create a new analysis run instead of updating it.")
        return super().save(*args, **kwargs)


class AnalysisReportRelease(models.Model):
    """Append-only approval trail for one report edition of an immutable analysis run."""
    EDITION_CHOICES = [("PHYSICIAN", "Physician"), ("PATIENT", "Patient"), ("MULTI_OMICS", "Multi-Omics")]
    STATE_CHOICES = [
        ("AI_DRAFT", "AI Draft"),
        ("PHYSICIAN_REVIEWED", "Physician Reviewed"),
        ("PHYSICIAN_APPROVED", "Physician Approved"),
        ("PATIENT_RELEASED", "Patient Released"),
    ]
    analysis_record = models.ForeignKey(AnalysisRecord, on_delete=models.CASCADE, related_name="report_releases")
    edition = models.CharField(max_length=20, choices=EDITION_CHOICES)
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default="AI_DRAFT")
    note = models.TextField(blank=True)
    acted_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_analysis_report_releases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.analysis_record.analysis_run_id} {self.edition}: {self.state}"


class AxisScoringContract(models.Model):
    """Clinician-owned approval registry; no score rule is implied by code alone."""
    STATUS_CHOICES = [("DRAFT", "Draft"), ("PENDING_APPROVAL", "Pending approval"), ("APPROVED", "Approved"), ("RETIRED", "Retired")]
    axis_code = models.CharField(max_length=8, unique=True)
    rule_id = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=40)
    threshold_spec = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    approved_by = models.CharField(max_length=150, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tspi_axis_scoring_contracts"
        ordering = ["axis_code"]


class ModuleRegistryEntry(models.Model):
    """
    DB-backed TSPI Module Registry (ans.txt P0-4.11 / roadmap item 3-A) — replaces reading
    data/last_dta/TSPI Modules Master Data + Training_Pairs.json directly at request time so
    module approval has a real audit trail (mapping_status/approved_by/approved_at) instead of
    a value baked into a JSON file with no history of who changed it or when.
    """
    MAPPING_STATUS_CHOICES = [
        ("PROVISIONAL", "Provisional"),
        ("APPROVED", "Approved"),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=150, blank=True, null=True)
    primary_function = models.TextField(blank=True, null=True)
    mechanisms = models.JSONField(default=list, blank=True)
    primary_axes = models.JSONField(default=list, blank=True)
    primary_networks = models.JSONField(default=list, blank=True)
    clinical_indications = models.JSONField(default=list, blank=True)
    contraindications = models.JSONField(default=list, blank=True)
    synergy_with = models.JSONField(default=list, blank=True)
    antagonism_with = models.JSONField(default=list, blank=True)
    mapping_status = models.CharField(max_length=20, choices=MAPPING_STATUS_CHOICES, default="PROVISIONAL", db_index=True)
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    source_version = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tspi_module_registry'
        ordering = ['code']
        verbose_name = "TSPI Module Registry Entry"
        verbose_name_plural = "TSPI Module Registry Entries"

    def __str__(self):
        return f"{self.code} — {self.name} ({self.mapping_status})"


class AuditLog(models.Model):
    """บันทึกประวัติการเข้าถึงข้อมูลตาม พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล (PDPA)"""
    timestamp = models.DateTimeField(auto_now_add=True)
    actor_id = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    action = models.CharField(max_length=200)
    layer = models.CharField(max_length=10)
    client_ip = models.CharField(max_length=100, blank=True, null=True)
    governance_status = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'patient_audit_logs'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.actor_id} -> {self.action} on {self.target_id} at {self.timestamp}"


class ClinicalKnowledge(models.Model):
    """คลังความรู้เชิงคลินิกสำหรับระบบ RAG (แทนที่ Firestore knowledge_base)"""
    text = models.TextField()
    source = models.CharField(max_length=200)
    axis = models.CharField(max_length=100, default='General')
    type = models.CharField(max_length=100, default='clinical_guideline')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_knowledge'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source} - {self.axis}"


class TspiSettings(models.Model):
    """การตั้งค่าระบบ (เช่นการถ่วงน้ำหนักคะแนนแกนชีวภาพ แทนที่ Firestore settings)"""
    setting_key = models.CharField(unique=True, max_length=100)
    setting_value = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'tspi_settings'
        verbose_name = "การตั้งค่าระบบ"
        verbose_name_plural = "การตั้งค่าระบบทั้งหมด"

    def __str__(self):
        return f"{self.setting_key} ({self.category or 'General'})"


class Appointment(models.Model):
    """นัดหมายแพทย์คนไข้ (ผูกกับตารางเดิมที่มีอยู่แล้วใน PostgreSQL)"""
    appid = models.TextField(db_column='appID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.
    doctorid = models.TextField(db_column='doctorID')  # Field name made lowercase.
    date_meet = models.DateField()
    time_meet = models.TextField()
    time_id = models.IntegerField()
    date_at = models.DateTimeField()
    status = models.CharField(max_length=100)
    symptom = models.TextField()
    noti_1 = models.TextField()
    noti_7 = models.TextField()
    noti_now = models.TextField()

    class Meta:
        managed = False
        db_table = 'appointment'

    def __str__(self):
        return f"App: {self.appid} - User: {self.userid} on {self.date_meet}"


class PatientHistory(models.Model):
    """ประวัติการรักษาและเอกสารตรวจวิเคราะห์ในไทม์ไลน์"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='history_items')
    type = models.CharField(max_length=50, db_index=True)  # 'AI Assessment', 'Lab Result', 'Doctor Visit', 'Prescription'
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patient_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.hn} - {self.type} - {self.title}"


class LineLinkingToken(models.Model):
    """รหัสความสิทธิ์เชื่อมบัญชี LINE OA สำหรับความปลอดภัย"""
    token = models.CharField(max_length=64, unique=True, db_index=True)
    line_user_id = models.CharField(max_length=150, db_index=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'line_linking_tokens'


class LineChat(models.Model):
    """ประวัติการสนทนาคนไข้กับบอทซักประวัติบน LINE"""
    line_user_id = models.CharField(max_length=150, db_index=True)
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'line_chats'
        ordering = ['timestamp']


class PdpaConsent(models.Model):
    """ความยินยอม PDPA ของคนไข้"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='pdpa_consents')
    terms_version = models.CharField(max_length=10, default="v1.0")
    consent_treatment = models.BooleanField(default=False)
    consent_marketing = models.BooleanField(default=False)
    consent_research = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pdpa_consents'
        ordering = ['-signed_at']

    def __str__(self):
        return f"Consent {self.terms_version} by {self.user.username} at {self.signed_at}"


class LabRangeReference(models.Model):
    """เกณฑ์อ้างอิงและช่วงพิกัดค่าแล็บ (สำหรับประเมินระบบไฟจราจร เขียว/เหลือง/แดง)"""
    biomarker_name = models.CharField(max_length=100, unique=True, db_index=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    min_normal = models.FloatField(default=0.0)
    max_normal = models.FloatField(default=0.0)
    min_warning = models.FloatField(default=0.0)
    max_warning = models.FloatField(default=0.0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'lab_range_references'

    def __str__(self):
        return f"{self.biomarker_name} ({self.unit}): {self.min_normal}-{self.max_normal}"


class AutomationTask(models.Model):
    """งานแจ้งเตือนอัตโนมัติ (เช่น ติดตามอาการ, เช็คประวัติคนไข้เบี้ยวตรวจ/No-show)"""
    TASK_TYPES = [
        ('FOLLOW_UP', 'ติดตามอาการตรวจหลังเข้าบำบัด'),
        ('PRE_VISIT_REMINDER', 'แจ้งเตือนนัดหมายล่วงหน้า'),
        ('NO_SHOW_CHECK', 'ตรวจสอบและแจ้งเตือนเมื่อเบี้ยวตรวจ (No-show)'),
    ]
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('processing', 'กำลังดำเนินการ'),
        ('completed', 'เสร็จสมบูรณ์'),
        ('failed', 'ล้มเหลว'),
    ]
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, default='FOLLOW_UP', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    patient_name = models.CharField(max_length=200)
    patient_hn = models.CharField(max_length=50, blank=True, null=True)
    scheduled_for = models.DateTimeField()
    logs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'automation_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_type} for {self.patient_name} - Status: {self.status}"


class ClinicalKnowledgeSegment(models.Model):
    """ชิ้นส่วนองค์ความรู้สำหรับการค้นหาแบบ RAG เวกเตอร์ (768/1536 มิติ)"""
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    source = models.CharField(max_length=200, blank=True, null=True)
    axis_id = models.IntegerField(blank=True, null=True, db_index=True)
    embedding = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clinical_knowledge_segments'

    def __str__(self):
        return f"Segment for Axis {self.axis_id}: {self.title or self.content[:30]}"


class TSPIBrainTrainingLog(models.Model):
    """ชุดบันทึกข้อมูลการตัดสินใจประเมินโรคระดับเซลล์จากโมดูลครู (Gemini/Deepseek) เพื่อใช้ฝึกฝนสมองกลจำลอง"""
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='brain_training_logs')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    inputs = models.JSONField(default=dict, blank=True)
    output_axes = models.JSONField(default=dict, blank=True)
    output_text = models.TextField(blank=True, null=True)
    engine_used = models.CharField(max_length=50, default='gemini', db_index=True)
    # P1-C: LLM-invented axis severities (output_axes) must be physician-reviewed before they
    # are eligible to train the TSPI Brain regression model — see train_brain_model in
    # views_ai.py, which now filters on reviewed=True instead of using every logged chat turn.
    reviewed = models.BooleanField(default=False, db_index=True)
    reviewed_by = models.CharField(max_length=150, blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'tspi_brain_training_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"TSPI Brain Log - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - Engine: {self.engine_used}"
