from sqlalchemy import select

from app.modules.detection.models import DetectionRecord


class DetectionAdapter:
    def __init__(self, db):
        self.db = db

    def latest_for_email(self, email_id):
        return self.db.scalar(
            select(DetectionRecord)
            .where(DetectionRecord.email_id == email_id)
            .order_by(DetectionRecord.created_at.desc())
            .limit(1)
        )
