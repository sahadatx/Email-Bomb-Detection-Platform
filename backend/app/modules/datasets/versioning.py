
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

from app.modules.datasets.models import (
    Dataset,
    DatasetMembership,
    DatasetSplit,
    DatasetVersion,
    DatasetVersionStatus,
)
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import (
    DatasetFeatureSchema,
    DatasetSplitConfiguration,
)
from app.modules.datasets.splitting import (
    SplitAssignment,
    SplitResult,
    SplitSample,
    create_split,
    validate_split_result,
)
from app.modules.datasets.validators import (
    DatasetValidationError,
    ensure_valid_dataset_version_request,
    ensure_valid_feature_schema,
    ensure_version_integrity,
    validate_ground_truth_distribution,
    validate_memberships,
    validate_split_configuration,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_FEATURE_SCHEMA_VERSION = "1.0"
DEFAULT_FEATURE_SCHEMA_NAME = "F1-F12"

DEFAULT_FEATURE_SCHEMA = {
    "version": DEFAULT_FEATURE_SCHEMA_VERSION,
    "name": DEFAULT_FEATURE_SCHEMA_NAME,
    "feature_count": 12,
    "features": [
        {
            "feature_id": "F1",
            "name": "Sender Email",
            "data_type": "string",
        },
        {
            "feature_id": "F2",
            "name": "Known Domain Indicator",
            "data_type": "boolean",
        },
        {
            "feature_id": "F3",
            "name": "Message-ID Presence",
            "data_type": "boolean",
        },
        {
            "feature_id": "F4",
            "name": "Auto-Submitted Header",
            "data_type": "boolean",
        },
        {
            "feature_id": "F5",
            "name": "Precedence Bulk Indicator",
            "data_type": "boolean",
        },
        {
            "feature_id": "F6",
            "name": "List-Id Header",
            "data_type": "boolean",
        },
        {
            "feature_id": "F7",
            "name": "X-BeenThere Header",
            "data_type": "boolean",
        },
        {
            "feature_id": "F8",
            "name": "X-Anti-Abuse Header",
            "data_type": "boolean",
        },
        {
            "feature_id": "F9",
            "name": "Keyword-Based Content Features",
            "data_type": "integer",
        },
        {
            "feature_id": "F10",
            "name": "Subject Length",
            "data_type": "integer",
        },
        {
            "feature_id": "F11",
            "name": "Emails Per Minute",
            "data_type": "integer",
        },
        {
            "feature_id": "F12",
            "name": "Emails Per Hour",
            "data_type": "integer",
        },
    ],
}

SPLIT_TO_MODEL = {
    "train": DatasetSplit.TRAIN,
    "validation": DatasetSplit.VALIDATION,
    "test": DatasetSplit.TEST,
}


# ============================================================
# TIME
# ============================================================

def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_label(value: Any) -> str:
    """Normalize an enum or string ground-truth label."""
    raw = getattr(value, "value", value)

    if raw is None:
        return ""

    return str(raw).strip().lower()


def normalize_status(value: Any) -> str:
    """Normalize an enum or string version status."""
    raw = getattr(value, "value", value)

    if raw is None:
        return ""

    return str(raw).strip().lower()


def normalize_feature_schema(
    schema: DatasetFeatureSchema | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Return a JSON-serializable feature-schema snapshot.

    The schema stores definitions and metadata only.
    Feature values remain owned by Module 04.
    """
    if schema is None:
        return {
            **DEFAULT_FEATURE_SCHEMA,
            "features": [
                dict(feature)
                for feature in DEFAULT_FEATURE_SCHEMA["features"]
            ],
        }

    if isinstance(schema, dict):
        normalized = {
            **DEFAULT_FEATURE_SCHEMA,
            **schema,
        }

        normalized["features"] = [
            dict(feature)
            for feature in schema.get(
                "features",
                DEFAULT_FEATURE_SCHEMA["features"],
            )
        ]

        if not normalized.get("name"):
            normalized["name"] = DEFAULT_FEATURE_SCHEMA_NAME

        return normalized

    if hasattr(schema, "model_dump"):
        return schema.model_dump(mode="json")

    raise DatasetValidationError(
        "Unsupported feature schema representation.",
        code="invalid_feature_schema",
    )


# ============================================================
# VERSION NUMBER
# ============================================================

def get_next_version_number(
    repository: DatasetRepository,
    dataset_id: UUID,
) -> int:
    """
    Return the next sequential version number.

    Version numbering starts at 1 and increases monotonically.
    """
    versions, _ = repository.list_dataset_versions(
        dataset_id=dataset_id,
        page=1,
        page_size=100,
    )

    if not versions:
        return 1

    return max(
        version.version_number
        for version in versions
    ) + 1


# ============================================================
# DATASET SAMPLE RESOLUTION
# ============================================================

def _get_dataset_sample_ids(
    repository: DatasetRepository,
    dataset: Dataset,
) -> list[UUID]:
    """
    Resolve the dataset's selected sample population.

    Dataset membership is based on DatasetSample rows.
    It does not use all workspace emails unless those emails
    were explicitly added to the Dataset.
    """
    dataset_id = getattr(dataset, "id", None)

    if not isinstance(dataset_id, UUID):
        raise DatasetValidationError(
            "Dataset must be persisted before creating a version.",
            code="dataset_not_persisted",
        )

    sample_ids = repository.list_dataset_email_ids(
        dataset_id=dataset_id,
    )

    normalized_ids = list(dict.fromkeys(sample_ids))

    if not normalized_ids:
        raise DatasetValidationError(
            "Cannot create a version from an empty Dataset.",
            code="empty_dataset",
        )

    return normalized_ids


def _resolve_requested_sample_ids(
    repository: DatasetRepository,
    dataset: Dataset,
    email_ids: Sequence[UUID] | None,
) -> list[UUID]:
    """
    Resolve the sample population for version creation.

    When email_ids is omitted, all Dataset samples are used.
    When supplied, every requested ID must belong to the Dataset.
    """
    dataset_sample_ids = _get_dataset_sample_ids(
        repository,
        dataset,
    )

    if email_ids is None:
        return dataset_sample_ids

    requested_ids = list(dict.fromkeys(email_ids))

    if not requested_ids:
        raise DatasetValidationError(
            "At least one email must be selected for the version.",
            code="empty_version_selection",
        )

    dataset_sample_set = set(dataset_sample_ids)
    unknown_ids = [
        email_id
        for email_id in requested_ids
        if email_id not in dataset_sample_set
    ]

    if unknown_ids:
        raise DatasetValidationError(
            "One or more selected emails do not belong to this Dataset.",
            code="samples_not_in_dataset",
            details={
                "email_ids": [
                    str(email_id)
                    for email_id in unknown_ids
                ],
            },
        )

    return requested_ids


# ============================================================
# SPLIT SAMPLE CREATION
# ============================================================

def build_split_samples(
    *,
    repository: DatasetRepository,
    email_ids: Sequence[UUID],
) -> list[SplitSample]:
    """
    Build the minimal input required by the splitter.

    Ground truth is read from the canonical Email records.
    Feature values are not recalculated or copied into the
    splitting layer.
    """
    normalized_ids = list(dict.fromkeys(email_ids))

    if not normalized_ids:
        raise DatasetValidationError(
            "Cannot create a Dataset Version without samples.",
            code="empty_version_selection",
        )

    eligible_ids = repository.list_eligible_email_ids(
        normalized_ids,
    )

    eligible_set = set(eligible_ids)

    ineligible_ids = [
        email_id
        for email_id in normalized_ids
        if email_id not in eligible_set
    ]

    if ineligible_ids:
        raise DatasetValidationError(
            "One or more selected emails are no longer Dataset-eligible.",
            code="ineligible_samples",
            details={
                "email_ids": [
                    str(email_id)
                    for email_id in ineligible_ids
                ],
            },
        )

    emails = repository.get_emails_by_ids(
        eligible_ids,
    )

    email_map = {
        email.id: email
        for email in emails
    }

    samples: list[SplitSample] = []

    for email_id in normalized_ids:
        email = email_map.get(email_id)

        if email is None:
            raise DatasetValidationError(
                f"Email {email_id} could not be found.",
                code="email_not_found",
            )

        label = normalize_label(
            email.ground_truth_label
        )

        if label not in {"normal", "bombing"}:
            raise DatasetValidationError(
                f"Email {email_id} has an invalid ground-truth label.",
                code="invalid_ground_truth",
                details={
                    "email_id": str(email_id),
                    "ground_truth": label,
                },
            )

        samples.append(
            SplitSample(
                email_id=email.id,
                ground_truth=label,
            )
        )

    return samples


# ============================================================
# GROUND-TRUTH COUNTS
# ============================================================

def calculate_ground_truth_counts(
    samples: Sequence[SplitSample],
) -> tuple[int, int, int]:
    """
    Return total, normal, and bombing sample counts.
    """
    normal_count = 0
    bombing_count = 0

    for sample in samples:
        label = normalize_label(sample.ground_truth)

        if label == "normal":
            normal_count += 1
        elif label == "bombing":
            bombing_count += 1
        else:
            raise DatasetValidationError(
                f"Unsupported ground-truth label: {label!r}.",
                code="invalid_ground_truth",
            )

    total_count = len(samples)

    return total_count, normal_count, bombing_count


# ============================================================
# SPLIT COUNTS
# ============================================================

def calculate_split_counts(
    split_result: SplitResult,
) -> tuple[int, int, int]:
    """Return training, validation, and testing counts."""
    return (
        split_result.training_count,
        split_result.validation_count,
        split_result.testing_count,
    )


# ============================================================
# MEMBERSHIP CREATION
# ============================================================

def build_memberships(
    *,
    version_id: UUID,
    split_result: SplitResult,
) -> list[DatasetMembership]:
    """
    Convert split assignments into DatasetMembership records.

    Ground-truth and split values are snapshots. The feature
    values themselves remain in the canonical feature table.
    """
    now = utc_now()
    memberships: list[DatasetMembership] = []

    for assignment in split_result.assignments:
        split_model = SPLIT_TO_MODEL.get(
            assignment.split
        )

        if split_model is None:
            raise DatasetValidationError(
                f"Unsupported dataset split: {assignment.split!r}.",
                code="invalid_split",
            )

        label = normalize_label(
            assignment.ground_truth
        )

        if label not in {"normal", "bombing"}:
            raise DatasetValidationError(
                "Membership requires a valid ground-truth label.",
                code="invalid_ground_truth",
            )

        memberships.append(
            DatasetMembership(
                id=uuid4(),
                dataset_version_id=version_id,
                email_id=assignment.email_id,
                split=split_model,
                ground_truth=label,
                feature_schema_version=DEFAULT_FEATURE_SCHEMA_NAME,
                created_at=now,
            )
        )

    result = validate_memberships(memberships)

    if not result.passed:
        raise DatasetValidationError(
            "Generated Dataset memberships are invalid.",
            code="invalid_memberships",
            details={
                "errors": result.errors,
            },
        )

    return memberships


# ============================================================
# VERSION OBJECT
# ============================================================

def build_dataset_version(
    *,
    dataset_id: UUID,
    version_number: int,
    name: str,
    samples: Sequence[SplitSample],
    split_result: SplitResult,
    feature_schema: DatasetFeatureSchema | dict[str, Any] | None = None,
) -> DatasetVersion:
    """
    Build a DatasetVersion ORM object without persisting it.

    The returned version records the selected population,
    class distribution, split configuration, and schema.
    """
    total_count, normal_count, bombing_count = (
        calculate_ground_truth_counts(samples)
    )

    training_count, validation_count, testing_count = (
        calculate_split_counts(split_result)
    )

    schema_snapshot = normalize_feature_schema(
        feature_schema
    )

    return DatasetVersion(
        id=uuid4(),
        dataset_id=dataset_id,
        version_number=version_number,
        name=name.strip(),
        status=DatasetVersionStatus.READY,
        sample_count=total_count,
        valid_samples=0,
        normal_count=normal_count,
        bombing_count=bombing_count,
        training_percentage=split_result.training_percentage,
        validation_percentage=split_result.validation_percentage,
        testing_percentage=split_result.testing_percentage,
        random_seed=split_result.random_seed,
        stratified=split_result.stratified,
        training_count=training_count,
        validation_count=validation_count,
        testing_count=testing_count,
        validation_passed=False,
        validation_summary={
            "status": "not_validated",
            "split_configuration": build_reproducibility_metadata(
                split_result
            ),
        },
        feature_schema=schema_snapshot,
        created_at=utc_now(),
        validated_at=None,
    )


# ============================================================
# SNAPSHOT VALIDATION
# ============================================================

def validate_split_population(
    samples: Sequence[SplitSample],
    split_result: SplitResult,
) -> None:
    """Ensure the split contains exactly the input population."""
    source_ids = [sample.email_id for sample in samples]
    assigned_ids = [
        assignment.email_id
        for assignment in split_result.assignments
    ]

    if len(source_ids) != len(set(source_ids)):
        raise DatasetValidationError(
            "Source sample population contains duplicate email IDs.",
            code="duplicate_source_samples",
        )

    if len(assigned_ids) != len(set(assigned_ids)):
        raise DatasetValidationError(
            "Split result contains duplicate email IDs.",
            code="duplicate_split_memberships",
        )

    if set(source_ids) != set(assigned_ids):
        raise DatasetValidationError(
            "Split result does not match the source sample population.",
            code="split_population_mismatch",
            details={
                "missing_ids": [
                    str(value)
                    for value in sorted(
                        set(source_ids) - set(assigned_ids),
                        key=str,
                    )
                ],
                "unexpected_ids": [
                    str(value)
                    for value in sorted(
                        set(assigned_ids) - set(source_ids),
                        key=str,
                    )
                ],
            },
        )

    source_labels = {
        sample.email_id: normalize_label(sample.ground_truth)
        for sample in samples
    }

    for assignment in split_result.assignments:
        expected_label = source_labels.get(assignment.email_id)
        actual_label = normalize_label(assignment.ground_truth)

        if expected_label != actual_label:
            raise DatasetValidationError(
                "Split assignment ground truth differs from the source snapshot.",
                code="split_ground_truth_mismatch",
                details={
                    "email_id": str(assignment.email_id),
                    "expected": expected_label,
                    "actual": actual_label,
                },
            )


# ============================================================
# VERSION CREATION
# ============================================================

def create_dataset_version(
    *,
    repository: DatasetRepository,
    dataset: Dataset,
    email_ids: Sequence[UUID] | None = None,
    name: str,
    split_configuration: DatasetSplitConfiguration,
    feature_schema: DatasetFeatureSchema | None = None,
) -> tuple[
    DatasetVersion,
    list[DatasetMembership],
    SplitResult,
]:
    """
    Create a Dataset Version snapshot.

    Workflow:
        1. Validate the request and split configuration.
        2. Resolve the Dataset sample population.
        3. Recheck canonical eligibility.
        4. Read ground-truth labels.
        5. Generate deterministic split assignments.
        6. Validate population and assignment integrity.
        7. Build the version and membership snapshots.
        8. Persist both through the repository.

    The caller should execute this operation within a database
    transaction and commit only after both writes succeed.
    """
    if not isinstance(getattr(dataset, "id", None), UUID):
        raise DatasetValidationError(
            "Dataset must be persisted before creating a version.",
            code="dataset_not_persisted",
        )

    if not isinstance(name, str) or not name.strip():
        raise DatasetValidationError(
            "Dataset Version name cannot be empty.",
            code="invalid_version_name",
        )

    if split_configuration is None:
        raise DatasetValidationError(
            "Split configuration is required.",
            code="missing_split_configuration",
        )

    split_validation = validate_split_configuration(
        split_configuration
    )

    if not split_validation.passed:
        raise DatasetValidationError(
            "Invalid Dataset split configuration.",
            code="invalid_split_configuration",
            details={
                "errors": split_validation.errors,
            },
        )

    if feature_schema is not None:
        ensure_valid_feature_schema(feature_schema)

    resolved_ids = _resolve_requested_sample_ids(
        repository,
        dataset,
        email_ids,
    )

    samples = build_split_samples(
        repository=repository,
        email_ids=resolved_ids,
    )

    if not samples:
        raise DatasetValidationError(
            "No eligible samples are available for the Dataset Version.",
            code="empty_version_population",
        )

    split_result = create_split(
        samples,
        split_configuration,
    )

    validate_split_result(split_result)
    validate_split_population(samples, split_result)

    total_count, normal_count, bombing_count = (
        calculate_ground_truth_counts(samples)
    )

    distribution_result = validate_ground_truth_distribution(
        normal_count,
        bombing_count,
    )

    if not distribution_result.passed:
        raise DatasetValidationError(
            "Dataset Version ground-truth distribution is invalid.",
            code="invalid_ground_truth_distribution",
            details={
                "errors": distribution_result.errors,
            },
        )

    version_number = get_next_version_number(
        repository,
        dataset.id,
    )

    version = build_dataset_version(
        dataset_id=dataset.id,
        version_number=version_number,
        name=name,
        samples=samples,
        split_result=split_result,
        feature_schema=feature_schema,
    )

    memberships = build_memberships(
        version_id=version.id,
        split_result=split_result,
    )

    if len(memberships) != total_count:
        raise DatasetValidationError(
            "Generated membership count does not match the sample count.",
            code="membership_count_mismatch",
        )

    # Persist version and memberships as one logical operation.
    # The service/route must provide transaction handling.
    repository.create_dataset_version(version)
    repository.create_memberships(memberships)

    return version, memberships, split_result


# ============================================================
# VERSION SNAPSHOT
# ============================================================

def build_version_snapshot(
    version: DatasetVersion,
) -> dict[str, Any]:
    """Return a JSON-compatible version metadata snapshot."""
    status = normalize_status(version.status)

    created_at = getattr(version, "created_at", None)
    validated_at = getattr(version, "validated_at", None)

    return {
        "id": str(version.id),
        "dataset_id": str(version.dataset_id),
        "version_number": version.version_number,
        "name": version.name,
        "status": status,
        "sample_count": version.sample_count,
        "valid_samples": getattr(version, "valid_samples", 0),
        "normal_count": version.normal_count,
        "bombing_count": version.bombing_count,
        "training_percentage": version.training_percentage,
        "validation_percentage": version.validation_percentage,
        "testing_percentage": version.testing_percentage,
        "random_seed": version.random_seed,
        "stratified": version.stratified,
        "training_count": version.training_count,
        "validation_count": version.validation_count,
        "testing_count": version.testing_count,
        "validation_passed": version.validation_passed,
        "validation_summary": version.validation_summary,
        "feature_schema": version.feature_schema,
        "created_at": (
            created_at.isoformat()
            if created_at
            else None
        ),
        "validated_at": (
            validated_at.isoformat()
            if validated_at
            else None
        ),
    }


# ============================================================
# IMMUTABILITY
# ============================================================

IMMUTABLE_VERSION_FIELDS = frozenset(
    {
        "dataset_id",
        "version_number",
        "sample_count",
        "normal_count",
        "bombing_count",
        "training_percentage",
        "validation_percentage",
        "testing_percentage",
        "random_seed",
        "stratified",
        "training_count",
        "validation_count",
        "testing_count",
        "feature_schema",
    }
)


def ensure_version_mutable(
    version: DatasetVersion,
) -> None:
    """
    Reject changes to finalized versions.

    Validation metadata may be updated independently, but the
    population, schema, and split configuration are immutable.
    """
    status = normalize_status(version.status)

    finalized_statuses = {
        DatasetVersionStatus.READY.value,
        DatasetVersionStatus.VALIDATED.value,
        DatasetVersionStatus.INVALID.value,
    }

    if status in finalized_statuses:
        raise DatasetValidationError(
            "Dataset Version is immutable. Create a new version instead.",
            code="immutable_dataset_version",
        )


def ensure_immutable_fields_unchanged(
    original: DatasetVersion,
    updated: DatasetVersion,
) -> None:
    """
    Compare protected snapshot fields between two version objects.
    """
    changed_fields = [
        field_name
        for field_name in IMMUTABLE_VERSION_FIELDS
        if getattr(original, field_name, None)
        != getattr(updated, field_name, None)
    ]

    if changed_fields:
        raise DatasetValidationError(
            "Immutable Dataset Version fields cannot be changed.",
            code="immutable_version_fields",
            details={
                "changed_fields": sorted(changed_fields),
            },
        )


# ============================================================
# VALIDATION STATE
# ============================================================

def mark_version_validated(
    version: DatasetVersion,
    *,
    valid: bool,
    summary: dict[str, Any],
) -> DatasetVersion:
    """
    Update validation status without changing the snapshot.

    This function is intended for the validation workflow.
    """
    if not isinstance(valid, bool):
        raise DatasetValidationError(
            "Validation result must be a boolean.",
            code="invalid_validation_result",
        )

    if not isinstance(summary, dict):
        raise DatasetValidationError(
            "Validation summary must be a dictionary.",
            code="invalid_validation_summary",
        )

    version.validation_passed = valid
    version.validation_summary = dict(summary)
    version.validated_at = utc_now()

    version.status = (
        DatasetVersionStatus.VALIDATED
        if valid
        else DatasetVersionStatus.INVALID
    )

    return version


# ============================================================
# MEMBERSHIP INTEGRITY
# ============================================================

def validate_membership_assignments(
    *,
    memberships: Sequence[DatasetMembership],
    expected_sample_count: int,
    expected_version_id: UUID | None = None,
) -> None:
    """
    Validate that each sample has exactly one valid membership.
    """
    if len(memberships) != expected_sample_count:
        raise DatasetValidationError(
            "Dataset membership count does not match the version sample count.",
            code="membership_count_mismatch",
        )

    result = validate_memberships(memberships)

    if not result.passed:
        raise DatasetValidationError(
            "Dataset membership assignments are invalid.",
            code="invalid_memberships",
            details={
                "errors": result.errors,
            },
        )

    for membership in memberships:
        if expected_version_id is not None:
            if membership.dataset_version_id != expected_version_id:
                raise DatasetValidationError(
                    "Membership references a different Dataset Version.",
                    code="membership_version_mismatch",
                )

        if normalize_label(membership.ground_truth) not in {
            "normal",
            "bombing",
        }:
            raise DatasetValidationError(
                "Membership contains an invalid ground-truth label.",
                code="invalid_membership_ground_truth",
            )


# ============================================================
# SPLIT DISTRIBUTION
# ============================================================

def build_split_distribution(
    split_result: SplitResult,
) -> dict[str, Any]:
    """Build split count and percentage metadata."""
    return {
        "training": {
            "count": split_result.training_count,
            "percentage": split_result.training_percentage,
        },
        "validation": {
            "count": split_result.validation_count,
            "percentage": split_result.validation_percentage,
        },
        "testing": {
            "count": split_result.testing_count,
            "percentage": split_result.testing_percentage,
        },
        "total": {
            "count": split_result.total_count,
            "percentage": 100,
        },
    }


# ============================================================
# REPRODUCIBILITY METADATA
# ============================================================

def build_reproducibility_metadata(
    split_result: SplitResult,
) -> dict[str, Any]:
    """Return the parameters needed to describe the split."""
    return {
        "random_seed": split_result.random_seed,
        "stratified": split_result.stratified,
        "training_percentage": split_result.training_percentage,
        "validation_percentage": split_result.validation_percentage,
        "testing_percentage": split_result.testing_percentage,
    }


# ============================================================
# PUBLIC CONTRACT
# ============================================================

__all__ = [
    "DEFAULT_FEATURE_SCHEMA_VERSION",
    "DEFAULT_FEATURE_SCHEMA_NAME",
    "DEFAULT_FEATURE_SCHEMA",
    "IMMUTABLE_VERSION_FIELDS",
    "utc_now",
    "normalize_label",
    "normalize_status",
    "normalize_feature_schema",
    "get_next_version_number",
    "build_split_samples",
    "calculate_ground_truth_counts",
    "calculate_split_counts",
    "build_memberships",
    "build_dataset_version",
    "validate_split_population",
    "create_dataset_version",
    "build_version_snapshot",
    "ensure_version_mutable",
    "ensure_immutable_fields_unchanged",
    "mark_version_validated",
    "validate_membership_assignments",
    "build_split_distribution",
    "build_reproducibility_metadata",
]