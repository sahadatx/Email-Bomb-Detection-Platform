from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    model_definition_id: UUID
    dataset_version_id: UUID
    preprocessing_run_id: UUID
    feature_set: list[str] = Field(default_factory=list, max_length=64)
    training_config: dict[str, Any] = Field(default_factory=dict)
    evaluation_split: Literal["validation", "testing"] = "validation"

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value: raise ValueError("Experiment name is required.")
        return value


class ExperimentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    feature_set: list[str] | None = Field(default=None, max_length=64)
    training_config: dict[str, Any] | None = None
    evaluation_split: Literal["validation", "testing"] | None = None

    @model_validator(mode="after")
    def non_empty(self):
        if not self.model_fields_set: raise ValueError("At least one field must be supplied.")
        return self

    @field_validator("name")
    @classmethod
    def clean_optional_name(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Experiment name cannot be blank.")
        return value


ExperimentStatus = Literal["draft", "queued", "running", "completed", "failed", "cancelled"]


class ExperimentRunSummary(BaseModel):
    id: UUID
    training_run_id: UUID
    evaluation_run_id: UUID | None = None
    model_version_id: UUID | None = None
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress_percent: int
    error_summary: str | None = None
    logs: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, float | None] | None = None
    evaluation_split: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ExperimentItem(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    status: ExperimentStatus
    model_definition_id: UUID
    model_name: str | None = None
    algorithm: str | None = None
    dataset_version_id: UUID
    dataset_id: UUID | None = None
    dataset_name: str | None = None
    dataset_version_name: str | None = None
    dataset_version_number: int | None = None
    preprocessing_run_id: UUID
    feature_set: list[str] = Field(default_factory=list)
    feature_count: int = 0
    training_config: dict[str, Any] = Field(default_factory=dict)
    evaluation_split: Literal["validation", "testing"] = "validation"
    latest_run: ExperimentRunSummary | None = None
    accuracy: float | None = None
    f1_score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExperimentDetail(ExperimentItem):
    runs: list[ExperimentRunSummary] = Field(default_factory=list)


class ExperimentList(BaseModel):
    items: list[ExperimentItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: dict[str, int] = Field(default_factory=dict)


class ExperimentSummary(BaseModel):
    total: int
    draft: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


class ExperimentCompare(BaseModel):
    experiment_ids: list[UUID] = Field(min_length=2, max_length=5)


class ExperimentComparisonItem(BaseModel):
    experiment_id: UUID
    code: str
    name: str
    model_name: str
    algorithm: str
    model_version: int
    dataset_name: str
    dataset_version: int
    evaluation_split: str
    sample_count: int
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    accuracy: float | None = None


class ExperimentComparison(BaseModel):
    items: list[ExperimentComparisonItem]


class ExperimentModelOption(BaseModel):
    id: UUID
    name: str
    algorithm: str
    hyperparameters: dict[str, Any] = Field(default_factory=dict)


class PreprocessingOption(BaseModel):
    preprocessing_run_id: UUID
    dataset_version_id: UUID
    dataset_id: UUID
    dataset_name: str
    dataset_version_name: str
    dataset_version_number: int
    sample_count: int
    feature_count: int
    features: list[str]
    training_count: int
    validation_count: int
    testing_count: int


class ExperimentOptions(BaseModel):
    models: list[ExperimentModelOption]
    preprocessing_runs: list[PreprocessingOption]
    feature_types: list[str]


class ExperimentEvaluationResult(BaseModel):
    id: UUID
    status: str
    split: str
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    sample_count: int = 0
    error_message: str | None = None


class ExperimentTrainingResult(BaseModel):
    id: UUID
    status: str
    progress_percent: int
    error_message: str | None = None
    created_at: datetime | None = None


class ExperimentRunDetail(ExperimentRunSummary):
    experiment_id: UUID
    experiment_code: str
    experiment_name: str
    training_run: ExperimentTrainingResult | None = None
    evaluation: ExperimentEvaluationResult | None = None


class ExperimentLogs(BaseModel):
    items: list[dict[str, Any]]
