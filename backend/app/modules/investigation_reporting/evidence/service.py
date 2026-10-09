from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..errors import EvidenceValidationError, InvestigationError
from ..models import EvidenceRecord, InvestigationEvidenceEvent
from .repository import EvidenceRepository
from .validators import EvidenceValidator


class EvidenceService:
    """Evidence CRUD, review workflow, source validation and audit trail."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = EvidenceRepository(db)
        self.validator = EvidenceValidator(self.repository)

    @staticmethod
    def _page(total: int, page: int, page_size: int) -> dict[str, int]:
        return {"page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def list(self, *, page: int, page_size: int, search: str | None = None, evidence_type: str | None = None, review_status: str | None = None, detection_id: UUID | None = None, source_email_id: UUID | None = None, created_by: str | None = None, has_analyst_note: bool | None = None, provenance_search: str | None = None, from_date: datetime | None = None, to_date: datetime | None = None) -> dict[str, Any]:
        rows, total = self.repository.list(page=page, page_size=page_size, search=search, evidence_type=evidence_type, review_status=review_status, detection_id=detection_id, source_email_id=source_email_id, created_by=created_by, has_analyst_note=has_analyst_note, provenance_search=provenance_search, from_date=from_date, to_date=to_date)
        return {"items": rows, "total": total, "summary": self.repository.summary(), **self._page(total, page, page_size)}

    def create(self, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        try:
            self.validator.validate_create(values)
        except EvidenceValidationError as exc:
            raise InvestigationError(str(exc)) from exc
        data = dict(values)
        data["collected_at"] = data.get("collected_at") or datetime.now(timezone.utc)
        record = EvidenceRecord(created_by=actor_id, updated_by=actor_id, **data)
        self.repository.add(record)
        self.repository.flush()
        self.repository.add_event(InvestigationEvidenceEvent(evidence_id=record.id, actor_id=actor_id, action="created", after_data={"name": record.name, "evidence_type": record.evidence_type, "review_status": record.review_status}))
        self.repository.flush()
        return record

    def update(self, evidence_id: UUID, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        record = self.repository.get(evidence_id)
        if record is None:
            raise InvestigationError("Evidence record not found.")
        try:
            self.validator.validate_update(record, values)
        except EvidenceValidationError as exc:
            raise InvestigationError(str(exc)) from exc
        before = self._audit_values(record, values)
        substantive_change = any(getattr(record, key) != value for key, value in values.items())
        for key, value in values.items():
            setattr(record, key, value)
        requires_review = record.review_status == "verified" and substantive_change
        if requires_review:
            record.review_status = "pending"
        record.updated_by = actor_id
        record.updated_at = datetime.now(timezone.utc)
        after = self._audit_values(record, values)
        self.repository.add_event(InvestigationEvidenceEvent(evidence_id=record.id, actor_id=actor_id, action="updated", before_data=before, after_data=after, reason="Edited verified evidence returned to pending review." if requires_review else None))
        self.repository.flush()
        return record

    def review(self, evidence_id: UUID, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        record = self.repository.get(evidence_id)
        if record is None:
            raise InvestigationError("Evidence record not found.")
        try:
            self.validator.validate_review(record.review_status, values)
        except EvidenceValidationError as exc:
            raise InvestigationError(str(exc)) from exc
        old_status = record.review_status
        record.review_status = values["review_status"]
        if values.get("analyst_comment") is not None:
            record.analyst_note = values["analyst_comment"]
        record.updated_by = actor_id
        record.updated_at = datetime.now(timezone.utc)
        self.repository.add_event(InvestigationEvidenceEvent(evidence_id=record.id, actor_id=actor_id, action="review_status_changed", reason=values["reason"], before_data={"review_status": old_status}, after_data={"review_status": record.review_status, "analyst_comment": values.get("analyst_comment")}))
        self.repository.flush()
        return record

    def detail(self, evidence_id: UUID) -> dict[str, Any]:
        record = self.repository.get(evidence_id)
        if record is None:
            raise InvestigationError("Evidence record not found.")
        return {"evidence": record, "history": self.repository.events(evidence_id)}

    def export(self, **filters: Any) -> list[EvidenceRecord]:
        rows: list[EvidenceRecord] = []
        page = 1
        page_size = 500
        while True:
            batch, total = self.repository.list(page=page, page_size=page_size, **filters)
            rows.extend(batch)
            if not batch or len(rows) >= total:
                return rows
            page += 1

    def for_detections(self, detection_ids: list[UUID]) -> list[EvidenceRecord]:
        return self.repository.for_detections(detection_ids)

    @staticmethod
    def serialize(record: EvidenceRecord) -> dict[str, Any]:
        return {
            "id": str(record.id), "detection_id": str(record.detection_id),
            "source_email_id": str(record.source_email_id) if record.source_email_id else None,
            "type": record.evidence_type, "name": record.name, "description": record.description,
            "observed_value": record.observed_value, "provenance": record.provenance,
            "review_status": record.review_status,
            "collected_at": record.collected_at.isoformat() if record.collected_at else None,
            "created_by": str(record.created_by), "updated_by": str(record.updated_by),
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    @staticmethod
    def _audit_values(record: EvidenceRecord, keys) -> dict[str, Any]:
        result = {}
        for key in keys:
            value = getattr(record, key)
            result[key] = str(value) if isinstance(value, UUID) else value
        return result
