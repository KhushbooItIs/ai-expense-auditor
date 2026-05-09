# OverpaidAI — Architecture

## System overview

```
[Browser]
  │  (1) GET /
  ▼
[Django: form view] ──► template renders form (HTMX + Alpine, localStorage persist)
  │
  │  (2) POST /audit (form submit, honeypot + ratelimit guards)
  ▼
[audits.views.run_audit]
  │
  ├─► audits.engine.runner.audit(input, pricing)   ◄── pure Python, no Django
  │     ├── generators per tool → Candidates
  │     ├── pick best valid Candidate per tool
  │     ├── apply honesty rails
  │     └── return AuditResult dataclass
  │
  ├─► audits.services.summary.generate(audit_result)
  │     ├── try OpenAI gpt-4o-mini (3s timeout)
  │     └── fallback: templated paragraph
  │
  ├─► save Audit row (slug, input_json, result_json, summary_text)
  │
  └─► redirect to /a/<slug>/
       │
       ▼
[audits.views.share] ──► template renders result page (OG meta in <head>)
       │
       ├─ email gate (HTMX POST)
       │   └─► leads.views.capture → save Lead, send Resend email
       │
       └─ Credex CTA (link out, no auth)
```

## Tech stack rationale

| Layer | Choice | Why |
|---|---|---|
| Web framework | Django 5 | Server-rendered templates trivially produce OG tags; ORM for relational data; admin for ops if needed |
| DB | Postgres 15 | Relational shape (Audit ↔ Lead); JSONField for snapshots |
| Frontend interactivity | HTMX + Alpine.js | No Node build; Django-native; sufficient for ~6 form interactions |
| Styling | Tailwind via django-tailwind | Fastest path to a screenshot-worthy result page |
| LLM | OpenAI gpt-4o-mini | User has access; cheap (~$0.0001/audit); fast; capable for 100 words |
| Email | Resend | Cleanest Python SDK, generous free tier |
| Hosting | Render | One-click Django + Postgres; free tier survives a PH launch |
| Anti-abuse | honeypot + django-ratelimit | Zero user friction; sufficient for launch |

## Data model

```python
# audits/models.py
class Audit(models.Model):
    slug = models.CharField(max_length=16, unique=True, db_index=True)
    input_json = models.JSONField()     # the raw AuditInput
    result_json = models.JSONField()    # the AuditResult (findings, totals, route)
    summary_text = models.TextField()   # the AI-generated or fallback paragraph
    created_at = models.DateTimeField(auto_now_add=True)

# leads/models.py
class Lead(models.Model):
    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="lead")
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=100, blank=True)
    team_size = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    consent_credex_outreach = models.BooleanField(default=False)
```

**PII separation by construction**: the share view (`/a/<slug>/`) queries `Audit` only and never joins to `Lead`. The template has no access to email/company. Even a regression in the template can't leak PII because the field isn't on the queryset.

## Audit engine

### Architectural pattern: Strategy comparison

For each tool line item, the engine generates every plausible alternative as a `Candidate`, picks the cheapest valid one, computes savings = current − best. Defensible because we're computing the optimum across alternatives, not pattern-matching a recommendation.

### Dataclasses

```python
@dataclass
class ToolLine:
    vendor: str           # "cursor", "copilot", ...
    plan: str             # "business", "pro", ...
    monthly_spend: Decimal
    seats: int

@dataclass
class AuditInput:
    tools: list[ToolLine]
    team_size: int
    use_case: Literal["coding", "writing", "data", "research", "mixed"]

@dataclass
class Candidate:
    label: str            # "Switch to GitHub Copilot Business"
    monthly_cost: Decimal
    fit_score: int        # 1-5 from use_case_fit matrix
    reasoning: str        # 1-sentence human-readable
    evidence: dict        # named numbers + source URLs
    is_credex_eligible: bool = False

    def is_valid(self, inp: AuditInput) -> bool: ...

@dataclass
class Finding:
    tool: str
    current_plan: str
    current_seats: int
    current_spend: Decimal
    recommended_action: str  # human-readable
    recommended_cost: Decimal
    monthly_savings: Decimal
    reasoning: str
    evidence: dict
    is_optimal: bool = False  # True when current is best

@dataclass
class AuditResult:
    findings: list[Finding]
    monthly_savings: Decimal
    annual_savings: Decimal
    route: Literal["high_savings", "normal", "optimal"]   # >=$500, $100-500, <$100
    credex_eligible: bool
```

### Generators

Each is a pure function `(line, input, pricing) -> list[Candidate]`. Add a generator → engine picks it up via the `CANDIDATE_GENERATORS` registry.

