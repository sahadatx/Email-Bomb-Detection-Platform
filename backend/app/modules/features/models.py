from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeatureExtractionStatus(str, Enum):
    """
    Persistence status of feature extraction.

    EXTRACTED:
        All F1-F12 features were extracted successfully.

    WARNING:
        Features were extracted, but one or more non-fatal
        validation or extraction warnings were recorded.

    FAILED:
        Feature extraction could not be completed successfully.
    """

    EXTRACTED = "extracted"
    WARNING = "warning"
    FAILED = "failed"


class EmailFeatures(Base):
    """
    Persisted F1-F12 feature record for one email.

    Module 04 is responsible only for feature extraction and
    persistence. Classification, prediction, confidence,
    risk scoring, and threat assessment are intentionally
    outside this model.

    One email can have at most one current feature record.
    Re-extraction updates the existing record instead of
    creating duplicate feature rows.
    """

    __tablename__ = "email_features"

    # ------------------------------------------------------------------
    # Primary Identity
    # ------------------------------------------------------------------

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

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

    # ------------------------------------------------------------------
    # F1-F12
    # ------------------------------------------------------------------

    # F1 — Sender Email
    #
    # Extracted sender email address from the From header field.
    f1_sender_email: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # F2 — Known Domain Indicator
    #
    # Identifies whether the sender domain belongs to
    # trusted providers.
    f2_known_domain: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F3 — Message-ID Presence
    #
    # Checks the existence of a valid Message-ID header.
    f3_message_id: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F4 — Auto-Submitted Header
    #
    # Detects automatically generated emails.
    f4_auto_submitted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F5 — Precedence Bulk Indicator
    #
    # Identifies bulk mailing behavior using the Precedence header.
    f5_precedence_bulk: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F6 — List-Id Header
    #
    # Detects mailing list identifiers in emails.
    f6_list_id: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F7 — X-BeenThere Header
    #
    # Identifies mailing list traversal headers.
    f7_x_beenthere: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F8 — X-Anti-Abuse Header
    #
    # Detects abuse or spam-related tracking headers.
    f8_x_anti_abuse: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # F9 — Keyword-Based Content Features
    #
    # Count of configured suspicious keywords detected
    # in normalized subject and text content.
    f9_keyword_features: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # F10 — Subject Length
    #
    # Length of the trimmed email subject.
    f10_subject_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # F11 — Emails Per Minute
    #
    # Number of emails received within the inclusive
    # 60-second temporal window ending at the current email.
    f11_emails_per_minute: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # F12 — Emails Per Hour
    #
    # Number of emails received within the inclusive
    # 3600-second temporal window ending at the current email.
    f12_emails_per_hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ------------------------------------------------------------------
    # Complete Feature Vector
    # ------------------------------------------------------------------

    feature_vector: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Extraction Metadata
    # ------------------------------------------------------------------

    status: Mapped[FeatureExtractionStatus] = mapped_column(
        SAEnum(
            FeatureExtractionStatus,
            name="feature_extraction_status",
            native_enum=False,
        ),
        nullable=False,
        default=FeatureExtractionStatus.EXTRACTED,
        index=True,
    )

    extractor_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    processing_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Audit Timestamps
    # ------------------------------------------------------------------

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