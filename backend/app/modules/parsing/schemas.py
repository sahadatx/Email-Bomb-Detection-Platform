from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.emails.models import (
    EmailGroundTruthLabel,
    EmailSource,
    EmailStatus,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# PAGINATION
# ============================================================


class ParsingPagination(BaseModel):
    """
    Pagination metadata for the Parsing Workspace.

    Pagination describes only the currently displayed result
    page. It does not represent global parsing statistics.

    Example:

        52 matching emails
        page_size = 30

        Page 1:
            1 - 30 / 52

        Page 2:
            31 - 52 / 52
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Current page number.",
    )

    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of emails displayed on one page.",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Total number of emails in the current filtered result set.",
    )

    total_pages: int = Field(
        default=1,
        ge=1,
        description="Total number of available pages.",
    )

    start_index: int = Field(
        default=0,
        ge=0,
        description="1-based index of the first item on the current page.",
    )

    end_index: int = Field(
        default=0,
        ge=0,
        description="1-based index of the last item on the current page.",
    )

    @property
    def has_previous(self) -> bool:
        """
        Return whether a previous page exists.
        """

        return self.page > 1

    @property
    def has_next(self) -> bool:
        """
        Return whether a next page exists.
        """

        return self.page < self.total_pages


# ============================================================
# PARSING STATUS
# ============================================================


class ParsingStatus(str, Enum):
    """
    High-level status of the Module 03 parsing pipeline.

    PENDING
        The collected email has not been parsed yet.

    PARSED
        Parsing completed successfully.

    WARNING
        Parsing completed, but non-fatal validation warnings
        were detected.

    FAILED
        Parsing or validation produced fatal errors.
    """

    PENDING = "pending"
    PARSED = "parsed"
    WARNING = "warning"
    FAILED = "failed"


# ============================================================
# PARSING FILTERS
# ============================================================


class ParsingEmailFilters(BaseModel):
    """
    Common filters used by the Parsing Workspace.

    Filter semantics are AND-based across different fields.

    Example:

        source = FILE_UPLOAD
        AND level = BOMBING
        AND status = PARSED
        AND received_at >= from_date
        AND received_at <= to_date

    Search itself is handled as an OR search across the
    supported searchable email fields.
    """

    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=512,
        description=(
            "Search subject, sender, Message-ID, or source identifier."
        ),
    )

    source: EmailSource | None = Field(
        default=None,
        description="Filter by email collection source.",
    )

    level: EmailGroundTruthLabel | None = Field(
        default=None,
        description="Filter by Module 02 ground-truth label.",
    )

    status: ParsingStatus | None = Field(
        default=None,
        description="Filter by Module 03 parsing status.",
    )

    from_date: date | None = Field(
        default=None,
        description="Filter emails received on or after this date.",
    )

    to_date: date | None = Field(
        default=None,
        description="Filter emails received on or before this date.",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "ParsingEmailFilters":
        """
        Ensure the date range is logically ordered.
        """

        if (
            self.from_date is not None
            and self.to_date is not None
            and self.from_date > self.to_date
        ):
            raise ValueError(
                "from_date must be earlier than or equal to to_date."
            )

        return self


class ParsingEmailListQuery(ParsingEmailFilters):
    """
    Query parameters used by the Parsing Workspace list API.

    The default page size remains 30 because pagination is a
    presentation concern. It is not the parsing batch size.
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Current result page.",
    )

    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of rows displayed on one page.",
    )


# ============================================================
# BULK SELECTION
# ============================================================


class ParsingSelectionRequest(ParsingEmailFilters):
    """
    Filter-based selection request for bulk parsing actions.

    This allows the UI to operate on all emails matching the
    current filters rather than only the 30 rows displayed on
    the current page.

    Example:

        Select All Matching
            -> selects every email matching the active filters

        Parse All Pending
            -> uses status = PENDING
    """

    pass


# ============================================================
# MIME PART
# ============================================================


class ParsedMimePart(BaseModel):
    """
    Structured metadata for one MIME part.

    Binary MIME content is intentionally not exposed here.
    """

    content_type: str = Field(
        description="MIME content type.",
    )

    content_disposition: str | None = Field(
        default=None,
        description="MIME content disposition.",
    )

    charset: str | None = Field(
        default=None,
        description="Character set declared by the MIME part.",
    )

    filename: str | None = Field(
        default=None,
        description="Filename associated with the MIME part.",
    )

    size: int = Field(
        default=0,
        ge=0,
        description="Size of the MIME part in bytes.",
    )


# ============================================================
# ATTACHMENT
# ============================================================


class ParsedAttachment(BaseModel):
    """
    Metadata describing an email attachment.

    Attachment binary content is intentionally not stored in
    the public parsing response.
    """

    filename: str | None = Field(
        default=None,
        description="Attachment filename.",
    )

    content_type: str = Field(
        description="Attachment MIME content type.",
    )

    content_disposition: str | None = Field(
        default=None,
        description="Attachment content disposition.",
    )

    size: int = Field(
        default=0,
        ge=0,
        description="Attachment size in bytes.",
    )

    content_id: str | None = Field(
        default=None,
        description="Optional MIME Content-ID.",
    )


# ============================================================
# EMAIL IDENTITY
# ============================================================


class ParsedEmailIdentity(BaseModel):
    """
    Identity and addressing information extracted from the
    collected email.
    """

    message_id: str | None = None

    subject: str | None = None

    sender: str | None = None

    recipients: list[str] = Field(
        default_factory=list,
    )

    reply_to: list[str] = Field(
        default_factory=list,
    )

    cc: list[str] = Field(
        default_factory=list,
    )

    bcc: list[str] = Field(
        default_factory=list,
    )

    date: str | None = None


# ============================================================
# EMAIL TIMESTAMPS
# ============================================================


class ParsedEmailTimestamps(BaseModel):
    """
    Important lifecycle timestamps associated with the email.
    """

    received_at: datetime | None = None

    collected_at: datetime

    parsed_at: datetime | None = None


# ============================================================
# PARSING METADATA
# ============================================================


class ParsingMetadata(BaseModel):
    """
    Metadata describing Module 03 processing state.

    Status here represents parsing status only.

    Ground-truth Level is represented separately on the
    ParsedEmailResponse and ParsingEmailListItem.
    """

    status: ParsingStatus = ParsingStatus.PENDING

    parser_version: str | None = None

    processing_time_ms: float | None = None


# ============================================================
# PARSED EMAIL RESPONSE
# ============================================================


