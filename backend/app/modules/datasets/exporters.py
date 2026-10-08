
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Sequence
from uuid import UUID

from app.modules.datasets.models import (
    DatasetMembership,
    DatasetSplit,
    DatasetVersion,
)
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.validators import (
    DatasetValidationError,
)


# ============================================================
# CONSTANTS
# ============================================================

EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"

EXPORT_SPLIT_ALL = "all"
EXPORT_SPLIT_TRAIN = "train"
EXPORT_SPLIT_VALIDATION = "validation"
EXPORT_SPLIT_TEST = "test"

SUPPORTED_EXPORT_FORMATS = frozenset({
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_JSON,
})

SUPPORTED_EXPORT_SPLITS = frozenset({
    EXPORT_SPLIT_ALL,
    EXPORT_SPLIT_TRAIN,
    EXPORT_SPLIT_VALIDATION,
    EXPORT_SPLIT_TEST,
})

SUPPORTED_GROUND_TRUTH_LABELS = frozenset({
    "normal",
    "bombing",
})

SUPPORTED_MEMBERSHIP_SPLITS = frozenset({
    EXPORT_SPLIT_TRAIN,
    EXPORT_SPLIT_VALIDATION,
    EXPORT_SPLIT_TEST,
})


# ============================================================
# EXPORT COLUMNS
# ============================================================

EXPORT_COLUMNS = (
    "email_id",
    "ground_truth",
    "f1_sender_email",
    "f2_known_domain",
    "f3_message_id",
    "f4_auto_submitted",
    "f5_precedence_bulk",
    "f6_list_id",
    "f7_x_beenthere",
    "f8_x_anti_abuse",
    "f9_keyword_features",
    "f10_subject_length",
    "f11_emails_per_minute",
    "f12_emails_per_hour",
    "split",
)


# ============================================================
# EXPORT RECORD
# ============================================================

@dataclass(frozen=True, slots=True)
class DatasetExportRecord:
    """
    One canonical ML-ready Dataset export row.

    F1-F12 are retrieved from Module 04's EmailFeatures record.

    This record intentionally excludes:
        - model predictions
        - confidence scores
        - risk scores
        - threat levels
    """

    email_id: UUID
    ground_truth: str

    f1_sender_email: str | None
    f2_known_domain: bool
    f3_message_id: bool
    f4_auto_submitted: bool
    f5_precedence_bulk: bool
    f6_list_id: bool
    f7_x_beenthere: bool
    f8_x_anti_abuse: bool

    f9_keyword_features: int
    f10_subject_length: int
    f11_emails_per_minute: int
    f12_emails_per_hour: int

    split: str


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_enum(value: Any) -> Any:
    """Return an enum's underlying value when applicable."""
    if isinstance(value, Enum):
        return value.value
    return value


def normalize_label(value: Any) -> str:
    """Normalize a ground-truth label."""
    raw = normalize_enum(value)

    if raw is None:
        return ""

    return str(raw).strip().lower()


def normalize_split(split: Any) -> str:
    """
    Normalize a DatasetSplit enum or split string.

    Valid membership splits:
        train
        validation
        test
    """
    raw = normalize_enum(split)

    if raw is None:
        raise DatasetValidationError(
            "Dataset membership is missing its split."
        )

    value = str(raw).strip().lower()

    if value not in SUPPORTED_MEMBERSHIP_SPLITS:
        raise DatasetValidationError(
            f"Unsupported dataset split: {value!r}."
        )

    return value


def normalize_requested_split(split: str) -> str:
    """Validate the requested export split."""
    if not isinstance(split, str):
        raise DatasetValidationError(
            "Export split must be a string."
        )

    value = split.strip().lower()

    if value not in SUPPORTED_EXPORT_SPLITS:
        raise DatasetValidationError(
            (
                f"Unsupported export split: {split!r}. "
                f"Supported values: "
                f"{', '.join(sorted(SUPPORTED_EXPORT_SPLITS))}."
            )
        )

    return value


