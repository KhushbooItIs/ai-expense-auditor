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

---

## What didn't work

Five iterations that got tried and rejected before landing on the prompt above:

### 1. Letting the LLM compute savings
**Tried:** Pass the raw form input to the LLM and ask it to "compute total monthly savings and explain why." Sounded elegant — one call, no engine code.

**Failed because:** gpt-4o-mini was wrong on ~15% of audits. It would, for example, double-count seat-based plans or miss `min_seats` floors. Worse, the wrong number sounded confident in the summary, so a finance reviewer couldn't tell when it was off.

**Fix:** Moved all math to the pure-Python engine. The LLM only gets the computed `AuditResult` JSON. It can only describe numbers that are already correct.

### 2. Temperature 0.7
**Tried:** Default OpenAI temperature.

**Failed because:** Output became verbose, padded with hedging ("you might want to consider possibly..."), and the same prompt produced wildly different summaries between runs — bad for a tool that gets screenshotted.

**Fix:** Dropped to `temperature=0.4`. Less padding, more deterministic, still reads natural enough.

### 3. Free-text input in the user message
**Tried:** "Here's the audit result: the user spends $680/mo across 3 tools, can save $420..." formatted as prose.

**Failed because:** The model occasionally hallucinated extra findings (mentioning a tool that wasn't in the audit) or rounded numbers differently than the result page. Whatever pattern it had seen in training leaked into the output.

**Fix:** Forced the user message to be the literal JSON of `AuditResult` — the model now sees the same structured numbers the page renders, with no prose around them.

### 4. Allowing bullet points and headings
**Tried:** Initial system prompt let the model use markdown for structure.

**Failed because:** The output read like a report, not advice from a friend. The result page already has the per-tool breakdown — duplicating it in bullets was redundant and clinical. The 60-second-audit framing wants a paragraph, not another table.

**Fix:** Added "no bullet points, no headings, single paragraph" to the system prompt. Output now feels like a Slack message from a CTO friend, which is the tone the result page is built for.

### 5. `max_tokens=300`
**Tried:** Allowed enough room for a full report.

**Failed because:** The model used every token. Summaries ran 150–250 words and buried the key savings number in the middle.

**Fix:** Dropped to `max_tokens=200`. Forces concision. The savings number now lands in the first sentence ~90% of the time.

### Considered and rejected (not even tried)

- **Fine-tuning a small model on audit summaries**: overkill. One well-shaped prompt on gpt-4o-mini is already $0.0001/audit and reads well. Fine-tuning adds maintenance for no measurable quality lift at this volume.
- **Streaming the summary to the page**: the engine is fast enough (~10ms) that the whole audit + summary completes in ~1.2s. Streaming would have been complexity for a UX win nobody asked for.
- **Multiple prompts (one for high_savings, one for optimal)**: would have meant duplicating instructions. Easier to handle conditional tone inside one system prompt via the JSON's `route` field.

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
