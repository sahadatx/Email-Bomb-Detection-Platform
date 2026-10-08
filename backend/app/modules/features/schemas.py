from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.features.models import FeatureExtractionStatus


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100

TOTAL_FEATURES = 12


# ============================================================
# PUBLIC STATUS VALUES
# ============================================================

PUBLIC_FEATURE_STATUSES: tuple[str, ...] = (
    "pending",
    "extracted",
    "warning",
    "failed",
)


# ============================================================
# WORKSPACE FILTER VALUES
# ============================================================

FEATURE_SOURCE_VALUES: tuple[str, ...] = (
    "file_upload",
    "raw_email",
)

FEATURE_LEVEL_VALUES: tuple[str, ...] = (
    "normal",
    "bombing",
)


# ============================================================
# TYPE ALIASES
# ============================================================

FeatureSource = Literal[
    "file_upload",
    "raw_email",
]

FeatureLevel = Literal[
    "normal",
    "bombing",
]

FeaturePublicStatus = Literal[
    "pending",
    "extracted",
    "warning",
    "failed",
]


# ============================================================
# PAGINATION
# ============================================================

class FeaturePagination(BaseModel):
    """
    Pagination metadata for the Feature Workspace.

    `total` represents the number of records after all active
    workspace filters have been applied.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    page: int = Field(
        ge=1,
        description="Current page number.",
    )

    page_size: int = Field(
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of records requested per page.",
    )

    total: int = Field(
        ge=0,
        description="Total records matching active filters.",
    )

    total_pages: int = Field(
        ge=0,
        description="Total number of available pages.",
    )

    has_previous: bool = Field(
        description="Whether a previous page exists.",
    )

    has_next: bool = Field(
        description="Whether a next page exists.",
    )


# ============================================================
# FEATURE WORKSPACE FILTERS
# ============================================================

class FeatureWorkspaceFilters(BaseModel):
    """
    Canonical filter contract for Module 04 Feature Workspace.

    Supported filters:

        Search
        Source
        Level
        Status
        From
        To

    Search fields:

        - Subject
        - Sender
        - Message-ID
        - Source Identifier

    All populated filters use AND semantics.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    search: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Search subject, sender, Message-ID, "
            "or source identifier."
        ),
    )

    source: FeatureSource | None = Field(
        default=None,
        description="Filter by canonical email source.",
    )

    level: FeatureLevel | None = Field(
        default=None,
        description="Filter by dataset ground-truth level.",
    )

    status: FeaturePublicStatus | None = Field(
        default=None,
        description="Filter by feature extraction status.",
    )

    from_date: date | None = Field(
        default=None,
        description=(
            "Inclusive lower date bound for received_at."
        ),
    )

    to_date: date | None = Field(
        default=None,
        description=(
            "Inclusive upper date bound for received_at."
        ),
    )


# ============================================================
# FEATURE SELECTION RESPONSE
# ============================================================

class FeatureSelectionResponse(BaseModel):
    """
    Response used by the Feature Workspace global-selection
    workflow.

    This endpoint resolves selection against the complete
    filtered result set rather than only the current page.

    `total_matching`
        Total emails matching the supplied filters.

    `total_selectable`
        Total emails currently eligible for extraction.

    `email_ids`
        All selectable email UUIDs across the complete filtered
        result set.

    Extracted records are not selectable.

    Selectable records include:

        - pending
        - warning
        - failed
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total_matching: int = Field(
        ge=0,
        description=(
            "Total emails matching the active workspace filters."
        ),
    )

    total_selectable: int = Field(
        ge=0,
        description=(
            "Total matching emails eligible for feature extraction."
        ),
    )

    email_ids: list[UUID] = Field(
        default_factory=list,
        description=(
            "All selectable email IDs across the complete "
            "filtered result set."
        ),
    )

    filters: FeatureWorkspaceFilters = Field(
        default_factory=FeatureWorkspaceFilters,
        description=(
            "Normalized filters used to resolve the selection."
        ),
    )


# ============================================================
# FEATURE VALUE
# ============================================================

class FeatureValue(BaseModel):
    """
    Canonical representation of one F1-F12 feature.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    feature_id: str = Field(
        min_length=2,
        max_length=4,
        pattern=r"^F(?:[1-9]|1[0-2])$",
        description="Canonical feature identifier: F1-F12.",
    )

    feature_name: str = Field(
        min_length=1,
        max_length=255,
        description="Canonical feature name.",
    )

    value: str | int | float | bool | None = Field(
        default=None,
        description="Typed feature value.",
    )

    data_type: str = Field(
        min_length=1,
        max_length=32,
        description="Feature value data type.",
    )

    source: str = Field(
        min_length=1,
        max_length=64,
        description="Feature extraction source.",
    )

    status: str = Field(
        default="valid",
        min_length=1,
        max_length=32,
        description="Validation status of this feature value.",
    )

    description: str | None = Field(
        default=None,
        description="Description of the feature.",
    )

    calculation: str | None = Field(
        default=None,
        description="Calculation or extraction rule.",
    )

    raw_value: Any = Field(
        default=None,
        description="Underlying extracted representation.",
    )

    display_value: str | None = Field(
        default=None,
        description="Frontend-friendly representation.",
    )


