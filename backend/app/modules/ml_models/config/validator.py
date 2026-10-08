from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


SUPPORTED_ALGORITHMS = {
    "decision_tree",
    "svm",
    "weighted_svm",
    "random_forest",
    "logistic_regression",
}

ALGORITHM_DEFAULTS: dict[str, dict[str, Any]] = {
    "decision_tree": {
        "criterion": "gini",
        "max_depth": None,
        "class_weight": "balanced",
    },
    "svm": {
        "kernel": "rbf",
        "C": 1.0,
        "gamma": "scale",
        "class_weight": None,
    },
    "weighted_svm": {
        "kernel": "rbf",
        "C": 1.0,
        "gamma": "scale",
    },
    "random_forest": {
        "n_estimators": 100,
        "max_depth": None,
        "class_weight": "balanced",
    },
    "logistic_regression": {
        "C": 1.0,
        "max_iter": 1000,
        "class_weight": "balanced",
    },
}


class ModelConfigurationError(ValueError):
    """Raised when an ML model configuration is invalid."""


class TrainingConfigurationError(ValueError):
    """Raised when a training configuration is invalid."""


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    algorithm: str = Field(min_length=1, max_length=100)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "algorithm")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty.")
        return value


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    random_state: int = 42
    test_size: float = Field(default=0.2, gt=0, lt=1)
    validation_size: float = Field(default=0.2, gt=0, lt=1)
    batch_size: int = Field(default=256, gt=0)
    save_artifact: bool = True


def validate_model_configuration(
    *,
    name: str,
    algorithm: str,
    hyperparameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and normalize a model definition configuration."""

    try:
        config = ModelConfig(
            name=name,
            algorithm=algorithm,
            hyperparameters=hyperparameters or {},
        )
    except ValidationError as exc:
        raise ModelConfigurationError(str(exc)) from exc

    algorithm_key = config.algorithm.lower()

    if algorithm_key not in SUPPORTED_ALGORITHMS:
        supported = ", ".join(sorted(SUPPORTED_ALGORITHMS))
        raise ModelConfigurationError(
            f"Unsupported algorithm '{config.algorithm}'. "
            f"Supported algorithms: {supported}."
        )

    parameters = {
        **ALGORITHM_DEFAULTS[algorithm_key],
        **config.hyperparameters,
    }

    _validate_hyperparameters(algorithm_key, parameters)

    return {
        "name": config.name,
        "algorithm": algorithm_key,
        "hyperparameters": parameters,
    }


def _validate_hyperparameters(
    algorithm: str,
    parameters: dict[str, Any],
) -> None:
    """Validate algorithm-specific hyperparameters."""

    if algorithm in {"weighted_svm", "svm"}:
        _validate_positive_number(parameters, "C")

        kernel = parameters.get("kernel")
        if kernel not in {"linear", "poly", "rbf", "sigmoid"}:
            raise ModelConfigurationError(
                "weighted_svm kernel must be linear, poly, rbf, or sigmoid."
            )

        gamma = parameters.get("gamma")
        if isinstance(gamma, (int, float)) and gamma <= 0:
            raise ModelConfigurationError("gamma must be positive.")

        if not (
            isinstance(gamma, (int, float))
            or gamma in {"scale", "auto"}
        ):
            raise ModelConfigurationError(
                "gamma must be a positive number, 'scale', or 'auto'."
            )

    elif algorithm == "decision_tree":
        if parameters.get("criterion", "gini") not in {"gini", "entropy", "log_loss"}:
            raise ModelConfigurationError("criterion must be gini, entropy, or log_loss.")
        depth = parameters.get("max_depth")
        if depth is not None and (not isinstance(depth, int) or isinstance(depth, bool) or depth <= 0):
            raise ModelConfigurationError("max_depth must be a positive integer or null.")
    elif algorithm == "random_forest":
        _validate_positive_integer(parameters, "n_estimators")

        max_depth = parameters.get("max_depth")
        if max_depth is not None and (
            not isinstance(max_depth, int)
            or isinstance(max_depth, bool)
            or max_depth <= 0
        ):
            raise ModelConfigurationError(
                "max_depth must be a positive integer or null."
            )

    elif algorithm == "logistic_regression":
        _validate_positive_number(parameters, "C")
        _validate_positive_integer(parameters, "max_iter")


def _validate_positive_number(
    parameters: dict[str, Any],
    key: str,
) -> None:
    value = parameters.get(key)

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ModelConfigurationError(
            f"{key} must be a positive number."
        )


def _validate_positive_integer(
    parameters: dict[str, Any],
    key: str,
) -> None:
    value = parameters.get(key)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ModelConfigurationError(
            f"{key} must be a positive integer."
        )


def validate_training_configuration(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and normalize training execution settings."""

    try:
        validated = TrainingConfig(**(config or {}))
    except ValidationError as exc:
        raise TrainingConfigurationError(str(exc)) from exc

    if validated.test_size + validated.validation_size >= 1:
        raise TrainingConfigurationError(
            "test_size + validation_size must be less than 1."
        )

    return validated.model_dump()
