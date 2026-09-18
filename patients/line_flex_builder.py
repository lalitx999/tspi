"""
LINE Flex Message Builder Module for TSPI Clinical Intelligence System
Creates structured, rich UI Flex Message cards (Bubbles & Carousels) for LINE Official Account responses.
"""
import json

def get_status_color(status_str):
    """Return badge background color based on status"""
    s = str(status_str).lower()
    if s in ["high", "วิกฤต", "สูง", "abnormal"]:
        return "#EF4444"  # Red
    elif s in ["warning", "เฝ้าระวัง", "เสี่ยง"]:
        return "#F59E0B"  # Yellow/Amber
    elif s in ["normal", "ปกติ", "ดี"]:
        return "#10B981"  # Emerald Green
    return "#3B82F6"  # Blue


def build_lab_result_flex(lab_data, patient_hn=None):
    """
    Builds a LINE Flex Bubble displaying extracted Lab Results (OCR) with badges & affected axes.
    """
    lab_items = lab_data.get("lab_items", [])
    affected_axes = lab_data.get("affected_axes", [])
    summary_text = lab_data.get("summary", "วิเคราะห์ผลแล็บเรียบร้อยแล้ว")

    # Construct table rows for lab items
    table_rows = []
    for item in lab_items[:6]:  # Show top 6 items
        name = item.get("name", "Unknown Test")
        val = str(item.get("value", "-"))
        unit = str(item.get("unit", ""))
        status = item.get("status", "ปกติ")
        color = get_status_color(status)

        table_rows.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": name,
                    "size": "xs",
                    "color": "#1F2937",
                    "flex": 4,
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"{val} {unit}".strip(),
                    "size": "xs",
                    "color": "#4B5563",
                    "align": "right",
                    "flex": 3
                },
                {
                    "type": "text",
                    "text": status,
                    "size": "xs",
                    "color": "#FFFFFF",
                    "align": "center",
                    "weight": "bold",
                    "flex": 2,
                    "backgroundColor": color,
                    "borderRadius": "sm"
                }
            ]
        })

    # Biological axes badges
    axes_badges = []
    for axis in affected_axes[:4]:
        axis_name = axis.get("name") or axis.get("id") or "Axis"
        axes_badges.append({
            "type": "text",
            "text": f"• {axis_name}",
            "size": "xs",
            "color": "#4338CA",
            "wrap": True,
            "margin": "xs"
        })

    hn_text = f" (HN: {patient_hn})" if patient_hn else ""

    flex_payload = {
        "type": "flex",
        "altText": f"สรุปผลการวิเคราะห์แล็บทางการแพทย์{hn_text}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#1E1B4B",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "สรุปผลแล็บสรีรวิทยา",
                        "weight": "bold",
                        "color": "#EEF2FF",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": f"TSPI Precision Lab OCR Analysis{hn_text}",
                        "size": "xs",
                        "color": "#A5B4FC",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": summary_text,
                        "size": "xs",
                        "color": "#374151",
                        "wrap": True,
                        "margin": "none"
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": "#E5E7EB"
                    },
                    {
                        "type": "text",
                        "text": "รายการตรวจแล็บที่พบ:",
                        "weight": "bold",
                        "size": "xs",
                        "color": "#111827",
                        "margin": "md"
                    },
                    *table_rows,
                    *(
                        [
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": "#E5E7EB"
                            },
                            {
                                "type": "text",
                                "text": "แกนชีววิทยาที่ได้รับผลกระทบหลัก:",
                                "weight": "bold",
                                "size": "xs",
                                "color": "#3730A3",
                                "margin": "md"
                            },
                            *axes_badges
                        ] if axes_badges else []
                    )
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "บันทึกเข้าประวัติเวชระเบียน",
                            "data": f"action=confirm_lab&hn={patient_hn or ''}",
                            "displayText": "ยืนยันการบันทึกข้อมูลแล็บเข้าประวัติ"
                        },
                        "style": "primary",
                        "color": "#4F46E5",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "ดูแดชบอร์ด 39 แกนชีววิทยา",
                            "data": f"action=view_dashboard&hn={patient_hn or ''}",
                            "displayText": "ขอเปิดแดชบอร์ด 39 แกนชีววิทยา"
                        },
                        "style": "secondary",
                        "height": "sm"
                    }
                ]
            }
        }
    }
    return flex_payload


