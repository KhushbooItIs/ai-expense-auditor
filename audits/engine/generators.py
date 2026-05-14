"""
Candidate generators — pure functions, no Django/DB imports.
Each takes (line, inp, pricing) and returns a list of Candidates.
Add a new generator here and append it to GENERATORS to extend the engine.
"""
from audits.engine.input import AuditInput, ToolLine
from audits.engine.candidate import Candidate

# Vendor keys where the user reports their own spend (no fixed plan to right-size)
_API_VENDOR_KEYS = {"anthropic_api", "openai_api"}

# Plan keys that represent usage-based billing — $0 price is misleading as an alternative
_USAGE_BASED_PLAN_KEYS = {"api"}


def _fit_score(pricing: dict, vendor_key: str, plan_key: str, use_case: str) -> int:
    entry = pricing["fit_scores"].get((vendor_key, plan_key, use_case))
    return entry["score"] if entry else 0


def _plan(pricing: dict, vendor_key: str, plan_key: str) -> dict | None:
    return pricing["plans"].get((vendor_key, plan_key))


def _cost_for_seats(plan: dict, seats: int) -> float:
    if plan.get("price_per_seat") is not None:
        effective = max(seats, plan["min_seats"])
        return plan["price_per_seat"] * effective
    if plan.get("price_monthly") is not None:
        return plan["price_monthly"]
    return 0.0


def _seats_fit(plan: dict, seats: int) -> bool:
    """Return False if this plan cannot accommodate the given seat count."""
    max_s = plan.get("max_seats")
    return max_s is None or seats <= max_s


def keep_current(line: ToolLine, inp: AuditInput, pricing: dict) -> list[Candidate]:
    """Baseline: stay on current plan. Always emitted."""
    plan = _plan(pricing, line.vendor_key, line.plan_key)
    if not plan:
        return []

    # For API tools use the user-reported spend as the cost
    if line.vendor_key in _API_VENDOR_KEYS:
        cost = line.monthly_spend
    else:
        cost = _cost_for_seats(plan, line.seats)

    score = _fit_score(pricing, line.vendor_key, line.plan_key, inp.use_case)

    return [Candidate(
        vendor_key=line.vendor_key,
        plan_key=line.plan_key,
        vendor_name=plan["vendor_name"],
        plan_name=plan["plan_name"],
        label=f"Stay on {plan['vendor_name']} {plan['plan_name']}",
        monthly_cost=cost,
        fit_score=score,
        reasoning="Current plan.",
        evidence={"source_url": plan["source_url"]},
        is_current=True,
        is_credex_eligible=plan["credex_eligible"],
    )]


def downgrade_within_vendor(line: ToolLine, inp: AuditInput, pricing: dict) -> list[Candidate]:
    """Cheaper plans from the same vendor that still cover the use case."""
    if line.vendor_key in _API_VENDOR_KEYS:
        return []

    current_plan = _plan(pricing, line.vendor_key, line.plan_key)
    if not current_plan:
        return []

    # Use what the user reports paying — not the theoretical plan price
    current_cost = line.monthly_spend
    current_score = _fit_score(pricing, line.vendor_key, line.plan_key, inp.use_case)

    candidates = []
    for (vk, pk), plan in pricing["plans"].items():
        if vk != line.vendor_key or pk == line.plan_key:
            continue
        if pk in _USAGE_BASED_PLAN_KEYS:
            continue  # usage-based pricing — $0 label would be misleading

        if not _seats_fit(plan, line.seats):
            continue  # plan cannot accommodate this seat count

        cost = _cost_for_seats(plan, line.seats)
        if cost >= current_cost:
            continue  # not cheaper than what they're paying

        score = _fit_score(pricing, vk, pk, inp.use_case)
        if score == 0 or score < current_score - 1:
            continue  # unrated or significant capability drop

        candidates.append(Candidate(
            vendor_key=vk,
            plan_key=pk,
            vendor_name=plan["vendor_name"],
            plan_name=plan["plan_name"],
            label=f"Downgrade to {plan['vendor_name']} {plan['plan_name']}",
            monthly_cost=cost,
            fit_score=score,
            reasoning=(
                f"{plan['vendor_name']} {plan['plan_name']} covers your {inp.use_case} "
                f"workflow at ${cost:.0f}/mo vs the ${current_cost:.0f}/mo you're paying now."
            ),
            evidence={
                "current_plan": current_plan["plan_name"],
                "current_cost": current_cost,
                "recommended_plan": plan["plan_name"],
                "recommended_cost": cost,
                "source_url": plan["source_url"],
            },
            is_credex_eligible=plan["credex_eligible"],
        ))

    return candidates


