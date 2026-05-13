# Tests

## How to run

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest audits/tests/

# With verbose output
pytest audits/tests/ -v

# With coverage
pytest audits/tests/ --tb=short
```

All tests run in ~20ms with no database, no network, and no Django test runner overhead. The engine is pure Python.

---

## Test file: `audits/tests/test_engine.py`

Tests the core audit engine using a minimal inline pricing fixture (no DB required).

### Happy path

| Test | What it covers |
|---|---|
| `test_cursor_business_2_seats_recommends_cheaper_option` | 2 seats on a plan requiring min 5 → seat waste flagged, savings > 0 |
| `test_single_user_cursor_pro_is_optimal` | 1 user on cheapest solo plan → savings within honesty rail |
| `test_copilot_individual_cheaper_than_cursor_pro_for_coding` | Cross-vendor switch surfaced when meaningfully cheaper |
| `test_writing_use_case_does_not_recommend_cursor` | Fit-score logic: Cursor (score 1 for writing) never recommended for writing teams |
| `test_zero_spend_tool_skipped` | Free/unused tools with $0 spend skipped entirely, not counted in tool_count |
| `test_multi_tool_savings_aggregate` | `result.monthly_savings` equals sum of per-finding savings (no rounding drift) |

### Honesty rails

| Test | What it covers |
|---|---|
| `test_savings_never_exceed_80_percent` | No finding claims savings > 80% of current spend (MAX_SAVINGS_RATIO cap) |
| `test_savings_below_threshold_marked_optimal` | Findings with savings < $5/mo surfaced as `is_optimal=True` |
| `test_recommended_cost_never_exceeds_current` | Recommended cost is always ≤ current spend |

### Routing

| Test | What it covers |
|---|---|
| `test_high_savings_route` | Large savings → route is `high_savings` or `normal`, never `optimal` |
| `test_optimal_route_when_no_savings` | All tools already cheapest → route is `optimal` |

### API tools

| Test | What it covers |
|---|---|
| `test_api_tool_uses_user_reported_spend` | API-style tools (Anthropic API, OpenAI API) use user-reported spend, not computed from plan pricing |

---

## Total: 12 tests, all engine-layer, zero I/O
