
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, desc, or_, select
from sqlalchemy.orm import Session

from app.modules.ml_models.models import (
    MLEvaluationRun,
    MLModelDefinition,
    MLModelVersion,
    MLTrainingRun,
)
from app.modules.preprocessing.models import PreprocessingRun


class MLModelRepository:
    """Database operations for ML model management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Model definitions
    # ------------------------------------------------------------------

    def create_model(
        self,
        *,
        name: str,
        algorithm: str,
        hyperparameters: dict[str, Any],
        description: str | None = None,
        status: str = "inactive",
    ) -> MLModelDefinition:
        model = MLModelDefinition(
            name=name,
            description=description,
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            status=status,
        )
        self.db.add(model)
        self.db.flush()
        return model

    def get_model(
        self,
        model_id: UUID,
    ) -> MLModelDefinition | None:
        return self.db.get(MLModelDefinition, model_id)

    def get_model_by_name(
        self,
        name: str,
    ) -> MLModelDefinition | None:
        statement = select(MLModelDefinition).where(
            MLModelDefinition.name == name
        )
        return self.db.scalar(statement)

    def list_models(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
        algorithm: str | None = None,
        search: str | None = None,
    ) -> list[MLModelDefinition]:
        statement = select(MLModelDefinition)

        if status is not None:
            statement = statement.where(
                MLModelDefinition.status == status
            )

        if algorithm is not None:
            statement = statement.where(
                MLModelDefinition.algorithm == algorithm
            )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                MLModelDefinition.name.ilike(pattern)
                | MLModelDefinition.description.ilike(pattern)
            )

        statement = (
            statement.order_by(desc(MLModelDefinition.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def count_models(
        self,
        *,
        status: str | None = None,
        algorithm: str | None = None,
        search: str | None = None,
    ) -> int:
        from sqlalchemy import func

        statement = select(func.count()).select_from(MLModelDefinition)

        if status is not None:
            statement = statement.where(
                MLModelDefinition.status == status
            )

        if algorithm is not None:
            statement = statement.where(
                MLModelDefinition.algorithm == algorithm
            )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                MLModelDefinition.name.ilike(pattern)
                | MLModelDefinition.description.ilike(pattern)
            )

        return self.db.scalar(statement) or 0

    def update_model(
        self,
        model: MLModelDefinition,
        *,
        name: str | None = None,
        description: str | None = None,
        algorithm: str | None = None,
        hyperparameters: dict[str, Any] | None = None,
    ) -> MLModelDefinition:
        if name is not None:
            model.name = name

        if description is not None:
            model.description = description

        if algorithm is not None:
            model.algorithm = algorithm
        if hyperparameters is not None:
            model.hyperparameters = hyperparameters

        self.db.flush()
        return model

    def update_model_status(
        self,
        model: MLModelDefinition,
        status: str,
    ) -> MLModelDefinition:
        model.status = status
        self.db.flush()
        return model


    def delete_model(self, model: MLModelDefinition) -> None:
        """Delete a definition after service-level dependency checks."""
        self.db.delete(model)
        self.db.flush()

    # ------------------------------------------------------------------
    # Training runs
    # ------------------------------------------------------------------

    def create_training_run(
        self,
        *,
        model_definition_id: UUID,
        preprocessing_run_id: UUID,
        config_snapshot: dict[str, Any],
        status: str = "pending",
    ) -> MLTrainingRun:
        run = MLTrainingRun(
            model_definition_id=model_definition_id,
            preprocessing_run_id=preprocessing_run_id,
            config_snapshot=config_snapshot,
            status=status,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def get_training_run(
        self,
        run_id: UUID,
    ) -> MLTrainingRun | None:
        return self.db.get(MLTrainingRun, run_id)

    def list_training_runs(
        self,
        *,
        model_definition_id: UUID | None = None,
        dataset_version_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLTrainingRun]:
        statement = select(MLTrainingRun)
        if search:
            statement = statement.outerjoin(
                MLModelDefinition,
                MLModelDefinition.id == MLTrainingRun.model_definition_id,
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    cast(MLTrainingRun.id, String).ilike(pattern),
                    cast(MLTrainingRun.preprocessing_run_id, String).ilike(pattern),
                    MLModelDefinition.name.ilike(pattern),
                )
            )

        if model_definition_id is not None:
            statement = statement.where(
                MLTrainingRun.model_definition_id == model_definition_id
            )

        if dataset_version_id is not None:
            statement = statement.join(
                PreprocessingRun,
                PreprocessingRun.id == MLTrainingRun.preprocessing_run_id,
            ).where(PreprocessingRun.dataset_version_id == dataset_version_id)

        if preprocessing_run_id is not None:
            statement = statement.where(
                MLTrainingRun.preprocessing_run_id == preprocessing_run_id
            )

        if status is not None:
            if status == "pending":
                statement = statement.where(
                    MLTrainingRun.status.in_({"pending", "queued", "running"})
                )
            else:
                statement = statement.where(MLTrainingRun.status == status)

        statement = (
            statement.order_by(desc(MLTrainingRun.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def count_training_runs(
        self,
        *,
        model_definition_id: UUID | None = None,
        dataset_version_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        from sqlalchemy import func

        statement = select(func.count()).select_from(MLTrainingRun)
        if search:
            statement = statement.outerjoin(
                MLModelDefinition,
                MLModelDefinition.id == MLTrainingRun.model_definition_id,
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    cast(MLTrainingRun.id, String).ilike(pattern),
                    cast(MLTrainingRun.preprocessing_run_id, String).ilike(pattern),
                    MLModelDefinition.name.ilike(pattern),
                )
            )

        if model_definition_id is not None:
            statement = statement.where(
                MLTrainingRun.model_definition_id == model_definition_id
            )

        if dataset_version_id is not None:
            statement = statement.join(
                PreprocessingRun,
                PreprocessingRun.id == MLTrainingRun.preprocessing_run_id,
            ).where(PreprocessingRun.dataset_version_id == dataset_version_id)

        if preprocessing_run_id is not None:
            statement = statement.where(
                MLTrainingRun.preprocessing_run_id == preprocessing_run_id
            )

        if status is not None:
            if status == "pending":
                statement = statement.where(
                    MLTrainingRun.status.in_({"pending", "queued", "running"})
                )
            else:
                statement = statement.where(MLTrainingRun.status == status)

        return self.db.scalar(statement) or 0

    def update_training_run(
        self,
        run: MLTrainingRun,
        **values: Any,
    ) -> MLTrainingRun:
        allowed_fields = {
            "status",
            "progress_percent",
            "training_sample_count",
            "validation_sample_count",
            "duration_ms",
            "error_code",
            "error_message",
            "result_summary",
            "started_at",
            "completed_at",
        }

        unknown_fields = set(values) - allowed_fields
        if unknown_fields:
            raise ValueError(
                f"Unsupported training run fields: "
                f"{', '.join(sorted(unknown_fields))}"
            )

        for field, value in values.items():
            setattr(run, field, value)

        self.db.flush()
        return run

    # ------------------------------------------------------------------
    # Model versions / registry
    # ------------------------------------------------------------------

    def create_model_version(
        self,
        *,
        model_definition_id: UUID,
        training_run_id: UUID,
        version: int,
        status: str = "registered",
        artifact_filename: str | None = None,
        storage_path: str | None = None,
        media_type: str | None = None,
        size_bytes: int = 0,
        checksum_sha256: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> MLModelVersion:
        model_version = MLModelVersion(
            model_definition_id=model_definition_id,
            training_run_id=training_run_id,
            version=version,
            status=status,
            artifact_filename=artifact_filename,
            storage_path=storage_path,
            media_type=media_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            metadata_json=metadata_json or {},
        )
        self.db.add(model_version)
        self.db.flush()
        return model_version

    def get_model_version(
        self,
        version_id: UUID,
    ) -> MLModelVersion | None:
        return self.db.get(MLModelVersion, version_id)

    def get_version_by_training_run(
        self,
        training_run_id: UUID,
    ) -> MLModelVersion | None:
        statement = select(MLModelVersion).where(
            MLModelVersion.training_run_id == training_run_id
        )
        return self.db.scalar(statement)

    def list_model_versions(
        self,
        *,
        model_definition_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLModelVersion]:
        statement = select(MLModelVersion)
        if search:
            statement = statement.outerjoin(
                MLModelDefinition,
                MLModelDefinition.id == MLModelVersion.model_definition_id,
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    MLModelDefinition.name.ilike(pattern),
                    cast(MLModelVersion.version, String).ilike(pattern),
                    cast(MLModelVersion.training_run_id, String).ilike(pattern),
                )
            )

        if model_definition_id is not None:
            statement = statement.where(
                MLModelVersion.model_definition_id == model_definition_id
            )

        if status is not None:
            statement = statement.where(
                MLModelVersion.status == status
            )

        statement = (
            statement.order_by(
                desc(MLModelVersion.created_at),
                desc(MLModelVersion.version),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def count_model_versions(
        self,
        *,
        model_definition_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        from sqlalchemy import func

        statement = select(func.count()).select_from(MLModelVersion)
        if search:
            statement = statement.outerjoin(
                MLModelDefinition,
                MLModelDefinition.id == MLModelVersion.model_definition_id,
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    MLModelDefinition.name.ilike(pattern),
                    cast(MLModelVersion.version, String).ilike(pattern),
                    cast(MLModelVersion.training_run_id, String).ilike(pattern),
                )
            )

        if model_definition_id is not None:
            statement = statement.where(
                MLModelVersion.model_definition_id == model_definition_id
            )

        if status is not None:
            statement = statement.where(
                MLModelVersion.status == status
            )

        return self.db.scalar(statement) or 0

    def get_next_version_number(
        self,
        model_definition_id: UUID,
    ) -> int:
        from sqlalchemy import func

        statement = select(
            func.max(MLModelVersion.version)
        ).where(
            MLModelVersion.model_definition_id == model_definition_id
        )
        current_version = self.db.scalar(statement)
        return (current_version or 0) + 1

    def update_model_version(
        self,
        model_version: MLModelVersion,
        **values: Any,
    ) -> MLModelVersion:
        allowed_fields = {
            "status",
            "artifact_filename",
            "storage_path",
            "media_type",
            "size_bytes",
            "checksum_sha256",
            "metadata_json",
            "activated_at",
            "archived_at",
        }

        unknown_fields = set(values) - allowed_fields
        if unknown_fields:
            raise ValueError(
                f"Unsupported model version fields: "
                f"{', '.join(sorted(unknown_fields))}"
            )

        for field, value in values.items():
            setattr(model_version, field, value)

        self.db.flush()
        return model_version

    # ------------------------------------------------------------------
    # Evaluation runs
    # ------------------------------------------------------------------

    def create_evaluation_run(
        self,
        *,
        model_version_id: UUID,
        preprocessing_run_id: UUID,
        evaluation_split: str,
        status: str = "pending",
    ) -> MLEvaluationRun:
        evaluation = MLEvaluationRun(
            model_version_id=model_version_id,
            preprocessing_run_id=preprocessing_run_id,
            evaluation_split=evaluation_split,
            status=status,
        )
        self.db.add(evaluation)
        self.db.flush()
        return evaluation

    def get_evaluation_run(
        self,
        evaluation_id: UUID,
    ) -> MLEvaluationRun | None:
        return self.db.get(MLEvaluationRun, evaluation_id)

    def list_evaluation_runs(
        self,
        *,
        model_version_id: UUID | None = None,
        model_definition_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        status: str | None = None,
        evaluation_split: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLEvaluationRun]:
        statement = select(MLEvaluationRun)
        if search:
            statement = (
                statement.outerjoin(
                    MLModelVersion,
                    MLModelVersion.id == MLEvaluationRun.model_version_id,
                )
                .outerjoin(
                    MLModelDefinition,
                    MLModelDefinition.id == MLModelVersion.model_definition_id,
                )
                .outerjoin(
                    MLTrainingRun,
                    MLTrainingRun.id == MLModelVersion.training_run_id,
                )
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    cast(MLEvaluationRun.id, String).ilike(pattern),
                    cast(MLEvaluationRun.preprocessing_run_id, String).ilike(pattern),
                    cast(MLEvaluationRun.model_version_id, String).ilike(pattern),
                    cast(MLTrainingRun.id, String).ilike(pattern),
                    MLModelDefinition.name.ilike(pattern),
                )
            )

        if model_version_id is not None:
            statement = statement.where(
                MLEvaluationRun.model_version_id == model_version_id
            )

        if model_definition_id is not None:
            if not search:
                statement = statement.join(
                    MLModelVersion,
                    MLModelVersion.id == MLEvaluationRun.model_version_id,
                )
            statement = statement.where(
                MLModelVersion.model_definition_id == model_definition_id
            )

        if preprocessing_run_id is not None:
            statement = statement.where(
                MLEvaluationRun.preprocessing_run_id == preprocessing_run_id
            )

        if status is not None:
            statement = statement.where(
                MLEvaluationRun.status == status
            )

        if evaluation_split is not None:
            statement = statement.where(
                MLEvaluationRun.evaluation_split == evaluation_split
            )

        statement = (
            statement.order_by(desc(MLEvaluationRun.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def count_evaluation_runs(
        self,
        *,
        model_version_id: UUID | None = None,
        model_definition_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        status: str | None = None,
        evaluation_split: str | None = None,
        search: str | None = None,
    ) -> int:
        from sqlalchemy import func

        statement = select(func.count()).select_from(MLEvaluationRun)
        if search:
            statement = (
                statement.outerjoin(
                    MLModelVersion,
                    MLModelVersion.id == MLEvaluationRun.model_version_id,
                )
                .outerjoin(
                    MLModelDefinition,
                    MLModelDefinition.id == MLModelVersion.model_definition_id,
                )
                .outerjoin(
                    MLTrainingRun,
                    MLTrainingRun.id == MLModelVersion.training_run_id,
                )
            )
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    cast(MLEvaluationRun.id, String).ilike(pattern),
                    cast(MLEvaluationRun.preprocessing_run_id, String).ilike(pattern),
                    cast(MLEvaluationRun.model_version_id, String).ilike(pattern),
                    cast(MLTrainingRun.id, String).ilike(pattern),
                    MLModelDefinition.name.ilike(pattern),
                )
            )

        if model_version_id is not None:
            statement = statement.where(
                MLEvaluationRun.model_version_id == model_version_id
            )

        if model_definition_id is not None:
            if not search:
                statement = statement.join(
                    MLModelVersion,
                    MLModelVersion.id == MLEvaluationRun.model_version_id,
                )
            statement = statement.where(
                MLModelVersion.model_definition_id == model_definition_id
            )

        if preprocessing_run_id is not None:
            statement = statement.where(
                MLEvaluationRun.preprocessing_run_id == preprocessing_run_id
            )

        if status is not None:
            statement = statement.where(
                MLEvaluationRun.status == status
            )

        if evaluation_split is not None:
            statement = statement.where(
                MLEvaluationRun.evaluation_split == evaluation_split
            )

        return self.db.scalar(statement) or 0

    def update_evaluation_run(
        self,
        evaluation: MLEvaluationRun,
        **values: Any,
    ) -> MLEvaluationRun:
        allowed_fields = {
            "status",
            "sample_count",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "roc_auc",
            "confusion_matrix",
            "classification_report",
            "result_summary",
            "duration_ms",
            "error_code",
            "error_message",
            "started_at",
            "completed_at",
        }

        unknown_fields = set(values) - allowed_fields
        if unknown_fields:
            raise ValueError(
                f"Unsupported evaluation fields: "
                f"{', '.join(sorted(unknown_fields))}"
            )

        for field, value in values.items():
            setattr(evaluation, field, value)

        self.db.flush()
        return evaluation
