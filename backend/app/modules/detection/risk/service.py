from collections import defaultdict

from app.modules.detection.models import RiskAssessment
from app.modules.detection.risk.repository import RiskRepository
from app.modules.detection.risk.engine.scoring import assess_risk


class RiskService:
    """Owns risk calculation and risk-report aggregation."""

    def __init__(self, db):
        self.repository = RiskRepository(db)

    def assess(self, prediction, confidence, features, settings):
        score, level, factors = assess_risk(prediction, confidence, features, settings)
        return RiskAssessment(score=score, level=level, factors=factors, status="completed")

    def summary(self):
        return {"distribution": self.repository.distribution()}

    def factors(self):
        grouped = defaultdict(lambda: {"occurrences": 0, "impact": None, "detection_ids": []})
        for assessment in self.repository.assessments():
            for factor in assessment.factors or []:
                item = grouped[factor["name"]]
                item["occurrences"] += 1
                item["impact"] = factor.get("impact")
                if len(item["detection_ids"]) < 100:
                    item["detection_ids"].append(str(assessment.detection_id))
        return [{"name": name, **value} for name, value in sorted(grouped.items(), key=lambda pair: pair[1]["occurrences"], reverse=True)]
