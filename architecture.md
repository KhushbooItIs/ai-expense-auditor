# OverpaidAI — Architecture

## System diagram

```mermaid
flowchart TD
    A[Browser] -->|GET /| B[form view]
    B --> C[form.html\nAlpine.js + localStorage]
    C -->|POST /audit/| D{honeypot\n+ ratelimit}
    D -->|bot / exceeded| E[redirect /]
    D -->|valid| F[run_audit view]
    F --> G[audit engine\npure Python]
    G --> H[get_pricing_data\n5-min cache]
    H --> I[(Postgres\nVendorPlan\nToolFitScore)]
    G --> J[AuditResult dataclass]
    J --> K[generate_summary\nOpenAI gpt-4o-mini]
    K -->|API fail| L[templated fallback]
    K --> M[summary_text]
    L --> M
    J --> N[Audit.objects.create\nslug + result_json]
    M --> N
    N --> O[redirect /r/slug/]
    O --> P[result.html\nsavings hero + findings]
    P -->|email submit| Q[/leads/capture/]
    Q --> R[(Lead row\nemail + audit FK)]
    R --> S[Resend email]
    P -->|share link| T[/a/slug/\nPII-free public view\nOG meta tags]
```

## Data flow: input → audit result

1. **Form submit** — Browser POSTs `tools[N][vendor_key]`, `tools[N][plan_key]`, `tools[N][monthly_spend]`, `tools[N][seats]`, `team_size`, `use_case`
2. **Parse** — `_parse_tools()` walks indexed POST keys into `list[ToolLine]` dataclasses
3. **Pricing load** — `get_pricing_data()` returns in-memory dict from Django cache (populated from Postgres, TTL 5 min)
4. **Engine** — For each `ToolLine`, four generators produce `Candidate` objects; runner picks `min(valid, key=(cost, -fit_score))`; honesty rails cap savings at 80% and suppress findings < $5/mo
5. **Routing** — `total_savings ≥ $500` → `high_savings`; any real saving → `normal`; all optimal → `optimal`
6. **Summary** — `AuditResult` JSON sent to `gpt-4o-mini` (5s timeout); falls back to deterministic template on any exception
7. **Persist** — `Audit` row written with `slug`, `input_json`, `result_json`, `summary_text`
8. **Redirect** — user lands on `/r/<slug>/` (owner view with email gate)
9. **Share** — `/a/<slug>/` queries `Audit` only; structurally cannot expose `Lead` PII

## Stack rationale

| Layer | Choice | Why |
|---|---|---|
| Web framework | Django 5.1 | Server-rendered HTML means OG meta tags are present on first HTTP response — no SSR complexity. ORM + admin for ops. |
| Database | Postgres 15 (SQLite in dev) | Relational shape fits Audit ↔ Lead. JSONField stores audit snapshots without schema churn. |
| Frontend | Django templates + Tailwind CDN + Alpine.js | No Node build step. Alpine covers ~6 interactions (dynamic tool rows, email submit, copy link). |
| Language | Python 3.12 | Dataclasses + type hints make the engine readable and testable. |
| LLM | OpenAI gpt-4o-mini | ~$0.0001/audit. Fast (~1s). Anthropic preferred by assignment but OpenAI key was available; prompt is model-agnostic. |
| Email | Resend | Clean Python SDK. `overpaid@cruxified.com` sender via verified domain. |
| Hosting | Render | `render.yaml` Blueprint auto-provisions web service + Postgres. |
| Anti-abuse | Honeypot + django-ratelimit | Zero user friction. Honeypot silently drops bot submissions. Rate limit (5/hr/IP) prevents scraping. |

## Audit engine — strategy comparison pattern

The engine never pattern-matches a recommendation. Instead it generates every plausible alternative as a `Candidate` and picks the cheapest valid one. This produces defensible output: the recommendation is provably the cheapest option that fits the team's use case and seat count.

### Generators (`audits/engine/generators.py`)

| Generator | What it returns |
|---|---|
| `keep_current` | Baseline — current plan at current cost |
| `downgrade_within_vendor` | Cheaper plans, same vendor, fit_score within 1 point |
| `rightsize_seats` | If seats < plan min_seats floor, find plan matching actual seats |
| `switch_to_alternative` | Different vendor, fit_score within 1, >10% cheaper |
| `surface_credex` | Flags Credex-eligible plans (no per-tool CTA in v1) |

### Selection (`audits/engine/runner.py`)

```python
valid = [c for c in candidates if c.is_valid(inp)]
best = min(valid, key=lambda c: (c.monthly_cost, -c.fit_score))
```

Cost-ascending; ties broken by fit score.

### Honesty rails

1. **80% cap** — savings capped at 80% of current spend
2. **$5 threshold** — savings < $5/mo → `is_optimal=True`, no recommendation shown
3. **max_seats guard** — plans with `max_seats` excluded if team exceeds limit

## What changes at 10k audits/day

| Concern | Current | At 10k/day |
|---|---|---|
| Engine compute | 10ms, in-process | Still fine — pure Python, no I/O |
| Pricing cache | 5-min Django LocMem | Switch to Redis; LocMem doesn't share across workers |
| OpenAI summary | Synchronous, 5s timeout | Async Celery task; result page renders immediately, summary loads via HTMX poll |
| DB writes | 1 INSERT/audit | Postgres handles this; add read replica for analytics queries |
| Rate limiting | Cache-backed per-process | Redis backend so counters are shared across workers |
| Render free tier | Single worker | Upgrade to Starter ($7/mo); 2-3 Gunicorn workers |
