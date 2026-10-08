
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from app.modules.ml_models.engine.base import (
    TrainingDataset,
    TrainingResult,
)
from app.modules.ml_models.engine.trainer import (
    ModelTrainer,
    ModelTrainerError,
)

logger = logging.getLogger(__name__)


class TrainingExecutorError(Exception):
    """Base exception for training execution errors."""


class TrainingRunExecutionError(TrainingExecutorError):
    """Raised when a training run cannot be executed."""


@dataclass(frozen=True, slots=True)
class TrainingExecutionResult:
    """Summary of a completed training execution."""

    training_run_id: UUID
    result: TrainingResult
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


class TrainingExecutor:
    """Execute model training using a prepared dataset.

    Database lifecycle, preprocessing artifact loading, and
    background scheduling are intentionally handled separately.
    """

    def __init__(
        self,
        trainer: ModelTrainer,
        dataset_loader: Callable[[UUID], TrainingDataset],
    ) -> None:
        self._trainer = trainer
        self._dataset_loader = dataset_loader

    def execute(
        self,
        *,
        training_run_id: UUID,
        algorithm: str,
        hyperparameters: dict[str, object] | None = None,
        random_state: int = 42,
    ) -> TrainingExecutionResult:
        """Load a prepared dataset and execute model training."""

        if not isinstance(training_run_id, UUID):
            raise TrainingRunExecutionError(
                "training_run_id must be a UUID."
            )

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise TrainingRunExecutionError(
                "algorithm must be a non-empty string."
            )

        started_at = datetime.now(timezone.utc)

        try:
            dataset = self._dataset_loader(training_run_id)

            if not isinstance(dataset, TrainingDataset):
                raise TrainingRunExecutionError(
                    "Dataset loader returned an invalid dataset."
                )

            result = self._trainer.train(
                algorithm=algorithm,
                dataset=dataset,
                hyperparameters=hyperparameters,
                random_state=random_state,
            )

            completed_at = datetime.now(timezone.utc)
            duration = (
                completed_at - started_at
            ).total_seconds()

            return TrainingExecutionResult(
                training_run_id=training_run_id,
                result=result,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=max(duration, 0.0),
            )

        except TrainingExecutorError:
            raise

        except ModelTrainerError as exc:
            logger.exception(
                "Model training failed for run %s",
                training_run_id,
            )
            raise TrainingRunExecutionError(
                f"Training failed: {exc}"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected error during training run %s",
                training_run_id,
            )
            raise TrainingRunExecutionError(
                "Unexpected training execution error."
            ) from exc