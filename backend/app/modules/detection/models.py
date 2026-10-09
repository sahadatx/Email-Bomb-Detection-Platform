from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DetectionRecord(Base):
    __tablename__ = "email_detections"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("emails.id", ondelete="RESTRICT"), nullable=True, index=True)
    input_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("detection_inputs.id", ondelete="RESTRICT"), nullable=True, index=True)
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("detection_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    model_version_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("ml_model_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    predicted_label: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed", index=True)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    __table_args__ = (CheckConstraint("(email_id IS NOT NULL AND input_id IS NULL) OR (email_id IS NULL AND input_id IS NOT NULL)", name="ck_email_detections_single_input"),)


class DetectionInput(Base):
    """Unlabeled .eml input submitted for classification, separate from dataset labels."""
    __tablename__ = "detection_inputs"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("detection_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    sender: Mapped[str | None] = mapped_column(String(512), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class DetectionBatch(Base):
    __tablename__ = "detection_batches"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class RiskAssessment(Base):
    __tablename__ = "detection_risk_assessments"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    detection_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("email_detections.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="unavailable", index=True)
    factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class BehavioralResult(Base):
    __tablename__ = "detection_behavioral_results"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    detection_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("email_detections.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="insufficient_data")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    anomalies: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class DetectionSettings(Base):
    __tablename__ = "detection_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    default_model_version_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("ml_model_versions.id", ondelete="SET NULL"), nullable=True)
    high_risk_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    critical_risk_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    enable_behavioral_analysis: Mapped[bool] = mapped_column(nullable=False, default=True)
    save_feature_snapshots: Mapped[bool] = mapped_column(nullable=False, default=True)
    store_detection_history: Mapped[bool] = mapped_column(nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (CheckConstraint("id = 1", name="ck_detection_settings_singleton"), CheckConstraint("high_risk_threshold BETWEEN 1 AND 100", name="ck_detection_settings_high_threshold"), CheckConstraint("critical_risk_threshold BETWEEN 1 AND 100", name="ck_detection_settings_critical_threshold"))
