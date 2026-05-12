import json
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from audits.models import Audit
from leads.models import Lead
from leads.services.email import send_audit_confirmation


@require_http_methods(["POST"])
def capture_lead(request):
    data = json.loads(request.body)
    slug = data.get("slug", "")
    email = data.get("email", "").strip()

    if not email or not slug:
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    audit_obj = get_object_or_404(Audit, slug=slug)

    # Idempotent — don't create a second Lead if already captured
    if hasattr(audit_obj, "lead"):
        return JsonResponse({"ok": True})

    lead = Lead.objects.create(
        audit=audit_obj,
        email=email,
        company=data.get("company", ""),
        role=data.get("role", ""),
        team_size=data.get("team_size") or None,
        consent_credex_outreach=bool(data.get("consent_credex_outreach", False)),
    )

    try:
        send_audit_confirmation(lead, audit_obj)
    except Exception:
        pass  # email failure must never break lead capture

    return JsonResponse({"ok": True})
