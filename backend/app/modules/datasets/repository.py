from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.datasets.models import (
    Dataset,
    DatasetMembership,
    DatasetSample,
    DatasetValidationIssue,
    DatasetValidationRun,
    DatasetVersion,
    ValidationIssueSeverity,
    ValidationRunStatus,
)
from app.modules.datasets.schemas import DatasetWorkspaceFilters
from app.modules.datasets.selectors import (
    apply_dataset_workspace_filters,
    build_dataset_source_query,
    build_eligible_email_ids_query,
    build_matching_email_ids_query,
    build_single_email_eligibility_query,
    dataset_eligibility_condition,
)
from app.modules.emails.models import Email
from app.modules.features.models import EmailFeatures
from app.modules.parsing.models import ParsedEmail


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100

DEFAULT_SPLIT_COUNTS = {
    "train": 0,
    "validation": 0,
    "test": 0,
}

DEFAULT_GROUND_TRUTH_COUNTS = {
    "normal": 0,
    "bombing": 0,
}

DEFAULT_ISSUE_COUNTS = {
    "error": 0,
    "warning": 0,
    "info": 0,
}


# ============================================================
# REPOSITORY
# ============================================================

class DatasetRepository:
    """
    Database access layer for Module 05 — Dataset Management.

    Responsibilities:
    - Query eligible emails for the Dataset Workspace.
    - Apply workspace filters and pagination.
    - Resolve complete filtered selections.
    - Read canonical Email, ParsedEmail, and EmailFeatures.
    - Create and retrieve Dataset records.
    - Update dataset metadata.
    - Add and remove dataset-level email memberships.
    - Retrieve paginated dataset samples.
    - Create and retrieve DatasetVersion records.
    - Persist and retrieve version-level memberships.
    - Create and retrieve validation runs.
    - Persist and retrieve validation issues.
    - Update dataset-version validation snapshots.
    - Provide database reads for validation and report export.

    Architectural boundaries:
    - Does not calculate F1-F12.
    - Does not duplicate email content or feature values.
    - Does not perform ML prediction.
    - Does not calculate risk or threat levels.
    - Does not calculate train/validation/test splits.
    - Does not implement validation business rules.
    - Does not serialize CSV or JSON exports.
    - Does not delete canonical Email records.

    Transaction ownership:
    - Repository methods flush but do not commit automatically,
      except when commit() is explicitly called.
    - The service or request layer owns transaction boundaries.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_page(page: int) -> int:
        """Return a valid one-based page number."""
        return max(int(page), DEFAULT_PAGE)

    @staticmethod
    def _normalize_page_size(page_size: int) -> int:
        """Return a page size between 1 and MAX_PAGE_SIZE."""
        return min(max(int(page_size), 1), MAX_PAGE_SIZE)

    @staticmethod
    def _deduplicate_ids(
        email_ids: Sequence[UUID],
    ) -> list[UUID]:
        """Remove duplicate IDs while preserving input order."""
        return list(dict.fromkeys(email_ids))

    @staticmethod
    def _normalize_enum_value(value: Any) -> str:
        """Normalize an enum or string value."""
        if hasattr(value, "value"):
            value = value.value

        return str(value).strip().lower()

    @classmethod
    def _normalize_split(cls, value: Any) -> str:
        """Normalize a split value to its canonical key."""
        split = cls._normalize_enum_value(value)

        aliases = {
            "training": "train",
            "testing": "test",
            "valid": "validation",
        }

        return aliases.get(split, split)

    # ========================================================
    # WORKSPACE
    # ========================================================

    def list_workspace(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> tuple[list[Email], int]:
        """
        Return a paginated list of eligible workspace emails.

        Eligibility is defined by selectors.py.
        The returned total is calculated without pagination.
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        statement = build_dataset_source_query(filters=filters)

        statement = (
            statement
            .order_by(
                Email.received_at.desc(),
                Email.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())
        total = self.count_workspace(filters=filters)

        return items, total

    def count_workspace(
        self,
        *,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> int:
        """Count all eligible emails matching workspace filters."""
        statement = (
            select(func.count(func.distinct(Email.id)))
            .select_from(Email)
            .join(
                ParsedEmail,
                ParsedEmail.email_id == Email.id,
            )
            .join(
                EmailFeatures,
                EmailFeatures.email_id == Email.id,
            )
            .where(dataset_eligibility_condition())
        )

        statement = apply_dataset_workspace_filters(
            statement,
            filters=filters,
        )

        return int(self.db.scalar(statement) or 0)

    # ========================================================
    # FILTERED SELECTION
    # ========================================================

    def list_matching_email_ids(
        self,
        *,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> list[UUID]:
        """
        Return every eligible email ID matching the filters.

        Pagination is intentionally not applied. This supports
        Select All Matching across all workspace pages.
        """
        statement = build_matching_email_ids_query(
            filters=filters,
        )

        return list(self.db.scalars(statement).all())

    def list_eligible_email_ids(
        self,
        email_ids: Sequence[UUID],
    ) -> list[UUID]:
        """
        Return supplied IDs that currently satisfy the
        canonical Dataset eligibility condition.
        """
        normalized_ids = self._deduplicate_ids(email_ids)

        if not normalized_ids:
            return []

        statement = build_eligible_email_ids_query(
            normalized_ids,
        )

        return list(self.db.scalars(statement).all())

    def is_email_eligible(self, email_id: UUID) -> bool:
        """Return whether one email is currently eligible."""
        statement = build_single_email_eligibility_query(
            email_id,
        )

        return self.db.scalar(statement) is not None

    # ========================================================
    # CANONICAL EMAIL READS
    # ========================================================

    def get_email(self, email_id: UUID) -> Email | None:
        """Return a canonical Module 02 Email record."""
        statement = select(Email).where(
            Email.id == email_id,
        )

        return self.db.scalar(statement)

    def get_emails_by_ids(
        self,
        email_ids: Sequence[UUID],
    ) -> list[Email]:
        """Return canonical Email records for supplied IDs."""
        normalized_ids = self._deduplicate_ids(email_ids)

        if not normalized_ids:
            return []

        statement = (
            select(Email)
            .where(Email.id.in_(normalized_ids))
            .order_by(
                Email.received_at.desc(),
                Email.id.desc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def get_parsed_email(
        self,
        email_id: UUID,
    ) -> ParsedEmail | None:
        """Return the canonical Module 03 ParsedEmail record."""
        statement = select(ParsedEmail).where(
            ParsedEmail.email_id == email_id,
        )

        return self.db.scalar(statement)

    def get_email_features(
        self,
        email_id: UUID,
    ) -> EmailFeatures | None:
        """Read canonical Module 04 F1-F12 values."""
        statement = select(EmailFeatures).where(
            EmailFeatures.email_id == email_id,
        )

        return self.db.scalar(statement)

    def get_email_features_by_ids(
        self,
        email_ids: Sequence[UUID],
    ) -> list[EmailFeatures]:
        """
        Return canonical EmailFeatures records for multiple emails.

        This bulk query supports validation of F1-F12 without
        issuing one database query per email.
        """
        normalized_ids = self._deduplicate_ids(email_ids)

        if not normalized_ids:
            return []

        statement = (
            select(EmailFeatures)
            .where(EmailFeatures.email_id.in_(normalized_ids))
            .order_by(EmailFeatures.email_id.asc())
        )

        return list(self.db.scalars(statement).all())

    # ========================================================
    # DATASET READ
    # ========================================================

    def get_dataset(
        self,
        dataset_id: UUID,
    ) -> Dataset | None:
        """Return one logical Dataset."""
        statement = select(Dataset).where(
            Dataset.id == dataset_id,
        )

        return self.db.scalar(statement)

    def list_datasets(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[Dataset], int]:
        """Return a paginated list of logical datasets."""
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        statement = (
            select(Dataset)
            .order_by(
                Dataset.created_at.desc(),
                Dataset.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())
        total = self.count_datasets()

        return items, total

    def count_datasets(self) -> int:
        """Return the total number of logical datasets."""
        statement = select(func.count(Dataset.id))

        return int(self.db.scalar(statement) or 0)

    # ========================================================
    # DATASET CREATE / UPDATE
    # ========================================================

    def create_dataset(self, dataset: Dataset) -> Dataset:
        """Add a Dataset to the current transaction."""
        self.db.add(dataset)
        self.db.flush()

        return dataset

    def update_dataset(self, dataset: Dataset) -> Dataset:
        """Flush changes to an existing Dataset."""
        self.db.add(dataset)
        self.db.flush()

        return dataset

    # ========================================================
    # DATASET SAMPLES
    # ========================================================

    def create_dataset_samples(
        self,
        samples: Sequence[DatasetSample],
    ) -> list[DatasetSample]:
        """
        Persist the selected email population for a dataset.

        Each row stores a dataset-level selection and its
        ground-truth/schema snapshot. It does not duplicate
        canonical email content or feature values.
        """
        items = list(samples)

        if not items:
            return []

        self.db.add_all(items)
        self.db.flush()

        return items

    def get_dataset_sample(
        self,
        *,
        dataset_id: UUID,
        email_id: UUID,
    ) -> DatasetSample | None:
        """Return one selected email for a dataset."""
        statement = (
            select(DatasetSample)
            .where(
                DatasetSample.dataset_id == dataset_id,
                DatasetSample.email_id == email_id,
            )
        )

        return self.db.scalar(statement)

    def list_dataset_samples(
        self,
        dataset_id: UUID,
    ) -> list[DatasetSample]:
        """Return all selected samples for a dataset."""
        statement = (
            select(DatasetSample)
            .where(
                DatasetSample.dataset_id == dataset_id,
            )
            .order_by(
                DatasetSample.created_at.asc(),
                DatasetSample.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def list_dataset_samples_paginated(
        self,
        *,
        dataset_id: UUID,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
    ) -> tuple[list[DatasetSample], int]:
        """
        Return a paginated list of samples for one dataset.

        Search is intentionally limited to the canonical email
        subject and sender fields. Dataset membership remains
        the source of the dataset's email population.
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = [
            DatasetSample.dataset_id == dataset_id,
        ]

        normalized_search = (
            search.strip()
            if search is not None
            else None
        )

        if normalized_search:
            pattern = f"%{normalized_search}%"

            matching_email_ids = (
                select(Email.id)
                .where(
                    Email.id == DatasetSample.email_id,
                    (
                        Email.subject.ilike(pattern)
                        | Email.sender.ilike(pattern)
                    ),
                )
                .exists()
            )

            conditions.append(matching_email_ids)

        statement = (
            select(DatasetSample)
            .where(*conditions)
            .order_by(
                DatasetSample.created_at.asc(),
                DatasetSample.id.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())

        total_statement = (
            select(func.count(DatasetSample.id))
            .where(*conditions)
        )

        total = int(self.db.scalar(total_statement) or 0)

        return items, total

    def list_dataset_email_ids(
        self,
        dataset_id: UUID,
    ) -> list[UUID]:
        """Return all selected email IDs for a dataset."""
        statement = (
            select(DatasetSample.email_id)
            .where(
                DatasetSample.dataset_id == dataset_id,
            )
            .order_by(
                DatasetSample.created_at.asc(),
                DatasetSample.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def list_existing_dataset_email_ids(
        self,
        *,
        dataset_id: UUID,
        email_ids: Sequence[UUID],
    ) -> list[UUID]:
        """
        Return supplied email IDs already selected in a dataset.

        This is useful for avoiding duplicate DatasetSample rows
        when adding emails.
        """
        normalized_ids = self._deduplicate_ids(email_ids)

        if not normalized_ids:
            return []

        statement = (
            select(DatasetSample.email_id)
            .where(
                DatasetSample.dataset_id == dataset_id,
                DatasetSample.email_id.in_(normalized_ids),
            )
            .order_by(
                DatasetSample.created_at.asc(),
                DatasetSample.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def count_dataset_samples(
        self,
        dataset_id: UUID,
    ) -> int:
        """Count selected samples belonging to a dataset."""
        statement = (
            select(func.count(DatasetSample.id))
            .where(
                DatasetSample.dataset_id == dataset_id,
            )
        )

        return int(self.db.scalar(statement) or 0)

    def count_dataset_samples_by_ground_truth(
        self,
        dataset_id: UUID,
    ) -> dict[str, int]:
        """Count selected samples by their stored ground truth."""
        statement = (
            select(
                DatasetSample.ground_truth,
                func.count(DatasetSample.id),
            )
            .where(
                DatasetSample.dataset_id == dataset_id,
            )
            .group_by(DatasetSample.ground_truth)
        )

        rows = self.db.execute(statement).all()
        result = dict(DEFAULT_GROUND_TRUTH_COUNTS)

        for label, count in rows:
            normalized_label = self._normalize_enum_value(label)

            if normalized_label in result:
                result[normalized_label] = int(count)

        return result

    def delete_dataset_samples(
        self,
        *,
        dataset_id: UUID,
        email_ids: Sequence[UUID],
    ) -> int:
        """
        Remove selected email memberships from one dataset only.

        This deletes DatasetSample rows, not canonical Email
        records or memberships in other datasets.

        Existing DatasetVersion and DatasetMembership snapshots
        are intentionally untouched.
        """
        normalized_ids = self._deduplicate_ids(email_ids)

        if not normalized_ids:
            return 0

        statement = (
            delete(DatasetSample)
            .where(
                DatasetSample.dataset_id == dataset_id,
                DatasetSample.email_id.in_(normalized_ids),
            )
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        self.db.flush()

        return int(result.rowcount or 0)

    # ========================================================
    # DATASET VERSION CREATE / READ
    # ========================================================

    def create_dataset_version(
        self,
        version: DatasetVersion,
    ) -> DatasetVersion:
        """Add a DatasetVersion to the current transaction."""
        self.db.add(version)
        self.db.flush()

        return version

    def get_dataset_version(
        self,
        version_id: UUID,
    ) -> DatasetVersion | None:
        """Return one DatasetVersion."""
        statement = select(DatasetVersion).where(
            DatasetVersion.id == version_id,
        )

        return self.db.scalar(statement)

    def list_dataset_versions(
        self,
        *,
        dataset_id: UUID | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[DatasetVersion], int]:
        """Return a paginated list of versions."""
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = []

        if dataset_id is not None:
            conditions.append(
                DatasetVersion.dataset_id == dataset_id,
            )

        statement = (
            select(DatasetVersion)
            .where(*conditions)
            .order_by(
                DatasetVersion.created_at.desc(),
                DatasetVersion.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())

        total_statement = (
            select(func.count(DatasetVersion.id))
            .where(*conditions)
        )

        total = int(self.db.scalar(total_statement) or 0)

        return items, total

    def count_dataset_versions(
        self,
        dataset_id: UUID,
    ) -> int:
        """Count versions belonging to one dataset."""
        statement = (
            select(func.count(DatasetVersion.id))
            .where(
                DatasetVersion.dataset_id == dataset_id,
            )
        )

        return int(self.db.scalar(statement) or 0)

    # ========================================================
    # VERSION MEMBERSHIPS
    # ========================================================

    def create_memberships(
        self,
        memberships: Sequence[DatasetMembership],
    ) -> list[DatasetMembership]:
        """Persist version-level split membership records."""
        items = list(memberships)

        if not items:
            return []

        self.db.add_all(items)
        self.db.flush()

        return items

    def list_memberships(
        self,
        version_id: UUID,
    ) -> list[DatasetMembership]:
        """Return all memberships belonging to a version."""
        statement = (
            select(DatasetMembership)
            .where(
                DatasetMembership.dataset_version_id == version_id,
            )
            .order_by(
                DatasetMembership.created_at.asc(),
                DatasetMembership.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def get_membership(
        self,
        *,
        version_id: UUID,
        email_id: UUID,
    ) -> DatasetMembership | None:
        """Return one version/email membership, if present."""
        statement = (
            select(DatasetMembership)
            .where(
                DatasetMembership.dataset_version_id == version_id,
                DatasetMembership.email_id == email_id,
            )
        )

        return self.db.scalar(statement)

    def count_memberships(
        self,
        version_id: UUID,
    ) -> int:
        """Count membership rows for one version."""
        statement = (
            select(func.count(DatasetMembership.id))
            .where(
                DatasetMembership.dataset_version_id == version_id,
            )
        )

        return int(self.db.scalar(statement) or 0)

    def count_memberships_by_split(
        self,
        version_id: UUID,
    ) -> dict[str, int]:
        """Return train, validation, and test membership counts."""
        statement = (
            select(
                DatasetMembership.split,
                func.count(DatasetMembership.id),
            )
            .where(
                DatasetMembership.dataset_version_id == version_id,
            )
            .group_by(DatasetMembership.split)
        )

        rows = self.db.execute(statement).all()
        result = dict(DEFAULT_SPLIT_COUNTS)

        for split_value, count in rows:
            split = self._normalize_split(split_value)

            if split in result:
                result[split] = int(count)

        return result

    # ========================================================
    # VERSION EMAIL IDS
    # ========================================================

    def list_version_email_ids(
        self,
        version_id: UUID,
    ) -> list[UUID]:
        """Return all email IDs assigned to a version."""
        statement = (
            select(DatasetMembership.email_id)
            .where(
                DatasetMembership.dataset_version_id == version_id,
            )
            .order_by(
                DatasetMembership.created_at.asc(),
                DatasetMembership.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def list_version_email_ids_by_split(
        self,
        *,
        version_id: UUID,
        split: Any,
    ) -> list[UUID]:
        """Return email IDs assigned to one version split."""
        normalized_split = self._normalize_split(split)

        statement = (
            select(DatasetMembership.email_id)
            .where(
                DatasetMembership.dataset_version_id == version_id,
                func.lower(DatasetMembership.split) == normalized_split,
            )
            .order_by(
                DatasetMembership.created_at.asc(),
                DatasetMembership.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def count_version_samples(
        self,
        version_id: UUID,
    ) -> int:
        """Count distinct email samples in a version."""
        statement = (
            select(
                func.count(
                    func.distinct(DatasetMembership.email_id)
                )
            )
            .where(
                DatasetMembership.dataset_version_id == version_id,
            )
        )

        return int(self.db.scalar(statement) or 0)

    # ========================================================
    # DATASET COUNTS
    # ========================================================

    def count_dataset_ground_truth(
        self,
        dataset_id: UUID,
    ) -> dict[str, int]:
        """Count dataset-level selected samples by ground truth."""
        return self.count_dataset_samples_by_ground_truth(
            dataset_id,
        )

    # ========================================================
    # VALIDATION RUNS — CREATE
    # ========================================================

    def create_run(
        self,
        run: DatasetValidationRun,
    ) -> DatasetValidationRun:
        """Add a validation run to the current transaction."""
        self.db.add(run)
        self.db.flush()
        return run

    # ========================================================
    # VALIDATION RUNS — READ
    # ========================================================

    def get_run(
        self,
        run_id: UUID,
    ) -> DatasetValidationRun | None:
        """Retrieve a validation run by its ID."""
        statement = select(DatasetValidationRun).where(
            DatasetValidationRun.id == run_id,
        )
        return self.db.scalar(statement)

    def get_run_for_version(
        self,
        *,
        run_id: UUID,
        version_id: UUID,
    ) -> DatasetValidationRun | None:
        """Retrieve a run only if it belongs to the given version."""
        statement = select(DatasetValidationRun).where(
            DatasetValidationRun.id == run_id,
            DatasetValidationRun.dataset_version_id == version_id,
        )
        return self.db.scalar(statement)

    def list_runs(
        self,
        *,
        version_id: UUID,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: str | None = None,
    ) -> tuple[list[DatasetValidationRun], int]:
        """Return paginated validation history, newest first."""
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = [
            DatasetValidationRun.dataset_version_id == version_id,
        ]

        if status is not None:
            conditions.append(
                func.lower(DatasetValidationRun.status)
                == self._normalize_enum_value(status)
            )

        statement = (
            select(DatasetValidationRun)
            .where(*conditions)
            .order_by(
                DatasetValidationRun.started_at.desc(),
                DatasetValidationRun.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())

        count_statement = (
            select(func.count(DatasetValidationRun.id))
            .where(*conditions)
        )
        total = int(self.db.scalar(count_statement) or 0)

        return items, total

    def get_latest_run(
        self,
        version_id: UUID,
    ) -> DatasetValidationRun | None:
        """Return the most recently started validation run."""
        statement = (
            select(DatasetValidationRun)
            .where(
                DatasetValidationRun.dataset_version_id == version_id,
            )
            .order_by(
                DatasetValidationRun.started_at.desc(),
                DatasetValidationRun.id.desc(),
            )
            .limit(1)
        )
        return self.db.scalar(statement)

    def count_runs(
        self,
        version_id: UUID,
        *,
        status: str | None = None,
    ) -> int:
        """Count validation runs for a version."""
        conditions = [
            DatasetValidationRun.dataset_version_id == version_id,
        ]

        if status is not None:
            conditions.append(
                func.lower(DatasetValidationRun.status)
                == self._normalize_enum_value(status)
            )

        statement = (
            select(func.count(DatasetValidationRun.id))
            .where(*conditions)
        )
        return int(self.db.scalar(statement) or 0)

    # ========================================================
    # VALIDATION RUNS — UPDATE
    # ========================================================

    def update_run(
        self,
        run: DatasetValidationRun,
    ) -> DatasetValidationRun:
        """Flush changes to an existing validation run."""
        self.db.add(run)
        self.db.flush()
        return run

    def complete_run(
        self,
        *,
        run: DatasetValidationRun,
        overall_status: str,
        total_checks: int,
        passed_checks: int,
        warning_checks: int,
        failed_checks: int,
        total_samples: int,
        error_count: int,
        warning_count: int,
        summary: dict[str, Any],
        completed_at: datetime,
    ) -> DatasetValidationRun:
        """
        Persist the final result of a validation run.

        The service calculates the status and result counts.
        """
        run.status = ValidationRunStatus.COMPLETED.value
        run.overall_status = self._normalize_enum_value(
            overall_status,
        )

        run.total_checks = total_checks
        run.passed_checks = passed_checks
        run.warning_checks = warning_checks
        run.failed_checks = failed_checks

        run.total_samples = total_samples
        run.error_count = error_count
        run.warning_count = warning_count

        run.summary = summary
        run.completed_at = completed_at

        self.db.add(run)
        self.db.flush()
        return run

    def fail_run(
        self,
        *,
        run: DatasetValidationRun,
        summary: dict[str, Any] | None = None,
        completed_at: datetime,
    ) -> DatasetValidationRun:
        """Mark a validation run as failed."""
        run.status = ValidationRunStatus.FAILED.value
        run.overall_status = "failed"
        run.summary = summary or {}
        run.completed_at = completed_at

        self.db.add(run)
        self.db.flush()
        return run

    # ========================================================
    # VALIDATION ISSUES — CREATE
    # ========================================================

    def create_issue(
        self,
        issue: DatasetValidationIssue,
    ) -> DatasetValidationIssue:
        """Persist one validation issue."""
        self.db.add(issue)
        self.db.flush()
        return issue

    def create_issues(
        self,
        issues: Sequence[DatasetValidationIssue],
    ) -> list[DatasetValidationIssue]:
        """Persist multiple validation issues in one operation."""
        items = list(issues)

        if not items:
            return []

        self.db.add_all(items)
        self.db.flush()
        return items

    # ========================================================
    # VALIDATION ISSUES — READ
    # ========================================================

    def get_issue(
        self,
        issue_id: UUID,
    ) -> DatasetValidationIssue | None:
        """Retrieve one validation issue by ID."""
        statement = select(DatasetValidationIssue).where(
            DatasetValidationIssue.id == issue_id,
        )
        return self.db.scalar(statement)

    def get_issue_for_run(
        self,
        *,
        issue_id: UUID,
        run_id: UUID,
    ) -> DatasetValidationIssue | None:
        """Retrieve an issue only if it belongs to the given run."""
        statement = select(DatasetValidationIssue).where(
            DatasetValidationIssue.id == issue_id,
            DatasetValidationIssue.validation_run_id == run_id,
        )
        return self.db.scalar(statement)

    def list_issues(
        self,
        *,
        run_id: UUID,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        severity: str | None = None,
        check_code: str | None = None,
    ) -> tuple[list[DatasetValidationIssue], int]:
        """Return paginated issues with optional filters."""
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = [
            DatasetValidationIssue.validation_run_id == run_id,
        ]

        if severity is not None:
            conditions.append(
                func.lower(DatasetValidationIssue.severity)
                == self._normalize_enum_value(severity)
            )

        if check_code is not None:
            normalized_check_code = check_code.strip()
            if normalized_check_code:
                conditions.append(
                    DatasetValidationIssue.check_code
                    == normalized_check_code
                )

        statement = (
            select(DatasetValidationIssue)
            .where(*conditions)
            .order_by(
                DatasetValidationIssue.created_at.asc(),
                DatasetValidationIssue.id.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())

        count_statement = (
            select(func.count(DatasetValidationIssue.id))
            .where(*conditions)
        )
        total = int(self.db.scalar(count_statement) or 0)

        return items, total

    def list_all_issues(
        self,
        run_id: UUID,
    ) -> list[DatasetValidationIssue]:
        """Return every issue for a validation run."""
        statement = (
            select(DatasetValidationIssue)
            .where(
                DatasetValidationIssue.validation_run_id == run_id,
            )
            .order_by(
                DatasetValidationIssue.created_at.asc(),
                DatasetValidationIssue.id.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    # ========================================================
    # VALIDATION ISSUES — COUNTS
    # ========================================================

    def count_issues(
        self,
        run_id: UUID,
        *,
        severity: str | None = None,
    ) -> int:
        """Count issues for a run, optionally by severity."""
        conditions = [
            DatasetValidationIssue.validation_run_id == run_id,
        ]

        if severity is not None:
            conditions.append(
                func.lower(DatasetValidationIssue.severity)
                == self._normalize_enum_value(severity)
            )

        statement = (
            select(func.count(DatasetValidationIssue.id))
            .where(*conditions)
        )
        return int(self.db.scalar(statement) or 0)

    def count_issues_by_severity(
        self,
        run_id: UUID,
    ) -> dict[str, int]:
        """Return issue counts grouped by severity."""
        result = dict(DEFAULT_ISSUE_COUNTS)

        statement = (
            select(
                DatasetValidationIssue.severity,
                func.count(DatasetValidationIssue.id),
            )
            .where(
                DatasetValidationIssue.validation_run_id == run_id,
            )
            .group_by(DatasetValidationIssue.severity)
        )

        for severity, count in self.db.execute(statement).all():
            normalized = self._normalize_enum_value(severity)

            if normalized in result:
                result[normalized] = int(count)

        return result

    # ========================================================
    # DATASET VERSION — VALIDATION SNAPSHOT
    # ========================================================

    def get_version(
        self,
        version_id: UUID,
    ) -> DatasetVersion | None:
        """Retrieve a dataset version."""
        statement = select(DatasetVersion).where(
            DatasetVersion.id == version_id,
        )
        return self.db.scalar(statement)

    def update_version_validation(
        self,
        *,
        version: DatasetVersion,
        validation_passed: bool,
        validation_summary: dict[str, Any],
        validated_at: datetime,
    ) -> DatasetVersion:
        """
        Update the version's latest validation snapshot.

        Historical run details remain in the validation
        run and issue tables.
        """
        version.validation_passed = validation_passed
        version.validation_summary = validation_summary
        version.validated_at = validated_at

        self.db.add(version)
        self.db.flush()
        return version

    # ========================================================
    # REPORT DATA ACCESS
    # ========================================================

    def get_report_data(
        self,
        *,
        version_id: UUID,
        run_id: UUID,
    ) -> tuple[
        Dataset | None,
        DatasetVersion | None,
        DatasetValidationRun | None,
        list[DatasetValidationIssue],
    ]:
        """
        Retrieve all database records required to build a report.

        The run must belong to the requested version.
        Serialization and report formatting belong to the
        service/export layer.
        """
        version = self.get_dataset_version(version_id)

        if version is None:
            return None, None, None, []

        run = self.get_run_for_version(
            run_id=run_id,
            version_id=version_id,
        )

        if run is None:
            return None, version, None, []

        dataset = self.get_dataset(version.dataset_id)
        issues = self.list_all_issues(run.id)

        return dataset, version, run, issues

    # ========================================================
    # TRANSACTION HELPERS
    # ========================================================

    def flush(self) -> None:
        """Flush pending changes without committing."""
        self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.db.rollback()


__all__ = [
    "DatasetRepository",
]