
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite
from statistics import mean, median
from typing import Any, Mapping, Sequence

from app.modules.preprocessing.config.validator import (
    FEATURE_ORDER,
    FEATURE_TYPES,
)


class MissingValueError(ValueError):
    """Raised when missing-value processing fails."""


@dataclass(frozen=True)
class ImputationState:
    """Immutable snapshot of fitted imputation parameters."""

    strategy: str
    feature_values: dict[str, Any]
    dropped_features: tuple[str, ...]


class MissingValueProcessor:
    """
    Handle missing values using training data only.

    Supported strategies:
        mean
        median
        most_frequent
        constant
        drop

    The processor must be fitted on training data before it can
    transform training, validation, or testing data.
    """

    SUPPORTED_STRATEGIES = {
        "mean",
        "median",
        "most_frequent",
        "constant",
        "drop",
    }

    def __init__(
        self,
        strategy: str = "median",
        constant_value: Any = 0,
        constant_values: Mapping[str, Any] | None = None,
        feature_order: Sequence[str] | None = None,
    ) -> None:
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise MissingValueError(
                f"Unsupported missing-value strategy: {strategy}"
            )

        self.strategy = strategy
        self.constant_value = constant_value
        self.constant_values = dict(constant_values or {})
        self.feature_order = tuple(
            FEATURE_ORDER if feature_order is None else feature_order
        )

        self._state: ImputationState | None = None

        if not self.feature_order:
            raise MissingValueError(
                "Feature order cannot be empty."
            )

        if len(self.feature_order) != len(set(self.feature_order)):
            raise MissingValueError(
                "Feature order contains duplicate features."
            )

        unknown = set(self.feature_order) - set(FEATURE_TYPES)
        if unknown:
            raise MissingValueError(
                "Unknown features: " + ", ".join(sorted(unknown))
            )

        unknown_constants = set(self.constant_values) - set(
            self.feature_order
        )
        if unknown_constants:
            raise MissingValueError(
                "Constant values configured for unknown or "
                "unselected features: "
                + ", ".join(sorted(unknown_constants))
            )

    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() == ""

        return False

    @staticmethod
    def _numeric_values(
        feature: str,
        values: Sequence[Any],
    ) -> list[float]:
        numbers: list[float] = []

        for value in values:
            if isinstance(value, bool):
                raise MissingValueError(
                    f"{feature} contains a boolean where a number "
                    "was expected."
                )

            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise MissingValueError(
                    f"{feature} contains a non-numeric value: "
                    f"{value!r}"
                ) from exc

            if not isfinite(number):
                raise MissingValueError(
                    f"{feature} contains a non-finite number."
                )

            numbers.append(number)

        return numbers

    @staticmethod
    def _most_frequent(
        values: Sequence[Any],
        feature: str,
    ) -> Any:
        if not values:
            raise MissingValueError(
                f"Cannot calculate most frequent value for {feature}: "
                "no non-missing training values."
            )

        try:
            counts = Counter(values)
        except TypeError as exc:
            raise MissingValueError(
                f"{feature} contains unsupported unhashable values."
            ) from exc

        highest_count = max(counts.values())

        # Deterministic tie-breaking: first observed tied value wins.
        for value in values:
            if counts[value] == highest_count:
                return value

        raise MissingValueError(
            f"Could not determine imputation value for {feature}."
        )

    def _constant_for(self, feature: str) -> Any:
        """Return the configured constant for one feature."""

        if feature in self.constant_values:
            return self.constant_values[feature]

        return self.constant_value

    @staticmethod
    def _validate_constant(feature: str, value: Any) -> Any:
        """Validate a constant against the canonical feature type."""

        feature_type = FEATURE_TYPES[feature]

        if feature_type == "string":
            if not isinstance(value, str):
                raise MissingValueError(
                    f"Constant for string feature {feature} "
                    "must be a string."
                )
            return value

        if feature_type == "boolean":
            if not isinstance(value, bool):
                raise MissingValueError(
                    f"Constant for boolean feature {feature} "
                    "must be a boolean."
                )
            return value

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MissingValueError(
                f"Constant for numeric feature {feature} "
                "must be a number."
            )

        if not isfinite(float(value)):
            raise MissingValueError(
                f"Constant for {feature} must be finite."
            )

        if feature_type == "integer":
            if isinstance(value, float) and not value.is_integer():
                raise MissingValueError(
                    f"Constant for integer feature {feature} "
                    "must be a whole number."
                )
            return int(value)

        return value

    def _calculate_value(
        self,
        feature: str,
        values: Sequence[Any],
    ) -> Any:
        feature_type = FEATURE_TYPES[feature]

        if self.strategy == "constant":
            return self._validate_constant(
                feature,
                self._constant_for(feature),
            )

        if self.strategy in {"mean", "median"}:
            if feature_type != "integer":
                raise MissingValueError(
                    f"{self.strategy} imputation is supported only "
                    f"for integer features; {feature} is "
                    f"{feature_type}."
                )

            numbers = self._numeric_values(feature, values)

            if not numbers:
                raise MissingValueError(
                    f"Cannot calculate {self.strategy} for {feature}: "
                    "no non-missing training values."
                )

            result = (
                mean(numbers)
                if self.strategy == "mean"
                else median(numbers)
            )

            return int(result) if result.is_integer() else result

        if self.strategy == "most_frequent":
            return self._most_frequent(values, feature)

        raise MissingValueError(
            f"Cannot calculate imputation value for {feature} "
            f"using strategy {self.strategy}."
        )

    def _validate_rows(
        self,
        rows: Sequence[Mapping[str, Any]],
        label: str,
    ) -> None:
        if not isinstance(rows, Sequence) or isinstance(
            rows, (str, bytes)
        ):
            raise MissingValueError(
                f"{label} must be a sequence of feature rows."
            )

        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise MissingValueError(
                    f"{label} row {index} must be a mapping."
                )

            missing = set(self.feature_order) - set(row)
            if missing:
                raise MissingValueError(
                    f"{label} row {index} is missing features: "
                    + ", ".join(sorted(missing))
                )

    def fit(
        self,
        training_rows: Sequence[Mapping[str, Any]],
    ) -> "MissingValueProcessor":
        """
        Learn imputation values from training data only.

        Validation and test data must never be passed to this method.
        """

        if not training_rows:
            raise MissingValueError(
                "Training data cannot be empty."
            )

        self._validate_rows(training_rows, "Training")

        if self.strategy == "drop":
            self._state = ImputationState(
                strategy=self.strategy,
                feature_values={},
                dropped_features=(),
            )
            return self

        feature_values: dict[str, Any] = {}

        for feature in self.feature_order:
            observed = [
                row[feature]
                for row in training_rows
                if not self._is_missing(row[feature])
            ]

            missing_count = len(training_rows) - len(observed)

            if self.strategy == "constant":
                # Constants are configuration values, not learned
                # from validation or test data.
                feature_values[feature] = self._calculate_value(
                    feature, observed
                )
                continue

            if missing_count == 0:
                continue

            if self.strategy in {"mean", "median"}:
                if FEATURE_TYPES[feature] != "integer":
                    raise MissingValueError(
                        f"{self.strategy} cannot impute missing "
                        f"values in {feature} "
                        f"({FEATURE_TYPES[feature]})."
                    )

            if not observed:
                raise MissingValueError(
                    f"Cannot impute {feature}: all training values "
                    "are missing."
                )

            feature_values[feature] = self._calculate_value(
                feature, observed
            )

        self._state = ImputationState(
            strategy=self.strategy,
            feature_values=feature_values,
            dropped_features=(),
        )
        return self

    def transform(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply fitted imputation values to any dataset split."""

        if self._state is None:
            raise MissingValueError(
                "Processor must be fitted before transform."
            )

        self._validate_rows(rows, "Input")

        result: list[dict[str, Any]] = []

        for row in rows:
            transformed = deepcopy(dict(row))

            if self.strategy == "drop":
                if any(
                    self._is_missing(transformed[feature])
                    for feature in self.feature_order
                ):
                    continue
            else:
                for feature, fill_value in (
                    self._state.feature_values.items()
                ):
                    if self._is_missing(transformed[feature]):
                        transformed[feature] = fill_value

            result.append(transformed)

        return result

    def fit_transform(
        self,
        training_rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Fit on training rows and transform the training split."""

        return self.fit(training_rows).transform(training_rows)

    @property
    def state(self) -> ImputationState:
        """Return the fitted state or raise if not fitted."""

        if self._state is None:
            raise MissingValueError(
                "Processor has not been fitted."
            )

        return self._state