def build_voice_intake_flex(transcript, symptoms, axes_scores=None, patient_hn=None):
    """
    Builds a LINE Flex Bubble displaying Symptom Intake extracted from Voice/Video clips.
    """
    symptom_tags = []
    for s in symptoms[:5]:
        symptom_tags.append({
            "type": "text",
            "text": f"• {s}",
            "size": "xs",
            "color": "#047857",
            "wrap": True,
            "margin": "xs"
        })

    hn_text = f" (HN: {patient_hn})" if patient_hn else ""

    flex_payload = {
        "type": "flex",
        "altText": f"สรุปการซักประวัติจากเสียง/วิดีโอ{hn_text}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#064E3B",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "สรุปประวัติจากคลิปเสียง / วิดีโอ",
                        "weight": "bold",
                        "color": "#ECFDF5",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": f"TSPI Clinical Audio/Video Intake{hn_text}",
                        "size": "xs",
                        "color": "#A7F3D0",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "ถอดบทเรียนถ้อยคำคนไข้:",
                        "weight": "bold",
                        "size": "xs",
                        "color": "#065F46"
                    },
                    {
                        "type": "text",
                        "text": f"\"{transcript[:180]}...\"" if len(transcript) > 180 else f"\"{transcript}\"",
                        "size": "xs",
                        "color": "#374151",
                        "style": "italic",
                        "wrap": True,
                        "margin": "xs"
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": "#E5E7EB"
                    },
                    {
                        "type": "text",
                        "text": "อาการหลักที่ดึงได้ (Chief Complaints):",
                        "weight": "bold",
                        "size": "xs",
                        "color": "#111827",
                        "margin": "md"
                    },
                    *symptom_tags
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "ยืนยันข้อมูลประวัติ",
                            "data": f"action=confirm_symptoms&hn={patient_hn or ''}",
                            "displayText": "ยืนยันการบันทึกประวัติสุขภาพเข้าคลินิก"
                        },
                        "style": "primary",
                        "color": "#059669",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "อัดเสียง/อธิบายเพิ่มเติม",
                            "data": f"action=add_more_info&hn={patient_hn or ''}",
                            "displayText": "ต้องการให้ข้อมูลเพิ่มเติม"
                        },
                        "style": "secondary",
                        "height": "sm"
                    }
                ]
            }
        }
    }
    return flex_payload


def build_axes_dashboard_flex(domain_scores, patient_hn=None):
    """
    Builds a LINE Flex Carousel showing 12 Health Scoring Domains.
    Uses only validated LINE Flex Message properties.
    """
    if not domain_scores:
        domain_scores = {
            "D1 Immune & Infection": 50,
            "D2 Energy, Mito & Redox": 50,
            "D3 Microbiome & Gut": 50,
            "D4 Autophagy & Lysosome": 50,
            "D5 Epigenomic & Genomic": 50,
            "D6 Neuro-Endocrine": 50,
            "D7 Vascular & Microcirc": 50,
            "D8 Fibrosis & ECM": 50,
            "D9 Stem Cell & Hematology": 50,
            "D10 Connective & Bone": 50,
            "D11 Organ Reserve Capacity": 50,
            "D12 Oncology & Regulation": 50,
        }

    cards = []
    domain_items = list(domain_scores.items())
    for i in range(0, len(domain_items), 3):
        chunk = domain_items[i:i + 3]
        rows = []
        for name, raw_score in chunk:
            score_val = 50.0
            is_na = False
            if raw_score is None:
                is_na = True
                score_val = 0.0
            elif isinstance(raw_score, (int, float)):
                score_val = float(raw_score)
            elif isinstance(raw_score, dict):
                val = raw_score.get("score")
                if val is not None and isinstance(val, (int, float)):
                    score_val = float(val)
                else:
                    is_na = True
                    score_val = 0.0
            elif isinstance(raw_score, str):
                try:
                    score_val = float(raw_score)
                except ValueError:
                    is_na = True
                    score_val = 0.0

            if is_na:
                percentage = 0
                score_label = "N/A"
                bar_color = "#94A3B8"
                status_emoji = "⬜"
            else:
                percentage = int(min(max(score_val * 10 if score_val <= 10 else score_val, 0), 100))
                score_label = f"{percentage}/100"
                if percentage >= 70:
                    bar_color = "#EF4444"
                    status_emoji = "🔴"
                elif percentage >= 40:
                    bar_color = "#F59E0B"
                    status_emoji = "🟡"
                else:
                    bar_color = "#10B981"
                    status_emoji = "🟢"

            # Build bar using 10 fixed-width boxes (LINE Flex safe - no % widths)
            bar_units = percentage // 10  # 0-10 filled units
            filled_boxes = []
            for _ in range(bar_units):
                filled_boxes.append({
                    "type": "box",
                    "layout": "vertical",
                    "width": "8px",
                    "height": "6px",
                    "backgroundColor": bar_color,
                    "contents": []
                })
            for _ in range(10 - bar_units):
                filled_boxes.append({
                    "type": "box",
                    "layout": "vertical",
                    "width": "8px",
                    "height": "6px",
                    "backgroundColor": "#E5E7EB",
                    "contents": []
                })

            rows.append({
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{status_emoji} {name}",
                                "size": "xs",
                                "weight": "bold",
                                "color": "#1F2937",
                                "flex": 4,
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": score_label,
                                "size": "xs",
                                "weight": "bold",
                                "color": bar_color,
                                "flex": 1
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "xs",
                        "spacing": "none",
                        "contents": filled_boxes
                    }
                ]
            })

        cards.append({
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#0F172A",
                "paddingAll": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": f"Health Domains ({i + 1}-{min(i + 3, len(domain_items))})",
                        "weight": "bold",
                        "color": "#F8FAFC",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": f"HN: {patient_hn or '-'} | TSPI 39-Axes",
                        "size": "xxs",
                        "color": "#64748B",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "contents": rows
            }
        })

    return {
        "type": "flex",
        "altText": "TSPI 12 Health Domain Dashboard",
        "contents": {
            "type": "carousel",
            "contents": cards
        }
    }


