from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audits.engine.input import AuditInput


@dataclass
class Candidate:
    vendor_key: str
    plan_key: str
    vendor_name: str
    plan_name: str
    label: str            # human-readable action, e.g. "Switch to GitHub Copilot Business"
    monthly_cost: float   # projected total cost for the user's seat count
    fit_score: int        # 1-5 from ToolFitScore table
    reasoning: str        # one sentence for the Finding card
    evidence: dict        # named numbers + source URL for the "evidence" toggle
    is_current: bool = False
    is_credex_eligible: bool = False

    def is_valid(self, inp: "AuditInput") -> bool:
        """A candidate is invalid if it needs more seats than the team."""
        return True  # min_seats is enforced at cost calculation; max_seats rarely relevant


@dataclass
class Finding:
    vendor_key: str
    vendor_name: str
    current_plan: str
    current_seats: int
    current_spend: float
    recommended_action: str
    recommended_cost: float
    monthly_savings: float
    reasoning: str
    evidence: dict
    is_optimal: bool = False   # True → current plan is already best


@dataclass
class AuditResult:
    findings: list[Finding]
    monthly_savings: float
    annual_savings: float
    total_current_spend: float
    route: str               # "high_savings" | "normal" | "optimal"
    credex_eligible: bool    # should we show the Credex CTA?
    tool_count: int
