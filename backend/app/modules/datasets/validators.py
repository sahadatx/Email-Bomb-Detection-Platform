
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
from uuid import UUID


# ============================================================
# CONSTANTS
# ============================================================

TOTAL_FEATURES = 12
DEFAULT_FEATURE_SCHEMA_NAME = "F1-F12"

EXPECTED_FEATURE_IDS = tuple(
    f"F{i}" for i in range(1, TOTAL_FEATURES + 1)
)

VALID_GROUND_TRUTHS = frozenset({"normal", "bombing"})
VALID_SPLITS = frozenset({"train", "validation", "test"})

FEATURE_FIELD_MAP = {
    "F1": "f1_sender_email",
    "F2": "f2_known_domain",
    "F3": "f3_message_id",
    "F4": "f4_auto_submitted",
    "F5": "f5_precedence_bulk",
    "F6": "f6_list_id",
    "F7": "f7_x_beenthere",
    "F8": "f8_x_anti_abuse",
    "F9": "f9_keyword_features",
    "F10": "f10_subject_length",
    "F11": "f11_emails_per_minute",
    "F12": "f12_emails_per_hour",
}

BOOLEAN_FEATURE_IDS = frozenset({
    "F2", "F3", "F4", "F5", "F6", "F7", "F8",
})

INTEGER_FEATURE_IDS = frozenset({
    "F9", "F10", "F11", "F12",
})

NON_NEGATIVE_FEATURE_IDS = INTEGER_FEATURE_IDS

CHECK_MISSING_FEATURE_VALUES = "MISSING_FEATURE_VALUES"
CHECK_LABEL_CONSISTENCY = "LABEL_CONSISTENCY"
CHECK_DUPLICATE_SAMPLES = "DUPLICATE_SAMPLES"
CHECK_FEATURE_SCHEMA = "FEATURE_SCHEMA"
CHECK_CLASS_DISTRIBUTION = "CLASS_DISTRIBUTION"
CHECK_INVALID_FEATURE_VALUES = "INVALID_FEATURE_VALUES"
CHECK_SPLIT_CONSISTENCY = "SPLIT_CONSISTENCY"
CHECK_VERSION_INTEGRITY = "VERSION_INTEGRITY"

