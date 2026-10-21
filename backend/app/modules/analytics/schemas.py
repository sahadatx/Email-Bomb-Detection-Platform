from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticsFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d"
    classification: Literal["normal", "bomb"] | None = None
    risk_level: Literal["low", "medium", "high", "critical"] | None = None
    model_definition_id: UUID | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class AnalyticsMetric(BaseModel):
    value: int | float | None
    available: bool = True
    description: str


class AnalyticsOverview(BaseModel):
    filters: AnalyticsFilters
    total_emails: AnalyticsMetric
    bomb_emails: AnalyticsMetric
    detection_rate: AnalyticsMetric
    high_risk_emails: AnalyticsMetric
    total_detections: int
    data_sources: list[str]


class AnalyticsModelOption(BaseModel):
    id: UUID
    name: str
    algorithm: str


class AnalyticsModelOptions(BaseModel):
    items: list[AnalyticsModelOption]


class AnalyticsTrendPoint(BaseModel):
    timestamp: str
    normal: int = 0
    bomb: int = 0


class AnalyticsClassificationCount(BaseModel):
    classification: Literal["normal", "bomb"]
    count: int


class AnalyticsClassification(BaseModel):
    items: list[AnalyticsTrendPoint]
    distribution: list[AnalyticsClassificationCount]


class AnalyticsRiskCount(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    count: int


class AnalyticsRiskDistribution(BaseModel):
    items: list[AnalyticsRiskCount]


class AnalyticsEvaluation(BaseModel):
    evaluation_id: UUID
    evaluation_split: str
    model_definition_id: UUID
    model_name: str
    algorithm: str
    model_version_id: UUID
    version: int
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    sample_count: int
    created_at: datetime | None = None


class AnalyticsPerformance(BaseModel):
    available: bool
    evaluation_split: Literal["validation", "testing"]
    evaluation: AnalyticsEvaluation | None = None
    metrics: dict[str, float | None]


class AnalyticsActivityPoint(BaseModel):
    timestamp: str
    emails: int


class AnalyticsBehavior(BaseModel):
    emails_analyzed: int
    burst_events: int
    suspicious_patterns: int
    activity: list[AnalyticsActivityPoint]
    available: bool


class AnalyticsRecentDetection(BaseModel):
    id: UUID
    email_id: UUID | None = None
    sender: str | None = None
    subject: str | None = None
    classification: Literal["normal", "bomb"]
    confidence: float | None = None
    risk_level: Literal["low", "medium", "high", "critical"] | None = None
    risk_score: float | None = None
    model_name: str | None = None
    model_version: int | None = None
    created_at: datetime | None = None


class AnalyticsRecentDetections(BaseModel):
    items: list[AnalyticsRecentDetection]
