
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ============================================================
# CONSTANTS
# ============================================================

FEATURE_SCHEMA_VERSION = "F1-F12"

DEFAULT_TRAINING_PERCENTAGE = 70
DEFAULT_VALIDATION_PERCENTAGE = 15
DEFAULT_TESTING_PERCENTAGE = 15
DEFAULT_RANDOM_SEED = 42

DEFAULT_VALIDATION_POLICY_VERSION = "1.0"


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# ============================================================
# ENUMS
# ============================================================


class DatasetStatus(str, Enum):
    """Lifecycle status of a logical dataset."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class DatasetVersionStatus(str, Enum):
    """Lifecycle status of an immutable dataset version."""

    CREATING = "creating"
    READY = "ready"
    VALIDATED = "validated"
    INVALID = "invalid"


class DatasetSplit(str, Enum):
    """Partition assigned to an email in a dataset version."""

    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class ValidationRunStatus(str, Enum):
    """Execution status of a validation run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationOverallStatus(str, Enum):
    """Final result of a completed validation run."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ValidationIssueSeverity(str, Enum):
    """Severity assigned to a validation issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ============================================================
# DATASET
# ============================================================


class Dataset(Base):
    """
    Logical dataset containing explicitly selected emails.

    Stores dataset metadata and sample counters only.
    Email content and F1-F12 values remain in their
    canonical source tables.

    DatasetSample stores the selected email population.
    DatasetVersion stores immutable version snapshots.
    """

    __tablename__ = "datasets"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DatasetStatus.ACTIVE.value,
    )

    feature_schema: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    normal_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    bombing_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    __table_args__ = (
        Index(
            "ix_datasets_name",
            "name",
        ),
        Index(
            "ix_datasets_status",
            "status",
        ),
    )


# ============================================================
# DATASET SAMPLE
# ============================================================


class DatasetSample(Base):
    """
    Persisted email selection belonging to a logical dataset.

    This is the dataset's source population. It stores the
    ground-truth snapshot and feature schema version, but
    does not duplicate email content or feature values.

    Each version creates its own DatasetMembership records.
    """

    __tablename__ = "dataset_samples"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE",
            name="fk_dataset_samples_dataset_id",
        ),
        nullable=False,
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "emails.id",
            ondelete="RESTRICT",
            name="fk_dataset_samples_email_id",
        ),
        nullable=False,
    )

    ground_truth: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    feature_schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FEATURE_SCHEMA_VERSION,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "email_id",
            name="uq_dataset_sample_dataset_email",
        ),
        CheckConstraint(
            "ground_truth IN ('normal', 'bombing')",
            name="ck_dataset_samples_ground_truth",
        ),
        Index(
            "ix_dataset_samples_dataset_id",
            "dataset_id",
        ),
        Index(
            "ix_dataset_samples_email_id",
            "email_id",
        ),
    )


# ============================================================
# DATASET VERSION
# ============================================================


class DatasetVersion(Base):
    """
    Immutable snapshot of a dataset's selected population.

    A version freezes:
      - selected email population
      - ground-truth snapshots
      - feature schema metadata
      - split percentages
      - random seed
      - stratification setting
      - resulting split counts
      - validation metadata

    A changed configuration should produce a new version.

    Validation execution history is stored separately in
    DatasetValidationRun and DatasetValidationIssue.
    """

    __tablename__ = "dataset_versions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "datasets.id",
            ondelete="CASCADE",
            name="fk_dataset_versions_dataset_id",
        ),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Retained because the current database schema
    # requires this column to be NOT NULL.
    valid_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    normal_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    bombing_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DatasetVersionStatus.CREATING.value,
    )

    validation_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    # --------------------------------------------------------
    # Split configuration
    # --------------------------------------------------------

    training_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_TRAINING_PERCENTAGE,
    )

    validation_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_VALIDATION_PERCENTAGE,
    )

    testing_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_TESTING_PERCENTAGE,
    )

    random_seed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_RANDOM_SEED,
    )

    stratified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # --------------------------------------------------------
    # Split result counts
    # --------------------------------------------------------

    training_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    validation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    testing_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # --------------------------------------------------------
    # Validation snapshot
    # --------------------------------------------------------

    validation_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    feature_schema: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "version_number",
            name="uq_dataset_version_number",
        ),
        CheckConstraint(
            "training_percentage >= 0 "
            "AND training_percentage <= 100",
            name="ck_dataset_version_training_percentage",
        ),
        CheckConstraint(
            "validation_percentage >= 0 "
            "AND validation_percentage <= 100",
            name="ck_dataset_version_validation_percentage",
        ),
        CheckConstraint(
            "testing_percentage >= 0 "
            "AND testing_percentage <= 100",
            name="ck_dataset_version_testing_percentage",
        ),
        CheckConstraint(
            "training_percentage + validation_percentage "
            "+ testing_percentage = 100",
            name="ck_dataset_version_split_percentages",
        ),
        Index(
            "ix_dataset_versions_dataset_id",
            "dataset_id",
        ),
        Index(
            "ix_dataset_versions_status",
            "status",
        ),
        Index(
            "ix_dataset_versions_dataset_status",
            "dataset_id",
            "status",
        ),
    )


