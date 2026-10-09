from __future__ import annotations

from typing import Any

from app.modules.detection.risk.engine.factors import calculate_factors


def assess_risk(prediction: str, probability: float | None, features: dict[str, Any], settings) -> tuple[int, str, list[dict[str, Any]]]:
    factors = calculate_factors(prediction, probability, features)
    score = min(100, max(0, sum(int(factor["points"]) for factor in factors)))
    if score >= settings.critical_risk_threshold:
        level = "critical"
    elif score >= settings.high_risk_threshold:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"
    return score, level, factors
