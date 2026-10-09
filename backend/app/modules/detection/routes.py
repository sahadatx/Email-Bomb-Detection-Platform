from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.core.rbac import require_module_access
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import User
from app.modules.audit_security_admin.audit.service import record_audit
from app.modules.audit_security_admin.administration.settings_manager import get_effective_setting

from app.modules.detection.dependencies import DetectionServiceDependency
from app.modules.detection.models import DetectionRecord
from app.modules.detection.schemas import DetectionBatchCreate, DetectionCreate, DetectionList, DetectionRawCreate, DetectionRead, EmailOption, SettingsRead, SettingsUpdate
from app.modules.detection.risk.schemas import RiskSummary
from app.modules.detection.behavioral.schemas import BehavioralActivity, BehavioralAnomaly, BehavioralSummary
from app.modules.detection.service import DetectionError

router = APIRouter(dependencies=[Depends(require_module_access("detection"))])


def _raise(exc: Exception):
    if isinstance(exc, DetectionError):
        code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(code, str(exc)) from exc
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Detection request failed.") from exc


@router.get("/summary")
def overview(service: DetectionServiceDependency, period: str = Query("7d", pattern="^(24h|7d|30d)$")):
    return service.overview(period)


@router.get("/emails", response_model=list[EmailOption])
def email_options(service: DetectionServiceDependency, search: str | None = None, limit: int = Query(30, ge=1, le=100)):
    rows = service.repo.list_emails(search, 0, limit)
    options = []
    for email, feature_id, feature_status in rows:
        normalized_status = getattr(feature_status, "value", feature_status)
        ready = feature_id is not None and normalized_status in {"extracted", "warning"}
        options.append({
            "id": email.id,
            "sender": email.sender,
            "subject": email.subject,
            "status": "ready" if ready else "features_failed" if normalized_status == "failed" else "features_missing",
            "has_features": ready,
        })
    return options


@router.get("/active-model")
def active_model(service: DetectionServiceDependency):
    settings = service.repo.settings()
    result = service.repo.get_version(settings.default_model_version_id) if settings.default_model_version_id else service.repo.active_version()
    if result is None or result[0].status != "active" or result[1].status != "active":
        return {"available": False, "model": None}
    version, model = result
    return {"available": True, "model_version_id": version.id, "model_name": model.name, "algorithm": model.algorithm, "version": version.version}


@router.get("/active-models")
def active_models(service: DetectionServiceDependency):
    return [{"model_version_id": version.id, "model_name": model.name, "algorithm": model.algorithm, "version": version.version} for version, model in service.repo.active_versions()]


@router.post("", response_model=DetectionRead, status_code=201)
def create_detection(payload: DetectionCreate, service: DetectionServiceDependency):
    try:
        return service.create(payload.email_id, payload.model_version_id, payload.run_behavioral_analysis, payload.calculate_risk_score)
    except Exception as exc:
        _raise(exc)


@router.post("/raw", response_model=DetectionRead, status_code=201)
def detect_raw_email(payload: DetectionRawCreate, service: DetectionServiceDependency):
    max_bytes = int(get_effective_setting(service.db, "email.max_upload_mb") or 20) * 1_000_000
    content = payload.raw_email.encode("utf-8")
    if len(content) > max_bytes:
        raise HTTPException(413, f"Raw email exceeds the configured {max_bytes // 1_000_000} MB limit.")
    filename = payload.filename if payload.filename.lower().endswith(".eml") else f"{payload.filename}.eml"
    try:
        return service.create(None, payload.model_version_id, payload.run_behavioral_analysis, payload.calculate_risk_score, (filename, content))
    except Exception as exc:
        _raise(exc)


@router.post("/batch", status_code=201)
def create_detection_batch(payload: DetectionBatchCreate, service: DetectionServiceDependency):
    items = [(None, email_id, None) for email_id in payload.email_ids]
    return service.create_batch(items, payload.model_version_id, payload.run_behavioral_analysis, payload.calculate_risk_score)


@router.post("/batch/upload", status_code=201)
async def upload_detection_batch(
    service: DetectionServiceDependency,
    files: Annotated[list[UploadFile], File()],
    model_version_id: Annotated[UUID | None, Form()] = None,
    run_behavioral_analysis: Annotated[bool, Form()] = True,
    calculate_risk_score: Annotated[bool, Form()] = True,
):
    if not files or len(files) > 20:
        raise HTTPException(422, "Select between 1 and 20 .eml files for one batch.")
    max_bytes = int(get_effective_setting(service.db, "email.max_upload_mb") or 20) * 1_000_000
    items = []
    for file in files:
        filename = file.filename or "email.eml"
        if not filename.lower().endswith(".eml"):
            raise HTTPException(422, f"{filename} is not an .eml file.")
        content = await file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(413, f"{filename} exceeds the configured {max_bytes // 1_000_000} MB limit.")
        items.append((filename, None, (filename, content)))
    return service.create_batch(items, model_version_id, run_behavioral_analysis, calculate_risk_score)


