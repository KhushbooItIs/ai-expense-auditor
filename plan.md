# OverpaidAI — Build Plan

## Context

OverpaidAI is a free public AI-spend audit tool, lead-gen funnel for Credex, screenshot-shareable. Cold visitor → fills form → instant audit → email gate for the report → high-savings cases routed to Credex consult.

Three audiences must all be served by the same artifact: the user (genuinely helped or the tool is dishonest), Credex (qualified leads), and social media (must want to screenshot). The audit math must be defensible to a finance reviewer; AI is used only for the friendly summary paragraph, never for savings math.

## Stack

- **Backend:** Django 5.x, Python 3.12, Postgres 15
- **Frontend:** Django templates + Tailwind CSS + HTMX + Alpine.js (no Node toolchain)
- **LLM:** OpenAI `gpt-4o-mini` (summary only); templated fallback when API fails
- **Email:** Resend (transactional)
- **Hosting:** Render (managed web service + Postgres)
- **Anti-abuse:** honeypot field + django-ratelimit (5/hr/IP)

## Repo layout

```
overpaidai/
├── manage.py
├── requirements.txt
├── Procfile
├── render.yaml
├── PRICING_DATA.md          # every plan, every source URL, every last_verified date
├── PROMPTS.md               # full LLM prompt + system message
├── plan.md
├── architecture.md
├── overpaidai/              # Django project settings
├── audits/
│   ├── engine/              # pure-Python rules engine, no Django imports
│   ├── services/            # summary.py (OpenAI integration)
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── templates/
├── leads/                   # email capture, transactional email
├── pricing/
│   ├── data/                # JSON files, one per vendor
│   └── loader.py
├── templates/               # base layout, shared partials
└── tests/
```

## 7-day sprint

### Day 1 — Foundation
- Django project skeleton; apps `audits`, `leads`, `pricing`
- Postgres locally; settings split via env vars (dev/prod)
- Tailwind via django-tailwind; base layout template; HTMX + Alpine via CDN
- pytest + ruff + mypy configured
- Render-ready: `Procfile`, `render.yaml`, `requirements.txt`, `runtime.txt`

### Day 2 — Pricing data & models
- `pricing/data/*.json` for all 8 vendors (Cursor, Copilot, Claude, ChatGPT, Anthropic API, OpenAI API, Gemini, Windsurf)
- `pricing/loader.py` — load + schema-validate at startup
- `PRICING_DATA.md` — table of every plan with source URL + `last_verified` date
- Models: `Audit` (slug, input_json, result_json, created_at) and `Lead` (email, company, role, team_size, audit FK)
- Initial migration

### Day 3 — Engine
- `audits/engine/input.py` — `AuditInput`, `ToolLine` dataclasses
- `audits/engine/candidate.py` — `Candidate`, `Finding` dataclasses
- `audits/engine/generators/` — `keep_current`, `downgrade_within_vendor`, `rightsize_seats`, `switch_to_alternative`, `surface_credex`
- `audits/engine/runner.py` — `audit(input, pricing)` main entry
- `audits/engine/use_case_fit.py` — static capability matrix (coding/writing/data/research/mixed × tool.plan → score 1-5)
- `audits/engine/honesty.py` — final-check rails (80% cap, $5 threshold, never-exceed-current assertion)
- Unit tests: ~30 cases covering happy path, edge cases (zero spend, free tier, all-optimal, massive overspend), and honesty rails

### Day 4 — Form
- Form template: 8 tool rows (one per supported vendor) with plan dropdown + spend + seats; team_size + use_case at the bottom
- Alpine.js handles add/remove dynamic rows + `Alpine.persist` for localStorage state
- Hidden honeypot field
- View: validate form → run engine → save `Audit` (with slug) → redirect to result page
- The audit runs *before* email is captured

### Day 5 — Result page & share
- Result template:
  - Hero: total monthly + annual savings (huge type)
  - Per-tool table: current → recommended → savings + 1-sentence reason
  - Routed CTA: high_savings → Credex consult, optimal → "notify me", normal → email gate for full report
- Tailwind pass: receipt-style design, dense info, screenshot-ready
- Public share view `/a/<slug>/`: same template, but reads `Audit.result_json` only (never joins to `Lead`)
- Open Graph tags: `og:title`, `og:description`, `og:image` (auto-generated savings card via Pillow or static template), Twitter `summary_large_image`

### Day 6 — AI summary, email, anti-abuse
- `audits/services/summary.py` — OpenAI client; prompt takes structured `AuditResult`, returns ~100 word paragraph; templated fallback on any exception or timeout (3s)
- `PROMPTS.md` — full prompt with system message, examples, structured output expectations
- Email gate: modal/section after results, captures email + optional company/role; saves `Lead`
- Resend integration: transactional email confirming the audit, Credex outreach note for high-savings cases
- `django-ratelimit` decorator on the form submit view (5/hr/IP)

### Day 7 — Deploy & polish
- Render deploy: env vars (`OPENAI_API_KEY`, `RESEND_API_KEY`, `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`), Postgres wired
- Domain configured (e.g. `overpaid.ai` or fallback)
- Manual end-to-end smoke (see Verification below)
- Performance check: audit submit → result render < 2s; AI summary streamed or cached so result page never blocks on it
- OG preview validators: Twitter Card Validator, opengraph.xyz, LinkedIn Post Inspector
- Visual polish pass on result page; lock the screenshot

## Verification

End-to-end checks (run manually before declaring done):

1. **Happy path** — Cursor Business 2 seats $80, coding → result shows ~$42/mo Copilot Business recommendation
2. **Optimal path** — single user on Cursor Pro $20, coding → "you're spending well", "notify me" CTA, no manufactured savings
3. **High-savings path** — multi-tool stack totalling $1500+/mo with detected waste → Credex CTA prominent at top of result page
4. **Form persistence** — fill form partially, reload page → fields restored from localStorage
5. **PII strip** — `/a/<slug>/` in incognito browser → no email/company anywhere on page or in source
6. **OG previews** — Twitter Card Validator + Slack unfurl + LinkedIn Post Inspector all show correct title/description/image
7. **AI failure path** — set bogus `OPENAI_API_KEY` → result page still ships with templated summary
8. **Rate limit** — submit form 6 times within an hour from one IP → 6th returns 429
9. **Honeypot** — submit form with hidden field filled → silently rejected, no Audit row written
10. **Engine tests** — `pytest audits/engine/` → 100% pass on rule paths
11. **Email** — high-savings audit → confirmation email lands in inbox within 30s

## Out of scope for v1

- API-vs-subscription recommendations (needs explicit token-volume input; deferring)
- Credex as a per-tool recommendation (meta-CTA only in v1)
- hCaptcha (honeypot + rate limit sufficient for a launch)
- User accounts / saved audit history (no login by design)
- Multi-currency (USD only)
- Audit re-run with updated pricing (each audit is a snapshot)
- Embedded screenshot generator (use static OG image template; dynamic OG card is a v2)
- Per-tool deep dives (e.g., contract negotiation tips)
