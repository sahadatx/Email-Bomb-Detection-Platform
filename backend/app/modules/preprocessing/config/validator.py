
from __future__ import annotations

from copy import deepcopy
from typing import Any


FEATURE_ORDER = tuple(f"F{i}" for i in range(1, 13))

FEATURE_TYPES = {
    "F1": "string",
    **{f"F{i}": "boolean" for i in range(2, 9)},
    **{f"F{i}": "integer" for i in range(9, 13)},
}

MISSING_VALUE_STRATEGIES = {
    "mean",
    "median",
    "most_frequent",
    "constant",
    "drop",
}

SCALING_STRATEGIES = {
    "none",
    "standard",
    "minmax",
}

ALLOWED_CONFIG_KEYS = {
    "feature_order",
    "missing_value_strategy",
    "missing_value_constant",
    "scaling_strategy",
    "scaling_features",
    "check_duplicates",
}


class PreprocessingConfigurationError(ValueError):
    """Raised when preprocessing configuration is invalid."""


class PreprocessingConfigValidator:
    """
    Validate and normalize Module 06 preprocessing configuration.

    Supported configuration:
        {
            "feature_order": ["F1", ..., "F12"],
            "missing_value_strategy": "median",
            "missing_value_constant": 0,
            "scaling_strategy": "standard",
            "scaling_features": ["F2", ..., "F12"],
            "check_duplicates": True
        }

    F1 is a string feature and cannot be scaled directly.
    Encoding and actual transformations belong to the engine.
    """

    @classmethod
    def validate(
        cls,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate configuration and return a normalized copy."""
        if not isinstance(config, dict):
            raise PreprocessingConfigurationError(
                "Configuration must be a JSON object."
            )

        unknown_keys = set(config) - ALLOWED_CONFIG_KEYS
        if unknown_keys:
            raise PreprocessingConfigurationError(
                "Unsupported configuration keys: "
                + ", ".join(sorted(unknown_keys))
            )

        normalized = deepcopy(config)

        normalized.setdefault(
            "feature_order",
            list(FEATURE_ORDER),
        )
        normalized.setdefault(
            "missing_value_strategy",
            "median",
        )
        normalized.setdefault(
            "scaling_strategy",
            "standard",
        )
        normalized.setdefault(
            "check_duplicates",
            True,
        )

        cls._validate_feature_order(normalized["feature_order"])
        cls._validate_missing_value_strategy(normalized)
        cls._validate_scaling(normalized)
        cls._validate_duplicate_check(normalized)

        return normalized

    @staticmethod
    def _validate_feature_order(value: Any) -> None:
        if not isinstance(value, list) or not value:
            raise PreprocessingConfigurationError(
                "feature_order must be a non-empty list."
            )

        if any(not isinstance(item, str) for item in value):
            raise PreprocessingConfigurationError(
                "Every feature name must be a string."
            )

        if len(value) != len(set(value)):
            raise PreprocessingConfigurationError(
                "feature_order contains duplicate features."
            )

        unknown = set(value) - set(FEATURE_ORDER)
        if unknown:
            raise PreprocessingConfigurationError(
                "Unknown features: " + ", ".join(sorted(unknown))
            )

        expected_order = [
            feature for feature in FEATURE_ORDER if feature in value
        ]
        if value != expected_order:
            raise PreprocessingConfigurationError(
                "feature_order must follow canonical F1-F12 order."
            )

    @staticmethod
    def _validate_missing_value_strategy(
        config: dict[str, Any],
    ) -> None:
        strategy = config["missing_value_strategy"]

        if strategy not in MISSING_VALUE_STRATEGIES:
            raise PreprocessingConfigurationError(
                "Unsupported missing_value_strategy. Supported: "
                + ", ".join(sorted(MISSING_VALUE_STRATEGIES))
            )

        if strategy == "constant":
            if "missing_value_constant" not in config:
                raise PreprocessingConfigurationError(
                    "missing_value_constant is required "
                    "when strategy is 'constant'."
                )
            if config["missing_value_constant"] is None:
                raise PreprocessingConfigurationError(
                    "missing_value_constant cannot be null "
                    "when strategy is 'constant'."
                )
        elif config.get("missing_value_constant") is not None:
            raise PreprocessingConfigurationError(
                "missing_value_constant is only allowed "
                "when strategy is 'constant'."
            )

        if strategy in {"mean", "median"}:
            # Mean and median require numeric data.
            # F1 is a string and must not be included.
            pass

    @staticmethod
    def _validate_scaling(
        config: dict[str, Any],
    ) -> None:
        strategy = config["scaling_strategy"]

        if strategy not in SCALING_STRATEGIES:
            raise PreprocessingConfigurationError(
                "Unsupported scaling_strategy. Supported: "
                + ", ".join(sorted(SCALING_STRATEGIES))
            )

        features = config.get("scaling_features")

        if features is None:
            features = [
                feature
                for feature in config["feature_order"]
                if FEATURE_TYPES[feature] != "string"
            ]
            config["scaling_features"] = features

        if not isinstance(features, list):
            raise PreprocessingConfigurationError(
                "scaling_features must be a list."
            )

        if any(not isinstance(item, str) for item in features):
            raise PreprocessingConfigurationError(
                "Every scaling feature must be a string."
            )

        if len(features) != len(set(features)):
            raise PreprocessingConfigurationError(
                "scaling_features contains duplicates."
            )

        selected = set(config["feature_order"])
        for feature in features:
            if feature not in FEATURE_ORDER:
                raise PreprocessingConfigurationError(
                    f"Unknown scaling feature: {feature}"
                )

            if feature not in selected:
                raise PreprocessingConfigurationError(
                    f"{feature} is not included in feature_order."
                )

            if FEATURE_TYPES[feature] == "string":
                raise PreprocessingConfigurationError(
                    f"{feature} is a string feature and cannot "
                    "be scaled directly. Configure encoding "
                    "in a future categorical-processing step."
                )

        if strategy == "none" and features:
            raise PreprocessingConfigurationError(
                "scaling_features must be empty when "
                "scaling_strategy is 'none'."
            )

    @staticmethod
    def _validate_duplicate_check(
        config: dict[str, Any],
    ) -> None:
        if not isinstance(config["check_duplicates"], bool):
            raise PreprocessingConfigurationError(
                "check_duplicates must be a boolean."
            )