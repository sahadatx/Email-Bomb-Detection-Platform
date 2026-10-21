from app.modules.detection.models import RiskAssessment


class RiskAdapter:
    def __init__(self, db): self.db = db

    def for_detection(self, detection_id):
        return self.db.query(RiskAssessment).filter(RiskAssessment.detection_id == detection_id).one_or_none()