# ============================================================
# F1-F12 FEATURE VECTOR
# ============================================================

class FeatureVector(BaseModel):
    """
    Canonical typed F1-F12 feature vector.

    Field names match the persisted EmailFeatures model.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    # F1 — Sender Email
    f1_sender_email: str | None = None

    # F2 — Known Domain Indicator
    f2_known_domain: bool = False

    # F3 — Message-ID Presence
    f3_message_id: bool = False

    # F4 — Auto-Submitted Header
    f4_auto_submitted: bool = False

    # F5 — Precedence Bulk Indicator
    f5_precedence_bulk: bool = False

    # F6 — List-Id Header
    f6_list_id: bool = False

    # F7 — X-BeenThere Header
    f7_x_beenthere: bool = False

    # F8 — X-Anti-Abuse Header
    f8_x_anti_abuse: bool = False

    # F9 — Keyword-Based Content Features
    f9_keyword_features: int = Field(
        default=0,
        ge=0,
    )

    # F10 — Subject Length
    f10_subject_length: int = Field(
        default=0,
        ge=0,
    )

    # F11 — Emails Per Minute
    f11_emails_per_minute: int = Field(
        default=0,
        ge=0,
    )

    # F12 — Emails Per Hour
    f12_emails_per_hour: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# VALIDATION RESULT
# ============================================================

class FeatureValidationResult(BaseModel):
    """Validation information produced during extraction."""

    model_config = ConfigDict(
        extra="forbid",
    )

    errors: list[str] = Field(
        default_factory=list,
        description="Fatal or blocking validation errors.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal extraction warnings.",
    )

    is_valid: bool = Field(
        default=True,
        description="Whether the extracted feature record is valid.",
    )


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

class FeatureDefinitionResponse(BaseModel):
    """Public definition of one canonical F1-F12 feature."""

    model_config = ConfigDict(
        extra="forbid",
    )

    feature_id: str = Field(
        min_length=2,
        max_length=4,
        pattern=r"^F(?:[1-9]|1[0-2])$",
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
    )

    data_type: str = Field(
        min_length=1,
        max_length=32,
    )

    source: str = Field(
        min_length=1,
        max_length=64,
    )

    calculation: str = Field(
        min_length=1,
    )

    missing_value: str = Field(
        min_length=1,
    )

    normalization: str = Field(
        min_length=1,
    )


class FeatureDefinitionListResponse(BaseModel):
    """Response containing the canonical F1-F12 definitions."""

    model_config = ConfigDict(
        extra="forbid",
    )

    definitions: list[FeatureDefinitionResponse]

    total: int = Field(
        ge=0,
    )


# ============================================================
# EMAIL IDENTITY
# ============================================================

class FeatureEmailIdentity(BaseModel):
    """
    Canonical email identity exposed by Module 04.

    Source and level are metadata inherited from the canonical
    Module 02 email record.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    email_id: UUID

    sender: str | None = None

    subject: str | None = None

    message_id: str | None = None

    source: str | None = None

    source_identifier: str | None = None

    level: str | None = None


