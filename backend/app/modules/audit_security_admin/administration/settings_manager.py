from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit.service import record_audit
from ..errors import AdminDomainError
from ..models import AdminSetting, AdminSettingHistory
from app.modules.detection.models import DetectionSettings

DEFAULTS = {
    "platform.display_name": ("general", "Email Bomb Detection Platform", "string"),
    "platform.timezone": ("general", "UTC", "timezone"),
    "security.session_timeout_minutes": ("security", 30, "integer"),
    "email.max_upload_mb": ("email", 20, "integer"),
    "detection.high_risk_threshold": ("ml_detection", 70, "threshold"),
    "detection.critical_risk_threshold": ("ml_detection", 90, "threshold"),
}


def get_effective_setting(db: Session, key: str):
    row = db.get(AdminSetting, key)
    return row.value if row is not None else DEFAULTS.get(key, (None, None, None))[1]


def validate(key, value):
    if key not in DEFAULTS:
        raise AdminDomainError("This setting is not editable through the administration API.")
    kind = DEFAULTS[key][2]
    if kind == "string" and (not isinstance(value, str) or not value.strip() or len(value) > 120):
        raise AdminDomainError("Value must be a non-empty string of at most 120 characters.")
    if kind == "timezone":
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, TypeError):
            raise AdminDomainError("Select a valid IANA timezone.")
    if kind in {"integer", "threshold"} and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= (1440 if kind == "integer" else 100)):
        raise AdminDomainError("Value must be a supported positive integer.")


def list_settings(db: Session):
    stored = {item.key: item for item in db.scalars(select(AdminSetting)).all()}
    detection = db.get(DetectionSettings, 1)
    detection_values = {
        "detection.high_risk_threshold": detection.high_risk_threshold if detection else DEFAULTS["detection.high_risk_threshold"][1],
        "detection.critical_risk_threshold": detection.critical_risk_threshold if detection else DEFAULTS["detection.critical_risk_threshold"][1],
    }
    values = []
    for key, (category, default, kind) in DEFAULTS.items():
        row = stored.get(key)
        current = detection_values[key] if key in detection_values else (row.value if row else default)
        if row is None:
            row = AdminSetting(key=key, category=category, value=default, value_type=kind, secret=False)
            db.add(row)
        values.append({"key": key, "category": category, "value": current, "value_type": kind, "secret": False, "updated_by": row.updated_by, "updated_at": row.updated_at.isoformat() if row.updated_at else None})
    return values


def update_setting(db: Session, key: str, value, reason: str, actor):
    validate(key, value)
    if not isinstance(reason, str) or len(reason.strip()) < 3:
        raise AdminDomainError("A change reason of at least three non-space characters is required.")
    category, default, kind = DEFAULTS[key]
    row = db.get(AdminSetting, key)
    detection = db.get(DetectionSettings, 1) if key.startswith("detection.") else None
    field = "high_risk_threshold" if key.endswith("high_risk_threshold") else "critical_risk_threshold"
    old_value = getattr(detection, field) if detection else (row.value if row else default)
    if key.startswith("detection."):
        counterpart_key = "detection.critical_risk_threshold" if field == "high_risk_threshold" else "detection.high_risk_threshold"
        counterpart_default = DEFAULTS[counterpart_key][1]
        counterpart_row = db.get(AdminSetting, counterpart_key)
        counterpart = getattr(detection, "critical_risk_threshold" if field == "high_risk_threshold" else "high_risk_threshold") if detection else (counterpart_row.value if counterpart_row else counterpart_default)
        high = value if field == "high_risk_threshold" else counterpart
        critical = value if field == "critical_risk_threshold" else counterpart
        if high >= critical:
            raise AdminDomainError("High risk threshold must be lower than the critical risk threshold.")
        if detection is None:
            detection = DetectionSettings(id=1)
            db.add(detection)
        setattr(detection, field, value)
    if row is None:
        row = AdminSetting(key=key, category=category, value=value, value_type=kind)
        db.add(row)
    row.value = value
    row.value_type = kind
    row.category = category
    row.updated_by = actor.id
    row.change_reason = reason.strip()
    row.updated_at = datetime.now(timezone.utc)
    db.add(AdminSettingHistory(setting_key=key, actor_id=actor.id, old_value=old_value, new_value=value, reason=reason.strip()))
    record_audit(db, actor=actor, action="system_setting.updated", target_type="system_setting", target_id=key, target_label=key, source="System Administration", details={"old_value": old_value, "new_value": value, "reason": reason.strip()})
    from ..security_monitoring.event_processor import process_security_event
    process_security_event(db, {"event_type": "system_setting.updated", "title": "System setting changed", "description": f"The {category} configuration category was updated.", "severity": "high", "source": "System Administration", "actor_id": actor.id, "details": {"setting_key": key, "reason": reason.strip()}}, actor=actor)
    return {"key": key, "category": category, "value": value, "value_type": kind, "secret": False, "updated_by": actor.id, "updated_at": row.updated_at.isoformat()}
