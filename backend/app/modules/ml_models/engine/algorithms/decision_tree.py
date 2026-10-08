from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.tree import DecisionTreeClassifier

from app.modules.ml_models.engine.base import (
    BaseTrainingEngine, TrainingConfig, TrainingConfigurationError,
    TrainingDataError, TrainingDataset, TrainingResult,
)


class DecisionTreeEngine(BaseTrainingEngine):
    """Decision Tree binary classification training engine."""

    @property
    def algorithm_name(self) -> str:
        return "decision_tree"

    def validate_config(self, config: TrainingConfig) -> None:
        if not isinstance(config, TrainingConfig):
            raise TrainingConfigurationError("config must be a TrainingConfig instance.")
        params = dict(config.hyperparameters)
        allowed = {"criterion", "splitter", "max_depth", "min_samples_split", "min_samples_leaf", "max_features", "class_weight", "ccp_alpha"}
        unknown = set(params) - allowed
        if unknown:
            raise TrainingConfigurationError(f"Unsupported Decision Tree parameters: {sorted(unknown)}")
        if params.get("criterion", "gini") not in {"gini", "entropy", "log_loss"}:
            raise TrainingConfigurationError("criterion must be gini, entropy, or log_loss.")
        if params.get("splitter", "best") not in {"best", "random"}:
            raise TrainingConfigurationError("splitter must be best or random.")
        depth = params.get("max_depth")
        if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int) or depth < 1):
            raise TrainingConfigurationError("max_depth must be a positive integer or null.")
        for key, minimum in (("min_samples_split", 2), ("min_samples_leaf", 1)):
            value = params.get(key, minimum)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise TrainingConfigurationError(f"{key} must be an integer >= {minimum}.")
        alpha = params.get("ccp_alpha", 0.0)
        if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or alpha < 0:
            raise TrainingConfigurationError("ccp_alpha must be a non-negative number.")
        weights = params.get("class_weight", "balanced")
        if weights not in (None, "balanced") and not isinstance(weights, dict):
            raise TrainingConfigurationError("class_weight must be None, balanced, or a dictionary.")

    def validate_dataset(self, dataset: TrainingDataset) -> None:
        if not isinstance(dataset, TrainingDataset):
            raise TrainingDataError("dataset must be a TrainingDataset instance.")
        try:
            x = np.asarray(dataset.training_features, dtype=np.float64)
            y = np.asarray(dataset.training_labels)
            xv = np.asarray(dataset.validation_features, dtype=np.float64)
            yv = np.asarray(dataset.validation_labels)
        except (TypeError, ValueError) as exc:
            raise TrainingDataError("Dataset contains invalid feature or label values.") from exc
        if x.ndim != 2 or xv.ndim != 2 or not len(x) or not len(xv) or not x.shape[1]:
            raise TrainingDataError("Training and validation features must be non-empty 2D arrays.")
        if x.shape[1] != xv.shape[1] or len(dataset.feature_names) != x.shape[1]:
            raise TrainingDataError("Feature names and training/validation feature counts must match.")
        if y.ndim != 1 or yv.ndim != 1 or len(y) != len(x) or len(yv) != len(xv):
            raise TrainingDataError("Training and validation labels must match their feature rows.")
        if not np.isfinite(x).all() or not np.isfinite(xv).all():
            raise TrainingDataError("Features must contain only finite numeric values.")
        if len(np.unique(y)) < 2 or not np.isin(y, [0, 1]).all() or not np.isin(yv, [0, 1]).all():
            raise TrainingDataError("Training data must contain both binary classes; labels must be 0 or 1.")

    def train(self, dataset: TrainingDataset, config: TrainingConfig) -> TrainingResult:
        self.validate_config(config)
        self.validate_dataset(dataset)
        params: dict[str, Any] = dict(config.hyperparameters)
        model = DecisionTreeClassifier(
            criterion=params.get("criterion", "gini"),
            splitter=params.get("splitter", "best"),
            max_depth=params.get("max_depth"),
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1),
            max_features=params.get("max_features"),
            class_weight=params.get("class_weight", "balanced"),
            ccp_alpha=params.get("ccp_alpha", 0.0),
            random_state=config.random_state,
        )
        x = np.asarray(dataset.training_features, dtype=np.float64)
        y = np.asarray(dataset.training_labels, dtype=np.int64)
        xv = np.asarray(dataset.validation_features, dtype=np.float64)
        yv = np.asarray(dataset.validation_labels, dtype=np.int64)
        model.fit(x, y)
        accuracy = float(np.mean(model.predict(xv) == yv))
        return TrainingResult(
            model=model,
            metrics={"validation_accuracy": accuracy},
            metadata={"algorithm": self.algorithm_name, "feature_names": list(dataset.feature_names), "training_sample_count": int(len(x)), "validation_sample_count": int(len(xv)), "class_labels": model.classes_.tolist(), "tree_depth": int(model.get_depth()), "leaf_count": int(model.get_n_leaves()), "feature_importances": model.feature_importances_.tolist()},
        )
