import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from patients.models import Patient

class Command(BaseCommand):
    help = 'Import patients from MariaDB SQL dump (table: user)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sql-file',
            type=str,
            default='../data/u239440273_drpatrcl_sys_fixed.sql',
            help='Path to SQL dump file'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of rows (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview only, do not save'
        )
    
    def handle(self, *args, **options):
        sql_file = options['sql_file']
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write(f"📂 Reading SQL file: {sql_file}")
        
        # Read SQL file
        try:
            with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ File not found: {sql_file}"))
            self.stdout.write("   Please check the path and try again.")
            return
        
        # Extract INSERT INTO `user`
        pattern = r"INSERT INTO `user` \(.*?\) VALUES\s*(.*?);"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            self.stdout.write(self.style.ERROR("❌ Could not find INSERT INTO `user` in SQL dump"))
            return
        
        values_text = match.group(1)
        
        # Parse rows
        rows = self.parse_rows(values_text, limit)
        self.stdout.write(f"✅ Found {len(rows)} rows")
        
        # Dry run - show sample only
        if dry_run:
            self.stdout.write("\n📋 Sample data (first 5 rows, first 10 columns):")
            for i, row in enumerate(rows[:5], 1):
                preview = [str(v)[:30] + '...' if len(str(v)) > 30 else str(v) for v in row[:10]]
                self.stdout.write(f"  Row {i}: {preview}")
            self.stdout.write(f"\n   Total rows: {len(rows)}")
            self.stdout.write("   ✅ Dry run completed (no data saved)")
            return
        
        # Import
        count = 0
        errors = 0
        error_details = []
        
        self.stdout.write("\n🔄 Importing patients...")
        
        with transaction.atomic():
            for i, row_values in enumerate(rows, 1):
                try:
                    patient = self.create_patient_from_row(row_values)
                    if patient:
                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f"   📝 Imported {count} patients...")
                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        error_details.append(f"Row {i}: {str(e)[:100]}")
                    continue
        
        # Show summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✅ Import completed!"))
        self.stdout.write(f"   Created: {count} patients")
        self.stdout.write(f"   Errors: {errors}")
        if error_details:
            self.stdout.write("\n📌 Last 5 errors:")
            for err in error_details[:5]:
                self.stdout.write(self.style.WARNING(f"   • {err}"))
        self.stdout.write("="*50)
    
    def parse_rows(self, values_text, limit):
        """
        Parse SQL VALUES into rows
        Format: ('value1', 'value2', ...), ('value3', ...)
        """
        rows = []
        current_row = []
        current_value = []
        in_string = False
        escaped = False
        
        for char in values_text:
            if escaped:
                current_value.append(char)
                escaped = False
                continue
            
            if char == '\\':
                escaped = True
                continue
            
            if char == "'":
                in_string = not in_string
                if not in_string:
                    # End of string
                    val = ''.join(current_value).strip()
                    current_row.append(val if val else None)
                    current_value = []
                continue
            
            if not in_string and char == '(':
                # Start of new row
                current_row = []
                current_value = []
                continue
            
            if not in_string and char == ')':
                # End of row
                if current_row:
                    rows.append(current_row)
                    if limit and len(rows) >= limit:
                        return rows
                current_row = []
                current_value = []
                continue
            
            if in_string:
                current_value.append(char)
        
        return rows
    
    def clean_value(self, value):
        """Clean and normalize value"""
        if value is None or value == 'NULL' or value == "''" or value == '':
            return None
        return str(value).strip()
    
    def parse_date(self, date_str):
        """
        Parse date from various formats
        Supports:
        - 2023-02-23
        - 23/02/2023
        - 02/23/2023
        - 2567-08-08 (Buddhist year)
        """
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Remove time part if exists: "2023-02-23 18:59:41" -> "2023-02-23"
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        
        # 1. Try YYYY-MM-DD
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                year = int(date_str[:4])
                # Convert Buddhist year to Christian year
                if year >= 2400:
                    year = year - 543
                return datetime.strptime(f"{year}{date_str[4:]}", '%Y-%m-%d').date()
        except:
            pass
        
        # 2. Try DD/MM/YYYY
        try:
            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                day, month, year = date_str.split('/')
                year = int(year)
                if year >= 2400:
                    year = year - 543
                return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
        except:
            pass
        
        # 3. Try MM/DD/YYYY
        try:
            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                month, day, year = date_str.split('/')
                year = int(year)
                if year >= 2400:
                    year = year - 543
                return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
        except:
            pass
        
        # 4. Try just year
        try:
            if re.match(r'^\d{4}$', date_str):
                year = int(date_str)
                if year >= 2400:
                    year = year - 543
                return datetime.strptime(f"{year}-01-01", '%Y-%m-%d').date()
        except:
            pass
        
        return None
    
    def create_patient_from_row(self, values):
        """
        Create Patient from row values using correct column mapping
        Based on CREATE TABLE `user`:
        
        Index | Column Name
        0     | id
        1     | userID
        2     | date_regis
        3     | IDcard
        4     | password
        5     | prefix
        6     | fname (first_name)
        7     | lname (last_name)
        8     | sex (gender)
        9     | pregnant
        10    | bd_year
        11    | bd_date (birth_date)
        12    | age
        13    | weight
        14    | height
        15    | bmi
        16    | bmi_val
        17    | email
        18    | phone
        19    | phone2
        20    | fb_name
        21    | line
        22    | address
        23    | district
        24    | amphur
        25    | province
        26    | zipcode
        27    | country
        28    | education
        29    | career
        30    | salary
        31    | update_at
        32    | status
        33    | userId_friend
        34    | percent
        35    | branchID
        36    | status_vip
        37    | status_check
        38    | userHN
        39    | hisDrug
        40    | type
        41    | jotform
        42    | my_number
        43    | last_uID
        44    | formapp
        45    | userIDApp
        46    | nationality
        47    | ethnicity
        48    | marry_status
        49    | smoking
        50    | drink
        51    | time_sleep
        52    | time_wakeup
        53    | time_total
        54    | sleep_score
        55    | vaccinated
        56    | symptoms
        57    | disease (JSON)
        58    | disease_other
        59    | cure_disease (JSON)
        60    | cure_other
        61    | score_disease
        62    | score_pain
        63    | detail_disease
        64    | where_cure
        65    | long_cure
        66    | long_cure_type
        67    | drug_current
        68    | drug_allergy
        69    | his_medicine
        70    | his_antibiotic
        71    | quantity_medicine
        72    | purpose_medicine
        73    | reason (JSON)
        74    | reason_other
        75    | accept
        76    | who_regis
        77    | who_regis2
        78    | img_disease
        """
        
        # Get legacy_id (index 0: id)
        legacy_id = self.clean_value(values[0]) if len(values) > 0 else None
        if not legacy_id:
            return None
        
        # Helper to get value safely
        def get_val(idx):
            return self.clean_value(values[idx]) if len(values) > idx else None
        
        # === Basic Info ===
        first_name = get_val(6) or 'ไม่ระบุ'   # fname
        last_name = get_val(7) or 'ไม่ระบุ'    # lname
        
        # === Gender ===
        sex_raw = get_val(8)  # sex
        gender_map = {'ชาย': 'M', 'หญิง': 'F', 'M': 'M', 'F': 'F'}
        gender = gender_map.get(sex_raw, None)
        
        # === Birth Date ===
        bd_date_raw = get_val(11)  # bd_date
        birth_date = self.parse_date(bd_date_raw)
        
        # If bd_date is empty, try bd_year
        if not birth_date:
            bd_year = get_val(10)  # bd_year
            if bd_year:
                try:
                    year = int(bd_year)
                    if year >= 2400:
                        year = year - 543
                    birth_date = datetime.strptime(f"{year}-01-01", '%Y-%m-%d').date()
                except:
                    pass
        
        # === Status ===
        status = get_val(32) or 'pending'  # status
        
        # === Create Patient ===
        patient = Patient(
            legacy_id=legacy_id,
            hn=get_val(1),  # userID
            first_name=first_name,
            last_name=last_name,
            nickname=None,  # No nickname in user table
            phone=get_val(18) or '',  # phone
            email=get_val(17),  # email
            line_id=get_val(21),  # line
            gender=gender,
            birth_date=birth_date,
            address=get_val(22),  # address
            province=get_val(25),  # province
            district=get_val(24),  # amphur
            subdistrict=get_val(23),  # district
            postcode=get_val(26),  # zipcode
            status=status,
            
            # Intake / Clinical History
            chief_complaint=get_val(63),  # detail_disease
            present_illness=None,  # Not directly available
            past_history=get_val(57),  # disease (JSON)
            drug_allergy=get_val(68),  # drug_allergy
            current_medications=get_val(67),  # drug_current
            
            # Extra data (everything else)
            extra_data={
                'userID': get_val(1),
                'date_regis': get_val(2),
                'IDcard': get_val(3),
                'prefix': get_val(5),
                'pregnant': get_val(9),
                'bd_year': get_val(10),
                'age': get_val(12),
                'weight': get_val(13),
                'height': get_val(14),
                'bmi': get_val(15),
                'bmi_val': get_val(16),
                'phone2': get_val(19),
                'fb_name': get_val(20),
                'country': get_val(27),
                'education': get_val(28),
                'career': get_val(29),
                'salary': get_val(30),
                'update_at': get_val(31),
                'userId_friend': get_val(33),
                'percent': get_val(34),
                'branchID': get_val(35),
                'status_vip': get_val(36),
                'status_check': get_val(37),
                'userHN': get_val(38),
                'hisDrug': get_val(39),
                'type': get_val(40),
                'jotform': get_val(41),
                'my_number': get_val(42),
                'last_uID': get_val(43),
                'formapp': get_val(44),
                'userIDApp': get_val(45),
                'nationality': get_val(46),
                'ethnicity': get_val(47),
                'marry_status': get_val(48),
                'smoking': get_val(49),
                'drink': get_val(50),
                'time_sleep': get_val(51),
                'time_wakeup': get_val(52),
                'time_total': get_val(53),
                'sleep_score': get_val(54),
                'vaccinated': get_val(55),
                'symptoms': get_val(56),
                'disease_other': get_val(58),
                'cure_disease': get_val(59),
                'cure_other': get_val(60),
                'score_disease': get_val(61),
                'score_pain': get_val(62),
                'where_cure': get_val(64),
                'long_cure': get_val(65),
                'long_cure_type': get_val(66),
                'his_medicine': get_val(69),
                'his_antibiotic': get_val(70),
                'quantity_medicine': get_val(71),
                'purpose_medicine': get_val(72),
                'reason': get_val(73),
                'reason_other': get_val(74),
                'accept': get_val(75),
                'who_regis': get_val(76),
                'who_regis2': get_val(77),
                'img_disease': get_val(78),
            }
        )
        patient.save()
        return patient