def rightsize_seats(line: ToolLine, inp: AuditInput, pricing: dict) -> list[Candidate]:
    """
    If the user is on a per-seat plan but their seat count is below the plan's
    min_seats floor, they're paying for seats they can't use.
    Suggest the cheapest per-seat plan that matches their actual seat count.
    """
    if line.vendor_key in _API_VENDOR_KEYS:
        return []

    current_plan = _plan(pricing, line.vendor_key, line.plan_key)
    if not current_plan or current_plan.get("price_per_seat") is None:
        return []

    if line.seats >= current_plan["min_seats"]:
        return []  # no seat waste

    # Find the cheapest per-seat plan from the same vendor with min_seats <= actual seats
    candidates = []
    for (vk, pk), plan in pricing["plans"].items():
        if vk != line.vendor_key or pk == line.plan_key:
            continue
        if plan.get("price_per_seat") is None:
            continue
        if plan["min_seats"] > line.seats:
            continue  # still requires more seats than they have

        cost = _cost_for_seats(plan, line.seats)
        current_cost = _cost_for_seats(current_plan, line.seats)
        if cost >= current_cost:
            continue

        score = _fit_score(pricing, vk, pk, inp.use_case)
        if score == 0:
            continue

        waste = current_plan["min_seats"] - line.seats
        candidates.append(Candidate(
            vendor_key=vk,
            plan_key=pk,
            vendor_name=plan["vendor_name"],
            plan_name=plan["plan_name"],
            label=f"Switch to {plan['vendor_name']} {plan['plan_name']} (right-size seats)",
            monthly_cost=cost,
            fit_score=score,
            reasoning=(
                f"You have {line.seats} seat(s) but {current_plan['plan_name']} "
                f"charges for a minimum of {current_plan['min_seats']}. "
                f"You're paying for {waste} unused seat(s)."
            ),
            evidence={
                "actual_seats": line.seats,
                "plan_min_seats": current_plan["min_seats"],
                "unused_seats": waste,
                "current_cost": current_cost,
                "recommended_cost": cost,
                "source_url": plan["source_url"],
            },
            is_credex_eligible=plan["credex_eligible"],
        ))

    return candidates


def switch_to_alternative(line: ToolLine, inp: AuditInput, pricing: dict) -> list[Candidate]:
    """
    Different vendor, similar capability (fit score within 1 point of current),
    meaningfully cheaper (saves at least $5/mo vs what the user reports paying).
    """
    if line.vendor_key in _API_VENDOR_KEYS:
        return []

    current_plan = _plan(pricing, line.vendor_key, line.plan_key)
    if not current_plan:
        return []

    # Use what the user reports paying as the baseline — not the theoretical plan price
    current_cost = line.monthly_spend
    current_score = _fit_score(pricing, line.vendor_key, line.plan_key, inp.use_case)

    candidates = []
    for (vk, pk), plan in pricing["plans"].items():
        if vk == line.vendor_key:
            continue  # same vendor handled by downgrade generator
        if vk in _API_VENDOR_KEYS:
            continue
        if pk in _USAGE_BASED_PLAN_KEYS:
            continue  # usage-based pricing — $0 label would be misleading

        if not _seats_fit(plan, line.seats):
            continue  # plan cannot accommodate this seat count

        score = _fit_score(pricing, vk, pk, inp.use_case)
        if score == 0:
            continue
        if score < current_score - 1:
            continue  # would be a significant capability downgrade

        cost = _cost_for_seats(plan, line.seats)
        if current_cost - cost < 5.0:
            continue  # saves less than $5/mo — not worth the switch friction

        candidates.append(Candidate(
            vendor_key=vk,
            plan_key=pk,
            vendor_name=plan["vendor_name"],
            plan_name=plan["plan_name"],
            label=f"Switch to {plan['vendor_name']} {plan['plan_name']}",
            monthly_cost=cost,
            fit_score=score,
            reasoning=(
                f"{plan['vendor_name']} {plan['plan_name']} is a strong fit for "
                f"{inp.use_case} work at ${cost:.0f}/mo — "
                f"${current_cost - cost:.0f}/mo less than you're paying now."
            ),
            evidence={
                "current_vendor": current_plan["vendor_name"],
                "current_plan": current_plan["plan_name"],
                "current_cost": current_cost,
                "alt_vendor": plan["vendor_name"],
                "alt_plan": plan["plan_name"],
                "alt_cost": cost,
                "fit_score": score,
                "current_fit_score": current_score,
                "source_url": plan["source_url"],
            },
            is_credex_eligible=plan["credex_eligible"],
        ))

    return candidates


def surface_credex(line: ToolLine, inp: AuditInput, pricing: dict) -> list[Candidate]:
    """
    Flag tools where Credex can source discounted licenses.
    Doesn't generate a lower-cost candidate — just tags the current plan
    so the aggregator knows to show the Credex CTA.
    Returns nothing if the current plan is not Credex-eligible.
    """
    plan = _plan(pricing, line.vendor_key, line.plan_key)
    if not plan or not plan["credex_eligible"]:
        return []
    # Return empty — the eligibility flag is on the keep_current candidate.
    # The runner checks credex_eligible on the chosen candidate to set AuditResult.credex_eligible.
    return []


GENERATORS = [
    keep_current,
    downgrade_within_vendor,
    rightsize_seats,
    switch_to_alternative,
    surface_credex,
]
