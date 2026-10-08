from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.modules.datasets.models import DatasetVersion
from app.modules.datasets.repository import DatasetRepository
from app.modules.preprocessing.engine.pipeline import (
    PreprocessingPipeline,
)
from app.modules.preprocessing.models import PreprocessingRun
from app.modules.preprocessing.repository import PreprocessingRepository
from app.modules.preprocessing.storage.artifact_store import ArtifactStore
from app.modules.preprocessing.config.validator import FEATURE_TYPES


class PreprocessingServiceError(Exception):
    """Base exception for preprocessing service errors."""


class DatasetVersionNotFoundError(PreprocessingServiceError):
    """Raised when a dataset version does not exist."""


class DatasetVersionNotValidatedError(PreprocessingServiceError):
    """Raised when a dataset version has not passed validation."""


class DatasetSplitError(PreprocessingServiceError):
    """Raised when dataset split membership is inconsistent."""


class PreprocessingConfigurationError(PreprocessingServiceError):
    """Raised when preprocessing configuration is invalid."""


class PreprocessingRunNotFoundError(PreprocessingServiceError):
    """Raised when a preprocessing run does not exist."""


class PreprocessingInputError(PreprocessingServiceError):
    """Raised when feature rows cannot be loaded for a run."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PreprocessingDatasetSelection:
    """Validated dataset version and its existing split membership."""

    version: DatasetVersion
    training_email_ids: list[UUID]
    validation_email_ids: list[UUID]
    testing_email_ids: list[UUID]

    @property
    def sample_count(self) -> int:
        return (
            len(self.training_email_ids)
            + len(self.validation_email_ids)
            + len(self.testing_email_ids)
        )

    @property
    def split_counts(self) -> dict[str, int]:
        return {
            "train": len(self.training_email_ids),
            "validation": len(self.validation_email_ids),
            "test": len(self.testing_email_ids),
        }


class PreprocessingService:
    """
    Application service for Module 06 — Preprocessing Pipeline.

    Responsibilities:
        - Select validated dataset versions.
        - Read immutable dataset split assignments.
        - Validate and snapshot preprocessing configuration.
        - Create and retrieve preprocessing runs.
        - Execute a pending run through the preprocessing engine.
        - Persist run status, artifact metadata and result metadata.

    Architectural boundaries:
        - Module 05 owns datasets, versions, and split assignments.
        - Module 04 owns canonical F1-F12 feature records.
        - This service does not create dataset versions or modify splits.
        - Data transformations belong to the preprocessing engine.
        - Large artifacts belong in file storage, not database rows.
    """

    DEFAULT_FEATURE_ORDER = tuple(f"F{i}" for i in range(1, 13))

    # Engine feature name -> EmailFeatures column name.
    FEATURE_COLUMNS = {
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

    def __init__(
        self,
        preprocessing_repository: PreprocessingRepository,
        dataset_repository: DatasetRepository,
    ) -> None:
        self.repository = preprocessing_repository
        self.dataset_repository = dataset_repository

    # ========================================================
    # DATASET VERSION SELECTION
    # ========================================================

    def get_dataset_selection(
        self,
        version_id: UUID,
    ) -> PreprocessingDatasetSelection:
        """
        Retrieve a validated dataset version and its existing splits.

        The version must have passed Module 05 validation.
        Split assignments are read-only.
        """
        version = self.dataset_repository.get_dataset_version(
            version_id
        )

        if version is None:
            raise DatasetVersionNotFoundError(
                f"Dataset version {version_id} was not found."
            )

        version_status = getattr(
            version.status,
            "value",
            version.status,
        )

        if (
            version_status != "validated"
            or not version.validation_passed
        ):
            raise DatasetVersionNotValidatedError(
                "Only dataset versions that have passed validation "
                "can be used for preprocessing."
            )

        training_ids = (
            self.dataset_repository.list_version_email_ids_by_split(
                version_id=version_id,
                split="train",
            )
        )
        validation_ids = (
            self.dataset_repository.list_version_email_ids_by_split(
                version_id=version_id,
                split="validation",
            )
        )
        testing_ids = (
            self.dataset_repository.list_version_email_ids_by_split(
                version_id=version_id,
                split="test",
            )
        )

        split_counts = {
            "train": len(training_ids),
            "validation": len(validation_ids),
            "test": len(testing_ids),
        }

        total = sum(split_counts.values())

        if total != version.sample_count:
            raise DatasetSplitError(
                "Dataset split membership count does not match "
                f"the version sample count: expected "
                f"{version.sample_count}, found {total}."
            )

        if not training_ids:
            raise DatasetSplitError(
                "The selected dataset version has no training samples."
            )

        return PreprocessingDatasetSelection(
            version=version,
            training_email_ids=training_ids,
            validation_email_ids=validation_ids,
            testing_email_ids=testing_ids,
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    @staticmethod
    def validate_configuration(
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate the basic configuration structure.

        Detailed option and feature-type validation is handled
        by the dedicated configuration validator.
        """
        if not isinstance(config, dict):
            raise PreprocessingConfigurationError(
                "Preprocessing configuration must be an object."
            )

        if not config:
            raise PreprocessingConfigurationError(
                "Preprocessing configuration cannot be empty."
            )

        return dict(config)

    # ========================================================
    # RUN MANAGEMENT
    # ========================================================

    def create_run(
        self,
        *,
        version_id: UUID,
        config: dict[str, Any],
    ) -> PreprocessingRun:
        """
        Create a pending preprocessing run.

        This method does not execute transformations. It stores
        a configuration snapshot and associates the run with an
        already validated dataset version. Use execute_run() to
        actually process a pending run.
        """
        selection = self.get_dataset_selection(version_id)
        config_snapshot = self.validate_configuration(config)

        return self.repository.create_run(
            dataset_version_id=selection.version.id,
            config_snapshot=config_snapshot,
            status="pending",
        )

    def get_run(self, run_id: UUID) -> PreprocessingRun:
        """Retrieve one preprocessing run or raise a not-found error."""
        run = self.repository.get_run(run_id)

        if run is None:
            raise PreprocessingRunNotFoundError(
                f"Preprocessing run {run_id} was not found."
            )

        return run

    def list_runs(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
        dataset_version_id: UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[PreprocessingRun], int]:
        """Return paginated preprocessing run history."""
        return self.repository.list_runs(
            page=page,
            page_size=page_size,
            dataset_version_id=dataset_version_id,
            status=status,
        )

    # ========================================================
    # RUN STATUS
    # ========================================================

    def mark_running(
        self,
        run_id: UUID,
    ) -> PreprocessingRun:
        """Mark a pending run as running."""
        run = self.get_run(run_id)

        if run.status != "pending":
            raise PreprocessingServiceError(
                f"Cannot start a run with status '{run.status}'."
            )

        return self.repository.update_run(
            run,
            status="running",
            started_at=_utc_now(),
        )

    def mark_completed(
        self,
        run_id: UUID,
        *,
        input_sample_count: int,
        output_sample_count: int,
        training_count: int,
        validation_count: int,
        testing_count: int,
        feature_count: int,
        duration_ms: int,
        result_summary: dict[str, Any],
    ) -> PreprocessingRun:
        """Persist successful preprocessing results."""
        run = self.get_run(run_id)

        if run.status != "running":
            raise PreprocessingServiceError(
                "Only running preprocessing runs can be completed."
            )

        counts = (
            input_sample_count,
            output_sample_count,
            training_count,
            validation_count,
            testing_count,
            feature_count,
            duration_ms,
        )

        if any(value < 0 for value in counts):
            raise PreprocessingServiceError(
                "Run result counts and duration cannot be negative."
            )

        if not isinstance(result_summary, dict):
            raise PreprocessingServiceError(
                "Result summary must be an object."
            )

        if (
            training_count + validation_count + testing_count
            != output_sample_count
        ):
            raise PreprocessingServiceError(
                "The sum of split counts must equal the output "
                "sample count."
            )

        return self.repository.update_run(
            run,
            status="completed",
            input_sample_count=input_sample_count,
            output_sample_count=output_sample_count,
            training_count=training_count,
            validation_count=validation_count,
            testing_count=testing_count,
            feature_count=feature_count,
            duration_ms=duration_ms,
            result_summary=result_summary,
            completed_at=_utc_now(),
        )

    def mark_failed(
        self,
        run_id: UUID,
        *,
        error_code: str,
        error_message: str,
        duration_ms: int | None = None,
    ) -> PreprocessingRun:
        """Persist a preprocessing failure and its diagnostic details."""
        run = self.get_run(run_id)

        if run.status not in {"pending", "running"}:
            raise PreprocessingServiceError(
                f"Cannot fail a run with status '{run.status}'."
            )

        if not isinstance(error_code, str) or not error_code.strip():
            raise PreprocessingServiceError(
                "A failure error code is required."
            )

        if (
            not isinstance(error_message, str)
            or not error_message.strip()
        ):
            raise PreprocessingServiceError(
                "A failure message is required."
            )

        if duration_ms is not None and duration_ms < 0:
            raise PreprocessingServiceError(
                "Failure duration cannot be negative."
            )

        return self.repository.update_run(
            run,
            status="failed",
            error_code=error_code.strip(),
            error_message=error_message.strip(),
            duration_ms=duration_ms,
            completed_at=_utc_now(),
        )

    # ========================================================
    # RUN EXECUTION
    # ========================================================

    def execute_run(self, run_id: UUID) -> PreprocessingRun:
        """
        Execute a pending run through the preprocessing engine.

        This method owns its transactions (it commits), so it must
        be called with a dedicated session, e.g. from a background
        task, not from a request-scoped session.

        Flow:
            pending -> running (committed, visible to the UI)
            load rows -> engine -> save artifact metadata
            -> completed (committed) or failed (committed)
        """
        run = self.get_run(run_id)

        if run.status != "pending":
            raise PreprocessingServiceError(
                f"Cannot execute a run with status '{run.status}'."
            )

        self.mark_running(run_id)
        self.repository.db.commit()

        started = perf_counter()
        artifact_store = ArtifactStore()

        try:
            selection = self.get_dataset_selection(
                run.dataset_version_id
            )
            config = dict(run.config_snapshot or {})
            feature_order = tuple(
                config.get("feature_order")
                or self.DEFAULT_FEATURE_ORDER
            )

            training_rows = self._load_rows(
                selection.training_email_ids, feature_order
            )
            validation_rows = self._load_rows(
                selection.validation_email_ids, feature_order
            )
            testing_rows = self._load_rows(
                selection.testing_email_ids, feature_order
            )
            dataset_schema = self._build_schema(
                selection.version, feature_order
            )

            result = PreprocessingPipeline(
                artifact_store=artifact_store
            ).run(
                run_id=run.id,
                dataset_schema=dataset_schema,
                training_rows=training_rows,
                validation_rows=validation_rows,
                testing_rows=testing_rows,
                config=config,
            )

            for artifact in result.artifacts:
                self.repository.create_artifact(
                    preprocessing_run_id=run.id,
                    artifact_type=artifact.artifact_type,
                    filename=artifact.filename,
                    storage_path=artifact.storage_path,
                    media_type=artifact.media_type,
                    size_bytes=artifact.size_bytes,
                    checksum_sha256=artifact.checksum_sha256,
                    metadata_json=artifact.metadata or {},
                )

            completed = self.mark_completed(
                run_id,
                input_sample_count=result.input_sample_count,
                output_sample_count=result.output_sample_count,
                training_count=result.training_count,
                validation_count=result.validation_count,
                testing_count=result.testing_count,
                feature_count=result.feature_count,
                duration_ms=result.duration_ms,
                result_summary=result.result_summary,
            )
            self.repository.db.commit()
            return completed

        except Exception as exc:
            self.repository.db.rollback()

            # Remove orphaned files if the pipeline succeeded but a
            # later DB step failed (the pipeline cleans up its own
            # failures).
            try:
                artifact_store.delete_run_artifacts(run_id)
            except Exception:
                pass

            failed = self.mark_failed(
                run_id,
                error_code=getattr(
                    exc, "error_code", "PREPROCESSING_FAILED"
                ),
                error_message=(
                    str(exc) or exc.__class__.__name__
                ),
                duration_ms=int((perf_counter() - started) * 1000),
            )
            self.repository.db.commit()
            return failed

    # --------------------------------------------------------
    # Row / schema loading helpers
    # --------------------------------------------------------

    def _load_rows(
        self,
        email_ids: list[UUID],
        feature_order: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        """
        Build engine input rows: email_id, ground_truth, F1..F12.

        Feature values come from EmailFeatures (f1_..f12_ columns),
        ground truth comes from the emails table. Boolean features
        are converted to 0/1 integers so the scaler accepts them.
        """
        if not email_ids:
            return []

        records = self.dataset_repository.get_email_features_by_ids(
            email_ids
        )
        by_id = {str(record.email_id): record for record in records}
        labels = self._load_ground_truth(email_ids)

        rows: list[dict[str, Any]] = []
        missing: list[str] = []

        for email_id in email_ids:
            key = str(email_id)
            record = by_id.get(key)

            if record is None:
                missing.append(key)
                continue

            if key not in labels:
                raise PreprocessingInputError(
                    f"Ground truth label not found for email {key}."
                )

            row: dict[str, Any] = {
                "email_id": key,
                "ground_truth": labels[key],
            }

            for name in feature_order:
                column = self.FEATURE_COLUMNS.get(name)

                if column is None:
                    raise PreprocessingInputError(
                        f"Unknown feature '{name}' in feature_order."
                    )

                value = getattr(record, column)

                if isinstance(value, bool):
                    value = int(value)

                row[name] = value

            rows.append(row)

        if missing:
            raise PreprocessingInputError(
                f"Feature records not found for {len(missing)} "
                f"email(s), e.g. {missing[:3]}."
            )

        return rows

    def _load_ground_truth(
        self,
        email_ids: list[UUID],
    ) -> dict[str, str]:
        """Map email_id -> 'normal' / 'bombing' from the emails table."""
        # Imported lazily so a wrong model name fails the run with a
        # clear message instead of breaking application startup.
        from app.modules.emails.models import Email

        statement = select(
            Email.id,
            Email.ground_truth_label,
        ).where(Email.id.in_(email_ids))

        result: dict[str, str] = {}

        for email_id, label in self.repository.db.execute(statement):
            result[str(email_id)] = str(
                getattr(label, "value", label)
            )

        return result

    def _build_schema(
        self,
        version: DatasetVersion,
        feature_order: tuple[str, ...],
    ) -> dict[str, str]:
        """
        Build the flat {feature_name: feature_type} schema expected
        by FeatureSchemaValidator.

        dataset_versions.feature_schema currently stores only
        metadata (version, feature_count, an empty features list),
        so the canonical Module 04 feature types are used instead.
        """
        unknown = [
            name for name in feature_order
            if name not in FEATURE_TYPES
        ]

        if unknown:
            raise PreprocessingInputError(
                "Unknown features in feature_order: "
                + ", ".join(unknown)
            )

        return {name: FEATURE_TYPES[name] for name in feature_order}