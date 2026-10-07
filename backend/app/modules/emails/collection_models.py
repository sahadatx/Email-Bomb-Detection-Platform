from __future__ import annotations

from datetime import datetime,timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CollectionSource(str, Enum):
    """Supported email collection sources."""

    IMAP = "imap"
    FILE_UPLOAD = "file_upload"
    RAW_EMAIL = "raw_email"


class CollectionJobStatus(str, Enum):
    """Lifecycle states for an email collection job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class CollectionJob(Base):
    """
    Persistent record of an email collection operation.

    A collection job represents one user-requested collection action,
    such as fetching emails from an IMAP mailbox or uploading a batch
    of .eml files.

    Email parsing, feature extraction, classification, and detection
    are intentionally outside this model.
    """

    __tablename__ = "email_collection_jobs"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source: Mapped[CollectionSource] = mapped_column(
        String(32),
        nullable=False,
    )

    mailbox: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    status: Mapped[CollectionJobStatus] = mapped_column(
        String(16),
        nullable=False,
        default=CollectionJobStatus.PENDING,
    )

    requested_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    fetched_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    ingested_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    duplicate_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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