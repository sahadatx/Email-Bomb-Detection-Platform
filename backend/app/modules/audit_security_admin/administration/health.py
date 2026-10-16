import os
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_health(db: Session):
    checked = datetime.now(timezone.utc).isoformat()
    services = [{"name": "API Service", "description": "Application API", "status": "healthy", "last_checked": checked, "message": None}]
    try:
        db.execute(text("SELECT 1"))
        services.append({"name": "Database", "description": "Database connectivity", "status": "healthy", "last_checked": checked, "message": None})
    except Exception:
        db.rollback()
        services.append({"name": "Database", "description": "Database connectivity", "status": "unavailable", "last_checked": checked, "message": "Database connectivity check failed."})
    services.append({"name": "Background Worker", "description": "Asynchronous task processing", "status": "unknown", "last_checked": checked, "message": "No worker heartbeat is configured; job records do not prove worker availability."})
    repository_root = Path(__file__).resolve().parents[5]
    storage_roots = [Path(os.getenv("PREPROCESSING_ARTIFACT_DIR", "data/processed/preprocessing")), Path(os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models"))]
    storage_roots = [path if path.is_absolute() else repository_root / path for path in storage_roots]
    storage_ok = all(path.exists() and path.is_dir() and os.access(path, os.R_OK | os.W_OK | os.X_OK) for path in storage_roots)
    services.append({"name": "File Storage", "description": "Preprocessing and model artifact storage", "status": "healthy" if storage_ok else "degraded", "last_checked": checked, "message": None if storage_ok else "One or more configured artifact directories are missing or not accessible."})
    try:
        from app.modules.ml_models.models import MLModelVersion
        active_versions = db.query(MLModelVersion).filter(MLModelVersion.status == "active").all()
        if not active_versions:
            ml_status, ml_message = "unknown", "No active model version is registered."
        elif all(Path(version.storage_path).expanduser().is_file() for version in active_versions):
            ml_status, ml_message = "healthy", None
        else:
            ml_status, ml_message = "degraded", "At least one active model artifact is unavailable."
    except Exception:
        db.rollback()
        ml_status, ml_message = "unknown", "Active model availability could not be checked."
    services.append({"name": "ML Service", "description": "Registered model artifact availability", "status": ml_status, "last_checked": checked, "message": ml_message})
    states = {item["status"] for item in services}
    overall = "unavailable" if "unavailable" in states else "degraded" if "unknown" in states or "degraded" in states else "healthy"
    return {"overall_status": overall, "checked_at": checked, "services": services}
