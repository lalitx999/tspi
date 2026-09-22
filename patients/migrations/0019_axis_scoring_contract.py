from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('patients', '0018_analysis_report_release')]
    operations = [
        migrations.CreateModel(
            name='AxisScoringContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('axis_code', models.CharField(max_length=8, unique=True)),
                ('rule_id', models.CharField(max_length=100, unique=True)),
                ('version', models.CharField(max_length=40)),
                ('threshold_spec', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING_APPROVAL', 'Pending approval'), ('APPROVED', 'Approved'), ('RETIRED', 'Retired')], default='DRAFT', max_length=20)),
                ('approved_by', models.CharField(blank=True, max_length=150)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'tspi_axis_scoring_contracts', 'ordering': ['axis_code']},
        ),
    ]