VALIDATION_CHECK_CODES = (
    CHECK_MISSING_FEATURE_VALUES,
    CHECK_LABEL_CONSISTENCY,
    CHECK_DUPLICATE_SAMPLES,
    CHECK_FEATURE_SCHEMA,
    CHECK_CLASS_DISTRIBUTION,
    CHECK_INVALID_FEATURE_VALUES,
    CHECK_SPLIT_CONSISTENCY,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class DatasetValidationError(ValueError):
    """Raised when a Dataset validation contract fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "dataset_validation_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


# ============================================================
# VALIDATION RESULT
# ============================================================

@dataclass(slots=True)
class ValidationResult:
    """Container for validation errors, warnings, and details."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.valid and not self.errors

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def status(self) -> str:
        if self.errors or not self.valid:
            return "failed"
        if self.warnings:
            return "warning"
        return "passed"

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> ValidationResult:
        if not other.valid or other.errors:
            self.valid = False

        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.details.update(other.details)
        return self


# ============================================================
# GENERIC HELPERS
# ============================================================

def _get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    """Read a field from an object or mapping."""
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _materialize_iterable(
    value: Iterable[Any] | None,
) -> tuple[list[Any] | None, str | None]:
    """Convert an iterable to a list exactly once."""
    if value is None:
        return None, "A value is required."

    if isinstance(value, (str, bytes, Mapping)):
        return None, "A collection is required."

    try:
        return list(value), None
    except (TypeError, ValueError):
        return None, "The value must be an iterable collection."


def _is_non_negative_integer(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def _feature_value(features: Any, feature_id: str) -> Any:
    """Read a feature by canonical ID or model field name."""
    field_name = FEATURE_FIELD_MAP[feature_id]

    value = _get_value(features, feature_id, None)
    if value is not None:
        return value

    return _get_value(features, field_name, None)


def _email_id(record: Any) -> Any:
    return _get_value(record, "email_id")


def _record_id(record: Any) -> str | None:
    value = _email_id(record)
    if value is None:
        value = _get_value(record, "id")
    return str(value) if value is not None else None


def _record_features(record: Any) -> Any:
    """Accept either an EmailFeatures record or a wrapper."""
    features = _get_value(record, "features")
    if features is not None:
        return features
    return record


def _record_label(record: Any) -> Any:
    return _enum_value(_get_value(record, "ground_truth"))


def _record_split(record: Any) -> Any:
    return _enum_value(_get_value(record, "split"))


def ensure_valid(
    result: ValidationResult,
    *,
    message: str = "Dataset validation failed.",
) -> None:
    if result.passed:
        return

    raise DatasetValidationError(
        message,
        details={
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            **result.details,
        },
    )


def validate_or_raise(
    result: ValidationResult,
    *,
    message: str = "Dataset validation failed.",
) -> ValidationResult:
    ensure_valid(result, message=message)
    return result


# ============================================================
# FEATURE SCHEMA VALIDATION
# ============================================================

def validate_feature_schema(
    feature_schema: Any,
) -> ValidationResult:
    """
    Validate Dataset feature schema metadata.

    Empty feature definitions are allowed during schema
    construction. If definitions exist, they must contain
    F1-F12 in canonical order.
    """
    result = ValidationResult()

    if feature_schema is None:
        result.add_error("Feature schema is required.")
        return result

    feature_count = _get_value(feature_schema, "feature_count")

    if isinstance(feature_count, bool) or not isinstance(
        feature_count, int
    ):
        result.add_error(
            "Feature schema feature_count must be an integer."
        )
    elif feature_count != TOTAL_FEATURES:
        result.add_error(
            "Dataset feature schema must declare exactly 12 features."
        )

    features = _get_value(feature_schema, "features")

    if features is None:
        result.add_error(
            "Dataset feature definitions are missing."
        )
        return result

    if not isinstance(features, (list, tuple)):
        result.add_error(
            "Dataset feature definitions must be a list or tuple."
        )
        return result

    if not features:
        return result

    if len(features) != TOTAL_FEATURES:
        result.add_error(
            "Dataset feature schema must contain exactly F1-F12."
        )
        return result

    actual_ids = [
        _get_value(feature, "feature_id")
        for feature in features
    ]

    if tuple(actual_ids) != EXPECTED_FEATURE_IDS:
        result.add_error(
            "Dataset feature schema must contain F1-F12 "
            "in canonical order."
        )

    result.details.update({
        "expected_feature_ids": list(EXPECTED_FEATURE_IDS),
        "actual_feature_ids": actual_ids,
        "feature_count": feature_count,
    })

    return result


def ensure_valid_feature_schema(feature_schema: Any) -> None:
    ensure_valid(
        validate_feature_schema(feature_schema),
        message="Invalid Dataset feature schema.",
    )


# ============================================================
# EMAIL ID VALIDATION
# ============================================================

def validate_email_ids(
    email_ids: Iterable[UUID] | None,
) -> ValidationResult:
    """Validate a non-empty collection of unique UUID values."""
    result = ValidationResult()
    ids, error = _materialize_iterable(email_ids)

    if error:
        result.add_error(
            "Email IDs are required and must be an iterable "
            "of UUID values."
        )
        return result

    assert ids is not None

    if not ids:
        result.add_error("At least one email must be selected.")
        return result

    invalid_ids = [
        value for value in ids if not isinstance(value, UUID)
    ]

    if invalid_ids:
        result.add_error(
            "All email IDs must be valid UUID values."
        )

    valid_ids = [
        value for value in ids if isinstance(value, UUID)
    ]

    if len(valid_ids) != len(set(valid_ids)):
        result.add_error(
            "Duplicate email IDs are not allowed."
        )

    return result


# ============================================================
# DATASET CREATE REQUEST VALIDATION
# ============================================================

def validate_dataset_create_request(
    request: Any,
) -> ValidationResult:
    """Validate fields required to create a Dataset."""
    result = ValidationResult()

    if request is None:
        result.add_error(
            "Dataset creation request is required."
        )
        return result

    name = _get_value(request, "name")

    if not isinstance(name, str):
        result.add_error("Dataset name must be a string.")
    elif not name.strip():
        result.add_error("Dataset name cannot be empty.")

    result.merge(
        validate_email_ids(_get_value(request, "email_ids"))
    )
    result.merge(
        validate_feature_schema(
            _get_value(request, "feature_schema")
        )
    )

    return result


def ensure_valid_dataset_create_request(request: Any) -> None:
    ensure_valid(
        validate_dataset_create_request(request),
        message="Invalid Dataset creation request.",
    )


# ============================================================
# SPLIT CONFIGURATION VALIDATION
# ============================================================

def validate_split_configuration(
    split: Any,
) -> ValidationResult:
    """Validate train/validation/test split percentages."""
    result = ValidationResult()

    if split is None:
        result.add_error("Split configuration is required.")
        return result

    fields = {
        "training_percentage": _get_value(
            split, "training_percentage"
        ),
        "validation_percentage": _get_value(
            split, "validation_percentage"
        ),
        "testing_percentage": _get_value(
            split, "testing_percentage"
        ),
    }

    percentages_valid = True

    for name, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, int):
            result.add_error(f"{name} must be an integer.")
            percentages_valid = False
            continue

        if not 0 <= value <= 100:
            result.add_error(
                f"{name} must be between 0 and 100."
            )
            percentages_valid = False

    if percentages_valid and sum(fields.values()) != 100:
        result.add_error(
            "Training, validation, and testing percentages "
            "must sum to exactly 100%."
        )

    random_seed = _get_value(split, "random_seed")

    if random_seed is not None:
        if isinstance(random_seed, bool) or not isinstance(
            random_seed, int
        ):
            result.add_error("Random seed must be an integer.")
        elif random_seed < 0:
            result.add_error("Random seed cannot be negative.")

    stratified = _get_value(split, "stratified", True)

    if not isinstance(stratified, bool):
        result.add_error(
            "Stratified must be a boolean value."
        )

    return result


def ensure_valid_split_configuration(split: Any) -> None:
    ensure_valid(
        validate_split_configuration(split),
        message="Invalid Dataset split configuration.",
    )


# ============================================================
# DATASET VERSION REQUEST VALIDATION
# ============================================================

def validate_dataset_version_request(
    request: Any,
) -> ValidationResult:
    """Validate a Dataset Version creation request."""
    result = ValidationResult()

    if request is None:
        result.add_error("Dataset Version request is required.")
        return result

    dataset_id = _get_value(request, "dataset_id")

    if not isinstance(dataset_id, UUID):
        result.add_error("dataset_id must be a valid UUID.")

    name = _get_value(request, "name")

    if not isinstance(name, str):
        result.add_error(
            "Dataset Version name must be a string."
        )
    elif not name.strip():
        result.add_error(
            "Dataset Version name cannot be empty."
        )

    result.merge(
        validate_split_configuration(
            _get_value(request, "split")
        )
    )

    return result


def ensure_valid_dataset_version_request(request: Any) -> None:
    ensure_valid(
        validate_dataset_version_request(request),
        message="Invalid Dataset Version request.",
    )


# ============================================================
# SELECTED EMAIL ELIGIBILITY
# ============================================================

def validate_selected_email_ids(
    selected_email_ids: Iterable[UUID] | None,
    eligible_email_ids: Iterable[UUID] | None,
) -> ValidationResult:
    """Ensure selected IDs are valid and eligible."""
    result = ValidationResult()

    selected, selected_error = _materialize_iterable(
        selected_email_ids
    )

    if selected_error:
        result.add_error(
            "Email IDs are required and must be iterable."
        )
        return result

    assert selected is not None
    result.merge(validate_email_ids(selected))

    if not result.passed:
        return result

    eligible, eligible_error = _materialize_iterable(
        eligible_email_ids
    )

    if eligible_error:
        result.add_error("Eligible email IDs are required.")
        return result

    assert eligible is not None

    invalid_eligible = [
        value for value in eligible if not isinstance(value, UUID)
    ]

    if invalid_eligible:
        result.add_error(
            "Eligible email IDs contain invalid UUID values."
        )
        return result

    ineligible = set(selected) - set(eligible)

    if ineligible:
        result.add_error(
            "One or more selected emails are not Dataset-eligible."
        )
        result.details["ineligible_email_ids"] = sorted(
            str(email_id) for email_id in ineligible
        )

    return result


def ensure_valid_selected_email_ids(
    selected_email_ids: Iterable[UUID] | None,
    eligible_email_ids: Iterable[UUID] | None,
) -> None:
    ensure_valid(
        validate_selected_email_ids(
            selected_email_ids,
            eligible_email_ids,
        ),
        message="Selected emails failed eligibility validation.",
    )


# ============================================================
# MEMBERSHIP VALIDATION
# ============================================================

def validate_memberships(
    memberships: Iterable[Any] | None,
) -> ValidationResult:
    """Validate membership IDs, splits, and ground-truth labels."""
    result = ValidationResult()
    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert items is not None
    seen_email_ids: set[UUID] = set()

    for index, membership in enumerate(items):
        email_id = _get_value(membership, "email_id")
        split = _enum_value(_get_value(membership, "split"))
        ground_truth = _enum_value(
            _get_value(membership, "ground_truth")
        )

        if not isinstance(email_id, UUID):
            result.add_error(
                f"Membership at index {index} must contain "
                "a valid email UUID."
            )
        elif email_id in seen_email_ids:
            result.add_error(
                "An email cannot appear more than once "
                "in the same Dataset Version."
            )
        else:
            seen_email_ids.add(email_id)

        if split not in VALID_SPLITS:
            result.add_error(
                f"Invalid Dataset split at membership "
                f"{index}: {split!r}."
            )

        if ground_truth not in VALID_GROUND_TRUTHS:
            result.add_error(
                f"Invalid ground-truth label at membership "
                f"{index}: {ground_truth!r}."
            )

    return result


def ensure_valid_memberships(
    memberships: Iterable[Any] | None,
) -> None:
    ensure_valid(
        validate_memberships(memberships),
        message="Invalid Dataset Version memberships.",
    )


# ============================================================
# SPLIT COUNT VALIDATION
# ============================================================

def validate_split_counts(
    split_counts: Any,
    expected_total: int,
) -> ValidationResult:
    """Validate split counts and their total."""
    result = ValidationResult()

    if split_counts is None:
        result.add_error("Split counts are required.")
        return result

    values = {
        name: _get_value(split_counts, name)
        for name in ("training", "validation", "testing", "total")
    }

    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int):
            result.add_error(
                f"Split count '{name}' must be an integer."
            )
        elif value < 0:
            result.add_error(
                f"Split count '{name}' cannot be negative."
            )

    if result.errors:
        return result

    calculated_total = (
        values["training"]
        + values["validation"]
        + values["testing"]
    )

    if calculated_total != values["total"]:
        result.add_error(
            "Split counts do not add up to the reported total."
        )

    if not _is_non_negative_integer(expected_total):
        result.add_error(
            "Expected split total must be a non-negative integer."
        )
    elif values["total"] != expected_total:
        result.add_error(
            "Split total does not match the Dataset Version "
            "sample count."
        )

    return result


