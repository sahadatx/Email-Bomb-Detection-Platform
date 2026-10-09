from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from .errors import InvestigationError
from .models import AnalystNote, AnalystNoteEvent, EvidenceRecord, InvestigationReport
from .explainability.service import ExplainabilityService
from .evidence.service import EvidenceService
from .reporting.service import ReportingService, ReportRenderingService


def render_report_pdf(snapshot: dict[str, Any]) -> bytes:
    """Compatibility entry point used by older integrations."""
    return ReportRenderingService().generate("pdf", snapshot).body


class InvestigationService:
    """Application facade retaining API compatibility over domain services."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.explainability = ExplainabilityService(db)
        self.evidence_service = EvidenceService(db)
        self.reporting_service = ReportingService(db)
        self.report_renderer = ReportRenderingService()

    @staticmethod
    def page(total: int, page: int, page_size: int) -> dict[str, int]:
        return {"page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    # Explainability query and analyst annotation use cases
    def explanations(self, *, page: int, page_size: int, search: str | None, detection_id: UUID | None, prediction: str | None, risk_level: str | None, model_name: str | None, model_version_id: UUID | None, from_date: datetime | None, to_date: datetime | None) -> dict[str, Any]:
        return self.explainability.list(page=page, page_size=page_size, search=search, detection_id=detection_id, prediction=prediction, risk_level=risk_level, model_name=model_name, model_version_id=model_version_id, from_date=from_date, to_date=to_date)

    def explanation_payload(self, detection: dict[str, Any]) -> dict[str, Any]:
        return self.explainability.explain_record(detection)

    def explanation_detail(self, detection_id: UUID) -> dict[str, Any]:
        return self.explainability.detail(detection_id)

    def add_note(self, detection_id: UUID, actor_id: str, values: dict[str, Any]) -> AnalystNote:
        return self.explainability.add_note(detection_id, actor_id, values)

    def update_note(self, note_id: UUID, actor_id: str, values: dict[str, Any], is_admin: bool = False) -> AnalystNote:
        return self.explainability.update_note(note_id, actor_id, values, is_admin=is_admin)

    def delete_note(self, note_id: UUID, actor_id: str, is_admin: bool) -> None:
        self.explainability.delete_note(note_id, actor_id, is_admin=is_admin)

    def note_audit(self, note_id: UUID):
        return self.explainability.note_audit(note_id)

    # Evidence compatibility methods; all business rules live in EvidenceService.
    def evidence_list(self, **filters: Any) -> dict[str, Any]:
        return self.evidence_service.list(**filters)

    def create_evidence(self, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        return self.evidence_service.create(actor_id, values)

    def update_evidence(self, evidence_id: UUID, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        return self.evidence_service.update(evidence_id, actor_id, values)

    def review_evidence(self, evidence_id: UUID, actor_id: str, values: dict[str, Any]) -> EvidenceRecord:
        return self.evidence_service.review(evidence_id, actor_id, values)

    def evidence_detail(self, evidence_id: UUID) -> dict[str, Any]:
        return self.evidence_service.detail(evidence_id)

    def evidence_export(self, **filters: Any) -> list[EvidenceRecord]:
        return self.evidence_service.export(**filters)

    @staticmethod
    def evidence_json(item: EvidenceRecord) -> dict[str, Any]:
        return EvidenceService.serialize(item)

    # Report compatibility methods; lifecycle and snapshot creation live in ReportingService.
    def report_list(self, **filters: Any) -> dict[str, Any]:
        return self.reporting_service.list(**filters)

    def create_report(self, actor_id: str, values: dict[str, Any]) -> InvestigationReport:
        return self.reporting_service.create(actor_id, values)

    def preview_report(self, actor_id: str, values: dict[str, Any]) -> dict[str, Any]:
        return self.reporting_service.preview(actor_id, values)

    def update_report(self, report_id: UUID, actor_id: str, values: dict[str, Any]) -> InvestigationReport:
        return self.reporting_service.update(report_id, actor_id, values)

    def generate_report(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        return self.reporting_service.generate(report_id, actor_id)

    def duplicate_report(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        return self.reporting_service.duplicate(report_id, actor_id)

    def archive_report(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        return self.reporting_service.archive(report_id, actor_id)

    def report_detail(self, report_id: UUID):
        report = self.reporting_service.get(report_id)
        if report is None:
            raise InvestigationError("Report not found.")
        return report

    def report_audit(self, report_id: UUID):
        if self.reporting_service.get(report_id) is None:
            raise InvestigationError("Report not found.")
        return self.reporting_service.repository.events(report_id)

    def rendered_report(self, report: InvestigationReport, *, viewer: bool = False):
        if report.status != "generated" or report.snapshot is None:
            raise InvestigationError("Only generated reports can be downloaded.")
        snapshot = report.snapshot
        if viewer:
            from .http import mask_viewer_report_snapshot
            snapshot = mask_viewer_report_snapshot(snapshot)
        return self.report_renderer.generate(report.output_format, snapshot)
