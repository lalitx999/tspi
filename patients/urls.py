from django.urls import path, include
from rest_framework.routers import DefaultRouter
from patients.views import (
    PatientViewSet, 
    PatientBiologicalRecordViewSet, 
    AuditLogViewSet, 
    ClinicalKnowledgeViewSet, 
    TspiSettingsViewSet,
    PatientHistoryViewSet,
    AppointmentViewSet,
    PdpaConsentViewSet,
    AutomationTaskViewSet,
    dashboard_stats
)
from patients.views_line import line_webhook, line_link, liff_identity
from patients.views_ai import (
    voice_to_soap, 
    analyze_lab_ocr, 
    ClinicalKnowledgeSegmentViewSet, 
    simulate_biology, 
    generate_clinical_pdf,
    log_brain_training,
    brain_training_stats,
    TSPIBrainTrainingLogViewSet,
    train_brain_model,
    generate_report_pdf_view,
    ModuleRegistryEntryViewSet
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'records', PatientBiologicalRecordViewSet, basename='record')
router.register(r'logs', AuditLogViewSet, basename='log')
router.register(r'knowledge', ClinicalKnowledgeViewSet, basename='knowledge')
router.register(r'settings', TspiSettingsViewSet, basename='setting')
router.register(r'history', PatientHistoryViewSet, basename='history')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'pdpa-consent', PdpaConsentViewSet, basename='pdpa-consent')
router.register(r'automations', AutomationTaskViewSet, basename='automation')
router.register(r'knowledge-segments', ClinicalKnowledgeSegmentViewSet, basename='knowledge-segment')
router.register(r'brain-training-logs', TSPIBrainTrainingLogViewSet, basename='brain-training-log')
router.register(r'module-registry', ModuleRegistryEntryViewSet, basename='module-registry')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', dashboard_stats, name='dashboard_stats'),
    path('line/webhook/', line_webhook, name='line_webhook'),
    path('line/link/', line_link, name='line_link'),
    path('liff/identity/', liff_identity, name='liff_identity'),
    path('ai/voice-to-soap/', voice_to_soap, name='voice_to_soap'),
    path('ai/analyze-lab-ocr/', analyze_lab_ocr, name='analyze_lab_ocr'),
    path('ai/simulate-biology/', simulate_biology, name='simulate_biology'),
    path('ai/generate-clinical-pdf/', generate_clinical_pdf, name='generate_clinical_pdf'),
    path('ai/log-brain-training/', log_brain_training, name='log_brain_training'),
    path('ai/brain-training-stats/', brain_training_stats, name='brain_training_stats'),
    path('ai/train-brain-model/', train_brain_model, name='train_brain_model'),
    path('ai/patients/<str:patient_id>/reports/<str:report_id>/pdf/', generate_report_pdf_view, name='generate_report_pdf'),
]