def normalize_format(export_format: str) -> str:
    """Validate the requested export format."""
    if not isinstance(export_format, str):
        raise DatasetValidationError(
            "Export format must be a string."
        )

    value = export_format.strip().lower()

    if value not in SUPPORTED_EXPORT_FORMATS:
        raise DatasetValidationError(
            (
                f"Unsupported export format: {export_format!r}. "
                f"Supported formats: "
                f"{', '.join(sorted(SUPPORTED_EXPORT_FORMATS))}."
            )
        )

    return value


# ============================================================
# VALUE SERIALIZATION
# ============================================================

def serialize_value(value: Any) -> Any:
    """
    Convert common Python and SQLAlchemy values into
    JSON-compatible primitive values.
    """
    if value is None:
        return None

    if isinstance(value, Enum):
        return serialize_value(value.value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    raise DatasetValidationError(
        f"Unsupported export value type: {type(value).__name__}."
    )


# ============================================================
# FEATURE VALIDATION
# ============================================================

def _read_feature(
    features: Any,
    field_name: str,
    email_id: UUID,
) -> Any:
    """Read a required feature field from EmailFeatures."""
    if not hasattr(features, field_name):
        raise DatasetValidationError(
            (
                f"Feature record for email {email_id} "
                f"is missing field {field_name!r}."
            )
        )

    value = getattr(features, field_name)

    if value is None:
        raise DatasetValidationError(
            (
                f"Feature {field_name} for email {email_id} "
                "cannot be null."
            )
        )

    return value


def _read_boolean_feature(
    features: Any,
    field_name: str,
    email_id: UUID,
) -> bool:
    """
    Read a boolean feature without silently converting
    arbitrary strings or integers into booleans.
    """
    value = _read_feature(
        features,
        field_name,
        email_id,
    )

    if not isinstance(value, bool):
        raise DatasetValidationError(
            (
                f"Feature {field_name} for email {email_id} "
                "must be a boolean."
            )
        )

    return value


def _read_integer_feature(
    features: Any,
    field_name: str,
    email_id: UUID,
) -> int:
    """
    Read an integer feature.

    Booleans are rejected because bool is a subclass of int.
    """
    value = _read_feature(
        features,
        field_name,
        email_id,
    )

    if isinstance(value, bool) or not isinstance(value, int):
        raise DatasetValidationError(
            (
                f"Feature {field_name} for email {email_id} "
                "must be an integer."
            )
        )

    if value < 0:
        raise DatasetValidationError(
            (
                f"Feature {field_name} for email {email_id} "
                "cannot be negative."
            )
        )

    return value


# ============================================================
# FEATURE RECORD CONVERSION
# ============================================================

def build_export_record(
    *,
    membership: DatasetMembership,
    features: Any,
) -> DatasetExportRecord:
    """
    Build one export record from a DatasetMembership and
    the canonical Module 04 EmailFeatures record.
    """
    email_id = membership.email_id

    if not isinstance(email_id, UUID):
        raise DatasetValidationError(
            "Membership contains an invalid email ID."
        )

    if features is None:
        raise DatasetValidationError(
            (
                f"Email {email_id} has no canonical "
                "feature record."
            )
        )

    feature_email_id = getattr(
        features,
        "email_id",
        None,
    )

    if (
        feature_email_id is not None
        and feature_email_id != email_id
    ):
        raise DatasetValidationError(
            (
                f"Feature record does not belong to "
                f"email {email_id}."
            )
        )

    status = normalize_label(
        getattr(features, "status", None)
    )

    if status != "extracted":
        raise DatasetValidationError(
            (
                f"Email {email_id} does not have "
                "successfully extracted F1-F12 features."
            )
        )

    ground_truth = normalize_label(
        membership.ground_truth
    )

    if ground_truth not in SUPPORTED_GROUND_TRUTH_LABELS:
        raise DatasetValidationError(
            (
                f"Email {email_id} has unsupported "
                f"ground truth: {ground_truth!r}."
            )
        )

    sender_email = getattr(
        features,
        "f1_sender_email",
        None,
    )

    if sender_email is not None and not isinstance(
        sender_email,
        str,
    ):
        raise DatasetValidationError(
            (
                f"Feature f1_sender_email for email "
                f"{email_id} must be a string or null."
            )
        )

    record = DatasetExportRecord(
        email_id=email_id,
        ground_truth=ground_truth,
        f1_sender_email=sender_email,
        f2_known_domain=_read_boolean_feature(
            features,
            "f2_known_domain",
            email_id,
        ),
        f3_message_id=_read_boolean_feature(
            features,
            "f3_message_id",
            email_id,
        ),
        f4_auto_submitted=_read_boolean_feature(
            features,
            "f4_auto_submitted",
            email_id,
        ),
        f5_precedence_bulk=_read_boolean_feature(
            features,
            "f5_precedence_bulk",
            email_id,
        ),
        f6_list_id=_read_boolean_feature(
            features,
            "f6_list_id",
            email_id,
        ),
        f7_x_beenthere=_read_boolean_feature(
            features,
            "f7_x_beenthere",
            email_id,
        ),
        f8_x_anti_abuse=_read_boolean_feature(
            features,
            "f8_x_anti_abuse",
            email_id,
        ),
        f9_keyword_features=_read_integer_feature(
            features,
            "f9_keyword_features",
            email_id,
        ),
        f10_subject_length=_read_integer_feature(
            features,
            "f10_subject_length",
            email_id,
        ),
        f11_emails_per_minute=_read_integer_feature(
            features,
            "f11_emails_per_minute",
            email_id,
        ),
        f12_emails_per_hour=_read_integer_feature(
            features,
            "f12_emails_per_hour",
            email_id,
        ),
        split=normalize_split(membership.split),
    )

    validate_export_record(record)

    return record


# ============================================================
# RECORD VALIDATION
# ============================================================

def validate_export_record(
    record: DatasetExportRecord,
) -> None:
    """Validate one canonical export record."""
    if not isinstance(record.email_id, UUID):
        raise DatasetValidationError(
            "Export record contains an invalid email ID."
        )

    if normalize_label(record.ground_truth) not in (
        SUPPORTED_GROUND_TRUTH_LABELS
    ):
        raise DatasetValidationError(
            (
                f"Email {record.email_id} has invalid "
                "ground truth."
            )
        )

    if record.f1_sender_email is not None:
        if not isinstance(record.f1_sender_email, str):
            raise DatasetValidationError(
                "F1 sender email must be a string or null."
            )

    boolean_fields = (
        "f2_known_domain",
        "f3_message_id",
        "f4_auto_submitted",
        "f5_precedence_bulk",
        "f6_list_id",
        "f7_x_beenthere",
        "f8_x_anti_abuse",
    )

    for field_name in boolean_fields:
        value = getattr(record, field_name)

        if not isinstance(value, bool):
            raise DatasetValidationError(
                f"{field_name} must be a boolean."
            )

    integer_fields = (
        "f9_keyword_features",
        "f10_subject_length",
        "f11_emails_per_minute",
        "f12_emails_per_hour",
    )

    for field_name in integer_fields:
        value = getattr(record, field_name)

        if isinstance(value, bool) or not isinstance(value, int):
            raise DatasetValidationError(
                f"{field_name} must be an integer."
            )

        if value < 0:
            raise DatasetValidationError(
                f"{field_name} cannot be negative."
            )

    normalize_split(record.split)


# ============================================================
# RECORD TO DICTIONARY
# ============================================================

def record_to_dict(
    record: DatasetExportRecord,
) -> dict[str, Any]:
    """Convert a validated record into the canonical flat row."""
    validate_export_record(record)

    return {
        "email_id": str(record.email_id),
        "ground_truth": record.ground_truth,
        "f1_sender_email": record.f1_sender_email,
        "f2_known_domain": record.f2_known_domain,
        "f3_message_id": record.f3_message_id,
        "f4_auto_submitted": record.f4_auto_submitted,
        "f5_precedence_bulk": record.f5_precedence_bulk,
        "f6_list_id": record.f6_list_id,
        "f7_x_beenthere": record.f7_x_beenthere,
        "f8_x_anti_abuse": record.f8_x_anti_abuse,
        "f9_keyword_features": record.f9_keyword_features,
        "f10_subject_length": record.f10_subject_length,
        "f11_emails_per_minute": record.f11_emails_per_minute,
        "f12_emails_per_hour": record.f12_emails_per_hour,
        "split": record.split,
    }


# ============================================================
# MEMBERSHIP VALIDATION
# ============================================================

def validate_export_memberships(
    memberships: Sequence[DatasetMembership],
    *,
    version_id: UUID | None = None,
) -> None:
    """
    Validate membership identity and prevent duplicate
    samples before export.
    """
    seen_email_ids: set[UUID] = set()

    for membership in memberships:
        email_id = membership.email_id

        if not isinstance(email_id, UUID):
            raise DatasetValidationError(
                "Dataset membership has an invalid email ID."
            )

        if email_id in seen_email_ids:
            raise DatasetValidationError(
                (
                    "Dataset Version contains duplicate "
                    f"membership for email {email_id}."
                )
            )

        seen_email_ids.add(email_id)

        membership_version_id = getattr(
            membership,
            "dataset_version_id",
            None,
        )

        if version_id is not None:
            if membership_version_id != version_id:
                raise DatasetValidationError(
                    (
                        "Dataset membership belongs to "
                        "a different Dataset Version."
                    )
                )

        if not normalize_label(membership.ground_truth):
            raise DatasetValidationError(
                f"Email {email_id} has no ground truth."
            )

        normalize_split(membership.split)


# ============================================================
# SPLIT FILTER
# ============================================================

def filter_memberships_by_split(
    memberships: Sequence[DatasetMembership],
    requested_split: str,
) -> list[DatasetMembership]:
    """
    Filter memberships by split.

    'all' preserves the original membership order.
    """
    normalized = normalize_requested_split(
        requested_split
    )

    if normalized == EXPORT_SPLIT_ALL:
        return list(memberships)

    return [
        membership
        for membership in memberships
        if normalize_split(membership.split) == normalized
    ]


# ============================================================
# EXPORT RECORD COLLECTION
# ============================================================

def build_export_records(
    *,
    repository: DatasetRepository,
    memberships: Sequence[DatasetMembership],
) -> list[DatasetExportRecord]:
    """
    Retrieve canonical EmailFeatures and build export records.

    Missing or incomplete feature records cause the export
    to fail rather than silently producing incomplete data.
    """
    records: list[DatasetExportRecord] = []

    for membership in memberships:
        features = repository.get_email_features(
            membership.email_id
        )

        records.append(
            build_export_record(
                membership=membership,
                features=features,
            )
        )

    return records


# ============================================================
# VERSION RECORD COLLECTION
# ============================================================

def collect_version_export_records(
    *,
    repository: DatasetRepository,
    version: DatasetVersion,
    split: str = EXPORT_SPLIT_ALL,
) -> list[DatasetExportRecord]:
    """
    Collect records for a persisted Dataset Version.
    """
    if not isinstance(getattr(version, "id", None), UUID):
        raise DatasetValidationError(
            "Dataset Version must be persisted before export."
        )

    normalized_split = normalize_requested_split(split)

    memberships = repository.list_memberships(
        version.id
    )

    validate_export_memberships(
        memberships,
        version_id=version.id,
    )

    selected_memberships = filter_memberships_by_split(
        memberships,
        normalized_split,
    )

    return build_export_records(
        repository=repository,
        memberships=selected_memberships,
    )


# ============================================================
# ROW CONVERSION
# ============================================================

def records_to_rows(
    records: Sequence[DatasetExportRecord],
) -> list[dict[str, Any]]:
    """Convert validated records into ordered export rows."""
    return [
        record_to_dict(record)
        for record in records
    ]


# ============================================================
# CSV EXPORT
# ============================================================

def export_csv(
    records: Sequence[DatasetExportRecord],
) -> str:
    """
    Serialize records to CSV.

    CSV column order is fixed by EXPORT_COLUMNS.
    """
    output = io.StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=list(EXPORT_COLUMNS),
        extrasaction="raise",
        lineterminator="\n",
    )

    writer.writeheader()

    for record in records:
        writer.writerow(record_to_dict(record))

    return output.getvalue()


