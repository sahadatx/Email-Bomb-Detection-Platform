
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.modules.datasets.schemas import (
    DatasetSplitConfiguration,
)
from app.modules.datasets.validators import (
    DatasetValidationError,
    ensure_valid,
    validate_split_configuration,
)


# ============================================================
# CONSTANTS
# ============================================================

TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
TEST_SPLIT = "test"

VALID_SPLITS = frozenset(
    {
        TRAIN_SPLIT,
        VALIDATION_SPLIT,
        TEST_SPLIT,
    }
)

NORMAL_LABEL = "normal"
BOMBING_LABEL = "bombing"

VALID_GROUND_TRUTH_LABELS = frozenset(
    {
        NORMAL_LABEL,
        BOMBING_LABEL,
    }
)


# ============================================================
# TYPES
# ============================================================


@dataclass(frozen=True, slots=True)
class SplitSample:
    """
    Minimal immutable sample representation required by the
    dataset splitting engine.

    The splitter only uses email_id and ground_truth.
    Feature extraction remains owned by Module 04.
    """

    email_id: UUID
    ground_truth: str


@dataclass(frozen=True, slots=True)
class SplitAssignment:
    """
    Immutable assignment of one email to one dataset split.
    """

    email_id: UUID
    ground_truth: str
    split: str


@dataclass(frozen=True, slots=True)
class SplitResult:
    """
    Immutable result of a complete dataset split operation.
    """

    assignments: tuple[SplitAssignment, ...]

    training_ids: tuple[UUID, ...]
    validation_ids: tuple[UUID, ...]
    testing_ids: tuple[UUID, ...]

    training_count: int
    validation_count: int
    testing_count: int

    total_count: int

    training_percentage: int
    validation_percentage: int
    testing_percentage: int

    random_seed: int
    stratified: bool


# ============================================================
# INPUT NORMALIZATION
# ============================================================


def _normalize_label(label: str) -> str:
    """
    Normalize and validate a ground-truth label.
    """

    if not isinstance(label, str):
        raise DatasetValidationError(
            "Ground-truth labels must be strings."
        )

    normalized = label.strip().lower()

    if normalized not in VALID_GROUND_TRUTH_LABELS:
        raise DatasetValidationError(
            f"Unsupported ground-truth label: {label!r}. "
            "Expected 'normal' or 'bombing'."
        )

    return normalized


def _normalize_samples(
    samples: Sequence[SplitSample],
) -> list[SplitSample]:
    """
    Validate and normalize the supplied sample population.

    Rejects:
        - duplicate email IDs
        - invalid sample objects
        - missing email IDs
        - unsupported ground-truth labels

    The original input sequence is not modified.
    """

    normalized: list[SplitSample] = []
    seen_ids: set[UUID] = set()

    for index, sample in enumerate(samples):
        if not isinstance(sample, SplitSample):
            raise DatasetValidationError(
                f"Invalid sample at index {index}. "
                "Expected SplitSample."
            )

        if not isinstance(sample.email_id, UUID):
            raise DatasetValidationError(
                f"Invalid email_id at sample index {index}."
            )

        if sample.email_id in seen_ids:
            raise DatasetValidationError(
                f"Duplicate email ID in split population: "
                f"{sample.email_id}"
            )

        seen_ids.add(sample.email_id)

        normalized.append(
            SplitSample(
                email_id=sample.email_id,
                ground_truth=_normalize_label(
                    sample.ground_truth,
                ),
            )
        )

    return normalized


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================


def _validate_configuration(
    configuration: DatasetSplitConfiguration,
) -> None:
    """
    Validate split configuration through the canonical
    Dataset validation layer.
    """

    ensure_valid(
        validate_split_configuration(
            configuration,
        )
    )


# ============================================================
# RANDOMIZATION
# ============================================================


def _shuffle(
    items: Sequence[SplitSample],
    *,
    seed: int,
) -> list[SplitSample]:
    """
    Return a deterministically shuffled copy of the samples.

    Uses Python's standard-library random module.
    """

    result = list(items)

    random.Random(seed).shuffle(result)

    return result


# ============================================================
# COUNT CALCULATION
# ============================================================


def calculate_split_counts(
    total_samples: int,
    configuration: DatasetSplitConfiguration,
) -> tuple[int, int, int]:
    """
    Calculate train, validation, and test sample counts.

    Training and validation receive their proportional floor
    counts. Testing receives the remainder.

    This guarantees that all calculated counts sum to the
    original sample count.
    """

    if total_samples < 0:
        raise DatasetValidationError(
            "Total sample count cannot be negative."
        )

    _validate_configuration(configuration)

    training_count = (
        total_samples
        * configuration.training_percentage
    ) // 100

    validation_count = (
        total_samples
        * configuration.validation_percentage
    ) // 100

    testing_count = (
        total_samples
        - training_count
        - validation_count
    )

    return (
        training_count,
        validation_count,
        testing_count,
    )


