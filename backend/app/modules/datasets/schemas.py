from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100

DEFAULT_TRAINING_PERCENTAGE = 70
DEFAULT_VALIDATION_PERCENTAGE = 15
DEFAULT_TESTING_PERCENTAGE = 15

DEFAULT_RANDOM_SEED = 42

TOTAL_FEATURES = 12
FEATURE_SCHEMA_VERSION = "1.0"
FEATURE_SCHEMA_NAME = "F1-F12"

VALIDATION_POLICY_VERSION = "1.0"


# ============================================================
# LITERALS
# ============================================================

DatasetStatusValue = Literal[
    "active",
    "archived",
]

DatasetVersionStatusValue = Literal[
    "creating",
    "ready",
    "validated",
    "invalid",
]

DatasetSplitValue = Literal[
    "train",
    "validation",
    "test",
]

GroundTruthValue = Literal[
    "normal",
    "bombing",
]

DatasetSourceValue = Literal[
    "file_upload",
    "raw_email",
]

ExportFormatValue = Literal[
    "csv",
    "json",
]

ExportSplitValue = Literal[
    "all",
    "train",
    "validation",
    "test",
]

ValidationSeverityValue = Literal[
    "error",
    "warning",
    "info",
]

ValidationRunStatusValue = Literal[
    "running",
    "completed",
    "failed",
]

ValidationOverallStatusValue = Literal[
    "passed",
    "warning",
    "failed",
]

DatasetSortValue = Literal[
    "newest",
    "oldest",
    "name_asc",
    "name_desc",
]


# ============================================================
# BASE MODEL
# ============================================================