# ============================================================
# JSON EXPORT
# ============================================================

def export_json(
    records: Sequence[DatasetExportRecord],
) -> str:
    """Serialize records to a JSON array."""
    rows = records_to_rows(records)

    return json.dumps(
        rows,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )


# ============================================================
# GENERIC EXPORT
# ============================================================

def export_records(
    records: Sequence[DatasetExportRecord],
    *,
    export_format: str,
) -> tuple[str, str]:
    """
    Serialize records into CSV or JSON.

    Returns:
        (content, content_type)
    """
    normalized_format = normalize_format(export_format)

    if normalized_format == EXPORT_FORMAT_CSV:
        return (
            export_csv(records),
            "text/csv; charset=utf-8",
        )

    if normalized_format == EXPORT_FORMAT_JSON:
        return (
            export_json(records),
            "application/json; charset=utf-8",
        )

    raise DatasetValidationError(
        f"Unsupported export format: {normalized_format}."
    )


# ============================================================
# VERSION EXPORT
# ============================================================

def export_dataset_version(
    *,
    repository: DatasetRepository,
    version: DatasetVersion,
    export_format: str,
    split: str = EXPORT_SPLIT_ALL,
) -> tuple[str, str, int]:
    """
    Export a Dataset Version in CSV or JSON format.

    Returns:
        content
        content_type
        exported_sample_count
    """
    normalized_format = normalize_format(export_format)
    normalized_split = normalize_requested_split(split)

    records = collect_version_export_records(
        repository=repository,
        version=version,
        split=normalized_split,
    )

    content, content_type = export_records(
        records,
        export_format=normalized_format,
    )

    return content, content_type, len(records)


