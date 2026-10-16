from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import Permission
from app.core.rbac import require_permission, require_role
from app.modules.users.models import User, UserRole
from ..dependencies import get_admin_services
from ..schemas import SettingUpdate
from ..errors import AdminDomainError

router = APIRouter(dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get("/administration/settings", dependencies=[Depends(require_permission(Permission.SYSTEM_SETTINGS_READ))])
def settings(services=Depends(get_admin_services)):
    return {"items": services.settings_list()}


@router.patch("/administration/settings/{setting_key:path}", dependencies=[Depends(require_permission(Permission.SYSTEM_SETTINGS_UPDATE))])
def update_setting(setting_key: str, payload: SettingUpdate, user: Annotated[User, Depends(require_permission(Permission.SYSTEM_SETTINGS_UPDATE))], services=Depends(get_admin_services)):
    try:
        return services.update_setting(setting_key, payload.value, payload.reason, user)
    except AdminDomainError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/administration/settings/{setting_key:path}/history", dependencies=[Depends(require_permission(Permission.SYSTEM_SETTINGS_READ))])
def setting_history(setting_key: str, services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100)):
    return services.setting_history(setting_key, page, page_size)


@router.get("/administration/jobs", dependencies=[Depends(require_permission(Permission.BACKGROUND_JOBS_READ))])
def jobs(services=Depends(get_admin_services), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), status: str | None = Query(None, pattern="^(queued|pending|running|completed|partial|failed|cancelled)$"), job_type: str | None = Query(None, pattern="^(email_ingestion|preprocessing|training|evaluation|report_generation)$"), search: str | None = Query(None, max_length=160)):
    return services.jobs_list(page, page_size, status, job_type, search)


@router.get("/administration/jobs/{job_id}", dependencies=[Depends(require_permission(Permission.BACKGROUND_JOBS_READ))])
def job_detail(job_id: str, services=Depends(get_admin_services)):
    result = services.job_detail(job_id)
    if result is None:
        raise HTTPException(404, "Background job not found.")
    return result


@router.get("/administration/health", dependencies=[Depends(require_permission(Permission.SYSTEM_HEALTH_READ))])
def health(services=Depends(get_admin_services)):
    return services.health()
