from __future__ import annotations

from typing import Any


def calculate_factors(prediction: str, probability: float | None, features: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate model output and canonical features into auditable risk evidence."""
    factors = []
    if prediction == "bomb":
        factors.append({"name": "Model prediction", "value": "Bomb", "impact": "high", "points": 45})
        if probability is not None:
            factors.append({"name": "Model probability", "value": round(probability, 4), "impact": "model", "points": round(probability * 30)})
    keywords = int(features.get("F9", 0) or 0)
    if keywords:
        factors.append({"name": "Suspicious keywords", "value": keywords, "impact": "medium", "points": min(15, keywords * 3)})
    per_minute = int(features.get("F11", 0) or 0)
    if per_minute >= 5:
        factors.append({"name": "Email frequency", "value": per_minute, "impact": "high", "points": 15})
    elif per_minute >= 3:
        factors.append({"name": "Email frequency", "value": per_minute, "impact": "medium", "points": 8})
    per_hour = int(features.get("F12", 0) or 0)
    if per_hour >= 20:
        factors.append({"name": "Hourly volume", "value": per_hour, "impact": "medium", "points": 10})
    if features.get("F2") is True:
        factors.append({"name": "Known sender domain", "value": True, "impact": "reducing", "points": -10})
    return factors
