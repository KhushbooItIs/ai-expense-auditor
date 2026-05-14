# OverpaidAI — Free AI Spend Auditor

OverpaidAI is a free tool that audits a startup's AI tool spend in ~60 seconds — no login, no fluff. Founders and engineering managers enter their tools, plans, and seat counts; a pure-Python engine generates every plausible alternative and picks the cheapest valid one with defensible reasoning; high-savings audits are routed to a Credex consultation.

**Live:** https://ai-expense-auditor-kos7.onrender.com

---

## Screenshots

| Step | What it shows |
|---|---|
| ![Form](docs/screenshots/01-form.png) | **Form** — add tools, plans, seats; localStorage persistence; ~6 Alpine.js interactions |
| ![Result hero](docs/screenshots/02-result-hero.png) | **Result hero** — monthly + annual savings, per-person benchmark vs typical range |
| ![Findings](docs/screenshots/03-findings.png) | **Per-tool breakdown** — every recommendation traces to an official pricing page |
| ![Share view](docs/screenshots/04-share.png) | **Share view** — PII-stripped public URL with OG meta for Slack/Twitter unfurls |

> Drop PNGs into `docs/screenshots/` with the filenames above. A 30-second Loom is also welcome — paste the link under this table.

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
pytest audits/tests/    # 18 tests: 12 engine + 6 benchmark
ruff check .            # lint
```

### Rebuild CSS (only when changing templates / Tailwind config)

```bash
npm install --ignore-scripts   # exact-pinned, no postinstall scripts
npx tailwindcss --input static/css/input.css --output static/css/main.css --minify
```

### Deploy to Render

1. Push to a public GitHub repo
2. Render dashboard → **New → Blueprint** → connect repo (auto-detects `render.yaml`)
3. Set two secrets in **Environment**: `OPENAI_API_KEY`, `RESEND_API_KEY`
4. Build command runs `migrate` + `collectstatic` + `seed_pricing` automatically

Free tier note: the web service sleeps after 15 min idle; first request after sleep takes ~30s.

---

## Decisions

### 1. Django over Next.js / React
Django server-renders the result page, which means Open Graph meta tags are in the HTML on first load — no SSR config, no hydration bugs. The result page is the viral artifact; it had to work perfectly with link unfurlers. The trade-off: no TypeScript, heavier backend. Justified because the form and result page have ~6 dynamic behaviours total — Alpine.js handles them as vanilla JavaScript with no build step on the JS side. (CSS is built once via `@tailwindcss/cli`; the output is checked in.)

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
| Frontend | Django templates + Alpine.js (vanilla JS) + HTMX |
| Styling | Tailwind CSS v4 via `@tailwindcss/cli` (npm, exact-pinned, `--ignore-scripts`) |
| AI summary | OpenAI gpt-4o-mini, templated fallback |
| Email | Resend |
| Hosting | Render (web + Postgres) |
| Anti-abuse | Honeypot + django-ratelimit (5/hr/IP) |
| CI | GitHub Actions — ruff + pytest |

---

## Project structure

```
ai-auditor/
├── audits/
│   ├── engine/          # Pure-Python audit logic — no Django imports
│   │   ├── input.py     # AuditInput, ToolLine dataclasses
│   │   ├── candidate.py # Candidate, Finding, AuditResult dataclasses
│   │   ├── generators.py# Strategy generators (keep_current, downgrade, etc.)
│   │   ├── runner.py    # Main audit() — composite scoring + honesty rails
│   │   └── benchmark.py # Per-person spend vs typical range by use_case
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
├── static/
│   ├── css/
│   │   ├── input.css    # Tailwind v4 entrypoint
│   │   └── main.css     # Built CSS (committed)
│   └── favicon.svg
├── ARCHITECTURE.md
├── PRICING_DATA.md
├── PROMPTS.md
├── LAUNCH_POST.md       # Blog post + Twitter thread (bonus)
├── render.yaml
├── package.json         # @tailwindcss/cli pin
└── requirements.txt
```
