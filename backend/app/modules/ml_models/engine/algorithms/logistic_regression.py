
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.modules.ml_models.engine.base import (
    BaseTrainingEngine,
    TrainingConfig,
    TrainingConfigurationError,
    TrainingDataError,
    TrainingDataset,
    TrainingResult,
)


class LogisticRegressionEngine(BaseTrainingEngine):
    """Logistic Regression classification training engine."""

    @property
    def algorithm_name(self) -> str:
        return "logistic_regression"

    def validate_config(self, config: TrainingConfig) -> None:
        if not isinstance(config, TrainingConfig):
            raise TrainingConfigurationError(
                "config must be a TrainingConfig instance."
            )

        params = dict(config.hyperparameters)

        allowed = {
            "C",
            "penalty",
            "solver",
            "max_iter",
            "tol",
            "class_weight",
            "fit_intercept",
            "intercept_scaling",
            "l1_ratio",
        }

        unknown = set(params) - allowed
        if unknown:
            raise TrainingConfigurationError(
                "Unsupported Logistic Regression parameters: "
                f"{sorted(unknown)}"
            )

        C = params.get("C", 1.0)
        if (
            isinstance(C, bool)
            or not isinstance(C, (int, float))
            or C <= 0
        ):
            raise TrainingConfigurationError(
                "C must be a positive number."
            )

        penalty = params.get("penalty", "l2")
        if penalty not in {"l1", "l2", "elasticnet", None}:
            raise TrainingConfigurationError(
                "penalty must be l1, l2, elasticnet, or None."
            )

        solver = params.get("solver", "lbfgs")
        if solver not in {
            "lbfgs",
            "liblinear",
            "newton-cg",
            "newton-cholesky",
            "sag",
            "saga",
        }:
            raise TrainingConfigurationError(
                "Unsupported Logistic Regression solver."
            )

        compatible = {
            "lbfgs": {"l2", None},
            "liblinear": {"l1", "l2"},
            "newton-cg": {"l2", None},
            "newton-cholesky": {"l2", None},
            "sag": {"l2", None},
            "saga": {"l1", "l2", "elasticnet", None},
        }

        if penalty not in compatible[solver]:
            raise TrainingConfigurationError(
                f"Solver '{solver}' does not support "
                f"penalty '{penalty}'."
            )

        max_iter = params.get("max_iter", 1000)
        if (
            isinstance(max_iter, bool)
            or not isinstance(max_iter, int)
            or max_iter < 1
        ):
            raise TrainingConfigurationError(
                "max_iter must be a positive integer."
            )

        tol = params.get("tol", 1e-4)
        if (
            isinstance(tol, bool)
            or not isinstance(tol, (int, float))
            or tol <= 0
        ):
            raise TrainingConfigurationError(
                "tol must be a positive number."
            )

        class_weight = params.get("class_weight", "balanced")
        if class_weight not in (None, "balanced") and not isinstance(
            class_weight, dict
        ):
            raise TrainingConfigurationError(
                "class_weight must be None, 'balanced', or a dictionary."
            )

        fit_intercept = params.get("fit_intercept", True)
        if not isinstance(fit_intercept, bool):
            raise TrainingConfigurationError(
                "fit_intercept must be a boolean."
            )

        intercept_scaling = params.get("intercept_scaling", 1.0)
        if (
            isinstance(intercept_scaling, bool)
            or not isinstance(intercept_scaling, (int, float))
            or intercept_scaling <= 0
        ):
            raise TrainingConfigurationError(
                "intercept_scaling must be a positive number."
            )

        l1_ratio = params.get("l1_ratio")
        if l1_ratio is not None and (
            isinstance(l1_ratio, bool)
            or not isinstance(l1_ratio, (int, float))
            or not 0 <= l1_ratio <= 1
        ):
            raise TrainingConfigurationError(
                "l1_ratio must be None or a number between 0 and 1."
            )

        if penalty == "elasticnet" and l1_ratio is None:
            raise TrainingConfigurationError(
                "l1_ratio is required when penalty is elasticnet."
            )

        if penalty != "elasticnet" and l1_ratio is not None:
            raise TrainingConfigurationError(
                "l1_ratio is only supported with elasticnet penalty."
            )

    def validate_dataset(self, dataset: TrainingDataset) -> None:
        if not isinstance(dataset, TrainingDataset):
            raise TrainingDataError(
                "dataset must be a TrainingDataset instance."
            )

        try:
            X_train = np.asarray(
                dataset.training_features,
                dtype=np.float64,
            )
            y_train = np.asarray(dataset.training_labels)
            X_valid = np.asarray(
                dataset.validation_features,
                dtype=np.float64,
            )
            y_valid = np.asarray(dataset.validation_labels)
        except (TypeError, ValueError) as exc:
            raise TrainingDataError(
                "Dataset contains invalid feature or label values."
            ) from exc

        if X_train.ndim != 2 or X_valid.ndim != 2:
            raise TrainingDataError(
                "Training and validation features must be 2D arrays."
            )

        if X_train.shape[0] == 0 or X_valid.shape[0] == 0:
            raise TrainingDataError(
                "Training and validation datasets must not be empty."
            )

        if X_train.shape[1] == 0:
            raise TrainingDataError(
                "Dataset must contain at least one feature."
            )

        if X_train.shape[1] != X_valid.shape[1]:
            raise TrainingDataError(
                "Training and validation feature counts do not match."
            )

        if len(dataset.feature_names) != X_train.shape[1]:
            raise TrainingDataError(
                "Feature names do not match the feature count."
            )

        if y_train.ndim != 1 or y_valid.ndim != 1:
            raise TrainingDataError(
                "Training and validation labels must be one-dimensional."
            )

        if len(y_train) != X_train.shape[0]:
            raise TrainingDataError(
                "Training feature and label counts do not match."
            )

        if len(y_valid) != X_valid.shape[0]:
            raise TrainingDataError(
                "Validation feature and label counts do not match."
            )

        if not np.isfinite(X_train).all() or not np.isfinite(X_valid).all():
            raise TrainingDataError(
                "Features must contain only finite numeric values."
            )

        if len(np.unique(y_train)) < 2:
            raise TrainingDataError(
                "Training data must contain at least two classes."
            )

        if not np.isin(y_train, [0, 1]).all():
            raise TrainingDataError(
                "Training labels must be binary (0 or 1)."
            )

        if not np.isin(y_valid, [0, 1]).all():
            raise TrainingDataError(
                "Validation labels must be binary (0 or 1)."
            )

    def train(
        self,
        dataset: TrainingDataset,
        config: TrainingConfig,
    ) -> TrainingResult:
        self.validate_config(config)
        self.validate_dataset(dataset)

        X_train = np.asarray(
            dataset.training_features,
            dtype=np.float64,
        )
        y_train = np.asarray(
            dataset.training_labels,
            dtype=np.int64,
        )
        X_valid = np.asarray(
            dataset.validation_features,
            dtype=np.float64,
        )
        y_valid = np.asarray(
            dataset.validation_labels,
            dtype=np.int64,
        )

        params: dict[str, Any] = dict(config.hyperparameters)

        model = LogisticRegression(
            C=params.get("C", 1.0),
            penalty=params.get("penalty", "l2"),
            solver=params.get("solver", "lbfgs"),
            max_iter=params.get("max_iter", 1000),
            tol=params.get("tol", 1e-4),
            class_weight=params.get("class_weight", "balanced"),
            fit_intercept=params.get("fit_intercept", True),
            intercept_scaling=params.get("intercept_scaling", 1.0),
            l1_ratio=params.get("l1_ratio"),
            random_state=config.random_state,
        )

        model.fit(X_train, y_train)

        predictions = model.predict(X_valid)
        accuracy = float(np.mean(predictions == y_valid))

        metadata = {
            "algorithm": self.algorithm_name,
            "feature_names": list(dataset.feature_names),
            "training_sample_count": int(X_train.shape[0]),
            "validation_sample_count": int(X_valid.shape[0]),
            "class_labels": model.classes_.tolist(),
            "iterations": model.n_iter_.tolist(),
            "coefficients": model.coef_.tolist(),
            "intercept": model.intercept_.tolist(),
        }

        return TrainingResult(
            model=model,
            metrics={
                "validation_accuracy": accuracy,
            },
            metadata=metadata,
        )