# ============================================================
# GROUND-TRUTH DISTRIBUTION
# ============================================================

def validate_ground_truth_distribution(
    normal_count: int,
    bombing_count: int,
    *,
    require_both_classes: bool = False,
) -> ValidationResult:
    """Validate Normal and Bombing sample counts."""
    result = ValidationResult()

    counts = {
        "normal_count": normal_count,
        "bombing_count": bombing_count,
    }

    for name, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int):
            result.add_error(f"{name} must be an integer.")
        elif value < 0:
            result.add_error(f"{name} cannot be negative.")

    if result.errors:
        return result

    total = normal_count + bombing_count

    if total == 0:
        result.add_error(
            "Dataset must contain at least one sample."
        )

    if require_both_classes:
        if normal_count == 0:
            result.add_error(
                "Dataset must contain at least one normal sample."
            )
        if bombing_count == 0:
            result.add_error(
                "Dataset must contain at least one bombing sample."
            )

    result.details.update({
        "normal_count": normal_count,
        "bombing_count": bombing_count,
        "total_samples": total,
        "normal_percentage": (
            normal_count / total * 100 if total else 0.0
        ),
        "bombing_percentage": (
            bombing_count / total * 100 if total else 0.0
        ),
    })

    return result


# ============================================================
# DATASET COUNTER VALIDATION
# ============================================================

