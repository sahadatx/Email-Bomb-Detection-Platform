from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class BehavioralSummary(BaseModel):
    emails_analyzed: int
    anomalies: int
    patterns: list[dict[str, Any]]


class BehavioralActivityPoint(BaseModel):
    time: str
    emails: int


class BehavioralActivity(BaseModel):
    period: str
    activity: list[BehavioralActivityPoint]


class BehavioralAnomaly(BaseModel):
    detection_id: UUID
    sender: str | None = None
    subject: str | None = None
    created_at: datetime
    pattern: str
    severity: str
    description: str
