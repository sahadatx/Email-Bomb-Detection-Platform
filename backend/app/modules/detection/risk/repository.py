from sqlalchemy import func, select

from app.modules.detection.models import RiskAssessment


class RiskRepository:
    def __init__(self, db):
        self.db = db

    def distribution(self):
        rows = self.db.execute(select(RiskAssessment.level, func.count()).group_by(RiskAssessment.level)).all()
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unavailable": 0}
        counts.update({level: count for level, count in rows})
        return counts

    def assessments(self):
        return list(self.db.scalars(select(RiskAssessment).order_by(RiskAssessment.created_at.desc())).all())
