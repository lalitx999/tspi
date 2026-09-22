# Generated manually for EP3. Apply only after reviewing this R0 schema change.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0016_import_module_registry_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisrecord',
            name='analysis_run_id',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='analysisrecord',
            name='identity_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='analysisrecord',
            name='evidence_provenance',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='analysisrecord',
            name='registry_versions',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='analysisrecord',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_analysis_records', to=settings.AUTH_USER_MODEL),
        ),
    ]