# ============================================================
# EMAIL TIMESTAMPS
# ============================================================

class FeatureEmailTimestamps(BaseModel):
    """Relevant email, parsing, and feature timestamps."""

    model_config = ConfigDict(
        extra="forbid",
    )

    received_at: datetime | None = None

    collected_at: datetime | None = None

    parsed_at: datetime | None = None

    extracted_at: datetime | None = None


# ============================================================
# EXTRACTION METADATA
# ============================================================

class FeatureExtractionMetadata(BaseModel):
    """Technical metadata describing feature extraction."""

    model_config = ConfigDict(
        extra="forbid",
    )

    extractor_version: str = Field(
        min_length=1,
        max_length=32,
    )

    processing_time_ms: int = Field(
        ge=0,
    )

    status: FeaturePublicStatus

    extracted_at: datetime


# ============================================================
# COMPLETE FEATURE RESPONSE
# ============================================================

class FeatureEmailResponse(BaseModel):
    """
    Complete Feature Engineering response for one email.

    Contains only Feature Engineering information.

    It intentionally contains no:

        - prediction
        - confidence
        - risk score
        - threat classification
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID

    email_id: UUID

    identity: FeatureEmailIdentity

    timestamps: FeatureEmailTimestamps

    feature_vector: FeatureVector

    features: list[FeatureValue]

    validation: FeatureValidationResult

    metadata: FeatureExtractionMetadata


# ============================================================
# FEATURE WORKSPACE LIST ITEM
# ============================================================

class FeatureEmailListItem(BaseModel):
    """
    Lightweight Feature Workspace table row.

    Table contract:

        Select
        Subject
        Sender
        Source
        Level
        Received
        Status
        Action
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    email_id: UUID

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    subject: str | None = None

    sender: str | None = None

    message_id: str | None = None

    # --------------------------------------------------------
    # Source metadata
    # --------------------------------------------------------

    source: str | None = None

    source_identifier: str | None = None

    # --------------------------------------------------------
    # Dataset ground-truth metadata
    # --------------------------------------------------------

    level: str | None = None

    # --------------------------------------------------------
    # Time information
    # --------------------------------------------------------

    received_at: datetime | None = None

    collected_at: datetime | None = None

    parsed_at: datetime | None = None

    # --------------------------------------------------------
    # Module 03 parsing state
    # --------------------------------------------------------

    parsed: bool = False

    # --------------------------------------------------------
    # Module 04 feature state
    # --------------------------------------------------------

    feature_status: FeaturePublicStatus

    feature_count: int = Field(
        ge=0,
        le=TOTAL_FEATURES,
    )

    total_features: int = Field(
        default=TOTAL_FEATURES,
        ge=TOTAL_FEATURES,
    )

    has_features: bool = False

    updated_at: datetime | None = None


class FeatureEmailListResponse(BaseModel):
    """
    Paginated Feature Workspace response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[FeatureEmailListItem]

    pagination: FeaturePagination

    filters: FeatureWorkspaceFilters = Field(
        default_factory=FeatureWorkspaceFilters,
    )


# ============================================================
# FEATURE ENGINEERING SUMMARY
# ============================================================

class FeatureSummary(BaseModel):
    """
    Global Feature Engineering persistence summary.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total_collected: int = Field(
        ge=0,
    )

    total_parsed: int = Field(
        ge=0,
    )

    total_features_ready: int = Field(
        ge=0,
    )

    total_pending: int = Field(
        ge=0,
    )

    total_warnings: int = Field(
        ge=0,
    )

    total_failed: int = Field(
        ge=0,
    )

    readiness_percentage: float = Field(
        ge=0.0,
        le=100.0,
    )


# ============================================================
# EXTRACTION REQUESTS
# ============================================================

class FeatureExtractionRequest(BaseModel):
    """Request to extract features for one email."""

    model_config = ConfigDict(
        extra="forbid",
    )

    force: bool = Field(
        default=False,
        description=(
            "Re-extract features even when a current feature "
            "record already exists."
        ),
    )


