from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import AuditEvent, SecurityEvent
from .exporters.csv_exporter import export_csv
from .exporters.json_exporter import export_json
from .repository import AuditRepository

SENSITIVE_PARTS = ("password", "passwd", "token", "secret", "api_key", "apikey", "authorization", "private_key", "raw_content", "email_body", "message_body")


def redact(value):
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if any("".join(ch for ch in part if ch.isalnum()) in "".join(ch for ch in str(key).lower() if ch.isalnum()) for part in SENSITIVE_PARTS) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def event_dict(event: AuditEvent):
    return {"id": str(event.id), "actor_id": event.actor_id, "actor_name": event.actor_name, "actor_role": event.actor_role, "action": event.action, "target_type": event.target_type, "target_id": event.target_id, "target_label": event.target_label, "status": event.status, "severity": event.severity, "source": event.source, "ip_address": event.ip_address, "correlation_id": event.correlation_id, "details": redact(event.details or {}), "created_at": event.created_at.isoformat() if event.created_at else None}


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditRepository(db)

    def list(self, **filters):
        rows, total = self.repository.list(**filters)
        return {"items": [event_dict(row) for row in rows], "total": total, "page": filters.get("page", 1), "page_size": filters.get("page_size", 30), "total_pages": max(1, (total + filters.get("page_size", 30) - 1) // filters.get("page_size", 30))}

    def detail(self, event_id: UUID):
        event = self.repository.get(event_id)
        if not event:
            return None
        result = event_dict(event)
        related_filters = []
        if event.actor_id:
            related_filters.append(AuditEvent.actor_id == event.actor_id)
        if event.target_id:
            related_filters.append(AuditEvent.target_id == event.target_id)
        if related_filters:
            related = self.db.scalars(select(AuditEvent).where(AuditEvent.id != event.id, or_(*related_filters)).order_by(AuditEvent.created_at.desc()).limit(10)).all()
            result["related_events"] = [event_dict(row) for row in related]
        else:
            result["related_events"] = []
        return result

    def summary(self, from_date: datetime | None = None, to_date: datetime | None = None):
        result = self.repository.summary(from_date=from_date, to_date=to_date)
        query = select(func.count(SecurityEvent.id))
        if from_date:
            query = query.where(SecurityEvent.occurred_at >= from_date)
        if to_date:
            query = query.where(SecurityEvent.occurred_at <= to_date)
        result["security_events"] = int(self.db.scalar(query) or 0)
        return result

    def export(self, *, format: str, **filters):
        filters.update(page=1, page_size=min(max(filters.pop("limit", 1000), 1), 10000))
        rows, _ = self.repository.list(**filters)
        data = [event_dict(row) for row in rows]
        if format == "csv":
            return "text/csv; charset=utf-8", "audit-events.csv", export_csv(data)
        return "application/json", "audit-events.json", export_json(data)


def record_audit(db: Session, *, actor=None, action: str, target_type: str | None = None, target_id: str | None = None, target_label: str | None = None, status: str = "success", severity: str | None = None, source: str = "Administration", ip_address: str | None = None, correlation_id: str | None = None, details: dict | None = None) -> AuditEvent:
    role = getattr(getattr(actor, "role", None), "value", getattr(actor, "role", None))
    event = AuditEvent(actor_id=getattr(actor, "id", None), actor_name=getattr(actor, "full_name", None) or getattr(actor, "username", "System"), actor_role=role, action=action, target_type=target_type, target_id=str(target_id) if target_id is not None else None, target_label=target_label, status=status, severity=severity, source=source, ip_address=ip_address, correlation_id=correlation_id, details=redact(details or {}))
    db.add(event)
    return event
