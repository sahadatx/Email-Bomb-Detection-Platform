
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class TrainingConfig:
    """Configuration for an ML training operation."""

    hyperparameters: Mapping[str, Any] = field(default_factory=dict)
    random_state: int = 42


@dataclass(frozen=True, slots=True)
class TrainingDataset:
    """Processed training, validation, and testing data."""

    feature_names: tuple[str, ...]

    training_features: Sequence[Sequence[float]]
    training_labels: Sequence[int]

    validation_features: Sequence[Sequence[float]]
    validation_labels: Sequence[int]

    testing_features: Sequence[Sequence[float]] = field(
        default_factory=tuple
    )
    testing_labels: Sequence[int] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Result returned by a training engine."""

    model: Any
    metrics: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)


class TrainingEngineError(Exception):
    """Base exception for training engine errors."""


class TrainingConfigurationError(TrainingEngineError):
    """Raised when the training configuration is invalid."""


class TrainingDataError(TrainingEngineError):
    """Raised when the supplied training data is invalid."""


class BaseTrainingEngine(ABC):
    """Abstract interface for machine-learning training engines."""

    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """Return the engine's algorithm identifier."""

    @abstractmethod
    def validate_config(
        self,
        config: TrainingConfig,
    ) -> None:
        """Validate the algorithm-specific training configuration."""

    @abstractmethod
    def validate_dataset(
        self,
        dataset: TrainingDataset,
    ) -> None:
        """Validate the processed training and validation data."""

    @abstractmethod
    def train(
        self,
        dataset: TrainingDataset,
        config: TrainingConfig,
    ) -> TrainingResult:
        """Train a model and return the fitted model and metrics."""