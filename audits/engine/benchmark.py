"""
Per-person AI spend benchmarks. Pure function — no DB, no I/O.

Ranges are conservative estimates derived from public vendor pricing
(Cursor $20/seat, Copilot $19/seat, ChatGPT Plus $20, Claude Pro $20,
Claude Team $30/seat, ChatGPT Team $30/seat, etc.) plus realistic
stack assumptions:
  - "coding" assumes IDE tool + chat assistant (Cursor + Claude/ChatGPT)
  - "writing"/"research" assumes one chat subscription
  - "mixed" assumes one chat + one IDE/work tool

Larger teams get a small volume discount from team plans replacing
individual subs. Numbers are documented in PRICING_DATA.md.
"""

# USD per person per month — low/median/high stack cost
BENCHMARKS_BY_USE_CASE = {
    "coding":   {"low": 50, "median": 90,  "high": 150},
    "writing":  {"low": 20, "median": 35,  "high": 60},
    "data":     {"low": 30, "median": 55,  "high": 90},
    "research": {"low": 20, "median": 40,  "high": 70},
    "mixed":    {"low": 30, "median": 60,  "high": 100},
}


def _team_size_factor(team_size: int) -> float:
    """Larger teams get small volume effects from team plans replacing individual subs."""
    if team_size <= 5:
        return 1.00
    if team_size <= 20:
        return 0.95
    if team_size <= 50:
        return 0.90
    return 0.85


def get_benchmark(team_size: int, use_case: str, current_total_spend: float) -> dict:
    """
    Return per-person spend, the typical range for this team profile, and a verdict.

    verdict ∈ {"below", "typical", "above"} — drives the UI tone (green / neutral / orange).
    """
    if team_size <= 0:
        team_size = 1

    base = BENCHMARKS_BY_USE_CASE.get(use_case, BENCHMARKS_BY_USE_CASE["mixed"])
    factor = _team_size_factor(team_size)

    low = round(base["low"] * factor)
    median = round(base["median"] * factor)
    high = round(base["high"] * factor)

    per_person = round(current_total_spend / team_size, 2)

    if per_person < low:
        verdict = "below"
    elif per_person > high:
        verdict = "above"
    else:
        verdict = "typical"

    return {
        "per_person": per_person,
        "low": low,
        "median": median,
        "high": high,
        "verdict": verdict,
        "use_case": use_case,
        "team_size": team_size,
    }
