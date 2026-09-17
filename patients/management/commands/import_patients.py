import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from patients.models import Patient

class Command(BaseCommand):
    help = 'Import patients from MariaDB SQL dump'
    
    def add_arguments(self, parser):
        parser.add_argument('--sql-file', type=str, default='../data/u239440273_drpatrcl_sys_fixed.sql')
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        sql_file = options['sql_file']
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write(f"📂 Reading: {sql_file}")
        
        try:
            with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ File not found: {sql_file}"))
            return
        
        # ดึง INSERT INTO `user`
        pattern = r"INSERT INTO `user` \(.*?\) VALUES\s*(.*?);"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            self.stdout.write(self.style.ERROR("❌ Not found INSERT INTO `user`"))
            return
        
        rows = self.parse_rows(match.group(1), limit)
        self.stdout.write(f"✅ Found {len(rows)} rows")
        
        if dry_run:
            self.stdout.write("\n📋 Sample (first 3):")
            for row in rows[:3]:
                self.stdout.write(f"  {row[:8]}...")
            return
        
        count, errors = 0, 0
        with transaction.atomic():
            for i, row in enumerate(rows, 1):
                try:
                    if self.create_patient(row):
                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f"📝 {count} patients...")
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        self.stdout.write(self.style.WARNING(f"⚠️ Row {i}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Done! Created: {count}, Errors: {errors}"))
    
    def parse_rows(self, text, limit):
        rows = []
        current = []
        val = []
        in_string = False
        escaped = False
        
        for ch in text:
            if escaped:
                val.append(ch)
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if ch == "'":
                in_string = not in_string
                if not in_string:
                    current.append(''.join(val).strip())
                    val = []
                continue
            if not in_string and ch == '(':
                current = []
                val = []
                continue
            if not in_string and ch == ')':
                if current:
                    rows.append(current)
                    if limit and len(rows) >= limit:
                        return rows
                current = []
                val = []
                continue
            if in_string:
                val.append(ch)
        return rows
    
    def clean(self, v):
        if v is None or v == 'NULL' or v == "''" or v == '':
            return None
        return str(v).strip()
    
    def parse_date(self, s):
        if not s:
            return None
        s = str(s).strip()
        # 2567-08-08 → 2024-08-08
        try:
            if re.match(r'^2\d{3}-\d{2}-\d{2}$', s):
                y = int(s[:4])
                if y >= 2400:
                    y -= 543
                return datetime.strptime(f"{y}{s[4:]}", '%Y-%m-%d').date()
        except:
            pass
        # 1990-01-01
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
                y = int(s[:4])
                if y >= 2400:
                    y -= 543
                return datetime.strptime(f"{y}{s[4:]}", '%Y-%m-%d').date()
        except:
            pass
        return None
    
    def create_patient(self, values):
        legacy_id = self.clean(values[0]) if len(values) > 0 else None
        if not legacy_id:
            return None
        
        # Map gender
        gender_raw = self.clean(values[8]) if len(values) > 8 else None
        gender_map = {'M': 'M', 'F': 'F', 'ชาย': 'M', 'หญิง': 'F'}
        gender = gender_map.get(gender_raw, None)
        
        patient = Patient(
            legacy_id=legacy_id,
            hn=self.clean(values[1]) if len(values) > 1 else None,
            first_name=self.clean(values[2]) or 'ไม่ระบุ',
            last_name=self.clean(values[3]) or 'ไม่ระบุ',
            nickname=self.clean(values[4]) if len(values) > 4 else None,
            phone=self.clean(values[5]) or '',
            email=self.clean(values[6]) if len(values) > 6 else None,
            line_id=self.clean(values[7]) if len(values) > 7 else None,
            gender=gender,
            birth_date=self.parse_date(self.clean(values[9])) if len(values) > 9 else None,
            address=self.clean(values[10]) if len(values) > 10 else None,
            province=self.clean(values[11]) if len(values) > 11 else None,
            district=self.clean(values[12]) if len(values) > 12 else None,
            subdistrict=self.clean(values[13]) if len(values) > 13 else None,
            postcode=self.clean(values[14]) if len(values) > 14 else None,
            status=self.clean(values[15]) or 'pending',
            chief_complaint=self.clean(values[16]) if len(values) > 16 else None,
            present_illness=self.clean(values[17]) if len(values) > 17 else None,
            past_history=self.clean(values[18]) if len(values) > 18 else None,
            drug_allergy=self.clean(values[19]) if len(values) > 19 else None,
            current_medications=self.clean(values[20]) if len(values) > 20 else None,
            extra_data={'raw_columns': values[21:] if len(values) > 21 else []}
        )
        patient.save()
        return patient
