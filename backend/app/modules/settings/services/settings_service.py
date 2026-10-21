"""Orchestrate category settings while delegating persistence to owning modules."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.modules.audit_security_admin.administration.settings_manager import (
    DEFAULTS,
    update_setting as update_admin_setting,
)
from app.modules.audit_security_admin.audit.service import record_audit
from app.modules.audit_security_admin.models import AdminSettingHistory
from app.modules.detection.models import DetectionSettings
from app.modules.detection.schemas import SettingsUpdate as DetectionSettingsUpdate
from app.modules.detection.service import DetectionError, DetectionService

from ..errors import SettingsValidationError
from ..repositories.settings_repository import SettingsRepository
from ..utils.settings_validators import (
    CATEGORY_KEYS,
    validate_category_values,
    validate_change_reason,
)

CATEGORY_DETAILS = {
    "general": ("General", "Platform identity and timezone preferences.", True),
    "detection": (
        "Detection",
        "Inference workflow behavior and retained detection records.",
        True,
    ),
    "risk": (
        "Risk",
        "Risk score thresholds used by the backend scoring service.",
        True,
    ),
    "models": ("Models", "Default active model version used by new detections.", True),
    "email_processing": (
        "Email Processing",
        "Limits applied to email ingestion and detection uploads.",
        True,
    ),
    "threat_intelligence": (
        "Threat Intelligence",
        "Feed status and its owning threat-feed workspace.",
        False,
    ),
    "notifications": (
        "Notifications",
        "Notification delivery is unavailable until a provider is configured.",
        False,
    ),
    "security": ("Security", "Authentication session policy.", True),
}


FIELD_DETAILS = {
    "platform.display_name": (
        "Platform name",
        "string",
        "Name displayed to platform users.",
    ),
    "platform.timezone": (
        "Platform timezone",
        "timezone",
        "IANA timezone used for platform date presentation.",
    ),
    "security.session_timeout_minutes": (
        "Session timeout",
        "integer",
        "Access token lifetime for newly issued sessions, in minutes.",
    ),
    "email.max_upload_mb": (
        "Maximum email upload",
        "integer",
        "Maximum .eml upload size in megabytes.",
    ),
    "enable_behavioral_analysis": (
        "Behavioral analysis",
        "boolean",
        "Run behavioral analysis when sufficient sender history is available.",
    ),
    "save_feature_snapshots": (
        "Save feature snapshots",
        "boolean",
        "Store extracted features with detection records.",
    ),
    "store_detection_history": (
        "Store detection history",
        "boolean",
        "Persist detection outcomes and related analysis.",
    ),
    "detection.high_risk_threshold": (
        "High risk threshold",
        "threshold",
        "Minimum backend risk score classified as High.",
    ),
    "detection.critical_risk_threshold": (
        "Critical risk threshold",
        "threshold",
        "Minimum backend risk score classified as Critical.",
    ),
    "default_model_version_id": (
        "Default model version",
        "model_version",
        "Model version selected for detections when no explicit version is provided.",
    ),
}


class SettingsService:
    """Category-oriented settings facade backed by existing domain storage."""

    def __init__(self, db: Session, repository: SettingsRepository):
        self.db = db
        self.repository = repository

    def overview(self) -> dict:
        return {
            "categories": [
                {
                    "category": key,
                    "title": title,
                    "description": description,
                    "editable": editable,
                    "supported": key != "notifications",
                }
                for key, (title, description, editable) in CATEGORY_DETAILS.items()
            ]
        }

    def category(self, category: str) -> dict:
        if category not in CATEGORY_DETAILS:
            raise SettingsValidationError("Unknown settings category.")
        title, description, editable = CATEGORY_DETAILS[category]
        generic = self.repository.generic_values()
        detection = self.repository.detection_values()
        values: dict[str, dict] = {}

        if category in {"general", "security", "email_processing"}:
            keys = CATEGORY_KEYS[category]
            values = {key: generic[key] for key in keys}
        elif category == "detection":
            values = {
                key: {"value": detection[key], "updated_at": None}
                for key in CATEGORY_KEYS[category]
            }
        elif category == "risk":
            values = {
                "detection.high_risk_threshold": {
                    "value": detection["high_risk_threshold"],
                    "updated_at": None,
                },
                "detection.critical_risk_threshold": {
                    "value": detection["critical_risk_threshold"],
                    "updated_at": None,
                },
            }
        elif category == "models":
            values = {
                "default_model_version_id": {
                    "value": (
                        str(detection["default_model_version_id"])
                        if detection["default_model_version_id"]
                        else None
                    ),
                    "updated_at": None,
                }
            }

        fields = []
        for key, stored in values.items():
            label, kind, hint = FIELD_DETAILS[key]
            options = []
            if key == "default_model_version_id":
                options = [
                    {"value": item["id"], "label": item["label"]}
                    for item in self.repository.active_model_versions()
                ]
            fields.append(
                {
                    "key": key,
                    "label": label,
                    "value": stored.get("value"),
                    "value_type": kind,
                    "description": hint,
                    "editable": editable,
                    "sensitive": False,
                    "options": options,
                    "updated_at": stored.get("updated_at"),
                }
            )

        notice = None
        links = []
        if category == "models" and not self.repository.active_model_versions():
            notice = "No active model versions are available. Activate a model in Model Registry before selecting a default."
        elif category == "threat_intelligence":
            summary = self.repository.threat_feed_summary()
            status = (
                "unknown"
                if not summary["total"]
                else "degraded" if summary["failed"] else "connected"
            )
            fields = [
                {
                    "key": "feed_status",
                    "label": "Feed status",
                    "value": status,
                    "value_type": "status",
                    "description": f"{summary['enabled']} enabled feed(s); {summary['failed']} enabled feed(s) failed their latest sync.",
                    "editable": False,
                    "sensitive": False,
                    "options": [],
                    "updated_at": None,
                },
                {
                    "key": "feed_count",
                    "label": "Configured feeds",
                    "value": summary["total"],
                    "value_type": "integer",
                    "description": "Managed in Threat Intelligence → Threat Feeds.",
                    "editable": False,
                    "sensitive": False,
                    "options": [],
                    "updated_at": None,
                },
                {
                    "key": "imported_indicators",
                    "label": "Imported indicators",
                    "value": summary["imported_indicators"],
                    "value_type": "integer",
                    "description": "Total indicators currently attributed to configured feeds.",
                    "editable": False,
                    "sensitive": False,
                    "options": [],
                    "updated_at": None,
                },
            ]
            notice = "Feed configuration and credentials stay in the Threat Intelligence module. This page does not expose feed URLs or secrets."
            links = [
                {"label": "Manage threat feeds", "href": "/threat-intelligence/feeds"}
            ]
        elif category == "notifications":
            notice = "No outbound notification provider is configured, so there are no notification settings to edit."
            fields = []
        elif category == "detection":
            notice = "These controls use the Detection Settings record. Risk thresholds and the default model are grouped under their own categories."
        elif category == "risk":
            notice = "Threshold updates are applied by the existing risk scoring engine and validated together."
        elif category == "security":
            notice = "Session timeout changes apply to newly created sessions; existing issued tokens keep their original expiry."
        elif category == "email_processing":
            notice = "The upload limit is enforced by Email ingestion and Detection upload endpoints."

        return {
            "category": category,
            "title": title,
            "description": description,
            "supported": category != "notifications",
            "editable": editable,
            "notice": notice,
            "fields": fields,
            "links": links,
        }

    def update_category(self, category: str, values: dict, reason: str, actor) -> dict:
        values = validate_category_values(category, values)
        reason = validate_change_reason(reason)
        if category not in CATEGORY_DETAILS or not CATEGORY_DETAILS[category][2]:
            raise SettingsValidationError("This settings category is read-only.")

        try:
            if category in {"general", "security", "email_processing"}:
                current = self.repository.generic_values()
                changed = {
                    key: value
                    for key, value in values.items()
                    if current[key]["value"] != value
                }
                for key, value in changed.items():
                    update_admin_setting(self.db, key, value, reason, actor)
            elif category == "risk":
                current = self.repository.detection_values()
                high = values.get(
                    "detection.high_risk_threshold", current["high_risk_threshold"]
                )
                critical = values.get(
                    "detection.critical_risk_threshold",
                    current["critical_risk_threshold"],
                )
                if high >= critical:
                    raise SettingsValidationError(
                        "High risk threshold must be lower than the critical risk threshold."
                    )
                changed = {
                    key: value
                    for key, value in values.items()
                    if current[key.removeprefix("detection.")] != value
                }
                for key, value in changed.items():
                    update_admin_setting(self.db, key, value, reason, actor)
            else:
                changed = self._update_detection_owned(category, values, reason, actor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "category": self.category(category),
            "changed_keys": sorted(changed),
            "saved_at": datetime.now(timezone.utc),
        }

    def _update_detection_owned(
        self, category: str, values: dict, reason: str, actor
    ) -> dict:
        current = self.repository.detection_values()
        if category == "models":
            raw_id = values["default_model_version_id"]
            try:
                model_version_id = UUID(raw_id) if raw_id else None
            except ValueError as exc:
                raise SettingsValidationError("Select a valid model version.") from exc
            values = {"default_model_version_id": model_version_id}
        candidate = {**current, **values}
        try:
            validated = DetectionSettingsUpdate.model_validate(candidate).model_dump()
        except ValidationError as exc:
            raise SettingsValidationError(
                "Detection settings failed validation."
            ) from exc
        service = DetectionService(self.db)
        try:
            row = service.repo.settings()
            service.update_settings(validated)
        except DetectionError as exc:
            raise SettingsValidationError(str(exc)) from exc

        changed = {
            key: value for key, value in values.items() if current.get(key) != value
        }
        if not changed:
            return changed

        category_title = CATEGORY_DETAILS[category][0]
        for key, value in changed.items():
            old = current[key]
            new_value = str(value) if isinstance(value, UUID) else value
            old_value = str(old) if isinstance(old, UUID) else old
            history_key = f"{category}.{key}"
            self.db.add(
                AdminSettingHistory(
                    setting_key=history_key,
                    actor_id=actor.id,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                )
            )
        record_audit(
            self.db,
            actor=actor,
            action="system_setting.updated",
            target_type="system_setting",
            target_id=category,
            target_label=f"{category_title} settings",
            source="System Settings",
            details={"changed_fields": sorted(changed), "reason": reason},
        )
        row.updated_at = datetime.now(timezone.utc)
        return changed
