
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any, Mapping, Sequence

from app.modules.preprocessing.config.validator import (
    FEATURE_ORDER,
    FEATURE_TYPES,
)


class ScalingError(ValueError):
    """Raised when feature scaling fails."""


@dataclass(frozen=True)
class FeatureScalingState:
    """Fitted scaling parameters for a single feature."""

    strategy: str
    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    scale: float | None = None


@dataclass(frozen=True)
class ScalerState:
    """Immutable snapshot of fitted scaling parameters."""

    strategy: str
    feature_order: tuple[str, ...]
    feature_states: dict[str, FeatureScalingState]


class FeatureScaler:
    """
    Scale numeric features using training data only.

    Supported strategies:
        none
        standard
        minmax

    Standard scaling:
        (value - training_mean) / training_standard_deviation

    Min-max scaling:
        (value - training_minimum) /
        (training_maximum - training_minimum)

    Constant features are transformed to 0.0 for standard and
    min-max scaling. The learned parameters are reused unchanged
    for validation and test data.
    """

    SUPPORTED_STRATEGIES = {"none", "standard", "minmax"}

    def __init__(
        self,
        strategy: str = "standard",
        scaling_features: Sequence[str] | None = None,
        feature_order: Sequence[str] | None = None,
    ) -> None:
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ScalingError(
                f"Unsupported scaling strategy: {strategy}"
            )

        self.strategy = strategy
        self.feature_order = tuple(
            FEATURE_ORDER if feature_order is None else feature_order
        )

        if len(self.feature_order) != len(set(self.feature_order)):
            raise ScalingError(
                "Feature order contains duplicate features."
            )

        unknown = set(self.feature_order) - set(FEATURE_TYPES)
        if unknown:
            raise ScalingError(
                "Unknown features: " + ", ".join(sorted(unknown))
            )

        if scaling_features is None:
            scaling_features = (
                ()
                if strategy == "none"
                else tuple(
                    feature
                    for feature in self.feature_order
                    if FEATURE_TYPES[feature] in {"boolean", "integer"}
                )
            )

        self.scaling_features = tuple(scaling_features)

        if len(self.scaling_features) != len(
            set(self.scaling_features)
        ):
            raise ScalingError(
                "Scaling feature list contains duplicates."
            )

        unknown_scaling = (
            set(self.scaling_features) - set(self.feature_order)
        )
        if unknown_scaling:
            raise ScalingError(
                "Scaling features are not in the selected feature order: "
                + ", ".join(sorted(unknown_scaling))
            )

        non_numeric = [
            feature
            for feature in self.scaling_features
            if FEATURE_TYPES[feature] not in {"boolean", "integer"}
        ]
        if non_numeric:
            raise ScalingError(
                "Cannot scale non-numeric features: "
                + ", ".join(non_numeric)
            )

        if strategy == "none" and self.scaling_features:
            raise ScalingError(
                "Scaling features must be empty when strategy is 'none'."
            )

        self._state: ScalerState | None = None

    @staticmethod
    def _to_number(feature: str, value: Any) -> float:
        """Convert a supported numeric feature value to float."""

        if isinstance(value, bool):
            number = float(value)
        elif isinstance(value, (int, float)):
            number = float(value)
        else:
            raise ScalingError(
                f"{feature} contains a non-numeric value: {value!r}"
            )

        if not isfinite(number):
            raise ScalingError(
                f"{feature} contains a non-finite value."
            )

        return number

    def _validate_rows(
        self,
        rows: Sequence[Mapping[str, Any]],
        label: str,
    ) -> None:
        if not isinstance(rows, Sequence) or isinstance(
            rows, (str, bytes)
        ):
            raise ScalingError(
                f"{label} must be a sequence of feature rows."
            )

        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ScalingError(
                    f"{label} row {index} must be a mapping."
                )

            missing = set(self.feature_order) - set(row)
            if missing:
                raise ScalingError(
                    f"{label} row {index} is missing features: "
                    + ", ".join(sorted(missing))
                )

            for feature in self.scaling_features:
                self._to_number(feature, row[feature])

    @staticmethod
    def _fit_standard(values: Sequence[float]) -> FeatureScalingState:
        if not values:
            raise ScalingError(
                "Cannot fit standard scaling on empty data."
            )

        feature_mean = sum(values) / len(values)

        # Population standard deviation (ddof=0).
        variance = sum(
            (value - feature_mean) ** 2 for value in values
        ) / len(values)

        standard_deviation = sqrt(variance)

        return FeatureScalingState(
            strategy="standard",
            mean=feature_mean,
            scale=standard_deviation,
        )

    @staticmethod
    def _fit_minmax(values: Sequence[float]) -> FeatureScalingState:
        if not values:
            raise ScalingError(
                "Cannot fit min-max scaling on empty data."
            )

        return FeatureScalingState(
            strategy="minmax",
            minimum=min(values),
            maximum=max(values),
        )

    def fit(
        self,
        training_rows: Sequence[Mapping[str, Any]],
    ) -> "FeatureScaler":
        """Learn scaling parameters exclusively from training data."""

        if not training_rows:
            raise ScalingError(
                "Training data cannot be empty."
            )

        self._validate_rows(training_rows, "Training")

        feature_states: dict[str, FeatureScalingState] = {}

        for feature in self.scaling_features:
            values = [
                self._to_number(feature, row[feature])
                for row in training_rows
            ]

            if self.strategy == "standard":
                feature_states[feature] = self._fit_standard(values)
            elif self.strategy == "minmax":
                feature_states[feature] = self._fit_minmax(values)

        self._state = ScalerState(
            strategy=self.strategy,
            feature_order=self.feature_order,
            feature_states=feature_states,
        )

        return self

    def transform(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply fitted parameters without refitting."""

        if self._state is None:
            raise ScalingError(
                "Scaler must be fitted before transform."
            )

        self._validate_rows(rows, "Input")

        result: list[dict[str, Any]] = []

        for row in rows:
            transformed = dict(row)

            if self.strategy == "none":
                result.append(transformed)
                continue

            for feature, state in self._state.feature_states.items():
                value = self._to_number(feature, row[feature])

                if self.strategy == "standard":
                    if state.scale is None or state.mean is None:
                        raise ScalingError(
                            f"Missing standard scaling parameters for {feature}."
                        )

                    if state.scale == 0:
                        scaled = 0.0
                    else:
                        scaled = (value - state.mean) / state.scale

                elif self.strategy == "minmax":
                    if state.minimum is None or state.maximum is None:
                        raise ScalingError(
                            f"Missing min-max parameters for {feature}."
                        )

                    feature_range = state.maximum - state.minimum

                    if feature_range == 0:
                        scaled = 0.0
                    else:
                        scaled = (
                            (value - state.minimum) / feature_range
                        )

                else:
                    raise ScalingError(
                        f"Unsupported fitted strategy: {self.strategy}"
                    )

                if not isfinite(scaled):
                    raise ScalingError(
                        f"Scaling produced a non-finite value for {feature}."
                    )

                transformed[feature] = scaled

            result.append(transformed)

        return result

    def fit_transform(
        self,
        training_rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Fit on training rows and transform the training split."""

        return self.fit(training_rows).transform(training_rows)

    @property
    def state(self) -> ScalerState:
        """Return fitted parameters or raise if not fitted."""

        if self._state is None:
            raise ScalingError(
                "Scaler has not been fitted."
            )

        return self._state