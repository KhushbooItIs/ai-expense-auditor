"""
Main engine entry point. Pure Python — no Django, no DB, no HTTP.
Call audit(inp, pricing) with data from pricing.loader.get_pricing_data().
"""
from audits.engine.input import AuditInput
from audits.engine.candidate import AuditResult, Candidate, Finding
from audits.engine.generators import GENERATORS

SAVINGS_THRESHOLD = 5.0    # ignore savings < $5/mo (noise)
MAX_SAVINGS_RATIO = 0.80   # never claim savings > 80% of current spend (honesty rail)
HIGH_SAVINGS_THRESHOLD = 500.0
OPTIMAL_THRESHOLD = 100.0


def audit(inp: AuditInput, pricing: dict) -> AuditResult:
    findings: list[Finding] = []
    credex_eligible = False

    for line in inp.tools:
        if line.monthly_spend <= 0:
            continue  # free/unused tool — skip

        # Generate all plausible alternatives for this tool line
        candidates: list[Candidate] = []
        for gen in GENERATORS:
            candidates.extend(gen(line, inp, pricing))

        if not candidates:
            continue

        valid = [c for c in candidates if c.is_valid(inp)]
        if not valid:
            continue

        # Pick best: cheapest first, break ties by preferring higher fit score
        best = min(valid, key=lambda c: (c.monthly_cost, -c.fit_score))

        # Track Credex eligibility on whichever plan they're staying on
        current = next((c for c in valid if c.is_current), None)
        if current and current.is_credex_eligible:
            credex_eligible = True

        raw_savings = line.monthly_spend - best.monthly_cost
        # Honesty rail: cap at 80% of current spend to avoid absurd claims
        savings = min(raw_savings, line.monthly_spend * MAX_SAVINGS_RATIO)

        if savings >= SAVINGS_THRESHOLD and not best.is_current:
            findings.append(Finding(
                vendor_key=line.vendor_key,
                vendor_name=best.vendor_name,
                current_plan=_plan_name(pricing, line.vendor_key, line.plan_key),
                current_seats=line.seats,
                current_spend=line.monthly_spend,
                recommended_action=best.label,
                recommended_cost=best.monthly_cost,
                monthly_savings=round(savings, 2),
                reasoning=best.reasoning,
                evidence=best.evidence,
                is_optimal=False,
            ))
        else:
            # Current plan is already optimal (or savings too small to surface)
            findings.append(Finding(
                vendor_key=line.vendor_key,
                vendor_name=_vendor_name(pricing, line.vendor_key),
                current_plan=_plan_name(pricing, line.vendor_key, line.plan_key),
                current_seats=line.seats,
                current_spend=line.monthly_spend,
                recommended_action="Keep current plan",
                recommended_cost=line.monthly_spend,
                monthly_savings=0,
                reasoning="This plan is well-matched to your team size and use case.",
                evidence={},
                is_optimal=True,
            ))

    total_savings = round(sum(f.monthly_savings for f in findings), 2)
    total_spend = round(sum(t.monthly_spend for t in inp.tools if t.monthly_spend > 0), 2)

    # Route determines which CTA to show on the result page
    if total_savings >= HIGH_SAVINGS_THRESHOLD:
        route = "high_savings"
    elif total_savings < OPTIMAL_THRESHOLD:
        route = "optimal"
    else:
        route = "normal"

    return AuditResult(
        findings=findings,
        monthly_savings=total_savings,
        annual_savings=round(total_savings * 12, 2),
        total_current_spend=total_spend,
        route=route,
        credex_eligible=credex_eligible,
        tool_count=len(findings),
    )


def _plan_name(pricing: dict, vendor_key: str, plan_key: str) -> str:
    plan = pricing["plans"].get((vendor_key, plan_key))
    return plan["plan_name"] if plan else plan_key.title()


def _vendor_name(pricing: dict, vendor_key: str) -> str:
    for (vk, _), plan in pricing["plans"].items():
        if vk == vendor_key:
            return plan["vendor_name"]
    return vendor_key.title()
