from __future__ import annotations

from typing import Any

from .base import BaseExplainer


class RuleExplainer(BaseExplainer):
    """Exposes only risk and behavior rules already persisted by their services."""

    name = "persisted_rules"

    def explain(self, detection: dict[str, Any]) -> dict[str, Any]:
        risk = detection.get("risk") or {}
        behavior = detection.get("behavioral") or {}
        factors = risk.get("factors") or []
        signals = behavior.get("anomalies") or []
        return {
            "status": "partial" if factors or signals else "unavailable",
            "method": self.name,
            "triggered_rules": factors,
            "behavioral_signals": signals,
            "risk_breakdown": risk,
            "limitations": "Rules and signals are copied from persisted risk and behavioral results.",
        }
