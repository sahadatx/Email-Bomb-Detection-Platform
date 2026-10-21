"""Small query builders used by dashboard repositories."""

from datetime import datetime

from sqlalchemy import select

from app.modules.emails.models import Email, EmailStatus


def ingested_emails_in_window(start: datetime, end: datetime):
    """Countable canonical email query; prediction filters do not alter intake."""
    return select(Email.id).where(
        Email.status == EmailStatus.INGESTED,
        Email.collected_at >= start,
        Email.collected_at <= end,
    )
