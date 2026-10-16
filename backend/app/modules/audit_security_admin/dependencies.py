from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from .audit.service import AuditService
from .administration.health import get_health
from .administration.job_manager import job_detail, list_jobs
from .administration.settings_manager import list_settings, update_setting
from .models import AdminSettingHistory
from .security_monitoring.service import SecurityMonitoringService


class AdminServices:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
        self.monitoring = SecurityMonitoringService(db)

    def options(self):
        from sqlalchemy import select
        from .models import AuditEvent
        events = self.db.scalars(select(AuditEvent)).all()
        actors = {row.actor_id: {"id": row.actor_id, "name": row.actor_name} for row in events if row.actor_id}
        return {"actions": sorted({row.action for row in events}), "actors": sorted(actors.values(), key=lambda actor: actor["name"].casefold()), "sources": sorted({row.source for row in events}), "severities": ["critical", "high", "medium", "low"], "statuses": ["success", "failure"]}

    def settings_list(self):
        return list_settings(self.db)

    def update_setting(self, key, value, reason, actor):
        return update_setting(self.db, key, value, reason, actor)

    def setting_history(self, key, page, page_size):
        from sqlalchemy import func, select
        query = select(AdminSettingHistory).where(AdminSettingHistory.setting_key == key)
        total = int(self.db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = self.db.scalars(query.order_by(AdminSettingHistory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return {"items": [{"id": str(row.id), "setting_key": row.setting_key, "actor_id": row.actor_id, "old_value": row.old_value, "new_value": row.new_value, "reason": row.reason, "created_at": row.created_at.isoformat()} for row in rows], "total": total, "page": page, "page_size": page_size}

    def jobs_list(self, page, page_size, status, job_type, search=None):
        return list_jobs(self.db, page, page_size, status, job_type, search)

    def job_detail(self, job_id):
        return job_detail(self.db, job_id)

    def health(self):
        return get_health(self.db)


def get_admin_services(db: Session = Depends(get_db)) -> AdminServices:
    return AdminServices(db)
