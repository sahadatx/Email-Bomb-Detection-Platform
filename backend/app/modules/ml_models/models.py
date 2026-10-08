
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class MLModelDefinition(Base):
    """Persistent definition and configuration of an ML model."""

    __tablename__ = "ml_model_definitions"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    hyperparameters: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    @property
    def model_type(self) -> str:
        """All currently registered model engines are classifiers."""
        return "classifier"

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_ml_model_definitions_status",
        ),
        Index(
            "ix_ml_model_definitions_name",
            "name",
        ),
        Index(
            "ix_ml_model_definitions_algorithm",
            "algorithm",
        ),
        Index(
            "ix_ml_model_definitions_status",
            "status",
        ),
        Index(
            "ix_ml_model_definitions_created_at",
            "created_at",
        ),
    )


class MLTrainingRun(Base):
    """Persistent record of one model training execution."""

    __tablename__ = "ml_training_runs"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    model_definition_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "ml_model_definitions.id",
            ondelete="RESTRICT",
            name="fk_ml_training_runs_model_definition_id",
        ),
        nullable=False,
    )

    preprocessing_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "preprocessing_runs.id",
            ondelete="RESTRICT",
            name="fk_ml_training_runs_preprocessing_run_id",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    config_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    training_sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    validation_sample_count: Mapped[int] = mapped_column(
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
            "('pending', 'queued', 'running', 'completed', "
            "'failed', 'cancelled')",
            name="ck_ml_training_runs_status",
        ),
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100 "
            "AND training_sample_count >= 0 "
            "AND validation_sample_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_ml_training_runs_counts",
        ),
        Index(
            "ix_ml_training_runs_model_definition_id",
            "model_definition_id",
        ),
        Index(
            "ix_ml_training_runs_preprocessing_run_id",
            "preprocessing_run_id",
        ),
        Index(
            "ix_ml_training_runs_status",
            "status",
        ),
        Index(
            "ix_ml_training_runs_created_at",
            "created_at",
        ),
        Index(
            "ix_ml_training_runs_model_created",
            "model_definition_id",
            "created_at",
        ),
    )


class MLModelVersion(Base):
    """A successfully trained model version and its artifact metadata."""

    __tablename__ = "ml_model_versions"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    model_definition_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "ml_model_definitions.id",
            ondelete="RESTRICT",
            name="fk_ml_model_versions_model_definition_id",
        ),
        nullable=False,
    )

    training_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "ml_training_runs.id",
            ondelete="RESTRICT",
            name="fk_ml_model_versions_training_run_id",
        ),
        nullable=False,
        unique=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="registered",
    )

    artifact_filename: Mapped[str] = mapped_column(
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

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "model_definition_id",
            "version",
            name="uq_ml_model_versions_definition_version",
        ),
        CheckConstraint(
            "version > 0 AND size_bytes >= 0",
            name="ck_ml_model_versions_values",
        ),
        CheckConstraint(
            "status IN ('registered', 'active', 'archived')",
            name="ck_ml_model_versions_status",
        ),
        Index(
            "ix_ml_model_versions_definition_id",
            "model_definition_id",
        ),
        Index(
            "ix_ml_model_versions_training_run_id",
            "training_run_id",
        ),
        Index(
            "ix_ml_model_versions_status",
            "status",
        ),
        Index(
            "ix_ml_model_versions_created_at",
            "created_at",
        ),
    )


class MLEvaluationRun(Base):
    """Persistent record of evaluating a trained model version."""

    __tablename__ = "ml_evaluation_runs"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    model_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "ml_model_versions.id",
            ondelete="RESTRICT",
            name="fk_ml_evaluation_runs_model_version_id",
        ),
        nullable=False,
    )

    preprocessing_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "preprocessing_runs.id",
            ondelete="RESTRICT",
            name="fk_ml_evaluation_runs_preprocessing_run_id",
        ),
        nullable=False,
    )

    evaluation_split: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    precision: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    recall: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    f1_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    roc_auc: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confusion_matrix: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    classification_report: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    result_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
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
            "evaluation_split IN ('validation', 'testing')",
            name="ck_ml_evaluation_runs_split",
        ),
        CheckConstraint(
            "status IN "
            "('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_ml_evaluation_runs_status",
        ),
        CheckConstraint(
            "sample_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_ml_evaluation_runs_counts",
        ),
        CheckConstraint(
            "(accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)) "
            "AND (precision IS NULL OR (precision >= 0 AND precision <= 1)) "
            "AND (recall IS NULL OR (recall >= 0 AND recall <= 1)) "
            "AND (f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)) "
            "AND (roc_auc IS NULL OR (roc_auc >= 0 AND roc_auc <= 1))",
            name="ck_ml_evaluation_runs_metrics",
        ),
        Index(
            "ix_ml_evaluation_runs_model_version_id",
            "model_version_id",
        ),
        Index(
            "ix_ml_evaluation_runs_preprocessing_run_id",
            "preprocessing_run_id",
        ),
        Index(
            "ix_ml_evaluation_runs_status",
            "status",
        ),
        Index(
            "ix_ml_evaluation_runs_created_at",
            "created_at",
        ),
        Index(
            "ix_ml_evaluation_runs_version_created",
            "model_version_id",
            "created_at",
        ),
    )