class DatasetBaseModel(BaseModel):
    """Common configuration for Dataset API schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ============================================================
# FEATURE SCHEMA
# ============================================================

class DatasetFeatureDefinition(DatasetBaseModel):
    """Definition of one canonical dataset feature."""

    feature_id: str = Field(
        ...,
        pattern=r"^F(?:[1-9]|1[0-2])$",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    data_type: str = Field(
        ...,
        min_length=1,
        max_length=64,
    )


class DatasetFeatureSchema(DatasetBaseModel):
    """Canonical F1-F12 feature metadata."""

    version: str = Field(
        default=FEATURE_SCHEMA_VERSION,
        min_length=1,
        max_length=64,
    )
    name: str = Field(
        default=FEATURE_SCHEMA_NAME,
        min_length=1,
        max_length=64,
    )
    feature_count: int = Field(
        default=TOTAL_FEATURES,
        ge=TOTAL_FEATURES,
        le=TOTAL_FEATURES,
    )
    features: list[DatasetFeatureDefinition] = Field(
        default_factory=list,
    )

    @field_validator("features")
    @classmethod
    def validate_features(
        cls,
        value: list[DatasetFeatureDefinition],
    ) -> list[DatasetFeatureDefinition]:
        if not value:
            return value

        if len(value) != TOTAL_FEATURES:
            raise ValueError(
                "Dataset feature schema must contain exactly "
                "12 features (F1-F12)."
            )

        expected = [
            f"F{index}"
            for index in range(1, TOTAL_FEATURES + 1)
        ]
        actual = [
            feature.feature_id
            for feature in value
        ]

        if actual != expected:
            raise ValueError(
                "Dataset feature schema must contain "
                "F1-F12 in canonical order."
            )

        return value


# ============================================================
# WORKSPACE FILTERS
# ============================================================

class DatasetWorkspaceFilters(DatasetBaseModel):
    """Workspace filters with AND semantics."""

    search: str | None = Field(
        default=None,
        max_length=500,
    )
    ground_truth: GroundTruthValue | None = None
    source: DatasetSourceValue | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None

    @field_validator("search")
    @classmethod
    def normalize_search(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    @model_validator(mode="after")
    def validate_date_range(
        self,
    ) -> DatasetWorkspaceFilters:
        if (
            self.from_date is not None
            and self.to_date is not None
            and self.to_date < self.from_date
        ):
            raise ValueError(
                "to_date must be greater than or equal to "
                "from_date."
            )

        return self


# ============================================================
# PAGINATION
# ============================================================

class DatasetPagination(DatasetBaseModel):
    """Standard pagination metadata."""

    page: int = Field(
        default=DEFAULT_PAGE,
        ge=1,
    )
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
    )
    total: int = Field(
        default=0,
        ge=0,
    )
    total_pages: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# DATASET CREATE
# ============================================================

class DatasetCreateRequest(DatasetBaseModel):
    """Create a dataset from selected eligible emails."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    email_ids: list[UUID] = Field(
        ...,
        min_length=1,
    )
    feature_schema: DatasetFeatureSchema = Field(
        default_factory=DatasetFeatureSchema,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Dataset name cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    @field_validator("email_ids")
    @classmethod
    def validate_email_ids(
        cls,
        value: list[UUID],
    ) -> list[UUID]:
        if not value:
            raise ValueError(
                "At least one email must be selected."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Duplicate email IDs are not allowed."
            )

        return value


DatasetCreate = DatasetCreateRequest


# ============================================================
# DATASET UPDATE
# ============================================================

class DatasetUpdateRequest(DatasetBaseModel):
    """Update dataset metadata only."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Dataset name cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    @model_validator(mode="after")
    def validate_update_fields(
        self,
    ) -> DatasetUpdateRequest:
        if not self.model_fields_set:
            raise ValueError(
                "At least one field must be provided "
                "for dataset update."
            )

        return self


# ============================================================
# DATASET EMAIL ADD
# ============================================================

class DatasetEmailAddRequest(DatasetBaseModel):
    """Add eligible emails to an existing dataset."""

    email_ids: list[UUID] = Field(
        ...,
        min_length=1,
    )

    @field_validator("email_ids")
    @classmethod
    def validate_email_ids(
        cls,
        value: list[UUID],
    ) -> list[UUID]:
        if not value:
            raise ValueError(
                "At least one email must be selected."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Duplicate email IDs are not allowed."
            )

        return value


# ============================================================
# DATASET EMAIL REMOVE
# ============================================================

class DatasetEmailRemoveRequest(DatasetBaseModel):
    """Remove dataset memberships without modifying emails."""

    email_ids: list[UUID] = Field(
        ...,
        min_length=1,
    )

    @field_validator("email_ids")
    @classmethod
    def validate_email_ids(
        cls,
        value: list[UUID],
    ) -> list[UUID]:
        if not value:
            raise ValueError(
                "At least one email must be selected."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Duplicate email IDs are not allowed."
            )

        return value


# ============================================================
# DATASET SUMMARY
# ============================================================

class DatasetSummary(DatasetBaseModel):
    """Dataset Workspace summary counters."""

    dataset_emails: int = Field(
        default=0,
        ge=0,
    )
    normal: int = Field(
        default=0,
        ge=0,
    )
    bombing: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# DATASET LIST
# ============================================================

class DatasetListItem(DatasetBaseModel):
    """One dataset list row."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID
    name: str
    description: str | None = None
    status: DatasetStatusValue
    sample_count: int = Field(ge=0)
    normal_count: int = Field(ge=0)
    bombing_count: int = Field(ge=0)
    version_count: int = Field(
        default=0,
        ge=0,
    )
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(DatasetBaseModel):
    """Paginated dataset list."""

    items: list[DatasetListItem]
    pagination: DatasetPagination


# ============================================================
# DATASET DETAIL
# ============================================================

class DatasetDetailResponse(DatasetBaseModel):
    """Complete dataset representation."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID
    name: str
    description: str | None = None
    status: DatasetStatusValue
    sample_count: int = Field(ge=0)
    normal_count: int = Field(ge=0)
    bombing_count: int = Field(ge=0)
    feature_schema: DatasetFeatureSchema
    version_count: int = Field(
        default=0,
        ge=0,
    )
    created_at: datetime
    updated_at: datetime


# ============================================================
# EMAIL IDENTITY
# ============================================================

class DatasetEmailIdentity(DatasetBaseModel):
    """Email identity displayed in the details drawer."""

    email_id: UUID
    subject: str | None = None
    sender: str | None = None
    message_id: str | None = None
    source: DatasetSourceValue
    source_identifier: str | None = None
    ground_truth: GroundTruthValue


# ============================================================
# DATASET EMAIL LIST
# ============================================================

class DatasetEmailListItem(DatasetBaseModel):
    """One email row belonging to a dataset."""

    email_id: UUID
    subject: str | None = None
    sender: str | None = None
    message_id: str | None = None
    source: DatasetSourceValue
    source_identifier: str | None = None
    ground_truth: GroundTruthValue


class DatasetEmailListResponse(DatasetBaseModel):
    """Paginated dataset email list."""

    items: list[DatasetEmailListItem]
    pagination: DatasetPagination
    dataset_id: UUID


# ============================================================
# DATASET EMAIL ADD RESPONSE
# ============================================================

class DatasetEmailAddResponse(DatasetBaseModel):
    """Result of adding emails to a dataset."""

    success: bool = True
    message: str
    dataset_id: UUID
    added_count: int = Field(
        default=0,
        ge=0,
    )
    skipped_count: int = Field(
        default=0,
        ge=0,
    )
    sample_count: int = Field(
        default=0,
        ge=0,
    )
    normal_count: int = Field(
        default=0,
        ge=0,
    )
    bombing_count: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# DATASET EMAIL REMOVE RESPONSE
# ============================================================

class DatasetEmailRemoveResponse(DatasetBaseModel):
    """Result of removing emails from a dataset."""

    success: bool = True
    message: str
    dataset_id: UUID
    removed_count: int = Field(
        default=0,
        ge=0,
    )
    sample_count: int = Field(
        default=0,
        ge=0,
    )
    normal_count: int = Field(
        default=0,
        ge=0,
    )
    bombing_count: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# EMAIL TIME INFORMATION
# ============================================================

class DatasetEmailTimeInformation(DatasetBaseModel):
    """Email lifecycle timestamps."""

    received_at: datetime | None = None
    collected_at: datetime | None = None
    parsed_at: datetime | None = None
    extracted_at: datetime | None = None


# ============================================================
# FEATURE VECTOR
# ============================================================

class DatasetFeatureVector(DatasetBaseModel):
    """Canonical F1-F12 values from feature extraction."""

    f1_sender_email: str | None = None
    f2_known_domain: bool
    f3_message_id: bool
    f4_auto_submitted: bool
    f5_precedence_bulk: bool
    f6_list_id: bool
    f7_x_beenthere: bool
    f8_x_anti_abuse: bool
    f9_keyword_features: int = Field(ge=0)
    f10_subject_length: int = Field(ge=0)
    f11_emails_per_minute: int = Field(ge=0)
    f12_emails_per_hour: int = Field(ge=0)


# ============================================================
# WORKSPACE
# ============================================================

class DatasetWorkspaceItem(DatasetBaseModel):
    """One eligible email in the dataset workspace."""

    email_id: UUID
    subject: str | None = None
    sender: str | None = None
    ground_truth: GroundTruthValue
    source: DatasetSourceValue
    received_at: datetime | None = None


class DatasetWorkspaceResponse(DatasetBaseModel):
    """Paginated workspace response."""

    items: list[DatasetWorkspaceItem]
    pagination: DatasetPagination
    filters: DatasetWorkspaceFilters
    summary: DatasetSummary


# ============================================================
# EMAIL DETAIL
# ============================================================

class DatasetEmailDetailResponse(DatasetBaseModel):
    """Email details drawer response."""

    identity: DatasetEmailIdentity
    time: DatasetEmailTimeInformation
    feature_vector: DatasetFeatureVector
    feature_schema: DatasetFeatureSchema


# ============================================================
# SELECTION
# ============================================================

class DatasetSelectionRequest(DatasetBaseModel):
    """Resolve a filtered selection across the full result set."""

    filters: DatasetWorkspaceFilters = Field(
        default_factory=DatasetWorkspaceFilters,
    )


class DatasetSelectionResponse(DatasetBaseModel):
    """Complete filtered selection response."""

    total_matching: int = Field(
        default=0,
        ge=0,
    )
    total_selectable: int = Field(
        default=0,
        ge=0,
    )
    email_ids: list[UUID] = Field(
        default_factory=list,
    )
    filters: DatasetWorkspaceFilters


# ============================================================
# SPLIT CONFIGURATION
# ============================================================

class DatasetSplitConfiguration(DatasetBaseModel):
    """Train/validation/test split configuration."""

    training_percentage: int = Field(
        default=DEFAULT_TRAINING_PERCENTAGE,
        ge=0,
        le=100,
    )
    validation_percentage: int = Field(
        default=DEFAULT_VALIDATION_PERCENTAGE,
        ge=0,
        le=100,
    )
    testing_percentage: int = Field(
        default=DEFAULT_TESTING_PERCENTAGE,
        ge=0,
        le=100,
    )
    random_seed: int = Field(
        default=DEFAULT_RANDOM_SEED,
        ge=0,
    )
    stratified: bool = True

    @property
    def total_percentage(self) -> int:
        return (
            self.training_percentage
            + self.validation_percentage
            + self.testing_percentage
        )

    @model_validator(mode="after")
    def validate_total_percentage(
        self,
    ) -> DatasetSplitConfiguration:
        if self.total_percentage != 100:
            raise ValueError(
                "Training, validation, and testing percentages "
                "must sum to exactly 100%."
            )

        return self


# ============================================================
# VERSION CREATE
# ============================================================

class DatasetVersionCreateRequest(DatasetBaseModel):
    """Create an immutable dataset version."""

    dataset_id: UUID
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    split: DatasetSplitConfiguration = Field(
        default_factory=DatasetSplitConfiguration,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Version name cannot be empty."
            )

        return value


DatasetVersionCreate = DatasetVersionCreateRequest
DatasetVersionRequest = DatasetVersionCreateRequest


# ============================================================
# SPLIT COUNTS
# ============================================================

class DatasetSplitCounts(DatasetBaseModel):
    """Resulting version split population."""

    training: int = Field(
        default=0,
        ge=0,
    )
    validation: int = Field(
        default=0,
        ge=0,
    )
    testing: int = Field(
        default=0,
        ge=0,
    )
    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# VERSION LIST
# ============================================================

class DatasetVersionListItem(DatasetBaseModel):
    """One dataset version list row."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID
    dataset_id: UUID
    version_number: int = Field(ge=1)
    name: str
    status: DatasetVersionStatusValue
    sample_count: int = Field(ge=0)
    normal_count: int = Field(ge=0)
    bombing_count: int = Field(ge=0)
    training_percentage: int = Field(
        ge=0,
        le=100,
    )
    validation_percentage: int = Field(
        ge=0,
        le=100,
    )
    testing_percentage: int = Field(
        ge=0,
        le=100,
    )
    created_at: datetime


class DatasetVersionListResponse(DatasetBaseModel):
    """Paginated dataset version list."""

    items: list[DatasetVersionListItem]
    pagination: DatasetPagination


# ============================================================
# VERSION DETAIL
# ============================================================

class DatasetVersionDetailResponse(DatasetBaseModel):
    """Complete dataset version representation."""

    id: UUID
    dataset_id: UUID
    version_number: int
    name: str
    status: DatasetVersionStatusValue
    sample_count: int
    normal_count: int
    bombing_count: int
    split: DatasetSplitConfiguration
    split_counts: DatasetSplitCounts
    validation_passed: bool
    validation_summary: dict[str, Any] | None = None
    feature_schema: DatasetFeatureSchema
    created_at: datetime
    validated_at: datetime | None = None


# ============================================================
# VALIDATION REQUEST
# ============================================================

class DatasetValidationRequest(DatasetBaseModel):
    """Validate one immutable dataset version."""

    dataset_id: UUID
    version_id: UUID


# ============================================================
# VALIDATION CHECK
# ============================================================

class DatasetValidationCheck(DatasetBaseModel):
    """Result of one validation check."""

    code: str
    name: str
    passed: bool
    severity: ValidationSeverityValue = "info"
    affected_samples: int = Field(
        default=0,
        ge=0,
    )
    message: str | None = None
    details: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================
# VALIDATION ISSUE
# ============================================================

class DatasetValidationIssue(DatasetBaseModel):
    """Persisted validation issue with affected records."""

    id: UUID | None = None
    validation_run_id: UUID | None = None
    check_code: str
    check_name: str
    severity: ValidationSeverityValue
    title: str
    details: str
    affected_count: int = Field(
        default=0,
        ge=0,
    )
    affected_email_ids: list[UUID] = Field(
        default_factory=list,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
    created_at: datetime | None = None


# ============================================================
# VALIDATION SUMMARY
# ============================================================

class DatasetValidationSummary(DatasetBaseModel):
    """Aggregated validation counts and overall status."""

    total_samples: int = Field(
        default=0,
        ge=0,
    )
    normal_samples: int = Field(
        default=0,
        ge=0,
    )
    bombing_samples: int = Field(
        default=0,
        ge=0,
    )

    total_checks: int = Field(
        default=0,
        ge=0,
    )
    passed_checks: int = Field(
        default=0,
        ge=0,
    )
    warning_checks: int = Field(
        default=0,
        ge=0,
    )
    failed_checks: int = Field(
        default=0,
        ge=0,
    )

    errors: int = Field(
        default=0,
        ge=0,
    )
    warnings: int = Field(
        default=0,
        ge=0,
    )

    overall_status: ValidationOverallStatusValue = "passed"


# ============================================================
# VALIDATION RUN RESPONSE
# ============================================================

class DatasetValidationRunResponse(DatasetBaseModel):
    """Persisted validation run metadata and results."""

    id: UUID
    dataset_id: UUID
    version_id: UUID

    status: ValidationRunStatusValue
    overall_status: ValidationOverallStatusValue | None = None

    total_samples: int = Field(
        default=0,
        ge=0,
    )
    error_count: int = Field(
        default=0,
        ge=0,
    )
    warning_count: int = Field(
        default=0,
        ge=0,
    )

    passed_checks: int = Field(
        default=0,
        ge=0,
    )
    warning_checks: int = Field(
        default=0,
        ge=0,
    )
    failed_checks: int = Field(
        default=0,
        ge=0,
    )

    summary: dict[str, Any] = Field(
        default_factory=dict,
    )
    policy_version: str = VALIDATION_POLICY_VERSION

    started_at: datetime
    completed_at: datetime | None = None


# ============================================================
# VALIDATION RESULT RESPONSE
# ============================================================

class DatasetValidationResponse(DatasetBaseModel):
    """Complete validation result for a dataset version."""

    dataset_id: UUID
    version_id: UUID
    run: DatasetValidationRunResponse

    summary: DatasetValidationSummary
    checks: list[DatasetValidationCheck] = Field(
        default_factory=list,
    )
    issues: list[DatasetValidationIssue] = Field(
        default_factory=list,
    )


# ============================================================
# VALIDATION HISTORY
# ============================================================

class DatasetValidationHistoryResponse(DatasetBaseModel):
    """Paginated validation run history for one version."""

    dataset_id: UUID
    version_id: UUID
    items: list[DatasetValidationRunResponse] = Field(
        default_factory=list,
    )
    pagination: DatasetPagination


# ============================================================
# VALIDATION ISSUE LIST
# ============================================================

class DatasetValidationIssueListResponse(DatasetBaseModel):
    """Paginated issues belonging to one validation run."""

    validation_run_id: UUID
    items: list[DatasetValidationIssue] = Field(
        default_factory=list,
    )
    pagination: DatasetPagination


# ============================================================
# VALIDATION REPORT
# ============================================================

class DatasetValidationReportResponse(DatasetBaseModel):
    """Validation report metadata."""

    dataset_id: UUID
    version_id: UUID
    validation_run_id: UUID
    filename: str
    content_type: str
    generated_at: datetime


# ============================================================
# LEGACY VALIDATION ISSUE
# ============================================================

class DatasetValidationLegacyIssue(DatasetBaseModel):
    """Compatibility schema for the previous validation contract."""

    code: str
    severity: ValidationSeverityValue
    message: str
    affected_samples: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# EXPORT
# ============================================================

class DatasetExportRequest(DatasetBaseModel):
    """Dataset export request."""

    dataset_version_id: UUID
    format: ExportFormatValue = "csv"
    split: ExportSplitValue = "all"


class DatasetExportResponse(DatasetBaseModel):
    """Dataset export metadata."""

    dataset_version_id: UUID
    format: ExportFormatValue
    split: ExportSplitValue
    sample_count: int = Field(ge=0)
    filename: str
    content_type: str


# ============================================================
# COMMON OPERATION RESPONSE
# ============================================================

class DatasetOperationResponse(DatasetBaseModel):
    """Generic dataset operation response."""

    success: bool = True
    message: str
    dataset_id: UUID | None = None
    version_id: UUID | None = None


# ============================================================
# HEALTH
# ============================================================

class DatasetHealthResponse(DatasetBaseModel):
    """Dataset Management health response."""

    module: str = "dataset-management"
    status: Literal[
        "ok",
        "degraded",
        "error",
    ] = "ok"
    feature_schema: str = FEATURE_SCHEMA_NAME

    export_formats: list[ExportFormatValue] = Field(
        default_factory=lambda: [
            "csv",
            "json",
        ],
    )
    splits: list[ExportSplitValue] = Field(
        default_factory=lambda: [
            "all",
            "train",
            "validation",
            "test",
        ],
    )


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_dataset_workspace_filters(
    filters: DatasetWorkspaceFilters | None,
) -> DatasetWorkspaceFilters:
    """Normalize optional workspace filters."""

    if filters is None:
        return DatasetWorkspaceFilters()

    return filters


def validate_split_percentages(
    split: DatasetSplitConfiguration,
) -> DatasetSplitConfiguration:
    """Validate split percentages and return the configuration."""

    if split.total_percentage != 100:
        raise ValueError(
            "Training, validation, and testing percentages "
            "must sum to exactly 100%."
        )

    return split


def normalize_dataset_create_request(
    request: DatasetCreateRequest,
) -> DatasetCreateRequest:
    """Stable service-layer contract for dataset creation."""

    return request


def normalize_dataset_update_request(
    request: DatasetUpdateRequest,
) -> DatasetUpdateRequest:
    """Stable service-layer contract for dataset updates."""

    return request


def normalize_dataset_version_request(
    request: DatasetVersionCreateRequest,
) -> DatasetVersionCreateRequest:
    """Stable service-layer contract for version creation."""

    validate_split_percentages(request.split)
    return request


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # Constants
    "DEFAULT_PAGE",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_TRAINING_PERCENTAGE",
    "DEFAULT_VALIDATION_PERCENTAGE",
    "DEFAULT_TESTING_PERCENTAGE",
    "DEFAULT_RANDOM_SEED",
    "TOTAL_FEATURES",
    "FEATURE_SCHEMA_VERSION",
    "FEATURE_SCHEMA_NAME",
    "VALIDATION_POLICY_VERSION",

    # Literals
    "DatasetStatusValue",
    "DatasetVersionStatusValue",
    "DatasetSplitValue",
    "GroundTruthValue",
    "DatasetSourceValue",
    "ExportFormatValue",
    "ExportSplitValue",
    "ValidationSeverityValue",
    "ValidationRunStatusValue",
    "ValidationOverallStatusValue",
    "DatasetSortValue",

    # Base and feature schemas
    "DatasetBaseModel",
    "DatasetFeatureDefinition",
    "DatasetFeatureSchema",

    # Filters and pagination
    "DatasetWorkspaceFilters",
    "DatasetPagination",

    # Dataset
    "DatasetCreateRequest",
    "DatasetCreate",
    "DatasetUpdateRequest",
    "DatasetSummary",
    "DatasetListItem",
    "DatasetListResponse",
    "DatasetDetailResponse",

    # Dataset email management
    "DatasetEmailAddRequest",
    "DatasetEmailRemoveRequest",
    "DatasetEmailListItem",
    "DatasetEmailListResponse",
    "DatasetEmailAddResponse",
    "DatasetEmailRemoveResponse",

    # Email and features
    "DatasetEmailIdentity",
    "DatasetEmailTimeInformation",
    "DatasetFeatureVector",
    "DatasetWorkspaceItem",
    "DatasetWorkspaceResponse",
    "DatasetEmailDetailResponse",

    # Selection
    "DatasetSelectionRequest",
    "DatasetSelectionResponse",

    # Version and split
    "DatasetSplitConfiguration",
    "DatasetVersionCreateRequest",
    "DatasetVersionCreate",
    "DatasetVersionRequest",
    "DatasetSplitCounts",
    "DatasetVersionListItem",
    "DatasetVersionListResponse",
    "DatasetVersionDetailResponse",

    # Validation
    "DatasetValidationRequest",
    "DatasetValidationCheck",
    "DatasetValidationIssue",
    "DatasetValidationSummary",
    "DatasetValidationRunResponse",
    "DatasetValidationResponse",
    "DatasetValidationHistoryResponse",
    "DatasetValidationIssueListResponse",
    "DatasetValidationReportResponse",
    "DatasetValidationLegacyIssue",

    # Export
    "DatasetExportRequest",
    "DatasetExportResponse",

    # Common
    "DatasetOperationResponse",
    "DatasetHealthResponse",

    # Helpers
    "normalize_dataset_workspace_filters",
    "validate_split_percentages",
    "normalize_dataset_create_request",
    "normalize_dataset_update_request",
    "normalize_dataset_version_request",
]