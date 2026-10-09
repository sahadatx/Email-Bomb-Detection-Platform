from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response as BinaryResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import UserRole
from ..dependencies import get_investigation_service
from ..service import InvestigationService
from .schemas import ReportCreate, ReportList, ReportPreview, ReportRead, ReportUpdate
from ..http import Page, PageSize, Viewer, raise_http_error, mask_viewer_report_snapshot, parse_date_filter

router = APIRouter()
_raise = raise_http_error
_viewer_report_snapshot = mask_viewer_report_snapshot

# Reports are generated from selected persisted source records into immutable snapshots.
@router.get("/reports", response_model=ReportList, dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def list_reports(service: Annotated[InvestigationService, Depends(get_investigation_service)], user: Viewer, page: Page = 1, page_size: PageSize = 30, search: str | None = Query(None, max_length=200), report_type: str | None = Query(None, pattern="^(detection|investigation|campaign|summary)$"), report_status: str | None = Query(None, alias="status", pattern="^(draft|generated|failed|archived)$"), output_format: str | None = Query(None, pattern="^(json|pdf)$"), created_by: str | None = None, detection_id: UUID | None = None, created_from: str | None = None, created_to: str | None = None, generated_from: str | None = None, generated_to: str | None = None):
    created_start, created_end = parse_date_filter(created_from), parse_date_filter(created_to, end=True)
    generated_start, generated_end = parse_date_filter(generated_from), parse_date_filter(generated_to, end=True)
    if (created_start and created_end and created_start > created_end) or (generated_start and generated_end and generated_start > generated_end):
        raise HTTPException(422, "Date range start must be before date range end.")
    result = service.report_list(page=page, page_size=page_size, search=search, report_type=report_type, report_status=report_status, output_format=output_format, created_by=created_by, detection_id=detection_id, created_from=created_start, created_to=created_end, generated_from=generated_start, generated_to=generated_end)
    result["items"] = [ReportRead.model_validate(item).model_copy(update={"snapshot": None}) for item in result["items"]]
    return result


@router.post("/reports", response_model=ReportRead, status_code=201, dependencies=[Depends(require_permission(Permission.REPORT_CREATE))])
def create_report(payload: ReportCreate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.create_report(user.id, payload.model_dump())
    except Exception as exc:
        _raise(exc)


@router.post("/reports/preview", dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def preview_report(payload: ReportPreview, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    """Build a preview without persisting a draft or changing audit history."""
    try:
        result = service.preview_report(user.id, payload.model_dump())
        return mask_viewer_report_snapshot(result) if user.role == UserRole.VIEWER else result
    except Exception as exc:
        _raise(exc)


@router.get("/reports/{report_id}", response_model=ReportRead, dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def report_detail(report_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        report = service.report_detail(report_id)
        if user.role == UserRole.VIEWER:
            payload = ReportRead.model_validate(report).model_dump()
            payload["snapshot"] = _viewer_report_snapshot(report.snapshot)
            return payload
        return report
    except Exception as exc:
        _raise(exc)


@router.patch("/reports/{report_id}", response_model=ReportRead, dependencies=[Depends(require_permission(Permission.REPORT_UPDATE))])
def update_report(report_id: UUID, payload: ReportUpdate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.update_report(report_id, user.id, payload.model_dump())
    except Exception as exc:
        _raise(exc)


@router.post("/reports/{report_id}/generate", response_model=ReportRead, dependencies=[Depends(require_permission(Permission.REPORT_GENERATE))])
def generate_report(report_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.generate_report(report_id, user.id)
    except Exception as exc:
        _raise(exc)


@router.post("/reports/{report_id}/duplicate", response_model=ReportRead, status_code=201, dependencies=[Depends(require_permission(Permission.REPORT_CREATE))])
def duplicate_report(report_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.duplicate_report(report_id, user.id)
    except Exception as exc:
        _raise(exc)


@router.post("/reports/{report_id}/archive", response_model=ReportRead, dependencies=[Depends(require_permission(Permission.REPORT_ARCHIVE))])
def archive_report(report_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.archive_report(report_id, user.id)
    except Exception as exc:
        _raise(exc)


@router.get("/reports/{report_id}/download", dependencies=[Depends(require_permission(Permission.REPORT_DOWNLOAD))])
def download_report(report_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        report = service.report_detail(report_id)
        generated = service.rendered_report(report, viewer=user.role == UserRole.VIEWER)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        _raise(exc)
    return BinaryResponse(content=generated.body, media_type=generated.media_type, headers={"Content-Disposition": f'attachment; filename="report-{report.id}.{generated.extension}"'})


@router.get("/reports/{report_id}/audit", dependencies=[Depends(require_permission(Permission.REPORT_AUDIT_READ))])
def report_audit(report_id: UUID, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.report_audit(report_id)
    except Exception as exc:
        _raise(exc)
