from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.detection.models import DetectionRecord, RiskAssessment
from app.modules.ml_models.models import MLModelDefinition, MLModelVersion


class DetectionAdapter:
    """Build a shared filtered detection query without copying source data."""

    def __init__(self, db: Session):
        self.db = db

    def statement(self, *, start: datetime, end: datetime, classification=None, risk_level=None, model_definition_id: UUID | None = None):
        statement = select(DetectionRecord).join(
            MLModelVersion, MLModelVersion.id == DetectionRecord.model_version_id
        ).where(
            DetectionRecord.status == "completed",
            DetectionRecord.created_at >= start,
            DetectionRecord.created_at <= end,
        )
        if classification:
            statement = statement.where(DetectionRecord.predicted_label == classification)
        if risk_level:
            matching_risk = select(RiskAssessment.detection_id).where(
                RiskAssessment.level == risk_level
            )
            statement = statement.where(DetectionRecord.id.in_(matching_risk))
        if model_definition_id:
            statement = statement.where(MLModelVersion.model_definition_id == model_definition_id)
        return statement

    def models(self):
        statement = select(MLModelDefinition).order_by(MLModelDefinition.name.asc())
        return self.db.scalars(statement).all()