def validate_dataset_counters(
    sample_count: int,
    normal_count: int,
    bombing_count: int,
) -> ValidationResult:
    """Ensure aggregate class counts match the sample count."""
    result = ValidationResult()

    values = {
        "sample_count": sample_count,
        "normal_count": normal_count,
        "bombing_count": bombing_count,
    }

    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int):
            result.add_error(f"{name} must be an integer.")
        elif value < 0:
            result.add_error(f"{name} cannot be negative.")

    if result.errors:
        return result

    if normal_count + bombing_count != sample_count:
        result.add_error(
            "Normal and bombing counts must equal "
            "the Dataset sample count."
        )

    return result


def ensure_valid_dataset_counters(
    sample_count: int,
    normal_count: int,
    bombing_count: int,
) -> None:
    ensure_valid(
        validate_dataset_counters(
            sample_count,
            normal_count,
            bombing_count,
        ),
        message="Invalid Dataset counters.",
    )


# ============================================================
# CHECK 1: MISSING FEATURE VALUES
# ============================================================

def validate_missing_feature_values(
    records: Iterable[Any] | None,
) -> ValidationResult:
    """
    Check whether required F1-F12 values are missing.

    F1 is nullable in the current feature schema and is
    therefore treated as missing when it is None or blank.
    F2-F12 must be present.
    """
    result = ValidationResult()
    items, error = _materialize_iterable(records)

    if error:
        result.add_error(
            "Feature records are required and must be iterable."
        )
        return result

    assert items is not None
    affected: list[dict[str, Any]] = []
    missing_counts = Counter()

    for record in items:
        features = _record_features(record)
        missing: list[str] = []

        for feature_id in EXPECTED_FEATURE_IDS:
            value = _feature_value(features, feature_id)

            if value is None:
                missing.append(feature_id)
            elif feature_id == "F1" and (
                isinstance(value, str) and not value.strip()
            ):
                missing.append(feature_id)

        if missing:
            affected.append({
                "email_id": _record_id(record),
                "missing_features": missing,
            })
            missing_counts.update(missing)

    if affected:
        result.add_error(
            f"Missing feature values detected in "
            f"{len(affected)} record(s)."
        )

    result.details.update({
        "total_records": len(items),
        "affected_count": len(affected),
        "missing_value_count": sum(missing_counts.values()),
        "missing_counts_by_feature": dict(missing_counts),
        "affected_records": affected,
    })

    return result


