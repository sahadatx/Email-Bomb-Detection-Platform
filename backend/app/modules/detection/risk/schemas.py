from pydantic import BaseModel


class RiskFactorSummary(BaseModel):
    name: str
    occurrences: int
    impact: str | None = None
    detection_ids: list[str]


class RiskSummary(BaseModel):
    distribution: dict[str, int]
    factors: list[RiskFactorSummary]
