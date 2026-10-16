from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session

from ..audit.service import record_audit, redact
from ..errors import AdminDomainError
from ..models import AuditEvent, MonitoringRule, SecurityAlert, SecurityEvent
from .validators import validate_condition


def serialize(model):
    output = {}
    for key in model.__table__.columns.keys():
        value = getattr(model, key)
        if key == "details":
            value = redact(value or {})
        output[key] = value.isoformat() if isinstance(value, datetime) else (str(value) if isinstance(value, UUID) else value)
    return output


def matches(rule: MonitoringRule, event: SecurityEvent):
    condition = rule.condition or {}
    if not condition:
        return True
    left = getattr(event, condition["field"], None)
    right = str(condition["value"])
    left = str(left or "")
    return left == right if condition["operator"] == "equals" else right.casefold() in left.casefold()


class SecurityMonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def list_events(self, *, page=1, page_size=30, search=None, severity=None, event_type=None, source=None, status=None, actor_id=None, source_ip=None, from_date=None, to_date=None, sort="occurred_at", order="desc"):
        query = select(SecurityEvent)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(SecurityEvent.title.ilike(term), SecurityEvent.description.ilike(term), SecurityEvent.source_ip.ilike(term), func.cast(SecurityEvent.id, String).ilike(term), func.cast(SecurityEvent.actor_id, String).ilike(term)))
        for column, value in ((SecurityEvent.severity, severity), (SecurityEvent.event_type, event_type), (SecurityEvent.source, source), (SecurityEvent.status, status)):
            if value:
                filters.append(column == value)
        if actor_id:
            filters.append(SecurityEvent.actor_id == actor_id)
        if source_ip:
            filters.append(SecurityEvent.source_ip.ilike(f"%{source_ip.strip()}%"))
        if from_date:
            filters.append(SecurityEvent.occurred_at >= from_date)
        if to_date:
            filters.append(SecurityEvent.occurred_at <= to_date)
        if filters:
            query = query.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        sort_columns = {"occurred_at": SecurityEvent.occurred_at, "severity": SecurityEvent.severity, "event_type": SecurityEvent.event_type, "source": SecurityEvent.source, "status": SecurityEvent.status}
        sort_column = sort_columns.get(sort, SecurityEvent.occurred_at)
        ordering = sort_column.asc() if order == "asc" else sort_column.desc()
        rows = self.db.scalars(query.order_by(ordering, SecurityEvent.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [self._event_dict(row) for row in rows], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def _event_dict(self, event):
        result = serialize(event)
        if event.assigned_to:
            from app.modules.users.models import User
            assignee = self.db.get(User, event.assigned_to)
            result["assignee_name"] = (assignee.full_name or assignee.username) if assignee else "Deleted user"
        else:
            result["assignee_name"] = None
        if event.actor_id:
            from app.modules.users.models import User
            actor = self.db.get(User, event.actor_id)
            result["actor_name"] = (actor.full_name or actor.username) if actor else "Deleted user"
            result["actor_role"] = getattr(actor.role, "value", actor.role) if actor else None
        else:
            result["actor_name"] = "System"
            result["actor_role"] = None
        return result

    def event_detail(self, event_id: UUID):
        event = self.db.get(SecurityEvent, event_id)
        if not event:
            raise AdminDomainError("Security event not found.")
        result = self._event_dict(event)
        if event.related_alert_id:
            alert = self.db.get(SecurityAlert, event.related_alert_id)
            result["alert"] = serialize(alert) if alert else None
        result["history"] = [serialize(row) for row in self.db.scalars(select(AuditEvent).where(AuditEvent.target_type == "security_event", AuditEvent.target_id == str(event_id)).order_by(AuditEvent.created_at.desc())).all()]
        return result

    def transition_event(self, event_id: UUID, values, actor):
        event = self.db.get(SecurityEvent, event_id)
        if not event:
            raise AdminDomainError("Security event not found.")
        allowed = {"new": {"new", "reviewed", "investigating"}, "reviewed": {"reviewed", "investigating"}, "investigating": {"investigating", "reviewed"}}
        status = values.get("status") or event.status
        if status not in allowed.get(event.status, set()):
            raise AdminDomainError(f"Transition from {event.status} to {status} is not allowed.")
        assignee = values.get("assigned_to", event.assigned_to)
        if assignee:
            from app.modules.users.models import User
            user = self.db.get(User, assignee)
            if user is None or not user.is_active or user.is_locked or user.role.value not in {"ADMIN", "SECURITY_ANALYST"}:
                raise AdminDomainError("Assigned analyst was not found.")
        previous = event.status
        event.status = status
        event.assigned_to = assignee
        if "disposition" in values:
            event.disposition = values["disposition"]
        if values.get("note") and values["note"].strip():
            event.investigation_note = values["note"].strip()
        record_audit(self.db, actor=actor, action="security_event.investigated", target_type="security_event", target_id=event.id, target_label=event.title, severity=event.severity, source="Security Monitoring", details={"from": previous, "to": event.status, "assigned_to": event.assigned_to, "disposition": event.disposition, "note": values.get("note")})
        return serialize(event)

    def create_alert_for_event(self, event_id: UUID, actor):
        """Create an analyst initiated alert and keep it linked to its source event."""
        event = self.db.get(SecurityEvent, event_id)
        if not event:
            raise AdminDomainError("Security event not found.")
        if event.related_alert_id:
            existing = self.db.get(SecurityAlert, event.related_alert_id)
            if existing:
                raise AdminDomainError("This event is already linked to an alert.")
        alert = SecurityAlert(
            title=event.title,
            description=event.description,
            severity=event.severity,
            first_seen=event.occurred_at,
            last_seen=event.occurred_at,
            event_count=1,
        )
        self.db.add(alert)
        self.db.flush()
        event.related_alert_id = alert.id
        record_audit(self.db, actor=actor, action="security_alert.created", target_type="security_alert", target_id=alert.id, target_label=alert.title, severity=alert.severity, source="Security Monitoring", details={"event_id": str(event.id), "creation_type": "analyst"})
        return {"alert": serialize(alert), "event": serialize(event)}

    def ingest(self, values, actor=None):
        event = SecurityEvent(**values, status="new")
        if event.occurred_at is None:
            event.occurred_at = datetime.now(timezone.utc)
        elif event.occurred_at.tzinfo is None:
            event.occurred_at = event.occurred_at.replace(tzinfo=timezone.utc)
        else:
            event.occurred_at = event.occurred_at.astimezone(timezone.utc)
        self.db.add(event)
        self.db.flush()
        triggered = []
        rules = self.db.scalars(select(MonitoringRule).where(MonitoringRule.enabled.is_(True), MonitoringRule.event_type.in_([event.event_type, "*"]))).all()
        for rule in rules:
            if not matches(rule, event):
                continue
            deduplication_key = self._deduplication_key(rule, event)
            alert = self.db.scalar(select(SecurityAlert).where(SecurityAlert.rule_id == rule.id, SecurityAlert.deduplication_key == deduplication_key, SecurityAlert.status.in_(("open", "investigating"))).order_by(SecurityAlert.updated_at.desc()).limit(1))
            if alert is None:
                alert = SecurityAlert(title=event.title, description=event.description, severity=rule.severity, rule_id=rule.id, deduplication_key=deduplication_key, first_seen=event.occurred_at, last_seen=event.occurred_at, event_count=1)
                self.db.add(alert)
                self.db.flush()
            else:
                alert.event_count += 1
                alert.last_seen = event.occurred_at
                alert.updated_at = datetime.now(timezone.utc)
            event.related_alert_id = alert.id
            triggered.append(alert)
        record_audit(self.db, actor=actor, action="security_event.ingested", target_type="security_event", target_id=event.id, target_label=event.title, source=event.source, severity=event.severity, details={"event_type": event.event_type, "triggered_alert_count": len(triggered)})
        return {"event": serialize(event), "alerts": [serialize(alert) for alert in triggered]}

    @staticmethod
    def _deduplication_key(rule, event):
        details = event.details or {}
        stable_reference = next((details.get(key) for key in ("correlation_id", "target_id", "email_id", "resource_id") if details.get(key)), None)
        identity = {"rule": str(rule.id), "event_type": event.event_type, "source": event.source, "actor": event.actor_id, "ip": event.source_ip, "reference": stable_reference}
        return hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()

    def summary(self):
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {"critical_alerts": int(self.db.scalar(select(func.count()).select_from(SecurityAlert).where(SecurityAlert.severity == "critical", SecurityAlert.status != "resolved")) or 0), "open_alerts": int(self.db.scalar(select(func.count()).select_from(SecurityAlert).where(SecurityAlert.status == "open")) or 0), "events_today": int(self.db.scalar(select(func.count()).select_from(SecurityEvent).where(SecurityEvent.occurred_at >= day_start)) or 0), "enabled_rules": int(self.db.scalar(select(func.count()).select_from(MonitoringRule).where(MonitoringRule.enabled.is_(True))) or 0)}

    def options(self):
        from app.modules.users.models import User
        sources = self.db.scalars(select(SecurityEvent.source).distinct().order_by(SecurityEvent.source)).all()
        event_types = self.db.scalars(select(SecurityEvent.event_type).distinct().order_by(SecurityEvent.event_type)).all()
        actors = self.db.execute(select(SecurityEvent.actor_id, User.full_name, User.username).outerjoin(User, User.id == SecurityEvent.actor_id).where(SecurityEvent.actor_id.is_not(None)).distinct()).all()
        return {"sources": sources, "event_types": event_types, "actors": [{"id": actor_id, "name": full_name or username or "Deleted user"} for actor_id, full_name, username in actors]}

    def list_alerts(self, *, page=1, page_size=30, search=None, severity=None, status=None, assigned_to=None, from_date=None, to_date=None, sort="updated_at", order="desc"):
        query = select(SecurityAlert)
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(SecurityAlert.title.ilike(term), SecurityAlert.description.ilike(term), func.cast(SecurityAlert.id, String).ilike(term)))
        if severity:
            filters.append(SecurityAlert.severity == severity)
        if status:
            filters.append(SecurityAlert.status == status)
        if assigned_to == "__unassigned__":
            filters.append(SecurityAlert.assigned_to.is_(None))
        elif assigned_to:
            filters.append(SecurityAlert.assigned_to == assigned_to)
        if from_date:
            filters.append(SecurityAlert.last_seen >= from_date)
        if to_date:
            filters.append(SecurityAlert.last_seen <= to_date)
        if filters:
            query = query.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        sort_columns = {"updated_at": SecurityAlert.updated_at, "first_seen": SecurityAlert.first_seen, "last_seen": SecurityAlert.last_seen, "severity": SecurityAlert.severity, "status": SecurityAlert.status, "event_count": SecurityAlert.event_count}
        sort_column = sort_columns.get(sort, SecurityAlert.updated_at)
        ordering = sort_column.asc() if order == "asc" else sort_column.desc()
        rows = self.db.scalars(query.order_by(ordering, SecurityAlert.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": self._alerts_dict(rows), "total": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def _alerts_dict(self, rows):
        from app.modules.users.models import User
        user_ids = {row.assigned_to for row in rows if row.assigned_to}
        users = {user.id: (user.full_name or user.username) for user in self.db.scalars(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
        return [{**serialize(row), "assignee_name": users.get(row.assigned_to, "Deleted user" if row.assigned_to else None)} for row in rows]

    def alert_detail(self, alert_id: UUID):
        alert = self.db.get(SecurityAlert, alert_id)
        if not alert:
            raise AdminDomainError("Alert not found.")
        result = self._alerts_dict([alert])[0]
        result["rule"] = serialize(self.db.get(MonitoringRule, alert.rule_id)) if alert.rule_id else None
        result["events"] = [serialize(row) for row in self.db.scalars(select(SecurityEvent).where(SecurityEvent.related_alert_id == alert_id).order_by(SecurityEvent.occurred_at.desc()).limit(100)).all()]
        result["history"] = [serialize(row) for row in self.db.scalars(select(AuditEvent).where(AuditEvent.target_type == "security_alert", AuditEvent.target_id == str(alert_id)).order_by(AuditEvent.created_at.desc())).all()]
        return result

    def transition_alert(self, alert_id: UUID, values, actor):
        alert = self.db.get(SecurityAlert, alert_id)
        if not alert:
            raise AdminDomainError("Alert not found.")
        allowed = {"open": {"open", "investigating", "resolved"}, "investigating": {"investigating", "resolved", "open"}, "resolved": {"resolved", "open"}}
        if values["status"] not in allowed[alert.status]:
            raise AdminDomainError(f"Transition from {alert.status} to {values['status']} is not allowed.")
        if values["status"] == "resolved" and not (values.get("resolution_note") or "").strip():
            raise AdminDomainError("A resolution note is required.")
        assignee = values.get("assigned_to", alert.assigned_to)
        if assignee:
            from app.modules.users.models import User
            user = self.db.get(User, assignee)
            if user is None or not user.is_active or user.is_locked or user.role.value not in {"ADMIN", "SECURITY_ANALYST"}:
                raise AdminDomainError("Assigned analyst was not found.")
        old_status = alert.status
        alert.status = values["status"]
        alert.assigned_to = assignee
        if alert.status == "open" and old_status == "resolved":
            alert.resolution_note = None
        elif values.get("resolution_note"):
            alert.resolution_note = values["resolution_note"].strip()
        alert.updated_at = datetime.now(timezone.utc)
        record_audit(self.db, actor=actor, action="security_alert.status_changed" if old_status != alert.status else "security_alert.updated", target_type="security_alert", target_id=alert.id, target_label=alert.title, severity=alert.severity, source="Security Monitoring", details={"from": old_status, "to": alert.status, "assigned_to": alert.assigned_to, "resolution_note": alert.resolution_note, "investigation_note": values.get("note")})
        return serialize(alert)

    def list_rules(self, *, page=1, page_size=30, search=None, enabled=None):
        query = select(MonitoringRule)
        filters = []
        if search:
            filters.append(or_(MonitoringRule.name.ilike(f"%{search.strip()}%"), MonitoringRule.event_type.ilike(f"%{search.strip()}%")))
        if enabled is not None:
            filters.append(MonitoringRule.enabled.is_(enabled))
        if filters:
            query = query.where(*filters)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = self.db.scalars(query.order_by(MonitoringRule.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        from app.modules.users.models import User
        user_ids = {identifier for row in rows for identifier in (row.created_by, row.updated_by) if identifier}
        names = {user.id: (user.full_name or user.username) for user in self.db.scalars(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
        items = [{**serialize(row), "created_by_name": names.get(row.created_by), "updated_by_name": names.get(row.updated_by)} for row in rows]
        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def save_rule(self, values, actor, rule_id: UUID | None = None):
        rule = self.db.get(MonitoringRule, rule_id) if rule_id else MonitoringRule(created_by=actor.id)
        if rule_id and not rule:
            raise AdminDomainError("Monitoring rule not found.")
        condition = values.get("condition", rule.condition if rule_id else {})
        validate_condition(condition)
        if not rule_id and not condition:
            raise AdminDomainError("A trigger condition is required.")
        candidate_name = values.get("name", rule.name if rule_id else None)
        if candidate_name:
            duplicate = self.db.scalar(select(MonitoringRule.id).where(MonitoringRule.name == candidate_name, MonitoringRule.id != rule.id if rule_id else True))
            if duplicate:
                raise AdminDomainError("A monitoring rule with this name already exists.")
        before = {"enabled": rule.enabled, "event_type": rule.event_type} if rule_id else None
        for key, value in values.items():
            setattr(rule, key, value)
        rule.updated_by = actor.id
        self.db.add(rule)
        self.db.flush()
        record_audit(self.db, actor=actor, action="monitoring_rule.updated" if rule_id else "monitoring_rule.created", target_type="monitoring_rule", target_id=rule.id, target_label=rule.name, source="Security Monitoring", details={"before": before, "event_type": rule.event_type, "severity": rule.severity, "enabled": rule.enabled})
        return serialize(rule)