def _calculate_class_split_counts(
    class_size: int,
    *,
    training_percentage: int,
    validation_percentage: int,
    testing_percentage: int,
) -> tuple[int, int, int]:
    """
    Calculate split counts for one ground-truth class.

    Testing receives the remainder to ensure that the class's
    split counts sum exactly to class_size.
    """

    if class_size < 0:
        raise DatasetValidationError(
            "Class size cannot be negative."
        )

    if (
        training_percentage
        + validation_percentage
        + testing_percentage
        != 100
    ):
        raise DatasetValidationError(
            "Split percentages must sum to exactly 100."
        )

    training_count = (
        class_size * training_percentage
    ) // 100

    validation_count = (
        class_size * validation_percentage
    ) // 100

    testing_count = (
        class_size
        - training_count
        - validation_count
    )

    return (
        training_count,
        validation_count,
        testing_count,
    )


# ============================================================
# RESULT BUILDER
# ============================================================


def _build_result(
    *,
    training_samples: Sequence[SplitSample],
    validation_samples: Sequence[SplitSample],
    testing_samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration,
) -> SplitResult:
    """
    Construct an immutable SplitResult from the three
    completed partitions.
    """

    training_assignments = tuple(
        SplitAssignment(
            email_id=sample.email_id,
            ground_truth=sample.ground_truth,
            split=TRAIN_SPLIT,
        )
        for sample in training_samples
    )

    validation_assignments = tuple(
        SplitAssignment(
            email_id=sample.email_id,
            ground_truth=sample.ground_truth,
            split=VALIDATION_SPLIT,
        )
        for sample in validation_samples
    )

    testing_assignments = tuple(
        SplitAssignment(
            email_id=sample.email_id,
            ground_truth=sample.ground_truth,
            split=TEST_SPLIT,
        )
        for sample in testing_samples
    )

    assignments = (
        training_assignments
        + validation_assignments
        + testing_assignments
    )

    training_ids = tuple(
        sample.email_id
        for sample in training_samples
    )

    validation_ids = tuple(
        sample.email_id
        for sample in validation_samples
    )

    testing_ids = tuple(
        sample.email_id
        for sample in testing_samples
    )

    return SplitResult(
        assignments=assignments,
        training_ids=training_ids,
        validation_ids=validation_ids,
        testing_ids=testing_ids,
        training_count=len(training_ids),
        validation_count=len(validation_ids),
        testing_count=len(testing_ids),
        total_count=len(assignments),
        training_percentage=(
            configuration.training_percentage
        ),
        validation_percentage=(
            configuration.validation_percentage
        ),
        testing_percentage=(
            configuration.testing_percentage
        ),
        random_seed=configuration.random_seed,
        stratified=configuration.stratified,
    )


# ============================================================
# NON-STRATIFIED SPLITTING
# ============================================================


def split_non_stratified(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration,
) -> SplitResult:
    """
    Perform deterministic random splitting without
    preserving class proportions.

    All samples are shuffled together before partitioning.
    """

    _validate_configuration(configuration)

    normalized_samples = _normalize_samples(samples)

    shuffled = _shuffle(
        normalized_samples,
        seed=configuration.random_seed,
    )

    (
        training_count,
        validation_count,
        testing_count,
    ) = calculate_split_counts(
        len(shuffled),
        configuration,
    )

    training_end = training_count

    validation_end = (
        training_count
        + validation_count
    )

    training_samples = shuffled[:training_end]

    validation_samples = shuffled[
        training_end:validation_end
    ]

    testing_samples = shuffled[validation_end:]

    result = _build_result(
        training_samples=training_samples,
        validation_samples=validation_samples,
        testing_samples=testing_samples,
        configuration=configuration,
    )

    validate_split_result(result)

    return result


# ============================================================
# STRATIFIED SPLITTING
# ============================================================


def split_stratified(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration,
) -> SplitResult:
    """
    Perform deterministic stratified splitting.

    Each ground-truth class is split independently. This
    approximately preserves class distribution across
    train, validation, and test.

    Small classes may not appear in every partition because
    integer sample counts cannot always satisfy that
    requirement.
    """

    _validate_configuration(configuration)

    normalized_samples = _normalize_samples(samples)

    if not normalized_samples:
        return _build_result(
            training_samples=[],
            validation_samples=[],
            testing_samples=[],
            configuration=configuration,
        )

    classes: dict[str, list[SplitSample]] = defaultdict(list)

    for sample in normalized_samples:
        classes[sample.ground_truth].append(sample)

    training_samples: list[SplitSample] = []
    validation_samples: list[SplitSample] = []
    testing_samples: list[SplitSample] = []

    for index, label in enumerate(
        sorted(classes),
    ):
        class_samples = classes[label]

        class_seed = (
            configuration.random_seed
            + index
            + 1
        )

        shuffled_class = _shuffle(
            class_samples,
            seed=class_seed,
        )

        (
            class_training_count,
            class_validation_count,
            class_testing_count,
        ) = _calculate_class_split_counts(
            len(shuffled_class),
            training_percentage=(
                configuration.training_percentage
            ),
            validation_percentage=(
                configuration.validation_percentage
            ),
            testing_percentage=(
                configuration.testing_percentage
            ),
        )

        training_end = class_training_count

        validation_end = (
            class_training_count
            + class_validation_count
        )

        training_samples.extend(
            shuffled_class[:training_end]
        )

        validation_samples.extend(
            shuffled_class[
                training_end:validation_end
            ]
        )

        testing_samples.extend(
            shuffled_class[validation_end:]
        )

    # Mix classes within each final partition while retaining
    # deterministic ordering.
    training_samples = _shuffle(
        training_samples,
        seed=configuration.random_seed + 1001,
    )

    validation_samples = _shuffle(
        validation_samples,
        seed=configuration.random_seed + 1002,
    )

    testing_samples = _shuffle(
        testing_samples,
        seed=configuration.random_seed + 1003,
    )

    result = _build_result(
        training_samples=training_samples,
        validation_samples=validation_samples,
        testing_samples=testing_samples,
        configuration=configuration,
    )

    validate_split_result(result)

    return result


# ============================================================
# MAIN SPLIT ENTRYPOINT
# ============================================================


def split_dataset(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration | None = None,
) -> SplitResult:
    """
    Main split entrypoint.

    Defaults are defined by DatasetSplitConfiguration:

        Training:    70%
        Validation:  15%
        Testing:     15%
        Random seed: 42
        Stratified:  True
    """

    if configuration is None:
        configuration = DatasetSplitConfiguration()

    _validate_configuration(configuration)

    if configuration.stratified:
        return split_stratified(
            samples,
            configuration,
        )

    return split_non_stratified(
        samples,
        configuration,
    )


# ============================================================
# SPLIT RESULT VALIDATION
# ============================================================


def validate_split_result(
    result: SplitResult,
) -> None:
    """
    Validate structural integrity of the split result.

    Checks:
        - split assignment labels are valid
        - no duplicate email IDs
        - every ID belongs to exactly one partition
        - assignments agree with partition ID lists
        - counts match the partition sizes
        - total count is consistent
        - percentages sum to 100
    """

    if not isinstance(result, SplitResult):
        raise DatasetValidationError(
            "Invalid split result."
        )

    if (
        result.training_percentage
        + result.validation_percentage
        + result.testing_percentage
        != 100
    ):
        raise DatasetValidationError(
            "Split result percentages must sum to 100."
        )

    partitions = {
        TRAIN_SPLIT: result.training_ids,
        VALIDATION_SPLIT: result.validation_ids,
        TEST_SPLIT: result.testing_ids,
    }

    all_partition_ids: list[UUID] = []

    for split, ids in partitions.items():
        if len(ids) != len(set(ids)):
            raise DatasetValidationError(
                f"Duplicate email IDs in {split} split."
            )

        all_partition_ids.extend(ids)

    if len(all_partition_ids) != len(set(all_partition_ids)):
        raise DatasetValidationError(
            "A sample was assigned to more than one split."
        )

    expected_counts = {
        TRAIN_SPLIT: result.training_count,
        VALIDATION_SPLIT: result.validation_count,
        TEST_SPLIT: result.testing_count,
    }

    for split, ids in partitions.items():
        if expected_counts[split] != len(ids):
            raise DatasetValidationError(
                f"{split} count does not match its ID list."
            )

    if result.total_count != len(all_partition_ids):
        raise DatasetValidationError(
            "Total count does not match partition membership."
        )

    assignment_ids: list[UUID] = []

    for assignment in result.assignments:
        if assignment.split not in VALID_SPLITS:
            raise DatasetValidationError(
                f"Unsupported split label: {assignment.split!r}"
            )

        if assignment.ground_truth not in VALID_GROUND_TRUTH_LABELS:
            raise DatasetValidationError(
                f"Unsupported ground-truth label: "
                f"{assignment.ground_truth!r}"
            )

        assignment_ids.append(assignment.email_id)

        if assignment.email_id not in partitions[assignment.split]:
            raise DatasetValidationError(
                "Assignment split does not match partition IDs."
            )

    if len(assignment_ids) != len(set(assignment_ids)):
        raise DatasetValidationError(
            "Duplicate email IDs found in assignments."
        )

    if set(assignment_ids) != set(all_partition_ids):
        raise DatasetValidationError(
            "Assignments do not match the complete split population."
        )


