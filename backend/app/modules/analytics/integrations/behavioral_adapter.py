from app.modules.detection.models import BehavioralResult


class BehavioralAdapter:
    def __init__(self, db): self.db = db

    def for_detection(self, detection_id):
        return self.db.query(BehavioralResult).filter(BehavioralResult.detection_id == detection_id).one_or_none()
