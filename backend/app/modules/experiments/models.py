from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now(): return datetime.now(timezone.utc)


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_definition_id: Mapped[UUID] = mapped_column(ForeignKey("ml_model_definitions.id", ondelete="RESTRICT"), nullable=False, index=True)
    dataset_version_id: Mapped[UUID] = mapped_column(ForeignKey("dataset_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    preprocessing_run_id: Mapped[UUID] = mapped_column(ForeignKey("preprocessing_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    feature_set_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    training_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evaluation_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {"split": "validation"})
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    # User IDs follow UUIDTimestampMixin and are persisted as 36-char strings.
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (CheckConstraint("status IN ('draft','queued','running','completed','failed','cancelled')", name="ck_experiments_status"), Index("ix_experiments_dataset_model", "dataset_version_id", "model_definition_id"))


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    training_run_id: Mapped[UUID] = mapped_column(ForeignKey("ml_training_runs.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    evaluation_run_id: Mapped[UUID | None] = mapped_column(ForeignKey("ml_evaluation_runs.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    logs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (CheckConstraint("status IN ('queued','running','completed','failed','cancelled')", name="ck_experiment_runs_status"), CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_experiment_runs_progress"))