# ============================================================
# CHECK 2: LABEL CONSISTENCY
# ============================================================

def validate_label_consistency(
    memberships: Iterable[Any] | None,
) -> ValidationResult:
    """Ensure each membership has a supported ground-truth label."""
    result = ValidationResult()
    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert items is not None
    affected: list[dict[str, Any]] = []
    label_counts = Counter()

    for index, membership in enumerate(items):
        label = _record_label(membership)
        label_counts[str(label)] += 1

        if label not in VALID_GROUND_TRUTHS:
            affected.append({
                "email_id": _record_id(membership),
                "index": index,
                "ground_truth": str(label),
            })

    if affected:
        result.add_error(
            f"Invalid ground-truth labels found in "
            f"{len(affected)} membership record(s)."
        )

    result.details.update({
        "total_records": len(items),
        "valid_labels": sorted(VALID_GROUND_TRUTHS),
        "label_counts": dict(label_counts),
        "affected_count": len(affected),
        "affected_records": affected,
    })

    return result


# ============================================================
# CHECK 3: DUPLICATE SAMPLES
# ============================================================

def validate_duplicate_samples(
    memberships: Iterable[Any] | None,
) -> ValidationResult:
    """
    Detect duplicate email membership IDs within a version.

    This checks duplicate membership, not identical email
    content or semantically similar messages.
    """
    result = ValidationResult()
    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert items is not None
    positions: dict[Any, list[int]] = {}

    for index, membership in enumerate(items):
        email_id = _email_id(membership)

        if email_id is not None:
            positions.setdefault(email_id, []).append(index)

    duplicates = [
        {
            "email_id": str(email_id),
            "occurrences": len(indices),
            "indexes": indices,
        }
        for email_id, indices in positions.items()
        if len(indices) > 1
    ]

    if duplicates:
        result.add_warning(
            f"Duplicate membership detected for "
            f"{len(duplicates)} email ID(s)."
        )

    result.details.update({
        "total_records": len(items),
        "duplicate_email_count": len(duplicates),
        "duplicate_occurrence_count": sum(
            item["occurrences"] - 1 for item in duplicates
        ),
        "affected_count": len(duplicates),
        "affected_records": duplicates,
    })

    return result


# ============================================================
# CHECK 4: FEATURE SCHEMA COMPATIBILITY
# ============================================================

