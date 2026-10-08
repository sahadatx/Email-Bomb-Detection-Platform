from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ML Model Definitions
# ---------------------------------------------------------------------------


class MLModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    model_type: Literal["classifier"] = "classifier"
    algorithm: str = Field(min_length=1, max_length=100)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active", pattern=r"^(active|inactive)$")

    @field_validator("name", "algorithm")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty.")
        return value


class MLModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    algorithm: str | None = Field(default=None, min_length=1, max_length=100)
    hyperparameters: dict[str, Any] | None = None

    @field_validator("name", "algorithm")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            raise ValueError("Name must not be empty.")
        return value


class MLModelStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(active|inactive)$")


class MLModelRead(ORMModel):
    id: UUID
    name: str
    description: str | None
    model_type: Literal["classifier"] = "classifier"
    algorithm: str
    hyperparameters: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ML Training Runs
# ---------------------------------------------------------------------------


class MLTrainingRunCreate(BaseModel):
    model_definition_id: UUID
    preprocessing_run_id: UUID
    config_snapshot: dict[str, Any] = Field(default_factory=dict)


class MLTrainingRunRead(ORMModel):
    id: UUID
    model_definition_id: UUID
    preprocessing_run_id: UUID
    status: str
    progress_percent: float
    config_snapshot: dict[str, Any]
    training_sample_count: int
    validation_sample_count: int
    duration_ms: int | None
    error_code: str | None
    error_message: str | None
    result_summary: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class MLTrainingRunList(BaseModel):
    items: list[MLTrainingRunRead]
    total: int


class MLTrainingRunRetry(BaseModel):
    """Request body for retrying a failed training run."""

    pass


# ---------------------------------------------------------------------------
# ML Model Versions / Registry
# ---------------------------------------------------------------------------


class MLModelVersionRead(ORMModel):
    id: UUID
    model_definition_id: UUID
    training_run_id: UUID
    version: int
    status: str
    artifact_filename: str | None
    storage_path: str | None
    media_type: str | None
    size_bytes: int
    checksum_sha256: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    activated_at: datetime | None
    archived_at: datetime | None


class MLModelVersionList(BaseModel):
    items: list[MLModelVersionRead]
    total: int


# ---------------------------------------------------------------------------
# ML Evaluation Runs
# ---------------------------------------------------------------------------


class MLEvaluationRunCreate(BaseModel):
    model_version_id: UUID
    preprocessing_run_id: UUID
    evaluation_split: str = Field(pattern=r"^(validation|testing)$")


class MLEvaluationRunRead(ORMModel):
    id: UUID
    model_version_id: UUID
    preprocessing_run_id: UUID
    evaluation_split: str
    status: str
    sample_count: int
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    confusion_matrix: dict[str, Any]
    classification_report: dict[str, Any]
    result_summary: dict[str, Any]
    duration_ms: int | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class MLEvaluationRunList(BaseModel):
    items: list[MLEvaluationRunRead]
    total: int