from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.datasets.models import (
    DatasetValidationIssue,
    DatasetValidationRun,
    DatasetVersion,
    ValidationIssueSeverity,
    ValidationRunStatus,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# REPOSITORY
# ============================================================

class ValidationRepository:
    """
    Database access layer for dataset validation.

    Responsibilities:
    - Create and retrieve validation runs.
    - Update validation run status and results.
    - List validation history for a dataset version.
    - Create and retrieve validation issues.
    - Filter and paginate validation issues.
    - Count checks and issues.
    - Update the validation snapshot on DatasetVersion.

    Architectural boundaries:
    - Does not execute validation checks.
    - Does not determine validation outcomes.
    - Does not calculate F1-F12.
    - Does not modify dataset memberships.
    - Does not commit transactions automatically.

    Transaction ownership:
    - Repository methods flush changes when necessary.
    - The service or request layer owns commit and rollback.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_page(page: int) -> int:
        """Ensure the page number is at least one."""
        return max(int(page), DEFAULT_PAGE)

    @staticmethod
    def _normalize_page_size(page_size: int) -> int:
        """Limit the requested page size."""
        return min(max(int(page_size), 1), MAX_PAGE_SIZE)

    @staticmethod
    def _normalize_enum(value: Any) -> str:
        """Convert enum or string values to lowercase strings."""
        if hasattr(value, "value"):
            value = value.value

        return str(value).strip().lower()

    # ========================================================
    # VALIDATION RUNS — CREATE
    # ========================================================

    def create_run(
        self,
        run: DatasetValidationRun,
    ) -> DatasetValidationRun:
        """
        Add a validation run to the current transaction.

        The caller should initialize the run with status
        RUNNING before validation starts.
        """
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
        """
        Return paginated validation history for a version.

        Results are ordered newest first.
        An optional status filter can restrict the results.
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = [
            DatasetValidationRun.dataset_version_id == version_id,
        ]

        if status is not None:
            conditions.append(
                func.lower(DatasetValidationRun.status)
                == self._normalize_enum(status)
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
                == self._normalize_enum(status)
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
        completed_at: Any,
    ) -> DatasetValidationRun:
        """
        Persist the final result of a validation run.

        The service is responsible for calculating the
        overall status and all result counts.
        """
        run.status = ValidationRunStatus.COMPLETED.value
        run.overall_status = self._normalize_enum(overall_status)

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
        completed_at: Any,
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
        """
        Return paginated issues for a validation run.

        Optional filters:
        - severity: error, warning, or info
        - check_code: exact validation check identifier
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        conditions = [
            DatasetValidationIssue.validation_run_id == run_id,
        ]

        if severity is not None:
            conditions.append(
                func.lower(DatasetValidationIssue.severity)
                == self._normalize_enum(severity)
            )

        if check_code is not None:
            conditions.append(
                DatasetValidationIssue.check_code == check_code.strip()
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
                == self._normalize_enum(severity)
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
        result = {
            ValidationIssueSeverity.ERROR.value: 0,
            ValidationIssueSeverity.WARNING.value: 0,
            ValidationIssueSeverity.INFO.value: 0,
        }

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
            normalized = self._normalize_enum(severity)

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
        validated_at: Any,
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
    "ValidationRepository",
]