def validate_feature_schema_compatibility(
    feature_schema: Any,
    memberships: Iterable[Any] | None = None,
) -> ValidationResult:
    """
    Validate schema metadata and membership schema identifiers.

    Membership.feature_schema_version stores the schema name,
    such as F1-F12, rather than the semantic schema version,
    such as 1.0.

    Older snapshots may not contain a schema name. In that
    case, use the established default schema name rather than
    the semantic version.
    """
    result = validate_feature_schema(feature_schema)

    if memberships is None:
        return result

    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required for schema "
            "compatibility validation."
        )
        return result

    assert items is not None

    schema_name = _get_value(feature_schema, "name")
    schema_version = _get_value(
        feature_schema,
        "version",
        _get_value(feature_schema, "schema_version"),
    )

    # Membership.feature_schema_version stores the schema name.
    # Older snapshots may omit name, so use the canonical default.
    expected_identifier = (
        schema_name.strip()
        if isinstance(schema_name, str) and schema_name.strip()
        else DEFAULT_FEATURE_SCHEMA_NAME
    )

    mismatches: list[dict[str, Any]] = []

    for membership in items:
        actual_identifier = _get_value(
            membership,
            "feature_schema_version",
        )

        if actual_identifier != expected_identifier:
            mismatches.append({
                "email_id": _record_id(membership),
                "expected_schema_identifier": str(
                    expected_identifier
                ),
                "actual_schema_identifier": (
                    str(actual_identifier)
                    if actual_identifier is not None
                    else None
                ),
            })

    if mismatches:
        result.add_error(
            "Feature schema identifier mismatch in "
            f"{len(mismatches)} membership record(s)."
        )

    result.details.update({
        "expected_schema_name": (
            str(schema_name) if schema_name is not None else None
        ),
        "expected_schema_version": (
            str(schema_version)
            if schema_version is not None
            else None
        ),
        "expected_schema_identifier": str(expected_identifier),
        "schema_identifier_mismatch_count": len(mismatches),
        "schema_version_mismatch_count": len(mismatches),
        "affected_count": len(mismatches),
        "affected_records": mismatches,
    })

    return result


# ============================================================
# CHECK 5: CLASS DISTRIBUTION
# ============================================================

def validate_class_distribution(
    memberships: Iterable[Any] | None,
    *,
    imbalance_threshold: float | None = None,
) -> ValidationResult:
    """
    Calculate class distribution and optionally flag imbalance.

    No threshold is assumed. If a backend policy supplies a
    threshold, a warning is raised when the minority class
    percentage is below it.
    """
    result = ValidationResult()
    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert items is not None

    normal_count = 0
    bombing_count = 0
    invalid_labels: list[dict[str, Any]] = []

    for membership in items:
        label = _record_label(membership)

        if label == "normal":
            normal_count += 1
        elif label == "bombing":
            bombing_count += 1
        else:
            invalid_labels.append({
                "email_id": _record_id(membership),
                "ground_truth": str(label),
            })

    total = normal_count + bombing_count
    normal_percentage = (
        normal_count / total * 100 if total else 0.0
    )
    bombing_percentage = (
        bombing_count / total * 100 if total else 0.0
    )
    minority_percentage = (
        min(normal_percentage, bombing_percentage)
        if total
        else 0.0
    )

    if invalid_labels:
        result.add_error(
            "Class distribution cannot be fully calculated "
            "because invalid labels exist."
        )

    if total == 0:
        result.add_error(
            "Class distribution cannot be calculated "
            "for an empty Dataset Version."
        )

    if imbalance_threshold is not None:
        if (
            isinstance(imbalance_threshold, bool)
            or not isinstance(imbalance_threshold, (int, float))
            or not 0 <= imbalance_threshold <= 50
        ):
            result.add_error(
                "Imbalance threshold must be between 0 and 50."
            )
        elif total and not invalid_labels:
            if minority_percentage < imbalance_threshold:
                result.add_warning(
                    "Class distribution is below the configured "
                    "minority-class threshold."
                )

    result.details.update({
        "total_samples": total,
        "normal_count": normal_count,
        "bombing_count": bombing_count,
        "normal_percentage": normal_percentage,
        "bombing_percentage": bombing_percentage,
        "minority_class_percentage": minority_percentage,
        "imbalance_threshold": imbalance_threshold,
        "invalid_label_count": len(invalid_labels),
        "affected_count": len(invalid_labels),
        "affected_records": invalid_labels,
    })

    return result


# ============================================================
# CHECK 6: INVALID FEATURE VALUES
# ============================================================

