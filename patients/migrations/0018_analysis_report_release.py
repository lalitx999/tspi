from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('patients', '0017_analysisrecord_provenance_and_immutability')]
    operations = [
        migrations.CreateModel(
            name='AnalysisReportRelease',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('edition', models.CharField(choices=[('PHYSICIAN', 'Physician'), ('PATIENT', 'Patient'), ('MULTI_OMICS', 'Multi-Omics')], max_length=20)),
                ('state', models.CharField(choices=[('AI_DRAFT', 'AI Draft'), ('PHYSICIAN_REVIEWED', 'Physician Reviewed'), ('PHYSICIAN_APPROVED', 'Physician Approved'), ('PATIENT_RELEASED', 'Patient Released')], default='AI_DRAFT', max_length=30)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('acted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('analysis_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_releases', to='patients.analysisrecord')),
            ],
            options={'db_table': 'patient_analysis_report_releases', 'ordering': ['-created_at']},
        ),
    ]
