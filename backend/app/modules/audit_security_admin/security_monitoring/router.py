from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.core.permissions import Permission
from app.core.rbac import require_permission, require_role
from app.modules.users.models import User, UserRole
from ..dependencies import get_admin_services
from ..schemas import AlertTransition, MonitoringRuleCreate, MonitoringRuleUpdate, SecurityEventIngest, SecurityEventTransition
from ..errors import AdminDomainError

router = APIRouter()


def domain_call(fn):
    try:
        return fn()
    except AdminDomainError as exc:
        message = str(exc)
        raise HTTPException(404 if "not found" in message.lower() else 409, message) from exc


@router.get("/security-monitoring/summary", dependencies=[Depends(require_permission(Permission.SECURITY_EVENTS_READ))])
def summary(services=Depends(get_admin_services)):
    return services.monitoring.summary()


@router.get("/security-monitoring/options", dependencies=[Depends(require_permission(Permission.SECURITY_EVENTS_READ))])
def filter_options(services=Depends(get_admin_services)):
    return services.monitoring.options()


@router.get("/security-monitoring/events", dependencies=[Depends(require_permission(Permission.SECURITY_EVENTS_READ))])
def events(services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), search: str | None = Query(None, max_length=200), severity: str | None = Query(None, pattern="^(critical|high|medium|low)$"), event_type: str | None = Query(None, max_length=80), source: str | None = Query(None, max_length=80), status: str | None = Query(None, pattern="^(new|reviewed|investigating)$"), actor_id: str | None = Query(None, max_length=36), source_ip: str | None = Query(None, max_length=45), from_date: datetime | None = None, to_date: datetime | None = None, sort: str = Query("occurred_at", pattern="^(occurred_at|severity|event_type|source|status)$"), order: str = Query("desc", pattern="^(asc|desc)$")):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "from_date must be before or equal to to_date.")
    return services.monitoring.list_events(page=page, page_size=page_size, search=search, severity=severity, event_type=event_type, source=source, status=status, actor_id=actor_id, source_ip=source_ip, from_date=from_date, to_date=to_date, sort=sort, order=order)


@router.post("/security-monitoring/events", dependencies=[Depends(require_role(UserRole.ADMIN))], status_code=201)
def ingest_event(payload: SecurityEventIngest, user: Annotated[User, Depends(require_role(UserRole.ADMIN))], services=Depends(get_admin_services)):
    values = payload.model_dump(exclude_none=True, exclude={"actor_id"})
    values["actor_id"] = user.id
    return domain_call(lambda: services.monitoring.ingest(values, actor=user))


@router.get("/security-monitoring/events/{event_id}", dependencies=[Depends(require_permission(Permission.SECURITY_EVENTS_READ))])
def event_detail(event_id: UUID, services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.event_detail(event_id))


@router.patch("/security-monitoring/events/{event_id}", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))])
def update_event(event_id: UUID, payload: SecurityEventTransition, user: Annotated[User, Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))], services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.transition_event(event_id, payload.model_dump(exclude_unset=True), user))


@router.post("/security-monitoring/events/{event_id}/alerts", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))], status_code=201)
def create_event_alert(event_id: UUID, user: Annotated[User, Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))], services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.create_alert_for_event(event_id, user))


@router.get("/security-monitoring/alerts", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_READ))])
def alerts(services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), search: str | None = Query(None, max_length=200), severity: str | None = Query(None, pattern="^(critical|high|medium|low)$"), status: str | None = Query(None, pattern="^(open|investigating|resolved)$"), assigned_to: str | None = Query(None, max_length=36), from_date: datetime | None = None, to_date: datetime | None = None, sort: str = Query("updated_at", pattern="^(updated_at|first_seen|last_seen|severity|status|event_count)$"), order: str = Query("desc", pattern="^(asc|desc)$")):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "from_date must be before or equal to to_date.")
    return services.monitoring.list_alerts(page=page, page_size=page_size, search=search, severity=severity, status=status, assigned_to=assigned_to, from_date=from_date, to_date=to_date, sort=sort, order=order)


@router.get("/security-monitoring/analysts", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))])
def analysts(services=Depends(get_admin_services)):
    users = services.db.scalars(select(User).where(User.is_active.is_(True), User.is_locked.is_(False), User.role.in_((UserRole.ADMIN, UserRole.SECURITY_ANALYST)))).all()
    return [{"id": user.id, "name": user.full_name or user.username, "role": user.role.value} for user in users]


@router.get("/security-monitoring/alerts/{alert_id}", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_READ))])
def alert_detail(alert_id: UUID, services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.alert_detail(alert_id))


@router.patch("/security-monitoring/alerts/{alert_id}", dependencies=[Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))])
def update_alert(alert_id: UUID, payload: AlertTransition, user: Annotated[User, Depends(require_permission(Permission.SECURITY_ALERTS_INVESTIGATE))], services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.transition_alert(alert_id, payload.model_dump(exclude_unset=True), user))


@router.get("/security-monitoring/rules", dependencies=[Depends(require_permission(Permission.MONITORING_RULES_READ))])
def rules(services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), search: str | None = None, enabled: bool | None = None):
    return services.monitoring.list_rules(page=page, page_size=page_size, search=search, enabled=enabled)


@router.post("/security-monitoring/rules", dependencies=[Depends(require_permission(Permission.MONITORING_RULES_MANAGE))], status_code=201)
def create_rule(payload: MonitoringRuleCreate, user: Annotated[User, Depends(require_permission(Permission.MONITORING_RULES_MANAGE))], services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.save_rule(payload.model_dump(), user))


@router.patch("/security-monitoring/rules/{rule_id}", dependencies=[Depends(require_permission(Permission.MONITORING_RULES_MANAGE))])
def update_rule(rule_id: UUID, payload: MonitoringRuleUpdate, user: Annotated[User, Depends(require_permission(Permission.MONITORING_RULES_MANAGE))], services=Depends(get_admin_services)):
    return domain_call(lambda: services.monitoring.save_rule(payload.model_dump(exclude_unset=True), user, rule_id))
