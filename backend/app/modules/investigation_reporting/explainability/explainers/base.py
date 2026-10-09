from __future__ import annotations

from typing import Any, Protocol


class Explainer(Protocol):
    name: str

    def explain(self, detection: dict[str, Any]) -> dict[str, Any]: ...


class BaseExplainer:
    name = "base"

    def explain(self, detection: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def feature_values(detection: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"feature": key, "value": value, "contribution": None, "direction": "unavailable"}
            for key, value in (detection.get("feature_snapshot") or {}).items()
        ]
