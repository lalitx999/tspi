import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('patients', '0019_axis_scoring_contract')]
    operations = [
        migrations.AddField(model_name='auditlog', name='event_type', field=models.CharField(db_index=True, default='LEGACY', max_length=80)),
        migrations.AddField(model_name='auditlog', name='request_method', field=models.CharField(blank=True, max_length=10)),
        migrations.AddField(model_name='auditlog', name='request_path', field=models.CharField(blank=True, db_index=True, max_length=500)),
        migrations.AddField(model_name='auditlog', name='response_status', field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='auditlog', name='user_agent', field=models.CharField(blank=True, max_length=500)),
        migrations.AddField(model_name='auditlog', name='request_id', field=models.UUIDField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='auditlog', name='metadata', field=models.JSONField(blank=True, default=dict)),
    ]
