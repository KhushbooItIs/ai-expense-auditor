"""
AI-generated ~100-word audit summary.
Falls back to a templated paragraph on any error so the result page always ships.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a finance-savvy CTO friend reviewing a startup's AI tool spend.
Given a structured audit result, write a single paragraph of ~100 words.
Rules:
- Use only the numbers provided — never invent figures
- Speak directly to the founder ("you", "your team")
- Be honest: if they're already spending well, say so
- Never be salesy; mention Credex only if credex_eligible is true
- End with one specific, actionable next step
- Plain language, no jargon, no bullet points"""


def generate_summary(result: dict) -> str:
    try:
        return _openai_summary(result)
    except Exception as exc:
        logger.warning("AI summary failed, using fallback: %s", exc)
        return _templated_summary(result)


def _openai_summary(result: dict) -> str:
    import openai  # imported lazily so the app boots without the package in dev
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=5.0)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({
                "monthly_savings": result["monthly_savings"],
                "annual_savings": result["annual_savings"],
                "total_current_spend": result["total_current_spend"],
                "route": result["route"],
                "credex_eligible": result["credex_eligible"],
                "tool_count": result["tool_count"],
                "findings": [
                    {
                        "vendor_name": f["vendor_name"],
                        "current_plan": f["current_plan"],
                        "monthly_savings": f["monthly_savings"],
                        "recommended_action": f["recommended_action"],
                        "reasoning": f["reasoning"],
                        "is_optimal": f["is_optimal"],
                    }
                    for f in result["findings"]
                ],
            })},
        ],
    )
    return response.choices[0].message.content.strip()


def _templated_summary(result: dict) -> str:
    n_tools = result["tool_count"]
    total_spend = result["total_current_spend"]
    monthly = result["monthly_savings"]
    annual = result["annual_savings"]
    route = result["route"]
    findings = result["findings"]

    # Find the biggest saving
    top = max(findings, key=lambda f: f["monthly_savings"], default=None)

    if route == "optimal" or monthly < 5:
        return (
            f"Your team is spending ${total_spend:.0f}/mo across {n_tools} AI tool(s) "
            f"and you're already making smart choices. We didn't find meaningful savings — "
            f"every plan matches your team size and use case well. "
            f"Keep an eye on your seat counts as your team grows; "
            f"that's usually where AI tool costs creep up first."
        )

    top_action = top["recommended_action"] if top else "review your plans"
    return (
        f"Your team is spending ${total_spend:.0f}/mo across {n_tools} AI tool(s). "
        f"We found ${monthly:.0f}/mo (${annual:.0f}/yr) in potential savings. "
        f"The biggest opportunity: {top_action} — "
        f"{top['reasoning'] if top else ''} "
        f"Start there, confirm the plan change covers your workflow, "
        f"and you could reclaim that budget within the month."
    )
