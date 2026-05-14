# Reflection

> Drafts below are starting points. Rewrite each section in your own voice — reviewers can spot AI-written reflections and they're a strong negative signal. Keep the specific numbers, file paths, and technical details; replace the connective tissue with how *you* actually talk.

---

## 1. The hardest bug I hit this week, and how I debugged it

The hardest bug was getting the Render deploy to actually serve a working page. Singular as "a bug," plural in practice — five distinct failures surfaced across five sequential deploys, and every fix exposed the next one.

The first deploy failed with `ModuleNotFoundError: No module named 'app'`. Render was running `gunicorn app:app`, not the `gunicorn overpaidai.wsgi` I had in `render.yaml`. My first hypothesis was that I'd mistyped the start command somewhere. I re-read render.yaml, Procfile, runtime.txt — all correct. Then I noticed the deploy log said Python 3.14, but I'd pinned 3.12.13 in `runtime.txt`. If both `runtime.txt` and `render.yaml` were being ignored, it wasn't a typo — Render was ignoring the entire Blueprint config. That was the real bug: I'd created a plain Web Service in the dashboard, not a Blueprint. They look identical, but only Blueprint deploys read `render.yaml`. I patched the start command directly in the dashboard.

Second deploy: `DisallowedHost: ai-expense-auditor-kos7.onrender.com`. I had hardcoded `ALLOWED_HOSTS=overpaidai.onrender.com` assuming that's what the URL would be. Render assigns a random suffix when there's a name collision and never says so explicitly — the real URL only shows up at the end of the deploy log. Updated `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` to match.

Third through fifth deploys: missing `DATABASE_URL`, missing `SECRET_KEY`, missing `DJANGO_SETTINGS_MODULE`, then a missing `staticfiles/` directory because the build command had never run `collectstatic`. Each one was a different env-var-shaped hole.

What worked was treating the deploy log as a forensic transcript rather than a status feed. Every failure had its answer in the line above the traceback — Python version, hostname, env var name. The real lesson: I'd treated deployment as one step. It's actually six independent contracts (Python version, settings module, allowed hosts, secrets, database URL, static files), and Render fails on each in turn until you satisfy all six.

---

## 2. A decision I reversed mid-week, and what made me reverse it

I reversed my decision on how to build CSS. The first version shipped Tailwind via the standalone CLI binary, gitignored, because I was wary of npm supply chain attacks — recent incidents like xz-utils and event-stream had me worried that a single malicious postinstall script could exfiltrate environment variables before I'd notice anything was wrong.

The standalone binary felt safer: one file, no transitive dependencies, no install scripts. The trade-off was that the binary doesn't go in git (~30 MB), so anyone cloning the repo has to download it manually and the build is harder to reproduce on a new machine.

What changed my mind was actually verifying the threat model instead of treating it as a categorical "npm is unsafe." I checked the npm advisory database for `tailwindcss` and `@tailwindcss/cli` — both clean. I walked the transitive dependency tree (27 packages total) — all from well-known, well-maintained sources. The real attack vector wasn't "is Tailwind itself compromised," it was "does some package's postinstall script run during install." Both of those are mitigable: `--ignore-scripts` blocks all lifecycle hooks, and a committed `package-lock.json` (with SHA-512 integrity hashes for every package) makes any tampering detectable on the next install.

So I switched back to npm — but with three guardrails the original setup didn't have:
1. `npm install --ignore-scripts` to block any postinstall execution
2. Exact version pins in `package.json` (no `^` or `~`)
3. `package-lock.json` committed so `npm ci` fails on any integrity mismatch

`npm audit` reports zero vulnerabilities. The CSS now builds reproducibly anywhere, the binary is out of the repo, and the supply chain risk is actively mitigated rather than just avoided.

The lesson: "I'm avoiding X because of risk Y" is only a valid decision when Y is genuinely unmitigable some other way. Once I actually verified the risk, the avoidance was costing me more friction than the proper mitigations would have.

---

## 3. What I would build in week 2

Three things, in priority order: distribution instrumentation, infra hardening, then org-level features.

**Firebase Analytics + SEO instrumentation.** Right now I have zero visibility into who's using the tool. I'd add Firebase Analytics with custom events for each step of the funnel — form started, tools added, audit completed, share link copied, email captured. Then I'd instrument the result page for SEO: structured data for the savings findings, sitemap.xml, robots.txt, and an OG-meta audit. The goal is to make queries like "cursor vs copilot 2025 cost" land on a personalised audit page rather than a static comparison article. Without instrumentation I'm guessing about what works; without SEO the tool is invisible.

