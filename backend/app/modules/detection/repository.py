from __future__ import annotations

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session

from app.modules.detection.models import BehavioralResult, DetectionInput, DetectionRecord, DetectionSettings, RiskAssessment
from app.modules.emails.models import Email
from app.modules.features.models import EmailFeatures
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion


class DetectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def email_input(self, email_id):
        return self.db.execute(select(Email, EmailFeatures).join(EmailFeatures, EmailFeatures.email_id == Email.id).where(Email.id == email_id)).first()

    def list_emails(self, search: str | None, offset: int, limit: int):
        stmt = select(Email, EmailFeatures.id, EmailFeatures.status).outerjoin(
            EmailFeatures,
            EmailFeatures.email_id == Email.id,
        )
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(or_(Email.sender.ilike(pattern), Email.subject.ilike(pattern), Email.id.cast(String).ilike(pattern)))
        return list(self.db.execute(stmt.order_by(Email.collected_at.desc()).offset(offset).limit(limit)).all())

    def active_version(self):
        stmt = select(MLModelVersion, MLModelDefinition).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).where(MLModelVersion.status == "active", MLModelDefinition.status == "active").order_by(MLModelVersion.activated_at.desc())
        return self.db.execute(stmt).first()

    def active_versions(self):
        stmt = select(MLModelVersion, MLModelDefinition).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).where(MLModelVersion.status == "active", MLModelDefinition.status == "active").order_by(MLModelVersion.activated_at.desc())
        return list(self.db.execute(stmt).all())

    def get_version(self, version_id):
        return self.db.execute(select(MLModelVersion, MLModelDefinition).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).where(MLModelVersion.id == version_id)).first()

    def insert(self, detection, risk, behavioral):
        self.db.add(detection)
        self.db.flush()
        if risk:
            risk.detection_id = detection.id
            self.db.add(risk)
        if behavioral:
            behavioral.detection_id = detection.id
            self.db.add(behavioral)
        self.db.flush()
        return detection

    def get(self, detection_id):
        return self.db.get(DetectionRecord, detection_id)

    def detail(self, detection_id):
        stmt = select(DetectionRecord, Email, MLModelVersion, MLModelDefinition, RiskAssessment, BehavioralResult).outerjoin(Email, Email.id == DetectionRecord.email_id).join(MLModelVersion, MLModelVersion.id == DetectionRecord.model_version_id).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).outerjoin(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id).outerjoin(BehavioralResult, BehavioralResult.detection_id == DetectionRecord.id).where(DetectionRecord.id == detection_id)
        return self.db.execute(stmt).first()

    def list(self, *, page, page_size, prediction=None, risk_level=None, search=None):
        stmt = select(DetectionRecord, Email, MLModelVersion, MLModelDefinition, RiskAssessment, BehavioralResult).outerjoin(Email, Email.id == DetectionRecord.email_id).join(MLModelVersion, MLModelVersion.id == DetectionRecord.model_version_id).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).outerjoin(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id).outerjoin(BehavioralResult, BehavioralResult.detection_id == DetectionRecord.id)
        filters = []
        if prediction in {"bomb", "normal"}:
            filters.append(DetectionRecord.predicted_label == prediction)
        if risk_level in {"critical", "high", "medium", "low", "unavailable"}:
            filters.append(RiskAssessment.level == risk_level)
        if search:
            pat = f"%{search.strip()}%"
            input_match = select(DetectionInput.id).where(DetectionInput.id == DetectionRecord.input_id, or_(DetectionInput.sender.ilike(pat), DetectionInput.subject.ilike(pat), DetectionInput.filename.ilike(pat))).exists()
            filters.append(or_(Email.sender.ilike(pat), Email.subject.ilike(pat), DetectionRecord.id.cast(String).ilike(pat), input_match))
        if filters:
            stmt = stmt.where(*filters)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.execute(stmt.order_by(DetectionRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
        return rows, total

    def summary(self):
        total = self.db.scalar(select(func.count()).select_from(DetectionRecord)) or 0
        bomb = self.db.scalar(select(func.count()).where(DetectionRecord.predicted_label == "bomb")) or 0
        normal = self.db.scalar(select(func.count()).where(DetectionRecord.predicted_label == "normal")) or 0
        high = self.db.scalar(select(func.count()).select_from(RiskAssessment).where(RiskAssessment.level == "high")) or 0
        return {"total_detections": total, "bomb_detected": bomb, "normal_emails": normal, "high_risk": high}

    def settings(self):
        row = self.db.get(DetectionSettings, 1)
        if row is None:
            row = DetectionSettings(id=1)
            self.db.add(row)
            self.db.flush()
        return row

    def recent_features_for_sender(self, sender: str | None):
        stmt = select(Email, EmailFeatures).join(EmailFeatures, EmailFeatures.email_id == Email.id)
        if sender:
            stmt = stmt.where(Email.sender == sender)
        return list(self.db.execute(stmt.order_by(Email.collected_at.desc()).limit(1000)).all())

    def received_at_values(self):
        return list(self.db.scalars(select(Email.received_at).where(Email.received_at.is_not(None))).all())

    def recent_detections(self, limit=10):
        return self.list(page=1, page_size=limit)[0]
