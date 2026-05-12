import json
import dataclasses
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from audits.engine.input import AuditInput, ToolLine
from audits.engine.runner import audit as run_engine
from audits.models import Audit
from audits.services.summary import generate_summary
from pricing.loader import get_pricing_data

SUPPORTED_VENDORS = [
    ("cursor",        "Cursor"),
    ("copilot",       "GitHub Copilot"),
    ("claude",        "Claude"),
    ("chatgpt",       "ChatGPT"),
    ("anthropic_api", "Anthropic API"),
    ("openai_api",    "OpenAI API"),
    ("gemini",        "Gemini"),
    ("windsurf",      "Windsurf"),
]


def index(request):
    pricing = get_pricing_data()
    vendor_plans = {}
    for vendor_key, vendor_name in SUPPORTED_VENDORS:
        plans = [
            (pk, p["plan_name"])
            for (vk, pk), p in pricing["plans"].items()
            if vk == vendor_key
        ]
        vendor_plans[vendor_key] = {"name": vendor_name, "plans": plans}

    return render(request, "audits/form.html", {
        "vendors": SUPPORTED_VENDORS,
        "vendor_plans_json": json.dumps(vendor_plans),
    })


@ratelimit(key="ip", rate="5/h", method="POST", block=True)
@require_http_methods(["POST"])
def run_audit(request):
    # Honeypot — bots fill hidden fields, humans don't
    if request.POST.get("website"):
        return redirect("/")

    tools = _parse_tools(request.POST)
    if not tools:
        return redirect("/")

    try:
        team_size = int(request.POST.get("team_size", 1))
    except (ValueError, TypeError):
        team_size = 1

    use_case = request.POST.get("use_case", "mixed")
    if use_case not in ("coding", "writing", "data", "research", "mixed"):
        use_case = "mixed"

    inp = AuditInput(tools=tools, team_size=team_size, use_case=use_case)
    pricing = get_pricing_data()
    result = run_engine(inp, pricing)

    result_dict = _result_to_dict(result)
    input_dict = _input_to_dict(inp)
    summary = generate_summary(result_dict)

    audit_obj = Audit.objects.create(
        input_json=input_dict,
        result_json=result_dict,
        summary_text=summary,
    )

    return redirect("audit_result", slug=audit_obj.slug)


def audit_result(request, slug):
    audit_obj = get_object_or_404(Audit, slug=slug)
    return render(request, "audits/result.html", {
        "audit": audit_obj,
        "result": audit_obj.result_json,
        "is_share": False,
    })


def audit_share(request, slug):
    """Public share view — queries Audit only, structurally cannot expose PII."""
    audit_obj = get_object_or_404(Audit, slug=slug)
    return render(request, "audits/result.html", {
        "audit": audit_obj,
        "result": audit_obj.result_json,
        "is_share": True,
    })


def healthz(request):
    from django.http import HttpResponse
    return HttpResponse("ok")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_tools(post) -> list[ToolLine]:
    tools = []
    i = 0
    while True:
        vendor_key = post.get(f"tools[{i}][vendor_key]")
        if vendor_key is None:
            break
        plan_key = post.get(f"tools[{i}][plan_key]", "")
        try:
            spend = float(post.get(f"tools[{i}][monthly_spend]", 0))
        except (ValueError, TypeError):
            spend = 0.0
        try:
            seats = int(post.get(f"tools[{i}][seats]", 1))
        except (ValueError, TypeError):
            seats = 1
        if vendor_key and plan_key:
            tools.append(ToolLine(vendor_key=vendor_key, plan_key=plan_key,
                                  monthly_spend=spend, seats=max(1, seats)))
        i += 1
    return tools


def _result_to_dict(result) -> dict:
    findings = []
    for f in result.findings:
        findings.append({
            "vendor_key": f.vendor_key,
            "vendor_name": f.vendor_name,
            "current_plan": f.current_plan,
            "current_seats": f.current_seats,
            "current_spend": f.current_spend,
            "recommended_action": f.recommended_action,
            "recommended_cost": f.recommended_cost,
            "monthly_savings": f.monthly_savings,
            "reasoning": f.reasoning,
            "evidence": f.evidence,
            "is_optimal": f.is_optimal,
        })
    return {
        "findings": findings,
        "monthly_savings": result.monthly_savings,
        "annual_savings": result.annual_savings,
        "total_current_spend": result.total_current_spend,
        "route": result.route,
        "credex_eligible": result.credex_eligible,
        "tool_count": result.tool_count,
    }


def _input_to_dict(inp) -> dict:
    return {
        "tools": [dataclasses.asdict(t) for t in inp.tools],
        "team_size": inp.team_size,
        "use_case": inp.use_case,
    }
