from dataclasses import dataclass
from typing import Literal


UseCase = Literal["coding", "writing", "data", "research", "mixed"]


@dataclass
class ToolLine:
    vendor_key: str       # "cursor"
    plan_key: str         # "business"
    monthly_spend: float  # user-reported, USD
    seats: int


@dataclass
class AuditInput:
    tools: list[ToolLine]
    team_size: int
    use_case: UseCase
