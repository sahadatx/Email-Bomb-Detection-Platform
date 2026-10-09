from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import InvestigationReport, InvestigationReportEvent


class ReportingRepository:
    """Report persistence queries and audit event writes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, report_id: UUID) -> InvestigationReport | None:
        return self.db.get(InvestigationReport, report_id)

    def list_reports(self, *, page: int, page_size: int, search: str | None = None, report_type: str | None = None, report_status: str | None = None, output_format: str | None = None, created_by: str | None = None, detection_id: UUID | None = None, created_from: datetime | None = None, created_to: datetime | None = None, generated_from: datetime | None = None, generated_to: datetime | None = None) -> tuple[list[InvestigationReport], int]:
        statement = select(InvestigationReport)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(InvestigationReport.title.ilike(term), InvestigationReport.description.ilike(term), func.cast(InvestigationReport.id, str).ilike(term), func.cast(InvestigationReport.detection_ids, str).ilike(term)))
        if report_type:
            filters.append(InvestigationReport.report_type == report_type)
        if report_status:
            filters.append(InvestigationReport.status == report_status)
        if output_format:
            filters.append(InvestigationReport.output_format == output_format)
        if created_by:
            filters.append(InvestigationReport.created_by == created_by)
        if detection_id:
            filters.append(func.cast(InvestigationReport.detection_ids, str).ilike(f"%{detection_id}%"))
        if created_from:
            filters.append(InvestigationReport.created_at >= created_from)
        if created_to:
            filters.append(InvestigationReport.created_at <= created_to)
        if generated_from:
            filters.append(InvestigationReport.generated_at >= generated_from)
        if generated_to:
            filters.append(InvestigationReport.generated_at <= generated_to)
        if filters:
            statement = statement.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        records = list(self.db.scalars(statement.order_by(InvestigationReport.created_at.desc(), InvestigationReport.id).offset((page - 1) * page_size).limit(page_size)).all())
        return records, total

    def report_summary(self) -> dict[str, int]:
        result = {"total": 0, "generated": 0, "draft": 0, "failed": 0, "archived": 0}
        for state, count in self.db.execute(select(InvestigationReport.status, func.count()).group_by(InvestigationReport.status)):
            if state in result:
                result[state] = int(count)
                result["total"] += int(count)
        return result

    def events(self, report_id: UUID) -> list[InvestigationReportEvent]:
        statement = select(InvestigationReportEvent).where(InvestigationReportEvent.report_id == report_id).order_by(InvestigationReportEvent.created_at.desc())
        return list(self.db.scalars(statement).all())

    def add(self, report: InvestigationReport) -> None:
        self.db.add(report)

    def add_event(self, event: InvestigationReportEvent) -> None:
        self.db.add(event)

    def flush(self) -> None:
        self.db.flush()
