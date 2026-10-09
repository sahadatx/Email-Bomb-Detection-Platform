from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from ..errors import InvestigationError
from ..models import InvestigationReport, InvestigationReportEvent
from ..repository import InvestigationRepository
from ..integrations.detection_adapter import DetectionAdapter
from ..integrations.risk_adapter import RiskAdapter
from ..integrations.behavioral_adapter import BehavioralAdapter
from ..explainability.service import ExplainabilityService
from ..evidence.service import EvidenceService
from .repository import ReportingRepository
from .generators.json_generator import JsonReportGenerator
from .generators.pdf_generator import PdfReportGenerator


class ReportRenderingService:
    """Selects a real serializer for each supported downloadable format."""

    def __init__(self) -> None:
        self._generators = {"json": JsonReportGenerator(), "pdf": PdfReportGenerator()}

    def generate(self, output_format: str, snapshot: dict):
        generator = self._generators.get(output_format)
        if generator is None:
            raise ValueError(f"Unsupported report format: {output_format}")
        return generator.generate(snapshot)


class ReportingService:
    """Report lifecycle: validate sources, snapshot, audit, duplicate and archive."""

    ALLOWED_SECTIONS = {
        "executive_summary", "detection_summary", "explainability", "evidence",
        "risk_analysis", "behavioral_analysis", "analyst_notes", "technical_appendix",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReportingRepository(db)
        self.source_repository = InvestigationRepository(db)
        self.detections = DetectionAdapter(db)
        self.risk = RiskAdapter()
        self.behavior = BehavioralAdapter()
        self.explainability = ExplainabilityService(db)
        self.evidence = EvidenceService(db)

    @staticmethod
    def _page(total: int, page: int, page_size: int) -> dict[str, int]:
        return {"page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def list(self, *, page: int, page_size: int, search: str | None = None, report_type: str | None = None, report_status: str | None = None, output_format: str | None = None, created_by: str | None = None, detection_id: UUID | None = None, created_from: datetime | None = None, created_to: datetime | None = None, generated_from: datetime | None = None, generated_to: datetime | None = None) -> dict[str, Any]:
        items, total = self.repository.list_reports(page=page, page_size=page_size, search=search, report_type=report_type, report_status=report_status, output_format=output_format, created_by=created_by, detection_id=detection_id, created_from=created_from, created_to=created_to, generated_from=generated_from, generated_to=generated_to)
        return {"items": items, "total": total, "summary": self.repository.report_summary(), **self._page(total, page, page_size)}

    def preview(self, actor_id: str, values: dict[str, Any]) -> dict[str, Any]:
        """Render a transient snapshot without persisting a draft or audit event."""
        self._validate_payload(values)
        ids = [str(value) for value in values["detection_ids"]]
        preview_report = InvestigationReport(
            id=uuid4(), title=values["title"], description=values.get("description"),
            report_type=values["report_type"], output_format=values["output_format"],
            status="draft", detection_ids=ids, sections=list(values["sections"]),
            analyst_notes=values.get("analyst_notes"), version=1, created_by=actor_id,
        )
        return self._build_snapshot(preview_report)

    def get(self, report_id: UUID) -> InvestigationReport | None:
        return self.repository.get(report_id)

    def create(self, actor_id: str, values: dict[str, Any]) -> InvestigationReport:
        self._validate_payload(values)
        data = dict(values)
        ids = [str(value) for value in data.pop("detection_ids")]
        data["detection_ids"] = ids
        data["configuration"] = {"detection_ids": ids, "sections": list(data["sections"]), "output_format": data["output_format"]}
        report = InvestigationReport(created_by=actor_id, **data)
        self.db.add(report)
        self.db.flush()
        self._event(report.id, actor_id, "created")
        return report

    def update(self, report_id: UUID, actor_id: str, values: dict[str, Any]) -> InvestigationReport:
        report = self.get(report_id)
        if report is None:
            raise InvestigationError("Report not found.")
        if report.status != "draft":
            raise InvestigationError("Only draft reports can be edited. Duplicate a generated report to create a new draft.")
        self._validate_payload(values)
        data = dict(values)
        ids = [str(value) for value in data.pop("detection_ids")]
        data["detection_ids"] = ids
        data["configuration"] = {"detection_ids": ids, "sections": list(data["sections"]), "output_format": data["output_format"]}
        for key, value in data.items():
            setattr(report, key, value)
        report.version += 1
        report.updated_at = datetime.now(timezone.utc)
        self._event(report.id, actor_id, "updated")
        self.db.flush()
        return report

    def generate(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        report = self.get(report_id)
        if report is None:
            raise InvestigationError("Report not found.")
        if report.status not in {"draft", "failed"}:
            raise InvestigationError("Only draft or failed reports can be generated. Duplicate a generated report to create a new snapshot.")
        try:
            snapshot = self._build_snapshot(report)
            report.snapshot = jsonable_encoder(snapshot)
            report.status = "generated"
            report.error_summary = None
            report.generated_at = datetime.now(timezone.utc)
            report.updated_at = report.generated_at
            self._event(report.id, actor_id, "generated")
        except Exception as exc:
            report.status = "failed"
            report.error_summary = str(exc)[:2000]
            report.updated_at = datetime.now(timezone.utc)
            self._event(report.id, actor_id, "generation_failed")
        self.db.flush()
        return report

    def duplicate(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        source = self.get(report_id)
        if source is None:
            raise InvestigationError("Report not found.")
        clone = InvestigationReport(
            title=f"{source.title} (Copy)", description=source.description,
            report_type=source.report_type, output_format=source.output_format,
            status="draft", detection_ids=list(source.detection_ids), sections=list(source.sections),
            analyst_notes=source.analyst_notes, configuration=dict(source.configuration),
            version=1, created_by=actor_id,
        )
        self.db.add(clone)
        self.db.flush()
        self._event(clone.id, actor_id, "duplicated")
        return clone

    def archive(self, report_id: UUID, actor_id: str) -> InvestigationReport:
        report = self.get(report_id)
        if report is None:
            raise InvestigationError("Report not found.")
        if report.status == "archived":
            raise InvestigationError("Report is already archived.")
        report.status = "archived"
        report.archived_at = datetime.now(timezone.utc)
        report.updated_at = report.archived_at
        self._event(report.id, actor_id, "archived")
        self.db.flush()
        return report

    def _validate_payload(self, values: dict[str, Any]) -> None:
        ids = values.get("detection_ids") or []
        if not ids:
            raise InvestigationError("Select at least one detection for the report.")
        if len(ids) > 100:
            raise InvestigationError("A report can include at most 100 detections.")
        if len(set(ids)) != len(ids):
            raise InvestigationError("Detection records must be unique.")
        missing = [str(item) for item in ids if not self.detections.exists(item)]
        if missing:
            raise InvestigationError(f"Detection '{missing[0]}' does not exist.")
        sections = values.get("sections") or []
        invalid = set(sections) - self.ALLOWED_SECTIONS
        if invalid:
            raise InvestigationError(f"Unsupported report section: {sorted(invalid)[0]}.")
        if values.get("output_format") not in {"json", "pdf"}:
            raise InvestigationError("Supported report formats are JSON and PDF.")

    def _build_snapshot(self, report: InvestigationReport) -> dict[str, Any]:
        ids = [UUID(item) for item in report.detection_ids]
        source_rows = []
        for detection_id in ids:
            detection = self.detections.get(detection_id)
            if detection is None:
                raise InvestigationError(f"Detection '{detection_id}' no longer exists.")
            detection = {**detection, "risk": self.risk.from_detection(detection), "behavioral": self.behavior.from_detection(detection)}
            if "explainability" in report.sections:
                detection["explanation"] = self.explainability.explain_record(detection, include_model_explanation=True)["explanation"]
            source_rows.append(detection)
        summary = {
            "total_detections": len(source_rows),
            "bomb_detections": sum(str(row.get("predicted_label", "")).lower() == "bomb" for row in source_rows),
            "normal_detections": sum(str(row.get("predicted_label", "")).lower() == "normal" for row in source_rows),
            "failed_detections": sum(row.get("status") != "completed" for row in source_rows),
        }
        # Keep the common record table limited to report-safe summary fields.
        # Detailed values are included only in the explicit sections below.
        detections = []
        for row in source_rows:
            summary_row = {key: row.get(key) for key in ("id", "email_id", "input_id", "predicted_label", "confidence", "status", "created_at", "sender", "email_subject", "model_version_id", "model_name", "algorithm", "model_type", "version")}
            if "risk_analysis" in report.sections:
                summary_row["risk"] = row.get("risk") or {"status": "unavailable", "score": None, "level": "unavailable"}
            detections.append(summary_row)
        snapshot: dict[str, Any] = {
            "report_id": str(report.id), "title": report.title, "description": report.description,
            "report_type": report.report_type, "format": report.output_format,
            "version": report.version, "sections": list(report.sections),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if "executive_summary" in report.sections:
            snapshot["executive_summary"] = summary
        if "detection_summary" in report.sections:
            snapshot["detection_summary"] = list(detections)
            snapshot["detections"] = detections
        if "risk_analysis" in report.sections:
            snapshot["risk_analysis"] = [{"detection_id": str(row["id"]), **(row.get("risk") or {"status": "unavailable", "score": None, "level": "unavailable", "factors": []})} for row in source_rows]
        if "behavioral_analysis" in report.sections:
            snapshot["behavioral_analysis"] = [{"detection_id": str(row["id"]), **(row.get("behavioral") or {"status": "unavailable", "summary": "", "metrics": {}, "anomalies": []})} for row in source_rows]
        if "explainability" in report.sections:
            snapshot["explainability"] = [{"detection_id": str(row["id"]), "explanation": row.get("explanation")} for row in source_rows]
        if "evidence" in report.sections:
            records = self.evidence.for_detections(ids)
            snapshot["evidence"] = [self.evidence.serialize(record) for record in records]
        if "analyst_notes" in report.sections:
            notes = []
            for detection_id in ids:
                notes.extend(self.source_repository.notes_for_detection(detection_id))
            snapshot["analyst_notes"] = [{"id": str(note.id), "detection_id": str(note.detection_id), "title": note.title, "body": note.body, "category": note.category, "author_id": str(note.author_id), "created_at": note.created_at.isoformat()} for note in notes]
        if "technical_appendix" in report.sections:
            snapshot["technical_appendix"] = [{"detection_id": str(row["id"]), "model_version_id": str(row.get("model_version_id")) if row.get("model_version_id") else None, "model_name": row.get("model_name"), "algorithm": row.get("algorithm"), "model_type": row.get("model_type"), "model_version": row.get("version"), "feature_snapshot": row.get("feature_snapshot") or {}, "inference_status": row.get("status"), "error_message": row.get("error_message")} for row in source_rows]
        if report.analyst_notes and "analyst_notes" in report.sections:
            snapshot["report_analyst_notes"] = report.analyst_notes
        return snapshot

    def _event(self, report_id: UUID, actor_id: str, action: str) -> None:
        self.db.add(InvestigationReportEvent(report_id=report_id, actor_id=actor_id, action=action))