def validate_invalid_feature_values(
    records: Iterable[Any] | None,
) -> ValidationResult:
    """
    Validate feature types and ranges using the current
    F1-F12 contract.

    F1: nullable string
    F2-F8: boolean
    F9-F12: non-negative integers
    """
    result = ValidationResult()
    items, error = _materialize_iterable(records)

    if error:
        result.add_error(
            "Feature records are required and must be iterable."
        )
        return result

    assert items is not None

    affected: list[dict[str, Any]] = []
    invalid_counts = Counter()

    for record in items:
        features = _record_features(record)
        invalid: list[dict[str, Any]] = []

        for feature_id in EXPECTED_FEATURE_IDS:
            value = _feature_value(features, feature_id)
            expected_type: str | None = None
            reason: str | None = None

            if feature_id == "F1":
                expected_type = "string or null"
                if value is not None and not isinstance(value, str):
                    reason = "Expected a string or null."

            elif feature_id in BOOLEAN_FEATURE_IDS:
                expected_type = "boolean"
                if not isinstance(value, bool):
                    reason = "Expected a boolean."

            elif feature_id in INTEGER_FEATURE_IDS:
                expected_type = "non-negative integer"
                if not _is_non_negative_integer(value):
                    reason = (
                        "Expected a non-negative integer; "
                        "booleans are not accepted."
                    )

            if reason:
                invalid.append({
                    "feature_id": feature_id,
                    "value": repr(value),
                    "expected_type": expected_type,
                    "reason": reason,
                })
                invalid_counts[feature_id] += 1

        if invalid:
            affected.append({
                "email_id": _record_id(record),
                "invalid_features": invalid,
            })

    if affected:
        result.add_error(
            f"Invalid feature values detected in "
            f"{len(affected)} record(s)."
        )

    result.details.update({
        "total_records": len(items),
        "affected_count": len(affected),
        "invalid_value_count": sum(invalid_counts.values()),
        "invalid_counts_by_feature": dict(invalid_counts),
        "affected_records": affected,
    })

    return result


# ============================================================
# CHECK 7: SPLIT CONSISTENCY
# ============================================================

def validate_split_consistency(
    memberships: Iterable[Any] | None,
    *,
    expected_total: int | None = None,
) -> ValidationResult:
    """
    Validate split assignments and aggregate consistency.

    Checks allowed split values, membership uniqueness,
    and optional expected sample count. This does not
    impose non-empty train/validation/test requirements.
    """
    result = ValidationResult()
    items, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert items is not None

    split_counts = Counter()
    seen: dict[Any, list[int]] = {}
    invalid_records: list[dict[str, Any]] = []

    for index, membership in enumerate(items):
        email_id = _email_id(membership)
        split = _record_split(membership)

        if email_id is not None:
            seen.setdefault(email_id, []).append(index)

        if split not in VALID_SPLITS:
            invalid_records.append({
                "email_id": _record_id(membership),
                "index": index,
                "split": str(split),
            })
        else:
            split_counts[split] += 1

    duplicate_records = [
        {
            "email_id": str(email_id),
            "indexes": indexes,
        }
        for email_id, indexes in seen.items()
        if len(indexes) > 1
    ]

    if invalid_records:
        result.add_error(
            f"Invalid split assignments found in "
            f"{len(invalid_records)} membership record(s)."
        )

    if duplicate_records:
        result.add_error(
            f"Duplicate membership IDs found for "
            f"{len(duplicate_records)} email(s)."
        )

    if expected_total is not None:
        if not _is_non_negative_integer(expected_total):
            result.add_error(
                "Expected total must be a non-negative integer."
            )
        elif len(items) != expected_total:
            result.add_error(
                "Membership count does not match the expected "
                "Dataset Version sample count."
            )

    result.details.update({
        "total_records": len(items),
        "split_counts": {
            split: split_counts.get(split, 0)
            for split in sorted(VALID_SPLITS)
        },
        "invalid_split_count": len(invalid_records),
        "duplicate_membership_count": len(duplicate_records),
        "affected_count": (
            len(invalid_records) + len(duplicate_records)
        ),
        "invalid_records": invalid_records,
        "duplicate_records": duplicate_records,
    })

    return result


# ============================================================
# VERSION INTEGRITY
# ============================================================

