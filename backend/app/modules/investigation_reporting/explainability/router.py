from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User, UserRole
from ..dependencies import get_investigation_service
from ..service import InvestigationService
from .schemas import AnalystNoteCreate, AnalystNoteRead, AnalystNoteUpdate, ExplanationList
from ..http import Page, PageSize, Viewer, raise_http_error, as_utc_datetime, mask_viewer_explanation

router = APIRouter()
_raise = raise_http_error
_date = as_utc_datetime
_viewer_explanation = mask_viewer_explanation

# Explainability: read-only summaries are adapted from persisted detection,
# model, risk and behavioral records; no prediction is repeated here.
@router.get("/explainability", response_model=ExplanationList, dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def list_explanations(service: Annotated[InvestigationService, Depends(get_investigation_service)], user: Viewer, page: Page = 1, page_size: PageSize = 30, search: str | None = Query(None, max_length=200), detection_id: UUID | None = None, prediction: str | None = Query(None, pattern="^(bomb|normal)$"), risk_level: str | None = Query(None, pattern="^(critical|high|medium|low|unavailable)$"), model_name: str | None = Query(None, max_length=240), model_version_id: UUID | None = None, from_date: date | None = None, to_date: date | None = None):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "from_date must be before to_date.")
    result = service.explanations(page=page, page_size=page_size, search=search, detection_id=detection_id, prediction=prediction, risk_level=risk_level, model_name=model_name, model_version_id=model_version_id, from_date=_date(from_date), to_date=_date(to_date, end=True))
    if user.role == UserRole.VIEWER:
        result["items"] = [_viewer_explanation(item) for item in result["items"]]
    return result


@router.get("/explainability/{detection_id}", dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def explanation_detail(detection_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        result = service.explanation_detail(detection_id)
        return _viewer_explanation(result) if user.role == UserRole.VIEWER else result
    except Exception as exc:
        _raise(exc)


@router.get("/explainability/{detection_id}/export", dependencies=[Depends(require_permission(Permission.INVESTIGATION_READ))])
def export_explanation(detection_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        data = service.explanation_detail(detection_id)
        if user.role == UserRole.VIEWER:
            data = _viewer_explanation(data)
        return JSONResponse(jsonable_encoder(data), headers={"Content-Disposition": f'attachment; filename="explanation-{detection_id}.json"'})
    except Exception as exc:
        _raise(exc)


@router.post("/explainability/{detection_id}/notes", response_model=AnalystNoteRead, status_code=201, dependencies=[Depends(require_permission(Permission.INVESTIGATION_NOTE_CREATE))])
def create_note(detection_id: UUID, payload: AnalystNoteCreate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.add_note(detection_id, user.id, payload.model_dump())
    except Exception as exc:
        _raise(exc)


@router.patch("/explainability/notes/{note_id}", response_model=AnalystNoteRead, dependencies=[Depends(require_permission(Permission.INVESTIGATION_NOTE_UPDATE))])
def update_note(note_id: UUID, payload: AnalystNoteUpdate, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.update_note(note_id, user.id, payload.model_dump(), user.role == UserRole.ADMIN)
    except Exception as exc:
        _raise(exc)


@router.delete("/explainability/notes/{note_id}", status_code=204, dependencies=[Depends(require_permission(Permission.INVESTIGATION_NOTE_DELETE))])
def delete_note(note_id: UUID, user: Viewer, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        service.delete_note(note_id, user.id, user.role == UserRole.ADMIN)
        return Response(status_code=204)
    except Exception as exc:
        _raise(exc)


@router.get("/explainability/notes/{note_id}/audit", dependencies=[Depends(require_permission(Permission.INVESTIGATION_AUDIT_READ))])
def note_audit(note_id: UUID, service: Annotated[InvestigationService, Depends(get_investigation_service)]):
    try:
        return service.note_audit(note_id)
    except Exception as exc:
        _raise(exc)
