from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmailSource(str, Enum):
    """
    Source from which an email entered the platform.

    Current controlled ingestion workflow:
        - FILE_UPLOAD
        - RAW_EMAIL

    IMAP is retained as a legacy database value so that any
    historical
    records can still be loaded safely. New IMAP collection is not part
    of the current Module 02 workflow.
    """

    FILE_UPLOAD = "file_upload"
    RAW_EMAIL = "raw_email"

    # Legacy value retained for compatibility with historical records.
    IMAP = "imap"


class EmailGroundTruthLabel(str, Enum):
    """
    Ground-truth label assigned during email ingestion.

    These values represent dataset ground truth and are not ML
    predictions.

    Supported labels:
        - NORMAL
        - BOMBING
    """

    NORMAL = "normal"
    BOMBING = "bombing"


class EmailStatus(str, Enum):
    """
    Lifecycle status of an email ingestion record.

    INGESTED:
        The email was successfully persisted.

    FAILED:
        The ingestion operation failed.
    """

    INGESTED = "ingested"
    FAILED = "failed"


class Email(Base):
    """
    Canonical stored representation of a collected email.

    Module 02 responsibilities:
        - Store the original raw email.
        - Store email header metadata.
        - Store source and source identifier.
        - Store the ground-truth label.
        - Store deterministic content hash.
        - Store received and collection timestamps.
        - Track ingestion lifecycle status.

    The ground-truth label is supplied by the controlled ingestion
    workflow. It is not calculated from features.

    Later modules are responsible for:
        - Parsing
        - Normalization
        - Feature extraction
        - Dataset processing
        - ML training
        - Prediction
        - Confidence
        - Risk scoring
        - Threat analysis
        - Detection decisions
    """

    __tablename__ = "emails"

    # ======================================================================
    # IDENTITY
    # ======================================================================

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # ======================================================================
    # SOURCE
    # ======================================================================

    source: Mapped[EmailSource] = mapped_column(
        SAEnum(
            EmailSource,
            name="email_source",
            native_enum=False,
        ),
        nullable=False,
    )

    source_identifier: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # ======================================================================
    # GROUND TRUTH
    # ======================================================================

    ground_truth_label: Mapped[EmailGroundTruthLabel] = mapped_column(
        SAEnum(
            EmailGroundTruthLabel,
            name="email_ground_truth_label",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    # ======================================================================
    # BASIC MESSAGE INFORMATION
    # ======================================================================

    message_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    sender: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    recipients: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cc: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    bcc: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reply_to: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    # ======================================================================
    # EMAIL TECHNICAL INFORMATION
    # ======================================================================

    content_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mime_version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # ======================================================================
    # RAW EMAIL
    # ======================================================================

    raw_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ======================================================================
    # DEDUPLICATION / INTEGRITY
    # ======================================================================

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # ======================================================================
    # TIME INFORMATION
    # ======================================================================

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ======================================================================
    # INGESTION LIFECYCLE
    # ======================================================================

    status: Mapped[EmailStatus] = mapped_column(
        SAEnum(
            EmailStatus,
            name="email_status",
            native_enum=False,
        ),
        nullable=False,
        default=EmailStatus.INGESTED,
        index=True,
    )

    # ======================================================================
    # AUDIT TIMESTAMPS
    # ======================================================================

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