from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ============================================================
# PARSING STATUS
# ============================================================


class ParsingStatus(str, Enum):
    """
    Current parsing state of a collected email.

    PENDING:
        No parsed result has been persisted yet.

    PARSED:
        Email was parsed successfully without validation
        warnings or errors.

    WARNING:
        Email was parsed successfully, but one or more
        non-fatal validation warnings were detected.

    FAILED:
        Parsing or validation produced one or more fatal
        errors.
    """

    PARSED = "parsed"
    WARNING = "warning"
    FAILED = "failed"


# ============================================================
# PARSED EMAIL
# ============================================================


class ParsedEmail(Base):
    """
    Persistent parsed representation of a collected email.

    This model belongs to Module 03 — Email Parsing &
    Normalization.

    The canonical raw email remains stored in Module 02:

        emails.raw_content

    This table stores only the structured result produced by
    the parsing, normalization, and validation pipeline.

    Relationship:

        emails.id
            │
            │ 1 : 1
            ▼
        parsed_emails.email_id
    """

    __tablename__ = "parsed_emails"

    # ========================================================
    # IDENTITY
    # ========================================================

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # --------------------------------------------------------
    # Canonical Module 02 email reference
    # --------------------------------------------------------

    email_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "emails.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # ========================================================
    # PARSED EMAIL IDENTITY
    # ========================================================

    message_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    # ========================================================
    # PARSED ADDRESSES
    # ========================================================

    sender: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    recipients: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    reply_to: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    cc: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    bcc: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ========================================================
    # PARSED DATE
    # ========================================================

    date: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    # ========================================================
    # NORMALIZED HEADERS
    # ========================================================

    headers: Mapped[dict[str, list[str]]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # ========================================================
    # MESSAGE BODY
    # ========================================================

    text_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    html_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # MIME STRUCTURE
    # ========================================================

    mime_parts: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ========================================================
    # ATTACHMENTS
    # ========================================================

    attachments: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    validation_errors: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    validation_warnings: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ========================================================
    # PARSING STATE
    # ========================================================

    status: Mapped[ParsingStatus] = mapped_column(
        SAEnum(
            ParsingStatus,
            name="parsing_status",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # PROCESSING METADATA
    # ========================================================

    parser_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    processing_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    parsed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )