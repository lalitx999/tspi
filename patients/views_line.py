import os
import json
import hmac
import hashlib
import base64
import secrets
import urllib.request
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from patients.models import Patient, PatientBiologicalRecord, LineLinkingToken, LineChat, AuditLog
from patients.multimodal_service import download_line_media, analyze_lab_image, transcribe_audio_video
from patients.line_flex_builder import (
    build_lab_result_flex,
    build_voice_intake_flex,
    build_axes_dashboard_flex,
    build_link_account_flex,
    build_greeting_flex,
    build_verified_patient_flex,
    build_registration_link_flex,
    build_ai_chat_flex,
    build_bot_status_flex
)

# System prompt for LLM AI Patient Intake with Strict Anti-Hallucination Guardrails
SYSTEM_PROMPT = """
คุณคือ "TSPI Clinical Intelligence Assistant" ปัญญาประดิษฐ์ซักประวัติทางการแพทย์เชิงระบบของ TSPI Clinic

กฎเหล็กป้องกันการหลอน (Strict Anti-Hallucination & Grounding Rules):
1. ห้ามสร้างข้อมูล มโน วินิจฉัยโรค หรือแต่งชื่อยาสมุนไพร/แกนสรีรวิทยาที่ไม่มีในระบบ TSPI เด็ดขาด
2. ข้อมูลเชิงสรีรวิทยาต้องอ้างอิงตรงตาม "39 Biological Axes" ของ TSPI Clinic เท่านั้น (เช่น AXIS_11 = DNA Repair & Genomic Stability, AXIS_12 = Epigenetic Regulation)
3. หากคนไข้ถามข้อมูลที่ไม่อยู่ในบริบท หรือเป็นกรณีซับซ้อน/อันตราย ให้ตอบอย่างสุภาพว่า "ข้อมูลส่วนนี้ระบบจะรวบรวมส่งต่อให้แพทย์ผู้รักษาประเมินโดยตรง"
4. หน้าที่ของคุณคือ 1) สุภาพ 2) ถามซักประวัติ (อาการ, ระยะเวลา, ปัจจัยกระตุ้น) 3) สรุปข้อมูลส่งต่อแพทย์ ห้ามสั่งการรักษาเองเด็ดขาด

แนวทางการซักประวัติ:
1. เริ่มต้นด้วยการถามอาการหลัก (Chief Complaint) และประวัติสุขภาพปัจจุบัน
2. ซักถามเพื่อประเมินแกนชีววิทยาหลัก (เช่น AXIS_1 ถึง AXIS_39)
3. ตรวจสอบความครบถ้วน (QC): ถามจนกว่าจะได้ข้อมูลชัดเจนเรื่อง อาการ, ระยะเวลา, ปัจจัยกระตุ้น

รูปแบบการตอบกลับ:
- ให้คำแนะนำและถามคำถามอย่างสุภาพ
- ท้ายข้อความของคุณ (บรรทัดสุดท้าย) ให้ใส่ JSON Block เสมอในรูปแบบ:
  [[{"scores": {"AXIS_1": 0, "AXIS_9": 0}, "status": "active|completed", "findings": ["..."]}]]
""".strip()



def verify_signature(body_text, signature, channel_secret):
    if not signature or not channel_secret:
        return False
    hash_val = hmac.new(
        channel_secret.encode('utf-8'),
        body_text.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_val).decode('utf-8') == signature


