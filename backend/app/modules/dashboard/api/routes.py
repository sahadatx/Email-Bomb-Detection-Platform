"""Authenticated read-only API for the Security Operations dashboard."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.analytics.errors import AnalyticsError
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User
from ..dependencies import get_dashboard_service
from ..selectors.dashboard_filters import DashboardFilters
from ..services.dashboard_service import DashboardService
from .schemas import (
    DashboardActivityResponse,
    DashboardClassificationResponse,
    DashboardModelOptionsResponse,
    DashboardOverview,
    DashboardRecentActivityResponse,
    DashboardRecentDetectionsResponse,
    DashboardSummary,
    RiskDistributionResponse,
    SystemHealth,
)

router = APIRouter()
DashboardRead = Depends(require_permission(Permission.ANALYTICS_READ))


def dashboard_filters(
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "24h",
    classification: Literal["normal", "bomb"] | None = None,
    risk_level: Literal["low", "medium", "high", "critical"] | None = None,
    model_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> DashboardFilters:
    return DashboardFilters(
        time_range=time_range,
        classification=classification,
        risk_level=risk_level,
        model_id=model_id,
        start_date=start_date,
        end_date=end_date,
    )


Filters = Annotated[DashboardFilters, Depends(dashboard_filters)]


def call(fn):
    try:
        return fn()
    except AnalyticsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview", response_model=DashboardOverview, dependencies=[DashboardRead])
def overview(
    filters: Filters,
    user: Annotated[User, Depends(get_current_authenticated_user)],
    service: DashboardService = Depends(get_dashboard_service),
):
    return call(lambda: service.overview(filters, user=user))


@router.get("/summary", response_model=DashboardSummary, dependencies=[DashboardRead])
def summary(
    filters: Filters,
    user: Annotated[User, Depends(get_current_authenticated_user)],
    service: DashboardService = Depends(get_dashboard_service),
):
    return call(lambda: service.summary(filters, user))


@router.get(
    "/activity", response_model=DashboardActivityResponse, dependencies=[DashboardRead]
)
def activity(
    filters: Filters, service: DashboardService = Depends(get_dashboard_service)
):
    return call(lambda: {"filters": filters, **service.activity(filters)})


@router.get(
    "/risk-distribution",
    response_model=RiskDistributionResponse,
    dependencies=[DashboardRead],
)
def risk_distribution(
    filters: Filters, service: DashboardService = Depends(get_dashboard_service)
):
    return call(lambda: {"items": service.risk(filters)})


@router.get(
    "/classification",
    response_model=DashboardClassificationResponse,
    dependencies=[DashboardRead],
)
def classification(
    filters: Filters, service: DashboardService = Depends(get_dashboard_service)
):
    return call(lambda: service.classification(filters))


@router.get(
    "/recent-detections",
    response_model=DashboardRecentDetectionsResponse,
    dependencies=[DashboardRead],
)
def recent_detections(
    filters: Filters,
    service: DashboardService = Depends(get_dashboard_service),
    limit: int = Query(8, ge=1, le=100),
):
    return call(
        lambda: {
            "filters": filters,
            "items": service.recent_detections(filters, limit),
            "limit": limit,
        }
    )


@router.get(
    "/recent-activity",
    response_model=DashboardRecentActivityResponse,
    dependencies=[DashboardRead],
)
def recent_activity(
    filters: Filters,
    user: Annotated[User, Depends(get_current_authenticated_user)],
    service: DashboardService = Depends(get_dashboard_service),
    limit: int = Query(8, ge=1, le=100),
):
    return call(
        lambda: {
            "filters": filters,
            "items": service.recent_activity(filters, limit, user=user),
            "limit": limit,
        }
    )


@router.get("/system-health", response_model=SystemHealth, dependencies=[DashboardRead])
def system_health(service: DashboardService = Depends(get_dashboard_service)):
    return service.system_health()


@router.get("/model-status", dependencies=[DashboardRead])
def model_status(service: DashboardService = Depends(get_dashboard_service)):
    return service.model_status()


@router.get(
    "/model-options",
    response_model=DashboardModelOptionsResponse,
    dependencies=[DashboardRead],
)
def model_options(service: DashboardService = Depends(get_dashboard_service)):
    return {"items": service.analytics.models()}


@router.get("/threat-feed-status", dependencies=[DashboardRead])
def threat_feed_status(service: DashboardService = Depends(get_dashboard_service)):
    return service.threat_feed_status()
