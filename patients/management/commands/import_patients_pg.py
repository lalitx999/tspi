import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from patients.models import Patient

class Command(BaseCommand):
    help = 'Import patients directly from the PostgreSQL "user" table'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']

        self.stdout.write("🔌 Fetching data from legacy 'user' table...")
        
        with connection.cursor() as cursor:
            # ตรวจสอบว่ามีตาราง user หรือไม่
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user'
                );
            """)
            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.ERROR("❌ Legacy table 'user' not found in PostgreSQL."))
                return
            
            # ดึงข้อมูล
            query = 'SELECT * FROM "user"'
            if limit:
                query += f' LIMIT {limit}'
                
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        self.stdout.write(f"✅ Found {len(rows)} legacy rows in table 'user'")

        if dry_run:
            self.stdout.write("📋 Dry-run mode: Printing first 3 mapped patients:")
            for i, row in enumerate(rows[:3], 1):
                mapped = self.map_patient_data(row)
                self.stdout.write(f"Patient {i}: {mapped.first_name} {mapped.last_name} (HN: {mapped.hn}, Gender: {mapped.gender}, Birth: {mapped.birth_date})")
            return

        self.stdout.write("📝 Migrating to 'patients' table...")
        count = 0
        errors = 0
        
        with transaction.atomic():
            for i, row in enumerate(rows, 1):
                try:
                    patient = self.map_patient_data(row)
                    # บันทึกหรืออัปเดตอ้างอิงตาม legacy_id
                    existing = Patient.objects.filter(legacy_id=patient.legacy_id).first()
                    if existing:
                        # อัปเดตข้อมูล
                        for field in patient._meta.fields:
                            if field.name not in ['id', 'created_at']:
                                setattr(existing, field.name, getattr(patient, field.name))
                        existing.save()
                    else:
                        patient.save()
                    
                    count += 1
                    if count % 200 == 0:
                        self.stdout.write(f"   Processed {count} patients...")
                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        self.stdout.write(self.style.WARNING(f"⚠️ Row {i} (userID: {row.get('userID')}): {e}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Migration Completed! Migrated: {count}, Errors: {errors}"))

    def clean(self, v):
        if v is None or v == 'NULL' or v == "''" or v == '':
            return None
        return str(v).strip()

    def parse_date(self, s):
        if not s:
            return None
        s = str(s).strip()
        
        # 1. จัดการวันที่ฟอร์แมต "Dec 23, 2516" (พ.ศ. 543 ปีต่าง)
        # Regex เช็คเช่น "Dec 23, 2516"
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        match_mdy = re.match(r'^([A-Za-z]{3})\s+(\d+),\s+(\d{4})$', s)
        if match_mdy:
            m_str, d_str, y_str = match_mdy.groups()
            m = month_map.get(m_str.capitalize(), 1)
            d = int(d_str)
            y = int(y_str)
            if y >= 2400:
                y -= 543
            try:
                return datetime(y, m, d).date()
            except:
                pass

        # 2. จัดการฟอร์แมต ISO หรือ YYYY-MM-DD (เช่น 2567-08-08 หรือ 1990-01-01)
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
                y = int(s[:4])
                if y >= 2400:
                    y -= 543
                return datetime.strptime(f"{y}{s[4:]}", '%Y-%m-%d').date()
        except:
            pass

        return None

    def map_patient_data(self, row):
        legacy_id = self.clean(row.get('userID'))
        if not legacy_id:
            # ใช้ id เผื่อไม่มี userID
            legacy_id = f"legacy_{row.get('id')}"

        # แปลงเพศ ชาย -> M, หญิง -> F
        gender_raw = self.clean(row.get('sex'))
        gender = None
        if gender_raw:
            if 'ชาย' in gender_raw or gender_raw.upper() in ['M', 'MALE']:
                gender = 'M'
            elif 'หญิง' in gender_raw or gender_raw.upper() in ['F', 'FEMALE']:
                gender = 'F'
            else:
                gender = 'O'

        # ทำความสะอาดเบอร์โทรศัพท์ (ลบวงเล็บและเว้นวรรคออก)
        phone_raw = self.clean(row.get('phone')) or ''
        phone = re.sub(r'[\(\)\s-]', '', phone_raw)

        # แปลงวันเกิด
        bd_raw = self.clean(row.get('bd_date')) or self.clean(row.get('bdDate'))
        birth_date = self.parse_date(bd_raw)
        
        # คลีน HN
        hn = self.clean(row.get('userHN')) or self.clean(row.get('userID'))
        if hn == '':
            hn = None

        # เก็บข้อมูลดิบไว้ใน extra_data
        extra_data = {
            'weight': self.clean(row.get('weight')),
            'height': self.clean(row.get('height')),
            'bmi': self.clean(row.get('bmi')),
            'pregnant': self.clean(row.get('pregnant')),
            'career': self.clean(row.get('career')),
            'education': self.clean(row.get('education')),
            'smoking': self.clean(row.get('smoking')),
            'sleep_score': row.get('sleep_score'),
        }

        # สร้าง Object Patient (ยังไม่เซฟ)
        patient = Patient(
            legacy_id=legacy_id,
            hn=hn,
            id_card=self.clean(row.get('IDcard')),
            first_name=self.clean(row.get('fname')) or 'ไม่ระบุชื่อ',
            last_name=self.clean(row.get('lname')) or 'ไม่ระบุสกุล',
            nickname=self.clean(row.get('prefix')), # ใช้ prefix แทนถ้าไม่มี
            phone=phone,
            email=self.clean(row.get('email')),
            line_id=self.clean(row.get('line')),
            gender=gender,
            birth_date=birth_date,
            address=self.clean(row.get('address')),
            province=self.clean(row.get('province')),
            district=self.clean(row.get('amphur')),
            subdistrict=self.clean(row.get('district')),
            postcode=self.clean(row.get('zipcode')),
            status=self.clean(row.get('status')) or 'pending',
            chief_complaint=self.clean(row.get('symptoms')),
            past_history=self.clean(row.get('disease')),
            drug_allergy=self.clean(row.get('drug_allergy')),
            current_medications=self.clean(row.get('drug_current')),
            extra_data=extra_data
        )
        return patient
