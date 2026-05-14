"""
Benchmark unit tests — pure function, no DB.
Run: pytest audits/tests/test_benchmark.py
"""
from audits.engine.benchmark import get_benchmark


def test_below_typical_marks_lean_stack():
    b = get_benchmark(team_size=5, use_case="coding", current_total_spend=100)
    assert b["per_person"] == 20.0
    assert b["verdict"] == "below"
    assert b["low"] == 50  # 50 * factor(1.0) for 5-person


def test_above_typical_marks_overspend():
    b = get_benchmark(team_size=5, use_case="writing", current_total_spend=500)
    assert b["per_person"] == 100.0
    assert b["verdict"] == "above"
    assert b["high"] == 60


def test_typical_in_range():
    b = get_benchmark(team_size=10, use_case="mixed", current_total_spend=600)
    assert b["per_person"] == 60.0
    assert b["verdict"] == "typical"


def test_team_size_factor_applied():
    """Larger teams should get a slightly lower benchmark band (volume effect)."""
    small = get_benchmark(team_size=5, use_case="coding", current_total_spend=0)
    large = get_benchmark(team_size=100, use_case="coding", current_total_spend=0)
    assert large["median"] < small["median"]


def test_unknown_use_case_falls_back_to_mixed():
    b = get_benchmark(team_size=10, use_case="something_weird", current_total_spend=0)
    mixed = get_benchmark(team_size=10, use_case="mixed", current_total_spend=0)
    assert b["low"] == mixed["low"]
    assert b["high"] == mixed["high"]


def test_zero_team_size_normalised_to_one():
    b = get_benchmark(team_size=0, use_case="coding", current_total_spend=100)
    assert b["team_size"] == 1
    assert b["per_person"] == 100.0
