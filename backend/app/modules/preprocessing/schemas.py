"""API schemas for the preprocessing pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PreprocessingStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
]

MissingValueStrategy = Literal[
    "mean",
    "median",
    "most_frequent",
    "constant",
    "drop",
]

ScalingStrategy = Literal[
    "none",
    "standard",
    "minmax",
]

DatasetSplit = Literal[
    "training",
    "validation",
    "testing",
]


class PreprocessingConfigRequest(BaseModel):
    """Configuration supplied when creating a preprocessing run."""

    model_config = ConfigDict(extra="forbid")

    feature_order: list[str] = Field(
        default_factory=lambda: [f"F{i}" for i in range(1, 13)],
        min_length=1,
        description="Ordered feature names to include in preprocessing.",
    )

    missing_value_strategy: MissingValueStrategy = Field(
        default="median",
        description="Strategy used to handle missing feature values.",
    )

    missing_value_constant: Any | None = Field(
        default=None,
        description="Replacement value when the constant strategy is selected.",
    )

    scaling_strategy: ScalingStrategy = Field(
        default="standard",
        description="Scaling method applied to selected numeric features.",
    )

    scaling_features: list[str] | None = Field(
        default=None,
        description="Features to scale. Defaults to eligible numeric features.",
    )

    check_duplicates: bool = Field(
        default=True,
        description="Whether duplicate samples should be checked.",
    )

    @field_validator("feature_order")
    @classmethod
    def validate_feature_order(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one feature must be selected.")

        if len(value) != len(set(value)):
            raise ValueError("Feature order must not contain duplicates.")

        return value

    @field_validator("scaling_features")
    @classmethod
    def validate_scaling_features(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("Scaling features must not contain duplicates.")

        return value

    @model_validator(mode="after")
    def validate_scaling_configuration(self) -> "PreprocessingConfigRequest":
        if self.scaling_features is not None:
            unknown = set(self.scaling_features) - set(self.feature_order)
            if unknown:
                raise ValueError(
                    f"Scaling features are not in feature_order: "
                    f"{sorted(unknown)}"
                )

        if self.scaling_strategy == "none" and self.scaling_features:
            raise ValueError(
                "scaling_features must be empty when scaling_strategy is 'none'."
            )

        return self


class DatasetSplitInfoResponse(BaseModel):
    """Read-only split information from a validated dataset version."""

    model_config = ConfigDict(from_attributes=True)

    training_percentage: float = Field(ge=0, le=100)
    validation_percentage: float = Field(ge=0, le=100)
    testing_percentage: float = Field(ge=0, le=100)

    training_count: int = Field(default=0, ge=0)
    validation_count: int = Field(default=0, ge=0)
    testing_count: int = Field(default=0, ge=0)

    random_seed: int | None = None
    stratified: bool = False

    @model_validator(mode="after")
    def validate_percentages(self) -> "DatasetSplitInfoResponse":
        total = (
            self.training_percentage
            + self.validation_percentage
            + self.testing_percentage
        )

        if abs(total - 100.0) > 0.01:
            raise ValueError("Dataset split percentages must total 100.")

        return self


class DatasetVersionSelectionResponse(BaseModel):
    """Dataset version eligible for preprocessing."""

    model_config = ConfigDict(from_attributes=True)

    dataset_version_id: UUID
    dataset_id: UUID | None = None
    version_number: int = Field(ge=1)
    name: str
    status: str
    validation_passed: bool
    sample_count: int = Field(ge=0)
    feature_schema: dict[str, Any] = Field(default_factory=dict)
    split: DatasetSplitInfoResponse


class PreprocessingArtifactResponse(BaseModel):
    """Metadata for a generated preprocessing artifact."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    preprocessing_run_id: UUID
    artifact_type: str
    filename: str
    media_type: str | None = None
    size_bytes: int = Field(default=0, ge=0)
    checksum_sha256: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PreprocessingRunCreateRequest(BaseModel):
    """Request to create a preprocessing run."""

    model_config = ConfigDict(extra="forbid")

    dataset_version_id: UUID
    config: PreprocessingConfigRequest = Field(
        default_factory=PreprocessingConfigRequest
    )


class PreprocessingRunResponse(BaseModel):
    """Preprocessing run details returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_version_id: UUID

    # Display details resolved from the dataset version.
    dataset_id: UUID | None = None
    dataset_name: str | None = None
    dataset_version_number: int | str | None = None
    dataset_version_name: str | None = None

    status: PreprocessingStatus

    config_snapshot: dict[str, Any] = Field(default_factory=dict)

    input_sample_count: int = Field(default=0, ge=0)
    output_sample_count: int = Field(default=0, ge=0)

    training_count: int = Field(default=0, ge=0)
    validation_count: int = Field(default=0, ge=0)
    testing_count: int = Field(default=0, ge=0)

    feature_count: int = Field(default=0, ge=0)
    duration_ms: int | None = Field(default=None, ge=0)

    error_code: str | None = None
    error_message: str | None = None

    result_summary: dict[str, Any] = Field(default_factory=dict)

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    artifacts: list[PreprocessingArtifactResponse] = Field(
        default_factory=list
    )


class PreprocessingRunListResponse(BaseModel):
    """Paginated preprocessing run history."""

    items: list[PreprocessingRunResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class PreprocessingRunListQuery(BaseModel):
    """Validated query parameters for listing preprocessing runs."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=30, ge=1, le=100)
    dataset_id: UUID | None = None
    dataset_version_id: UUID | None = None
    status: PreprocessingStatus | None = None


class PreprocessingRunResultResponse(BaseModel):
    """Summary of a completed preprocessing run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    status: PreprocessingStatus
    input_sample_count: int = Field(ge=0)
    output_sample_count: int = Field(ge=0)

    training_count: int = Field(ge=0)
    validation_count: int = Field(ge=0)
    testing_count: int = Field(ge=0)

    feature_count: int = Field(ge=0)
    duration_ms: int | None = Field(default=None, ge=0)

    result_summary: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[PreprocessingArtifactResponse] = Field(
        default_factory=list
    )


class PreprocessingErrorResponse(BaseModel):
    """Standard error response for preprocessing operations."""

    code: str
    message: str
    stage: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)