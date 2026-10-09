from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import UserRole
from ..dependencies import get_investigation_service
from ..service import InvestigationService
from .schemas import EvidenceCreate, EvidenceList, EvidenceRead, EvidenceReview, EvidenceUpdate
from ..http import Page, PageSize, Viewer, raise_http_error, parse_date_filter

router = APIRouter()
_raise = raise_http_error
_to_datetime = parse_date_filter

# Evidence management.
@router.get("/evidence", response_model=EvidenceList, dependencies=[Depends(require_permission(Permission.EVIDENCE_READ))])
def list_evidence(service: Annotated[InvestigationService, Depends(get_investigation_service)], user: Viewer, page: Page = 1, page_size: PageSize = 30, search: str | None = Query(None, max_length=200), evidence_type: str | None = Query(None, pattern="^(email_header|content|feature|behavioral|network|other)$"), review_status: str | None = Query(None, alias="status", pattern="^(pending|verified|flagged|rejected)$"), detection_id: UUID | None = None, source_email_id: UUID | None = None, created_by: str | None = None, has_analyst_note: bool | None = None, provenance_search: str | None = Query(None, max_length=200), from_date: str | None = None, to_date: str | None = None):
    start = _to_datetime(from_date)
    end = _to_datetime(to_date, end=True)
    if start and end and start > end:
        raise HTTPException(422, "from_date must be before to_date.")
    result = service.evidence_list(page=page, page_size=page_size, search=search, evidence_type=evidence_type, review_status=review_status, detection_id=detection_id, source_email_id=source_email_id, created_by=created_by, has_analyst_note=has_analyst_note, provenance_search=provenance_search, from_date=start, to_date=end)
    if user.role == UserRole.VIEWER:
        result["items"] = [EvidenceRead.model_validate(item).model_copy(update={"observed_value": None, "provenance": {}, "analyst_note": None}) for item in result["items"]]
    return result


@router.post("/evidence", response_model=EvidenceRead, status_code=201, dependencies=[Depends(require_permission(Permission.EVIDENCE_CREATE))])
def create_evidence(payload: EvidenceCreate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.create_evidence(user.id, payload.model_dump())
    except Exception as exc:
        _raise(exc)


@router.get("/evidence/export", dependencies=[Depends(require_permission(Permission.EVIDENCE_EXPORT))])
def export_evidence(service: Annotated[InvestigationService, Depends(get_investigation_service)], user: Viewer, search: str | None = None, evidence_type: str | None = None, review_status: str | None = Query(None, alias="status"), detection_id: UUID | None = None, source_email_id: UUID | None = None, created_by: str | None = None, has_analyst_note: bool | None = None, provenance_search: str | None = None, from_date: str | None = None, to_date: str | None = None):
    start, end = _to_datetime(from_date), _to_datetime(to_date, end=True)
    if start and end and start > end:
        raise HTTPException(422, "from_date must be before to_date.")
    rows = service.evidence_export(search=search, evidence_type=evidence_type, review_status=review_status, detection_id=detection_id, source_email_id=source_email_id, created_by=created_by, has_analyst_note=has_analyst_note, provenance_search=provenance_search, from_date=start, to_date=end)
    content = [service.evidence_json(row) for row in rows]
    if user.role == UserRole.VIEWER:
        content = [{**item, "observed_value": None, "provenance": {}, "analyst_note": None} for item in content]
    content = jsonable_encoder(content)
    return JSONResponse(content, headers={"Content-Disposition": 'attachment; filename="evidence-export.json"'})


@router.get("/evidence/{evidence_id}", dependencies=[Depends(require_permission(Permission.EVIDENCE_READ))])
def evidence_detail(evidence_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        result = service.evidence_detail(evidence_id)
        if user.role == UserRole.VIEWER:
            record = result["evidence"]
            result["evidence"] = EvidenceRead.model_validate(record).model_copy(update={"observed_value": None, "provenance": {}, "analyst_note": None})
            result["history"] = []
        return result
    except Exception as exc:
        _raise(exc)


@router.patch("/evidence/{evidence_id}", response_model=EvidenceRead, dependencies=[Depends(require_permission(Permission.EVIDENCE_UPDATE))])
def update_evidence(evidence_id: UUID, payload: EvidenceUpdate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.update_evidence(evidence_id, user.id, payload.model_dump(exclude_unset=True))
    except Exception as exc:
        _raise(exc)


@router.post("/evidence/{evidence_id}/review", response_model=EvidenceRead, dependencies=[Depends(require_permission(Permission.EVIDENCE_REVIEW))])
def review_evidence(evidence_id: UUID, payload: EvidenceReview, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.review_evidence(evidence_id, user.id, payload.model_dump())
    except Exception as exc:
        _raise(exc)


@router.get("/evidence/{evidence_id}/audit", dependencies=[Depends(require_permission(Permission.EVIDENCE_AUDIT_READ))])
def evidence_audit(evidence_id: UUID, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        detail = service.evidence_detail(evidence_id)
        return detail["history"]
    except Exception as exc:
        _raise(exc)
