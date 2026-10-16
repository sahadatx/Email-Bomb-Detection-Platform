from datetime import datetime
from uuid import UUID

from sqlalchemy import String, case, func, or_, select
from sqlalchemy.orm import Session

from ..models import AuditEvent


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, event_id: UUID):
        return self.db.get(AuditEvent, event_id)

    def list(self, *, page=1, page_size=30, search=None, action=None, actor_id=None, status=None, severity=None, source=None, ip_address=None, from_date=None, to_date=None, sort_by="created_at", sort_order="desc"):
        query = select(AuditEvent)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(AuditEvent.actor_name.ilike(term), AuditEvent.action.ilike(term), AuditEvent.target_label.ilike(term), AuditEvent.target_id.ilike(term), AuditEvent.ip_address.ilike(term), func.cast(AuditEvent.id, String).ilike(term)))
        for column, value in ((AuditEvent.action, action), (AuditEvent.actor_id, actor_id), (AuditEvent.status, status), (AuditEvent.severity, severity), (AuditEvent.source, source)):
            if value:
                filters.append(column == value)
        if ip_address:
            filters.append(AuditEvent.ip_address.ilike(f"%{ip_address.strip()}%"))
        if from_date:
            filters.append(AuditEvent.created_at >= from_date)
        if to_date:
            filters.append(AuditEvent.created_at <= to_date)
        if filters:
            query = query.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        sortable = {"created_at": AuditEvent.created_at, "actor_name": AuditEvent.actor_name, "action": AuditEvent.action, "status": AuditEvent.status, "severity": AuditEvent.severity, "source": AuditEvent.source}
        column = sortable.get(sort_by, AuditEvent.created_at)
        order = column.asc() if sort_order == "asc" else column.desc()
        rows = list(self.db.scalars(query.order_by(order, AuditEvent.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
        return rows, total

    def summary(self, *, from_date: datetime | None = None, to_date: datetime | None = None):
        query = select(
            func.count(AuditEvent.id),
            func.coalesce(func.sum(case((AuditEvent.status == "failure", 1), else_=0)), 0),
            func.coalesce(func.sum(case((AuditEvent.severity.in_(("critical", "high", "medium", "low")), 1), else_=0)), 0),
            func.count(func.distinct(AuditEvent.actor_id)),
        )
        filters = []
        if from_date:
            filters.append(AuditEvent.created_at >= from_date)
        if to_date:
            filters.append(AuditEvent.created_at <= to_date)
        if filters:
            query = query.where(*filters)
        total, failed, security, active_users = self.db.execute(query).one()
        return {"total_events": int(total or 0), "failed_actions": int(failed or 0), "security_events": int(security or 0), "active_users": int(active_users or 0)}
