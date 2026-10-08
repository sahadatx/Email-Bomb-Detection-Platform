
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class MetricsError(Exception):
    """Raised when evaluation metrics cannot be calculated."""


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    """Classification metrics for binary email detection."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None
    confusion_matrix: dict[str, int]
    classification_report: dict[str, Any]


class MetricsCalculator:
    """Calculate binary classification evaluation metrics."""

    LABELS = (0, 1)

    @staticmethod
    def _validate_inputs(
        y_true: Any,
        y_pred: Any,
    ) -> tuple[np.ndarray, np.ndarray]:
        try:
            actual = np.asarray(y_true)
            predicted = np.asarray(y_pred)
        except (TypeError, ValueError) as exc:
            raise MetricsError(
                "Labels could not be converted to arrays."
            ) from exc

        if actual.ndim != 1 or predicted.ndim != 1:
            raise MetricsError(
                "Actual and predicted labels must be one-dimensional."
            )

        if len(actual) == 0:
            raise MetricsError(
                "Evaluation labels must not be empty."
            )

        if len(actual) != len(predicted):
            raise MetricsError(
                "Actual and predicted label counts do not match."
            )

        if not np.isin(actual, MetricsCalculator.LABELS).all():
            raise MetricsError(
                "Actual labels must be binary (0 or 1)."
            )

        if not np.isin(predicted, MetricsCalculator.LABELS).all():
            raise MetricsError(
                "Predicted labels must be binary (0 or 1)."
            )

        return (
            actual.astype(np.int64),
            predicted.astype(np.int64),
        )

    @classmethod
    def calculate(
        cls,
        y_true: Any,
        y_pred: Any,
        y_score: Any | None = None,
    ) -> ClassificationMetrics:
        """Calculate classification metrics.

        y_score should contain the positive-class probability
        or decision score when available.
        """

        actual, predicted = cls._validate_inputs(
            y_true,
            y_pred,
        )

        auc: float | None = None

        if y_score is not None:
            try:
                scores = np.asarray(
                    y_score,
                    dtype=np.float64,
                )
            except (TypeError, ValueError) as exc:
                raise MetricsError(
                    "ROC-AUC scores must be numeric."
                ) from exc

            if scores.ndim != 1 or len(scores) != len(actual):
                raise MetricsError(
                    "ROC-AUC scores must be one-dimensional "
                    "and match the label count."
                )

            if not np.isfinite(scores).all():
                raise MetricsError(
                    "ROC-AUC scores must contain finite values."
                )

            # ROC-AUC is undefined if the evaluation set
            # contains only one class.
            if len(np.unique(actual)) == 2:
                auc = float(roc_auc_score(actual, scores))

        matrix = confusion_matrix(
            actual,
            predicted,
            labels=cls.LABELS,
        )

        tn, fp, fn, tp = matrix.ravel()

        report = classification_report(
            actual,
            predicted,
            labels=list(cls.LABELS),
            target_names=["normal", "bomb"],
            output_dict=True,
            zero_division=0,
        )

        return ClassificationMetrics(
            accuracy=float(
                accuracy_score(actual, predicted)
            ),
            precision=float(
                precision_score(
                    actual,
                    predicted,
                    pos_label=1,
                    zero_division=0,
                )
            ),
            recall=float(
                recall_score(
                    actual,
                    predicted,
                    pos_label=1,
                    zero_division=0,
                )
            ),
            f1_score=float(
                f1_score(
                    actual,
                    predicted,
                    pos_label=1,
                    zero_division=0,
                )
            ),
            roc_auc=auc,
            confusion_matrix={
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
            classification_report=report,
        )