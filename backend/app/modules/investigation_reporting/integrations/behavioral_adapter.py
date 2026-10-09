from __future__ import annotations

from typing import Any


class BehavioralAdapter:
    """Normalize persisted Detection BehavioralService output."""

    @staticmethod
    def from_detection(payload: dict[str, Any]) -> dict[str, Any] | None:
        result = payload.get("behavioral")
        if not result:
            return None
        return {"status": result.get("status", "unavailable"), "summary": result.get("summary") or "", "metrics": result.get("metrics") or {}, "anomalies": result.get("anomalies") or []}
