# OverpaidAI — Pricing Data Sources

All prices in USD/month. Verified: 2026-05-10.
**These must be re-verified before each production deploy.**

| Vendor | Plan | Price | Type | Min Seats | Source URL |
|---|---|---|---|---|---|
| Cursor | Hobby | $0 | flat | 1 | https://cursor.com/pricing |
| Cursor | Pro | $20/seat | per-seat | 1 | https://cursor.com/pricing |
| Cursor | Business | $40/seat | per-seat | 1 | https://cursor.com/pricing |
| GitHub Copilot | Individual | $10 | flat | 1 | https://github.com/features/copilot |
| GitHub Copilot | Business | $19/seat | per-seat | 1 | https://github.com/features/copilot |
| GitHub Copilot | Enterprise | $39/seat | per-seat | 1 | https://github.com/features/copilot |
| Claude | Free | $0 | flat | 1 | https://claude.ai/upgrade |
| Claude | Pro | $20 | flat | 1 | https://claude.ai/upgrade |
| Claude | Max | $100 | flat | 1 | https://claude.ai/upgrade |
| Claude | Team | $30/seat | per-seat | 5 | https://claude.ai/upgrade |
| ChatGPT | Free | $0 | flat | 1 | https://openai.com/chatgpt/pricing |
| ChatGPT | Plus | $20 | flat | 1 | https://openai.com/chatgpt/pricing |
| ChatGPT | Team | $30/seat | per-seat | 2 | https://openai.com/chatgpt/pricing |
| Anthropic API | API | usage-based | — | — | https://www.anthropic.com/pricing |
| OpenAI API | API | usage-based | — | — | https://openai.com/api/pricing |
| Gemini | Free | $0 | flat | 1 | https://gemini.google.com |
| Gemini | Advanced | $19.99 | flat | 1 | https://one.google.com/about/ai-premium |
| Gemini | Business | $30/seat | per-seat | 1 | https://workspace.google.com/products/gemini |
| Windsurf | Free | $0 | flat | 1 | https://windsurf.com/pricing |
| Windsurf | Pro | $15 | flat | 1 | https://windsurf.com/pricing |
| Windsurf | Teams | $30/seat | per-seat | 2 | https://windsurf.com/pricing |

## Notes

- Cursor Business: check if 5-seat minimum is enforced at checkout (some reports say 1-seat purchase is possible)
- Claude Max: verify current price — launched mid-2025, pricing may have changed
- Gemini Business: part of Google Workspace AI add-on; verify per-seat cost
- Enterprise plans (all vendors): `price: contact` — excluded from recommendations for non-Enterprise users
- API tools: user-reported spend; no plan-based recommendation in v1

## Credex-eligible plans
Plans where Credex can source discounted licenses:
- Cursor Business
- GitHub Copilot Enterprise
- Claude Team
- ChatGPT Team

## Re-verification checklist
Before each deploy, open each source URL and confirm price matches the table above.
Update `last_verified` in `seed_pricing.py` and re-run `python manage.py seed_pricing`.
