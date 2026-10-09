from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ReportType = Literal["detection", "investigation", "campaign", "summary"]
ReportStatus = Literal["draft", "generated", "failed", "archived"]
ReportSection = Literal[
    "executive_summary", "detection_summary", "explainability", "evidence",
    "risk_analysis", "behavioral_analysis", "analyst_notes", "technical_appendix",
]


class ReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    report_type: ReportType = "investigation"
    detection_ids: list[UUID] = Field(min_length=1, max_length=100)
    sections: list[ReportSection] = Field(min_length=1)
    output_format: Literal["json", "pdf"] = "json"
    analyst_notes: str | None = Field(default=None, max_length=10000)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Report title is required.")
        return value

    @field_validator("detection_ids")
    @classmethod
    def unique_detection_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Detection records must be unique.")
        return value

    @field_validator("sections")
    @classmethod
    def unique_sections(cls, value: list[ReportSection]) -> list[ReportSection]:
        if len(set(value)) != len(value):
            raise ValueError("Report sections must be unique.")
        return value


class ReportUpdate(ReportCreate):
    """Draft replacement payload; generated snapshots are immutable."""


class ReportPreview(ReportCreate):
    """Transient preview payload; it is validated and never persisted."""


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None
    report_type: str
    output_format: str
    status: str
    detection_ids: list[str]
    sections: list[str]
    analyst_notes: str | None
    configuration: dict[str, Any]
    snapshot: dict[str, Any] | None
    error_summary: str | None
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    generated_at: datetime | None
    archived_at: datetime | None


class ReportEventRead(BaseModel):
    id: UUID
    report_id: UUID
    actor_id: str
    action: str
    created_at: datetime


class ReportList(BaseModel):
    items: list[ReportRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: dict[str, int]