# ============================================================
# FILENAME
# ============================================================

def _safe_filename_component(value: str) -> str:
    """Convert a user-provided name into a safe filename part."""
    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        value.strip(),
    ).strip("_")

    return cleaned or "dataset_version"


def build_export_filename(
    *,
    version: DatasetVersion,
    export_format: str,
    split: str = EXPORT_SPLIT_ALL,
) -> str:
    """Build a deterministic filename for a version export."""
    normalized_format = normalize_format(export_format)
    normalized_split = normalize_requested_split(split)

    safe_name = _safe_filename_component(version.name)

    return (
        f"{safe_name}"
        f"_v{version.version_number}"
        f"_{normalized_split}"
        f".{normalized_format}"
    )


# ============================================================
# CONTENT TYPE
# ============================================================

def get_export_content_type(
    export_format: str,
) -> str:
    """Return the HTTP content type for an export format."""
    normalized = normalize_format(export_format)

    if normalized == EXPORT_FORMAT_CSV:
        return "text/csv; charset=utf-8"

    return "application/json; charset=utf-8"


# ============================================================
# EXPORT METADATA
# ============================================================

def build_export_metadata(
    *,
    version: DatasetVersion,
    export_format: str,
    split: str,
    sample_count: int,
) -> dict[str, Any]:
    """
    Build metadata for API responses, audit records,
    and frontend download handling.
    """
    normalized_format = normalize_format(export_format)
    normalized_split = normalize_requested_split(split)

    if isinstance(sample_count, bool) or not isinstance(sample_count, int):
        raise DatasetValidationError(
            "Export sample count must be an integer."
        )

    if sample_count < 0:
        raise DatasetValidationError(
            "Export sample count cannot be negative."
        )

    return {
        "dataset_version_id": str(version.id),
        "version_number": version.version_number,
        "format": normalized_format,
        "split": normalized_split,
        "sample_count": sample_count,
        "filename": build_export_filename(
            version=version,
            export_format=normalized_format,
            split=normalized_split,
        ),
        "content_type": get_export_content_type(
            normalized_format
        ),
        "columns": list(EXPORT_COLUMNS),
    }


