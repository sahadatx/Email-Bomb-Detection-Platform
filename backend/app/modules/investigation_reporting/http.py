"""Shared FastAPI dependency, pagination and privacy helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User
from .service import InvestigationError, InvestigationService

Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Viewer = Annotated[User, Depends(get_current_authenticated_user)]


def raise_http_error(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise HTTPException(403, str(exc)) from exc
    if isinstance(exc, InvestigationError):
        message = str(exc).lower()
        code = 404 if "not found" in message or "does not exist" in message else 409
        raise HTTPException(code, str(exc)) from exc
    raise HTTPException(500, "Investigation request failed.") from exc


def as_utc_datetime(value: date | None, *, end: bool = False) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.max if end else time.min, tzinfo=timezone.utc)


def parse_date_filter(value: str | None, *, end: bool = False) -> datetime | None:
    if not value:
        return None
    try:
        return as_utc_datetime(date.fromisoformat(value), end=end)
    except ValueError as exc:
        raise HTTPException(422, "Dates must use YYYY-MM-DD format.") from exc


def mask_sender(value: str | None) -> str | None:
    if not value or "@" not in value:
        return value
    return f"***@{value.rsplit('@', 1)[1]}"


def mask_viewer_explanation(payload: dict) -> dict:
    """Remove email identifiers, feature details and private analyst notes."""
    safe = dict(payload)
    safe["sender"] = mask_sender(safe.get("sender"))
    safe["email_subject"] = "Restricted"
    safe["feature_snapshot"] = {}
    safe["analyst_notes"] = []
    explanation = dict(safe.get("explanation") or {})
    explanation["feature_contributions"] = []
    explanation["status"] = "restricted"
    explanation["limitations"] = "Feature values and analyst notes are restricted for this role."
    safe["explanation"] = explanation
    return safe


def mask_viewer_report_snapshot(snapshot: dict | None):
    if not snapshot:
        return snapshot
    safe = dict(snapshot)
    if "detections" in snapshot:
        safe["detections"] = [mask_viewer_explanation(item) for item in snapshot.get("detections", [])]
    safe.pop("analyst_notes", None)
    safe.pop("report_analyst_notes", None)
    if "evidence" in snapshot:
        safe["evidence"] = [
            {**item, "observed_value": None, "provenance": {}, "analyst_note": None}
            for item in snapshot.get("evidence", [])
        ]
    if "explainability" in snapshot:
        safe["explainability"] = [
            {"detection_id": item.get("detection_id"), "explanation": {"status": "restricted", "feature_contributions": [], "triggered_rules": [], "behavioral_signals": [], "limitations": "Explainability values are restricted for this role."}}
            for item in snapshot.get("explainability", [])
        ]
    if "technical_appendix" in snapshot:
        safe["technical_appendix"] = [
            {key: value for key, value in item.items() if key not in {"feature_snapshot", "error_message"}}
            for item in snapshot.get("technical_appendix", [])
        ]
    return safe
