from __future__ import annotations

from typing import Any

from .base import BaseExplainer


class ShapExplainer(BaseExplainer):
    """Compute local SHAP values when a caller supplies the exact model inputs."""

    name = "shap"

    def explain(self, detection: dict[str, Any], *, model=None, model_input=None, background=None, feature_names=None) -> dict[str, Any]:
        try:
            import numpy as np
            import shap
        except ImportError:
            return {"status": "unavailable", "method": self.name, "feature_contributions": [], "limitations": "SHAP is optional and is not installed; no attribution values were generated."}
        if model is None or model_input is None or background is None:
            return {"status": "unavailable", "method": self.name, "feature_contributions": [], "limitations": "A loaded version-matched model, transformed input, and training background are required."}
        try:
            row = np.asarray(model_input, dtype=float)
            baseline = np.asarray(background, dtype=float)
            if row.ndim == 1:
                row = row.reshape(1, -1)
            if baseline.ndim != 2 or row.shape != (1, baseline.shape[1]) or not np.isfinite(row).all() or not np.isfinite(baseline).all():
                raise ValueError("Model input and background dimensions or values are invalid.")
            names = list(feature_names or (detection.get("feature_snapshot") or {}).keys())
            if len(names) != row.shape[1]:
                raise ValueError("Feature names do not match the model input width.")
            explanation = shap.Explainer(model, baseline)(row)
            values = np.asarray(explanation.values)
            expected = np.asarray(explanation.base_values)
            if values.ndim == 3:
                class_labels = list(getattr(model, "classes_", []))
                prediction = detection.get("predicted_label")
                desired = 1 if str(prediction).lower() == "bomb" else 0
                class_index = class_labels.index(desired) if desired in class_labels else min(desired, values.shape[-1] - 1)
                values = values[0, :, class_index]
                if expected.ndim > 1:
                    expected = expected.reshape(-1)[class_index]
            else:
                values = values.reshape(-1)
                expected = expected.reshape(-1)[0] if expected.size else None
                classes = list(getattr(model, "classes_", []))
                if len(classes) == 2 and str(detection.get("predicted_label", "")).lower() == "normal":
                    values = -values
                    if expected is not None:
                        expected = -expected
            contributions = []
            for name, value in zip(names, values, strict=True):
                amount = float(value)
                contributions.append({"feature": name, "value": float(row[0, len(contributions)]), "contribution": amount, "direction": "positive" if amount > 0 else "negative" if amount < 0 else "neutral"})
            return {"status": "available", "method": self.name, "feature_contributions": contributions, "base_value": float(expected) if expected is not None else None, "limitations": "SHAP values explain this prediction relative to the supplied training background."}
        except Exception as exc:
            return {"status": "unavailable", "method": self.name, "feature_contributions": [], "limitations": f"SHAP could not explain this model input: {exc}"}