| Generator | Returns |
|---|---|
| `keep_current` | One Candidate matching current line (baseline) |
| `downgrade_within_vendor` | Cheaper plans from same vendor that still cover use case |
| `rightsize_seats` | If on Team plan with seats < team-plan floor → individual plan × N seats |
| `switch_to_alternative` | Different vendors with `fit_score` within 1 of current's score |
| `surface_credex` | If vendor is in Credex sourced set → flag (no per-tool action in v1) |

### Picking the best

```python
valid = [c for c in candidates if c.is_valid(inp)]
best = min(valid, key=lambda c: (c.monthly_cost, -c.fit_score))
```

Cost ascending; ties broken by capability fit. Means on a tie, we prefer the better-fitting tool, not just the cheapest.

### Honesty rails

Run as final checks on each Finding before adding to result:

1. **Cap at 80%** — `monthly_savings = min(monthly_savings, current_spend * 0.8)`
2. **Threshold $5** — if `monthly_savings < $5`, mark `Finding.is_optimal = True`, no recommendation surfaced
3. **Never-exceed assertion** — `assert recommended_cost <= current_spend` (should be impossible by construction, but caught here)
4. **Enterprise plans** — plans with `price: "contact"` are only valid candidates if user is *currently* on a similar tier (we can't know enterprise pricing)

### Aggregation

```python
total = sum(f.monthly_savings for f in findings)
route = (
    "high_savings" if total >= 500
    else "optimal" if total < 100
    else "normal"
)
```

### Performance

- 8 tools × ~7 generators × dict lookups = bounded, ~10ms per audit
- Pricing JSON loaded once at module import; not re-read per audit
- Zero external calls during engine execution
- Engine result is structured input to summary service (the only AI step)

## Pricing data

### File shape

```jsonc
// pricing/data/cursor.json
{
  "vendor": "Cursor",
  "vendor_key": "cursor",
  "source_url": "https://cursor.com/pricing",
  "last_verified": "2026-05-09",
  "plans": {
    "hobby":      {"price_monthly": 0,   "min_seats": 1, "max_seats": 1,  "features": []},
    "pro":        {"price_per_seat": 20, "min_seats": 1, "features": []},
    "business":   {"price_per_seat": 40, "min_seats": 1, "features": ["sso", "admin", "privacy"]},
    "enterprise": {"price": "contact",   "min_seats": 50, "features": ["sso", "admin", "sla"]}
  }
}
```

### Sourcing & verification

- Every plan has `last_verified` matching `PRICING_DATA.md`
- `PRICING_DATA.md` is a markdown table: `vendor | plan | price | source URL | last_verified`
- Implementation step: open every URL, screenshot the price, transcribe, commit
- Loader runs JSON Schema validation at startup → server fails to boot if pricing data is malformed

### Use-case fit matrix (`pricing/use_case_fit.json`)

```jsonc
{
  "coding": {
    "cursor.pro": 5, "cursor.business": 5,
    "copilot.individual": 4, "copilot.business": 4,
    "windsurf.pro": 4,
    "claude.pro": 3, "chatgpt.plus": 3
  },
  "writing": {
    "claude.pro": 5, "claude.team": 5,
    "chatgpt.plus": 4, "chatgpt.team": 4,
    "cursor.pro": 1
  },
  "data": { ... },
  "research": { ... },
  "mixed": { ... }
}
```

Hand-curated. Reviewable in PR diffs. The "within 1 point" tolerance for alternatives is encoded in `switch_to_alternative` generator.

## Frontend

### Form

- Single page, all 8 vendors visible as collapsible rows (default collapsed; user expands the ones they pay for)
- Per-row: plan dropdown, monthly spend (number), seats (number)
- Bottom: team_size + use_case + honeypot
- Alpine.js state stored via `Alpine.persist` to localStorage
- Submit is a regular form POST; HTMX optional for nicer UX (swap form for results) but not required

### Result page

- Server-rendered (Django template)
- Hero block: total monthly savings (huge), annual savings (sub-headline), route-specific CTA
- Per-tool findings table: current → recommended → savings + reason
- Optional collapsed `evidence` block per Finding (for the curious / finance-minded user)
- AI summary paragraph below findings
- Email gate (HTMX modal) for "Get your full report" → captures Lead → triggers email
- Credex CTA on `route == "high_savings"` audits

### Share view (`/a/<slug>/`)

- Same template as result page, with `is_share=True`
- Hides email gate and personalized greetings; PII not loaded
- OG meta in `<head>`:
  - `og:title` = "I'm overpaying $X/mo on AI tools — find out yours"
  - `og:description` = "Free audit. Tells you where you're overspending. No login."
  - `og:image` = static or templated PNG with the savings hero (v1: static; v2: dynamic)
  - Twitter `card: summary_large_image`

## API surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Marketing + form |
| POST | `/audit/` | Submit form, run engine, save Audit, redirect to result |
| GET | `/r/<slug>/` | Owner's result view (immediately after submit; same shape as share) |
| GET | `/a/<slug>/` | Public share view (PII-stripped, OG meta) |
| POST | `/leads/capture/` | HTMX endpoint: save Lead from email gate, send confirmation email |
| GET | `/healthz/` | Render health check |

Note: `/r/<slug>/` vs `/a/<slug>/` is the same template but different views — `/r/` is the immediate post-submit experience (with email gate), `/a/` is the canonical share URL (no email gate, no PII access). Same Audit record, two views.

## AI summary integration

### Service: `audits/services/summary.py`

```python
def generate(result: AuditResult, *, timeout_s: int = 3) -> str:
    try:
        return _openai_call(result, timeout_s=timeout_s)
    except Exception as e:
        logger.warning("summary fallback used: %s", e)
        return _templated_fallback(result)
```

### Prompt design (full version in `PROMPTS.md`)

- **System:** "You are a finance-savvy CTO friend. Read the structured audit and write a ~100-word paragraph telling the founder what's going on, in plain language. Don't invent numbers; use only the numbers in the audit. Don't be salesy. End with one specific next step."
- **User:** JSON-serialized `AuditResult` (findings, totals, route)
- **Constraints:** `max_tokens=200`, `temperature=0.4`, `timeout=3s`
- **Cost:** ~150 input + ~120 output tokens with cached system prompt = ~$0.0001/audit on gpt-4o-mini

### Templated fallback

When OpenAI fails, return a deterministic paragraph composed from `AuditResult` fields:

> "Your audit looked at {N} tools totaling ${current}/mo. We found {M} opportunities to save ${monthly}/mo (${annual}/year). The biggest is {top_finding.recommended_action}. {route_specific_sentence}."

The fallback is good enough that we'd ship without AI if needed.

## Anti-abuse

### Honeypot
Hidden field `email_address_confirm` with CSS `display:none` and `tabindex=-1`. Bots fill it; humans don't. If filled, return 200 (no leak that we detected) but don't write Audit.

### Rate limit
`@ratelimit(key='ip', rate='5/h', method='POST', block=True)` on `/audit/` view. 6th submit returns 429.

### CSRF
Default Django CSRF middleware on form POST.

## Email (Resend)

### Confirmation email
Triggered when Lead is captured. Plain HTML, branded, includes:
- Audit summary (savings hero)
- Link to share URL
- For `route == "high_savings"`: "A Credex specialist will reach out shortly about claiming these savings via discounted credits."

### Implementation
- `leads/services/email.py` wraps Resend Python SDK
- Templates in `leads/templates/emails/`
- Failure is logged, not surfaced to user (the Lead is already saved)

## Deployment (Render)

### `render.yaml`
```yaml
services:
  - type: web
    name: overpaidai
    env: python
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn overpaidai.wsgi"
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: overpaidai-db, property: connectionString }
      - key: OPENAI_API_KEY
        sync: false
      - key: RESEND_API_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: overpaid.ai

databases:
  - name: overpaidai-db
    plan: free
```

## Cost & performance

| Item | Per-audit cost |
|---|---|
| Engine math | 0 tokens, ~10ms |
| OpenAI summary (gpt-4o-mini, cached system prompt) | ~$0.0001 |
| Postgres writes | 1 INSERT (Audit) on submit, 1 INSERT (Lead) on email gate |
| Resend send | $0 (free tier covers ~3000/mo) |
| **Total marginal cost per completed audit** | **< $0.001** |

Latency budget for the form-submit → result-page transition:
- Form validation + engine: ~50ms
- DB insert: ~30ms
- OpenAI summary: ~1-2s (this dominates)
- Render: ~30ms

To keep the result page snappy, the AI summary is generated *after* the audit is saved, and either:
- (a) Streamed to the page via HTMX/SSE while the user reads the per-tool findings
- (b) Kicked off async (e.g., Django background task) and rendered when ready, with a skeleton loader

v1 implementation: synchronous with 3s timeout — ships faster, slightly worse UX. Upgrade to (a) on day 7 if time permits.

## Out of scope (v2)

- API-vs-subscription rule (needs token-volume input)
- Credex per-tool recommendations (meta-CTA only in v1)
- Dynamic OG card generation (static template in v1)
- hCaptcha
- User accounts, saved audits
- Multi-currency
- Audit re-run with updated pricing
- Programmatic pricing-data refresh (manual + dated for v1)
