from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.detection.models import DetectionRecord
from app.modules.emails.models import Email
from ..models import EvidenceRecord, InvestigationEvidenceEvent


class EvidenceRepository:
    """Persistence boundary for evidence, its source records and audit events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def detection_exists(self, detection_id: UUID) -> bool:
        return self.db.scalar(select(DetectionRecord.id).where(DetectionRecord.id == detection_id)) is not None

    def email_exists(self, email_id: UUID) -> bool:
        return self.db.scalar(select(Email.id).where(Email.id == email_id)) is not None

    def detection_source_email(self, detection_id: UUID) -> UUID | None:
        return self.db.scalar(select(DetectionRecord.email_id).where(DetectionRecord.id == detection_id))

    def list(self, *, page: int, page_size: int, search: str | None = None, evidence_type: str | None = None, review_status: str | None = None, detection_id: UUID | None = None, source_email_id: UUID | None = None, created_by: str | None = None, has_analyst_note: bool | None = None, provenance_search: str | None = None, from_date: datetime | None = None, to_date: datetime | None = None) -> tuple[list[EvidenceRecord], int]:
        query = select(EvidenceRecord)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(EvidenceRecord.name.ilike(term), EvidenceRecord.description.ilike(term), EvidenceRecord.observed_value.ilike(term), func.cast(EvidenceRecord.id, str).ilike(term), func.cast(EvidenceRecord.detection_id, str).ilike(term)))
        if evidence_type:
            filters.append(EvidenceRecord.evidence_type == evidence_type)
        if review_status:
            filters.append(EvidenceRecord.review_status == review_status)
        if detection_id:
            filters.append(EvidenceRecord.detection_id == detection_id)
        if source_email_id:
            filters.append(EvidenceRecord.source_email_id == source_email_id)
        if created_by:
            filters.append(EvidenceRecord.created_by == created_by)
        if has_analyst_note is True:
            filters.append(EvidenceRecord.analyst_note.is_not(None))
            filters.append(EvidenceRecord.analyst_note != "")
        elif has_analyst_note is False:
            filters.append(or_(EvidenceRecord.analyst_note.is_(None), EvidenceRecord.analyst_note == ""))
        if provenance_search:
            filters.append(func.cast(EvidenceRecord.provenance, str).ilike(f"%{provenance_search.strip()}%"))
        if from_date:
            filters.append(EvidenceRecord.collected_at >= from_date)
        if to_date:
            filters.append(EvidenceRecord.collected_at <= to_date)
        if filters:
            query = query.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = list(self.db.scalars(query.order_by(EvidenceRecord.created_at.desc(), EvidenceRecord.id).offset((page - 1) * page_size).limit(page_size)).all())
        return rows, total

    def summary(self) -> dict[str, int]:
        summary = {"total": 0, "verified": 0, "pending": 0, "flagged": 0, "rejected": 0}
        for status, count in self.db.execute(select(EvidenceRecord.review_status, func.count()).group_by(EvidenceRecord.review_status)):
            summary["total"] += int(count)
            if status in summary:
                summary[status] = int(count)
        return summary

    def for_detections(self, detection_ids: list[UUID]) -> list[EvidenceRecord]:
        if not detection_ids:
            return []
        statement = select(EvidenceRecord).where(EvidenceRecord.detection_id.in_(detection_ids)).order_by(EvidenceRecord.created_at, EvidenceRecord.id)
        return list(self.db.scalars(statement).all())

    def get(self, evidence_id: UUID) -> EvidenceRecord | None:
        return self.db.get(EvidenceRecord, evidence_id)

    def events(self, evidence_id: UUID) -> list[InvestigationEvidenceEvent]:
        stmt = select(InvestigationEvidenceEvent).where(InvestigationEvidenceEvent.evidence_id == evidence_id).order_by(InvestigationEvidenceEvent.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def add(self, evidence: EvidenceRecord) -> None:
        self.db.add(evidence)

    def add_event(self, event: InvestigationEvidenceEvent) -> None:
        self.db.add(event)

    def flush(self) -> None:
        self.db.flush()
