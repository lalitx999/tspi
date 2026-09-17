# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Admin(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    username = models.TextField()
    password = models.TextField()
    fname = models.TextField()
    lname = models.TextField()
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.
    positionid = models.TextField(db_column='positionID', blank=True, null=True)  # Field name made lowercase.
    update_at = models.DateTimeField()
    create_at = models.DateTimeField()
    login_at = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    cardimage = models.TextField(db_column='cardImage', blank=True, null=True)  # Field name made lowercase.
    bddate = models.TextField(db_column='bdDate', blank=True, null=True)  # Field name made lowercase.
    phone = models.TextField(blank=True, null=True)
    phone2 = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    userid_friend = models.TextField(db_column='userId_friend', blank=True, null=True)  # Field name made lowercase.
    fname_en = models.TextField(blank=True, null=True)
    lname_en = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin'


class AdminBranch(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'admin_branch'


class AdminNoti(models.Model):
    date_at = models.DateTimeField()
    by_user = models.TextField()
    title = models.TextField()
    link = models.TextField(blank=True, null=True)
    status = models.IntegerField()
    type = models.TextField()

    class Meta:
        managed = False
        db_table = 'admin_noti'


class AiOutputs(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    ai_request = models.ForeignKey('AiRequests', models.DO_NOTHING, blank=True, null=True)
    output_type = models.CharField(max_length=50, blank=True, null=True)
    content_json = models.TextField(blank=True, null=True)
    rendered_text = models.TextField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, blank=True, null=True)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    missing_data_json = models.TextField(blank=True, null=True)
    review_required = models.SmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ai_outputs'


class AiRequests(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    patient_id = models.IntegerField(blank=True, null=True)
    requested_by = models.IntegerField(blank=True, null=True)
    request_type = models.CharField(max_length=50, blank=True, null=True)
    user_prompt = models.TextField(blank=True, null=True)
    template_used = models.CharField(max_length=100, blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    data_scope_json = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ai_requests'


class AiReviews(models.Model):
    ai_output_id = models.IntegerField()
    reviewed_by = models.IntegerField()
    review_status = models.CharField(max_length=20, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ai_reviews'


class Appointment(models.Model):
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


class AuditLogs(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user_id = models.IntegerField(blank=True, null=True)
    action_type = models.CharField(max_length=50, blank=True, null=True)
    object_type = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    patient_id = models.IntegerField(blank=True, null=True)
    metadata_json = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'audit_logs'


class Bank(models.Model):
    bankid = models.TextField(db_column='bankID')  # Field name made lowercase.
    bank_branch = models.TextField()
    acc_name = models.TextField()
    acc_number = models.TextField()
    status = models.CharField(max_length=100)
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'bank'


class BankName(models.Model):
    name_th = models.TextField()
    name_en = models.TextField()
    logo = models.TextField()

    class Meta:
        managed = False
        db_table = 'bank_name'


class BannerPromotion(models.Model):
    img = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'banner_promotion'


class BiomarkerToAxisMapping(models.Model):
    biomarker_name = models.CharField(max_length=255)
    axis_code = models.CharField(max_length=10)
    unit = models.CharField(max_length=50, blank=True, null=True)
    normal_range_low = models.CharField(max_length=50, blank=True, null=True)
    normal_range_high = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'biomarker_to_axis_mapping'


class BotIdentity(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    platform = models.CharField(max_length=20)
    platform_user_id = models.CharField(max_length=255)
    user_id = models.IntegerField()
    linked_at = models.DateTimeField()
    status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bot_identity'
        unique_together = (('platform', 'platform_user_id'),)


class Box(models.Model):
    name = models.TextField()
    width = models.FloatField()
    long = models.FloatField()
    height = models.FloatField()
    weight = models.FloatField()
    price = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'box'


class Branch(models.Model):
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.
    branchname = models.TextField(db_column='branchName')  # Field name made lowercase.
    branchphone = models.TextField(db_column='branchPhone')  # Field name made lowercase.
    branchemail = models.TextField(db_column='branchEmail')  # Field name made lowercase.
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    branchaddress = models.TextField(db_column='branchAddress')  # Field name made lowercase.
    level = models.TextField()
    ownername = models.TextField(db_column='ownerName')  # Field name made lowercase.
    owneridcard = models.TextField(db_column='ownerIDcard')  # Field name made lowercase.
    ownerphone = models.TextField(db_column='ownerPhone')  # Field name made lowercase.
    owneremail = models.TextField(db_column='ownerEmail')  # Field name made lowercase.
    ownerpassword = models.TextField(db_column='ownerPassword')  # Field name made lowercase.
    date_at = models.DateTimeField()
    at_by = models.TextField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'branch'


class Broadcast(models.Model):
    type1 = models.TextField()
    type2 = models.TextField()
    type3 = models.TextField()
    type4 = models.TextField()
    type5 = models.TextField()
    type6 = models.TextField()
    to_disease = models.TextField(blank=True, null=True)
    date_send = models.DateField()
    time_send = models.TimeField()
    msg = models.TextField()
    status = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'broadcast'


class Chats(models.Model):
    chat_id = models.IntegerField()
    msg = models.TextField()
    file = models.TextField(blank=True, null=True)
    voice = models.TextField(blank=True, null=True)
    me = models.TextField()
    userid = models.TextField(db_column='userID', blank=True, null=True)  # Field name made lowercase.
    adminid = models.TextField(db_column='adminID', blank=True, null=True)  # Field name made lowercase.
    date_at = models.DateTimeField()
    status = models.IntegerField()
    video = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chats'


class ChatsMain(models.Model):
    chat_id = models.AutoField(primary_key=True)
    disease = models.TextField()
    date_start = models.DateTimeField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    typemsg = models.TextField(db_column='typeMsg', blank=True, null=True)  # Field name made lowercase.
    status = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'chats_main'


class ClinicalAxes(models.Model):
    axis_code = models.CharField(unique=True, max_length=10)
    axis_name_en = models.CharField(max_length=255)
    axis_name_th = models.CharField(max_length=255)
    domain_code = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    biomarkers = models.TextField(blank=True, null=True)
    mechanisms = models.TextField(blank=True, null=True)
    herbal_modules = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_axes'


class ClinicalDomains(models.Model):
    domain_code = models.CharField(unique=True, max_length=20)
    name_en = models.CharField(max_length=255)
    name_th = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_domains'


class ClinicalModuleAxisMapping(models.Model):
    module = models.ForeignKey('ClinicalModules', models.DO_NOTHING)
    axis = models.ForeignKey(ClinicalAxes, models.DO_NOTHING)
    relevance_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    evidence_level = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_module_axis_mapping'
        unique_together = (('module', 'axis'),)


class ClinicalModules(models.Model):
    module_code = models.CharField(unique=True, max_length=50)
    module_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    indications_json = models.TextField(blank=True, null=True)
    safety_alerts = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_modules'


class ClinicalProtocolAxisMapping(models.Model):
    protocol = models.ForeignKey('ClinicalProtocols', models.DO_NOTHING)
    axis = models.ForeignKey(ClinicalAxes, models.DO_NOTHING)
    priority = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_protocol_axis_mapping'


class ClinicalProtocols(models.Model):
    protocol_code = models.CharField(unique=True, max_length=20)
    protocol_name = models.CharField(max_length=255)
    step_number = models.IntegerField(blank=True, null=True)
    phase = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    duration_days = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_protocols'


class ClinicalSubAxes(models.Model):
    axis = models.ForeignKey(ClinicalAxes, models.DO_NOTHING)
    sub_axis_code = models.CharField(max_length=1)
    sub_axis_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    markers = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clinical_sub_axes'
        unique_together = (('axis', 'sub_axis_code'),)


class Config(models.Model):
    payment_bank = models.TextField()
    payment_card = models.TextField()
    percent = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'config'


class Country(models.Model):
    iso = models.CharField(max_length=2)
    name = models.CharField(max_length=80)
    numcode = models.SmallIntegerField(blank=True, null=True)
    phonecode = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'country'


class Disease(models.Model):
    diseaseid = models.TextField(db_column='diseaseID')  # Field name made lowercase.
    name_th = models.TextField()
    name_en = models.TextField()

    class Meta:
        managed = False
        db_table = 'disease'


class DocBloodTestEn(models.Model):
    cerid = models.TextField(db_column='cerID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    create_at = models.DateField()
    userfname = models.TextField(db_column='userFname')  # Field name made lowercase.
    userlname = models.TextField(db_column='userLname')  # Field name made lowercase.
    userage = models.TextField(db_column='userAge')  # Field name made lowercase.
    disease = models.TextField()
    symptom = models.TextField()
    listcheck = models.TextField()
    note = models.TextField(blank=True, null=True)
    other = models.TextField(blank=True, null=True)
    doctorname = models.TextField(db_column='doctorName')  # Field name made lowercase.
    medicaladdress = models.TextField(db_column='medicalAddress')  # Field name made lowercase.
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doc_blood_test_en'


class DocBloodTestTh(models.Model):
    cerid = models.TextField(db_column='cerID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    create_at = models.DateField()
    userfname = models.TextField(db_column='userFname')  # Field name made lowercase.
    userlname = models.TextField(db_column='userLname')  # Field name made lowercase.
    userage = models.TextField(db_column='userAge')  # Field name made lowercase.
    disease = models.TextField()
    symptom = models.TextField()
    listcheck = models.TextField()
    note = models.TextField(blank=True, null=True)
    other = models.TextField(blank=True, null=True)
    doctorname = models.TextField(db_column='doctorName')  # Field name made lowercase.
    medicaladdress = models.TextField(db_column='medicalAddress')  # Field name made lowercase.
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doc_blood_test_th'


class DocMedicalCerEn(models.Model):
    cerid = models.TextField(db_column='cerID')  # Field name made lowercase.
    cernumber = models.IntegerField(db_column='cerNumber')  # Field name made lowercase.
    date_create = models.DateField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    medicaladdress = models.TextField(db_column='medicalAddress')  # Field name made lowercase.
    doctorname = models.TextField(db_column='doctorName')  # Field name made lowercase.
    doctornocer = models.TextField(db_column='doctorNoCer')  # Field name made lowercase.
    username = models.TextField(db_column='userName')  # Field name made lowercase.
    userage = models.TextField(db_column='userAge')  # Field name made lowercase.
    userhn = models.TextField(db_column='userHN')  # Field name made lowercase.
    usercardid = models.TextField(db_column='userCardID')  # Field name made lowercase.
    useraddress = models.TextField(db_column='userAddress')  # Field name made lowercase.
    opdcard = models.TextField(db_column='opdCard')  # Field name made lowercase.
    date_medical = models.DateField()
    disease = models.TextField()
    physical_result = models.TextField()
    diagnosis = models.TextField()
    medical = models.TextField()
    detail = models.TextField()
    next_visit = models.TextField(blank=True, null=True)
    rest_day = models.TextField(blank=True, null=True)
    rest_start = models.TextField(blank=True, null=True)
    rest_end = models.TextField(blank=True, null=True)
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doc_medical_cer_en'


class DocMedicalCerTh(models.Model):
    cerid = models.TextField(db_column='cerID')  # Field name made lowercase.
    cernumber = models.IntegerField(db_column='cerNumber')  # Field name made lowercase.
    date_create = models.DateField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    medicaladdress = models.TextField(db_column='medicalAddress')  # Field name made lowercase.
    doctorname = models.TextField(db_column='doctorName')  # Field name made lowercase.
    doctornocer = models.TextField(db_column='doctorNoCer')  # Field name made lowercase.
    username = models.TextField(db_column='userName')  # Field name made lowercase.
    userage = models.TextField(db_column='userAge')  # Field name made lowercase.
    userhn = models.TextField(db_column='userHN')  # Field name made lowercase.
    usercardid = models.TextField(db_column='userCardID')  # Field name made lowercase.
    useraddress = models.TextField(db_column='userAddress')  # Field name made lowercase.
    opdcard = models.TextField(db_column='opdCard')  # Field name made lowercase.
    date_medical = models.DateField()
    disease = models.TextField()
    physical_result = models.TextField()
    diagnosis = models.TextField()
    medical = models.TextField()
    detail = models.TextField()
    next_visit = models.TextField(blank=True, null=True)
    rest_day = models.TextField(blank=True, null=True)
    rest_start = models.TextField(blank=True, null=True)
    rest_end = models.TextField(blank=True, null=True)
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doc_medical_cer_th'


class DocPhysicalExamination(models.Model):
    cerid = models.TextField(db_column='cerID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    create_at = models.DateField()
    userfname = models.TextField(db_column='userFname')  # Field name made lowercase.
    userlname = models.TextField(db_column='userLname')  # Field name made lowercase.
    userage = models.TextField(db_column='userAge')  # Field name made lowercase.
    disease = models.TextField()
    symptom = models.TextField()
    listcheck = models.TextField()
    note = models.TextField(blank=True, null=True)
    other = models.TextField(blank=True, null=True)
    doctorname = models.TextField(db_column='doctorName')  # Field name made lowercase.
    medicaladdress = models.TextField(db_column='medicalAddress')  # Field name made lowercase.
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doc_physical_examination'


class Doctor(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    imgprofile = models.TextField(db_column='imgProfile', blank=True, null=True)  # Field name made lowercase.
    age = models.TextField()
    expert = models.TextField()
    about = models.TextField()
    dt_working = models.TextField()
    education = models.TextField()
    imgcer = models.TextField(db_column='imgCer', blank=True, null=True)  # Field name made lowercase.
    nocer = models.TextField(db_column='noCer')  # Field name made lowercase.
    nocer_en = models.TextField(db_column='noCer_en', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'doctor'


class DoctorSchedule(models.Model):
    doctorid = models.TextField(db_column='doctorID')  # Field name made lowercase.
    type = models.TextField()
    time_meet = models.TextField()
    limit_user = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'doctor_schedule'


class DoctorScheduleLimit(models.Model):
    doctorid = models.TextField(db_column='doctorID')  # Field name made lowercase.
    date_meet = models.DateField()
    time_meet = models.TextField()
    limit_user = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'doctor_schedule_limit'


class Document(models.Model):
    name = models.TextField()
    file = models.TextField(blank=True, null=True)
    update_at = models.DateTimeField()
    des = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'document'


class Drug(models.Model):
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    name = models.TextField()
    des = models.TextField()
    kw = models.TextField()
    img = models.TextField()
    license_number = models.TextField()
    price_bath = models.DecimalField(max_digits=18, decimal_places=2)
    price_dollar = models.DecimalField(max_digits=18, decimal_places=2)
    component = models.TextField()
    properties = models.TextField()
    research = models.TextField()
    eat_wakeup = models.CharField(max_length=10)
    eat_morning = models.CharField(max_length=10)
    eat_during = models.CharField(max_length=10)
    eat_evening = models.CharField(max_length=10)
    eat_night = models.CharField(max_length=10)
    unit = models.TextField()
    unit_type = models.TextField()
    detail = models.TextField(blank=True, null=True)
    box_width = models.FloatField()
    box_long = models.FloatField()
    box_height = models.FloatField()
    weight = models.FloatField()
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()
    update_by = models.TextField()
    stock = models.IntegerField()
    view = models.IntegerField()
    flavor = models.TextField(blank=True, null=True)
    drug_effect = models.TextField(blank=True, null=True)
    side_effect = models.TextField(blank=True, null=True)
    contraindication = models.TextField(blank=True, null=True)
    type_box = models.TextField()
    lunch = models.TextField()
    warning = models.TextField(blank=True, null=True)
    unit_in_box = models.TextField(blank=True, null=True)
    date_out = models.DateField(blank=True, null=True)
    out_age = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'drug'


class DrugImg(models.Model):
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    img = models.TextField()

    class Meta:
        managed = False
        db_table = 'drug_img'


class Encounters(models.Model):
    patient_id = models.IntegerField()
    encounter_date = models.DateTimeField(blank=True, null=True)
    encounter_type = models.CharField(max_length=50, blank=True, null=True)
    chief_complaint = models.TextField(blank=True, null=True)
    history_note = models.TextField(blank=True, null=True)
    assessment_note = models.TextField(blank=True, null=True)
    plan_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'encounters'


class EvaluateMain(models.Model):
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'evaluate_main'


class Formula(models.Model):
    formulaid = models.TextField(db_column='formulaID')  # Field name made lowercase.
    diseaseid = models.TextField(db_column='diseaseID')  # Field name made lowercase.
    versionno = models.TextField(db_column='versionNo')  # Field name made lowercase.
    detail = models.TextField()
    todo = models.TextField()
    effect = models.TextField()
    price_bath = models.DecimalField(max_digits=18, decimal_places=2)
    price_dollar = models.DecimalField(max_digits=18, decimal_places=2)
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()
    img = models.TextField()
    stock = models.IntegerField()
    sale = models.TextField()
    formulaname = models.TextField(db_column='formulaName', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'formula'


class FormulaDrug(models.Model):
    formulaid = models.TextField(db_column='formulaID')  # Field name made lowercase.
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    eat_wakeup = models.CharField(max_length=10)
    eat_morning = models.CharField(max_length=10)
    eat_during = models.CharField(max_length=10)
    eat_evening = models.CharField(max_length=10)
    eat_night = models.CharField(max_length=10)
    unit = models.TextField()
    detail = models.TextField()

    class Meta:
        managed = False
        db_table = 'formula_drug'


class GenomicReports(models.Model):
    patient_id = models.IntegerField()
    sequencing_type = models.CharField(max_length=50, blank=True, null=True)
    curated_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'genomic_reports'


class HisDrug(models.Model):
    appid = models.TextField(db_column='appID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    doctorid = models.TextField(db_column='doctorID')  # Field name made lowercase.
    type = models.TextField()
    mainid = models.TextField(db_column='mainID')  # Field name made lowercase.
    unit = models.IntegerField()
    date_at = models.DateTimeField()
    how_buy = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'his_drug'


class HisEvaluate(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_at = models.DateTimeField()
    score1 = models.TextField()
    score2 = models.TextField()
    score3 = models.TextField()
    score4 = models.TextField()
    score5 = models.TextField()
    score6 = models.TextField()
    score7 = models.TextField()
    score8 = models.TextField()
    score9 = models.TextField()
    score10 = models.TextField()
    score11 = models.TextField(blank=True, null=True)
    score12 = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'his_evaluate'


class HisMedical(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    appid = models.TextField(db_column='appID', blank=True, null=True)  # Field name made lowercase.
    detail = models.TextField()
    file = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    next_date = models.TextField(blank=True, null=True)
    next_time = models.TextField(blank=True, null=True)
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()
    doctorid = models.TextField(db_column='doctorID')  # Field name made lowercase.
    disease = models.TextField(blank=True, null=True)
    physical_result = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    medical = models.TextField(blank=True, null=True)
    next_visit = models.TextField(blank=True, null=True)
    rest_day = models.TextField(blank=True, null=True)
    rest_start = models.TextField(blank=True, null=True)
    rest_end = models.TextField(blank=True, null=True)
    date_at = models.DateField()

    class Meta:
        managed = False
        db_table = 'his_medical'


class HisMedicalFile(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    file = models.TextField()
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'his_medical_file'


class HisUpdated(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_at = models.DateTimeField()
    score1 = models.TextField(blank=True, null=True)
    week1 = models.TextField(blank=True, null=True)
    befor1 = models.TextField(blank=True, null=True)
    note1 = models.TextField(blank=True, null=True)
    img1 = models.TextField(blank=True, null=True)
    score2 = models.TextField(blank=True, null=True)
    week2 = models.TextField(blank=True, null=True)
    befor2 = models.TextField(blank=True, null=True)
    note2 = models.TextField(blank=True, null=True)
    img2 = models.TextField(blank=True, null=True)
    score3 = models.TextField(blank=True, null=True)
    week3 = models.TextField(blank=True, null=True)
    befor3 = models.TextField(blank=True, null=True)
    note3 = models.TextField(blank=True, null=True)
    img3 = models.TextField(blank=True, null=True)
    score4 = models.TextField()
    week4 = models.TextField()
    befor4 = models.TextField()
    note4 = models.TextField(blank=True, null=True)
    img4 = models.TextField(blank=True, null=True)
    score5 = models.TextField()
    week5 = models.TextField()
    befor5 = models.TextField()
    note5 = models.TextField(blank=True, null=True)
    img5 = models.TextField(blank=True, null=True)
    score6 = models.TextField()
    week6 = models.TextField()
    befor6 = models.TextField()
    note6 = models.TextField(blank=True, null=True)
    img6 = models.TextField(blank=True, null=True)
    score7 = models.TextField()
    week7 = models.TextField()
    befor7 = models.TextField()
    note7 = models.TextField(blank=True, null=True)
    img7 = models.TextField(blank=True, null=True)
    score8 = models.TextField()
    week8 = models.TextField()
    befor8 = models.TextField()
    note8 = models.TextField(blank=True, null=True)
    img8 = models.TextField(blank=True, null=True)
    weight = models.TextField()
    pressure_top = models.TextField(blank=True, null=True)
    pressure_bottom = models.TextField(blank=True, null=True)
    heart_rate = models.TextField(blank=True, null=True)
    blood_file = models.TextField(blank=True, null=True)
    blood_detail = models.TextField(blank=True, null=True)
    disease_file = models.TextField(blank=True, null=True)
    disease_detail = models.TextField(blank=True, null=True)
    size_wound = models.TextField(blank=True, null=True)
    other = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'his_updated'


class InCart(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    type = models.TextField()
    mainid = models.TextField(db_column='mainID')  # Field name made lowercase.
    unit = models.IntegerField()
    update_at = models.DateTimeField()
    type_in = models.TextField()
    price = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'in_cart'


class LogOrder(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    txt = models.TextField()
    by_user = models.TextField()
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'log_order'


class MicrobiomeReports(models.Model):
    patient_id = models.IntegerField()
    diversity_metrics = models.TextField(blank=True, null=True)
    functional_patterns = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'microbiome_reports'


class ModuleAxisMapping(models.Model):
    module_name = models.CharField(max_length=100)
    axis = models.ForeignKey(ClinicalAxes, models.DO_NOTHING)
    relevance_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    evidence_level = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'module_axis_mapping'


class MyDrug(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    update_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'my_drug'


class News(models.Model):
    title = models.TextField()
    img = models.TextField()
    detail = models.TextField()
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()
    view = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'news'


class Orders(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_at = models.DateTimeField()
    type_payment = models.TextField()
    status = models.TextField()
    total = models.DecimalField(max_digits=18, decimal_places=2)
    vat = models.DecimalField(max_digits=18, decimal_places=2)
    shipping = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2)
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.
    type_ship = models.TextField(blank=True, null=True)
    orderidapp = models.TextField(db_column='orderidApp', blank=True, null=True)  # Field name made lowercase.
    note = models.TextField(blank=True, null=True)
    doctorid = models.TextField(db_column='doctorID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'orders'


class OrdersAddress(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    fname = models.TextField()
    lname = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    district = models.TextField()
    amphur = models.TextField()
    province = models.TextField()
    zipcode = models.TextField()
    country = models.TextField()

    class Meta:
        managed = False
        db_table = 'orders_address'


class OrdersList(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    type = models.TextField()
    mainid = models.TextField(db_column='mainID')  # Field name made lowercase.
    unit = models.IntegerField()
    price_bath = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2)
    return_tus = models.TextField(blank=True, null=True)
    return_date = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_list'


class OrdersPayment(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    type = models.TextField()
    slip = models.TextField(blank=True, null=True)
    date_at = models.DateField(blank=True, null=True)
    time_at = models.TimeField(blank=True, null=True)
    total = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    ch_id = models.TextField(blank=True, null=True)
    other = models.TextField(blank=True, null=True)
    create_at = models.DateTimeField()
    receipt_no = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_payment'


class OrdersShipping(models.Model):
    orderid = models.TextField(db_column='orderID')  # Field name made lowercase.
    tracking_number = models.TextField()
    transportid = models.TextField(db_column='transportID')  # Field name made lowercase.
    date_ship = models.DateField()
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_shipping'


class PatientConsent(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user_id = models.IntegerField()
    consent_type = models.CharField(max_length=50)
    consent_version = models.CharField(max_length=20)
    consented_at = models.DateTimeField()
    channel = models.CharField(max_length=20, blank=True, null=True)
    ip = models.CharField(max_length=45, blank=True, null=True)
    withdrawn_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_consent'


class PatientConsents(models.Model):
    user_id = models.IntegerField()
    consent_type = models.CharField(max_length=50)
    version = models.CharField(max_length=10)
    status = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_consents'


class PgxInterpretations(models.Model):
    patient_id = models.IntegerField()
    gene = models.CharField(max_length=50)
    phenotype = models.CharField(max_length=255, blank=True, null=True)
    affected_drugs = models.TextField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, blank=True, null=True)
    review_required = models.SmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pgx_interpretations'


class Position(models.Model):
    positionid = models.AutoField(db_column='positionID', primary_key=True)  # Field name made lowercase.
    name = models.TextField()
    colors = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'position'


class ProcessedUpdates(models.Model):
    update_id = models.CharField(unique=True, max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'processed_updates'


class Promotion(models.Model):
    promotionid = models.TextField(db_column='promotionID')  # Field name made lowercase.
    name = models.TextField()
    type = models.CharField(max_length=100)
    type_product = models.TextField()
    mainid = models.TextField(db_column='mainID')  # Field name made lowercase.
    price_bath = models.DecimalField(max_digits=18, decimal_places=2)
    price_dollar = models.DecimalField(max_digits=18, decimal_places=2)
    unit_buy = models.IntegerField()
    unit_free = models.IntegerField()
    date_start = models.DateField()
    date_end = models.DateField()
    note = models.TextField()
    username = models.TextField()
    unit_get = models.IntegerField()
    form_price = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'promotion'


class RegisDisease(models.Model):
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'regis_disease'


class Service(models.Model):
    name = models.TextField()
    price = models.IntegerField()
    branchid = models.TextField(db_column='branchID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'service'


class SettingShop(models.Model):
    shipping_all = models.IntegerField()
    shipping_keep = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'setting_shop'


class Stock(models.Model):
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    loid = models.TextField(db_column='loID')  # Field name made lowercase.
    type = models.TextField()
    stock = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'stock'


class StockDaily(models.Model):
    locationid = models.TextField(db_column='locationID')  # Field name made lowercase.
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    current_unit = models.TextField()
    checked = models.TextField()
    note = models.TextField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_daily'


class StockHis(models.Model):
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    form_location = models.TextField()
    form_type = models.TextField()
    user_send = models.TextField()
    to_location = models.TextField()
    to_type = models.TextField()
    user_get = models.TextField()
    unit = models.IntegerField()
    lotnumber = models.TextField(db_column='lotNumber')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'stock_his'


class StockLocation(models.Model):
    locationid = models.AutoField(db_column='locationID', primary_key=True)  # Field name made lowercase.
    name = models.TextField()
    branchid = models.TextField(db_column='branchID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'stock_location'


class StockPlan(models.Model):
    planid = models.AutoField(db_column='planID', primary_key=True)  # Field name made lowercase.
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    unit = models.IntegerField()
    for_number = models.IntegerField()
    for_type = models.TextField()
    update_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'stock_plan'


class StockPlanWork(models.Model):
    planid = models.TextField(db_column='planID')  # Field name made lowercase.
    drugid = models.TextField(db_column='drugID')  # Field name made lowercase.
    unit = models.IntegerField()
    balance = models.IntegerField()
    date_work = models.DateField()
    date_out = models.DateField()
    lotnumber = models.TextField(db_column='lotNumber')  # Field name made lowercase.
    mylotnumber = models.IntegerField(db_column='mylotNumber')  # Field name made lowercase.
    location_work = models.TextField()
    dateline = models.DateField(blank=True, null=True)
    date_at = models.DateTimeField()
    userid = models.TextField(db_column='userID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'stock_plan_work'


class SymptomToAxisMapping(models.Model):
    symptom_keyword = models.CharField(max_length=255)
    axis_code = models.CharField(max_length=10)
    weight = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'symptom_to_axis_mapping'


class Transport(models.Model):
    name = models.TextField()
    link = models.TextField()
    branchid = models.TextField(db_column='branchID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'transport'


class TspiAiIntakeSessions(models.Model):
    platform = models.TextField()
    platform_user_id = models.CharField(max_length=100)
    patient_id = models.IntegerField()
    current_status = models.CharField(max_length=50, blank=True, null=True)
    last_question = models.TextField(blank=True, null=True)
    context_buffer = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    current_step = models.CharField(max_length=50, blank=True, null=True)
    last_message = models.TextField(blank=True, null=True)
    collected_data = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_ai_intake_sessions'


class TspiClinicalAnamnesis(models.Model):
    patient_id = models.IntegerField()
    session_id = models.IntegerField()
    intake_type = models.CharField(max_length=50, blank=True, null=True)
    raw_content = models.TextField(blank=True, null=True)
    structured_data = models.TextField(blank=True, null=True)
    axis_relevance = models.TextField(blank=True, null=True)
    collected_via = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_clinical_anamnesis'


class TspiClinicalEvents(models.Model):
    patient_id = models.IntegerField()
    event_type = models.CharField(max_length=100)
    importance = models.TextField(blank=True, null=True)
    summary = models.CharField(max_length=512)
    data_payload = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_clinical_events'


class TspiExportsAudit(models.Model):
    patient_id = models.IntegerField()
    export_type = models.CharField(max_length=100)
    data_layer = models.TextField()
    file_format = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_exports_audit'


class TspiIdentities(models.Model):
    patient_id = models.IntegerField()
    channel_type = models.TextField()
    channel_user_id = models.CharField(max_length=255)
    verified = models.SmallIntegerField(blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    data_payload = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_identities'
        unique_together = (('channel_type', 'channel_user_id'),)


class TspiLabResults(models.Model):
    patient_id = models.IntegerField()
    test_name = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, blank=True, null=True)
    reference_range = models.CharField(max_length=50, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    test_date = models.DateField(blank=True, null=True)
    clinical_event_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)
    data_payload = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_lab_results'


class TspiMessages(models.Model):
    identity_id = models.IntegerField()
    direction = models.TextField()
    message_type = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    media_url = models.CharField(max_length=512, blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)
    clinical_event_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    data_payload = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_messages'


class TspiModules(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    module_code = models.CharField(unique=True, max_length=50)
    module_name_th = models.CharField(max_length=255, blank=True, null=True)
    module_name_en = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    indications_json = models.TextField(blank=True, null=True)
    contraindications_json = models.TextField(blank=True, null=True)
    expected_markers_json = models.TextField(blank=True, null=True)
    safety_notes = models.TextField(blank=True, null=True)
    active_flag = models.SmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tspi_modules'


class TspiPatientConsent(models.Model):
    patient_id = models.IntegerField()
    consent_type = models.CharField(max_length=100)
    version = models.CharField(max_length=20, blank=True, null=True)
    channel = models.CharField(max_length=50, blank=True, null=True)
    is_agreed = models.SmallIntegerField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    consented_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_patient_consent'


class TspiSettings(models.Model):
    setting_key = models.CharField(unique=True, max_length=100)
    setting_value = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_settings'


class TspiTelegramSessions(models.Model):
    user_id = models.CharField(max_length=50)
    status = models.CharField(max_length=50, blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tspi_telegram_sessions'


class TypeBox(models.Model):
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'type_box'


class TypeUnit(models.Model):
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'type_unit'


class User(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_regis = models.DateTimeField()
    idcard = models.TextField(db_column='IDcard', blank=True, null=True)  # Field name made lowercase.
    password = models.TextField(blank=True, null=True)
    prefix = models.TextField(blank=True, null=True)
    fname = models.TextField(blank=True, null=True)
    lname = models.TextField(blank=True, null=True)
    sex = models.TextField(blank=True, null=True)
    pregnant = models.TextField(blank=True, null=True)
    bd_year = models.TextField(blank=True, null=True)
    bd_date = models.TextField(blank=True, null=True)
    age = models.TextField(blank=True, null=True)
    weight = models.TextField(blank=True, null=True)
    height = models.TextField(blank=True, null=True)
    bmi = models.TextField(blank=True, null=True)
    bmi_val = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    phone2 = models.TextField(blank=True, null=True)
    fb_name = models.TextField(blank=True, null=True)
    line = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.TextField(blank=True, null=True)
    amphur = models.TextField(blank=True, null=True)
    province = models.TextField(blank=True, null=True)
    zipcode = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    career = models.TextField(blank=True, null=True)
    salary = models.DecimalField(max_digits=18, decimal_places=2)
    update_at = models.DateTimeField()
    status = models.CharField(max_length=100)
    userid_friend = models.TextField(db_column='userId_friend', blank=True, null=True)  # Field name made lowercase.
    percent = models.IntegerField()
    branchid = models.TextField(db_column='branchID', blank=True, null=True)  # Field name made lowercase.
    status_vip = models.TextField(blank=True, null=True)
    status_check = models.TextField()
    userhn = models.TextField(db_column='userHN', blank=True, null=True)  # Field name made lowercase.
    hisdrug = models.TextField(db_column='hisDrug', blank=True, null=True)  # Field name made lowercase.
    type = models.TextField(blank=True, null=True)
    jotform = models.TextField()
    my_number = models.IntegerField(blank=True, null=True)
    last_uid = models.TextField(db_column='last_uID', blank=True, null=True)  # Field name made lowercase.
    formapp = models.TextField()
    useridapp = models.TextField(db_column='userIDApp', blank=True, null=True)  # Field name made lowercase.
    nationality = models.TextField(blank=True, null=True)
    ethnicity = models.TextField(blank=True, null=True)
    marry_status = models.TextField(blank=True, null=True)
    smoking = models.CharField(max_length=10, blank=True, null=True)
    drink = models.CharField(max_length=100, blank=True, null=True)
    time_sleep = models.CharField(max_length=10, blank=True, null=True)
    time_wakeup = models.CharField(max_length=10, blank=True, null=True)
    time_total = models.CharField(max_length=50, blank=True, null=True)
    sleep_score = models.SmallIntegerField(blank=True, null=True)
    vaccinated = models.CharField(max_length=100, blank=True, null=True)
    symptoms = models.CharField(max_length=200, blank=True, null=True)
    disease = models.TextField(blank=True, null=True)
    disease_other = models.TextField(blank=True, null=True)
    cure_disease = models.TextField(blank=True, null=True)
    cure_other = models.TextField(blank=True, null=True)
    score_disease = models.CharField(max_length=50, blank=True, null=True)
    score_pain = models.SmallIntegerField(blank=True, null=True)
    detail_disease = models.TextField(blank=True, null=True)
    where_cure = models.CharField(max_length=100, blank=True, null=True)
    long_cure = models.CharField(max_length=20, blank=True, null=True)
    long_cure_type = models.CharField(max_length=20, blank=True, null=True)
    drug_current = models.TextField(blank=True, null=True)
    drug_allergy = models.TextField(blank=True, null=True)
    his_medicine = models.TextField(blank=True, null=True)
    his_antibiotic = models.TextField(blank=True, null=True)
    quantity_medicine = models.TextField(blank=True, null=True)
    purpose_medicine = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    reason_other = models.TextField(blank=True, null=True)
    accept = models.CharField(max_length=10, blank=True, null=True)
    who_regis = models.CharField(max_length=100, blank=True, null=True)
    who_regis2 = models.CharField(max_length=200, blank=True, null=True)
    img_disease = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    google2fa_secret = models.CharField(max_length=255, blank=True, null=True)
    google2fa_enabled = models.SmallIntegerField(blank=True, null=True)
    backup_codes = models.TextField(blank=True, null=True)
    trust_device_token = models.TextField(blank=True, null=True)
    trust_device_expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user'


class Userlogin(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    idcard = models.TextField(db_column='IDcard', blank=True, null=True)  # Field name made lowercase.
    password = models.TextField()
    level = models.TextField()

    class Meta:
        managed = False
        db_table = 'userLogin'


class UserAddress(models.Model):
    userid = models.TextField(db_column='userID', blank=True, null=True)  # Field name made lowercase.
    fname = models.TextField(blank=True, null=True)
    lname = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.TextField(blank=True, null=True)
    amphur = models.TextField(blank=True, null=True)
    province = models.TextField(blank=True, null=True)
    zipcode = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    date_use = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_address'


class UserDied(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    date_at = models.DateTimeField()
    type = models.TextField(blank=True, null=True)
    drug = models.TextField(blank=True, null=True)
    drug_now = models.TextField(blank=True, null=True)
    long_eat = models.TextField(blank=True, null=True)
    drug_other = models.TextField(blank=True, null=True)
    disease = models.TextField(blank=True, null=True)
    file = models.TextField(blank=True, null=True)
    cause_died = models.TextField(blank=True, null=True)
    date_died = models.TextField(blank=True, null=True)
    effect_sick = models.TextField(blank=True, null=True)
    effect_test_results = models.TextField(blank=True, null=True)
    effect_other = models.TextField(blank=True, null=True)
    effect_test_results_file = models.TextField(blank=True, null=True)
    efficiency = models.TextField(blank=True, null=True)
    after = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    results_doctor = models.TextField(blank=True, null=True)
    doctor = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_died'


class UserHealth(models.Model):
    userid = models.TextField(db_column='userID')  # Field name made lowercase.
    smoking = models.TextField()
    drink = models.TextField(blank=True, null=True)
    time_sleep = models.TextField(blank=True, null=True)
    time_wackup = models.TextField(blank=True, null=True)
    time_total = models.TextField(blank=True, null=True)
    sleep_score = models.TextField(blank=True, null=True)
    vaccinated = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    disease = models.TextField(blank=True, null=True)
    cure_disease = models.TextField(blank=True, null=True)
    score_disease = models.TextField(blank=True, null=True)
    drug_current = models.TextField(blank=True, null=True)
    drug_allergy = models.TextField(blank=True, null=True)
    score_pain = models.TextField(blank=True, null=True)
    detail_disease = models.TextField(blank=True, null=True)
    img_disease = models.TextField(blank=True, null=True)
    where_cure = models.TextField(blank=True, null=True)
    long_cure = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    accept = models.CharField(max_length=255)
    who_regis = models.TextField(blank=True, null=True)
    his_medicine = models.TextField(blank=True, null=True)
    his_antibiotic = models.TextField(blank=True, null=True)
    quantity_medicine = models.TextField(blank=True, null=True)
    purpose_medicine = models.TextField(blank=True, null=True)
    pregnant = models.TextField(blank=True, null=True)
    cancer = models.TextField(blank=True, null=True)
    exercise = models.TextField(blank=True, null=True)
    effective = models.TextField(blank=True, null=True)
    symptoms_after = models.TextField(blank=True, null=True)
    effect_other = models.TextField(blank=True, null=True)
    suggestions = models.TextField(blank=True, null=True)
    drug_together = models.TextField(blank=True, null=True)
    day_better = models.TextField(blank=True, null=True)
    after_img = models.TextField(blank=True, null=True)
    date_recovery = models.TextField(blank=True, null=True)
    jotform = models.TextField()

    class Meta:
        managed = False
        db_table = 'user_health'
