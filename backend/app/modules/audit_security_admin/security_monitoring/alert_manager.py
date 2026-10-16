"""Focused alert lifecycle facade used by API and trusted services."""

from uuid import UUID

from sqlalchemy.orm import Session

from ..errors import AdminDomainError
from ..models import SecurityAlert
from .service import SecurityMonitoringService


class AlertManager:
    """Validate lifecycle operations through the shared monitoring service."""

    def __init__(self, db: Session):
        self.db = db
        self.service = SecurityMonitoringService(db)

    def get(self, alert_id: UUID) -> dict:
        return self.service.alert_detail(alert_id)

    def transition(self, alert_id: UUID, values: dict, actor) -> dict:
        return self.service.transition_alert(alert_id, values, actor)

    def assign(self, alert_id: UUID, analyst_id: str | None, actor) -> dict:
        alert = self.db.get(SecurityAlert, alert_id)
        if alert is None:
            raise AdminDomainError("Alert not found.")
        return self.service.transition_alert(
            alert_id,
            {"status": alert.status, "assigned_to": analyst_id},
            actor,
        )

    def resolve(self, alert_id: UUID, note: str, actor) -> dict:
        if not isinstance(note, str) or not note.strip():
            raise AdminDomainError("A resolution note is required.")
        return self.service.transition_alert(
            alert_id,
            {"status": "resolved", "resolution_note": note.strip()},
            actor,
        )


def transition_alert(db: Session, alert_id: UUID, values: dict, actor):
    """Compatibility wrapper for existing trusted integrations."""
    return AlertManager(db).transition(alert_id, values, actor)
