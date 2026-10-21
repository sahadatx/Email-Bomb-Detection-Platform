"""Read current configuration from its owning module and shared settings tables."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit_security_admin.models import AdminSetting
from app.modules.detection.models import DetectionSettings
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion
from app.modules.threat_intelligence.models import ThreatFeed
from app.modules.audit_security_admin.administration.settings_manager import DEFAULTS


class SettingsRepository:
    """Read-only database access; setting ownership remains with each domain."""

    DETECTION_DEFAULTS = {
        "default_model_version_id": None,
        "high_risk_threshold": 70,
        "critical_risk_threshold": 90,
        "enable_behavioral_analysis": True,
        "save_feature_snapshots": True,
        "store_detection_history": True,
    }

    def __init__(self, db: Session):
        self.db = db

    def generic_values(self) -> dict:
        stored = {row.key: row for row in self.db.scalars(select(AdminSetting)).all()}
        return {
            key: {
                "value": stored[key].value if key in stored else default,
                "updated_at": stored[key].updated_at if key in stored else None,
                "updated_by": stored[key].updated_by if key in stored else None,
            }
            for key, (_, default, _) in DEFAULTS.items()
        }

    def detection_values(self) -> dict:
        row = self.db.get(DetectionSettings, 1)
        return {
            key: getattr(row, key) if row is not None else value
            for key, value in self.DETECTION_DEFAULTS.items()
        }

    def active_model_versions(self) -> list[dict]:
        rows = self.db.execute(
            select(MLModelDefinition, MLModelVersion)
            .join(
                MLModelVersion,
                MLModelVersion.model_definition_id == MLModelDefinition.id,
            )
            .where(
                MLModelDefinition.status == "active", MLModelVersion.status == "active"
            )
            .order_by(MLModelDefinition.name, MLModelVersion.version.desc())
        ).all()
        return [
            {
                "id": str(version.id),
                "label": f"{model.name} · {model.algorithm} · v{version.version}",
                "name": model.name,
                "algorithm": model.algorithm,
                "version": version.version,
            }
            for model, version in rows
        ]

    def threat_feed_summary(self) -> dict:
        feeds = self.db.scalars(select(ThreatFeed)).all()
        return {
            "total": len(feeds),
            "enabled": sum(feed.enabled for feed in feeds),
            "failed": sum(
                feed.enabled and feed.sync_status == "failed" for feed in feeds
            ),
            "imported_indicators": sum(
                feed.imported_indicator_count or 0 for feed in feeds
            ),
        }