**Cloudflare in front of Render.** The free Render tier sleeps after 15 minutes idle, so the first request after sleep takes ~30 seconds. Cloudflare's edge caching would serve the form page from the edge so cold starts only affect actual audit submissions. It also handles DDoS protection and a free SSL cert — both things I'd want in place before any real launch. This is one afternoon of work for a massive UX win.

**Org-level dashboard.** The current product is a one-shot audit. The real value is recurring — vendors change pricing, teams add seats, new tools enter the stack. I'd build multi-user accounts with role-based access, audit history with a savings-over-time graph, cost-anomaly alerts ("your Cursor spend jumped 40% this month"), a Stripe / Brex billing import so users don't have to retype their stack, and a monthly Slack digest into #engineering. This is where the SaaS lives.

The first two are what make the one-shot tool findable and survivable under load. The third is what makes a user come back next month instead of running one audit and forgetting the URL.

---

## 4. How I used AI tools

*(Pick which AI moment to highlight — see questions below. Then rewrite in your own voice.)*

For most of the build I worked with Claude Code (Anthropic's CLI agent) as a pair programmer. Tasks I delegated heavily: Django scaffolding (models, views, URL routing), the audit engine's strategy-comparison structure, deployment debugging (Render env-var cascade, ALLOWED_HOSTS), test scaffolding, documentation files, and the LLM prompt for the result-page summary.

What I didn't trust the AI with:
- **Pricing data.** Every number in `seed_pricing.py` and `PRICING_DATA.md` I verified against the vendor's official pricing page myself. AI-generated pricing tables drift — the model's training data is months stale and it confidently fabricates plausible numbers. I double-checked all 28 plans against live pages on 2026-05-13.
- **Product / brand decisions.** The tone of the result page, the framing of the email gate, the GTM specifics — those needed my judgement, not training-data averages.

**One specific time the AI was wrong and I caught it:**

When I was wiring up localStorage persistence on the audit form, the AI suggested using Alpine.js's `$persist` plugin — clean, idiomatic, two lines of code. I added the plugin script, wrapped my reactive state with `$persist(...)`, and the form silently broke. Nothing rendered. No console error at first glance.

The first symptom I noticed was "Add another tool" doing nothing on click. Then I opened the console and saw `Alpine Expression Error: addTool is not defined`. That was misleading — `addTool` was defined fine; the whole `auditForm()` component had failed to initialise, so none of its methods were on the scope.

The actual issue: `$persist` is only available inside Alpine *template expressions* (HTML attributes like `x-data="..."`), not inside the plain JS function `auditForm()` that returns the data object. When my `auditForm()` ran during component construction, it called `$persist` against `undefined` and threw — silently, because Alpine swallows the error and just doesn't mount the component.

The AI suggestion was wrong in a particular way: the plugin exists, the syntax was valid, and the example was internally consistent — it just violated Alpine's runtime contract for *where* the directive is allowed. That's the kind of mistake I have to catch manually, because the AI can't observe what didn't get mounted.

The fix was straightforward once I understood it: drop the plugin entirely, read from `localStorage.getItem(...)` directly during init, and use `$watch` to persist changes back on every state mutation. Six lines instead of two, but it actually works and has no hidden runtime dependency.

---

## 5. Self-ratings

*(Pick a number from the suggested range, or override entirely. Rewrite the reason in your own words.)*

- **Discipline: __/10** *(suggested range 7–9)* — Shipped MVP, deployed, all required docs, CI green, and bonus features (benchmark mode, launch copy) inside the week. Where I lost points: deploy debugging burned a half-day I could have planned around.

- **Code quality: __/10** *(suggested range 8–9)* — Pure-Python engine with full type annotations, dataclasses, 18 tests, ruff clean, separation between engine / services / models is strict. Where I'd push: more integration tests around the views and the lead-capture flow.

- **Design sense: __/10** *(suggested range 6–8)* — Brand-consistent dark + orange gradient palette, accessible form (ARIA labels, fieldset/legend, dynamic id/for pairs), OG meta tags for shareability. Where it's weakest: no truly delightful detail or animation — it's functional more than memorable.

- **Problem solving: __/10** *(suggested range 8–9)* — Debugged the Render env-var cascade methodically by reading each log line. Caught the engine's "cheapest-wins ignores migration friction" issue mid-week and reversed to composite scoring with a worked example. Reversed the npm-vs-binary decision after actually verifying the threat model.

- **Entrepreneurial thinking: __/10** *(suggested range 7–9)* — GTM names a specific target user, specific Reddit / Slack / Discord channels, a week-by-week $0 plan, and a real unfair distribution channel (Credex's existing customer list). Economics traces every dollar. Where it's weakest: zero validation interviews this week — those are still in the "to do" column.
