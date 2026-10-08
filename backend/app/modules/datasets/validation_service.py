from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Callable
from uuid import UUID

from app.modules.datasets.models import (
    DatasetVersion,
    DatasetValidationIssue as ValidationIssueModel,
    DatasetValidationRun,
    ValidationIssueSeverity,
    ValidationRunStatus,
)
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.validators import (
    DatasetValidationError,
    ValidationResult,
    validate_class_distribution,
    validate_duplicate_samples,
    validate_feature_schema_compatibility,
    validate_invalid_feature_values,
    validate_label_consistency,
    validate_missing_feature_values,
    validate_split_consistency,
    validate_version_integrity,
)
from app.modules.datasets.versioning import mark_version_validated


class ValidationService:
    """
    Application service for comprehensive Dataset Version validation.

    Responsibilities:
        - Execute all dataset validation checks.
        - Persist validation runs and issues.
        - Update the version validation snapshot.
        - Retrieve validation results and history.
        - Provide validation summaries.

    This service does not:
        - Modify canonical Email records.
        - Modify DatasetSample records.
        - Modify immutable DatasetVersion memberships.
        - Perform ML predictions or model evaluation.

    Transaction ownership:
        Repository methods flush changes.
        The caller or request lifecycle owns commit/rollback.
    """

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 30
    MAX_PAGE_SIZE = 100

    VALIDATION_CHECKS = (
        {
            "code": "VERSION_INTEGRITY",
            "name": "Dataset Version Integrity",
        },
        {
            "code": "MISSING_FEATURE_VALUES",
            "name": "Missing Feature Values",
        },
        {
            "code": "LABEL_CONSISTENCY",
            "name": "Label Consistency",
        },
        {
            "code": "DUPLICATE_SAMPLES",
            "name": "Duplicate Samples",
        },
        {
            "code": "FEATURE_SCHEMA_COMPATIBILITY",
            "name": "Feature Schema Compatibility",
        },
        {
            "code": "CLASS_DISTRIBUTION",
            "name": "Class Distribution",
        },
        {
            "code": "INVALID_FEATURE_VALUES",
            "name": "Invalid Feature Values",
        },
        {
            "code": "SPLIT_CONSISTENCY",
            "name": "Split Consistency",
        },
    )

    FEATURE_FIELDS = (
        "f1_sender_email",
        "f2_has_subject",
        "f3_has_body",
        "f4_has_attachments",
        "f5_is_html",
        "f6_has_links",
        "f7_has_images",
        "f8_has_headers",
        "f9_subject_length",
        "f10_body_length",
        "f11_link_count",
        "f12_attachment_count",
    )

    def __init__(
        self,
        repository: DatasetRepository,
        *,
        imbalance_threshold: float | None = None,
    ) -> None:
        self.repository = repository
        self.imbalance_threshold = imbalance_threshold

    # ========================================================
    # VALIDATION EXECUTION
    # ========================================================

    def validate_version(
        self,
        version_id: UUID,
    ) -> DatasetValidationRun:
        """
        Execute and persist all validation checks for one version.

        Each check is evaluated independently. A failed check does
        not prevent subsequent checks from running.

        Unexpected execution errors fail the run and are propagated.
        """
        version = self._require_version(version_id)
        memberships = self.repository.list_memberships(version_id)

        email_ids = [
            membership.email_id
            for membership in memberships
        ]

        feature_records = (
            self.repository.get_email_features_by_ids(email_ids)
            if email_ids
            else []
        )

        features_by_email_id = {
            record.email_id: record
            for record in feature_records
        }

        run = self._create_running_run(
            version=version,
            total_samples=len(memberships),
        )

        try:
            results = self._execute_checks(
                version=version,
                memberships=memberships,
                feature_records=feature_records,
                features_by_email_id=features_by_email_id,
            )

            summary = self._build_summary(
                results=results,
                version=version,
                total_samples=len(memberships),
            )

            issues = self._build_issue_models(
                run_id=run.id,
                results=results,
            )

            if issues:
                self.repository.create_issues(issues)

            completed_at = self._now()

            self._update_version_snapshot(
                version=version,
                passed=summary["passed"],
                summary=summary,
                validated_at=completed_at,
            )

            self._complete_run(
                run=run,
                summary=summary,
                completed_at=completed_at,
            )

            self.repository.flush()

            return self._require_run(run.id)

        except Exception as exc:
            self._fail_run(
                run=run,
                error=exc,
            )
            raise

    def _execute_checks(
        self,
        *,
        version: DatasetVersion,
        memberships: list[Any],
        feature_records: list[Any],
        features_by_email_id: dict[UUID, Any],
    ) -> list[tuple[dict[str, str], ValidationResult]]:
        """Run all validation checks and return their results."""

        missing_feature_records = self._build_feature_validation_records(
            memberships=memberships,
            features_by_email_id=features_by_email_id,
        )

        schema = self._normalize_feature_schema(
            version.feature_schema,
        )

        checks: list[
            tuple[dict[str, str], Callable[[], ValidationResult]]
        ] = [
            (
                self.VALIDATION_CHECKS[0],
                lambda: validate_version_integrity(
                    version=version,
                    memberships=memberships,
                ),
            ),
            (
                self.VALIDATION_CHECKS[1],
                lambda: validate_missing_feature_values(
                    missing_feature_records,
                ),
            ),
            (
                self.VALIDATION_CHECKS[2],
                lambda: validate_label_consistency(
                    memberships,
                ),
            ),
            (
                self.VALIDATION_CHECKS[3],
                lambda: validate_duplicate_samples(
                    memberships,
                ),
            ),
            (
                self.VALIDATION_CHECKS[4],
                lambda: validate_feature_schema_compatibility(
                    schema,
                    memberships=memberships,
                ),
            ),
            (
                self.VALIDATION_CHECKS[5],
                lambda: validate_class_distribution(
                    memberships,
                    imbalance_threshold=self.imbalance_threshold,
                ),
            ),
            (
                self.VALIDATION_CHECKS[6],
                lambda: validate_invalid_feature_values(
                    feature_records,
                ),
            ),
            (
                self.VALIDATION_CHECKS[7],
                lambda: validate_split_consistency(
                    memberships,
                    expected_total=len(memberships),
                ),
            ),
        ]

        results: list[
            tuple[dict[str, str], ValidationResult]
        ] = []

        for check, validator in checks:
            result = validator()
            results.append((check, result))

        return results

    @classmethod
    def _build_feature_validation_records(
        cls,
        *,
        memberships: list[Any],
        features_by_email_id: dict[UUID, Any],
    ) -> list[Any]:
        """
        Create a record for each membership.

        Missing feature rows are represented as records with null
        F1-F12 values, allowing the missing-value validator to
        detect missing feature data.

        Invalid-value validation receives only persisted records.
        """
        records: list[Any] = []

        for membership in memberships:
            email_id = membership.email_id
            feature_record = features_by_email_id.get(email_id)

            if feature_record is not None:
                records.append(feature_record)
                continue

            missing_record = SimpleNamespace(
                email_id=email_id,
                features=None,
            )

            for field in cls.FEATURE_FIELDS:
                setattr(missing_record, field, None)

            records.append(missing_record)

        return records

    @staticmethod
    def _normalize_feature_schema(
        schema: Any,
    ) -> Any:
        """
        Adapt the persisted JSON schema to the attribute-based
        structure expected by the schema validator.
        """
        if not isinstance(schema, dict):
            return schema

        normalized_features = schema.get("features", [])

        if isinstance(normalized_features, list):
            normalized_features = [
                (
                    SimpleNamespace(**item)
                    if isinstance(item, dict)
                    else item
                )
                for item in normalized_features
            ]

        return SimpleNamespace(
            **{
                **schema,
                "features": normalized_features,
            }
        )

    # ========================================================
    # RUN LIFECYCLE
    # ========================================================

    def _create_running_run(
        self,
        *,
        version: DatasetVersion,
        total_samples: int,
    ) -> DatasetValidationRun:
        """Create and flush a RUNNING validation run."""

        run = DatasetValidationRun(
            dataset_version_id=version.id,
            status=self._enum_value(
                ValidationRunStatus.RUNNING,
            ),
            overall_status=None,
            total_checks=0,
            total_samples=max(int(total_samples), 0),
            error_count=0,
            warning_count=0,
            passed_checks=0,
            warning_checks=0,
            failed_checks=0,
            summary={},
            started_at=self._now(),
        )

        run = self.repository.create_run(run)
        self.repository.flush()

        return run

    def _update_version_snapshot(
        self,
        *,
        version: DatasetVersion,
        passed: bool,
        summary: dict[str, Any],
        validated_at: datetime,
    ) -> None:
        """Update the version's validation state and summary."""

        mark_version_validated(
            version,
            valid=passed,
            summary=summary,
        )

        self.repository.update_version_validation(
            version=version,
            validation_passed=passed,
            validation_summary=summary,
            validated_at=validated_at,
        )

    def _complete_run(
        self,
        *,
        run: DatasetValidationRun,
        summary: dict[str, Any],
        completed_at: datetime,
    ) -> None:
        """Persist the completed validation result."""

        self.repository.complete_run(
            run=run,
            overall_status=summary["overall_status"],
            total_checks=summary["total_checks"],
            passed_checks=summary["passed_checks"],
            warning_checks=summary["warning_checks"],
            failed_checks=summary["failed_checks"],
            total_samples=summary["total_samples"],
            error_count=summary["errors"],
            warning_count=summary["warnings"],
            summary=summary,
            completed_at=completed_at,
        )

    def _fail_run(
        self,
        *,
        run: DatasetValidationRun,
        error: Exception,
    ) -> None:
        """Mark an unexpected validation execution failure."""

        self.repository.fail_run(
            run=run,
            summary={
                "overall_status": "failed",
                "execution_error": str(error),
            },
            completed_at=self._now(),
        )
        self.repository.flush()

    # ========================================================
    # VALIDATION HISTORY
    # ========================================================

    def get_validation_run(
        self,
        run_id: UUID,
    ) -> DatasetValidationRun:
        """Retrieve one validation run by ID."""

        run = self.repository.get_run(run_id)

        if run is None:
            raise DatasetValidationError(
                f"Validation run {run_id} was not found."
            )

        return run

    def list_validation_runs(
        self,
        version_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[DatasetValidationRun], int]:
        """Return paginated validation history for a version."""

        self._require_version(version_id)

        return self.repository.list_runs(
            version_id=version_id,
            page=self._normalize_page(page),
            page_size=self._normalize_page_size(page_size),
        )

    def get_latest_validation_run(
        self,
        version_id: UUID,
    ) -> DatasetValidationRun | None:
        """Return the latest validation run for a version."""

        self._require_version(version_id)
        return self.repository.get_latest_run(version_id)

    def count_validation_runs(
        self,
        version_id: UUID,
    ) -> int:
        """Count validation runs for a version."""

        self._require_version(version_id)
        return self.repository.count_runs(version_id)

    # ========================================================
    # VALIDATION ISSUES
    # ========================================================

    def list_validation_issues(
        self,
        run_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        severity: str | None = None,
        check_code: str | None = None,
    ) -> tuple[list[ValidationIssueModel], int]:
        """Return paginated issues for a validation run."""

        self.get_validation_run(run_id)

        return self.repository.list_issues(
            run_id=run_id,
            page=self._normalize_page(page),
            page_size=self._normalize_page_size(page_size),
            severity=self._normalize_severity(severity),
            check_code=self._normalize_check_code(check_code),
        )

    def count_validation_issues(
        self,
        run_id: UUID,
        *,
        severity: str | None = None,
    ) -> int:
        """Count issues for a validation run."""

        self.get_validation_run(run_id)

        return self.repository.count_issues(
            run_id=run_id,
            severity=self._normalize_severity(severity),
        )

    def get_issue_severity_counts(
        self,
        run_id: UUID,
    ) -> dict[str, int]:
        """Return issue counts grouped by severity."""

        self.get_validation_run(run_id)

        counts = self.repository.count_issues_by_severity(run_id)

        return {
            self._enum_value(key): int(value)
            for key, value in counts.items()
        }

    # ========================================================
    # VALIDATION SUMMARY
    # ========================================================

    def get_validation_summary(
        self,
        version_id: UUID,
    ) -> dict[str, Any]:
        """Return the latest validation summary for a version."""

        version = self._require_version(version_id)
        latest_run = self.repository.get_latest_run(version_id)

        if latest_run is None:
            return {
                "dataset_id": str(version.dataset_id),
                "version_id": str(version.id),
                "has_validation": False,
                "validation_passed": bool(version.validation_passed),
                "validation_summary": version.validation_summary or {},
                "latest_run": None,
            }

        return {
            "dataset_id": str(version.dataset_id),
            "version_id": str(version.id),
            "has_validation": True,
            "validation_passed": bool(version.validation_passed),
            "validation_summary": version.validation_summary or {},
            "latest_run": self._run_to_dict(latest_run),
        }

    # ========================================================
    # TRANSACTION HELPERS
    # ========================================================

    def commit(self) -> None:
        """Commit the current transaction."""
        self.repository.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.repository.rollback()

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _require_version(
        self,
        version_id: UUID,
    ) -> DatasetVersion:
        """Retrieve a version or raise a domain error."""

        version = self.repository.get_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        return version

    def _require_run(
        self,
        run_id: UUID,
    ) -> DatasetValidationRun:
        """Reload a validation run or raise a domain error."""

        run = self.repository.get_run(run_id)

        if run is None:
            raise DatasetValidationError(
                f"Validation run {run_id} could not be reloaded."
            )

        return run

    @staticmethod
    def _now() -> datetime:
        """Return the current UTC timestamp."""
        return datetime.now(timezone.utc)

    @staticmethod
    def _enum_value(value: Any) -> str:
        """Normalize enum or string values."""
        return str(
            getattr(value, "value", value)
        ).strip().lower()

    @staticmethod
    def _normalize_page(page: int) -> int:
        """Normalize a page number."""
        return max(int(page), 1)

    @classmethod
    def _normalize_page_size(
        cls,
        page_size: int,
    ) -> int:
        """Normalize a page size within the supported limit."""
        return min(
            max(int(page_size), 1),
            cls.MAX_PAGE_SIZE,
        )

    @staticmethod
    def _normalize_severity(
        severity: str | None,
    ) -> str | None:
        """Validate and normalize an issue severity filter."""

        if severity is None:
            return None

        value = severity.strip().lower()

        allowed = {
            str(getattr(item, "value", item)).strip().lower()
            for item in ValidationIssueSeverity
        }

        if value not in allowed:
            raise DatasetValidationError(
                "Unsupported validation issue severity: "
                f"{severity}"
            )

        return value

    @staticmethod
    def _normalize_check_code(
        check_code: str | None,
    ) -> str | None:
        """Normalize an optional check code filter."""

        if check_code is None:
            return None

        return check_code.strip() or None

    # ========================================================
    # RESULT NORMALIZATION
    # ========================================================

    @staticmethod
    def _result_status(
        result: ValidationResult,
    ) -> str:
        """Determine the normalized status of a validation result."""

        if not result.passed:
            return "failed"

        if result.warnings:
            return "warning"

        return "passed"

    @staticmethod
    def _affected_email_ids(
        details: dict[str, Any],
    ) -> list[str]:
        """Extract unique affected email IDs from validator details."""

        candidates: list[Any] = []

        for key in (
            "affected_email_ids",
            "email_ids",
            "affected_records",
            "records",
        ):
            value = details.get(key)

            if isinstance(value, (list, tuple, set)):
                candidates.extend(value)

        email_ids: list[str] = []

        for item in candidates:
            if isinstance(item, dict):
                email_id = (
                    item.get("email_id")
                    or item.get("id")
                )
            else:
                email_id = getattr(
                    item,
                    "email_id",
                    item if isinstance(item, (UUID, str)) else None,
                )

            if email_id is not None:
                normalized = str(email_id)
                if normalized not in email_ids:
                    email_ids.append(normalized)

        return email_ids

    @classmethod
    def _result_issues(
        cls,
        *,
        check: dict[str, str],
        result: ValidationResult,
    ) -> list[dict[str, Any]]:
        """Convert a validation result into issue summaries."""

        details = dict(result.details or {})
        email_ids = cls._affected_email_ids(details)

        issues: list[dict[str, Any]] = []

        for message in result.errors:
            issues.append(
                {
                    "check_code": check["code"],
                    "check_name": check["name"],
                    "severity": "error",
                    "title": str(message),
                    "details": str(message),
                    "affected_count": len(email_ids),
                    "affected_email_ids": email_ids,
                    "metadata": details,
                }
            )

        for message in result.warnings:
            issues.append(
                {
                    "check_code": check["code"],
                    "check_name": check["name"],
                    "severity": "warning",
                    "title": str(message),
                    "details": str(message),
                    "affected_count": len(email_ids),
                    "affected_email_ids": email_ids,
                    "metadata": details,
                }
            )

        return issues

    # ========================================================
    # SUMMARY BUILDER
    # ========================================================

    @classmethod
    def _build_summary(
        cls,
        *,
        results: list[tuple[dict[str, str], ValidationResult]],
        version: DatasetVersion,
        total_samples: int,
    ) -> dict[str, Any]:
        """Build a JSON-compatible summary for all validation checks."""

        checks: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []

        for check_definition, result in results:
            status = cls._result_status(result)
            details = dict(result.details or {})
            check_issues = cls._result_issues(
                check=check_definition,
                result=result,
            )

            issues.extend(check_issues)

            checks.append(
                {
                    "code": check_definition["code"],
                    "name": check_definition["name"],
                    "status": status,
                    "passed": status != "failed",
                    "severity": (
                        "error"
                        if status == "failed"
                        else "warning"
                        if status == "warning"
                        else "info"
                    ),
                    "affected_samples": len(
                        cls._affected_email_ids(details)
                    ),
                    "message": cls._check_message(
                        name=check_definition["name"],
                        status=status,
                    ),
                    "errors": list(result.errors),
                    "warnings": list(result.warnings),
                    "details": details,
                }
            )

        passed_checks = sum(
            check["status"] == "passed"
            for check in checks
        )
        warning_checks = sum(
            check["status"] == "warning"
            for check in checks
        )
        failed_checks = sum(
            check["status"] == "failed"
            for check in checks
        )

        error_count = sum(
            len(result.errors)
            for _, result in results
        )
        warning_count = sum(
            len(result.warnings)
            for _, result in results
        )

        if failed_checks:
            overall_status = "failed"
        elif warning_checks:
            overall_status = "warning"
        else:
            overall_status = "passed"

        return {
            "passed": overall_status == "passed",
            "overall_status": overall_status,
            "total_samples": max(int(total_samples), 0),
            "normal_samples": max(
                int(getattr(version, "normal_count", 0) or 0),
                0,
            ),
            "bombing_samples": max(
                int(getattr(version, "bombing_count", 0) or 0),
                0,
            ),
            "total_checks": len(checks),
            "passed_checks": passed_checks,
            "warning_checks": warning_checks,
            "failed_checks": failed_checks,
            "errors": error_count,
            "warnings": warning_count,
            "checks": checks,
            "issues": issues,
        }

    @staticmethod
    def _check_message(
        *,
        name: str,
        status: str,
    ) -> str:
        """Build a concise check message."""

        if status == "failed":
            return f"{name} validation failed."

        if status == "warning":
            return f"{name} validation completed with warnings."

        return f"{name} validation passed."

    # ========================================================
    # ISSUE MODEL BUILDER
    # ========================================================

    @classmethod
    def _build_issue_models(
        cls,
        *,
        run_id: UUID,
        results: list[tuple[dict[str, str], ValidationResult]],
    ) -> list[ValidationIssueModel]:
        """Convert all check results into persisted issue models."""

        issues: list[ValidationIssueModel] = []

        for check, result in results:
            for issue in cls._result_issues(
                check=check,
                result=result,
            ):
                issues.append(
                    ValidationIssueModel(
                        validation_run_id=run_id,
                        check_code=issue["check_code"],
                        check_name=issue["check_name"],
                        severity=issue["severity"],
                        title=issue["title"],
                        details=issue["details"],
                        affected_count=issue["affected_count"],
                        affected_email_ids=issue[
                            "affected_email_ids"
                        ],
                        metadata_json=issue["metadata"],
                    )
                )

        return issues

    # ========================================================
    # RUN SERIALIZER
    # ========================================================

    @classmethod
    def _run_to_dict(
        cls,
        run: DatasetValidationRun,
    ) -> dict[str, Any]:
        """Serialize a validation run into JSON-compatible data."""

        return {
            "id": str(run.id),
            "dataset_version_id": str(run.dataset_version_id),
            "status": cls._enum_value(run.status),
            "overall_status": (
                cls._enum_value(run.overall_status)
                if run.overall_status is not None
                else None
            ),
            "total_checks": int(run.total_checks or 0),
            "total_samples": int(run.total_samples or 0),
            "error_count": int(run.error_count or 0),
            "warning_count": int(run.warning_count or 0),
            "passed_checks": int(run.passed_checks or 0),
            "warning_checks": int(run.warning_checks or 0),
            "failed_checks": int(run.failed_checks or 0),
            "summary": run.summary or {},
            "policy_version": run.policy_version,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        }


# ============================================================
# FACTORY
# ============================================================

def create_validation_service(
    repository: DatasetRepository,
    *,
    imbalance_threshold: float | None = None,
) -> ValidationService:
    """Create a ValidationService instance."""

    return ValidationService(
        repository=repository,
        imbalance_threshold=imbalance_threshold,
    )


__all__ = [
    "ValidationService",
    "create_validation_service",
]