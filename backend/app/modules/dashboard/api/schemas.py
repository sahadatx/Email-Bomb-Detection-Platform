"""Validated read models returned by dashboard endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from ..selectors.dashboard_filters import DashboardFilters


class DashboardMetric(BaseModel):
    value: int
    available: bool = True
    description: str


class DashboardSummary(BaseModel):
    total_emails: DashboardMetric
    emails_analyzed: DashboardMetric
    bomb_detected: DashboardMetric
    high_risk_emails: DashboardMetric
    active_security_alerts: DashboardMetric


class ClassificationCount(BaseModel):
    classification: Literal["normal", "bomb"]
    count: int = Field(ge=0)


class RiskCount(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    count: int = Field(ge=0)


class RiskDistributionResponse(BaseModel):
    items: list[RiskCount]


class ActivityPoint(BaseModel):
    timestamp: str
    normal: int = Field(0, ge=0)
    bomb: int = Field(0, ge=0)


class ClassificationResponse(BaseModel):
    distribution: list[ClassificationCount]
    trend: list[ActivityPoint]


class RecentDetection(BaseModel):
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


class RecentActivityItem(BaseModel):
    id: str
    occurred_at: datetime
    category: Literal["audit", "security"]
    title: str
    actor: str | None = None
    target: str | None = None
    status: str | None = None
    severity: str | None = None
    source: str
    href: str


class HealthComponent(BaseModel):
    name: str
    status: str
    description: str
    last_checked: datetime | None = None
    message: str | None = None


class SystemHealth(BaseModel):
    overall_status: str
    checked_at: datetime
    components: list[HealthComponent]


class ModelStatusItem(BaseModel):
    model_id: UUID
    model_version_id: UUID
    name: str
    algorithm: str
    version: int
    activated_at: datetime | None = None
    artifact_available: bool


class ModelStatus(BaseModel):
    status: str
    active_count: int = Field(ge=0)
    active_models: list[ModelStatusItem]
    message: str | None = None


class ThreatFeedStatusItem(BaseModel):
    id: UUID
    name: str
    enabled: bool
    sync_status: str
    imported_indicator_count: int = Field(ge=0)
    last_sync_at: datetime | None = None
    latest_error: str | None = None


class ThreatFeedStatus(BaseModel):
    status: str
    total_feeds: int = Field(ge=0)
    active_feeds: int = Field(ge=0)
    failed_feeds: int = Field(ge=0)
    imported_indicators: int = Field(ge=0)
    feeds: list[ThreatFeedStatusItem]
    message: str | None = None


class DashboardModelOption(BaseModel):
    id: UUID
    name: str
    algorithm: str


class DashboardOverview(BaseModel):
    generated_at: datetime
    filters: DashboardFilters
    filter_scope: dict[str, str]
    summary: DashboardSummary
    classification: list[ClassificationCount]
    risk_distribution: list[RiskCount]
    activity: list[ActivityPoint]
    recent_detections: list[RecentDetection]
    recent_activity: list[RecentActivityItem]
    system_health: SystemHealth
    model_status: ModelStatus
    threat_feed_status: ThreatFeedStatus
    model_options: list[DashboardModelOption]
    data_sources: list[str]


class DashboardActivityResponse(BaseModel):
    filters: DashboardFilters
    interval: Literal["hour", "day"]
    scope: str
    items: list[ActivityPoint]


class DashboardClassificationResponse(ClassificationResponse):
    pass


class DashboardRecentDetectionsResponse(BaseModel):
    filters: DashboardFilters
    items: list[RecentDetection]
    limit: int


class DashboardRecentActivityResponse(BaseModel):
    filters: DashboardFilters
    items: list[RecentActivityItem]
    limit: int


class DashboardModelOptionsResponse(BaseModel):
    items: list[DashboardModelOption]
