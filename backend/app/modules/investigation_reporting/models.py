from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceRecord(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    detection_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("email_detections.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_email_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("emails.id", ondelete="RESTRICT"), nullable=True, index=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    analyst_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # User IDs use String(36) in the user module; keep FK column types aligned.
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    updated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (Index("ix_investigation_evidence_created", "created_at"),)


class InvestigationEvidenceEvent(Base):
    __tablename__ = "investigation_evidence_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    evidence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("investigation_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    after_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)


class AnalystNote(Base):
    __tablename__ = "detection_analyst_notes"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    detection_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("email_detections.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False, default="observation")
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class AnalystNoteEvent(Base):
    __tablename__ = "detection_analyst_note_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    note_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    detection_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("email_detections.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    before_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    after_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)


class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(String(24), nullable=False, default="investigation", index=True)
    output_format: Mapped[str] = mapped_column(String(12), nullable=False, default="json")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    detection_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    sections: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InvestigationReportEvent(Base):
    __tablename__ = "investigation_report_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
