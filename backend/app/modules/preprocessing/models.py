from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PreprocessingRun(Base):
    """Persistent record of one preprocessing execution."""

    __tablename__ = "preprocessing_runs"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "dataset_versions.id",
            ondelete="RESTRICT",
            name="fk_preprocessing_runs_dataset_version_id",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    config_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    input_sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    output_sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    training_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    validation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    testing_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    feature_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
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
        default=utc_now,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('pending', 'running', 'completed', 'failed')",
            name="ck_preprocessing_runs_status",
        ),
        CheckConstraint(
            "input_sample_count >= 0 "
            "AND output_sample_count >= 0 "
            "AND training_count >= 0 "
            "AND validation_count >= 0 "
            "AND testing_count >= 0 "
            "AND feature_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_preprocessing_runs_counts",
        ),
        Index(
            "ix_preprocessing_runs_dataset_version_id",
            "dataset_version_id",
        ),
        Index(
            "ix_preprocessing_runs_status",
            "status",
        ),
        Index(
            "ix_preprocessing_runs_created_at",
            "created_at",
        ),
        Index(
            "ix_preprocessing_runs_version_created",
            "dataset_version_id",
            "created_at",
        ),
    )


class PreprocessingArtifact(Base):
    """Metadata for a generated preprocessing artifact."""

    __tablename__ = "preprocessing_artifacts"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    preprocessing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "preprocessing_runs.id",
            ondelete="CASCADE",
            name="fk_preprocessing_artifacts_run_id",
        ),
        nullable=False,
    )

    artifact_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    media_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "preprocessing_run_id",
            "artifact_type",
            name="uq_preprocessing_artifacts_run_type",
        ),
        CheckConstraint(
            "size_bytes >= 0",
            name="ck_preprocessing_artifacts_size",
        ),
        Index(
            "ix_preprocessing_artifacts_run_id",
            "preprocessing_run_id",
        ),
        Index(
            "ix_preprocessing_artifacts_type",
            "artifact_type",
        ),
    )