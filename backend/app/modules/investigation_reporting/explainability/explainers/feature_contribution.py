from __future__ import annotations

from typing import Any

from .base import BaseExplainer


class FeatureContributionExplainer(BaseExplainer):
    """Reports recorded feature values without claiming unsupported attribution."""

    name = "feature_values"

    def explain(self, detection: dict[str, Any], *, model=None, model_input=None, baseline=None, feature_names=None) -> dict[str, Any]:
        persisted = detection.get("feature_contributions")
        if isinstance(persisted, list):
            return {"status": "available", "method": "persisted_model_contributions", "feature_contributions": persisted, "limitations": "Contribution values were supplied by the prediction backend."}
        if model is not None and model_input is not None and hasattr(model, "coef_"):
            try:
                import numpy as np
                row = np.asarray(model_input, dtype=float).reshape(-1)
                coefficients = np.asarray(model.coef_, dtype=float)
                if coefficients.ndim == 2:
                    class_labels = list(getattr(model, "classes_", []))
                    desired = 1 if str(detection.get("predicted_label", "")).lower() == "bomb" else 0
                    if coefficients.shape[0] == 1 and len(class_labels) == 2 and desired in class_labels:
                        coefficients = coefficients[0] * (1 if class_labels[1] == desired else -1)
                    else:
                        index = class_labels.index(desired) if desired in class_labels else min(desired, coefficients.shape[0] - 1)
                        coefficients = coefficients[index]
                else:
                    coefficients = coefficients.reshape(-1)
                base = np.zeros_like(row) if baseline is None else np.asarray(baseline, dtype=float).reshape(-1)
                if row.shape != coefficients.shape or base.shape != row.shape:
                    raise ValueError("Input, baseline, and coefficient widths differ.")
                names = list(feature_names or (detection.get("feature_snapshot") or {}).keys())
                if len(names) != len(row):
                    raise ValueError("Feature names do not match the model input width.")
                contributions = []
                for name, value, amount in zip(names, row, coefficients * (row - base), strict=True):
                    score = float(amount)
                    contributions.append({"feature": name, "value": float(value), "contribution": score, "direction": "positive" if score > 0 else "negative" if score < 0 else "neutral"})
                return {"status": "available", "method": "linear_coefficient_contribution", "feature_contributions": contributions, "limitations": "Linear contribution is relative to the supplied baseline and applies only to a linear model."}
            except Exception as exc:
                limitation = f"Linear contribution could not be calculated: {exc}"
        else:
            limitation = "The detection record stores feature values, not local contribution scores."
        values = self.feature_values(detection)
        return {"status": "partial" if values else "unavailable", "method": self.name, "feature_contributions": values, "limitations": limitation}
