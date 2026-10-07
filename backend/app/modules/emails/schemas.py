from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    EmailGroundTruthLabel,
    EmailSource,
    EmailStatus,
)


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================================
# PAGINATION
# ============================================================================

class PaginationMetadata(BaseModel):
    """
    Standard pagination metadata for email-management APIs.
    """

    page: int = Field(
        default=1,
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
        default=1,
        ge=1,
    )

    start_index: int = Field(
        default=0,
        ge=0,
    )

    end_index: int = Field(
        default=0,
        ge=0,
    )


# ============================================================================
# EMAIL INGESTION
# ============================================================================

class EmailIngestRequest(BaseModel):
    """
    Request for ingesting a single raw email.

    Raw Email ingestion always uses RAW_EMAIL as its source.

    A ground-truth label is mandatory because Module 02 follows
    a controlled labeled-email ingestion workflow.
    """

    source_identifier: str | None = Field(
        default=None,
        max_length=512,
    )

    ground_truth_label: EmailGroundTruthLabel

    raw_content: str = Field(
        min_length=1,
    )


class EmailUploadBatchMetadata(BaseModel):
    """
    Metadata describing one .EML upload batch.

    All files in one batch receive the same ground-truth label.
    """

    ground_truth_label: EmailGroundTruthLabel


class EmailUploadResult(BaseModel):
    """
    Result for a single uploaded .EML file.
    """

    filename: str

    email_id: UUID | None = None

    source: EmailSource = EmailSource.FILE_UPLOAD

    ground_truth_label: EmailGroundTruthLabel

    status: EmailStatus

    duplicate: bool = False

    error: str | None = None


class EmailBulkUploadResponse(BaseModel):
    """
    Result returned after a multiple-.EML upload operation.
    """

    total_files: int = Field(
        ge=0,
    )

    successful: int = Field(
        ge=0,
    )

    duplicates: int = Field(
        ge=0,
    )

    failed: int = Field(
        ge=0,
    )

    items: list[EmailUploadResult]


# ============================================================================
# EMAIL FILTERS
# ============================================================================

class EmailListFilters(BaseModel):
    """
    Filters supported by the Email Management page.

    Every filter is optional.

    Frontend behavior:
        Changing any filter triggers an immediate filtered request.

    No explicit Apply Filters operation is required.
    """

    search: str | None = Field(
        default=None,
        max_length=512,
    )

    source: EmailSource | None = None

    status: EmailGroundTruthLabel | None = None

    from_date: datetime | None = None

    to_date: datetime | None = None


# ============================================================================
# EMAIL LIST QUERY
# ============================================================================

class EmailListQuery(EmailListFilters):
    """
    Complete query contract for the paginated Email Management list.
    """

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
    )


# ============================================================================
# EMAIL RESPONSE
# ============================================================================

class EmailResponse(BaseModel):
    """
    Public representation of an email used by the Email Management
    list/table.

    ground_truth_label:
        Dataset ground truth displayed by the UI as NORMAL/BOMBING.

    status:
        Internal ingestion lifecycle status.

    Detailed metadata such as CC, BCC, Reply-To, MIME information,
    and raw email content belongs to EmailDetailResponse.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    source: EmailSource

    source_identifier: str | None

    ground_truth_label: EmailGroundTruthLabel

    message_id: str | None

    sender: str | None

    recipients: str | None

    subject: str | None

    content_hash: str

    received_at: datetime | None

    collected_at: datetime

    status: EmailStatus

    created_at: datetime

    updated_at: datetime


# ============================================================================
# EMAIL LIST RESPONSE
# ============================================================================

class EmailListResponse(BaseModel):
    """
    Paginated response for the Email Management table.
    """

    items: list[EmailResponse]

    total: int = Field(
        ge=0,
    )

    page: int = Field(
        ge=1,
    )

    page_size: int = Field(
        ge=1,
        le=MAX_PAGE_SIZE,
    )

    total_pages: int = Field(
        ge=1,
    )

    start_index: int = Field(
        ge=0,
    )

    end_index: int = Field(
        ge=0,
    )

    @property
    def has_previous(self) -> bool:
        """
        Whether a previous page exists.
        """

        return self.page > 1

    @property
    def has_next(self) -> bool:
        """
        Whether a next page exists.
        """

        return self.page < self.total_pages


# ============================================================================
# EMAIL DETAILS
# ============================================================================

class EmailDetailResponse(BaseModel):
    """
    Complete email representation used by the Email Details view.

    Sections represented by this response:

        Ground Truth
            - ground_truth_label

        Source
            - source
            - source_identifier

        Basic Message Information
            - subject
            - sender
            - recipients
            - cc
            - bcc
            - reply_to
            - message_id

        Time Information
            - received_at
            - collected_at

        Technical Information
            - content_type
            - mime_version
            - content_hash
            - id

        Email Content
            - raw_content

    This response intentionally contains email collection,
    ingestion, metadata, and content information only.

    Prediction, confidence, risk score, threat level, feature vector,
    ML model results, and detection decisions belong to later modules.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ========================================================================
    # IDENTITY
    # ========================================================================

    id: UUID

    # ========================================================================
    # GROUND TRUTH
    # ========================================================================

    ground_truth_label: EmailGroundTruthLabel

    # ========================================================================
    # SOURCE
    # ========================================================================

    source: EmailSource

    source_identifier: str | None

    # ========================================================================
    # BASIC MESSAGE INFORMATION
    # ========================================================================

    subject: str | None

    sender: str | None

    recipients: str | None

    cc: str | None

    bcc: str | None

    reply_to: str | None

    message_id: str | None

    # ========================================================================
    # TIME INFORMATION
    # ========================================================================

    received_at: datetime | None

    collected_at: datetime

    # ========================================================================
    # EMAIL TECHNICAL INFORMATION
    # ========================================================================

    content_type: str | None

    mime_version: str | None

    content_hash: str

    # ========================================================================
    # EMAIL CONTENT
    # ========================================================================

    raw_content: str

    # ========================================================================
    # INGESTION LIFECYCLE
    # ========================================================================

    status: EmailStatus

    # ========================================================================
    # AUDIT TIMESTAMPS
    # ========================================================================

    created_at: datetime

    updated_at: datetime


# ============================================================================
# EMAIL STATISTICS
# ============================================================================

class EmailStatisticsResponse(BaseModel):
    """
    Statistics displayed at the top of the Email Management page.

    These statistics represent ground-truth labels, not ML predictions.
    """

    total_emails: int = Field(
        ge=0,
    )

    normal_emails: int = Field(
        ge=0,
    )

    bombing_emails: int = Field(
        ge=0,
    )


# ============================================================================
# DELETE / RESET SUPPORT
# ============================================================================

class EmailDeleteResponse(BaseModel):
    """
    Response returned after deleting an email.

    This schema is retained for compatibility with any existing
    internal code. The current locked Email Management UI does not
    expose a delete-email action.
    """

    email_id: UUID

    deleted: bool


# ============================================================================
# HEALTH / VALIDATION
# ============================================================================

class EmailIngestionValidationResponse(BaseModel):
    """
    Validation result used before persistence when required.
    """

    valid: bool

    source: EmailSource

    ground_truth_label: EmailGroundTruthLabel

    error: str | None = None