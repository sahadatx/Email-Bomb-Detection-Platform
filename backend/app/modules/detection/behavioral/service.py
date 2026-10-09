from datetime import datetime, timedelta, timezone

from app.modules.detection.behavioral.engine.analysis import analyze_sender_history
from app.modules.detection.models import BehavioralResult
from app.modules.detection.behavioral.repository import BehavioralRepository


class BehavioralService:
    """Owns sender-history analysis and behavioral reporting."""

    def __init__(self, db):
        self.repository = BehavioralRepository(db)

    def analyze(self, email, history, enabled=True):
        status, summary, metrics, anomalies = analyze_sender_history(email, history, enabled)
        return BehavioralResult(status=status, summary=summary, metrics=metrics, anomalies=anomalies)

    def summary(self):
        results = self.repository.all_results()
        anomalies = [item for result in results for item in (result.anomalies or [])]
        return {"emails_analyzed": self.repository.analyzed_email_count(), "anomalies": len(anomalies), "patterns": anomalies}

    def activity(self, period="7d"):
        days = {"24h": 1, "7d": 7, "30d": 30}[period]
        since = datetime.now(timezone.utc) - timedelta(days=days)
        counts = {}
        for timestamp in self.repository.activity_timestamps(since):
            if timestamp:
                key = timestamp.strftime("%Y-%m-%d %H:00" if period == "24h" else "%Y-%m-%d")
                counts[key] = counts.get(key, 0) + 1
        return {"period": period, "activity": [{"time": key, "emails": value} for key, value in sorted(counts.items())]}

    def anomalies(self):
        output = []
        for result, detection, email, input_row in self.repository.anomaly_records():
            for anomaly in result.anomalies or []:
                output.append({"detection_id": detection.id, "sender": email.sender if email else (input_row.sender if input_row else None), "subject": email.subject if email else (input_row.subject if input_row else None), "created_at": result.created_at, **anomaly})
        return output
