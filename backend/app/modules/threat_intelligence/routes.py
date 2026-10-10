import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import User
from .dependencies import get_threat_service
from .schemas import (
    FeedCreate,
    FeedList,
    FeedRead,
    FeedUpdate,
    IndicatorCreate,
    IndicatorList,
    IndicatorRead,
    IndicatorStatus,
    IndicatorUpdate,
    MatchList,
    MatchStatusUpdate,
    MatchSummary,
    Overview,
    ReconcileResult,
    SyncList,
    SyncRead,
)
from .service import (
    ThreatConflict,
    ThreatError,
    ThreatNotFound,
    ThreatService,
    ThreatValidationError,
    execute_feed_sync,
)

router = APIRouter()
Read = Depends(require_permission(Permission.THREAT_INTELLIGENCE_READ))
ManageIndicators = Depends(require_permission(Permission.THREAT_INDICATORS_MANAGE))
ManageFeeds = Depends(require_permission(Permission.THREAT_FEEDS_MANAGE))
Investigate = Depends(require_permission(Permission.THREAT_MATCHES_INVESTIGATE))
Export = Depends(require_permission(Permission.THREAT_INTELLIGENCE_EXPORT))


def invoke(fn):
    try:
        return fn()
    except ThreatNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except ThreatConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except (ThreatValidationError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except ThreatError as exc:
        raise HTTPException(400, str(exc)) from exc


def period(time_range, from_date, to_date):
    now = datetime.now(timezone.utc)
    if time_range == "custom":
        if not from_date or not to_date:
            raise HTTPException(
                422, "Custom time range requires from_date and to_date."
            )
        if from_date > to_date:
            raise HTTPException(422, "from_date must be before or equal to to_date.")
        return from_date, to_date
    days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}[time_range]
    return (
        now - (timedelta(hours=24) if time_range == "24h" else timedelta(days=days)),
        now,
    )


def export_response(rows, filename, output_format):
    if output_format == "json":
        return JSONResponse(
            content={"count": len(rows), "items": rows},
            headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
        )
    fields = list(rows[0].keys()) if rows else []
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@router.get(
    "/threat-intelligence/overview", response_model=Overview, dependencies=[Read]
)
def overview(
    service=Depends(get_threat_service),
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    threat_type: Literal["ip", "domain", "url", "hash", "email"] | None = None,
    severity: Literal["low", "medium", "high", "critical"] | None = None,
    feed_id: UUID | None = None,
):
    start, end = period(time_range, from_date, to_date)
    return invoke(
        lambda: service.overview(
            start=start,
            end=end,
            threat_type=threat_type,
            severity=severity,
            feed_id=feed_id,
        )
    )


@router.get("/threat-intelligence/overview/export", dependencies=[Export])
def export_overview(
    service=Depends(get_threat_service),
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    threat_type: str | None = None,
    severity: str | None = None,
    feed_id: UUID | None = None,
    format: Literal["csv", "json"] = "csv",
    limit: int = Query(1000, ge=1, le=10000),
):
    start, end = period(time_range, from_date, to_date)
    result = invoke(
        lambda: service.list_matches(
            page=1,
            page_size=limit,
            start=start,
            end=end,
            severity=severity,
            indicator_type=threat_type,
            feed_id=feed_id,
        )
    )
    return export_response(
        [item.model_dump(mode="json") for item in result["items"]],
        "threat-overview",
        format,
    )


