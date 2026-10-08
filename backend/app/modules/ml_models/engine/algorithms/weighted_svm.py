
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.svm import SVC

from app.modules.ml_models.engine.base import (
    BaseTrainingEngine,
    TrainingConfig,
    TrainingConfigurationError,
    TrainingDataError,
    TrainingDataset,
    TrainingResult,
)


class WeightedSVMEngine(BaseTrainingEngine):
    """Weighted Support Vector Machine training engine."""

    @property
    def algorithm_name(self) -> str:
        return "weighted_svm"

    def validate_config(self, config: TrainingConfig) -> None:
        if not isinstance(config, TrainingConfig):
            raise TrainingConfigurationError(
                "config must be a TrainingConfig instance."
            )

        params = dict(config.hyperparameters)

        allowed = {
            "C",
            "kernel",
            "degree",
            "gamma",
            "coef0",
            "class_weight",
            "probability",
            "tol",
            "max_iter",
            "decision_function_shape",
        }

        unknown = set(params) - allowed
        if unknown:
            raise TrainingConfigurationError(
                f"Unsupported Weighted SVM parameters: {sorted(unknown)}"
            )

        if "C" in params and (
            isinstance(params["C"], bool)
            or not isinstance(params["C"], (int, float))
            or params["C"] <= 0
        ):
            raise TrainingConfigurationError(
                "C must be a positive number."
            )

        if params.get("kernel", "rbf") not in {
            "linear",
            "poly",
            "rbf",
            "sigmoid",
        }:
            raise TrainingConfigurationError(
                "kernel must be linear, poly, rbf, or sigmoid."
            )

        if "degree" in params and (
            isinstance(params["degree"], bool)
            or not isinstance(params["degree"], int)
            or params["degree"] < 1
        ):
            raise TrainingConfigurationError(
                "degree must be a positive integer."
            )

        if "max_iter" in params and (
            isinstance(params["max_iter"], bool)
            or not isinstance(params["max_iter"], int)
            or params["max_iter"] == 0
            or params["max_iter"] < -1
        ):
            raise TrainingConfigurationError(
                "max_iter must be -1 or a positive integer."
            )

        if "tol" in params and (
            isinstance(params["tol"], bool)
            or not isinstance(params["tol"], (int, float))
            or params["tol"] <= 0
        ):
            raise TrainingConfigurationError(
                "tol must be a positive number."
            )

        if "gamma" in params:
            gamma = params["gamma"]
            if not (
                isinstance(gamma, (int, float))
                and not isinstance(gamma, bool)
                and gamma > 0
            ) and gamma not in {"scale", "auto"}:
                raise TrainingConfigurationError(
                    "gamma must be 'scale', 'auto', or a positive number."
                )

        if "class_weight" in params:
            class_weight = params["class_weight"]
            if class_weight not in (None, "balanced") and not isinstance(
                class_weight, dict
            ):
                raise TrainingConfigurationError(
                    "class_weight must be None, 'balanced', or a dictionary."
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

        if len(np.unique(y_valid)) < 1:
            raise TrainingDataError(
                "Validation data must contain at least one class."
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

        # The model uses class weights to adjust the penalty
        # applied to errors for each class.
        model = SVC(
            C=params.get("C", 1.0),
            kernel=params.get("kernel", "rbf"),
            degree=params.get("degree", 3),
            gamma=params.get("gamma", "scale"),
            coef0=params.get("coef0", 0.0),
            class_weight=params.get("class_weight", "balanced"),
            probability=params.get("probability", True),
            tol=params.get("tol", 1e-3),
            max_iter=params.get("max_iter", -1),
            decision_function_shape=params.get(
                "decision_function_shape",
                "ovr",
            ),
            random_state=config.random_state,
        )

        model.fit(X_train, y_train)

        predictions = model.predict(X_valid)
        accuracy = float(np.mean(predictions == y_valid))

        metrics = {
            "validation_accuracy": accuracy,
        }

        metadata = {
            "algorithm": self.algorithm_name,
            "kernel": model.kernel,
            "feature_names": list(dataset.feature_names),
            "training_sample_count": int(X_train.shape[0]),
            "validation_sample_count": int(X_valid.shape[0]),
            "class_labels": model.classes_.tolist(),
            "support_vector_count": int(
                model.n_support_.sum()
            ),
        }

        return TrainingResult(
            model=model,
            metrics=metrics,
            metadata=metadata,
        )