from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EvidenceType = Literal["email_header", "content", "feature", "behavioral", "network", "other"]
EvidenceStatus = Literal["pending", "verified", "flagged", "rejected"]
class EvidenceCreate(BaseModel):
    detection_id: UUID
    source_email_id: UUID | None = None
    evidence_type: EvidenceType
    name: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    observed_value: str | None = Field(default=None, max_length=20000)
    provenance: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime | None = None
    analyst_note: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Evidence name is required.")
        return value


class EvidenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    evidence_type: EvidenceType | None = None
    observed_value: str | None = Field(default=None, max_length=20000)
    provenance: dict[str, Any] | None = None
    analyst_note: str | None = Field(default=None, max_length=5000)
    source_email_id: UUID | None = None


class EvidenceReview(BaseModel):
    review_status: EvidenceStatus
    reason: str = Field(min_length=1, max_length=2000)
    analyst_comment: str | None = Field(default=None, max_length=5000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A review reason is required.")
        return value


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    detection_id: UUID
    source_email_id: UUID | None
    evidence_type: str
    name: str
    description: str | None
    observed_value: str | None
    provenance: dict[str, Any]
    review_status: str
    analyst_note: str | None
    collected_at: datetime | None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class EvidenceEventRead(BaseModel):
    id: UUID
    actor_id: str
    action: str
    reason: str | None
    before_data: dict[str, Any]
    after_data: dict[str, Any]
    created_at: datetime


class EvidenceList(BaseModel):
    items: list[EvidenceRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: dict[str, int]
