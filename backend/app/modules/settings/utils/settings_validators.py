"""Validate supported settings payloads before any configuration is mutated."""

from app.modules.audit_security_admin.administration.settings_manager import (
    DEFAULTS,
    validate as validate_admin_setting,
)

from ..errors import SettingsValidationError

CATEGORY_KEYS = {
    "general": {"platform.display_name", "platform.timezone"},
    "security": {"security.session_timeout_minutes"},
    "email_processing": {"email.max_upload_mb"},
    "risk": {"detection.high_risk_threshold", "detection.critical_risk_threshold"},
    "detection": {
        "enable_behavioral_analysis",
        "save_feature_snapshots",
        "store_detection_history",
    },
    "models": {"default_model_version_id"},
    "threat_intelligence": set(),
    "notifications": set(),
}


def validate_change_reason(reason: str) -> str:
    if not isinstance(reason, str) or len(reason.strip()) < 3:
        raise SettingsValidationError(
            "A change reason of at least three non-space characters is required."
        )
    if len(reason) > 1000:
        raise SettingsValidationError("Change reason must not exceed 1000 characters.")
    return reason.strip()


def validate_category_values(category: str, values: dict) -> dict:
    if category not in CATEGORY_KEYS:
        raise SettingsValidationError("Unknown settings category.")
    if not isinstance(values, dict) or not values:
        raise SettingsValidationError("Provide at least one setting value to save.")
    unknown = set(values) - CATEGORY_KEYS[category]
    if unknown:
        raise SettingsValidationError(
            f"Unsupported setting(s) for {category}: {', '.join(sorted(unknown))}."
        )
    if category in {"general", "security", "email_processing", "risk"}:
        for key, value in values.items():
            if key not in DEFAULTS:
                continue
            try:
                validate_admin_setting(key, value)
            except Exception as exc:
                raise SettingsValidationError(str(exc)) from exc
    if category == "detection":
        if any(not isinstance(value, bool) for value in values.values()):
            raise SettingsValidationError("Detection options must be boolean values.")
    if category == "models":
        value = values.get("default_model_version_id")
        if value is not None and not isinstance(value, str):
            raise SettingsValidationError(
                "Default model version must be a UUID or null."
            )
    if category in {"notifications", "threat_intelligence"}:
        raise SettingsValidationError(
            f"{category.replace('_', ' ').title()} settings are managed by their owning module."
        )
    return values
