"""
Seed VendorPlan and ToolFitScore rows.
Run once after first deploy: python manage.py seed_pricing
Safe to re-run — uses update_or_create so it won't duplicate rows.

Pricing verified: 2026-05-10
Sources documented in PRICING_DATA.md
"""
import datetime
from django.core.management.base import BaseCommand
from pricing.models import VendorPlan, ToolFitScore

TODAY = datetime.date(2026, 5, 10)

PLANS = [
    # ── Cursor ─────────────────────────────────────────────────────────────
    dict(vendor_key="cursor", vendor_name="Cursor", plan_key="hobby", plan_name="Hobby",
         price_monthly=0, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://cursor.com/pricing", last_verified=TODAY),
    dict(vendor_key="cursor", vendor_name="Cursor", plan_key="pro", plan_name="Pro",
         price_per_seat=20, min_seats=1, features=[],
         credex_eligible=False,
         source_url="https://cursor.com/pricing", last_verified=TODAY),
    dict(vendor_key="cursor", vendor_name="Cursor", plan_key="business", plan_name="Business",
         price_per_seat=40, min_seats=1, features=["sso", "admin", "privacy"],
         credex_eligible=True,
         source_url="https://cursor.com/pricing", last_verified=TODAY),

    # ── GitHub Copilot ─────────────────────────────────────────────────────
    dict(vendor_key="copilot", vendor_name="GitHub Copilot", plan_key="individual",
         plan_name="Individual",
         price_monthly=10, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://github.com/features/copilot", last_verified=TODAY),
    dict(vendor_key="copilot", vendor_name="GitHub Copilot", plan_key="business",
         plan_name="Business",
         price_per_seat=19, min_seats=1, features=["admin", "policy"],
         credex_eligible=False,
         source_url="https://github.com/features/copilot", last_verified=TODAY),
    dict(vendor_key="copilot", vendor_name="GitHub Copilot", plan_key="enterprise",
         plan_name="Enterprise",
         price_per_seat=39, min_seats=1, features=["admin", "policy", "kb", "pr-summaries"],
         credex_eligible=True,
         source_url="https://github.com/features/copilot", last_verified=TODAY),

    # ── Claude (Anthropic subscription) ────────────────────────────────────
    dict(vendor_key="claude", vendor_name="Claude", plan_key="free", plan_name="Free",
         price_monthly=0, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://claude.ai/upgrade", last_verified=TODAY),
    dict(vendor_key="claude", vendor_name="Claude", plan_key="pro", plan_name="Pro",
         price_monthly=20, min_seats=1, max_seats=1, features=["projects", "priority-access"],
         credex_eligible=False,
         source_url="https://claude.ai/upgrade", last_verified=TODAY),
    dict(vendor_key="claude", vendor_name="Claude", plan_key="max", plan_name="Max",
         price_monthly=100, min_seats=1, max_seats=1, features=["5x-usage", "priority-access"],
         credex_eligible=False,
         source_url="https://claude.ai/upgrade", last_verified=TODAY),
    dict(vendor_key="claude", vendor_name="Claude", plan_key="team", plan_name="Team",
         price_per_seat=30, min_seats=5, features=["admin", "projects", "priority-access"],
         credex_eligible=True,
         source_url="https://claude.ai/upgrade", last_verified=TODAY),

    # ── ChatGPT ────────────────────────────────────────────────────────────
    dict(vendor_key="chatgpt", vendor_name="ChatGPT", plan_key="free", plan_name="Free",
         price_monthly=0, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://openai.com/chatgpt/pricing", last_verified=TODAY),
    dict(vendor_key="chatgpt", vendor_name="ChatGPT", plan_key="plus", plan_name="Plus",
         price_monthly=20, min_seats=1, max_seats=1, features=["gpt4o", "advanced-voice"],
         credex_eligible=False,
         source_url="https://openai.com/chatgpt/pricing", last_verified=TODAY),
    dict(vendor_key="chatgpt", vendor_name="ChatGPT", plan_key="team", plan_name="Team",
         price_per_seat=30, min_seats=2, features=["admin", "workspace", "gpt4o"],
         credex_eligible=True,
         source_url="https://openai.com/chatgpt/pricing", last_verified=TODAY),

    # ── Anthropic API (usage-based — user reports their own monthly spend) ──
    dict(vendor_key="anthropic_api", vendor_name="Anthropic API", plan_key="api",
         plan_name="API (pay-as-you-go)",
         price_monthly=0, min_seats=1,  # 0 = user-reported; no fixed plan cost
         features=["api-access"],
         credex_eligible=False,
         source_url="https://www.anthropic.com/pricing", last_verified=TODAY),

    # ── OpenAI API (usage-based) ────────────────────────────────────────────
    dict(vendor_key="openai_api", vendor_name="OpenAI API", plan_key="api",
         plan_name="API (pay-as-you-go)",
         price_monthly=0, min_seats=1,
         features=["api-access"],
         credex_eligible=False,
         source_url="https://openai.com/api/pricing", last_verified=TODAY),

    # ── Gemini ─────────────────────────────────────────────────────────────
    dict(vendor_key="gemini", vendor_name="Gemini", plan_key="free", plan_name="Free",
         price_monthly=0, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://gemini.google.com", last_verified=TODAY),
    dict(vendor_key="gemini", vendor_name="Gemini", plan_key="advanced", plan_name="Advanced",
         price_monthly=19.99, min_seats=1, max_seats=1,
         features=["gemini-ultra", "2tb-storage"],
         credex_eligible=False,
         source_url="https://one.google.com/about/ai-premium", last_verified=TODAY),
    dict(vendor_key="gemini", vendor_name="Gemini", plan_key="business", plan_name="Business",
         price_per_seat=30, min_seats=1, features=["workspace", "gemini-ultra"],
         credex_eligible=False,
         source_url="https://workspace.google.com/products/gemini", last_verified=TODAY),

    # ── Windsurf ───────────────────────────────────────────────────────────
    dict(vendor_key="windsurf", vendor_name="Windsurf", plan_key="free", plan_name="Free",
         price_monthly=0, min_seats=1, max_seats=1, features=[],
         credex_eligible=False,
         source_url="https://windsurf.com/pricing", last_verified=TODAY),
    dict(vendor_key="windsurf", vendor_name="Windsurf", plan_key="pro", plan_name="Pro",
         price_monthly=15, min_seats=1, max_seats=1, features=["unlimited-completions"],
         credex_eligible=False,
         source_url="https://windsurf.com/pricing", last_verified=TODAY),
    dict(vendor_key="windsurf", vendor_name="Windsurf", plan_key="teams", plan_name="Teams",
         price_per_seat=30, min_seats=2, features=["admin", "unlimited-completions"],
         credex_eligible=False,
         source_url="https://windsurf.com/pricing", last_verified=TODAY),
]

# Fit scores: how well each tool.plan serves a given use case (1=poor, 5=perfect)
# Only defined where meaningful — missing combos default to 0 (excluded from alternatives)
FIT_SCORES = [
    # coding
    ("cursor", "pro",       "coding", 5, "Purpose-built IDE with multi-file context, edit mode, and .cursorrules"),
    ("cursor", "business",  "coding", 5, "Same as Pro with team admin features; identical coding capability"),
    ("copilot", "individual","coding", 4, "Strong inline completions; IDE-native but less multi-file context than Cursor"),
    ("copilot", "business", "coding", 4, "Same coding capability as Individual, adds org-level policy controls"),
    ("copilot", "enterprise","coding", 4, "Same coding capability, adds knowledge bases and PR summaries"),
    ("windsurf", "pro",     "coding", 4, "Strong alternative to Copilot; fast completions, improving rapidly"),
    ("windsurf", "teams",   "coding", 4, "Same coding capability as Pro with team management"),
    ("claude", "pro",       "coding", 3, "Excellent at code reasoning in chat; no IDE integration"),
    ("claude", "max",       "coding", 3, "Higher usage limits of Pro; same IDE-less experience"),
    ("claude", "team",      "coding", 3, "Team plan of Pro capability; no IDE integration"),
    ("chatgpt", "plus",     "coding", 3, "GPT-4o capable at coding; chat only, no IDE integration"),
    ("chatgpt", "team",     "coding", 3, "Same as Plus with team workspace; no IDE integration"),

    # writing
    ("claude", "pro",       "writing", 5, "Best-in-class long-form writing; nuanced tone, avoids generic phrasing"),
    ("claude", "max",       "writing", 5, "Claude Pro with 5x usage — same quality, higher limits"),
    ("claude", "team",      "writing", 5, "Claude Pro quality with team workspace and shared projects"),
    ("chatgpt", "plus",     "writing", 4, "GPT-4o is excellent at writing; slightly more verbose than Claude on average"),
    ("chatgpt", "team",     "writing", 4, "ChatGPT Plus quality with team workspace"),
    ("gemini", "advanced",  "writing", 4, "Gemini Ultra strong at writing; deeply integrated with Google Docs"),
    ("gemini", "business",  "writing", 4, "Gemini Advanced quality with Google Workspace integration"),
    ("cursor", "pro",       "writing", 1, "Code editor — very poor writing UX"),
    ("cursor", "business",  "writing", 1, "Code editor — very poor writing UX"),
    ("windsurf", "pro",     "writing", 1, "Code editor — very poor writing UX"),

    # data / analysis
    ("chatgpt", "plus",     "data", 5, "Advanced Data Analysis (Code Interpreter) is best-in-class for data work"),
    ("chatgpt", "team",     "data", 5, "Same Advanced Data Analysis with team workspace"),
    ("claude", "pro",       "data", 4, "Strong at data reasoning and code generation; no native chart output"),
    ("claude", "max",       "data", 4, "Higher usage limits for sustained data analysis sessions"),
    ("claude", "team",      "data", 4, "Claude Pro capability with team collaboration"),
    ("gemini", "advanced",  "data", 4, "Good at data analysis; native Google Sheets integration"),
    ("copilot", "individual","data", 3, "Useful for data science code (Python, R); limited analysis beyond code"),
    ("copilot", "business", "data", 3, "Same as Individual for data work"),

    # research
    ("claude", "pro",       "research", 5, "Excellent synthesis of long documents; 200K context window"),
    ("claude", "max",       "research", 5, "Same as Pro with higher usage — critical for sustained research sessions"),
    ("claude", "team",      "research", 5, "Claude Pro quality with shared research projects"),
    ("chatgpt", "plus",     "research", 4, "Good at synthesis; browsing feature adds real-time research capability"),
    ("chatgpt", "team",     "research", 4, "ChatGPT Plus quality with team workspace"),
    ("gemini", "advanced",  "research", 4, "Good at research; integrates with Google Search natively"),
    ("copilot", "enterprise","research", 3, "Knowledge bases useful for internal docs; limited general research"),

    # mixed
    ("claude", "pro",       "mixed", 5, "Best all-rounder: coding, writing, analysis, research"),
    ("claude", "team",      "mixed", 5, "Claude Pro quality with team features"),
    ("chatgpt", "plus",     "mixed", 4, "Strong across all use cases; slightly weaker writing vs Claude"),
    ("chatgpt", "team",     "mixed", 4, "ChatGPT Plus quality with team workspace"),
    ("cursor", "pro",       "mixed", 3, "Excellent for coding component; weak for writing/research"),
    ("copilot", "business", "mixed", 3, "Good for coding; limited for writing/research"),
    ("gemini", "advanced",  "mixed", 3, "Decent all-rounder; strong with Google Workspace integration"),
]


class Command(BaseCommand):
    help = "Seed VendorPlan and ToolFitScore tables. Safe to re-run."

    def handle(self, *args, **kwargs):
        plan_count = 0
        for data in PLANS:
            _, created = VendorPlan.objects.update_or_create(
                vendor_key=data["vendor_key"],
                plan_key=data["plan_key"],
                defaults={k: v for k, v in data.items()
                          if k not in ("vendor_key", "plan_key")},
            )
            plan_count += 1

        score_count = 0
        for vendor_key, plan_key, use_case, score, reasoning in FIT_SCORES:
            _, created = ToolFitScore.objects.update_or_create(
                vendor_key=vendor_key,
                plan_key=plan_key,
                use_case=use_case,
                defaults={"score": score, "reasoning": reasoning},
            )
            score_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {plan_count} plans and {score_count} fit scores."
        ))
