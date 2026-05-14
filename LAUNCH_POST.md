# Launch copy — OverpaidAI

Two artifacts for launching:
1. **Blog post** (200-word version, for a personal blog / Substack / Medium)
2. **Twitter / X thread** (7 tweets)

---

## Blog post

### I built a free tool to find out if your team is overpaying for AI

I keep meeting founders who can't tell me what their team spends on AI. They know it's "a few hundred a month." They don't know which seats are unused, which plans are wrong-sized, or which paid subscriptions could be replaced with the free tier.

So I built **OverpaidAI**. You enter your AI tools, plans, and seat counts. In ~10 seconds, you get a defensible breakdown of where you're overspending and exactly what to switch to.

It's not a guessing tool. The engine generates every plausible alternative for each line item — same-vendor downgrades, vendor switches with comparable capability, seat right-sizes — and picks the cheapest valid option. Each recommendation cites the exact pricing page it's based on, so a finance person can verify in 30 seconds.

The honesty rails matter as much as the math:
- Savings under $5/mo are suppressed (it's noise)
- Claimed savings are capped at 80% of current spend (nothing absurd)
- If you're already on the right plan, the tool says so — no fake findings

Try it: **https://ai-expense-auditor-kos7.onrender.com**

Free. No login. 60 seconds.

---

## Twitter / X thread

**1/**
Most 10-person startups don't know what they spend on AI. They know it's "a few hundred." They don't know which seats are unused, which plans are oversized, or which subs could just be the free tier.

So I built a free tool to find out: 👇

**2/**
**OverpaidAI** — enter your AI tools, plans, and seat counts. Get a defensible breakdown of where you're overspending in ~10 seconds.

No login. No fluff. No "book a demo." Just the numbers.

**3/**
The engine doesn't guess. For each tool, it generates every plausible alternative — cheaper plan from the same vendor, switch to a comparable tool, right-size seats — and picks the cheapest valid one.

Every recommendation cites the official pricing page it's based on.

**4/**
Honesty rails I cared about:
- Savings < $5/mo are hidden (noise floor)
- Claims capped at 80% of current spend (no absurd numbers)
- If you're already optimal, it says so. No fake findings to justify the tool.

**5/**
Example: a team paying $150/mo for Claude Team with 2 seats. The plan has a 5-seat minimum — they're paying for 3 unused seats. Recommendation: drop to Claude Pro × 2 ($40/mo). Annual savings: $1,320.

This is the kind of thing that's invisible until someone surfaces it.

**6/**
Tech: Django + Postgres + Alpine.js. The audit engine is pure Python — no LLM in the math, just rule-based candidate generation + cost-minimisation with a fit-score tiebreaker. LLM only writes the human-readable summary at the end.

Open source, free to run yourself.

**7/**
Try it: https://ai-expense-auditor-kos7.onrender.com

If you find $X/mo in savings, I'd love to hear it. If you don't, also tell me — that means you're doing it right and I want to know what you're doing differently.

🟠
