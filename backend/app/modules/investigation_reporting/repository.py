from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.detection.models import BehavioralResult, DetectionInput, DetectionRecord, RiskAssessment
from app.modules.emails.models import Email
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion
from app.modules.users.models import User
from .models import AnalystNote, AnalystNoteEvent, EvidenceRecord, InvestigationEvidenceEvent, InvestigationReport, InvestigationReportEvent


class InvestigationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def detection_exists(self, detection_id: UUID) -> bool:
        return self.db.scalar(select(DetectionRecord.id).where(DetectionRecord.id == detection_id)) is not None

    def email_exists(self, email_id: UUID) -> bool:
        return self.db.scalar(select(Email.id).where(Email.id == email_id)) is not None

    def list_detections(self, *, page: int, page_size: int, search: str | None = None, detection_id: UUID | None = None, prediction: str | None = None, risk_level: str | None = None, model_version_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None) -> tuple[list[dict[str, Any]], int]:
        stmt = select(DetectionRecord, RiskAssessment, BehavioralResult, MLModelVersion, MLModelDefinition, Email, DetectionInput).outerjoin(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id).outerjoin(BehavioralResult, BehavioralResult.detection_id == DetectionRecord.id).join(MLModelVersion, MLModelVersion.id == DetectionRecord.model_version_id).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).outerjoin(Email, Email.id == DetectionRecord.email_id).outerjoin(DetectionInput, DetectionInput.id == DetectionRecord.input_id)
        conditions = []
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(or_(func.cast(DetectionRecord.id, str).ilike(pattern), DetectionRecord.predicted_label.ilike(pattern), Email.sender.ilike(pattern), Email.subject.ilike(pattern), DetectionInput.filename.ilike(pattern), DetectionInput.sender.ilike(pattern), DetectionInput.subject.ilike(pattern), MLModelDefinition.name.ilike(pattern)))
        if prediction:
            conditions.append(DetectionRecord.predicted_label == prediction)
        if detection_id:
            conditions.append(DetectionRecord.id == detection_id)
        if risk_level:
            conditions.append(RiskAssessment.level == risk_level)
        if model_version_id:
            conditions.append(DetectionRecord.model_version_id == model_version_id)
        if from_date:
            conditions.append(DetectionRecord.created_at >= from_date)
        if to_date:
            conditions.append(DetectionRecord.created_at <= to_date)
        if conditions:
            stmt = stmt.where(*conditions)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.execute(stmt.order_by(DetectionRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return [self.detection_payload(*row) for row in rows], int(total)

    @staticmethod
    def detection_payload(detection, risk, behavior, version, model, email, input_row) -> dict[str, Any]:
        return {
            "id": detection.id, "email_id": detection.email_id, "input_id": detection.input_id,
            "predicted_label": detection.predicted_label, "confidence": detection.confidence,
            "status": detection.status, "created_at": detection.created_at,
            "feature_snapshot": detection.feature_snapshot or {}, "error_message": detection.error_message,
            "sender": email.sender if email else (input_row.sender if input_row else None),
            "email_subject": email.subject if email else (input_row.subject if input_row else None),
            "model_version_id": version.id, "model_name": model.name, "algorithm": model.algorithm,
            "model_type": model.model_type, "version": version.version,
            "risk": {"id": risk.id, "score": risk.score, "level": risk.level, "status": risk.status, "factors": risk.factors or []} if risk else None,
            "behavioral": {"id": behavior.id, "status": behavior.status, "summary": behavior.summary, "metrics": behavior.metrics or {}, "anomalies": behavior.anomalies or []} if behavior else None,
        }

    def get_detection(self, detection_id: UUID) -> dict[str, Any] | None:
        rows, _ = self.list_detections(page=1, page_size=1, detection_id=detection_id)
        for row in rows:
            if row["id"] == detection_id:
                return row
        return None

    def list_evidence(self, *, page: int, page_size: int, search: str | None = None, evidence_type: str | None = None, review_status: str | None = None, detection_id: UUID | None = None, source_email_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None) -> tuple[list[EvidenceRecord], int]:
        stmt = select(EvidenceRecord)
        conditions = []
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(or_(EvidenceRecord.name.ilike(pattern), EvidenceRecord.description.ilike(pattern), EvidenceRecord.observed_value.ilike(pattern), func.cast(EvidenceRecord.id, str).ilike(pattern), func.cast(EvidenceRecord.detection_id, str).ilike(pattern)))
        if evidence_type: conditions.append(EvidenceRecord.evidence_type == evidence_type)
        if review_status: conditions.append(EvidenceRecord.review_status == review_status)
        if detection_id: conditions.append(EvidenceRecord.detection_id == detection_id)
        if source_email_id: conditions.append(EvidenceRecord.source_email_id == source_email_id)
        if from_date: conditions.append(EvidenceRecord.collected_at >= from_date)
        if to_date: conditions.append(EvidenceRecord.collected_at <= to_date)
        if conditions: stmt = stmt.where(*conditions)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(self.db.scalars(stmt.order_by(EvidenceRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all())
        return rows, int(total)

    def evidence_summary(self) -> dict[str, int]:
        result = {"total": 0, "verified": 0, "pending": 0, "flagged": 0, "rejected": 0}
        for status, count in self.db.execute(select(EvidenceRecord.review_status, func.count()).group_by(EvidenceRecord.review_status)):
            result["total"] += int(count)
            if status in result: result[status] = int(count)
        return result

    def evidence(self, evidence_id: UUID) -> EvidenceRecord | None:
        return self.db.get(EvidenceRecord, evidence_id)

    def evidence_events(self, evidence_id: UUID) -> list[InvestigationEvidenceEvent]:
        return list(self.db.scalars(select(InvestigationEvidenceEvent).where(InvestigationEvidenceEvent.evidence_id == evidence_id).order_by(InvestigationEvidenceEvent.created_at.desc())).all())

    def notes_for_detection(self, detection_id: UUID) -> list[AnalystNote]:
        return list(self.db.scalars(select(AnalystNote).where(AnalystNote.detection_id == detection_id).order_by(AnalystNote.created_at.desc())).all())

    def note(self, note_id: UUID) -> AnalystNote | None:
        return self.db.get(AnalystNote, note_id)

    def note_events(self, note_id: UUID) -> list[AnalystNoteEvent]:
        return list(self.db.scalars(select(AnalystNoteEvent).where(AnalystNoteEvent.note_id == note_id).order_by(AnalystNoteEvent.created_at.desc())).all())

    def report(self, report_id: UUID) -> InvestigationReport | None:
        return self.db.get(InvestigationReport, report_id)

    def list_reports(self, *, page: int, page_size: int, search: str | None = None, report_type: str | None = None, report_status: str | None = None, output_format: str | None = None) -> tuple[list[InvestigationReport], int]:
        stmt = select(InvestigationReport)
        conditions = []
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(or_(InvestigationReport.title.ilike(pattern), InvestigationReport.description.ilike(pattern), func.cast(InvestigationReport.id, str).ilike(pattern)))
        if report_type: conditions.append(InvestigationReport.report_type == report_type)
        if report_status: conditions.append(InvestigationReport.status == report_status)
        if output_format: conditions.append(InvestigationReport.output_format == output_format)
        if conditions: stmt = stmt.where(*conditions)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(self.db.scalars(stmt.order_by(InvestigationReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all())
        return rows, int(total)

    def report_summary(self) -> dict[str, int]:
        result = {"total": 0, "generated": 0, "draft": 0, "failed": 0, "archived": 0}
        for status, count in self.db.execute(select(InvestigationReport.status, func.count()).group_by(InvestigationReport.status)):
            if status == "archived": continue
            result["total"] += int(count)
            if status in result: result[status] = int(count)
        return result

    def report_events(self, report_id: UUID) -> list[InvestigationReportEvent]:
        return list(self.db.scalars(select(InvestigationReportEvent).where(InvestigationReportEvent.report_id == report_id).order_by(InvestigationReportEvent.created_at.desc())).all())

    def user_name(self, user_id: UUID) -> str | None:
        user = self.db.get(User, user_id)
        return user.full_name if user else None