class BatchFeatureExtractionRequest(BaseModel):
    """Request to extract features for multiple emails."""

    model_config = ConfigDict(
        extra="forbid",
    )

    email_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
    )

    force: bool = Field(
        default=False,
    )


# ============================================================
# EXTRACTION OPERATION SUMMARY
# ============================================================

class FeatureExtractionOperationSummary(BaseModel):
    """Summary of one feature extraction operation."""

    model_config = ConfigDict(
        extra="forbid",
    )

    selected: int = Field(
        ge=0,
    )

    extracted: int = Field(
        ge=0,
    )

    warnings: int = Field(
        ge=0,
    )

    failed: int = Field(
        ge=0,
    )


class FeatureExtractionResponse(BaseModel):
    """Response after one or more feature extraction operations."""

    model_config = ConfigDict(
        extra="forbid",
    )

    summary: FeatureExtractionOperationSummary

    results: list[FeatureEmailResponse]


# ============================================================
# HEALTH
# ============================================================

class FeatureHealthResponse(BaseModel):
    """Health response for Module 04."""

    model_config = ConfigDict(
        extra="forbid",
    )

    status: str = "healthy"

    module: str = "feature-engineering"

    feature_schema: str = "F1-F12"

    feature_count: int = TOTAL_FEATURES


# ============================================================
# SUMMARY API RESPONSE
# ============================================================

class FeatureSummaryResponse(BaseModel):
    """API response wrapper for the global feature summary."""

    model_config = ConfigDict(
        extra="forbid",
    )

    summary: FeatureSummary


# ============================================================
# TYPE / STATUS HELPERS
# ============================================================

def is_feature_status(
    value: str,
) -> bool:
    """
    Return whether a value is a valid public Feature status.
    """

    if not isinstance(value, str):
        return False

    return value.strip().lower() in PUBLIC_FEATURE_STATUSES


def is_feature_source(
    value: str,
) -> bool:
    """
    Return whether a value is a supported workspace source.
    """

    if not isinstance(value, str):
        return False

    return value.strip().lower() in FEATURE_SOURCE_VALUES


def is_feature_level(
    value: str,
) -> bool:
    """
    Return whether a value is a supported workspace level.
    """

    if not isinstance(value, str):
        return False

    return value.strip().lower() in FEATURE_LEVEL_VALUES


def public_feature_status(
    status: FeatureExtractionStatus | None,
) -> FeaturePublicStatus:
    """
    Convert persistence status into the public API status.

    Missing EmailFeatures:

        pending
    """

    if status is None:
        return "pending"

    value = status.value

    if value not in PUBLIC_FEATURE_STATUSES:
        raise ValueError(
            f"Unsupported feature status: {value}",
        )

    return value  # type: ignore[return-value]


def feature_count_from_vector(
    vector: FeatureVector,
) -> int:
    """
    Return the number of canonical F1-F12 fields represented
    by the vector.
    """

    return len(vector.model_dump())


# ============================================================
# FILTER NORMALIZATION
# ============================================================

def normalize_feature_workspace_filters(
    filters: FeatureWorkspaceFilters,
) -> FeatureWorkspaceFilters:
    """
    Normalize Feature Workspace filters before repository use.

    Rules:

        Search
            strip whitespace
            empty -> None

        Source
            lowercase

        Level
            lowercase

        Status
            lowercase

        Dates
            unchanged
    """

    search = (
        filters.search.strip()
        if (
            filters.search is not None
            and filters.search.strip()
        )
        else None
    )

    source = (
        filters.source.strip().lower()
        if filters.source is not None
        else None
    )

    level = (
        filters.level.strip().lower()
        if filters.level is not None
        else None
    )

    feature_status = (
        filters.status.strip().lower()
        if filters.status is not None
        else None
    )

    if (
        filters.from_date is not None
        and filters.to_date is not None
        and filters.from_date > filters.to_date
    ):
        raise ValueError(
            "from_date cannot be later than to_date.",
        )

    return FeatureWorkspaceFilters(
        search=search,
        source=source,
        level=level,
        status=feature_status,
        from_date=filters.from_date,
        to_date=filters.to_date,
    )