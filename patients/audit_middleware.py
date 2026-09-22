"""Request audit trail. Never records request bodies, passwords, tokens, or clinical payloads."""

import re
import uuid


class RequestAuditMiddleware:
    EXCLUDED_PREFIXES = ("/static/", "/media/", "/favicon.ico")
    PATIENT_PATH = re.compile(r"/patients/(?P<patient_id>[^/]+)")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4()
        response = self.get_response(request)
        if not request.path.startswith(self.EXCLUDED_PREFIXES):
            self._write_log(request, response, request_id)
        response["X-Request-ID"] = str(request_id)
        return response

    @staticmethod
    def _client_ip(request):
        # The first forwarded address is used only when the reverse proxy sets it.
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", ""))[:100]

    def _write_log(self, request, response, request_id):
        try:
            from patients.models import AuditLog
            user = getattr(request, "user", None)
            actor = getattr(user, "username", None) if getattr(user, "is_authenticated", False) else "ANONYMOUS"
            target_match = self.PATIENT_PATH.search(request.path)
            AuditLog.objects.create(
                actor_id=str(actor)[:100],
                target_id=(target_match.group("patient_id") if target_match else "SYSTEM")[:100],
                action=f"HTTP {request.method} {response.status_code}",
                layer="HTTP",
                client_ip=self._client_ip(request),
                governance_status="AUDIT_RECORDED",
                event_type="HTTP_REQUEST",
                request_method=request.method[:10],
                request_path=request.path[:500],
                response_status=response.status_code,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                request_id=request_id,
                metadata={"query_parameter_names": sorted(request.GET.keys())[:30]},
            )
        except Exception:
            # Audit storage must not turn a successful clinical request into an error.
            pass
