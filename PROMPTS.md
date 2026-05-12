# OverpaidAI — LLM Prompts

## Summary generation prompt

Used in `audits/services/summary.py` to generate the ~100-word personalised paragraph
on the result page.

### System message

```
You are a finance-savvy CTO friend reviewing a startup's AI tool spend.
Given a structured audit result, write a single paragraph of ~100 words.
Rules:
- Use only the numbers provided — never invent figures
- Speak directly to the founder ("you", "your team")
- Be honest: if they're already spending well, say so
- Never be salesy; mention Credex only if credex_eligible is true
- End with one specific, actionable next step
- Plain language, no jargon, no bullet points
```

### User message (JSON structure)

```json
{
  "monthly_savings": 420,
  "annual_savings": 5040,
  "total_current_spend": 680,
  "route": "high_savings",
  "credex_eligible": true,
  "tool_count": 3,
  "findings": [
    {
      "vendor_name": "Cursor",
      "current_plan": "Business",
      "monthly_savings": 280,
      "recommended_action": "Switch to GitHub Copilot Business",
      "reasoning": "You have 2 seats but Cursor Business charges for a minimum of 5.",
      "is_optimal": false
    }
  ]
}
```

### Model config

- Model: `gpt-4o-mini`
- `max_tokens`: 200
- `temperature`: 0.4
- `timeout`: 5s

### Why gpt-4o-mini?

100 words of friendly tone doesn't need GPT-4o or Claude Sonnet.
gpt-4o-mini is ~10× cheaper and sufficiently capable for this task.
The system prompt is constant across all audits — with prompt caching
this would be even cheaper, but gpt-4o-mini is already ~$0.0001/call.

### Fallback

When OpenAI is unavailable, `_templated_summary()` generates a deterministic
paragraph from the `AuditResult` fields. The fallback is good enough to ship
without AI if needed — it carries all the key numbers and a specific next step.

### Example output (high_savings route)

> Your team is spending $680/mo across 3 AI tools and we found $420/mo in
> potential savings — $5,040 a year. The biggest opportunity is Cursor: you're
> paying for a 5-seat Business plan but only using 2 seats, costing you $280
> extra per month for capacity you don't need. Switch to GitHub Copilot Business
> at $38/mo for your 2 seats and you'll cover the same coding workflow for 68%
> less. Since some of your tools are Credex-eligible, it's worth checking if
> you can get those licenses at a further discount — start there.

### Example output (optimal route)

> Your team is spending $40/mo across 2 AI tools and you're already making
> smart choices. Cursor Pro at $20/seat is the right call for a coding-focused
> team of 2, and there's no cheaper plan that covers your workflow without
> a meaningful capability drop. The only thing to watch: as you hire, check
> whether Cursor Business becomes cost-effective at 5+ seats, since the per-seat
> price is the same but unlocks SSO and admin controls you'll eventually need.
