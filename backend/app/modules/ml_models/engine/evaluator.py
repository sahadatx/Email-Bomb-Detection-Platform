
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from app.modules.ml_models.engine.base import TrainingDataset
from app.modules.ml_models.engine.metrics import (
    ClassificationMetrics,
    MetricsCalculator,
    MetricsError,
)


EvaluationSplit = Literal["validation", "testing"]


class ModelEvaluationError(Exception):
    """Base exception for model evaluation errors."""


class InvalidEvaluationSplitError(ModelEvaluationError):
    """Raised when an unsupported evaluation split is requested."""


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Result of evaluating a trained model."""

    split: EvaluationSplit
    sample_count: int
    metrics: ClassificationMetrics
    predictions: list[int]


class ModelEvaluator:
    """Evaluate a fitted binary classification model."""

    def __init__(
        self,
        metrics_calculator: MetricsCalculator | None = None,
    ) -> None:
        self._metrics_calculator = (
            metrics_calculator or MetricsCalculator()
        )

    @staticmethod
    def _get_split_data(
        dataset: TrainingDataset,
        split: EvaluationSplit,
    ) -> tuple[np.ndarray, np.ndarray]:
        if split == "validation":
            features = dataset.validation_features
            labels = dataset.validation_labels
        elif split == "testing":
            features = dataset.testing_features
            labels = dataset.testing_labels
        else:
            raise InvalidEvaluationSplitError(
                f"Unsupported evaluation split: {split}"
            )

        try:
            X = np.asarray(features, dtype=np.float64)
            y = np.asarray(labels)
        except (TypeError, ValueError) as exc:
            raise ModelEvaluationError(
                "Evaluation data contains invalid values."
            ) from exc

        if X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0:
            raise ModelEvaluationError(
                "Evaluation features must be a non-empty 2D array."
            )

        if y.ndim != 1 or len(y) != X.shape[0]:
            raise ModelEvaluationError(
                "Evaluation labels must be one-dimensional "
                "and match the feature count."
            )

        if not np.isfinite(X).all():
            raise ModelEvaluationError(
                "Evaluation features must contain only finite values."
            )

        if not np.isin(y, [0, 1]).all():
            raise ModelEvaluationError(
                "Evaluation labels must be binary (0 or 1)."
            )

        return X, y.astype(np.int64)

    @staticmethod
    def _get_positive_scores(
        model: Any,
        X: np.ndarray,
    ) -> np.ndarray | None:
        """Return the model's score for the positive class."""

        classes = getattr(model, "classes_", None)

        if classes is None or 1 not in classes:
            return None

        positive_index = list(classes).index(1)

        if hasattr(model, "predict_proba"):
            probabilities = np.asarray(
                model.predict_proba(X),
                dtype=np.float64,
            )

            if probabilities.ndim != 2:
                raise ModelEvaluationError(
                    "Model returned invalid probability output."
                )

            return probabilities[:, positive_index]

        if hasattr(model, "decision_function"):
            scores = np.asarray(
                model.decision_function(X),
                dtype=np.float64,
            )

            if scores.ndim == 1:
                # For binary classifiers, sklearn's decision
                # scores are oriented toward classes_[1].
                if positive_index == 1:
                    return scores
                return -scores

            if scores.ndim == 2:
                return scores[:, positive_index]

        return None

    def evaluate(
        self,
        *,
        model: Any,
        dataset: TrainingDataset,
        split: EvaluationSplit,
    ) -> EvaluationResult:
        """Evaluate a fitted model on validation or testing data."""

        if split not in {"validation", "testing"}:
            raise InvalidEvaluationSplitError(
                f"Unsupported evaluation split: {split}"
            )

        if model is None or not callable(
            getattr(model, "predict", None)
        ):
            raise ModelEvaluationError(
                "A fitted model with a predict() method is required."
            )

        if not isinstance(dataset, TrainingDataset):
            raise ModelEvaluationError(
                "dataset must be a TrainingDataset instance."
            )

        X, y_true = self._get_split_data(dataset, split)

        try:
            predictions = np.asarray(model.predict(X))
        except Exception as exc:
            raise ModelEvaluationError(
                "Model prediction failed."
            ) from exc

        if predictions.ndim != 1 or len(predictions) != len(y_true):
            raise ModelEvaluationError(
                "Model returned invalid prediction dimensions."
            )

        if not np.isin(predictions, [0, 1]).all():
            raise ModelEvaluationError(
                "Model predictions must be binary (0 or 1)."
            )

        scores = self._get_positive_scores(model, X)

        try:
            metrics = self._metrics_calculator.calculate(
                y_true=y_true,
                y_pred=predictions,
                y_score=scores,
            )
        except MetricsError as exc:
            raise ModelEvaluationError(
                f"Metric calculation failed: {exc}"
            ) from exc

        return EvaluationResult(
            split=split,
            sample_count=int(len(y_true)),
            metrics=metrics,
            predictions=predictions.astype(int).tolist(),
        )