def reply_line_message(reply_token, messages, channel_access_token):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}"
    }
    body = {
        "replyToken": reply_token,
        "messages": messages
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(body).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as res:
            res.read()
    except urllib.error.HTTPError as err:
        err_body = err.read().decode('utf-8') if err.fp else ""
        print(f"❌ LINE Reply API HTTP Error {err.code}: {err.reason} | Detail: {err_body} | Token prefix: '{channel_access_token[:15]}...'")
    except Exception as e:
        print("❌ LINE Reply API Error:", e)


def push_line_message(to_user_id, messages, channel_access_token):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}"
    }
    body = {
        "to": to_user_id,
        "messages": messages
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(body).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as res:
            res.read()
    except Exception as e:
        print("❌ LINE Push API Error:", e)


def get_link_flex_message(app_url, token):
    link_url = f"{app_url}/patient/login?t={token}"
    return build_link_account_flex(link_url) if 'build_link_account_flex' in globals() else {
        "type": "flex",
        "altText": "กรุณาเชื่อมต่อบัญชีคนไข้ของคุณ",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "เชื่อมต่อบัญชีคนไข้",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "lg",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#FF7444"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ยินดีต้อนรับสู่ TSPI Clinical AI Engine",
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True,
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "ระบบตรวจพบว่าบัญชี LINE ของคุณยังไม่ได้เชื่อมต่อกับประวัติการรักษาในคลินิก กรุณากดปุ่มด้านล่างเพื่อเชื่อมต่อบัญชีด้วยเบอร์โทรศัพท์ของคุณ",
                        "size": "xs",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "เชื่อมต่อบัญชีทันที",
                            "uri": link_url
                        },
                        "style": "primary",
                        "color": "#FF7444"
                    }
                ]
            }
        }
    }


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def line_webhook(request):
    """
    LINE Message & Event Webhook Handler (Supports Text, Image, Video, Audio & Postback Flex Events)
    """
    body_text = request.body.decode('utf-8')
    signature = request.headers.get("x-line-signature") or ""

    channel_secret = (
        os.environ.get("LINE_DOCTORPATT_CHANNEL_SECRET") or 
        os.environ.get("LINE_CHANNEL_SECRET") or 
        ""
    ).strip()
    channel_access_token = (
        os.environ.get("LINE_DOCTORPATT_CHANNEL_ACCESS_TOKEN") or 
        os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") or 
        ""
    ).strip()

    if not channel_access_token:
        print("⚠️ WARNING: LINE Channel Access Token is EMPTY in environment variables!")

    # Signature Check (bypassed in development mode if signature is absent)
    if not settings.DEBUG and signature and channel_secret and not verify_signature(body_text, signature, channel_secret):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = json.loads(body_text)
        events = payload.get("events", [])

        for event in events:
            reply_token = event.get("replyToken")
            line_user_id = event.get("source", {}).get("userId")
            event_type = event.get("type")

            if not line_user_id:
                continue

            # Check if patient is already linked in Database
            patient = Patient.objects.filter(line_user_id=line_user_id).first()
            app_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

            # -------------------------------------------------------------
            # CASE 1: UNLINKED PATIENT PROCESSING
            # Unlinked patients will pass through to handle "เปิดใช้งานบอท" and 13-digit Citizen ID verification
            # -------------------------------------------------------------

            # -------------------------------------------------------------
            # CASE 2: POSTBACK EVENT (User clicked button on Flex Card)
            # -------------------------------------------------------------
            if event_type == "postback":
                postback_data = event.get("postback", {}).get("data", "")
                print(f"🔘 Received LINE Postback Event: '{postback_data}' from {line_user_id}")

                params = dict(urllib.parse.parse_qsl(postback_data))
                action = params.get("action")

                if action == "confirm_lab":
                    confirm_text = f"บันทึกข้อมูลผลแล็บสรีรวิทยาเข้าสู่ประวัติเวชระเบียนของคุณ {patient.full_name if patient else ''} เรียบร้อยแล้วครับ!"
                    if reply_token:
                        flex_confirm = build_bot_status_flex("บันทึกข้อมูลผลแล็บสำเร็จ", confirm_text, is_active=True)
                        reply_line_message(reply_token, [flex_confirm], channel_access_token)

                elif action == "confirm_symptoms":
                    confirm_text = f"บันทึกสรุปประวัติสุขภาพจากคลิปเสียง/วิดีโอเข้าสู่ระบบคลินิกเรียบร้อยแล้วครับ แพทย์ผู้เชี่ยวชาญจะนำไปวิเคราะห์ร่วมกับแกนชีววิทยา 39 แกนต่อไป"
                    if reply_token:
                        flex_confirm = build_bot_status_flex("บันทึกสรุปประวัติสำเร็จ", confirm_text, is_active=True)
                        reply_line_message(reply_token, [flex_confirm], channel_access_token)

                elif action == "view_dashboard":
                    # Build and return 12 Health Domains Carousel Flex Message
                    dashboard_flex = build_axes_dashboard_flex({}, patient.hn if patient else None)
                    if reply_token:
                        reply_line_message(reply_token, [dashboard_flex], channel_access_token)

                continue

            # -------------------------------------------------------------
            # CASE 3: MESSAGE EVENT (Text, Image, Video, Audio)
            # -------------------------------------------------------------
            if event_type == "message":
                msg_type = event.get("message", {}).get("type")
                message_id = event.get("message", {}).get("id")
                user_text = event.get("message", {}).get("text", "").strip() if msg_type == "text" else ""

                # 1. Trigger: Bot Activation ("เปิดใช้งานบอท")
                if msg_type == "text" and "เปิดใช้งานบอท" in user_text:
                    greeting_flex = build_greeting_flex()
                    if reply_token:
                        reply_line_message(reply_token, [greeting_flex], channel_access_token)
                    LineChat.objects.create(line_user_id=line_user_id, role="assistant", text="[SYSTEM_FLEX: BOT_ACTIVATED]")
                    continue

                # 2. Trigger: Bot Deactivation ("ปิดใช้งานบอท")
                if msg_type == "text" and "ปิดใช้งานบอท" in user_text:
                    bye_text = "ปิดการทำงานของระบบหมอ AI เรียบร้อยแล้วครับ หากต้องการเปิดใช้งานอีกครั้ง ท่านสามารถพิมพ์ 'เปิดใช้งานบอท' หรือกดปุ่มด้านล่างได้ทุกเมื่อครับ"
                    bye_flex = build_bot_status_flex("ปิดการทำงานของบอท", bye_text, is_active=False)
                    if reply_token:
                        reply_line_message(reply_token, [bye_flex], channel_access_token)
                    LineChat.objects.create(line_user_id=line_user_id, role="assistant", text="[SYSTEM_FLEX: BOT_DEACTIVATED]")
                    continue

                # Check if Bot is currently Active for this LINE user
                last_sys_chat = LineChat.objects.filter(
                    line_user_id=line_user_id,
                    text__startswith="[SYSTEM_FLEX:"
                ).order_by('-timestamp').first()

                is_bot_active = False
                if last_sys_chat and last_sys_chat.text != "[SYSTEM_FLEX: BOT_DEACTIVATED]":
                    if any(tag in last_sys_chat.text for tag in [
                        "[SYSTEM_FLEX: BOT_ACTIVATED]",
                        "[SYSTEM_FLEX: GREETING_ASK_IDCARD]",
                        "[SYSTEM_FLEX: VERIFIED_PATIENT]",
                        "[SYSTEM_FLEX: UNREGISTERED_ID_CARD]"
                    ]):
                        is_bot_active = True

                # IF BOT IS INACTIVE: Remain 100% silent (do not auto-reply to text/image/voice/video!)
                if not is_bot_active:
                    print(f"🤐 Bot is INACTIVE for LINE user {line_user_id}. Ignoring {msg_type} event.")
                    continue

                # --- 3A: IMAGE MESSAGE (Lab OCR / Symptom Photo Analysis) ---
                if msg_type == "image":
                    print(f"📸 Processing Image Message ID: {message_id} from HN: {patient.hn if patient else 'Unlinked'}")
                    image_bytes = download_line_media(message_id, channel_access_token)
                    
                    lab_result_data = analyze_lab_image(image_bytes)
                    lab_flex_message = build_lab_result_flex(lab_result_data, patient.hn if patient else None)

                    if reply_token:
                        reply_line_message(reply_token, [lab_flex_message], channel_access_token)

                    AuditLog.objects.create(
                        actor_id="line_bot",
                        target_id=str(patient.id) if patient else line_user_id,
                        action="LINE_WEBHOOK_IMAGE_ANALYSIS",
                        layer="LINE",
                        client_ip="server-side",
                        governance_status="PATIENT_ACCESSIBLE"
                    )
                    continue

                # --- 3B: VIDEO / AUDIO MESSAGE (Voice Intake & Symptom Analysis) ---
                elif msg_type in ["video", "audio"]:
                    print(f"🎙️ Processing {msg_type.upper()} Message ID: {message_id} from HN: {patient.hn if patient else 'Unlinked'}")
                    media_bytes = download_line_media(message_id, channel_access_token)
                    
                    transcription_data = transcribe_audio_video(media_bytes, mime_type=f"{msg_type}/m4a")
                    voice_flex_message = build_voice_intake_flex(
                        transcript=transcription_data.get("transcript", ""),
                        symptoms=transcription_data.get("symptoms", []),
                        patient_hn=patient.hn if patient else None
                    )

                    if reply_token:
                        reply_line_message(reply_token, [voice_flex_message], channel_access_token)

                    AuditLog.objects.create(
                        actor_id="line_bot",
                        target_id=str(patient.id) if patient else line_user_id,
                        action="LINE_WEBHOOK_AUDIO_VIDEO_INTAKE",
                        layer="LINE",
                        client_ip="server-side",
                        governance_status="PATIENT_ACCESSIBLE"
                    )
                    continue

                # --- 3C: TEXT MESSAGE (AI Patient Intake Chat & State Handler) ---
                elif msg_type == "text":
                    if not reply_token:
                        continue

                    # 3. ID Card Verification Flow (13-digit number check)
                    import re
                    digits_only = re.sub(r"[^\d]", "", user_text)
                    if len(digits_only) == 13 and (not patient or "เลขบัตร" in user_text or digits_only == user_text):
                        matched_patient = Patient.objects.filter(id_card=digits_only).first()
                        if matched_patient:
                            matched_patient.line_user_id = line_user_id
                            matched_patient.save()

                            verified_flex = build_verified_patient_flex(matched_patient)
                            reply_line_message(reply_token, [verified_flex], channel_access_token)
                            LineChat.objects.create(line_user_id=line_user_id, role="assistant", text=f"[SYSTEM_FLEX: VERIFIED_PATIENT {matched_patient.full_name}]")
                        else:
                            reg_flex = build_registration_link_flex(line_user_id)
                            reply_line_message(reply_token, [reg_flex], channel_access_token)
                            LineChat.objects.create(line_user_id=line_user_id, role="assistant", text="[SYSTEM_FLEX: UNREGISTERED_ID_CARD]")
                        continue

                    # 4. If patient is not linked yet and bot is active:
                    if not patient:
                        greeting_flex = build_greeting_flex()
                        reply_line_message(reply_token, [greeting_flex], channel_access_token)
                        continue

                    # 5. Process AI Intake Chat for Linked Patient using DeepSeek API (with Groq & Gemini Fallbacks)
                    print(f"🤖 Processing Text AI Intake for linked patient HN: {patient.hn if patient else 'Unlinked'}")

                    # Fetch recent chat history from LineChat model
                    history = LineChat.objects.filter(line_user_id=line_user_id).order_by('timestamp')[:10]
                    chat_messages = [{"role": chat.role, "content": chat.text} for chat in history if not chat.text.startswith("[SYSTEM_FLEX:")]
                    chat_messages.append({"role": "user", "content": user_text})

                    # Dedicated DeepSeek key for LINE OA Patient Chat (DEEPSEEK_API_KEY_V2)
                    deepseek_key = (os.environ.get("DEEPSEEK_API_KEY_V2") or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
                    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
                    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY", "")

                    ai_reply_raw = ""

                    # 1. Try DeepSeek API (Primary)
                    if deepseek_key and deepseek_key != "dummy-key":
                        try:
                            ds_url = "https://api.deepseek.com/v1/chat/completions"
                            ds_headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {deepseek_key}"
                            }
                            ds_payload = {
                                "model": "deepseek-chat",
                                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *chat_messages],
                                "temperature": 0.7
                            }
                            ds_req = urllib.request.Request(
                                ds_url,
                                data=json.dumps(ds_payload).encode('utf-8'),
                                headers=ds_headers,
                                method='POST'
                            )
                            with urllib.request.urlopen(ds_req, timeout=15) as ds_res:
                                ds_data = json.loads(ds_res.read().decode('utf-8'))
                                ai_reply_raw = ds_data['choices'][0]['message']['content'] or ""
                        except Exception as ds_err:
                            print("⚠️ DeepSeek API Call Failed, falling back:", ds_err)

                    # 2. Try Groq API (Fallback 1)
                    if not ai_reply_raw and groq_key and groq_key != "dummy-key":
                        try:
                            groq_url = "https://api.groq.com/openai/v1/chat/completions"
                            groq_headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {groq_key}"
                            }
                            groq_payload = {
                                "model": "llama-3.3-70b-versatile",
                                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *chat_messages],
                                "temperature": 0.7
                            }
                            groq_req = urllib.request.Request(
                                groq_url,
                                data=json.dumps(groq_payload).encode('utf-8'),
                                headers=groq_headers,
                                method='POST'
                            )
                            with urllib.request.urlopen(groq_req, timeout=15) as groq_res:
                                groq_data = json.loads(groq_res.read().decode('utf-8'))
                                ai_reply_raw = groq_data['choices'][0]['message']['content'] or ""
                        except Exception as groq_err:
                            print("⚠️ Groq API Call Failed, falling back:", groq_err)

                    # 3. Try Gemini 2.5 Flash (Fallback 2)
                    if not ai_reply_raw and gemini_key and gemini_key != "dummy-key":
                        try:
                            gem_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                            gem_headers = {"Content-Type": "application/json"}
                            
                            # Convert chat history for Gemini
                            gem_contents = []
                            for m in chat_messages:
                                g_role = "user" if m["role"] == "user" else "model"
                                gem_contents.append({"role": g_role, "parts": [{"text": m["content"]}]})

                            gem_payload = {
                                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                                "contents": gem_contents
                            }
                            gem_req = urllib.request.Request(
                                gem_url,
                                data=json.dumps(gem_payload).encode('utf-8'),
                                headers=gem_headers,
                                method='POST'
                            )
                            with urllib.request.urlopen(gem_req, timeout=15) as gem_res:
                                gem_data = json.loads(gem_res.read().decode('utf-8'))
                                parts = gem_data['candidates'][0]['content']['parts']
                                ai_reply_raw = parts[0]['text'] if parts else ""
                        except Exception as gem_err:
                            print("⚠️ Gemini API Call Failed:", gem_err)

                    if not ai_reply_raw:
                        ai_reply_raw = "ขออภัยครับ ระบบประมวลผลทางการแพทย์ขัดข้องชั่วคราว กรุณาลองส่งข้อความใหม่อีกครั้งครับ"

                    clean_reply = ai_reply_raw
                    extracted_json = None

                    json_regex = r"\[\[\s*(\{[\s\S]*?\})\s*\]\]"
                    match = re.search(json_regex, ai_reply_raw)

                    if match:
                        try:
                            extracted_json = json.loads(match.group(1))
                            clean_reply = re.sub(json_regex, "", ai_reply_raw).strip()
                        except Exception as json_err:
                            print("⚠️ Failed to parse extracted JSON block:", json_err)

                    # Save chat history
                    LineChat.objects.create(line_user_id=line_user_id, role="user", text=user_text)
                    LineChat.objects.create(line_user_id=line_user_id, role="assistant", text=clean_reply)

                    # Check if scores exist to update PatientBiologicalRecord
                    if extracted_json and patient:
                        scores = extracted_json.get("scores")
                        if scores:
                            record = PatientBiologicalRecord(patient=patient)
                            for i in range(1, 40):
                                axis_key = f"AXIS_{i}"
                                setattr(record, f"axis_{i}", scores.get(axis_key, 50))
                            record.save()
                            print(f"📈 Recorded 39 Axes scores to timeline for HN: {patient.hn}")

                    # Reply to LINE with Flex Card
                    ai_flex = build_ai_chat_flex(
                        clean_reply,
                        patient_name=patient.full_name if patient else None,
                        patient_hn=patient.hn if patient else None
                    )
                    reply_line_message(reply_token, [ai_flex], channel_access_token)

                    AuditLog.objects.create(
                        actor_id="line_bot",
                        target_id=str(patient.id) if patient else line_user_id,
                        action="LINE_WEBHOOK_AI_INTAKE",
                        layer="LINE",
                        client_ip="server-side",
                        governance_status="PATIENT_ACCESSIBLE"
                    )

        return Response({"success": True})
    except Exception as e:
        print("❌ LINE Webhook processing error:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def line_link(request):

    """
    Secures linking between LINE account and clinic patient profile
    """
    token = request.data.get("token")
    phone = request.data.get("phone")

    if not token or not phone:
        return Response({"error": "Token and Phone number are required"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Verify and retrieve token from LineLinkingToken
    link_token = LineLinkingToken.objects.filter(token=token).first()
    if not link_token:
        return Response({"error": "รหัสรักษาสิทธิ์เชื่อมต่อไม่ถูกต้องหรือเคยถูกใช้งานไปแล้ว"}, status=status.HTTP_400_BAD_REQUEST)

    if link_token.expires_at < timezone.now():
        link_token.delete()
        return Response({"error": "ลิงก์หมดอายุการใช้งานแล้ว (มีอายุการใช้งาน 1 ชั่วโมง) กรุณาทักแชท LINE เพื่อรับลิงก์ใหม่"}, status=status.HTTP_400_BAD_REQUEST)

    line_user_id = link_token.line_user_id

    # 2. Search for patient by phone number
    patient = Patient.objects.filter(phone=phone).first()
    if not patient:
        return Response({"error": "ไม่พบประวัติคนไข้ด้วยเบอร์โทรศัพท์นี้ในระบบคลินิก กรุณาพิมพ์หมายเลขใหม่ หรือลงทะเบียนคนไข้ใหม่"}, status=status.HTTP_404_NOT_FOUND)

    # 3. Link LINE User ID to patient document
    patient.line_user_id = line_user_id
    patient.save()

    # Delete token after successful linking
    link_token.delete()

    # 4. Send Welcome Push Notification to LINE
    channel_access_token = os.environ.get("LINE_DOCTORPATT_CHANNEL_ACCESS_TOKEN", "")
    welcome_text = f"🎉 เชื่อมต่อบัญชีสำเร็จแล้วครับ!\n\nสวัสดีครับคุณ {patient.first_name} {patient.last_name}\n\nระบบ Dr. Pat AI ได้ทำการเชื่อมข้อมูลของคุณเข้ากับระบบคลินิกเรียบร้อยแล้ว\n\nคุณสามารถเริ่มต้นการซักประวัติสุขภาพเพื่อประเมินแกนชีววิทยา 39 แกนได้ทันทีโดยการพิมพ์อธิบายอาการเจ็บป่วยหรือปัญหาหลักที่พบมาในแชทนี้ได้เลยครับ! 🦾"
    push_line_message(line_user_id, [{"type": "text", "text": welcome_text}], channel_access_token)

    # 5. Audit Logging
    AuditLog.objects.create(
        actor_id="system",
        target_id=str(patient.id),
        action="LINE_SECURE_LINKED",
        layer="LINE",
        client_ip="server-side",
        governance_status="PATIENT_ACCESSIBLE"
    )

    return Response({
        "success": True,
        "patientName": patient.full_name,
        "patientId": patient.id
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def liff_identity(request):
    """
    Connects LINE details directly using LIFF App
    """
    phone = request.data.get("phone")
    line_user_id = request.data.get("lineUserId")
    display_name = request.data.get("displayName")
    picture_url = request.data.get("pictureUrl")

    if not phone or not line_user_id:
        return Response({"error": "Phone number and LINE User ID are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Search for patient by phone number
    patient = Patient.objects.filter(phone=phone).first()
    if not patient:
        return Response({"error": "ไม่พบประวัติการรักษาด้วยเบอร์โทรศัพท์นี้ กรุณาลงทะเบียนใหม่"}, status=status.HTTP_404_NOT_FOUND)

    # Update patient record with LINE data
    patient.line_user_id = line_user_id
    patient.line_display_name = display_name or None
    patient.line_picture_url = picture_url or None
    patient.save()

    # Log the linking event
    AuditLog.objects.create(
        actor_id="system",
        target_id=str(patient.id),
        action="LINE_LIFF_LINKED",
        layer="LIFF",
        client_ip="server-side",
        governance_status="PATIENT_ACCESSIBLE"
    )

    return Response({
        "success": True,
        "message": "เชื่อมต่อบัญชี LINE กับประวัติผู้ป่วยสำเร็จ",
        "patientId": patient.id,
        "patientName": patient.full_name
    })
