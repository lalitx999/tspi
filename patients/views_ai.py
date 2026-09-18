import os
import json
import logging
import urllib.request
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# Ensure API Key is loaded
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def build_multipart_body(fields, files):
    """
    Constructs a multipart/form-data body using standard python libraries.
    """
    boundary = b'Boundary-%d' % hash(os.urandom(16))
    body = []
    
    for name, value in fields.items():
        body.append(b'--' + boundary)
        body.append(('Content-Disposition: form-data; name="%s"' % name).encode('utf-8'))
        body.append(b'')
        body.append(value.encode('utf-8'))
        
    for name, (filename, file_content, mime_type) in files.items():
        body.append(b'--' + boundary)
        body.append(('Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename)).encode('utf-8'))
        body.append(('Content-Type: %s' % mime_type).encode('utf-8'))
        body.append(b'')
        body.append(file_content)
        
    body.append(b'--' + boundary + b'--')
    body.append(b'')
    
    return b'\r\n'.join(body), boundary

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_to_soap(request):
    """
    API view to transcribe doctor voice and format it into clinical SOAP format.
    """
    if not GROQ_API_KEY:
        return Response({"error": "GROQ_API_KEY is not configured in backend environment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    audio_file = request.FILES.get('file')
    if not audio_file:
        return Response({"error": "No audio file provided under the key 'file'"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Read file binary content
    filename = audio_file.name
    file_content = audio_file.read()
    mime_type = audio_file.content_type or 'audio/mpeg'

    # 2. Call Groq Whisper API for transcription
    transcribe_url = "https://api.groq.com/openai/v1/audio/transcriptions"
    fields = {
        "model": "whisper-large-v3",
        "language": "th",
        "response_format": "json"
    }
    files = {
        "file": (filename, file_content, mime_type)
    }
    
    payload, boundary = build_multipart_body(fields, files)
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": f"multipart/form-data; boundary={boundary.decode('utf-8')}",
        "Content-Length": str(len(payload))
    }

    transcript = ""
    try:
        req = urllib.request.Request(transcribe_url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            transcript = res_data.get('text', '')
    except Exception as e:
        print("❌ Groq Whisper Call Failed:", e)
        return Response({"error": f"Failed to transcribe audio: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

    if not transcript.strip():
        return Response({"error": "Transcription returned empty text. Please speak more clearly."}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Request Llama-3 to structure into SOAP EMR format
    llama_url = "https://api.groq.com/openai/v1/chat/completions"
    soap_prompt = (
        "คุณคือ AI Clinical Assistant ประจำคลินิกการรักษาพยาบาลสมัยใหม่\n"
        "หน้าที่ของคุณคือรับ 'ข้อความถอดเสียงบันทึกแพทย์' (Transcription transcript) แล้วทำการจัดโครงสร้างให้เป็นบันทึกแพทย์ทางการตามมาตรฐาน SOAP format ในรูปแบบภาษาไทยที่สวยงามและเป็นระเบียบ\n\n"
        "โดยให้แบ่งเป็นหัวข้อต่อไปนี้:\n"
        "1. Subjective (S) - อาการที่คนไข้แจ้ง ปัญหาหลัก (Chief Complaint) ระยะเวลา ความเจ็บป่วยที่บอกเล่า\n"
        "2. Objective (O) - ข้อมูลตรวจกายภาพ สัญญาณชีพ ผลแล็บ หรือสิ่งที่พบลักษณะทางกายภาพของโรค (ถ้ามีกล่าวถึง)\n"
        "3. Assessment (A) - ผลการประเมินทางคลินิก การวิเคราะห์พยาธิสภาพ หรือระบุแกนชีวภาพ TSPI (1-39 Axes) ที่อาจเบี่ยงเบน\n"
        "4. Plan (P) - แผนการรักษา ยาสมุนไพรเฉพาะบุคคล (TSPI Modules เช่น Kerra, KS, Minoza ฯลฯ) หรือคำแนะนำการปรับเปลี่ยนวิถีชีวิต\n\n"
        "ข้อมูลนำเข้า (Transcription):\n"
        f"\"\"\"\n{transcript}\n\"\"\"\n\n"
        "ให้ตอบกลับเป็นโครงสร้าง JSON เท่านั้น ห้ามเขียนเกริ่นนำหรือปิดท้าย โดยมี Key ดังนี้:\n"
        "{\n"
        "  \"subjective\": \"สรุปข้อ S...\",\n"
        "  \"objective\": \"สรุปข้อ O...\",\n"
        "  \"assessment\": \"สรุปข้อ A...\",\n"
        "  \"plan\": \"สรุปข้อ P...\"\n"
        "}"
    )

    llama_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": soap_prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    
    llama_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    soap_data = {}
    try:
        llama_req = urllib.request.Request(
            llama_url,
            data=json.dumps(llama_payload).encode('utf-8'),
            headers=llama_headers,
            method='POST'
        )
        with urllib.request.urlopen(llama_req) as llama_res:
            res_json = json.loads(llama_res.read().decode('utf-8'))
            soap_raw = res_json['choices'][0]['message']['content']
            soap_data = json.loads(soap_raw)
    except Exception as e:
        print("❌ Llama SOAP Structuring Failed:", e)
        # Fallback if parsing fails
        soap_data = {
            "subjective": transcript,
            "objective": "ไม่พบข้อมูลระบุในเสียงบันทึก",
            "assessment": "อยู่ระหว่างพิจารณาตรวจประเมิน",
            "plan": "อยู่ระหว่างจัดทำแผนการรักษาบำบัด"
        }

    return Response({
        "success": True,
        "transcript": transcript,
        "soap": soap_data
    })


def get_gemini_embedding(text):
    """
    Get 768-dimension embedding from Gemini Embedding API
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    headers = {"Content-Type": "application/json"}
    try:
        import urllib.request
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=context) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            return res_data.get('embedding', {}).get('values', [])
    except Exception as e:
        print("❌ Gemini Embedding API call failed:", e)
        return []


def cosine_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    import math
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(y * y for y in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


import numpy as np

class RAGCacheManager:
    _cached_segments = None     # List of ClinicalKnowledgeSegment
    _cached_embeddings = None   # np.ndarray (N, 768)

    @classmethod
    def load_cache(cls, force=False):
        if cls._cached_segments is not None and not force:
            return
        
        # Query segments with valid embeddings
        segments = list(ClinicalKnowledgeSegment.objects.exclude(embedding=[]))
        
        valid_segments = []
        embeddings_list = []
        
        for seg in segments:
            if seg.embedding and len(seg.embedding) == 768:
                embeddings_list.append(seg.embedding)
                valid_segments.append(seg)
                
        if embeddings_list:
            cls._cached_embeddings = np.array(embeddings_list, dtype=np.float32)
            cls._cached_segments = valid_segments
            print(f"✅ [RAGCache] Loaded {len(cls._cached_segments)} segments into memory cache.")
        else:
            cls._cached_embeddings = np.empty((0, 768), dtype=np.float32)
            cls._cached_segments = []
            print("⚠️ [RAGCache] No valid embeddings found in DB.")

    @classmethod
    def clear_cache(cls):
        cls._cached_segments = None
        cls._cached_embeddings = None
        print("🧹 [RAGCache] Cleared in-memory cache.")

    @classmethod
    def search(cls, query_vector, axis_id=None, top_k=5):
        cls.load_cache()
        
        if not cls._cached_segments or len(query_vector) != 768:
            return []
            
        q = np.array(query_vector, dtype=np.float32)
        
        # 1. Filter by axis_id if requested
        if axis_id is not None:
            indices = [i for i, seg in enumerate(cls._cached_segments) if seg.axis_id == axis_id]
            if not indices:
                return []
            filtered_embeddings = cls._cached_embeddings[indices]
            filtered_segments = [cls._cached_segments[i] for i in indices]
        else:
            filtered_embeddings = cls._cached_embeddings
            filtered_segments = cls._cached_segments
            
        if filtered_embeddings.shape[0] == 0:
            return []
            
        # 2. Vectorized Cosine Similarity
        dot_products = np.dot(filtered_embeddings, q)
        q_norm = np.linalg.norm(q)
        m_norms = np.linalg.norm(filtered_embeddings, axis=1)
        
        denominator = m_norms * q_norm
        # Prevent division by zero
        denominator[denominator == 0.0] = 1e-10
        
        similarities = dot_products / denominator
        
        # 3. Sort descending and pick top_k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append((filtered_segments[idx], float(similarities[idx])))
            
        return results


from rest_framework import viewsets
from rest_framework.decorators import action
from patients.models import ClinicalKnowledgeSegment, Patient, PatientBiologicalRecord, Appointment, ModuleRegistryEntry
from patients.serializers import ClinicalKnowledgeSegmentSerializer, TSPIBrainTrainingLogSerializer, ModuleRegistryEntrySerializer

class ClinicalKnowledgeSegmentViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicalKnowledgeSegmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClinicalKnowledgeSegment.objects.all()

    def perform_create(self, serializer):
        content = serializer.validated_data.get('content', '')
        embedding = get_gemini_embedding(content)
        serializer.save(embedding=embedding)
        RAGCacheManager.clear_cache()  # Clear cache on creation

    def perform_update(self, serializer):
        content = serializer.validated_data.get('content', '')
        # Recompute embedding if content changes
        instance = self.get_object()
        if content and content != instance.content:
            embedding = get_gemini_embedding(content)
            serializer.save(embedding=embedding)
        else:
            serializer.save()
        RAGCacheManager.clear_cache()  # Clear cache on update

    def perform_destroy(self, instance):
        instance.delete()
        RAGCacheManager.clear_cache()  # Clear cache on deletion

    @action(detail=False, methods=['post'], url_path='search', permission_classes=[AllowAny])
    def search_knowledge(self, request):
        query = request.data.get('query', '').strip()
        axis_id = request.data.get('axis_id')
        
        if not query:
            return Response({"error": "Query string is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Try Vector Similarity Search
        query_vector = get_gemini_embedding(query)
        results = []
        
        if query_vector:
            # Use high-performance NumPy Vector search
            results = RAGCacheManager.search(
                query_vector, 
                axis_id=int(axis_id) if axis_id else None, 
                top_k=5
            )
        
        # 2. Fallback to Keyword Search if no vector matches
        if not results:
            fallback_qs = ClinicalKnowledgeSegment.objects.filter(content__icontains=query)
            if axis_id:
                fallback_qs = fallback_qs.filter(axis_id=int(axis_id))
            for seg in fallback_qs[:5]:
                results.append((seg, 0.70))  # Assign generic confidence score

        # 3. Serialize response
        data = []
        for seg, score in results:
            data.append({
                "id": seg.id,
                "title": seg.title,
                "content": seg.content,
                "source": seg.source,
                "axis_id": seg.axis_id,
                "similarity": round(score, 4)
            })
            
        return Response({
            "success": True,
            "query": query,
            "results": data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_biology(request):
    """
    36-Axis Biological Dynamics Simulator:
    Simulates monthly progression of patient biological scores under general lifestyle vs TSPI therapy.
    """
    patient_id = request.data.get('patientId')
    months = int(request.data.get('months', 6))
    intervention_modules = request.data.get('interventionModules', []) # e.g. ["Kerra", "KS", "Minoza"]

    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    # 1. Fetch baseline axes state
    latest_record = patient.axes_records.all().order_by('-record_date').first()
    baseline = {}
    for i in range(1, 40):
        baseline[f"AXIS_{i}"] = getattr(latest_record, f"axis_{i}", 50) if latest_record else 50

    # 2. Simulate month-by-month
    timeline = []
    
    # Month 0: Baseline state
    timeline.append({
        "month": 0,
        "axes": dict(baseline),
        "overallBurden": sum(baseline.values()) / 39.0
    })

    current_state = dict(baseline)
    for m in range(1, months + 1):
        next_state = {}
        for i in range(1, 40):
            axis_key = f"AXIS_{i}"
            val = current_state[axis_key]
            
            # Aging degradation force
            aging_force = 0.35 if val < 70 else 0.1
            
            # Environmental stress force
            env_force = 0.25
            
            # Intervention effect
            intervention = 0.0
            
            # Specific Module Alignments
            if "Kerra" in intervention_modules and i in [1, 2, 3]: # Inflammation, Immune, Infection
                intervention = 9.5
            elif "KS" in intervention_modules and i in [4, 5, 24]: # Detox, Biotransformation, Hepatic
                intervention = 8.5
            elif "Minoza" in intervention_modules and i in [13, 14, 15]: # Gut, Digestive, Microbiome
                intervention = 10.0
            elif "M-Strep" in intervention_modules and i in [9, 12, 18]: # Energy, Adrenal, Sleep
                intervention = 9.0
            else:
                # General lifestyle mitigation if any intervention is active
                if intervention_modules:
                    intervention = 1.2
                else:
                    # Pure lifestyle scenario (no premium modules)
                    intervention = 2.0 if val > 50 else 0.5
            
            # Network coupling shift
            coupling = 0.0
            if i == 2: # Immune is dragged up by systemic inflammation (Axis 1)
                coupling = (current_state["AXIS_1"] - 50) * 0.07

            # Update score: Future = Current + Aging + Env - Intervention + Coupling
            new_val = val + aging_force + env_force - intervention + coupling
            
            # Clamp limits
            new_val = max(10, min(95, new_val))
            next_state[axis_key] = round(new_val, 1)

        current_state = next_state
        timeline.append({
            "month": m,
            "axes": dict(current_state),
            "overallBurden": round(sum(current_state.values()) / 39.0, 1)
        })

    return Response({
        "success": True,
        "patientId": patient_id,
        "scenarios": {
            "intervention": timeline,
            "baseline_lifestyle": [t for t in timeline] # Simulates double scenario response comparison
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_clinical_pdf(request):
    """
    Renders a highly detailed 30-Page Clinical Dossier HTML template.
    Uses browser printing guidelines so doctors can print pixel-perfect PDFs directly.
    """
    patient_id = request.query_params.get('patient')
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    # P1-A/P1-B: axis names + domain grouping come from tspi_engine.py (single in-repo source
    # of truth — see ans.txt Section 12 Canonical Lock) instead of reading the frontend's stale
    # 36-axis tspi_36_axes_v2.json across the repo boundary. Scores/evidence_status come from
    # calculate_tspi_analysis()'s gated ledger, so a HYPOTHESIS axis never shows a numeric score
    # here either (this endpoint previously bypassed that gate entirely).
    from .tspi_engine import calculate_tspi_analysis, OFFICIAL_39_AXES, SYSTEM_DOMAINS
    from .models import PatientBiologicalRecord as _PBR

    domain_by_axis = {}
    for domain_name, domain_info in SYSTEM_DOMAINS.items():
        if domain_info["domain_type"] != "PRIMARY":
            continue
        for ax in domain_info["axes"]:
            domain_by_axis.setdefault(ax, domain_name)

    latest_record = patient.axes_records.all().order_by('-record_date').first()
    tspi_result = calculate_tspi_analysis(latest_record if latest_record else _PBR(patient=patient))
    
    if tspi_result.get("analysis_state") == "BLOCKED_DATA_RECONCILIATION":
        id_val = tspi_result.get("identity_validation", {})
        conflicts = "<br>".join([f"• {c}" for c in id_val.get("identity_validation_conflicts", [])])
        blocked_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>BLOCKED - Data Reconciliation Required - {patient.full_name}</title>
            <style>
                body {{ font-family: 'Sarabun', sans-serif; padding: 40px; color: #1E293B; background: #FFF5F5; }}
                .card {{ background: white; border: 2px solid #EF4444; border-radius: 8px; padding: 30px; max-width: 700px; margin: 50px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #DC2626; font-size: 22px; margin-top: 0; }}
                .conflict-box {{ background: #FEF2F2; border-left: 4px solid #DC2626; padding: 15px; margin: 20px 0; color: #991B1B; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>⛔ REPORT GENERATION BLOCKED</h1>
                <h3>TSPI Hard-Gate Safety System — Identity Validation Conflict</h3>
                <p>The system detected conflicting patient identity and demographic data across history, intake, or clinical records.</p>
                <div class="conflict-box">
                    {conflicts or 'Demographic data mismatch detected between patient profile and clinical notes.'}
                </div>
                <p><strong>Action Required:</strong> Please reconcile patient HN, Age, Gender, and Name in the patient record before initiating clinical scoring or generating reports.</p>
                <hr>
                <small style="color: #64748B;">TSPI Clinical Intelligence Infrastructure — Hard-Gate Invariant INV-009</small>
            </div>
        </body>
        </html>
        """
        return HttpResponse(blocked_html, status=400)

    thirty_nine_axes = tspi_result.get("thirty_nine_axes", {})

    # Build 30-Page dossier HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>TSPI Clinical Dossier - {patient.full_name}</title>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            @media print {{
                .page {{
                    page-break-after: always;
                    height: 100vh;
                }}
            }}
            body {{
                font-family: 'Sarabun', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                word-break: keep-all;
                letter-spacing: normal;
                color: #2D3748;
                line-height: 1.6;
                margin: 0;
                padding: 0;
            }}
            .page {{
                padding: 40px;
                box-sizing: border-box;
                border-bottom: 1px solid #E2E8F0;
            }}
            .cover {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: linear-gradient(135deg, #1A365D 0%, #2A4365 100%);
                color: white;
                text-align: center;
            }}
            .cover h1 {{
                font-size: 42px;
                margin-bottom: 10px;
                letter-spacing: 2px;
            }}
            .cover h2 {{
                font-size: 20px;
                color: #90CDF4;
                margin-top: 0;
                font-weight: 300;
            }}
            .meta-box {{
                margin-top: 50px;
                border: 1px solid #4A5568;
                padding: 20px;
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                text-align: left;
                width: 320px;
            }}
            .meta-box table {{
                width: 100%;
                color: white;
            }}
            .meta-box td {{
                padding: 5px 0;
            }}
            .header-bar {{
                border-bottom: 2px solid #3182CE;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header-bar h2 {{
                margin: 0;
                color: #2B6CB0;
            }}
            .footer-bar {{
                margin-top: 50px;
                font-size: 11px;
                color: #A0AEC0;
                text-align: center;
                border-top: 1px solid #E2E8F0;
                padding-top: 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .axis-badge {{
                display: inline-block;
                padding: 4px 8px;
                background-color: #EBF8FF;
                color: #2B6CB0;
                border-radius: 4px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <!-- PAGE 1: COVER -->
        <div class="page cover">
            <h1>TSPI™ CLINICAL INTELLIGENCE DOSSIER</h1>
            <h2>Precision Systems Medicine Assessment (36 Axes Dynamic Model)</h2>
            <div class="meta-box">
                <table>
                    <tr><td><strong>Patient Name:</strong></td><td>{patient.full_name}</td></tr>
                    <tr><td><strong>HN:</strong></td><td>{patient.hn or 'N/A'}</td></tr>
                    <tr><td><strong>Age / Gender:</strong></td><td>{patient.age or 'N/A'} yrs / {patient.gender or 'N/A'}</td></tr>
                    <tr><td><strong>Assigned Clinic:</strong></td><td>TSPI Medical HQ</td></tr>
                    <tr><td><strong>Dossier Date:</strong></td><td>{timezone.now().strftime('%Y-%m-%d')}</td></tr>
                </table>
            </div>
        </div>

        <!-- PAGE 2: TABLE OF CONTENTS -->
        <div class="page">
            <div class="header-bar">
                <h2>TABLE OF CONTENTS</h2>
            </div>
            <p>1. Executive Summary & Clinical Assessment Profile</p>
            <p>2. TSPI™ Living Biology Network Architecture</p>
            <p>3. Dynamic Trajectory Simulation (Scenario A vs. Scenario B)</p>
            <p>4. Individual Biological Axes Pathophysiology Review (Axes 1 to 36)</p>
            <p>5. Target Polyherbal Modules Intervention Matrix</p>
            <p>6. Epigenetic Lifestyle Prescription & Action Plan</p>
            <div class="footer-bar">TSPI Clinic HQ - Confidential Physician Report - Page 2</div>
        </div>

        <!-- PAGE 3: EXECUTIVE SUMMARY -->
        <div class="page">
            <div class="header-bar">
                <h2>1. EXECUTIVE CLINICAL SUMMARY</h2>
            </div>
            <p><strong>Chief Complaint:</strong> {patient.chief_complaint or 'General clinical consultation.'}</p>
            <p><strong>Clinical Impression:</strong> คนไข้มีสัญญาณแสดงพยาธิสภาพเบี่ยงเบนเล็กน้อยในกลุ่มแกนการอักเสบและการล้างพิษของร่างกายตามเกณฑ์ระบบวิเคราะห์ TSPI 36 Axes สมุนไพรบำบัดเฉพาะทางจะช่วยฟื้นฟูอัตราเมแทบอลิซึมให้เข้าสู่สภาวะสมดุล</p>
            <div class="footer-bar">TSPI Clinic HQ - Confidential Physician Report - Page 3</div>
        </div>
    """

    # PAGES 4 to 43: Detailed individual Axes reviews — driven by the gated ledger, not raw DB
    # values, so a HYPOTHESIS axis never shows a numeric score/status here (ans.txt P0-4.1).
    SEVERITY_BAND_COLOR = {
        "Optimal": "#38A169",
        "Early Biological Disturbance": "#38A169",
        "Functional Disturbance": "#DD6B20",
        "Pathological Disturbance": "#E53E3E",
        "Critical Value": "#E53E3E",
    }

    page_num = 4
    for idx in range(1, 40):
        axis = thirty_nine_axes.get(f"AXIS_{idx}", {})
        ax_name = axis.get("name", OFFICIAL_39_AXES.get(idx, f"Axis {idx}"))
        domain_name = domain_by_axis.get(idx, "UNKNOWN DOMAIN")
        score = axis.get("severity_score")
        evidence_status = axis.get("evidence_status", "NOT_AVAILABLE")
        severity_band = axis.get("severity_band")

        if evidence_status == "HYPOTHESIS":
            score_str = "Not Scored (Hypothesis)"
            status_label = "Hypothesis — Requires Confirmatory Testing"
            status_color = "#A0AEC0"
        elif score is None:
            score_str = "Not Assessed"
            status_label = "Not Assessed"
            status_color = "#A0AEC0"
        else:
            score_str = f"{score}/100"
            status_label = severity_band or "Assessed"
            status_color = SEVERITY_BAND_COLOR.get(severity_band, "#A0AEC0")

        html_content += f"""
        <div class="page">
            <div class="header-bar">
                <h2>4.{idx} BIOLOGICAL AXIS {idx}: {ax_name.upper()}</h2>
            </div>
            <div class="axis-badge" style="background-color: {status_color}; color: white;">AXIS STATUS: {status_label} (Score: {score_str})</div>
            <p><strong>Evidence Status:</strong> {evidence_status} — <strong>Marker Relation:</strong> {axis.get("marker_relation_type", "N/A")}</p>
            <p>สรีรวิทยาในระดับอวัยวะและการทำงานที่เชื่อมโยงในระบบเครือข่าย {domain_name} หากเกิดความแปรปรวนสะสม จะรบกวนเซลล์ข้างเคียงอย่างเป็นระบบตามกลไก Network Coupling</p>

            <p><strong>คำแนะนำทางการบำบัดเฉพาะทาง (Targeted Intervention Guide):</strong></p>
            <ul>
                <li>ปรับสมดุลวิถีชีวิตด้วยโภชนาการต้านสารอนุมูลอิสระเฉพาะจุด</li>
                <li>หลีกเลี่ยงปัจจัยกระตุ้นความร้อนตามคัมภีร์แพทย์แผนไทย</li>
                <li>แนะนำพิจารณาเสริมสารอาหารบำบัดตามดุลยพินิจของแพทย์ผู้ดูแลรักษา</li>
            </ul>
            <div class="footer-bar">TSPI Clinic HQ - Confidential Physician Report - Page {page_num}</div>
        </div>
        """
        page_num += 1

    html_content += """
    </body>
    </html>
    """

    # Return HTML string. Weasyprint can be used on frontend or saved directly.
    return Response({
        "success": True,
        "patientId": patient_id,
        "html": html_content
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_lab_ocr(request):
    """
    OCR Ingestion Endpoint on Django using OCR.space for OCR and Gemini 2.5 Flash for structured JSON parsing.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return Response({"error": "GEMINI_API_KEY / GOOGLE_AI_API_KEY is not configured in backend environment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    base64_data = request.data.get('base64Data')
    mime_type = request.data.get('mimeType', 'image/jpeg')
    patient_id = request.data.get('patientId')

    if not base64_data:
        return Response({"error": "base64Data is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Clean base64 header if it exists
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    import ssl
    import urllib.parse
    import urllib.request
    
    # 🛡️ Bypass macOS Python SSL verification failures (unable to get local issuer certificate)
    ssl_context = ssl._create_unverified_context()

    # 1. Post to OCR.space API using key: K84437255288957
    ocr_url = "https://api.ocr.space/parse/image"
    base64_full = f"data:{mime_type};base64,{base64_data}"
    
    ocr_payload = urllib.parse.urlencode({
        "apikey": "K84437255288957",
        "base64image": base64_full,
        "OCREngine": "2",
        "scale": "true",
        "isTable": "true"
    }).encode('utf-8')
    
    try:
        ocr_req = urllib.request.Request(
            ocr_url,
            data=ocr_payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(ocr_req, context=ssl_context) as ocr_res:
            ocr_json = json.loads(ocr_res.read().decode('utf-8'))
            
        if ocr_json.get("OCRExitCode") == 1:
            parsed_text = ocr_json["ParsedResults"][0]["ParsedText"]
        else:
            error_msg = ocr_json.get("ErrorMessage") or "OCR.space parsed with errors"
            if isinstance(error_msg, list):
                error_msg = ", ".join(error_msg)
            raise Exception(error_msg)
            
    except Exception as ocr_err:
        print("❌ OCR.space API parsing failed:", ocr_err)
        return Response({"error": f"Failed to perform OCR.space parsing: {str(ocr_err)}"}, status=status.HTTP_502_BAD_GATEWAY)

    # 2. Feed raw OCR text to Gemini 2.5 Flash to extract JSON representation
    prompt = (
        "คุณคือระบบ AI ผู้เชี่ยวชาญสกัดวิเคราะห์ใบตรวจแล็บแพทย์ (Lab Report Ingestion Specialist)\n"
        "กรุณาประมวลผลข้อความดิบที่ได้จากการสแกนใบแล็บคนไข้ด้านล่างนี้:\n"
        f"--- START SCANNED TEXT ---\n{parsed_text}\n--- END SCANNED TEXT ---\n\n"
        "และดำเนินการตามคำสั่งดังนี้:\n"
        "1. สกัดรายการค่าตรวจชีวเคมี/ชีวโมเลกุล (Biomarkers) ทั้งหมดที่พบ เช่น Fasting Blood Sugar, HbA1c, Cholesterol, LDL, ALT, GGT, Bun, Creatinine, หรืออื่นๆ\n"
        "2. เสนอแนะแกนระบบสรีรวิทยา TSPI 39 แกนที่ควรปรับเปลี่ยนตามผลพยาธิวิทยา (เช่น ค่าเบาหวานเสี่ยงปรับแกน 7) โดยกำหนดความรุนแรง (0-100) และอธิบายเหตุผลภาษาไทย\n\n"
        "ส่งกลับข้อมูลเป็น JSON เท่านั้นตามโครงสร้างนี้ ห้ามมีเครื่องหมาย Markdown ครอบหน้าหลัง:\n"
        "{\n"
        "  \"extractedBiomarkers\": [\n"
        "    {\"name\": \"Fasting Blood Sugar\", \"value\": 105.0, \"unit\": \"mg/dL\", \"referenceRange\": \"70-100\"}\n"
        "  ],\n"
        "  \"recommendedAxesUpdates\": [\n"
        "    {\"axisId\": 7, \"axisName\": \"Glycemic Regulation\", \"scoreImpact\": 65, \"reasoning\": \"ระดับน้ำตาลสะสมอยู่ในภาวะ Prediabetes\"}\n"
        "  ]\n"
        "}"
    )

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    gemini_payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        gemini_req = urllib.request.Request(
            gemini_url,
            data=json.dumps(gemini_payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        with urllib.request.urlopen(gemini_req, context=ssl_context) as gemini_res:
            res_json = json.loads(gemini_res.read().decode('utf-8'))
            candidate = res_json['candidates'][0]
            ocr_raw = candidate['content']['parts'][0]['text']
            ocr_data = json.loads(ocr_raw)
    except Exception as e:
        print("❌ Gemini OCR Parser Failed:", e)
        return Response({"error": f"Failed to perform Gemini OCR Parser: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

    # Programmatic Traffic Light Validation using LabRangeReference database lookup
    from patients.models import LabRangeReference
    refined_biomarkers = []
    for b in ocr_data.get("extractedBiomarkers", []):
        name = b.get("name", "").strip()
        val_str = str(b.get("value", "0")).replace(",", "")
        try:
            val = float(val_str)
        except ValueError:
            val = 0.0
            
        unit = b.get("unit", "")
        ref_range = b.get("referenceRange", "")
        
        # Default traffic light status is Normal (Green)
        status_color = "Normal"
        
        # Look up reference ranges in database
        ref = LabRangeReference.objects.filter(biomarker_name__iexact=name).first()
        if ref:
            if ref.max_warning > 0 and val > ref.max_warning:
                status_color = "High"  # Red
            elif ref.min_warning > 0 and val < ref.min_warning:
                status_color = "Low"  # Red
            elif ref.max_normal > 0 and val > ref.max_normal:
                status_color = "Warning"  # Yellow
            elif ref.min_normal > 0 and val < ref.min_normal:
                status_color = "Warning"  # Yellow
        else:
            # Fallback to simple reference range parsing if database has no record
            if ref_range and "-" in ref_range:
                try:
                    parts = ref_range.split("-")
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    if val > high:
                        status_color = "High"
                    elif val < low:
                        status_color = "Low"
                except Exception:
                    pass

        refined_biomarkers.append({
            "name": name,
            "value": val,
            "unit": unit,
            "referenceRange": ref_range,
            "status": status_color
        })

    return Response({
        "success": True,
        "extractedBiomarkers": refined_biomarkers,
        "recommendedAxesUpdates": ocr_data.get("recommendedAxesUpdates", [])
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_brain_training(request):
    """
    Logs a dataset pair (input parameters vs AI outputs) for training the local TSPI Brain.
    """
    patient_id = request.data.get('patientId')
    inputs = request.data.get('inputs', {})
    output_axes = request.data.get('output_axes', {})
    output_text = request.data.get('output_text', '')
    engine_used = request.data.get('engine_used', 'gemini')

    from patients.models import Patient, TSPIBrainTrainingLog
    patient = Patient.objects.filter(id=patient_id).first()

    log_entry = TSPIBrainTrainingLog.objects.create(
        patient=patient,
        inputs=inputs,
        output_axes=output_axes,
        output_text=output_text,
        engine_used=engine_used
    )

    return Response({
        "success": True,
        "log_id": log_entry.id
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def brain_training_stats(request):
    """
    Returns the total count of logged training pairs for the TSPI Brain.
    """
    from patients.models import TSPIBrainTrainingLog
    count = TSPIBrainTrainingLog.objects.count()
    reviewed_count = TSPIBrainTrainingLog.objects.filter(reviewed=True).count()
    return Response({
        "success": True,
        "logged_cases": count,
        "reviewed_cases": reviewed_count,
        # P1-C: readiness is gated on physician-reviewed cases, not raw logged chat turns.
        "ready": reviewed_count >= 30,
        "required_cases": 30
    })


class TSPIBrainTrainingLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing training log pairs collected for TSPI Brain self-learning"""
    serializer_class = TSPIBrainTrainingLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TSPIBrainTrainingLog.objects.all().order_by('-created_at')


class ModuleRegistryEntryViewSet(viewsets.ModelViewSet):
    """
    DB-backed TSPI Module Registry (roadmap 3-E). A physician approves a module by PATCHing
    mapping_status="APPROVED" + approved_by here — that becomes a real, queryable audit trail
    instead of a value baked into a JSON file with no history (ans.txt P0-4.11).
    """
    serializer_class = ModuleRegistryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ModuleRegistryEntry.objects.all().order_by('code')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_brain_model(request):
    """
    Trains the local TSPI Brain weights using OLS Ridge Regression on the collected logs.
    Saves the weights to a JSON file.
    """
    import numpy as np
    import json
    import os
    from patients.models import TSPIBrainTrainingLog

    # P1-C: only physician-reviewed logs may train the model — an unreviewed log is an
    # LLM-invented axis severity (see /api/ai/brain's :::BIO_UPDATE::: block) and must not
    # silently become "ground truth" that the model later predicts real patient scores from.
    logs = TSPIBrainTrainingLog.objects.filter(reviewed=True)
    N = logs.count()
    if N < 1:
        return Response({
            "success": False,
            "message": "ต้องการชุดข้อมูลที่แพทย์ตรวจสอบแล้ว (reviewed=True) อย่างน้อย 1 เคสเพื่อฝึกฝน — ยังไม่มี log ใดผ่านการตรวจสอบ"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Imputation defaults
    defaults = {
        "fbs": 90.0,
        "hba1c": 5.5,
        "crp": 0.5,
        "ldl": 110.0,
        "alt": 30.0,
        "ggt": 35.0
    }

    def safe_float(val, default):
        try:
            if val not in (None, ""):
                return float(val)
        except (ValueError, TypeError):
            pass
        return default

    X_list = []
    Y_list = []

    for log in logs:
        inputs = log.inputs or {}
        labs_data = inputs.get("labs", {})

        # Build features list
        fbs = safe_float(labs_data.get("fbs"), defaults["fbs"])
        hba1c = safe_float(labs_data.get("hba1c"), defaults["hba1c"])
        crp = safe_float(labs_data.get("crp"), defaults["crp"])
        ldl = safe_float(labs_data.get("ldl"), defaults["ldl"])
        alt = safe_float(labs_data.get("alt"), defaults["alt"])
        ggt = safe_float(labs_data.get("ggt"), defaults["ggt"])

        row_x = [1.0, fbs, hba1c, crp, ldl, alt, ggt]
        X_list.append(row_x)

        # Build output targets (39 axes)
        axes_data = log.output_axes or {}
        row_y = []
        for i in range(1, 40):
            val = axes_data.get(f"AXIS_{i}")
            row_y.append(safe_float(val, 50.0))  # Default base baseline score
        Y_list.append(row_y)

    X = np.array(X_list)
    Y = np.array(Y_list)

    # Ridge Regression (L2 regularization)
    # W = (X^T X + lambda I)^(-1) X^T Y
    D = X.shape[1]
    lam = 0.1  # L2 regularizer
    
    XtX = X.T.dot(X)
    I = np.eye(D)
    I[0, 0] = 0.0  # Do not regularize bias term
    
    try:
        W = np.linalg.inv(XtX + lam * I).dot(X.T).dot(Y)
    except np.linalg.LinAlgError:
        # Fallback to pseudo-inverse if singular
        W = np.linalg.pinv(XtX + lam * I).dot(X.T).dot(Y)

    # Save weights to json file
    # W is size (7, 39)
    weights_dict = {
        "bias": W[0].tolist(),  # W[0] has size (39,)
        "coefficients": {
            "fbs": W[1].tolist(),
            "hba1c": W[2].tolist(),
            "crp": W[3].tolist(),
            "ldl": W[4].tolist(),
            "alt": W[5].tolist(),
            "ggt": W[6].tolist(),
        },
        "cases_trained": N
    }

    config_dir = os.path.join(settings.BASE_DIR, '..', 'data')
    os.makedirs(config_dir, exist_ok=True)
    weights_path = os.path.join(config_dir, "tspi_brain_weights.json")

    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(weights_dict, f, indent=4, ensure_ascii=False)

    return Response({
        "success": True,
        "message": f"ฝึกฝนสำเร็จด้วยข้อมูล {N} เคส",
        "cases_trained": N,
        "coefficients": weights_dict["coefficients"]
    })


def markdown_to_html(text):
    if not text:
        return ""
    import re
    html = text
    # Convert headings
    html = re.sub(r'^###\s+(.*?)$', r'<h4 style="font-size: 12pt; font-weight: 700; margin-top: 15px; margin-bottom: 5px; color: #334155;">\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##\s+(.*?)$', r'<h3 style="font-size: 14pt; font-weight: 700; margin-top: 20px; margin-bottom: 8px; color: #1E3A5F;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#\s+(.*?)$', r'<h2 style="font-size: 16pt; font-weight: 700; margin-top: 25px; margin-bottom: 10px; color: #1E3A5F;">\1</h2>', html, flags=re.MULTILINE)
    
    # Convert bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Convert italic
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    lines = html.split('\n')
    new_lines = []
    
    in_list = False
    list_type = None
    
    in_table = False
    table_headers = []
    table_rows = []
    
    def render_html_table(headers, rows):
        t_html = '<div class="table-wrap"><table>'
        if headers:
            t_html += '<thead><tr>'
            for h in headers:
                t_html += f'<th>{h}</th>'
            t_html += '</tr></thead>'
        if rows:
            t_html += '<tbody>'
            for r in rows:
                t_html += '<tr>'
                for cell in r:
                    t_html += f'<td>{cell}</td>'
                t_html += '</tr>'
            t_html += '</tbody>'
        t_html += '</table></div>'
        return t_html

    for line in lines:
        stripped = line.strip()
        
        # 1. Handle Markdown Table parsing
        if stripped.startswith('|') and stripped.endswith('|'):
            # Close list if open
            if in_list:
                new_lines.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
                list_type = None
                
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            is_separator = all(re.match(r'^:?-+:?$', c) for c in cells) if cells else False
            
            if is_separator:
                continue
                
            if not in_table:
                in_table = True
                table_headers = cells
                table_rows = []
            else:
                table_rows.append(cells)
            continue
        else:
            if in_table:
                new_lines.append(render_html_table(table_headers, table_rows))
                in_table = False
                table_headers = []
                table_rows = []

        # 2. Handle Markdown Lists parsing
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_list and list_type != 'ul':
                new_lines.append('</ol>')
                in_list = False
            if not in_list:
                new_lines.append('<ul style="margin-top: 5px; margin-bottom: 10px; padding-left: 20px;">')
                in_list = True
                list_type = 'ul'
            new_lines.append(f'<li style="margin-bottom: 4px;">{stripped[2:]}</li>')
            
        elif re.match(r'^\d+\.\s+', stripped):
            match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
            if in_list and list_type != 'ol':
                new_lines.append('</ul>')
                in_list = False
            if not in_list:
                new_lines.append('<ol style="margin-top: 5px; margin-bottom: 10px; padding-left: 20px;">')
                in_list = True
                list_type = 'ol'
            new_lines.append(f'<li style="margin-bottom: 4px;">{match.group(2)}</li>')
            
        else:
            if in_list:
                new_lines.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
                list_type = None
                
            if stripped:
                if not stripped.startswith('<h') and not stripped.startswith('<d') and not stripped.startswith('<t') and not stripped.startswith('<b'):
                    new_lines.append(f'<p style="margin-bottom: 12px; text-align: justify; text-justify: inter-word;">{stripped}</p>')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
    if in_table:
        new_lines.append(render_html_table(table_headers, table_rows))
    if in_list:
        new_lines.append('</ul>' if list_type == 'ul' else '</ol>')
        
    html = '\n'.join(new_lines)
    
    # Replace clinical badges
    html = html.replace('[PASS]', '<span class="badge badge-pass">PASS</span>')
    html = html.replace('[HOLD]', '<span class="badge badge-hold">HOLD</span>')
    html = html.replace('[CONTRAINDICATED]', '<span class="badge badge-contraindicated">CONTRAINDICATED</span>')
    html = html.replace('[MEASURED]', '<span class="badge" style="background-color:#E2E8F0; color:#475569;">MEASURED</span>')
    html = html.replace('[DERIVED]', '<span class="badge" style="background-color:#EBF8FF; color:#2B6CB0;">DERIVED</span>')
    html = html.replace('[HYPOTHESIS]', '<span class="badge" style="background-color:#FFF5F5; color:#C53030;">HYPOTHESIS</span>')
    html = html.replace('[CLINICAL_INFERENCE]', '<span class="badge" style="background-color:#F0FFF4; color:#22543D;">CLINICAL INFERENCE</span>')
    html = html.replace('[NOT_AVAILABLE]', '<span class="badge" style="background-color:#F7FAFC; color:#718096;">NOT AVAILABLE</span>')

    return html


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_report_pdf_view(request, patient_id, report_id):
    """
    Finds a saved report in the patient's extra_data,
    renders it as a premium PDF using WeasyPrint, and returns it.
    """
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    import json
    import os
    import sys
    
    if sys.platform == "darwin":
        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')
    
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return HttpResponse("Patient not found", status=404)
        
    extra_data = patient.extra_data or {}
    reports = extra_data.get("generated_reports", [])
    
    # Find the report by ID
    report_obj = None
    for r in reports:
        if r.get("id") == report_id:
            report_obj = r
            break
            
    if not report_obj:
        return HttpResponse("Report not found", status=404)
        
    # Get chapters list
    raw_chapters = report_obj.get("report", [])
    chapters = []
    for ch in raw_chapters:
        title = ch.get("chapterTitle", "")
        content = ch.get("content", "")
        
        # Convert content markdown to HTML
        content_html = markdown_to_html(content)
        
        chapters.append({
            "chapterTitle": title,
            "content_html": content_html
        })
        
    # P1-B: axis names come from tspi_engine.py's OFFICIAL_39_AXES (single in-repo source of
    # truth) instead of reading the frontend's stale 36-axis tspi_36_axes_v2.json across the
    # repo boundary — eliminates the third, possibly-drifting copy of axis identity/naming.
    from .tspi_engine import OFFICIAL_39_AXES
    axis_names_map = dict(OFFICIAL_39_AXES)


    # Build context
    report_type = report_obj.get("reportType", "physician")
    report_type_label = "Physician Edition"
    if report_type == "patient":
        report_type_label = "Patient Edition"
    elif report_type == "multi-omics":
        report_type_label = "Multi-Omics Edition"
        
    created_at = report_obj.get("createdAt", "")
    date_str = ""
    try:
        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(created_at)
        if dt:
            date_str = dt.strftime('%d/%m/%Y')
    except Exception:
        date_str = created_at
        
    # Fetch active axes scores — prefer the AnalysisRecord this report was actually generated
    # from (gated: HYPOTHESIS axes have score=None there) so the PDF's axis table can't show a
    # number that contradicts the report's own narrative text for the same axis (ans.txt problem
    # #11 — the axis table used to bypass the ledger by reading latest_record.axis_N directly).
    # Falls back to the raw latest-record pull only for older reports saved before this existed.
    active_axes = []
    try:
        from .models import AnalysisRecord
        analysis_record_id = report_obj.get("analysisRecordId")
        analysis_record = None
        if analysis_record_id and (isinstance(analysis_record_id, int) or str(analysis_record_id).isdigit()):
            analysis_record = AnalysisRecord.objects.filter(id=int(analysis_record_id), patient=patient).first()

        if analysis_record:
            thirty_nine_axes = (analysis_record.ledger or {}).get("thirty_nine_axes", {})
            for i in range(1, 40):
                axis = thirty_nine_axes.get(f"AXIS_{i}")
                if axis and axis.get("severity_score") is not None:
                    axis_name = axis_names_map.get(i, axis.get("name", f"Axis {i}"))
                    active_axes.append({
                        "id": f"AXIS_{i}",
                        "name": axis_name,
                        "score": axis.get("severity_score"),
                        "evidence_status": axis.get("evidence_status")
                    })
        else:
            latest_record = patient.axes_records.order_by('-record_date').first()
            if latest_record:
                for i in range(1, 40):
                    val = getattr(latest_record, f"axis_{i}", None)
                    if val is not None:
                        axis_name = axis_names_map.get(i, f"Axis {i}")
                        active_axes.append({
                            "id": f"AXIS_{i}",
                            "name": axis_name,
                            "score": val
                        })
    except Exception as e:
        logger.error(f"Error loading patient biological records: {e}")

    # Local Sarabun font files (Thai+Latin, single file per weight) for WeasyPrint —
    # see backend/patients/static/fonts/ — WeasyPrint reads these via file:// URLs
    # since it does not fetch relative static URLs without a running server.
    fonts_dir = os.path.join(settings.BASE_DIR, "patients", "static", "fonts")
    font_regular_url = f"file://{os.path.join(fonts_dir, 'Sarabun-Regular.ttf')}"
    font_semibold_url = f"file://{os.path.join(fonts_dir, 'Sarabun-SemiBold.ttf')}"
    font_bold_url = f"file://{os.path.join(fonts_dir, 'Sarabun-Bold.ttf')}"

    context = {
        "patient": patient,
        "report_obj": report_obj,
        "report_type_label": report_type_label,
        "date_str": date_str,
        "chapters": chapters,
        "axis_names_map": axis_names_map,
        "active_axes": active_axes,
        "font_regular_url": font_regular_url,
        "font_semibold_url": font_semibold_url,
        "font_bold_url": font_bold_url
    }

    # Render template to HTML string
    html_string = render_to_string("patients/precision_medicine_report_v4.html", context)
    
    # Generate PDF using WeasyPrint
    try:
        from weasyprint import HTML
        pdf_file = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f"TSPI_Report_{patient.hn or patient.id}_{report_id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f"WeasyPrint PDF generation error: {e}")
        return HttpResponse(f"PDF generation failed: {e}. Please ensure Homebrew system dependencies (pango, cairo) are installed on this machine.", status=500)

