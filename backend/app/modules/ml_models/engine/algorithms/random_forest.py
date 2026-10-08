
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.modules.ml_models.engine.base import (
    BaseTrainingEngine,
    TrainingConfig,
    TrainingConfigurationError,
    TrainingDataError,
    TrainingDataset,
    TrainingResult,
)


class RandomForestEngine(BaseTrainingEngine):
    """Random Forest classification training engine."""

    @property
    def algorithm_name(self) -> str:
        return "random_forest"

    def validate_config(self, config: TrainingConfig) -> None:
        if not isinstance(config, TrainingConfig):
            raise TrainingConfigurationError(
                "config must be a TrainingConfig instance."
            )

        params = dict(config.hyperparameters)

        allowed = {
            "n_estimators",
            "criterion",
            "max_depth",
            "min_samples_split",
            "min_samples_leaf",
            "max_features",
            "bootstrap",
            "class_weight",
            "max_samples",
            "n_jobs",
        }

        unknown = set(params) - allowed
        if unknown:
            raise TrainingConfigurationError(
                f"Unsupported Random Forest parameters: {sorted(unknown)}"
            )

        n_estimators = params.get("n_estimators", 100)
        if (
            isinstance(n_estimators, bool)
            or not isinstance(n_estimators, int)
            or n_estimators < 1
        ):
            raise TrainingConfigurationError(
                "n_estimators must be a positive integer."
            )

        criterion = params.get("criterion", "gini")
        if criterion not in {"gini", "entropy", "log_loss"}:
            raise TrainingConfigurationError(
                "criterion must be gini, entropy, or log_loss."
            )

        max_depth = params.get("max_depth")
        if max_depth is not None and (
            isinstance(max_depth, bool)
            or not isinstance(max_depth, int)
            or max_depth < 1
        ):
            raise TrainingConfigurationError(
                "max_depth must be None or a positive integer."
            )

        for name, default in (
            ("min_samples_split", 2),
            ("min_samples_leaf", 1),
        ):
            value = params.get(name, default)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < (2 if name == "min_samples_split" else 1)
            ):
                raise TrainingConfigurationError(
                    f"{name} must be an integer >= "
                    f"{2 if name == 'min_samples_split' else 1}."
                )

        max_features = params.get("max_features", "sqrt")
        if max_features not in {"sqrt", "log2", None} and not (
            isinstance(max_features, (int, float))
            and not isinstance(max_features, bool)
            and 0 < max_features <= 1
        ):
            raise TrainingConfigurationError(
                "max_features must be sqrt, log2, None, "
                "or a number in (0, 1]."
            )

        bootstrap = params.get("bootstrap", True)
        if not isinstance(bootstrap, bool):
            raise TrainingConfigurationError(
                "bootstrap must be a boolean."
            )

        class_weight = params.get("class_weight", "balanced")
        if class_weight not in (
            None,
            "balanced",
            "balanced_subsample",
        ) and not isinstance(class_weight, dict):
            raise TrainingConfigurationError(
                "class_weight must be None, balanced, "
                "balanced_subsample, or a dictionary."
            )

        max_samples = params.get("max_samples")
        if max_samples is not None:
            if not bootstrap:
                raise TrainingConfigurationError(
                    "max_samples requires bootstrap=True."
                )
            if isinstance(max_samples, bool) or not (
                isinstance(max_samples, int)
                and max_samples >= 1
                or isinstance(max_samples, float)
                and 0 < max_samples <= 1
            ):
                raise TrainingConfigurationError(
                    "max_samples must be None, a positive integer, "
                    "or a float in (0, 1]."
                )

        n_jobs = params.get("n_jobs", -1)
        if (
            isinstance(n_jobs, bool)
            or not isinstance(n_jobs, int)
            or n_jobs == 0
        ):
            raise TrainingConfigurationError(
                "n_jobs must be a non-zero integer."
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

        model = RandomForestClassifier(
            n_estimators=params.get("n_estimators", 100),
            criterion=params.get("criterion", "gini"),
            max_depth=params.get("max_depth"),
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1),
            max_features=params.get("max_features", "sqrt"),
            bootstrap=params.get("bootstrap", True),
            class_weight=params.get("class_weight", "balanced"),
            max_samples=params.get("max_samples"),
            n_jobs=params.get("n_jobs", -1),
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
            "feature_names": list(dataset.feature_names),
            "training_sample_count": int(X_train.shape[0]),
            "validation_sample_count": int(X_valid.shape[0]),
            "class_labels": model.classes_.tolist(),
            "tree_count": len(model.estimators_),
            "feature_importances": (
                model.feature_importances_.tolist()
            ),
        }

        return TrainingResult(
            model=model,
            metrics=metrics,
            metadata=metadata,
        )