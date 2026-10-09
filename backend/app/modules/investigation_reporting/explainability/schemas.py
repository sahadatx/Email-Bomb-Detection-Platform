from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalystNoteCreate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    body: str = Field(min_length=1, max_length=10000)
    category: Literal["observation", "interpretation", "follow_up"] = "observation"

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("body")
    @classmethod
    def clean_body(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Note body is required.")
        return normalized


class AnalystNoteUpdate(AnalystNoteCreate):
    category: Literal["observation", "interpretation", "follow_up"]


class AnalystNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    detection_id: UUID
    title: str | None
    body: str
    category: str
    author_id: str
    created_at: datetime
    updated_at: datetime


class ExplanationList(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