# ============================================================
# ASSIGNMENT CONVERSION
# ============================================================


def assignments_to_dicts(
    result: SplitResult,
) -> list[dict[str, object]]:
    """
    Convert assignments into dictionaries suitable for the
    service or repository layer.
    """

    validate_split_result(result)

    return [
        {
            "email_id": assignment.email_id,
            "ground_truth": assignment.ground_truth,
            "split": assignment.split,
        }
        for assignment in result.assignments
    ]


# ============================================================
# SPLIT ID ACCESS
# ============================================================


def get_split_ids(
    result: SplitResult,
    split: str,
) -> tuple[UUID, ...]:
    """
    Return IDs belonging to the requested split.
    """

    validate_split_result(result)

    normalized = split.strip().lower()

    if normalized == TRAIN_SPLIT:
        return result.training_ids

    if normalized == VALIDATION_SPLIT:
        return result.validation_ids

    if normalized == TEST_SPLIT:
        return result.testing_ids

    raise ValueError(
        f"Unsupported dataset split: {split!r}"
    )


# ============================================================
# CLASS DISTRIBUTION
# ============================================================


def calculate_split_class_distribution(
    result: SplitResult,
) -> dict[str, dict[str, int]]:
    """
    Calculate Normal and Bombing counts for each partition.
    """

    validate_split_result(result)

    distribution = {
        TRAIN_SPLIT: {
            NORMAL_LABEL: 0,
            BOMBING_LABEL: 0,
        },
        VALIDATION_SPLIT: {
            NORMAL_LABEL: 0,
            BOMBING_LABEL: 0,
        },
        TEST_SPLIT: {
            NORMAL_LABEL: 0,
            BOMBING_LABEL: 0,
        },
    }

    for assignment in result.assignments:
        distribution[assignment.split][
            assignment.ground_truth
        ] += 1

    return distribution


# ============================================================
# REPRODUCIBILITY
# ============================================================


def split_is_reproducible(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration,
) -> bool:
    """
    Verify that the same ordered input and configuration
    produce identical split assignments.
    """

    first = split_dataset(
        samples,
        configuration,
    )

    second = split_dataset(
        samples,
        configuration,
    )

    return first.assignments == second.assignments


# ============================================================
# STRATIFIED POPULATION VALIDATION
# ============================================================


def validate_stratified_class_sizes(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration,
) -> None:
    """
    Validate the class labels used by stratified splitting.

    Empty populations are permitted and produce empty splits.
    Each supplied sample must have a valid ground-truth label.

    This function does not require every class to appear in
    every split because small populations may make that
    mathematically impossible.
    """

    _validate_configuration(configuration)

    if not configuration.stratified:
        return

    _normalize_samples(samples)


# ============================================================
# HIGH-LEVEL SPLIT PIPELINE
# ============================================================


def create_split(
    samples: Sequence[SplitSample],
    configuration: DatasetSplitConfiguration | None = None,
) -> SplitResult:
    """
    Execute the complete split pipeline.

    Steps:
        1. Resolve default configuration.
        2. Validate configuration.
        3. Validate stratified input when enabled.
        4. Generate deterministic assignments.
        5. Validate split integrity.
        6. Return immutable result.
    """

    if configuration is None:
        configuration = DatasetSplitConfiguration()

    _validate_configuration(configuration)

    validate_stratified_class_sizes(
        samples,
        configuration,
    )

    result = split_dataset(
        samples,
        configuration,
    )

    validate_split_result(result)

    return result


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "TRAIN_SPLIT",
    "VALIDATION_SPLIT",
    "TEST_SPLIT",
    "VALID_SPLITS",
    "NORMAL_LABEL",
    "BOMBING_LABEL",
    "VALID_GROUND_TRUTH_LABELS",
    "SplitSample",
    "SplitAssignment",
    "SplitResult",
    "calculate_split_counts",
    "split_non_stratified",
    "split_stratified",
    "split_dataset",
    "validate_split_result",
    "assignments_to_dicts",
    "get_split_ids",
    "calculate_split_class_distribution",
    "split_is_reproducible",
    "validate_stratified_class_sizes",
    "create_split",
]