# ============================================================
# DATASET MEMBERSHIP
# ============================================================


class DatasetMembership(Base):
    """
    Immutable assignment of an email to a version and split.

    The email references the canonical Module 02 record.
    F1-F12 remain in Module 04's email_features table.

    Membership stores version-specific ground truth,
    schema version, and split assignment.
    """

    __tablename__ = "dataset_memberships"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "dataset_versions.id",
            ondelete="CASCADE",
            name="fk_dataset_memberships_version_id",
        ),
        nullable=False,
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "emails.id",
            ondelete="RESTRICT",
            name="fk_dataset_memberships_email_id",
        ),
        nullable=False,
    )

    split: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    ground_truth: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    feature_schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FEATURE_SCHEMA_VERSION,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_version_id",
            "email_id",
            name="uq_dataset_membership_version_email",
        ),
        CheckConstraint(
            "split IN ('train', 'validation', 'test')",
            name="ck_dataset_memberships_split",
        ),
        CheckConstraint(
            "ground_truth IN ('normal', 'bombing')",
            name="ck_dataset_memberships_ground_truth",
        ),
        Index(
            "ix_dataset_memberships_version_id",
            "dataset_version_id",
        ),
        Index(
            "ix_dataset_memberships_email_id",
            "email_id",
        ),
        Index(
            "ix_dataset_memberships_version_split",
            "dataset_version_id",
            "split",
        ),
    )


# ============================================================
# DATASET VALIDATION RUN
# ============================================================


class DatasetValidationRun(Base):
    """
    One record of a validation execution.

    Multiple runs may belong to the same dataset version.
    Run results are stored independently of the immutable
    version population and split configuration.
    """

    __tablename__ = "dataset_validation_runs"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "dataset_versions.id",
            ondelete="CASCADE",
            name="fk_validation_runs_version_id",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ValidationRunStatus.RUNNING.value,
    )

    overall_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    total_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    passed_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    warning_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    summary: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    policy_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DEFAULT_VALIDATION_POLICY_VERSION,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="ck_validation_runs_status",
        ),
        CheckConstraint(
            "overall_status IS NULL OR "
            "overall_status IN ('passed', 'warning', 'failed')",
            name="ck_validation_runs_overall_status",
        ),
        CheckConstraint(
            "total_checks >= 0 AND "
            "passed_checks >= 0 AND "
            "warning_checks >= 0 AND "
            "failed_checks >= 0",
            name="ck_validation_runs_check_counts",
        ),
        CheckConstraint(
            "total_samples >= 0 AND "
            "error_count >= 0 AND "
            "warning_count >= 0",
            name="ck_validation_runs_issue_counts",
        ),
        Index(
            "ix_validation_runs_version_id",
            "dataset_version_id",
        ),
        Index(
            "ix_validation_runs_status",
            "status",
        ),
        Index(
            "ix_validation_runs_started_at",
            "started_at",
        ),
        Index(
            "ix_validation_runs_version_started",
            "dataset_version_id",
            "started_at",
        ),
    )


# ============================================================
# DATASET VALIDATION ISSUE
# ============================================================


class DatasetValidationIssue(Base):
    """
    An issue discovered during a validation run.

    Stores issue details and optional affected email IDs.
    Does not modify canonical emails, dataset samples,
    or immutable version memberships.
    """

    __tablename__ = "dataset_validation_issues"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    validation_run_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "dataset_validation_runs.id",
            ondelete="CASCADE",
            name="fk_validation_issues_run_id",
        ),
        nullable=False,
    )

    check_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    check_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    affected_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    affected_email_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('error', 'warning', 'info')",
            name="ck_validation_issues_severity",
        ),
        CheckConstraint(
            "affected_count >= 0",
            name="ck_validation_issues_affected_count",
        ),
        Index(
            "ix_validation_issues_run_id",
            "validation_run_id",
        ),
        Index(
            "ix_validation_issues_severity",
            "severity",
        ),
        Index(
            "ix_validation_issues_run_severity",
            "validation_run_id",
            "severity",
        ),
        Index(
            "ix_validation_issues_check_code",
            "check_code",
        ),
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "Dataset",
    "DatasetSample",
    "DatasetVersion",
    "DatasetMembership",
    "DatasetValidationRun",
    "DatasetValidationIssue",
    "DatasetStatus",
    "DatasetVersionStatus",
    "DatasetSplit",
    "ValidationRunStatus",
    "ValidationOverallStatus",
    "ValidationIssueSeverity",
    "FEATURE_SCHEMA_VERSION",
    "DEFAULT_TRAINING_PERCENTAGE",
    "DEFAULT_VALIDATION_PERCENTAGE",
    "DEFAULT_TESTING_PERCENTAGE",
    "DEFAULT_RANDOM_SEED",
    "DEFAULT_VALIDATION_POLICY_VERSION",
    "utc_now",
]
