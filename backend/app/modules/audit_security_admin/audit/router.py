from datetime import datetime, time, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User
from ..dependencies import get_admin_services

router = APIRouter()


def parse_date(value: str | None, end=False):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if len(value) == 10:
            parsed = datetime.combine(parsed.date(), time.max if end else time.min, tzinfo=timezone.utc)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HTTPException(422, "Date filters must use ISO-8601 format.") from exc


def validate_range(from_date: str | None, to_date: str | None):
    start, end = parse_date(from_date), parse_date(to_date, True)
    if start and end and start > end:
        raise HTTPException(422, "from_date must be before or equal to to_date.")
    return start, end


@router.get("/audit/summary", dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def summary(services=Depends(get_admin_services), from_date: str | None = None, to_date: str | None = None):
    start, end = validate_range(from_date, to_date)
    return services.audit.summary(start, end)


@router.get("/audit", dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def list_events(services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), search: str | None = Query(None, max_length=200), action: str | None = None, actor_id: str | None = None, status: str | None = Query(None, pattern="^(success|failure)$"), severity: str | None = Query(None, pattern="^(critical|high|medium|low)$"), source: str | None = None, ip_address: str | None = Query(None, max_length=80), from_date: str | None = None, to_date: str | None = None, sort_by: str = Query("created_at", pattern="^(created_at|actor_name|action|status|severity|source)$"), sort_order: str = Query("desc", pattern="^(asc|desc)$")):
    start, end = validate_range(from_date, to_date)
    return services.audit.list(page=page, page_size=page_size, search=search, action=action, actor_id=actor_id, status=status, severity=severity, source=source, ip_address=ip_address, from_date=start, to_date=end, sort_by=sort_by, sort_order=sort_order)


@router.get("/audit/options", dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def filter_options(services=Depends(get_admin_services)):
    return services.options()


@router.get("/audit/export", dependencies=[Depends(require_permission(Permission.AUDIT_EXPORT))])
def export_events(services=Depends(get_admin_services), format: str = Query("csv", pattern="^(csv|json)$"), limit: int = Query(1000, ge=1, le=10000), search: str | None = None, action: str | None = None, actor_id: str | None = None, status: str | None = None, severity: str | None = None, source: str | None = None, ip_address: str | None = None, from_date: str | None = None, to_date: str | None = None):
    start, end = validate_range(from_date, to_date)
    media_type, filename, body = services.audit.export(format=format, limit=limit, search=search, action=action, actor_id=actor_id, status=status, severity=severity, source=source, ip_address=ip_address, from_date=start, to_date=end)
    return Response(body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/audit/{event_id}", dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def detail(event_id: UUID, services=Depends(get_admin_services)):
    result = services.audit.detail(event_id)
    if result is None:
        raise HTTPException(404, "Audit event not found.")
    return result
