from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0001_initial'),  # ตรวจสอบว่าเป็น migration ล่าสุด
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='hn',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True),
        ),
    ]