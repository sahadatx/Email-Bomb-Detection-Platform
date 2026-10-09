from __future__ import annotations

from typing import Any


class RiskAdapter:
    """Normalize persisted Detection RiskService output without recalculating it."""

    @staticmethod
    def from_detection(payload: dict[str, Any]) -> dict[str, Any] | None:
        risk = payload.get("risk")
        if not risk:
            return None
        return {"score": risk.get("score"), "level": risk.get("level", "unavailable"), "status": risk.get("status", "unavailable"), "factors": risk.get("factors") or []}
