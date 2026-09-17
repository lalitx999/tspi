import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from patients.models import Patient, PatientBiologicalRecord, AuditLog
from patients.serializers import PatientSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def patient_activate(request):
    """
    Step 1 of Activation: Verify phone + name against 3,028 imported legacy patients in PostgreSQL
    """
    phone = request.data.get("phone", "").strip()
    name_query = request.data.get("name", "").strip().lower().replace(" ", "")

    if not phone or not name_query:
        return Response({"error": "กรุณากรอกหมายเลขโทรศัพท์และชื่อผู้ป่วย"}, status=status.HTTP_400_BAD_REQUEST)

    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) != 10:
        return Response({"error": "กรุณากรอกหมายเลขโทรศัพท์ให้ครบ 10 หลัก"}, status=status.HTTP_400_BAD_REQUEST)

    # Clean legacy formats matching phone numbers like "(084) 627-7101" or "084-627-7101"
    formatted_options = [clean_phone]
    if len(clean_phone) == 10:
        formatted_options.append(f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}")
        formatted_options.append(f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}")

    # Query from PostgreSQL Patient table
    matched_patient = None
    patients = Patient.objects.filter(phone__in=formatted_options)

    for p in patients:
        db_fname = p.first_name.strip().lower().replace(" ", "")
        db_lname = p.last_name.strip().lower().replace(" ", "")
        
        # Check if query matches first name or last name
        if name_query in db_fname or name_query in db_lname:
            matched_patient = p
            break

    if not matched_patient:
        return Response({"error": "ไม่พบข้อมูลหมายเลขโทรศัพท์หรือชื่อนี้ในระบบ กรุณาตรวจสอบหรือติดต่อคลินิก"}, status=status.HTTP_404_NOT_FOUND)

    # Check if this patient already has an activated Django account
    if matched_patient.id_card:
        existing_user = User.objects.filter(username=matched_patient.id_card).exists()
        if existing_user:
            return Response({"error": "คนไข้รายนี้ได้ทำการเปิดใช้งานบัญชีเรียบร้อยแล้ว กรุณาเข้าสู่ระบบผ่านหน้าล็อกอิน"}, status=status.HTTP_400_BAD_REQUEST)

    # Return patient data to pre-fill registration wizard
    serializer = PatientSerializer(matched_patient)
    return Response({
        "success": True,
        "patient": serializer.data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def patient_register(request):
    """
    Step 2: Proceed with Wizard Registration. Create Django user and link to Patient EMR record in PostgreSQL
    """
    id_card = request.data.get("IDcard", "").strip().replace(" ", "")
    password = request.data.get("password", "")
    email = request.data.get("email", "").strip()
    
    is_activation_mode = request.data.get("is_activation_mode", False)
    existing_doc_id = request.data.get("existing_doc_id")

    if not id_card or len(id_card) != 13:
        return Response({"error": "กรุณากรอกเลขบัตรประชาชนให้ครบ 13 หลัก"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not password:
        return Response({"error": "กรุณากำหนดรหัสผ่าน"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if Django User already exists
    if User.objects.filter(username=id_card).exists():
        return Response({"error": "เลขบัตรประชาชนนี้เคยทำการลงทะเบียนแล้ว กรุณาใช้หน้าล็อกอิน"}, status=status.HTTP_400_BAD_REQUEST)

    # Create Django User
    try:
        user_email = email if email else f"{id_card}@tspi-patient.com"
        user = User.objects.create_user(username=id_card, email=user_email, password=password)
    except Exception as e:
        return Response({"error": f"เกิดข้อผิดพลาดในการสร้างบัญชี: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Link/Create Patient profile
    patient = None
    if is_activation_mode and existing_doc_id:
        # Update existing legacy patient profile
        patient = Patient.objects.filter(id=existing_doc_id).first()
        if patient:
            patient.id_card = id_card
            patient.email = user_email
            # Pre-fill other wizard fields from request data
            patient.nickname = request.data.get("nickname", patient.nickname)
            patient.phone = request.data.get("phone", patient.phone)
            patient.address = request.data.get("address", patient.address)
            patient.province = request.data.get("province", patient.province)
            patient.district = request.data.get("district", patient.district)
            patient.subdistrict = request.data.get("subdistrict", patient.subdistrict)
            patient.postcode = request.data.get("zipcode", patient.postcode)
            
            # Save extra questionnaire data to extra_data JSON field
            extra_data = patient.extra_data or {}
            for field in [
                'nationality', 'ethnicity', 'marry_status', 'weight', 'height', 'smoking', 'drink',
                'time_sleep', 'time_wakeup', 'sleep_score', 'vaccinated', 'symptoms', 'disease', 
                'disease_other', 'cure_disease', 'cure_other', 'score_disease', 'score_pain', 
                'drug_current', 'drug_allergy', 'detail_disease', 'where_cure', 'long_cure', 
                'long_cure_type', 'his_medicine', 'his_antibiotic', 'quantity_medicine', 
                'purpose_medicine', 'reason', 'reason_other', 'who_regis'
            ]:
                if field in request.data:
                    extra_data[field] = request.data[field]
            patient.extra_data = extra_data
            patient.save()
    
    if not patient:
        # Create a new patient profile
        hn = request.data.get("hn") or f"HN{secrets.token_hex(4).upper()}"
        patient = Patient.objects.create(
            legacy_id=id_card,
            hn=hn,
            id_card=id_card,
            first_name=request.data.get("fname", ""),
            last_name=request.data.get("lname", ""),
            nickname=request.data.get("nickname", ""),
            phone=request.data.get("phone", ""),
            email=user_email,
            gender=request.data.get("sex", "O"),
            birth_date=request.data.get("bd_date") or None,
            address=request.data.get("address", ""),
            province=request.data.get("province", ""),
            district=request.data.get("district", ""),
            subdistrict=request.data.get("subdistrict", ""),
            postcode=request.data.get("zipcode", ""),
            status="pending"
        )
        # Store extra wizard questionnaire details
        extra_data = {}
        for field in [
            'nationality', 'ethnicity', 'marry_status', 'weight', 'height', 'smoking', 'drink',
            'time_sleep', 'time_wakeup', 'sleep_score', 'vaccinated', 'symptoms', 'disease', 
            'disease_other', 'cure_disease', 'cure_other', 'score_disease', 'score_pain', 
            'drug_current', 'drug_allergy', 'detail_disease', 'where_cure', 'long_cure', 
            'long_cure_type', 'his_medicine', 'his_antibiotic', 'quantity_medicine', 
            'purpose_medicine', 'reason', 'reason_other', 'who_regis'
        ]:
            if field in request.data:
                extra_data[field] = request.data[field]
        patient.extra_data = extra_data
        patient.save()

    # Link LINE OA account if line_user_id passed from registration URL
    line_user_id = request.data.get("line_user_id", "").strip()
    if line_user_id:
        patient.line_user_id = line_user_id
        patient.save()

        try:
            from patients.line_flex_builder import build_verified_patient_flex
            from patients.views_line import push_line_message
            channel_access_token = os.environ.get("LINE_DOCTORPATT_CHANNEL_ACCESS_TOKEN", "")
            if channel_access_token:
                flex_msg = build_verified_patient_flex(patient)
                push_line_message(line_user_id, [flex_msg], channel_access_token)
        except Exception as push_err:
            print("⚠️ Failed to push welcome LINE Flex Message after registration:", push_err)

    # Generate JWT Tokens for Next.js login state
    tokens = get_tokens_for_user(user)

    AuditLog.objects.create(
        actor_id=id_card,
        target_id=str(patient.id),
        action="USER_REGISTRATION_SUCCESS",
        layer="AUTH",
        client_ip="server-side",
        governance_status="PATIENT_ACCESSIBLE"
    )

    serializer = PatientSerializer(patient)
    return Response({
        "success": True,
        "tokens": tokens,
        "patient": serializer.data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def patient_login(request):
    """
    Authenticate Patient via Citizen ID or Email using Django credentials and issue JWT
    """
    auth_method = request.data.get("auth_method", "idcard") # "idcard" or "email"
    password = request.data.get("password")
    
    username = ""
    if auth_method == "idcard":
        citizen_id = request.data.get("citizenId", "").strip().replace(" ", "")
        username = citizen_id
    else:
        email = request.data.get("email", "").strip()
        # Find Django user by email
        user_by_email = User.objects.filter(email=email).first()
        if user_by_email:
            username = user_by_email.username
        else:
            return Response({"error": "ไม่พบบัญชีผู้ใช้งานที่ใช้อีเมลนี้"}, status=status.HTTP_400_BAD_REQUEST)

    if not username or not password:
        return Response({"error": "กรุณากรอกข้อมูลเพื่อเข้าสู่ระบบให้ครบถ้วน"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "เลขบัตรประชาชนหรือรหัสผ่านไม่ถูกต้อง หรือคุณยังไม่ได้ทำการลงทะเบียนเปิดใช้งานบัญชีครั้งแรก"}, status=status.HTTP_401_UNAUTHORIZED)

    # Find the linked Patient profile
    patient = Patient.objects.filter(id_card=user.username).first()
    if not patient:
        patient = Patient.objects.filter(email=user.email).first()

    if not patient:
        return Response({"error": "พบบัญชีล็อกอินแต่ไม่มีฐานข้อมูลสุขภาพในประวัติคลินิก กรุณาติดต่อเจ้าหน้าที่"}, status=status.HTTP_404_NOT_FOUND)

    tokens = get_tokens_for_user(user)

    AuditLog.objects.create(
        actor_id=user.username,
        target_id=str(patient.id),
        action="USER_LOGIN_SUCCESS",
        layer="AUTH",
        client_ip="server-side",
        governance_status="PATIENT_ACCESSIBLE"
    )

    serializer = PatientSerializer(patient)
    return Response({
        "success": True,
        "tokens": tokens,
        "patient": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_me(request):
    """
    Get current logged in patient profile based on JWT Token header
    """
    user = request.user
    
    # Lookup profile
    patient = Patient.objects.filter(id_card=user.username).first()
    if not patient:
        patient = Patient.objects.filter(email=user.email).first()

    if not patient:
        return Response({"error": "ไม่พบโปรไฟล์แพทย์หรือคนไข้ของคุณในฐานข้อมูล"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PatientSerializer(patient)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_login(request):
    """
    Authenticate Doctor/Staff via Email directly against public.admin table and issue JWT
    """
    email = request.data.get("email", "").strip()
    password = request.data.get("password")

    print(f"🔍 [DEBUG doctor_login] Received email='{email}', password length={len(password) if password else 0}")

    if not email or not password:
        return Response({"error": "กรุณากรอกอีเมลและรหัสผ่านให้ครบถ้วน"}, status=status.HTTP_400_BAD_REQUEST)

    admin_row = None
    from django.db import connection
    import hashlib

    # 1. Direct authentication against public.admin table
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password, fname, lname, email FROM public.admin WHERE LOWER(TRIM(email)) = %s", [email.lower()])
            admin_row = cursor.fetchone()
            print(f"🔍 [DEBUG public.admin query result for '{email}']:", admin_row)

            if not admin_row:
                cursor.execute("SELECT id, email FROM public.admin ORDER BY id ASC")
                all_emails = cursor.fetchall()
                print("🔍 [DEBUG all emails in public.admin]:", all_emails)
    except Exception as db_err:
        print("⚠️ Error querying public.admin table:", db_err)

    if admin_row:
        admin_id, legacy_username, stored_password, fname, lname, legacy_email = admin_row
        
        md5_pw = hashlib.md5(password.encode('utf-8')).hexdigest()
        sha256_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        is_match = (password == stored_password) or (md5_pw == stored_password) or (sha256_pw == stored_password)
        
        if not is_match:
            return Response({"error": "รหัสผ่านไม่ถูกต้อง"}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Ensure corresponding Django User exists for JWT token generation
        user = User.objects.filter(email__iexact=email).first()
        clean_username = legacy_username or email.split('@')[0]
        
        if not user:
            if User.objects.filter(username=clean_username).exists():
                import secrets
                clean_username = f"{clean_username}_{secrets.token_hex(2)}"
            user = User.objects.create_user(
                username=clean_username,
                email=email,
                password=password,
                first_name=fname or "",
                last_name=lname or "",
                is_staff=True
            )
        else:
            user.set_password(password)
            user.is_staff = True
            user.save()
            
        tokens = get_tokens_for_user(user)

        AuditLog.objects.create(
            actor_id=user.username,
            target_id=str(user.id),
            action="DOCTOR_LOGIN_SUCCESS",
            layer="AUTH",
            client_ip="server-side",
            governance_status="SYSTEM"
        )

        return Response({
            "success": True,
            "tokens": tokens,
            "user": {
                "id": user.id,
                "admin_id": admin_id,
                "username": user.username,
                "email": user.email,
                "first_name": fname or user.first_name,
                "last_name": lname or user.last_name,
                "name": f"{fname or user.first_name} {lname or user.last_name}".strip() or user.username
            }
        })

    # 2. Fallback to auth_user table if not found in public.admin
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response({"error": "ไม่พบบัญชีผู้ใช้งานที่ใช้อีเมลนี้ในระบบ"}, status=status.HTTP_400_BAD_REQUEST)

    authenticated_user = authenticate(username=user.username, password=password)
    if not authenticated_user:
        return Response({"error": "รหัสผ่านไม่ถูกต้อง"}, status=status.HTTP_401_UNAUTHORIZED)

    if not authenticated_user.is_staff:
        return Response({"error": "คุณไม่มีสิทธิ์เข้าถึงในฐานะแพทย์หรือเจ้าหน้าที่ของระบบ"}, status=status.HTTP_403_FORBIDDEN)

    tokens = get_tokens_for_user(authenticated_user)

    AuditLog.objects.create(
        actor_id=authenticated_user.username,
        target_id=str(authenticated_user.id),
        action="DOCTOR_LOGIN_SUCCESS",
        layer="AUTH",
        client_ip="server-side",
        governance_status="SYSTEM"
    )

    return Response({
        "success": True,
        "tokens": tokens,
        "user": {
            "id": authenticated_user.id,
            "username": authenticated_user.username,
            "email": authenticated_user.email,
            "first_name": authenticated_user.first_name,
            "last_name": authenticated_user.last_name,
            "name": f"{authenticated_user.first_name} {authenticated_user.last_name}".strip() or authenticated_user.username
        }
    })


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def doctor_me(request):
    """
    Get or update current logged in doctor profile details based on JWT Token
    """
    user = request.user
    if not user.is_staff:
        return Response({"error": "คุณไม่มีสิทธิ์เข้าถึงในฐานะแพทย์หรือเจ้าหน้าที่ของระบบ"}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
            
        user.save()

    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "role": "doctor"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_register(request):
    """
    Register a Doctor/Staff account in Django (creates a user with is_staff=True)
    """
    name = request.data.get("name", "").strip()
    email = request.data.get("email", "").strip()
    password = request.data.get("password")

    if not name or not email or not password:
        return Response({"error": "กรุณากรอกข้อมูลให้ครบถ้วน"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"error": "อีเมลนี้เคยลงทะเบียนแล้ว"}, status=status.HTTP_400_BAD_REQUEST)

    # Use email prefix or email itself as username
    username = email.split('@')[0]
    if User.objects.filter(username=username).exists():
        import secrets
        username = f"{username}_{secrets.token_hex(2)}"

    try:
        # Split first and last name if possible
        name_parts = name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True
        )

        # Also insert directly into public.admin table
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO public.admin ("userID", username, password, fname, lname, email, "branchID", "positionID", create_at, update_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, [username, username, password, first_name, last_name, email, "B001", "3"])
        except Exception as admin_ins_err:
            print("⚠️ Insert into public.admin error:", admin_ins_err)
    except Exception as e:
        return Response({"error": f"ไม่สามารถสร้างบัญชีได้: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    tokens = get_tokens_for_user(user)

    AuditLog.objects.create(
        actor_id=username,
        target_id=str(user.id),
        action="DOCTOR_REGISTRATION_SUCCESS",
        layer="AUTH",
        client_ip="server-side",
        governance_status="SYSTEM"
    )

    return Response({
        "success": True,
        "tokens": tokens,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": name
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    """
    Register or update the FCM token for the currently authenticated patient.
    Saves the token inside the patient's extra_data JSON field.
    """
    user = request.user
    token = request.data.get("fcm_token")
    if not token:
        return Response({"error": "กรุณาระบุ fcm_token ในคำขอ"}, status=status.HTTP_400_BAD_REQUEST)

    patient = Patient.objects.filter(id_card=user.username).first()
    if not patient:
        patient = Patient.objects.filter(email=user.email).first()

    if not patient:
        return Response({"error": "ไม่พบข้อมูลโปรไฟล์คนไข้ในระบบ"}, status=status.HTTP_404_NOT_FOUND)

    if not patient.extra_data:
        patient.extra_data = {}

    patient.extra_data["fcm_token"] = token
    patient.save()

    return Response({
        "success": True,
        "message": "ลงทะเบียน FCM Token เข้าสู่ระบบ EMR สำเร็จ"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for the authenticated patient/user.
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    
    if not old_password or not new_password:
        return Response({"error": "กรุณาระบุรหัสผ่านเดิมและรหัสผ่านใหม่"}, status=status.HTTP_400_BAD_REQUEST)
        
    if not user.check_password(old_password):
        return Response({"error": "รหัสผ่านเดิมไม่ถูกต้อง"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        user.set_password(new_password)
        user.save()
        
        # Log this event
        AuditLog.objects.create(
            actor_id=user.username,
            target_id=str(user.id),
            action="USER_PASSWORD_CHANGE_SUCCESS",
            layer="AUTH",
            client_ip="server-side",
            governance_status="PATIENT_ACCESSIBLE"
        )
        
        return Response({
            "success": True,
            "message": "เปลี่ยนรหัสผ่านสำเร็จแล้ว"
        })
    except Exception as e:
        return Response({"error": f"ไม่สามารถเปลี่ยนรหัสผ่านได้: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




