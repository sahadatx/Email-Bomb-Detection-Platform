from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Page(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(30, ge=1, le=100)
    total: int
    total_pages: int


class IndicatorCreate(BaseModel):
    value: str = Field(min_length=3, max_length=2048)
    indicator_type: Literal["ip", "domain", "url", "hash", "email"]
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    confidence: int | None = Field(None, ge=0, le=100)
    source: Literal["manual"] = "manual"
    description: str | None = Field(None, max_length=10000)
    expires_at: datetime | None = None


class IndicatorUpdate(BaseModel):
    value: str | None = Field(None, min_length=3, max_length=2048)
    indicator_type: Literal["ip", "domain", "url", "hash", "email"] | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    confidence: int | None = Field(None, ge=0, le=100)
    description: str | None = Field(None, max_length=10000)
    expires_at: datetime | None = None


class IndicatorStatus(BaseModel):
    status: Literal["active", "inactive"]


class IndicatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    value: str
    indicator_type: str
    severity: str
    confidence: int | None
    source: str
    feed_id: UUID | None
    feed_name: str | None = None
    description: str | None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    matches_count: int = 0


class IndicatorList(Page):
    items: list[IndicatorRead]


class FeedCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    feed_type: Literal["stix_taxii", "csv", "json", "api", "internal"]
    url: str | None = Field(None, max_length=2048)
    auth_type: Literal["none", "api_key", "bearer", "basic"] = "none"
    credential: str | None = Field(None, max_length=4096, repr=False)
    sync_interval_minutes: int = Field(60, ge=5, le=10080)
    description: str | None = Field(None, max_length=10000)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_connection(self):
        if self.feed_type != "internal" and not self.url:
            raise ValueError("A feed URL is required for external feeds.")
        if self.feed_type == "internal" and self.url:
            raise ValueError("Internal feeds do not accept an external URL.")
        if self.feed_type == "internal" and self.auth_type != "none":
            raise ValueError("Internal feeds do not use external authentication.")
        if self.auth_type != "none" and not self.credential:
            raise ValueError(
                "A credential is required for the selected authentication type."
            )
        if self.auth_type == "none" and self.credential:
            raise ValueError(
                "Choose an authentication type before supplying a credential."
            )
        return self


class FeedUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=180)
    feed_type: Literal["stix_taxii", "csv", "json", "api", "internal"] | None = None
    url: str | None = Field(None, max_length=2048)
    auth_type: Literal["none", "api_key", "bearer", "basic"] | None = None
    credential: str | None = Field(None, max_length=4096, repr=False)
    sync_interval_minutes: int | None = Field(None, ge=5, le=10080)
    description: str | None = Field(None, max_length=10000)
    enabled: bool | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self):
        if self.auth_type == "none" and self.credential:
            raise ValueError(
                "Choose an authentication type before supplying a credential."
            )
        return self


class FeedRead(BaseModel):
    id: UUID
    name: str
    feed_type: str
    url: str | None
    auth_type: str
    has_credential: bool
    sync_interval_minutes: int
    description: str | None
    enabled: bool
    sync_status: str
    imported_indicator_count: int
    last_sync_at: datetime | None
    next_sync_at: datetime | None
    latest_error: str | None
    created_at: datetime
    updated_at: datetime


class FeedList(Page):
    items: list[FeedRead]


class SyncRead(BaseModel):
    id: UUID
    feed_id: UUID
    status: str
    imported_count: int
    error_summary: str | None
    started_at: datetime
    completed_at: datetime | None


class SyncList(Page):
    items: list[SyncRead]


class MatchRead(BaseModel):
    id: UUID
    email_id: UUID
    email_label: str | None
    detection_id: UUID | None
    indicator_id: UUID
    indicator_value: str
    indicator_type: str
    severity: str
    classification: str | None
    feed_id: UUID | None
    feed_name: str | None
    match_status: str
    matched_field: str
    matched_at: datetime


class MatchStatusUpdate(BaseModel):
    match_status: Literal["new", "reviewed", "investigating", "resolved"]


class MatchList(Page):
    items: list[MatchRead]


class ThreatFilters(BaseModel):
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d"
    from_date: datetime | None = None
    to_date: datetime | None = None
    threat_type: Literal["ip", "domain", "url", "hash", "email"] | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    feed_id: UUID | None = None


class Overview(BaseModel):
    total_indicators: int
    active_feeds: int
    threat_matches: int
    critical_threats: int
    trends: list[dict[str, Any]]
    types: list[dict[str, Any]]
    severities: list[dict[str, Any]]
    recent_matches: list[MatchRead]
    data_sources: list[str]


class MatchSummary(BaseModel):
    total_matches: int
    critical_matches: int
    matched_emails: int
    unique_indicators: int


class ReconcileResult(BaseModel):
    indicators_checked: int
    matches_created: int


class ThreatExport(BaseModel):
    format: Literal["csv", "json"] = "csv"
    limit: int = Field(1000, ge=1, le=10000)