def build_link_account_flex(linking_url):
    """
    Builds a LINE Flex Bubble for unlinked patients requesting them to connect their clinic profile.
    """
    return {
        "type": "flex",
        "altText": "กรุณาเชื่อมต่อบัญชีคนไข้ของคุณ",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FF7444",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "เชื่อมต่อบัญชีคนไข้",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "lg",
                        "align": "center"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
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
                "paddingAll": "md",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "เชื่อมต่อบัญชีทันที",
                            "uri": linking_url
                        },
                        "style": "primary",
                        "color": "#FF7444"
                    }
                ]
            }
        }
    }


def build_greeting_flex():
    """
    Builds a LINE Flex Bubble asking patient for 13-digit Thai National ID Card Number.
    """
    return {
        "type": "flex",
        "altText": "เปิดใช้งานหมอ AI (กรุณาระบุเลขบัตรประชาชน 13 หลัก)",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#0A5C8E",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "เปิดใช้งาน TSPI Clinical AI",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": "ระบบยืนยันตัวตนคนไข้ทางการแพทย์",
                        "size": "xs",
                        "color": "#93C5FD",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "สวัสดีครับ/ค่ะ ยินดีต้อนรับสู่ระบบซักประวัติและประเมินสุขภาพอัจฉริยะ TSPI",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#1E293B",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "เพื่อความปลอดภัยของข้อมูลเวชระเบียนทางการแพทย์ กรุณาพิมพ์ส่ง \"เลขบัตรประชาชน 13 หลัก\" ของท่านในช่องแชตนี้ เพื่อทำการตรวจสอบยืนยันประวัติในฐานข้อมูลระบบคลินิกครับ",
                        "size": "xs",
                        "color": "#475569",
                        "wrap": True,
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "วิธียืนยันตัวตน",
                            "text": "พิมพ์เลขบัตรประชาชน 13 หลักติดกัน (เช่น 1100200300400)"
                        },
                        "style": "secondary",
                        "height": "sm"
                    }
                ]
            }
        }
    }


