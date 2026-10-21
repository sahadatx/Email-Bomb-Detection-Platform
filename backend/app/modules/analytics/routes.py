import csv
import io
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import User
from .dependencies import get_analytics_service
from .errors import AnalyticsError
from .schemas import (
    AnalyticsBehavior,
    AnalyticsClassification,
    AnalyticsFilters,
    AnalyticsModelOptions,
    AnalyticsOverview,
    AnalyticsPerformance,
    AnalyticsRecentDetections,
    AnalyticsRiskDistribution,
)

router = APIRouter()
AnalyticsRead = Depends(require_permission(Permission.ANALYTICS_READ))


def filters(time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d", classification: Literal["normal", "bomb"] | None = None, risk_level: Literal["low", "medium", "high", "critical"] | None = None, model_definition_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None):
    return AnalyticsFilters(time_range=time_range, classification=classification, risk_level=risk_level, model_definition_id=model_definition_id, from_date=from_date, to_date=to_date)


Filters = Annotated[AnalyticsFilters, Depends(filters)]


def call(fn):
    try:
        return fn()
    except AnalyticsError as exc:
        raise HTTPException(422, str(exc)) from exc


def safe_csv_cell(value):
    """Keep untrusted text from being interpreted as a spreadsheet formula."""
    if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(
        ("=", "+", "-", "@")
    ):
        return "'" + value
    return value


@router.get("/analytics/models", response_model=AnalyticsModelOptions, dependencies=[AnalyticsRead])
def models(service=Depends(get_analytics_service)):
    return {"items": service.repository.model_options()}


@router.get("/analytics/overview", response_model=AnalyticsOverview, dependencies=[AnalyticsRead])
def overview(query: Filters, service=Depends(get_analytics_service)):
    return call(lambda: service.overview(query))


@router.get("/analytics/classification", response_model=AnalyticsClassification, dependencies=[AnalyticsRead])
def classification(query: Filters, service=Depends(get_analytics_service)):
    return call(lambda: service.classification(query))


@router.get("/analytics/risk", response_model=AnalyticsRiskDistribution, dependencies=[AnalyticsRead])
def risk(query: Filters, service=Depends(get_analytics_service)):
    return call(lambda: service.risk(query))


@router.get("/analytics/detection-performance", response_model=AnalyticsPerformance, dependencies=[AnalyticsRead])
def performance(query: Filters, service=Depends(get_analytics_service), evaluation_split: Literal["validation", "testing"] = "validation"):
    return call(lambda: service.performance(query, evaluation_split))


@router.get("/analytics/behavior", response_model=AnalyticsBehavior, dependencies=[AnalyticsRead])
def behavior(query: Filters, service=Depends(get_analytics_service)):
    return call(lambda: service.behavior(query))


@router.get("/analytics/recent-detections", response_model=AnalyticsRecentDetections, dependencies=[AnalyticsRead])
def recent(query: Filters, service=Depends(get_analytics_service), limit: int = Query(20, ge=1, le=100)):
    return call(lambda: service.recent(query, limit))


@router.get("/analytics/export", dependencies=[Depends(require_permission(Permission.ANALYTICS_EXPORT))])
def export(query: Filters, service=Depends(get_analytics_service), limit: int = Query(1000, ge=1, le=10000), format: Literal["csv", "json"] = "csv"):
    try:
        rows = service.repository.recent(filters=service.filters(query), limit=limit)
    except AnalyticsError as exc:
        raise HTTPException(422, str(exc)) from exc
    if format == "json":
        return JSONResponse(
            content={"count": len(rows), "items": rows},
            headers={"Content-Disposition": 'attachment; filename="analytics.json"'},
        )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=("id", "email_id", "sender", "subject", "classification", "confidence", "risk_level", "risk_score", "model_name", "model_version", "created_at"))
    writer.writeheader()
    writer.writerows(
        {key: safe_csv_cell(value) for key, value in row.items()}
        for row in rows
    )
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="analytics.csv"'})
