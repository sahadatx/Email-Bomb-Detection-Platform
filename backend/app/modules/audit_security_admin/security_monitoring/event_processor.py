"""Callable integration for trusted modules to submit a security signal."""

from sqlalchemy.orm import Session

from .service import SecurityMonitoringService


def process_security_event(db: Session, values: dict, actor=None):
    """Persist an event and evaluate enabled, validated monitoring rules."""
    return SecurityMonitoringService(db).ingest(values, actor)