# ============================================================
# EXPORT SCHEMA
# ============================================================

EXPORT_SCHEMA = (
    {
        "field": "email_id",
        "description": "Canonical email identifier",
        "data_type": "string",
    },
    {
        "field": "ground_truth",
        "description": "Dataset ground-truth label",
        "data_type": "string",
    },
    {
        "field": "f1_sender_email",
        "description": "F1 Sender Email",
        "data_type": "string",
    },
    {
        "field": "f2_known_domain",
        "description": "F2 Known Domain Indicator",
        "data_type": "boolean",
    },
    {
        "field": "f3_message_id",
        "description": "F3 Message-ID Presence",
        "data_type": "boolean",
    },
    {
        "field": "f4_auto_submitted",
        "description": "F4 Auto-Submitted Header",
        "data_type": "boolean",
    },
    {
        "field": "f5_precedence_bulk",
        "description": "F5 Precedence Bulk Indicator",
        "data_type": "boolean",
    },
    {
        "field": "f6_list_id",
        "description": "F6 List-Id Header",
        "data_type": "boolean",
    },
    {
        "field": "f7_x_beenthere",
        "description": "F7 X-BeenThere Header",
        "data_type": "boolean",
    },
    {
        "field": "f8_x_anti_abuse",
        "description": "F8 X-Anti-Abuse Header",
        "data_type": "boolean",
    },
    {
        "field": "f9_keyword_features",
        "description": "F9 Keyword-Based Content Features",
        "data_type": "integer",
    },
    {
        "field": "f10_subject_length",
        "description": "F10 Subject Length",
        "data_type": "integer",
    },
    {
        "field": "f11_emails_per_minute",
        "description": "F11 Emails Per Minute",
        "data_type": "integer",
    },
    {
        "field": "f12_emails_per_hour",
        "description": "F12 Emails Per Hour",
        "data_type": "integer",
    },
    {
        "field": "split",
        "description": "Train/Validation/Test split",
        "data_type": "string",
    },
)


