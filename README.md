# OverpaidAI — Free AI Spend Auditor

OverpaidAI is a free tool that audits a startup's AI tool spend in 60 seconds — no login, no fluff. Founders and engineering managers enter their tools, plans, and seat counts; the engine computes defensible savings recommendations; and high-savings cases are routed to a Credex consultation.

**Live:** https://cruxified.com

---

## Screenshots

> _Add 3+ screenshots or a 30-second Loom/YouTube recording here once deployed._

1. Form — enter your tools and plans
2. Result page — savings hero + per-tool breakdown
3. Share URL — screenshot-ready, OG preview for Twitter/Slack

---

## Quick Start

### Requirements
- Python 3.12
- Git

### Run locally

```bash
git clone <repo-url>
cd ai-auditor

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

cp .env.example .env
# Fill in OPENAI_API_KEY and RESEND_API_KEY in .env

python manage.py migrate
python manage.py seed_pricing
python manage.py runserver
```

Open http://localhost:8000

### Run tests

```bash
pytest audits/tests/
```

### Deploy to Render

1. Push to a public GitHub repo
2. Connect repo in Render dashboard → **New Blueprint** (auto-detects `render.yaml`)
3. Set env vars in Render dashboard: `OPENAI_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `SITE_URL`
4. First deploy runs `migrate` and `collectstatic` automatically

---

## Decisions

### 1. Django over Next.js / React
Django server-renders the result page, which means Open Graph meta tags are in the HTML on first load — no SSR config, no hydration bugs. The result page is the viral artifact; it had to work perfectly with link unfurlers. The trade-off: no TypeScript, heavier backend. Justified because the form and result page have minimal interactivity — Alpine.js handles the ~6 dynamic behaviours without a build step.

### 2. Pure-Python audit engine with no AI in the math
The engine is a strategy comparison: generate every plausible alternative, pick the cheapest valid one, compute savings. Zero LLM calls. A finance reviewer can trace every number to a pricing page URL. The trade-off: manual maintenance of pricing data. Accepted because accuracy matters more than automation here — wrong savings claims destroy trust.

### 3. Pricing data in Postgres (not JSON files)
Pricing is stored in `VendorPlan` and `ToolFitScore` tables, seeded via `seed_pricing` management command. The trade-off: requires a DB seeding step. Benefit: editable via Django admin without a code deploy, auditable via migrations, cache-invalidatable at runtime.

### 4. Email captured after audit, not before
The tool shows the full audit result before asking for an email. This is intentional — the value is shown first so the email ask feels like "get a copy" rather than "pay to see." The trade-off: lower email capture rate from users who leave immediately. Accepted because the assignment explicitly required it and it's also just the right product decision.

### 5. Honeypot + rate limit instead of hCaptcha
A hidden `website` field catches bots; `django-ratelimit` (5 POSTs/hr/IP) prevents scraping. No visible CAPTCHA means zero friction for real users. The trade-off: a determined attacker could work around rate limits. Accepted for launch — the audit compute cost is negligible and the DB rows are cheap. hCaptcha is a v2 option if abuse materialises.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | Django 5.1, Python 3.12 |
| Database | Postgres 15 (SQLite in dev) |
| Frontend | Django templates + Tailwind CDN + Alpine.js + HTMX |
| AI summary | OpenAI gpt-4o-mini, templated fallback |
| Email | Resend |
| Hosting | Render |
| Anti-abuse | Honeypot + django-ratelimit |

---

## Project structure

```
ai-auditor/
├── audits/
│   ├── engine/          # Pure-Python audit logic — no Django imports
│   │   ├── input.py     # AuditInput, ToolLine dataclasses
│   │   ├── candidate.py # Candidate, Finding, AuditResult dataclasses
│   │   ├── generators.py# Strategy generators (keep_current, downgrade, etc.)
│   │   └── runner.py    # Main audit() entry point + honesty rails
│   ├── services/
│   │   └── summary.py   # OpenAI gpt-4o-mini summary + templated fallback
│   ├── tests/
│   │   └── test_engine.py
│   ├── models.py        # Audit model (slug, input_json, result_json, summary_text)
│   └── views.py
├── leads/
│   ├── models.py        # Lead model (OneToOne → Audit, email, company, role)
│   ├── views.py         # capture_lead JSON endpoint
│   └── services/
│       └── email.py     # Resend / Django console backend
├── pricing/
│   ├── models.py        # VendorPlan, ToolFitScore
│   ├── loader.py        # get_pricing_data() with 5-min cache
│   └── management/
│       └── commands/
│           └── seed_pricing.py
├── templates/
│   ├── base.html
│   └── audits/
│       ├── form.html
│       └── result.html
├── ARCHITECTURE.md
├── PRICING_DATA.md
├── PROMPTS.md
├── render.yaml
└── requirements.txt
```