def build_verified_patient_flex(patient):
    """
    Builds a LINE Flex Bubble displaying verified Patient name, HN, and Intake Menu.
    """
    hn_str = patient.hn or patient.legacy_id or "-"
    full_name = f"{patient.first_name} {patient.last_name}".strip()
    return {
        "type": "flex",
        "altText": f"ยืนยันตัวตนสำเร็จ: คุณ{full_name}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#059669",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "ยืนยันตัวตนสำเร็จ",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": f"HN: {hn_str} | เชื่อมต่อข้อมูลเวชระเบียนแล้ว",
                        "size": "xs",
                        "color": "#A7F3D0",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": f"ยินดีต้อนรับ คุณ{full_name}",
                        "weight": "bold",
                        "size": "md",
                        "color": "#111827"
                    },
                    {
                        "type": "text",
                        "text": "ระบบเปิดการซักประวัติ AI เรียบร้อยแล้ว ท่านสามารถพิมพ์บอกเล่าอาการ, อัปโหลดภาพถ่ายใบตรวจแล็บ, หรืออัดคลิปเสียงส่งมาในแชตนี้ได้ทันทีครับ",
                        "size": "xs",
                        "color": "#4B5563",
                        "wrap": True,
                        "margin": "sm"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "เริ่มซักประวัติสุขภาพ",
                            "text": "เริ่มซักประวัติสุขภาพ"
                        },
                        "style": "primary",
                        "color": "#059669",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "ปิดใช้งานบอท",
                            "text": "ปิดใช้งานบอท"
                        },
                        "style": "secondary",
                        "height": "sm"
                    }
                ]
            }
        }
    }


def build_registration_link_flex(line_user_id):
    """
    Builds a LINE Flex Bubble when ID card is not found in PostgreSQL DB,
    offering direct link to register at https://tspi.vercel.app/patient/register
    """
    reg_url = f"https://tspi.vercel.app/patient/register?line_user_id={line_user_id}"
    return {
        "type": "flex",
        "altText": "ไม่พบข้อมูลคนไข้ในระบบ - กรุณาลงทะเบียน",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#D97706",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "ไม่พบข้อมูลในระบบคลินิก",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": "ยังไม่มีประวัติเลขบัตรประชาชนนี้ใน PostgreSQL",
                        "size": "xs",
                        "color": "#FDE68A",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "ระบบไม่พบข้อมูลประวัติคนไข้ตรงกับเลขบัตรประชาชนที่ระบุ",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#1F2937",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "หากท่านเป็นคนไข้ใหม่ กรุณากดปุ่มด้านล่างเพื่อลงทะเบียนเปิดประวัติสุขภาพกับคลินิกผ่านระบบออนไลน์ได้ทันทีครับ",
                        "size": "xs",
                        "color": "#4B5563",
                        "wrap": True,
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "ลงทะเบียนคนไข้ใหม่ทันที",
                            "uri": reg_url
                        },
                        "style": "primary",
                        "color": "#D97706",
                        "height": "sm"
                    }
                ]
            }
        }
    }


def build_ai_chat_flex(clean_reply, patient_name=None, patient_hn=None):
    """
    Builds a premium TSPI Clinical AI Chat Flex Message Bubble for AI intake responses.
    """
    hn_text = f" (HN: {patient_hn})" if patient_hn else ""
    title_text = f"คุณ{patient_name}" if patient_name else "ระบบซักประวัติ TSPI"

    return {
        "type": "flex",
        "altText": f"คำตอบจากระบบซักประวัติ TSPI Clinical AI",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#0F172A",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": "TSPI AI Clinical Intake",
                        "weight": "bold",
                        "color": "#F8FAFC",
                        "size": "md"
                    },
                    {
                        "type": "text",
                        "text": f"คนไข้: {title_text}{hn_text}",
                        "size": "xs",
                        "color": "#94A3B8",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": clean_reply,
                        "size": "sm",
                        "color": "#334155",
                        "wrap": True,
                        "lineSpacing": "4px"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "paddingAll": "md",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "39 แกน",
                            "data": f"action=view_dashboard&hn={patient_hn or ''}",
                            "displayText": "ขอเปิดแดชบอร์ด 39 แกนชีววิทยา"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "flex": 1
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "ปิดบอท",
                            "text": "ปิดใช้งานบอท"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "flex": 1
                    }
                ]
            }
        }
    }


def build_bot_status_flex(title, message, is_active=True):
    """
    Builds a status notification Flex Message Bubble for bot status events.
    """
    header_bg = "#059669" if is_active else "#DC2626"

    return {
        "type": "flex",
        "altText": f"{title}",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": header_bg,
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{title}",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "md"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "contents": [
                    {
                        "type": "text",
                        "text": message,
                        "size": "sm",
                        "color": "#334155",
                        "wrap": True
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "md",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "เปิดใช้งานบอท" if not is_active else "เริ่มซักประวัติสุขภาพ",
                            "text": "เปิดใช้งานบอท" if not is_active else "เริ่มซักประวัติสุขภาพ"
                        },
                        "style": "primary",
                        "color": header_bg,
                        "height": "sm"
                    }
                ]
            }
        }
    }