def get_export_columns() -> tuple[str, ...]:
    """Return the canonical column order."""
    return EXPORT_COLUMNS


def get_export_schema() -> list[dict[str, str]]:
    """Return a copy of the export schema metadata."""
    return [dict(field) for field in EXPORT_SCHEMA]


# ============================================================
# EXPORT STATISTICS
# ============================================================

def calculate_export_statistics(
    records: Sequence[DatasetExportRecord],
) -> dict[str, int]:
    """
    Calculate class and split counts for exported records.

    No prediction, risk, or threat score is calculated.
    """
    normal_count = 0
    bombing_count = 0

    train_count = 0
    validation_count = 0
    test_count = 0

    for record in records:
        validate_export_record(record)

        label = normalize_label(record.ground_truth)

        if label == "normal":
            normal_count += 1
        elif label == "bombing":
            bombing_count += 1

        split = normalize_split(record.split)

        if split == EXPORT_SPLIT_TRAIN:
            train_count += 1
        elif split == EXPORT_SPLIT_VALIDATION:
            validation_count += 1
        elif split == EXPORT_SPLIT_TEST:
            test_count += 1

    return {
        "total": len(records),
        "normal": normal_count,
        "bombing": bombing_count,
        "train": train_count,
        "validation": validation_count,
        "test": test_count,
    }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EXPORT_FORMAT_CSV",
    "EXPORT_FORMAT_JSON",
    "EXPORT_SPLIT_ALL",
    "EXPORT_SPLIT_TRAIN",
    "EXPORT_SPLIT_VALIDATION",
    "EXPORT_SPLIT_TEST",
    "SUPPORTED_EXPORT_FORMATS",
    "SUPPORTED_EXPORT_SPLITS",
    "EXPORT_COLUMNS",
    "EXPORT_SCHEMA",
    "DatasetExportRecord",
    "normalize_label",
    "normalize_split",
    "normalize_requested_split",
    "normalize_format",
    "serialize_value",
    "build_export_record",
    "validate_export_record",
    "validate_export_memberships",
    "filter_memberships_by_split",
    "build_export_records",
    "collect_version_export_records",
    "records_to_rows",
    "export_csv",
    "export_json",
    "export_records",
    "export_dataset_version",
    "build_export_filename",
    "get_export_content_type",
    "build_export_metadata",
    "get_export_columns",
    "get_export_schema",
    "calculate_export_statistics",
]