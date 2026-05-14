# Tests

## How to run

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest audits/tests/

# With verbose output
pytest audits/tests/ -v

# Lint
ruff check .
```

All tests run in ~30ms — pure Python, no database, no network, no Django test runner overhead.

**CI:** Every push to `main` runs lint + tests via [.github/workflows/ci.yml](.github/workflows/ci.yml). The badge / green check on the latest commit on GitHub is the source of truth.

---

## Test file 1 — `audits/tests/test_engine.py` (14 tests)

Tests the audit engine using a minimal inline pricing fixture (no DB required).

### Happy path

| Test | What it covers |
|---|---|
| `test_cursor_business_2_seats_recommends_cheaper_option` | 2 seats on a plan requiring min 5 → seat waste flagged, savings > 0 |
| `test_single_user_cursor_pro_is_optimal` | 1 user on cheapest solo plan → savings within honesty rail |
| `test_copilot_individual_cheaper_than_cursor_pro_for_coding` | Cross-vendor switch surfaced when meaningfully cheaper |
| `test_writing_use_case_does_not_recommend_cursor` | Fit-score logic: Cursor (score 1 for writing) never recommended for writing teams |
| `test_zero_spend_tool_skipped` | Free/unused tools with $0 spend skipped entirely |
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
| `test_high_savings_route` | Large savings → route is `high_savings` |
| `test_optimal_route_when_no_savings` | All tools already cheapest → route is `optimal` |

### API tools

| Test | What it covers |
|---|---|
| `test_api_tool_uses_user_reported_spend` | API-style tools (Anthropic API, OpenAI API) use user-reported spend, not computed from plan pricing |

### Verify-billing (reported spend >> retail)

| Test | What it covers |
|---|---|
| `test_reported_spend_far_above_retail_flagged_as_verify_billing` | $1000 reported on a $20 plan → surface a 'verify billing' finding, never mark optimal |
| `test_reported_spend_matching_retail_is_optimal` | Reporting actual retail price → finding is optimal (no false positives) |

---

## Test file 2 — `audits/tests/test_benchmark.py` (6 tests)

Tests the per-person spend benchmark module ([audits/engine/benchmark.py](audits/engine/benchmark.py)).

| Test | What it covers |
|---|---|
| `test_below_typical_marks_lean_stack` | $20/person on coding → verdict = "below" |
| `test_above_typical_marks_overspend` | $100/person on writing (high is $60) → verdict = "above" |
| `test_typical_in_range` | $60/person on mixed (range 30-100) → verdict = "typical" |
| `test_team_size_factor_applied` | 100-person team gets lower median than 5-person team (volume effect) |
| `test_unknown_use_case_falls_back_to_mixed` | Unknown use_case input doesn't crash; uses "mixed" defaults |
| `test_zero_team_size_normalised_to_one` | `team_size=0` divides by 1, not by zero |

---

## Test file 3 — `audits/tests/test_referrals.py` (3 tests)

Tests the referral attribution feature (audit-to-audit referral tracking via `Audit.referred_by_slug`).

| Test | What it covers |
|---|---|
| `test_referrer_slug_stored_on_audit` | New audit keeps `referred_by_slug` attribution |
| `test_referral_count_aggregates_correctly` | Counting + summing savings across referrals returns correct totals |
| `test_audit_without_referrer_has_blank_slug` | Default empty string when no referral attribution provided |

---

## Total: 23 tests (14 engine + 6 benchmark + 3 referrals), zero I/O on engine/benchmark; referrals use Django test DB

Run them yourself:

```bash
pytest audits/tests/ -v
```

Expected output: `23 passed in ~0.08s`.