def validate_version_integrity(
    version: Any,
    memberships: Iterable[Any] | None,
) -> ValidationResult:
    """Validate the structural integrity of a Dataset Version."""
    result = ValidationResult()

    if version is None:
        result.add_error("Dataset Version is required.")
        return result

    membership_list, error = _materialize_iterable(memberships)

    if error:
        result.add_error(
            "Dataset memberships are required and must be iterable."
        )
        return result

    assert membership_list is not None

    result.merge(validate_memberships(membership_list))

    sample_count = _get_value(version, "sample_count")

    if isinstance(sample_count, bool) or not isinstance(
        sample_count, int
    ):
        result.add_error(
            "Dataset Version sample_count must be an integer."
        )
    elif sample_count < 0:
        result.add_error(
            "Dataset Version sample_count cannot be negative."
        )
    elif sample_count != len(membership_list):
        result.add_error(
            "Dataset Version sample count does not match "
            "membership count."
        )

    split_counts = _get_value(version, "split_counts")

    if split_counts is None:
        training = _get_value(version, "training_count")
        validation = _get_value(version, "validation_count")
        testing = _get_value(version, "testing_count")

        if all(
            value is not None
            for value in (training, validation, testing)
        ):
            if all(
                isinstance(value, int)
                and not isinstance(value, bool)
                for value in (training, validation, testing)
            ):
                split_counts = {
                    "training": training,
                    "validation": validation,
                    "testing": testing,
                    "total": training + validation + testing,
                }

    if split_counts is not None:
        expected_total = (
            sample_count
            if _is_non_negative_integer(sample_count)
            else len(membership_list)
        )
        result.merge(
            validate_split_counts(split_counts, expected_total)
        )

    normal_count = _get_value(version, "normal_count")
    bombing_count = _get_value(version, "bombing_count")

    if normal_count is not None and bombing_count is not None:
        if (
            _is_non_negative_integer(normal_count)
            and _is_non_negative_integer(bombing_count)
            and normal_count + bombing_count != len(membership_list)
        ):
            result.add_error(
                "Version ground-truth counts do not match "
                "membership count."
            )

    return result


def ensure_version_integrity(
    version: Any,
    memberships: Iterable[Any] | None,
) -> None:
    ensure_valid(
        validate_version_integrity(version, memberships),
        message="Dataset Version integrity validation failed.",
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # Constants
    "TOTAL_FEATURES",
    "EXPECTED_FEATURE_IDS",
    "VALID_GROUND_TRUTHS",
    "VALID_SPLITS",
    "FEATURE_FIELD_MAP",
    "BOOLEAN_FEATURE_IDS",
    "INTEGER_FEATURE_IDS",
    "NON_NEGATIVE_FEATURE_IDS",
    "VALIDATION_CHECK_CODES",

    # Check codes
    "CHECK_MISSING_FEATURE_VALUES",
    "CHECK_LABEL_CONSISTENCY",
    "CHECK_DUPLICATE_SAMPLES",
    "CHECK_FEATURE_SCHEMA",
    "CHECK_CLASS_DISTRIBUTION",
    "CHECK_INVALID_FEATURE_VALUES",
    "CHECK_SPLIT_CONSISTENCY",
    "CHECK_VERSION_INTEGRITY",

    # Exception and result
    "DatasetValidationError",
    "ValidationResult",

    # Generic helpers
    "ensure_valid",
    "validate_or_raise",

    # Feature schema
    "validate_feature_schema",
    "ensure_valid_feature_schema",
    "validate_feature_schema_compatibility",

    # Email selection
    "validate_email_ids",
    "validate_selected_email_ids",
    "ensure_valid_selected_email_ids",

    # Dataset creation
    "validate_dataset_create_request",
    "ensure_valid_dataset_create_request",

    # Split configuration
    "validate_split_configuration",
    "ensure_valid_split_configuration",

    # Version creation and integrity
    "validate_dataset_version_request",
    "ensure_valid_dataset_version_request",
    "validate_version_integrity",
    "ensure_version_integrity",

    # Memberships and counts
    "validate_memberships",
    "ensure_valid_memberships",
    "validate_split_counts",
    "validate_ground_truth_distribution",
    "validate_dataset_counters",
    "ensure_valid_dataset_counters",

    # Validation Page checks
    "validate_missing_feature_values",
    "validate_label_consistency",
    "validate_duplicate_samples",
    "validate_class_distribution",
    "validate_invalid_feature_values",
    "validate_split_consistency",
]