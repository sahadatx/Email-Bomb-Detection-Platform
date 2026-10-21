"""Permission-protected Settings endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import User

from ..dependencies import get_settings_service
from ..errors import SettingsValidationError
from ..services.settings_service import SettingsService
from .schemas import (
    SettingsCategory,
    SettingsOverview,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)

router = APIRouter()
SettingsReader = Depends(require_permission(Permission.SYSTEM_SETTINGS_READ))


@router.get("", response_model=SettingsOverview, dependencies=[SettingsReader])
def get_settings_overview(
    service: Annotated[SettingsService, Depends(get_settings_service)],
):
    return service.overview()


@router.get(
    "/{category}", response_model=SettingsCategory, dependencies=[SettingsReader]
)
def get_settings_category(
    category: str, service: Annotated[SettingsService, Depends(get_settings_service)]
):
    try:
        return service.category(category)
    except SettingsValidationError as exc:
        raise HTTPException(
            status_code=404 if "Unknown" in str(exc) else 422, detail=str(exc)
        ) from exc


@router.put("/{category}", response_model=SettingsUpdateResponse)
def update_settings_category(
    category: str,
    payload: SettingsUpdateRequest,
    actor: Annotated[
        User, Depends(require_permission(Permission.SYSTEM_SETTINGS_UPDATE))
    ],
    service: Annotated[SettingsService, Depends(get_settings_service)],
):
    try:
        return service.update_category(category, payload.values, payload.reason, actor)
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
