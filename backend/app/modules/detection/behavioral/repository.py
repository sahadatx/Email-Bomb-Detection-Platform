from sqlalchemy import func, select

from app.modules.detection.models import BehavioralResult, DetectionRecord, DetectionInput
from app.modules.emails.models import Email


class BehavioralRepository:
    def __init__(self, db):
        self.db = db

    def analyzed_email_count(self):
        # Count actual behavioral analyses, including analyses of uploaded
        # emails that do not have an EmailFeatures collection row.
        return self.db.scalar(select(func.count()).select_from(BehavioralResult)) or 0

    def all_results(self):
        return list(self.db.scalars(select(BehavioralResult).order_by(BehavioralResult.created_at.desc())).all())

    def activity_timestamps(self, since):
        return list(self.db.scalars(select(Email.collected_at).where(Email.collected_at >= since)).all())

    def anomaly_records(self):
        stmt = select(BehavioralResult, DetectionRecord, Email, DetectionInput).join(DetectionRecord, DetectionRecord.id == BehavioralResult.detection_id).outerjoin(Email, Email.id == DetectionRecord.email_id).outerjoin(DetectionInput, DetectionInput.id == DetectionRecord.input_id).order_by(BehavioralResult.created_at.desc())
        return list(self.db.execute(stmt).all())
