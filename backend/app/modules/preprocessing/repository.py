from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.preprocessing.models import (
    PreprocessingArtifact,
    PreprocessingRun,
)


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


class PreprocessingRepository:
    """
    Database access layer for Module 06 — Preprocessing Pipeline.

    Responsibilities:
    - Create and retrieve preprocessing runs.
    - Update run status and execution results.
    - List preprocessing run history.
    - Create and retrieve artifact metadata.
    - Keep database operations separate from pipeline execution
      and artifact file storage.

    Architectural boundaries:
    - Does not execute preprocessing.
    - Does not validate pipeline configuration.
    - Does not create or modify dataset versions or splits.
    - Does not read or write artifact file contents.
    - Does not commit transactions automatically.

    Transaction ownership:
    - Repository methods flush after writes.
    - The service or request layer owns commit and rollback.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_page(page: int) -> int:
        """Return a valid one-based page number."""
        return max(int(page), DEFAULT_PAGE)

    @staticmethod
    def _normalize_page_size(page_size: int) -> int:
        """Return a page size between 1 and MAX_PAGE_SIZE."""
        return min(max(int(page_size), 1), MAX_PAGE_SIZE)

    # ============================================================
    # PREPROCESSING RUNS
    # ============================================================

    def create_run(
        self,
        *,
        dataset_version_id: UUID,
        config_snapshot: dict[str, Any],
        status: str = "pending",
    ) -> PreprocessingRun:
        """Create a preprocessing run record."""
        run = PreprocessingRun(
            dataset_version_id=dataset_version_id,
            config_snapshot=dict(config_snapshot),
            status=status,
        )

        self.db.add(run)
        self.db.flush()
        self.db.refresh(run)

        return run

    def get_run(
        self,
        run_id: UUID,
    ) -> PreprocessingRun | None:
        """Retrieve one preprocessing run by ID."""
        return self.db.get(PreprocessingRun, run_id)

    def list_runs(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        dataset_version_id: UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[PreprocessingRun], int]:
        """
        Return paginated preprocessing history.

        Optional filters:
        - dataset_version_id
        - status

        The total count is calculated without pagination.
        """
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        statement = select(PreprocessingRun)

        count_statement = select(func.count(PreprocessingRun.id))

        if dataset_version_id is not None:
            statement = statement.where(
                PreprocessingRun.dataset_version_id
                == dataset_version_id
            )
            count_statement = count_statement.where(
                PreprocessingRun.dataset_version_id
                == dataset_version_id
            )

        if status is not None:
            normalized_status = str(status).strip().lower()

            statement = statement.where(
                PreprocessingRun.status == normalized_status
            )
            count_statement = count_statement.where(
                PreprocessingRun.status == normalized_status
            )

        statement = (
            statement
            .order_by(
                PreprocessingRun.created_at.desc(),
                PreprocessingRun.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(statement).all())
        total = int(self.db.scalar(count_statement) or 0)

        return items, total

    def count_runs(
        self,
        *,
        dataset_version_id: UUID | None = None,
        status: str | None = None,
    ) -> int:
        """Count preprocessing runs using optional filters."""
        statement = select(func.count(PreprocessingRun.id))

        if dataset_version_id is not None:
            statement = statement.where(
                PreprocessingRun.dataset_version_id
                == dataset_version_id
            )

        if status is not None:
            statement = statement.where(
                PreprocessingRun.status == str(status).strip().lower()
            )

        return int(self.db.scalar(statement) or 0)

    def update_run(
        self,
        run: PreprocessingRun,
        *,
        status: str | None = None,
        input_sample_count: int | None = None,
        output_sample_count: int | None = None,
        training_count: int | None = None,
        validation_count: int | None = None,
        testing_count: int | None = None,
        feature_count: int | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        result_summary: dict[str, Any] | None = None,
        started_at: Any | None = None,
        completed_at: Any | None = None,
    ) -> PreprocessingRun:
        """
        Update execution fields on an existing run.

        Only explicitly supplied values are changed.
        Configuration and dataset version are immutable here.
        """
        updates = {
            "status": status,
            "input_sample_count": input_sample_count,
            "output_sample_count": output_sample_count,
            "training_count": training_count,
            "validation_count": validation_count,
            "testing_count": testing_count,
            "feature_count": feature_count,
            "duration_ms": duration_ms,
            "error_code": error_code,
            "error_message": error_message,
            "result_summary": result_summary,
            "started_at": started_at,
            "completed_at": completed_at,
        }

        for field, value in updates.items():
            if value is not None:
                setattr(run, field, value)

        self.db.add(run)
        self.db.flush()
        self.db.refresh(run)

        return run

    # ============================================================
    # PREPROCESSING ARTIFACTS
    # ============================================================

    def create_artifact(
        self,
        *,
        preprocessing_run_id: UUID,
        artifact_type: str,
        filename: str,
        storage_path: str,
        media_type: str | None = None,
        size_bytes: int = 0,
        checksum_sha256: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> PreprocessingArtifact:
        """Persist metadata for a generated artifact."""
        artifact = PreprocessingArtifact(
            preprocessing_run_id=preprocessing_run_id,
            artifact_type=artifact_type,
            filename=filename,
            storage_path=storage_path,
            media_type=media_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            metadata_json=dict(metadata_json or {}),
        )

        self.db.add(artifact)
        self.db.flush()
        self.db.refresh(artifact)

        return artifact

    def get_artifact(
        self,
        artifact_id: UUID,
    ) -> PreprocessingArtifact | None:
        """Retrieve one artifact by ID."""
        return self.db.get(PreprocessingArtifact, artifact_id)

    def get_artifact_by_type(
        self,
        *,
        preprocessing_run_id: UUID,
        artifact_type: str,
    ) -> PreprocessingArtifact | None:
        """Retrieve an artifact by run ID and artifact type."""
        statement = select(PreprocessingArtifact).where(
            PreprocessingArtifact.preprocessing_run_id
            == preprocessing_run_id,
            PreprocessingArtifact.artifact_type == artifact_type,
        )

        return self.db.scalar(statement)

    def list_artifacts(
        self,
        preprocessing_run_id: UUID,
    ) -> list[PreprocessingArtifact]:
        """List artifacts belonging to a preprocessing run."""
        statement = (
            select(PreprocessingArtifact)
            .where(
                PreprocessingArtifact.preprocessing_run_id
                == preprocessing_run_id
            )
            .order_by(
                PreprocessingArtifact.created_at.asc(),
                PreprocessingArtifact.id.asc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def count_artifacts(
        self,
        preprocessing_run_id: UUID,
    ) -> int:
        """Count artifacts belonging to a preprocessing run."""
        statement = select(
            func.count(PreprocessingArtifact.id)
        ).where(
            PreprocessingArtifact.preprocessing_run_id
            == preprocessing_run_id
        )

        return int(self.db.scalar(statement) or 0)