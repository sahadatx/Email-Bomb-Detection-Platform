from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.modules.detection.models import BehavioralResult, DetectionInput, DetectionRecord, RiskAssessment
from app.modules.emails.models import Email
from app.modules.ml_models.models import MLEvaluationRun, MLModelDefinition, MLModelVersion
from app.modules.preprocessing.models import PreprocessingRun
from .integrations.detection_adapter import DetectionAdapter


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db
        self.detections = DetectionAdapter(db)

    def count_detections(self, **filters):
        statement = self.detections.statement(**filters).with_only_columns(func.count(DetectionRecord.id))
        return int(self.db.scalar(statement) or 0)

    def overview(self, **filters):
        base = self.detections.statement(**filters)
        total = int(self.db.scalar(base.with_only_columns(func.count(DetectionRecord.id))) or 0)
        bomb = int(self.db.scalar(base.where(DetectionRecord.predicted_label == "bomb").with_only_columns(func.count(DetectionRecord.id))) or 0)
        high = int(self.db.scalar(base.join(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id).where(RiskAssessment.level.in_(("high", "critical"))).with_only_columns(func.count(func.distinct(DetectionRecord.id)))) or 0)
        return {"total": total, "bomb": bomb, "high_risk": high}

    def classification_trend(self, *, filters, interval: str):
        base = self.detections.statement(**filters)
        dialect = self.db.get_bind().dialect.name
        if dialect == "sqlite":
            bucket = func.strftime(
                "%Y-%m-%d" if interval == "day" else "%Y-%m-%dT%H:00:00Z",
                DetectionRecord.created_at,
            )
        else:
            bucket = func.date_trunc(interval, DetectionRecord.created_at)
        rows = self.db.execute(
            base.with_only_columns(
                bucket.label("timestamp"),
                DetectionRecord.predicted_label,
                func.count(DetectionRecord.id),
            ).group_by(bucket, DetectionRecord.predicted_label).order_by(bucket)
        ).all()
        grouped: dict[str, dict[str, int]] = {}
        for timestamp, label, count in rows:
            key = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            if interval == "hour" and not key.endswith("Z"):
                key = key[:13] + ":00:00Z"
            grouped.setdefault(key, {"normal": 0, "bomb": 0})[label] = int(count)
        return [{"timestamp": key, **value} for key, value in sorted(grouped.items())]

    def classification_distribution(self, **filters):
        base = self.detections.statement(**filters)
        rows = self.db.execute(base.with_only_columns(DetectionRecord.predicted_label, func.count(DetectionRecord.id)).group_by(DetectionRecord.predicted_label)).all()
        result = {"normal": 0, "bomb": 0}
        result.update({label: int(count) for label, count in rows if label in result})
        return [{"classification": label, "count": count} for label, count in result.items()]

    def risk_distribution(self, **filters):
        base = self.detections.statement(**filters).join(RiskAssessment, RiskAssessment.detection_id == DetectionRecord.id)
        rows = self.db.execute(base.with_only_columns(RiskAssessment.level, func.count(func.distinct(DetectionRecord.id))).group_by(RiskAssessment.level)).all()
        counts = {level: 0 for level in ("low", "medium", "high", "critical")}
        counts.update({level: int(count) for level, count in rows if level in counts})
        return [{"risk_level": level, "count": count} for level, count in counts.items()]

    def performance(self, *, start: datetime, end: datetime, model_definition_id: UUID | None, evaluation_split: str):
        statement = select(MLEvaluationRun, MLModelVersion, MLModelDefinition).join(MLModelVersion, MLModelVersion.id == MLEvaluationRun.model_version_id).join(MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id).where(MLEvaluationRun.status == "completed", MLEvaluationRun.evaluation_split == evaluation_split, MLEvaluationRun.created_at >= start, MLEvaluationRun.created_at <= end)
        if model_definition_id:
            statement = statement.where(MLModelDefinition.id == model_definition_id)
        row = self.db.execute(statement.order_by(MLEvaluationRun.created_at.desc()).limit(1)).first()
        if not row:
            return None
        evaluation, version, model = row
        return {"evaluation_id": str(evaluation.id), "evaluation_split": evaluation.evaluation_split, "model_definition_id": str(model.id), "model_name": model.name, "algorithm": model.algorithm, "model_version_id": str(version.id), "version": version.version, "accuracy": evaluation.accuracy, "precision": evaluation.precision, "recall": evaluation.recall, "f1_score": evaluation.f1_score, "sample_count": evaluation.sample_count, "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None}

    def behavior(self, **filters):
        base = self.detections.statement(**filters).join(BehavioralResult, BehavioralResult.detection_id == DetectionRecord.id)
        records = self.db.scalars(base.with_only_columns(BehavioralResult)).all()
        burst = 0
        patterns = 0
        hourly: dict[str, int] = {}
        for record in records:
            anomalies = record.anomalies or []
            if anomalies:
                patterns += len(anomalies)
            for anomaly in anomalies:
                kind = str(anomaly.get("type", anomaly.get("kind", ""))).lower() if isinstance(anomaly, dict) else str(anomaly).lower()
                if "burst" in kind:
                    burst += 1
            dt = record.created_at
            if dt:
                key = dt.strftime("%Y-%m-%dT%H:00:00Z")
                hourly[key] = hourly.get(key, 0) + 1
        return {"emails_analyzed": len(records), "burst_events": burst, "suspicious_patterns": patterns, "activity": [{"timestamp": key, "emails": val} for key, val in sorted(hourly.items())], "available": bool(records)}

    def recent(self, *, filters, limit: int):
        risk_row = aliased(RiskAssessment)
        statement = self.detections.statement(**filters).outerjoin(
            risk_row, risk_row.detection_id == DetectionRecord.id
        ).outerjoin(
            Email, Email.id == DetectionRecord.email_id
        ).outerjoin(
            DetectionInput, DetectionInput.id == DetectionRecord.input_id
        ).join(
            MLModelDefinition, MLModelDefinition.id == MLModelVersion.model_definition_id
        ).with_only_columns(
            DetectionRecord,
            Email,
            DetectionInput,
            risk_row,
            MLModelVersion,
            MLModelDefinition,
        ).order_by(DetectionRecord.created_at.desc()).limit(limit)
        result = []
        for detection, email, input_record, risk, version, model in self.db.execute(statement).all():
            result.append({"id": str(detection.id), "email_id": str(detection.email_id) if detection.email_id else None, "sender": email.sender if email else (input_record.sender if input_record else None), "subject": email.subject if email else (input_record.subject if input_record else None), "classification": detection.predicted_label, "confidence": detection.confidence, "risk_level": risk.level if risk else None, "risk_score": risk.score if risk else None, "model_name": model.name if model else None, "model_version": version.version if version else None, "created_at": detection.created_at.isoformat() if detection.created_at else None})
        return result

    def model_options(self):
        return [{"id": str(model.id), "name": model.name, "algorithm": model.algorithm} for model in self.detections.models()]
