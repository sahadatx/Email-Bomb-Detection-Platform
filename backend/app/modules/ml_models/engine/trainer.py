
from __future__ import annotations

from typing import Mapping

from app.modules.ml_models.engine.base import (
    BaseTrainingEngine,
    TrainingConfig,
    TrainingConfigurationError,
    TrainingDataset,
    TrainingEngineError,
    TrainingResult,
)
from app.modules.ml_models.engine.algorithms.logistic_regression import (
    LogisticRegressionEngine,
)
from app.modules.ml_models.engine.algorithms.random_forest import (
    RandomForestEngine,
)
from app.modules.ml_models.engine.algorithms.decision_tree import (
    DecisionTreeEngine,
)
from app.modules.ml_models.engine.algorithms.svm import SVMEngine
from app.modules.ml_models.engine.algorithms.weighted_svm import (
    WeightedSVMEngine,
)


class ModelTrainerError(Exception):
    """Base exception for model training orchestration errors."""


class UnsupportedAlgorithmError(ModelTrainerError):
    """Raised when the requested algorithm is not registered."""


class ModelTrainer:
    """Select and execute an ML training engine."""

    def __init__(
        self,
        engines: Mapping[str, BaseTrainingEngine] | None = None,
    ) -> None:
        if engines is None:
            engines = {
                "weighted_svm": WeightedSVMEngine(),
                "random_forest": RandomForestEngine(),
                "logistic_regression": LogisticRegressionEngine(),
                "decision_tree": DecisionTreeEngine(),
                "svm": SVMEngine(),
            }

        self._engines = dict(engines)

        for name, engine in self._engines.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Engine names must be non-empty strings."
                )

            if not isinstance(engine, BaseTrainingEngine):
                raise TypeError(
                    f"Engine '{name}' must implement BaseTrainingEngine."
                )

            if engine.algorithm_name != name:
                raise ValueError(
                    f"Engine registration name '{name}' does not match "
                    f"its algorithm name '{engine.algorithm_name}'."
                )

    @property
    def supported_algorithms(self) -> tuple[str, ...]:
        """Return the registered algorithm identifiers."""
        return tuple(sorted(self._engines))

    def get_engine(self, algorithm: str) -> BaseTrainingEngine:
        """Return the engine registered for an algorithm."""

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise UnsupportedAlgorithmError(
                "Algorithm must be a non-empty string."
            )

        engine = self._engines.get(algorithm.strip().lower())

        if engine is None:
            raise UnsupportedAlgorithmError(
                f"Unsupported algorithm: {algorithm}"
            )

        return engine

    def train(
        self,
        *,
        algorithm: str,
        dataset: TrainingDataset,
        hyperparameters: Mapping[str, object] | None = None,
        random_state: int = 42,
    ) -> TrainingResult:
        """Train a model using the selected algorithm engine."""

        engine = self.get_engine(algorithm)

        if hyperparameters is not None and not isinstance(
            hyperparameters, Mapping
        ):
            raise TrainingConfigurationError(
                "hyperparameters must be a mapping."
            )

        if (
            isinstance(random_state, bool)
            or not isinstance(random_state, int)
        ):
            raise TrainingConfigurationError(
                "random_state must be an integer."
            )

        config = TrainingConfig(
            hyperparameters=dict(hyperparameters or {}),
            random_state=random_state,
        )

        try:
            engine.validate_config(config)
            engine.validate_dataset(dataset)

            result = engine.train(
                dataset=dataset,
                config=config,
            )

        except TrainingEngineError as exc:
            raise ModelTrainerError(
                f"Training failed for '{algorithm}': {exc}"
            ) from exc

        if not isinstance(result, TrainingResult):
            raise ModelTrainerError(
                f"Engine '{algorithm}' returned an invalid training result."
            )

        return result
