import json
import os

from django.conf import settings
from django.db import migrations

MASTER_DATA_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'last_dta', 'TSPI Modules Master Data + Training_Pairs.json')


def import_modules(apps, schema_editor):
    """
    One-time import of the existing module master data into the DB-backed registry
    (roadmap item 3-A). Values are copied verbatim from the JSON file — nothing is
    invented or altered, including mapping_status (all PROVISIONAL in the source file).
    """
    ModuleRegistryEntry = apps.get_model('patients', 'ModuleRegistryEntry')

    if not os.path.exists(MASTER_DATA_PATH):
        return

    with open(MASTER_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    source_version = f"module-master-v{data.get('version', 'unknown')}"
    modules = data.get('tspi_modules', [])

    for mod in modules:
        code = mod.get('code')
        if not code:
            continue
        ModuleRegistryEntry.objects.update_or_create(
            code=code,
            defaults={
                "name": mod.get("name", code),
                "category": mod.get("category"),
                "primary_function": mod.get("primary_function"),
                "mechanisms": mod.get("mechanisms", []),
                "primary_axes": mod.get("primary_axes", []),
                "primary_networks": mod.get("primary_networks", []),
                "clinical_indications": mod.get("clinical_indications", []),
                "contraindications": mod.get("contraindications", []),
                "synergy_with": mod.get("synergy_with", []),
                "antagonism_with": mod.get("antagonism_with", []),
                "mapping_status": mod.get("mapping_status", "PROVISIONAL"),
                "source_version": source_version,
            }
        )


def remove_imported_modules(apps, schema_editor):
    ModuleRegistryEntry = apps.get_model('patients', 'ModuleRegistryEntry')
    ModuleRegistryEntry.objects.filter(source_version__startswith="module-master-v").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0015_module_registry_entry'),
    ]

    operations = [
        migrations.RunPython(import_modules, reverse_code=remove_imported_modules),
    ]
