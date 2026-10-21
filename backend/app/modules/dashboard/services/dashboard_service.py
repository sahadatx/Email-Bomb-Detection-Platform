"""Compose dashboard widgets from existing email, analytics and health data."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.core.rbac import has_permission
from app.modules.analytics.errors import AnalyticsError
from app.modules.analytics.aggregations import chart_interval
from app.modules.users.models import User
from ..integrations.analytics_adapter import AnalyticsAdapter
from ..repositories.dashboard_repository import DashboardRepository
from ..selectors.dashboard_filters import DashboardFilters
from ..utils.aggregation import distribution_map, normalize_trend
from ..utils.date_range import resolve_window


class DashboardService:
    """Read-only facade; business rules remain in their owning modules."""

    def __init__(self, db: Session):
        self.repository = DashboardRepository(db)
        self.analytics = AnalyticsAdapter(db)

    def summary(self, filters: DashboardFilters, user: User | None = None) -> dict:
        start, end = resolve_window(filters)
        analytics = self.analytics.overview(filters)
        can_read_alerts = user is not None and has_permission(
            user, Permission.SECURITY_ALERTS_READ
        )
        return {
            "total_emails": {
                "value": self.repository.count_emails(start, end),
                "available": True,
                "description": "Successfully ingested emails in range (including unclassified); classification, risk and model filters apply to detections only.",
            },
            "emails_analyzed": {
                "value": int(analytics["total_detections"]),
                "available": True,
                "description": "Completed detection records matching the selected filters.",
            },
            "bomb_detected": {
                "value": int(analytics["bomb_emails"]["value"] or 0),
                "available": True,
                "description": "Completed detections classified as bomb.",
            },
            "high_risk_emails": {
                "value": int(analytics["high_risk_emails"]["value"] or 0),
                "available": True,
                "description": "Completed detections rated High or Critical.",
            },
            "active_security_alerts": {
                "value": (
                    self.repository.count_active_security_alerts(start, end)
                    if can_read_alerts
                    else 0
                ),
                "available": can_read_alerts,
                "description": (
                    "Unresolved security alerts first seen in the selected period."
                    if can_read_alerts
                    else "Security alert access is required to view this metric."
                ),
            },
        }

    def classification(self, filters: DashboardFilters) -> dict:
        result = self.analytics.classification(filters)
        return {
            "distribution": distribution_map(
                result.get("distribution", []), "classification", ("normal", "bomb")
            ),
            "trend": normalize_trend(result.get("items", [])),
        }

    def risk(self, filters: DashboardFilters) -> list[dict]:
        result = self.analytics.risk(filters)
        return distribution_map(
            result.get("items", []), "risk_level", ("critical", "high", "medium", "low")
        )

    def activity(self, filters: DashboardFilters) -> dict:
        result = self.classification(filters)
        start, end = resolve_window(filters)
        # Trend timestamps and counts come from completed detections. Keep an
        # explicit scope in the API instead of implying it represents ingestion.
        return {
            "items": result["trend"],
            "interval": chart_interval(start, end),
            "scope": "completed_detections",
        }

    def recent_detections(
        self, filters: DashboardFilters, limit: int = 8
    ) -> list[dict]:
        return self.analytics.recent(filters, limit).get("items", [])

    def recent_activity(
        self, filters: DashboardFilters, limit: int = 8, *, user: User | None = None
    ) -> list[dict]:
        start, end = resolve_window(filters)
        return self.repository.recent_activity(
            start,
            end,
            limit,
            include_audit=(
                user is not None and has_permission(user, Permission.AUDIT_READ)
            ),
            include_security=(
                user is not None
                and has_permission(user, Permission.SECURITY_EVENTS_READ)
            ),
        )

    def model_status(self) -> dict:
        active = self.repository.active_models()
        if not active:
            return {
                "status": "unknown",
                "active_count": 0,
                "active_models": [],
                "message": "No active model version is registered.",
            }
        unavailable = [model for model in active if not model["artifact_available"]]
        status = "degraded" if unavailable else "healthy"
        return {
            "status": status,
            "active_count": len(active),
            "active_models": active,
            "message": (
                "An active model artifact is unavailable." if unavailable else None
            ),
        }

    def threat_feed_status(self) -> dict:
        data = self.repository.threat_feeds()
        if data["total_feeds"] == 0:
            status, message = "unknown", "No threat feeds are configured."
        elif data["failed_feeds"]:
            status, message = (
                "degraded",
                f"{data['failed_feeds']} feed(s) have a failed synchronization.",
            )
        elif data["active_feeds"] and any(
            feed["sync_status"] == "success" for feed in data["feeds"]
        ):
            status, message = "healthy", None
        else:
            status, message = (
                "unknown",
                "Enabled feeds have no successful synchronization recorded.",
            )
        return {"status": status, **data, "message": message}

    def system_health(self) -> dict:
        raw = self.repository.health_check()
        components = {item["name"]: item for item in raw.get("services", [])}
        api = components.get("API Service", {})
        db = components.get("Database", {})
        detection_status = (
            "healthy"
            if api.get("status") == "healthy" and db.get("status") == "healthy"
            else (
                "unavailable"
                if "unavailable" in (api.get("status"), db.get("status"))
                else "unknown"
            )
        )
        model = self.model_status()
        feeds = self.threat_feed_status()
        prep = self.repository.preprocessing()
        return {
            "overall_status": raw.get("overall_status", "unknown"),
            "checked_at": raw.get("checked_at") or datetime.now(timezone.utc),
            "components": [
                {
                    "name": "Detection Engine",
                    "status": detection_status,
                    "description": "API and database availability required for detection workflows.",
                    "last_checked": raw.get("checked_at"),
                    "message": (
                        None
                        if detection_status == "healthy"
                        else "The API or database health check is unavailable."
                    ),
                },
                {
                    "name": "ML Model",
                    "status": model["status"],
                    "description": "Active model registration and artifact availability.",
                    "last_checked": raw.get("checked_at"),
                    "message": model["message"],
                },
                {
                    "name": "Threat Intelligence",
                    "status": feeds["status"],
                    "description": "Configured threat feed synchronization state.",
                    "last_checked": raw.get("checked_at"),
                    "message": feeds["message"],
                },
                {"name": "Preprocessing", **prep},
            ],
        }

    def overview(
        self,
        filters: DashboardFilters,
        recent_limit: int = 8,
        *,
        user: User | None = None,
    ) -> dict:
        classification = self.classification(filters)
        return {
            "generated_at": datetime.now(timezone.utc),
            "filters": filters,
            "filter_scope": {
                "time_range": "All widgets",
                "classification": "Detection, classification and risk widgets; intake total remains unclassified",
                "risk_level": "Detection, classification and risk widgets; intake total is unaffected",
                "model_id": "Detection, classification and risk widgets; intake total is unaffected",
            },
            "summary": self.summary(filters, user),
            "classification": classification["distribution"],
            "risk_distribution": self.risk(filters),
            "activity": classification["trend"],
            "recent_detections": self.recent_detections(filters, recent_limit),
            "recent_activity": self.recent_activity(
                filters, recent_limit, user=user
            ),
            "system_health": self.system_health(),
            "model_status": self.model_status(),
            "threat_feed_status": self.threat_feed_status(),
            "model_options": self.analytics.models(),
            "data_sources": [
                "emails",
                "email_detections",
                "detection_risk_assessments",
                "audit_events",
                "security_events",
                "security_alerts",
                "ml_model_definitions",
                "ml_model_versions",
                "threat_feeds",
                "preprocessing_runs",
            ],
        }


__all__ = ["DashboardService", "AnalyticsError"]
