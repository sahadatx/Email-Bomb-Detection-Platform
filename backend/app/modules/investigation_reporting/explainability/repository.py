from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.detection.models import BehavioralResult, DetectionInput, DetectionRecord, RiskAssessment
from app.modules.emails.models import Email
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion
from ..models import AnalystNote, AnalystNoteEvent
from ..repository import InvestigationRepository


class ExplainabilityRepository:
    """Queries detection evidence and analyst-note history for explanations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_detections(self, *, page: int, page_size: int, search: str | None = None, detection_id: UUID | None = None, prediction: str | None = None, risk_level: str | None = None, model_name: str | None = None, model_version_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None) -> tuple[list[dict[str, Any]], int]:
        statement = select(DetectionRecord, RiskAssessment, BehavioralResult, MLModelVersion, MLModelDefinition, Email, DetectionInput)
        statement = statement.outerjoin(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id)
        statement = statement.outerjoin(BehavioralResult, BehavioralResult.detection_id == DetectionRecord.id)
        statement = statement.join(MLModelVersion, MLModelVersion.id == DetectionRecord.model_version_id)
        statement = statement.join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id)
        statement = statement.outerjoin(Email, Email.id == DetectionRecord.email_id)
        statement = statement.outerjoin(DetectionInput, DetectionInput.id == DetectionRecord.input_id)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(func.cast(DetectionRecord.id, str).ilike(term), DetectionRecord.predicted_label.ilike(term), Email.sender.ilike(term), Email.subject.ilike(term), DetectionInput.filename.ilike(term), DetectionInput.sender.ilike(term), DetectionInput.subject.ilike(term), MLModelDefinition.name.ilike(term)))
        if prediction:
            filters.append(DetectionRecord.predicted_label == prediction)
        if risk_level:
            filters.append(RiskAssessment.level == risk_level)
        if detection_id:
            filters.append(DetectionRecord.id == detection_id)
        if model_name:
            filters.append(MLModelDefinition.name.ilike(f"%{model_name.strip()}%"))
        if model_version_id:
            filters.append(DetectionRecord.model_version_id == model_version_id)
        if from_date:
            filters.append(DetectionRecord.created_at >= from_date)
        if to_date:
            filters.append(DetectionRecord.created_at <= to_date)
        if filters:
            statement = statement.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        rows = self.db.execute(statement.order_by(DetectionRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return [InvestigationRepository.detection_payload(*row) for row in rows], total

    def get_detection(self, detection_id: UUID) -> dict[str, Any] | None:
        rows, _ = self.list_detections(page=1, page_size=1, detection_id=detection_id)
        return next((item for item in rows if item["id"] == detection_id), None)

    def detection_exists(self, detection_id: UUID) -> bool:
        return self.db.scalar(select(DetectionRecord.id).where(DetectionRecord.id == detection_id)) is not None

    def note(self, note_id: UUID) -> AnalystNote | None:
        return self.db.get(AnalystNote, note_id)

    def notes_for_detection(self, detection_id: UUID) -> list[AnalystNote]:
        statement = select(AnalystNote).where(AnalystNote.detection_id == detection_id).order_by(AnalystNote.created_at.desc())
        return list(self.db.scalars(statement).all())

    def note_events(self, note_id: UUID) -> list[AnalystNoteEvent]:
        statement = select(AnalystNoteEvent).where(AnalystNoteEvent.note_id == note_id).order_by(AnalystNoteEvent.created_at.desc())
        return list(self.db.scalars(statement).all())

    def add_note(self, note: AnalystNote) -> None:
        self.db.add(note)

    def add_note_event(self, event: AnalystNoteEvent) -> None:
        self.db.add(event)

    def flush(self) -> None:
        self.db.flush()