@router.get(
    "/threat-intelligence/indicators", response_model=IndicatorList, dependencies=[Read]
)
def indicators(
    service=Depends(get_threat_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    search: str | None = Query(None, max_length=300),
    indicator_type: Literal["ip", "domain", "url", "hash", "email"] | None = None,
    severity: Literal["low", "medium", "high", "critical"] | None = None,
    status_filter: Literal["active", "inactive", "expired"] | None = Query(
        None, alias="status"
    ),
    source: Literal["manual", "feed"] | None = None,
    feed_id: UUID | None = None,
):
    return invoke(
        lambda: service.indicators(
            page=page,
            page_size=page_size,
            search=search,
            indicator_type=indicator_type,
            severity=severity,
            status=status_filter,
            source=source,
            feed_id=feed_id,
        )
    )


@router.post(
    "/threat-intelligence/indicators",
    response_model=IndicatorRead,
    status_code=201,
    dependencies=[ManageIndicators],
)
def create_indicator(
    payload: IndicatorCreate,
    actor: Annotated[
        User, Depends(require_permission(Permission.THREAT_INDICATORS_MANAGE))
    ],
    service=Depends(get_threat_service),
):
    return invoke(lambda: service.create_indicator(payload, actor))


@router.get(
    "/threat-intelligence/indicators/{indicator_id}",
    response_model=IndicatorRead,
    dependencies=[Read],
)
def indicator_detail(indicator_id: UUID, service=Depends(get_threat_service)):
    return invoke(lambda: service.get_indicator(indicator_id))


@router.patch(
    "/threat-intelligence/indicators/{indicator_id}",
    response_model=IndicatorRead,
    dependencies=[ManageIndicators],
)
def update_indicator(
    indicator_id: UUID,
    payload: IndicatorUpdate,
    actor: Annotated[
        User, Depends(require_permission(Permission.THREAT_INDICATORS_MANAGE))
    ],
    service=Depends(get_threat_service),
):
    return invoke(
        lambda: service.update_indicator(
            indicator_id, payload.model_dump(exclude_unset=True), actor
        )
    )


@router.patch(
    "/threat-intelligence/indicators/{indicator_id}/status",
    response_model=IndicatorRead,
    dependencies=[ManageIndicators],
)
def indicator_status(
    indicator_id: UUID,
    payload: IndicatorStatus,
    actor: Annotated[
        User, Depends(require_permission(Permission.THREAT_INDICATORS_MANAGE))
    ],
    service=Depends(get_threat_service),
):
    return invoke(
        lambda: service.set_indicator_status(indicator_id, payload.status, actor)
    )


@router.delete(
    "/threat-intelligence/indicators/{indicator_id}",
    status_code=204,
    dependencies=[ManageIndicators],
)
def delete_indicator(
    indicator_id: UUID,
    actor: Annotated[
        User, Depends(require_permission(Permission.THREAT_INDICATORS_MANAGE))
    ],
    service=Depends(get_threat_service),
):
    invoke(lambda: service.set_indicator_status(indicator_id, "inactive", actor))
    return Response(status_code=204)


@router.get(
    "/threat-intelligence/indicators/{indicator_id}/matches",
    response_model=MatchList,
    dependencies=[Read],
)
def indicator_matches(
    indicator_id: UUID,
    service=Depends(get_threat_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    return invoke(lambda: service.indicator_matches(indicator_id, page, page_size))


@router.get("/threat-intelligence/feeds", response_model=FeedList, dependencies=[ManageFeeds])
def feeds(
    service=Depends(get_threat_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    search: str | None = Query(None, max_length=180),
    status_filter: Literal["active", "inactive"] | None = Query(None, alias="status"),
    feed_type: Literal["stix_taxii", "csv", "json", "api", "internal"] | None = None,
    sync_status: (
        Literal["never_synced", "queued", "running", "success", "failed"] | None
    ) = None,
):
    return service.feeds(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        feed_type=feed_type,
        sync_status=sync_status,
    )


@router.get("/threat-intelligence/feeds/summary", dependencies=[ManageFeeds])
def feed_summary(service=Depends(get_threat_service)):
    return service.feed_summary()


@router.post(
    "/threat-intelligence/feeds",
    response_model=FeedRead,
    status_code=201,
    dependencies=[ManageFeeds],
)
def create_feed(
    payload: FeedCreate,
    actor: Annotated[User, Depends(require_permission(Permission.THREAT_FEEDS_MANAGE))],
    service=Depends(get_threat_service),
):
    return invoke(lambda: service.create_feed(payload, actor))


@router.get("/threat-intelligence/feeds/{feed_id}", dependencies=[ManageFeeds])
def feed_detail(feed_id: UUID, service=Depends(get_threat_service)):
    return invoke(lambda: service.get_feed(feed_id))


@router.patch(
    "/threat-intelligence/feeds/{feed_id}",
    response_model=FeedRead,
    dependencies=[ManageFeeds],
)
def update_feed(
    feed_id: UUID,
    payload: FeedUpdate,
    actor: Annotated[User, Depends(require_permission(Permission.THREAT_FEEDS_MANAGE))],
    service=Depends(get_threat_service),
):
    return invoke(
        lambda: service.update_feed(
            feed_id, payload.model_dump(exclude_unset=True), actor
        )
    )


@router.post(
    "/threat-intelligence/feeds/{feed_id}/sync",
    response_model=SyncRead,
    status_code=202,
    dependencies=[ManageFeeds],
)
def sync_feed(
    feed_id: UUID,
    tasks: BackgroundTasks,
    actor: Annotated[User, Depends(require_permission(Permission.THREAT_FEEDS_MANAGE))],
    service=Depends(get_threat_service),
):
    run = invoke(lambda: service.queue_sync(feed_id, actor))
    service.db.commit()
    tasks.add_task(execute_feed_sync, run["id"])
    return run


@router.get(
    "/threat-intelligence/feeds/{feed_id}/sync-history",
    response_model=SyncList,
    dependencies=[ManageFeeds],
)
def feed_sync_history(
    feed_id: UUID,
    service=Depends(get_threat_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    return invoke(lambda: service.sync_history(feed_id, page, page_size))


@router.get(
    "/threat-intelligence/matches/summary",
    response_model=MatchSummary,
    dependencies=[Read],
)
def match_summary(
    service=Depends(get_threat_service),
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    severity: str | None = None,
    indicator_type: str | None = None,
    feed_id: UUID | None = None,
    classification: Literal["normal", "bomb", "unknown"] | None = None,
):
    start, end = period(time_range, from_date, to_date)
    return invoke(
        lambda: service.match_summary(
            start=start,
            end=end,
            severity=severity,
            indicator_type=indicator_type,
            feed_id=feed_id,
            classification=classification,
        )
    )


@router.post(
    "/threat-intelligence/matches/reconcile",
    response_model=ReconcileResult,
    dependencies=[ManageIndicators],
)
def reconcile_matches(service=Depends(get_threat_service)):
    return invoke(service.reconcile_existing_data)


@router.get("/threat-intelligence/matches/export", dependencies=[Export])
def export_matches(
    service=Depends(get_threat_service),
    page_size: int = Query(1000, ge=1, le=10000),
    search: str | None = None,
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    classification: Literal["normal", "bomb", "unknown"] | None = None,
    severity: str | None = None,
    indicator_type: str | None = None,
    feed_id: UUID | None = None,
    match_status: str | None = Query(None, alias="status"),
    format: Literal["csv", "json"] = "csv",
):
    start, end = period(time_range, from_date, to_date)
    result = invoke(
        lambda: service.list_matches(
            page=1,
            page_size=page_size,
            search=search,
            start=start,
            end=end,
            classification=classification,
            severity=severity,
            indicator_type=indicator_type,
            feed_id=feed_id,
            status=match_status,
        )
    )
    return export_response(
        [item.model_dump(mode="json") for item in result["items"]],
        "threat-matches",
        format,
    )


@router.get(
    "/threat-intelligence/matches", response_model=MatchList, dependencies=[Read]
)
def matches(
    service=Depends(get_threat_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    search: str | None = Query(None, max_length=300),
    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "30d",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    classification: Literal["normal", "bomb", "unknown"] | None = None,
    severity: Literal["low", "medium", "high", "critical"] | None = None,
    indicator_type: Literal["ip", "domain", "url", "hash", "email"] | None = None,
    feed_id: UUID | None = None,
    match_status: (
        Literal["new", "reviewed", "investigating", "resolved"] | None
    ) = Query(None, alias="status"),
):
    start, end = period(time_range, from_date, to_date)
    return invoke(
        lambda: service.list_matches(
            page=page,
            page_size=page_size,
            search=search,
            start=start,
            end=end,
            classification=classification,
            severity=severity,
            indicator_type=indicator_type,
            feed_id=feed_id,
            status=match_status,
        )
    )


@router.get("/threat-intelligence/matches/{match_id}", dependencies=[Read])
def match_detail(match_id: UUID, service=Depends(get_threat_service)):
    return invoke(lambda: service.match_detail(match_id))


@router.patch(
    "/threat-intelligence/matches/{match_id}/status", dependencies=[Investigate]
)
def update_match(
    match_id: UUID,
    payload: MatchStatusUpdate,
    actor: Annotated[
        User, Depends(require_permission(Permission.THREAT_MATCHES_INVESTIGATE))
    ],
    service=Depends(get_threat_service),
):
    return invoke(
        lambda: service.update_match_status(match_id, payload.match_status, actor)
    )
