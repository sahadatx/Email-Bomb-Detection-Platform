"""Read-only queries across canonical platform records for dashboard widgets."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit_security_admin.administration.health import get_health
from app.modules.audit_security_admin.models import AuditEvent, SecurityAlert, SecurityEvent
from app.modules.emails.models import Email
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion
from app.modules.preprocessing.models import PreprocessingRun
from app.modules.threat_intelligence.models import ThreatFeed
from ..selectors.dashboard_queries import ingested_emails_in_window


class DashboardRepository:
    """Collect only the source data not already covered by Analytics."""

    def __init__(self, db: Session):
        self.db = db

    def count_emails(self, start: datetime, end: datetime) -> int:
        """Count successfully ingested canonical emails in a UTC window."""
        statement = select(func.count()).select_from(
            ingested_emails_in_window(start, end).subquery()
        )
        return int(self.db.scalar(statement) or 0)

    def count_active_security_alerts(self, start: datetime, end: datetime) -> int:
        """Count unresolved alerts first observed in the selected UTC window."""
        statement = select(func.count()).select_from(SecurityAlert).where(
            SecurityAlert.status != "resolved",
            SecurityAlert.first_seen >= start,
            SecurityAlert.first_seen <= end,
        )
        return int(self.db.scalar(statement) or 0)

    def active_models(self) -> list[dict]:
        """Return active versions without exposing artifact paths or secrets."""
        rows = self.db.execute(
            select(MLModelDefinition, MLModelVersion)
            .join(
                MLModelVersion,
                MLModelVersion.model_definition_id == MLModelDefinition.id,
            )
            .where(
                MLModelDefinition.status == "active",
                MLModelVersion.status == "active",
            )
            .order_by(
                MLModelVersion.activated_at.desc(), MLModelVersion.created_at.desc()
            )
        ).all()
        result = []
        for model, version in rows:
            artifact = Path(version.storage_path).expanduser()
            result.append(
                {
                    "model_id": model.id,
                    "model_version_id": version.id,
                    "name": model.name,
                    "algorithm": model.algorithm,
                    "version": version.version,
                    "activated_at": version.activated_at,
                    "artifact_available": artifact.is_file(),
                }
            )
        return result

    def threat_feeds(self) -> dict:
        """Summarize feed records while never returning configured URLs/credentials."""
        rows = self.db.scalars(
            select(ThreatFeed).order_by(ThreatFeed.updated_at.desc())
        ).all()
        enabled = [feed for feed in rows if feed.enabled]
        failed = [feed for feed in rows if feed.sync_status == "failed"]
        feeds = sorted(
            rows, key=lambda feed: (feed.enabled, feed.updated_at), reverse=True
        )[:6]
        return {
            "total_feeds": len(rows),
            "active_feeds": len(enabled),
            "failed_feeds": len(failed),
            "imported_indicators": sum(
                max(0, feed.imported_indicator_count or 0) for feed in rows
            ),
            "feeds": [
                {
                    "id": feed.id,
                    "name": feed.name,
                    "enabled": feed.enabled,
                    "sync_status": feed.sync_status,
                    "imported_indicator_count": feed.imported_indicator_count,
                    "last_sync_at": feed.last_sync_at,
                    "latest_error": feed.latest_error,
                }
                for feed in feeds
            ],
        }

    def preprocessing(self) -> dict:
        """Return the newest persisted preprocessing run as a health signal."""
        run = self.db.scalar(
            select(PreprocessingRun)
            .order_by(PreprocessingRun.created_at.desc())
            .limit(1)
        )
        if run is None:
            return {
                "status": "unknown",
                "description": "No preprocessing run is recorded.",
                "last_checked": None,
                "message": "No preprocessing history is available.",
            }
        mapping = {
            "completed": "healthy",
            "running": "degraded",
            "pending": "unknown",
            "queued": "unknown",
            "failed": "degraded",
        }
        status = mapping.get(str(run.status).lower(), "unknown")
        return {
            "status": status,
            "description": "Most recent preprocessing pipeline run.",
            "last_checked": run.completed_at or run.created_at,
            "message": (
                "The latest preprocessing run failed."
                if status == "degraded" and str(run.status).lower() == "failed"
                else None
            ),
        }

    def recent_activity(
        self,
        start: datetime,
        end: datetime,
        limit: int = 8,
        *,
        include_audit: bool = False,
        include_security: bool = False,
    ) -> list[dict]:
        """Merge safe audit/security summaries; omit raw metadata, IPs and payloads."""
        audits = (
            self.db.scalars(
                select(AuditEvent)
                .where(AuditEvent.created_at >= start, AuditEvent.created_at <= end)
                .order_by(AuditEvent.created_at.desc())
                .limit(limit)
            ).all()
            if include_audit
            else []
        )
        security = (
            self.db.scalars(
                select(SecurityEvent)
                .where(SecurityEvent.occurred_at >= start, SecurityEvent.occurred_at <= end)
                .order_by(SecurityEvent.occurred_at.desc())
                .limit(limit)
            ).all()
            if include_security
            else []
        )
        items = [
            {
                "id": str(event.id),
                "occurred_at": event.created_at,
                "category": "audit",
                "title": event.action.replace("_", " ").title(),
                "actor": event.actor_name or "System",
                "target": event.target_label or event.target_type,
                "status": event.status,
                "severity": event.severity,
                "source": event.source,
                "href": "/audit",
            }
            for event in audits
        ]
        items.extend(
            {
                "id": str(event.id),
                "occurred_at": event.occurred_at,
                "category": "security",
                "title": event.title,
                "actor": None,
                "target": None,
                "status": event.status,
                "severity": event.severity,
                "source": event.source,
                "href": "/security-monitoring",
            }
            for event in security
        )
        return sorted(items, key=lambda item: item["occurred_at"], reverse=True)[:limit]

    def health_check(self) -> dict:
        """Reuse Administration's actual, sanitized service health checks."""
        return get_health(self.db)