class ParsedEmailResponse(BaseModel):
    """
    Complete public representation of a parsed email.

    Module 02 remains the canonical source for the original
    collected email and its ground-truth label.

    The raw MIME content is intentionally not exposed by this
    response.

    Important distinction:

        level
            Ground-truth label from Module 02.

        parsing.status
            Module 03 parsing status.

    These are separate concepts and must not be mixed.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    email_id: UUID

    # --------------------------------------------------------
    # Module 02 canonical metadata
    # --------------------------------------------------------

    source: EmailSource

    source_identifier: str | None = None

    level: EmailGroundTruthLabel

    # --------------------------------------------------------
    # Parsed email identity
    # --------------------------------------------------------

    identity: ParsedEmailIdentity

    timestamps: ParsedEmailTimestamps

    parsing: ParsingMetadata

    # --------------------------------------------------------
    # Parsed headers
    # --------------------------------------------------------

    headers: dict[str, list[str]] = Field(
        default_factory=dict,
    )

    # --------------------------------------------------------
    # Parsed body
    # --------------------------------------------------------

    text_body: str | None = None

    html_body: str | None = None

    # --------------------------------------------------------
    # MIME structure
    # --------------------------------------------------------

    mime_parts: list[ParsedMimePart] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Attachments
    # --------------------------------------------------------

    attachments: list[ParsedAttachment] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation_errors: list[str] = Field(
        default_factory=list,
    )

    validation_warnings: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# PARSING EMAIL LIST ITEM
# ============================================================


class ParsingEmailListItem(BaseModel):
    """
    Lightweight representation used by the Parsing Workspace.

    The list item intentionally excludes:

        - parsed body
        - MIME structure
        - attachment metadata
        - validation detail

    The workspace table requires only:

        Subject
        Sender
        Source
        Level
        Received
        Status
        Action

    Level comes from Module 02 ground truth.

    parsing_status comes from Module 03.
    """

    email_id: UUID

    # --------------------------------------------------------
    # Source / collection metadata
    # --------------------------------------------------------

    source: EmailSource

    source_identifier: str | None = None

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    level: EmailGroundTruthLabel

    # --------------------------------------------------------
    # Basic email identity
    # --------------------------------------------------------

    message_id: str | None = None

    sender: str | None = None

    subject: str | None = None

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    received_at: datetime | None = None

    collected_at: datetime

    # --------------------------------------------------------
    # Parsing state
    # --------------------------------------------------------

    parsing_status: ParsingStatus = ParsingStatus.PENDING


# ============================================================
# PARSING EMAIL LIST RESPONSE
# ============================================================


class ParsingEmailListResponse(BaseModel):
    """
    Paginated email list for the Parsing Workspace.

    The response represents the currently filtered collection,
    not the entire database when filters are active.
    """

    items: list[ParsingEmailListItem]

    total: int = Field(
        default=0,
        ge=0,
        description="Total number of emails matching the filters.",
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
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

    @property
    def has_previous(self) -> bool:
        """
        Return whether a previous page exists.
        """

        return self.page > 1

    @property
    def has_next(self) -> bool:
        """
        Return whether a next page exists.
        """

        return self.page < self.total_pages


# ============================================================
# PARSING REQUESTS
# ============================================================


class ParseEmailRequest(BaseModel):
    """
    Request to parse one collected email.
    """

    email_id: UUID


class ParseEmailsRequest(BaseModel):
    """
    Request to parse explicitly selected collected emails.

    This request is intentionally limited to 100 IDs per API
    call. Large selections should be processed internally in
    controlled batches.
    """

    email_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
    )


class ParseMatchingEmailsRequest(ParsingSelectionRequest):
    """
    Request to parse every email matching the supplied filters.

    This is used for operations such as:

        Parse Selected / Parse All Matching

    The filter criteria determine the complete target set;
    current UI pagination does not limit the operation.
    """

    pass


class ParseAllPendingRequest(BaseModel):
    """
    Request to parse all currently pending emails.

    No email IDs are required because the backend resolves
    the pending population from persisted parsing state.
    """

    confirm: bool = Field(
        default=True,
        description="Explicit confirmation that all pending emails may be parsed.",
    )


# ============================================================
# OPERATION SUMMARY
# ============================================================


class ParsingSummary(BaseModel):
    """
    Summary of a single parsing operation.

    This is NOT the global Module 03 database summary.

    It describes what happened during a user-triggered
    single or batch parsing operation.
    """

    selected: int = Field(
        default=0,
        ge=0,
        description="Number of emails selected for this operation.",
    )

    parsed: int = Field(
        default=0,
        ge=0,
        description="Number successfully parsed in this operation.",
    )

    warnings: int = Field(
        default=0,
        ge=0,
        description="Number parsed with validation warnings.",
    )

    failed: int = Field(
        default=0,
        ge=0,
        description="Number that failed during this operation.",
    )


# ============================================================
# GLOBAL PARSING SUMMARY
# ============================================================


class ParsingPersistenceSummary(BaseModel):
    """
    Global persisted parsing state for Module 03.

    This is independent of UI pagination.

    Example:

        total_collected       = 52
        total_parsed          = 22
        total_pending         = 30
        total_warnings        = 0
        total_failed         = 0
        ready_for_features    = 22
        readiness_percentage  = 42.31
    """

    total_collected: int = Field(
        default=0,
        ge=0,
        description="Total number of collected emails.",
    )

    total_parsed: int = Field(
        default=0,
        ge=0,
        description="Total successfully parsed emails.",
    )

    total_pending: int = Field(
        default=0,
        ge=0,
        description="Total emails that have not been parsed yet.",
    )

    total_warnings: int = Field(
        default=0,
        ge=0,
        description="Total parsed emails with validation warnings.",
    )

    total_failed: int = Field(
        default=0,
        ge=0,
        description="Total parsed emails with fatal parsing failures.",
    )

    ready_for_features: int = Field(
        default=0,
        ge=0,
        description="Number of emails ready for Module 04.",
    )

    readiness_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of collected emails ready for Module 04.",
    )


# ============================================================
# GLOBAL PARSING SUMMARY RESPONSE
# ============================================================


class ParsingSummaryResponse(BaseModel):
    """
    Public API response for the global Module 03 parsing
    summary.

    This endpoint is intentionally separate from paginated
    email listing and from a user-triggered parsing operation.
    """

    total_collected: int = Field(
        default=0,
        ge=0,
    )

    parsed: int = Field(
        default=0,
        ge=0,
    )

    pending: int = Field(
        default=0,
        ge=0,
    )

    warnings: int = Field(
        default=0,
        ge=0,
    )

    failed: int = Field(
        default=0,
        ge=0,
    )

    ready_for_features: int = Field(
        default=0,
        ge=0,
    )

    readiness_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )