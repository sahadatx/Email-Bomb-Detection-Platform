
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.modules.preprocessing.config.validator import (
    FEATURE_ORDER,
    FEATURE_TYPES,
)


class SchemaValidationError(ValueError):
    """Raised when a dataset feature schema is incompatible."""


@dataclass(frozen=True)
class SchemaValidationResult:
    """Immutable result of a successful schema validation."""

    feature_order: tuple[str, ...]
    feature_types: dict[str, str]

    @property
    def feature_count(self) -> int:
        return len(self.feature_order)


class FeatureSchemaValidator:
    """Validate dataset feature schemas against canonical definitions."""

    @staticmethod
    def _normalize_type(value: Any) -> str:
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"Feature type must be a string, got {type(value).__name__}."
            )

        normalized = value.strip().lower()

        aliases = {
            "str": "string",
            "text": "string",
            "bool": "boolean",
            "int": "integer",
            "int32": "integer",
            "int64": "integer",
        }

        return aliases.get(normalized, normalized)

    @classmethod
    def validate(
        cls,
        schema: Mapping[str, Any],
        expected_features: Sequence[str] | None = None,
    ) -> SchemaValidationResult:
        """
        Validate a schema represented as {feature_name: feature_type}.

        Example:
            {
                "F1": "string",
                "F2": "boolean",
                ...
            }
        """
        if not isinstance(schema, Mapping):
            raise SchemaValidationError(
                "Feature schema must be a mapping of feature names to types."
            )

        if not schema:
            raise SchemaValidationError("Feature schema cannot be empty.")

        expected = tuple(expected_features or FEATURE_ORDER)

        if not expected:
            raise SchemaValidationError(
                "Expected feature list cannot be empty."
            )

        if len(expected) != len(set(expected)):
            raise SchemaValidationError(
                "Expected feature list contains duplicates."
            )

        unknown_expected = set(expected) - set(FEATURE_TYPES)
        if unknown_expected:
            raise SchemaValidationError(
                "Unknown expected features: "
                + ", ".join(sorted(unknown_expected))
            )

        actual_names = list(schema.keys())

        if any(not isinstance(name, str) for name in actual_names):
            raise SchemaValidationError(
                "All feature names must be strings."
            )

        actual_set = set(actual_names)
        expected_set = set(expected)

        missing = expected_set - actual_set
        unexpected = actual_set - expected_set

        if missing:
            raise SchemaValidationError(
                "Missing required features: "
                + ", ".join(sorted(missing))
            )

        if unexpected:
            raise SchemaValidationError(
                "Unexpected features: "
                + ", ".join(sorted(unexpected))
            )

        normalized_types: dict[str, str] = {}

        for feature in expected:
            actual_type = cls._normalize_type(schema[feature])
            expected_type = FEATURE_TYPES[feature]

            if actual_type != expected_type:
                raise SchemaValidationError(
                    f"{feature} has type '{actual_type}', "
                    f"but expected '{expected_type}'."
                )

            normalized_types[feature] = actual_type

        return SchemaValidationResult(
            feature_order=expected,
            feature_types=normalized_types,
        )