from .aggregations import chart_interval, date_window
from .repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, db):
        self.repository = AnalyticsRepository(db)

    def filters(self, filters):
        start, end = date_window(filters)
        return {"start": start, "end": end, "classification": filters.classification, "risk_level": filters.risk_level, "model_definition_id": filters.model_definition_id}

    def overview(self, filters):
        values = self.filters(filters)
        data = self.repository.overview(**values)
        total = data["total"]
        return {"filters": filters.model_dump(mode="json"), "total_emails": {"value": total, "available": True, "description": "Emails with a completed detection in the selected range"}, "bomb_emails": {"value": data["bomb"], "available": True, "description": "Completed detections classified as bomb"}, "detection_rate": {"value": round(data["bomb"] / total * 100, 2) if total else None, "available": total > 0, "description": "Bomb classifications divided by completed detections"}, "high_risk_emails": {"value": data["high_risk"], "available": True, "description": "Completed detections with High or Critical risk"}, "total_detections": total, "data_sources": ["email_detections", "detection_risk_assessments"]}

    def classification(self, filters):
        values = self.filters(filters)
        start, end = values.pop("start"), values.pop("end")
        return {"items": self.repository.classification_trend(filters={"start": start, "end": end, **values}, interval=chart_interval(start, end)), "distribution": self.repository.classification_distribution(start=start, end=end, **values)}

    def risk(self, filters):
        return {"items": self.repository.risk_distribution(**self.filters(filters))}

    def performance(self, filters, evaluation_split):
        start, end = date_window(filters)
        value = self.repository.performance(start=start, end=end, model_definition_id=filters.model_definition_id, evaluation_split=evaluation_split)
        return {"available": value is not None, "evaluation_split": evaluation_split, "evaluation": value, "metrics": ({key: value[key] for key in ("precision", "recall", "f1_score", "accuracy")} if value else {"precision": None, "recall": None, "f1_score": None, "accuracy": None})}

    def behavior(self, filters):
        return self.repository.behavior(**self.filters(filters))

    def recent(self, filters, limit=20):
        return {"items": self.repository.recent(filters=self.filters(filters), limit=limit)}
