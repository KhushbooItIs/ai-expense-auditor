# OverpaidAI — Pricing Data Sources

All prices in USD/month. Every number in [seed_pricing.py](pricing/management/commands/seed_pricing.py) traces to one of the lines below.

**All plans verified: 2026-05-13.**

Enterprise plans are listed with "contact sales" floor estimates — exact pricing is negotiated, but the engine uses these floors so it never over-claims savings against a custom contract.

---

## Cursor
- Hobby: $0 (free, 1-seat cap) — https://cursor.com/pricing — verified 2026-05-13
- Pro: $20/user/month — https://cursor.com/pricing — verified 2026-05-13
- Business: $40/user/month (adds SSO, admin, privacy) — https://cursor.com/pricing — verified 2026-05-13
- Enterprise: $50/user/month (estimated floor; contact sales for actual pricing) — https://cursor.com/pricing — verified 2026-05-13

## GitHub Copilot
- Individual: $10/month (1-seat cap) — https://github.com/features/copilot — verified 2026-05-13
- Business: $19/user/month — https://github.com/features/copilot — verified 2026-05-13
- Enterprise: $39/user/month — https://github.com/features/copilot — verified 2026-05-13

## Claude (Anthropic subscriptions)
- Free: $0 (free, 1-seat cap) — https://claude.ai/upgrade — verified 2026-05-13
- Pro: $20/month (1-seat cap) — https://claude.ai/upgrade — verified 2026-05-13
- Max (5x): $100/month (1-seat cap, 5x usage limits of Pro) — https://claude.ai/upgrade — verified 2026-05-13
- Max (20x): $200/month (1-seat cap, 20x usage limits of Pro) — https://claude.ai/upgrade — verified 2026-05-13
- Team: $30/user/month (min 5 seats) — https://claude.ai/upgrade — verified 2026-05-13
- Enterprise: $60/user/month (estimated floor; contact sales) — https://www.anthropic.com/enterprise — verified 2026-05-13
- API (pay-as-you-go): usage-based, user reports own spend — https://www.anthropic.com/pricing — verified 2026-05-13

## ChatGPT (OpenAI subscriptions)
- Free: $0 (free, 1-seat cap) — https://openai.com/chatgpt/pricing — verified 2026-05-13
- Plus: $20/month (1-seat cap) — https://openai.com/chatgpt/pricing — verified 2026-05-13
- Team: $30/user/month (min 2 seats) — https://openai.com/chatgpt/pricing — verified 2026-05-13
- Enterprise: $75/user/month (estimated floor; contact sales) — https://openai.com/chatgpt/pricing — verified 2026-05-13
- API (pay-as-you-go): usage-based, user reports own spend — https://openai.com/api/pricing — verified 2026-05-13

## Anthropic API (direct)
- API (pay-as-you-go): usage-based, user reports own spend — https://www.anthropic.com/pricing — verified 2026-05-13

## OpenAI API (direct)
- API (pay-as-you-go): usage-based, user reports own spend — https://openai.com/api/pricing — verified 2026-05-13

## Gemini (Google)
- Free: $0 (free, 1-seat cap) — https://gemini.google.com — verified 2026-05-13
- Advanced: $19.99/month (1-seat cap, Google One AI Premium) — https://one.google.com/about/ai-premium — verified 2026-05-13
- Business: $30/user/month (Google Workspace add-on) — https://workspace.google.com/products/gemini — verified 2026-05-13
- API (pay-as-you-go): usage-based via Google AI Studio / Vertex — https://ai.google.dev/pricing — verified 2026-05-13

## Windsurf
- Free: $0 (free, 1-seat cap) — https://windsurf.com/pricing — verified 2026-05-13
- Pro: $15/month (1-seat cap) — https://windsurf.com/pricing — verified 2026-05-13
- Teams: $30/user/month (min 2 seats) — https://windsurf.com/pricing — verified 2026-05-13

---

## Per-person benchmark ranges

Used by [audits/engine/benchmark.py](audits/engine/benchmark.py) to surface "your team spends $X/person vs typical $Y" on the result page. Ranges are derived from the prices above plus realistic stack assumptions (one IDE tool + one chat assistant for coding teams; one chat sub for writing/research teams).

| Use case | Low $/person | Median $/person | High $/person | Stack assumption |
|---|---|---|---|---|
| coding | 50 | 90 | 150 | Copilot/Cursor + Claude/ChatGPT |
| writing | 20 | 35 | 60 | one chat sub |
| data | 30 | 55 | 90 | ChatGPT Plus (Code Interpreter) + chat |
| research | 20 | 40 | 70 | Claude Pro or ChatGPT Plus |
| mixed | 30 | 60 | 100 | one chat + one work tool |

Teams >5 get a small volume factor (0.85–0.95) reflecting team plans replacing individual subs.

---

## Credex-eligible plans
Plans where Credex can source discounted licenses (`credex_eligible=True` in seed):

- Cursor Business, Cursor Enterprise
- GitHub Copilot Enterprise
- Claude Team, Claude Enterprise
- ChatGPT Team, ChatGPT Enterprise

---

## Re-verification checklist
Before each production deploy:

1. Open each source URL above in a browser
2. Confirm price matches what's listed here
3. Update the verified date on any line that changed
4. Update `TODAY = datetime.date(YYYY, M, D)` in [seed_pricing.py](pricing/management/commands/seed_pricing.py)
5. Re-run `python manage.py seed_pricing` (locally and on Render)

## Caveats and notes

- **Enterprise plans** (Cursor, Claude, ChatGPT): exact pricing is negotiated and not publicly listed. The numbers above are conservative *floor* estimates so the engine never over-claims savings vs a custom enterprise contract. Real pricing is typically equal or higher.
- **Claude Max** has two SKUs (5x and 20x usage). Both are 1-seat consumer plans.
- **Gemini Advanced** is the consumer-facing Google One AI Premium tier (uses the Gemini Ultra model).
- **API plans** are pay-as-you-go — there is no fixed monthly cost. The engine uses user-reported spend as the baseline and won't recommend "switch to API at $0/mo" (filtered out via `_USAGE_BASED_PLAN_KEYS` in [generators.py](audits/engine/generators.py)).
