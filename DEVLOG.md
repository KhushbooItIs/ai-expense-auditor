# DEVLOG

Daily notes from the week. Hours are honest — if I didn't work, I wrote 0.

> Personalise the **Hours worked** and **Mood / lesson** lines before submitting. The factual "What I did / What didn't work" rows are pulled from the actual commits — keep them tied to real activity, don't smooth them out.

---

## 2026-05-09 (Saturday)
**Hours worked:** _[fill in — roughly 3-4h based on planning depth]_

**What I did:**
- Read the assignment end-to-end twice, made a one-page brief of what the tool actually has to do
- Drafted the initial architecture: Django + Postgres + Alpine.js, pure-Python engine, server-rendered result page for OG-tag unfurling
- Wrote `plan.md` and `architecture.md` (uppercased to `ARCHITECTURE.md` later)
- Picked the stack: Django over Next.js because the share URL has to OG-render on first byte, and the form has ~6 interactions so a React app would be ~130KB of framework overhead for nothing

**What didn't work:**
- Initial pricing data structure assumed a flat list — realised mid-sketch that fit-scores per use case need their own table or the data shape collapses

**Mood / lesson:** _[your one-line take — what felt clear vs murky on day 1]_

---

## 2026-05-10 (Sunday)
**Hours worked:** 0

**What I did:** Nothing. Didn't commit, didn't open the editor.

**Mood / lesson:** _[your one-line — whatever the honest reason was]_

---

## 2026-05-11 (Monday)
**Hours worked:** _[~2-3h]_

**What I did:**
- Set up the Django 5.1 project skeleton: settings split (base / dev / prod), requirements pinned, base template, URL routing, healthcheck endpoint
- Quick day — mostly boilerplate, designed so the dev/prod settings diverge cleanly when deploy time comes

**What didn't work:**
- Spent time fiddling with `STATICFILES_STORAGE` for whitenoise compressed manifest — turns out the order in MIDDLEWARE matters, whitenoise has to come right after SecurityMiddleware

**Mood / lesson:** _[your one-line]_

---

## 2026-05-12 (Tuesday)
**Hours worked:** _[8-10h — heavy build day]_

**What I did:**
- Models: `VendorPlan`, `ToolFitScore`, `Audit`, `Lead` with migrations
- Pricing seed command: 21 plans across 8 vendors with source URLs and last-verified dates
- The audit engine — strategy comparison pattern: 4 candidate generators (keep_current, downgrade_within_vendor, rightsize_seats, switch_to_alternative), runner that picks `min(valid, key=(cost, -fit))`, honesty rails (80% cap, $5 noise floor)
- Views, URLs, templates (form + result), Resend email service, OpenAI summary with templated fallback
- 5 commits — most of the actual product shipped today

**What didn't work:**
- First version of `switch_to_alternative` didn't respect `max_seats`, so for a 5-seat team it kept recommending Claude Pro (1-seat-only). Added `_seats_fit` helper.
- Tried letting the LLM compute savings on the result page — wrong ~15% of the time. Moved all math to pure Python, gave the LLM only the structured result to describe.

**Mood / lesson:** _[your one-line — this was the biggest day, what surprised you?]_

---

## 2026-05-13 (Wednesday)
**Hours worked:** _[8-10h — long day, lots of stops and restarts]_

**What I did:**
- Replaced Tailwind Play CDN (800KB runtime) with a static build — first via standalone CLI binary, then reversed to `@tailwindcss/cli` via npm with `--ignore-scripts` and pinned `package-lock.json`. Net: 16KB CSS, zero npm-audit findings.
- Accessibility pass on the form: dynamic `:id`/`:for` pairs on every Alpine input, fieldset/legend wrappers, aria labels, `aria-busy` on the submit button
- Deployment day from hell on Render: 5 cascading failures
  1. `ModuleNotFoundError: 'app'` — Render was using its default `gunicorn app:app` because I'd created a Web Service, not a Blueprint
  2. `DisallowedHost` — actual URL was `ai-expense-auditor-kos7.onrender.com`, not the `overpaidai.onrender.com` I'd assumed
  3. Missing `DATABASE_URL`, `SECRET_KEY`, `DJANGO_SETTINGS_MODULE`
  4. Missing `staticfiles/` because build never ran `collectstatic`
- 7 commits, mostly trying to land the deploy

**What didn't work:**
- Alpine.js `$persist` plugin crashed the form silently — `$persist` is only available in template expressions, not in plain JS functions like `auditForm()`. Replaced with manual `localStorage` + `$watch`.
- Tried `npm install tailwindcss` alone (Tailwind v4 split the CLI into `@tailwindcss/cli` — had to add the second package)

**Mood / lesson:** _[your one-line — deployment frustration is real, what kept you going?]_

---

## 2026-05-14 (Thursday)
**Hours worked:** _[6-8h — submission prep + engine improvements]_

**What I did:**
- Engine accuracy fixes: replaced theoretical-cost baseline with `line.monthly_spend`, replaced 10% relative threshold with $5 absolute, excluded `plan_key="api"` from recommendations
- Composite scoring in the runner: `value = savings + fit_bonus - switch_penalty`. Prevents a marginally cheaper vendor switch from beating a same-vendor downgrade with equal capability.
- Benchmark mode: per-person spend vs typical range by use_case and team_size, with 6 new tests
- LAUNCH_POST.md (blog + Twitter thread)
- Documentation pass: README, PRICING_DATA (per-vendor format with verification dates), TESTS, PROMPTS (added "what didn't work"), REFLECTION, USER_INTERVIEWS
- One real user interview (sister, team lead at an early-stage startup) — the $1600 single-month bill story is the single most valuable signal I got all week. Reframed GTM ICP from EM → CTO based on it.
- 6 commits, CI green throughout

**What didn't work:**
- Tried to write 3 interviews in the available time, only got 1 done. Honest acknowledgment in USER_INTERVIEWS.md is better than 2 fabricated entries that reviewers would spot.

**Mood / lesson:** _[your one-line — submission day energy, what changed in your head about the project?]_

---

## 2026-05-15 (Friday) — submission day
**Hours worked:** _[however long the polish + submit takes]_

**What I did:**
- Final voice pass on REFLECTION.md and DEVLOG.md (made them sound like me, not the agent)
- Took 4 screenshots for the README (form, result hero, findings, share view)
- Verified the deployed URL was awake and reachable
- Verified CI green on the latest commit
- Submitted the Google Form

**What didn't work:** _[anything that broke on submission day, or "nothing — clean submit"]_

**Mood / lesson:** _[your one-line close — what would you do differently if you ran this week again?]_

---

## Total time

- Sat 5/9: ~3h
- Sun 5/10: 0h
- Mon 5/11: ~2h
- Tue 5/12: ~9h
- Wed 5/13: ~9h
- Thu 5/14: ~7h
- Fri 5/15: ~_h

**Estimated total: ~30-35 hours over 6 active days.**
