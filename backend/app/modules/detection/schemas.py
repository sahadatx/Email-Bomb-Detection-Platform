from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DetectionCreate(BaseModel):
    email_id: UUID | None = None
    model_version_id: UUID | None = None
    run_behavioral_analysis: bool = True
    calculate_risk_score: bool = True


class DetectionRawCreate(BaseModel):
    raw_email: str = Field(min_length=20, max_length=20_000_000)
    filename: str = Field(default="pasted-email.eml", max_length=255)
    model_version_id: UUID | None = None
    run_behavioral_analysis: bool = True
    calculate_risk_score: bool = True


class DetectionBatchCreate(BaseModel):
    email_ids: list[UUID] = Field(min_length=1, max_length=100)
    model_version_id: UUID | None = None
    run_behavioral_analysis: bool = True
    calculate_risk_score: bool = True


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email_id: UUID | None
    input_id: UUID | None = None
    input_filename: str | None = None
    model_version_id: UUID
    predicted_label: str
    confidence: float | None
    status: str
    feature_snapshot: dict[str, Any]
    error_message: str | None
    created_at: datetime
    email_subject: str | None = None
    sender: str | None = None
    model_name: str | None = None
    version: int | None = None
    risk: dict[str, Any] | None = None
    behavioral: dict[str, Any] | None = None


class DetectionList(BaseModel):
    items: list[DetectionRead]
    total: int
    page: int
    page_size: int


class SettingsRead(BaseModel):
    default_model_version_id: UUID | None
    high_risk_threshold: int
    critical_risk_threshold: int
    enable_behavioral_analysis: bool
    save_feature_snapshots: bool
    store_detection_history: bool


class SettingsUpdate(BaseModel):
    default_model_version_id: UUID | None = None
    high_risk_threshold: int = Field(ge=1, le=100)
    critical_risk_threshold: int = Field(ge=1, le=100)
    enable_behavioral_analysis: bool
    save_feature_snapshots: bool
    store_detection_history: bool


class EmailOption(BaseModel):
    id: UUID
    sender: str | None
    subject: str | None
    status: Literal["ready", "features_missing", "features_failed"]
    has_features: bool