@router.post("/upload", response_model=DetectionRead, status_code=201)
async def upload_detection(
    service: DetectionServiceDependency,
    file: Annotated[UploadFile, File()],
    model_version_id: Annotated[UUID | None, Form()] = None,
    run_behavioral_analysis: Annotated[bool, Form()] = True,
    calculate_risk_score: Annotated[bool, Form()] = True,
):
    filename = file.filename or "email.eml"
    if not filename.lower().endswith(".eml"):
        raise HTTPException(422, "Upload must be an .eml file.")
    max_bytes = int(get_effective_setting(service.db, "email.max_upload_mb") or 20) * 1_000_000
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(413, f"Email file exceeds the configured {max_bytes // 1_000_000} MB limit.")
    try:
        return service.create(None, model_version_id, run_behavioral_analysis, calculate_risk_score, (filename, content))
    except Exception as exc:
        _raise(exc)


@router.get("", response_model=DetectionList)
def list_detections(service: DetectionServiceDependency, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), prediction: str | None = Query(None, pattern="^(bomb|normal)$"), risk_level: str | None = Query(None, pattern="^(critical|high|medium|low|unavailable)$"), search: str | None = Query(None, max_length=200)):
    items, total = service.list(page=page, page_size=page_size, prediction=prediction, risk_level=risk_level, search=search)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{detection_id:uuid}", response_model=DetectionRead)
def get_detection(detection_id: UUID, service: DetectionServiceDependency):
    try:
        return service.detail(detection_id)
    except Exception as exc:
        _raise(exc)


@router.get("/{detection_id:uuid}/report")
def export_detection_report(detection_id: UUID, service: DetectionServiceDependency):
    """Download the persisted detection result and its evidence as JSON."""
    try:
        report = service.detail(detection_id)
        return JSONResponse(
            content=jsonable_encoder(report),
            headers={
                "Content-Disposition": f'attachment; filename="detection-{detection_id}.json"'
            },
        )
    except Exception as exc:
        _raise(exc)


@router.get("/risk/summary", response_model=RiskSummary)
def risk_summary(service: DetectionServiceDependency):
    return {**service.risk_service.summary(), "factors": service.risk_service.factors()}


@router.get("/risk/distribution")
def risk_distribution(service: DetectionServiceDependency):
    return service.risk_service.summary()["distribution"]


@router.get("/risk/factors")
def risk_factors(service: DetectionServiceDependency):
    return service.risk_service.factors()


@router.get("/behavior/summary", response_model=BehavioralSummary)
def behavior_summary(service: DetectionServiceDependency):
    return service.behavioral_service.summary()


@router.get("/behavior/activity", response_model=BehavioralActivity)
def behavior_activity(service: DetectionServiceDependency, period: str = Query("7d", pattern="^(24h|7d|30d)$")):
    return service.behavioral_service.activity(period)


@router.get("/behavior/anomalies", response_model=list[BehavioralAnomaly])
def behavior_anomalies(service: DetectionServiceDependency):
    return service.behavioral_service.anomalies()


@router.get("/settings", response_model=SettingsRead, dependencies=[Depends(require_permission(Permission.SYSTEM_SETTINGS_READ))])
def get_settings(service: DetectionServiceDependency):
    return service.repo.settings()


@router.patch("/settings", response_model=SettingsRead, dependencies=[Depends(require_permission(Permission.SYSTEM_SETTINGS_UPDATE))])
def patch_settings(payload: SettingsUpdate, service: DetectionServiceDependency, user: Annotated[User, Depends(require_permission(Permission.SYSTEM_SETTINGS_UPDATE))]):
    try:
        values = payload.model_dump()
        old = service.repo.settings()
        result = service.update_settings(values)
        record_audit(service.db, actor=user, action="detection.settings_updated", target_type="detection_settings", target_id="1", target_label="Detection settings", source="Detection", details={"changed_fields": sorted(values), "previous_default_model_version_id": str(old.default_model_version_id) if old.default_model_version_id else None, "default_model_version_id": str(result.default_model_version_id) if result.default_model_version_id else None, "high_risk_threshold": result.high_risk_threshold, "critical_risk_threshold": result.critical_risk_threshold})
        return result
    except Exception as exc:
        _raise(exc)
