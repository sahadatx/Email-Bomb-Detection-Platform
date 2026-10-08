
from __future__ import annotations

import csv
import io
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.ml_models.engine.base import TrainingConfig
from app.modules.ml_models.engine.trainer import ModelTrainer
from app.modules.ml_models.models import (
    MLModelDefinition,
    MLTrainingRun,
    MLModelVersion,
    MLEvaluationRun,
)
from app.modules.ml_models.repository import MLModelRepository
from app.modules.preprocessing.models import (
    PreprocessingArtifact,
    PreprocessingRun,
)
from app.modules.preprocessing.config.validator import FEATURE_TYPES


class MLModelServiceError(Exception):
    """Base exception for ML model service errors."""


class MLModelNotFoundError(MLModelServiceError):
    """Raised when an ML model does not exist."""


class TrainingRunNotFoundError(MLModelServiceError):
    """Raised when a training run does not exist."""


class ModelVersionNotFoundError(MLModelServiceError):
    """Raised when a model version does not exist."""


class EvaluationRunNotFoundError(MLModelServiceError):
    """Raised when an evaluation run does not exist."""


class InvalidModelStateError(MLModelServiceError):
    """Raised when an operation is invalid for the current model state."""


class MLModelService:
    """Business logic for ML model management."""

    ALLOWED_MODEL_STATUSES = {"active", "inactive"}
    ALLOWED_TRAINING_STATUSES = {
        "pending",
        "queued",
        "running",
        "completed",
        "failed",
        "cancelled",
    }
    ALLOWED_EVALUATION_STATUSES = {
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
    }
    ALLOWED_VERSION_STATUSES = {"registered", "active", "archived"}

    def __init__(self, db: Session):
        self.db = db
        self.repository = MLModelRepository(db)

    @staticmethod
    def _validate_model_configuration(
        algorithm: str,
        hyperparameters: dict[str, Any],
    ) -> None:
        """Validate against the same engine used by background training."""
        try:
            engine = ModelTrainer().get_engine(algorithm)
            engine.validate_config(
                TrainingConfig(hyperparameters=hyperparameters)
            )
        except Exception as exc:
            raise ValueError(str(exc)) from exc

    def _validate_preprocessing_run(self, preprocessing_run_id: UUID) -> PreprocessingRun:
        run = self.db.get(PreprocessingRun, preprocessing_run_id)
        if run is None:
            raise InvalidModelStateError("Preprocessing run was not found.")
        if run.status != "completed":
            raise InvalidModelStateError(
                "Only completed preprocessing runs can be used."
            )

        artifacts = self.db.query(PreprocessingArtifact).filter(
            PreprocessingArtifact.preprocessing_run_id == preprocessing_run_id
        ).all()
        by_type = {artifact.artifact_type: artifact for artifact in artifacts}
        required = {
            "train_processed",
            "validation_processed",
            "test_processed",
        }
        missing = required - set(by_type)
        if missing:
            raise InvalidModelStateError(
                "Preprocessing run is missing required processed artifacts: "
                + ", ".join(sorted(missing))
            )

        from app.modules.preprocessing.storage.artifact_store import ArtifactStore

        artifact_store = ArtifactStore()
        for artifact_type in required:
            artifact = by_type[artifact_type]
            try:
                artifact_store.read_bytes(preprocessing_run_id, artifact.filename)
                if artifact.checksum_sha256 and not artifact_store.verify_checksum(
                    preprocessing_run_id,
                    artifact.filename,
                    artifact.checksum_sha256,
                ):
                    raise ValueError(
                        f"Checksum mismatch for {artifact.filename}."
                    )
            except Exception as exc:
                raise InvalidModelStateError(
                    f"Processed artifact {artifact.filename} is unavailable or invalid: {exc}"
                ) from exc
        return run

    @staticmethod
    def _validate_training_class_distribution(
        preprocessing_run_id: UUID,
    ) -> None:
        """Reject preprocessing output that cannot train a binary classifier."""
        from app.modules.preprocessing.storage.artifact_store import ArtifactStore

        artifact_store = ArtifactStore()
        try:
            payload = artifact_store.read_bytes(
                preprocessing_run_id,
                "train_processed.csv",
            )
            rows = csv.DictReader(io.StringIO(payload.decode("utf-8")))
            counts = {"normal": 0, "bombing": 0}
            for row in rows:
                label = str(row.get("ground_truth", "")).strip().lower()
                if label in counts:
                    counts[label] += 1
        except Exception as exc:
            raise InvalidModelStateError(
                f"Could not validate training labels in the processed artifact: {exc}"
            ) from exc

        present = [label for label, count in counts.items() if count > 0]
        if len(present) < 2:
            distribution = ", ".join(
                f"{label}: {count}" for label, count in counts.items()
            )
            raise InvalidModelStateError(
                "The training split must contain both Normal and Bombing samples "
                f"to train a binary classifier. Current training labels — {distribution}. "
                "Choose a dataset version containing both classes, then preprocess it again."
            )

    # ------------------------------------------------------------------
    # Model definitions
    # ------------------------------------------------------------------

    def create_model(
        self,
        *,
        name: str,
        algorithm: str,
        hyperparameters: dict[str, Any] | None = None,
        description: str | None = None,
        status: str = "active",
    ) -> MLModelDefinition:
        name = name.strip()
        algorithm = algorithm.strip().lower()

        if not name:
            raise ValueError("Model name cannot be empty.")

        if not algorithm:
            raise ValueError("Algorithm cannot be empty.")

        if status not in self.ALLOWED_MODEL_STATUSES:
            raise ValueError(f"Unsupported model status: {status}")

        hyperparameters = hyperparameters or {}
        if not isinstance(hyperparameters, dict):
            raise ValueError("Hyperparameters must be a JSON object.")
        self._validate_model_configuration(algorithm, hyperparameters)

        existing = self.repository.get_model_by_name(name)
        if existing is not None:
            raise InvalidModelStateError(
                f"A model named '{name}' already exists."
            )

        return self.repository.create_model(
            name=name,
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            description=description,
            status=status,
        )

    def get_model(self, model_id: UUID) -> MLModelDefinition:
        model = self.repository.get_model(model_id)
        if model is None:
            raise MLModelNotFoundError(
                f"ML model '{model_id}' was not found."
            )
        return model

    def get_model_by_name(self, name: str) -> MLModelDefinition:
        model = self.repository.get_model_by_name(name.strip())
        if model is None:
            raise MLModelNotFoundError(
                f"ML model '{name}' was not found."
            )
        return model

    def list_models(
        self,
        *,
        status: str | None = None,
        algorithm: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLModelDefinition]:
        if offset < 0:
            raise ValueError("Offset cannot be negative.")
        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        if status is not None and status not in self.ALLOWED_MODEL_STATUSES:
            raise ValueError(f"Unsupported model status: {status}")

        return self.repository.list_models(
            status=status,
            algorithm=algorithm,
            search=search,
            offset=offset,
            limit=limit,
        )

    def count_models(
        self,
        *,
        status: str | None = None,
        algorithm: str | None = None,
        search: str | None = None,
    ) -> int:
        return self.repository.count_models(
            status=status,
            algorithm=algorithm,
            search=search,
        )

    def update_model(
        self,
        model_id: UUID,
        **changes: Any,
    ) -> MLModelDefinition:
        model = self.get_model(model_id)

        allowed_fields = {
            "name",
            "description",
            "algorithm",
            "hyperparameters",
        }
        unknown = set(changes) - allowed_fields
        if unknown:
            raise ValueError(
                f"Unsupported model fields: {', '.join(sorted(unknown))}"
            )

        if "name" in changes:
            name = changes["name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Model name cannot be empty.")

            name = name.strip()
            existing = self.repository.get_model_by_name(name)
            if existing is not None and existing.id != model.id:
                raise InvalidModelStateError(
                    f"A model named '{name}' already exists."
                )
            changes["name"] = name

        if "algorithm" in changes:
            algorithm = changes["algorithm"]
            if not isinstance(algorithm, str) or not algorithm.strip():
                raise ValueError("Algorithm cannot be empty.")
            changes["algorithm"] = algorithm.strip().lower()

        if "hyperparameters" in changes:
            if not isinstance(changes["hyperparameters"], dict):
                raise ValueError("Hyperparameters must be a JSON object.")

        next_algorithm = changes.get("algorithm", model.algorithm)
        next_hyperparameters = changes.get(
            "hyperparameters", model.hyperparameters or {}
        )
        self._validate_model_configuration(
            next_algorithm, next_hyperparameters
        )

        # Preserve explicit null for description if the repository supports it.
        if "description" in changes and changes["description"] is None:
            model.description = None
            changes.pop("description")

        if changes:
            self.repository.update_model(model, **changes)

        return model

    def set_model_status(
        self,
        model_id: UUID,
        status: str,
    ) -> MLModelDefinition:
        if status not in self.ALLOWED_MODEL_STATUSES:
            raise ValueError(f"Unsupported model status: {status}")

        model = self.get_model(model_id)
        self.repository.update_model_status(model, status)
        return model

    def activate_model(self, model_id: UUID) -> MLModelDefinition:
        return self.set_model_status(model_id, "active")

    def deactivate_model(self, model_id: UUID) -> MLModelDefinition:
        return self.set_model_status(model_id, "inactive")

    def delete_model(self, model_id: UUID) -> None:
        model = self.get_model(model_id)
        training_count = self.repository.count_training_runs(
            model_definition_id=model_id
        )
        version_count = self.repository.count_model_versions(
            model_definition_id=model_id
        )
        if training_count or version_count:
            raise InvalidModelStateError(
                "Models with training runs or registered versions cannot be deleted."
            )
        self.repository.delete_model(model)

    # ------------------------------------------------------------------
    # Training runs
    # ------------------------------------------------------------------

    def create_training_run(
        self,
        *,
        model_definition_id: UUID,
        preprocessing_run_id: UUID,
        config_snapshot: dict[str, Any] | None = None,
    ) -> MLTrainingRun:
        model = self.get_model(model_definition_id)

        if model.status != "active":
            raise InvalidModelStateError(
                "Cannot train an inactive model."
            )

        self._validate_preprocessing_run(preprocessing_run_id)
        self._validate_training_class_distribution(preprocessing_run_id)
        if not isinstance(config_snapshot or {}, dict):
            raise ValueError("Training configuration must be a JSON object.")

        snapshot = dict(config_snapshot or {})
        random_state = snapshot.get("random_state", 42)
        if isinstance(random_state, bool) or not isinstance(random_state, int):
            raise ValueError("random_state must be an integer.")
        overrides = snapshot.get("hyperparameters", {})
        if not isinstance(overrides, dict):
            raise ValueError("Training hyperparameters must be a JSON object.")
        selected_features = snapshot.get("feature_names")
        if selected_features is not None:
            if not isinstance(selected_features, list) or not selected_features or any(not isinstance(name, str) for name in selected_features):
                raise ValueError("feature_names must be a non-empty list of feature names.")
            if len(set(selected_features)) != len(selected_features):
                raise ValueError("feature_names must not contain duplicates.")
            artifacts = self.db.query(PreprocessingArtifact).filter(PreprocessingArtifact.preprocessing_run_id == preprocessing_run_id, PreprocessingArtifact.artifact_type == "train_processed").all()
            available = {name for name in ((artifacts[0].metadata_json or {}).get("feature_order", []) if artifacts else []) if FEATURE_TYPES.get(name) in {"boolean", "integer", "float"}}
            unknown_features = set(selected_features) - available
            if unknown_features:
                raise ValueError("Unsupported feature names: " + ", ".join(sorted(unknown_features)))
        parameters = dict(model.hyperparameters or {})
        parameters.update(overrides)
        self._validate_model_configuration(model.algorithm, parameters)
        unsupported = set(snapshot) - {"random_state", "hyperparameters", "feature_names"}
        if unsupported:
            raise ValueError(
                "Unsupported training configuration fields: "
                + ", ".join(sorted(unsupported))
            )

        return self.repository.create_training_run(
            model_definition_id=model.id,
            preprocessing_run_id=preprocessing_run_id,
            config_snapshot={
                "random_state": random_state,
                "hyperparameters": overrides,
                **({"feature_names": selected_features} if selected_features is not None else {}),
            },
        )

    def retry_training_run(self, training_run_id: UUID) -> MLTrainingRun:
        """Create a new pending run from a failed run's inputs."""
        previous = self.get_training_run(training_run_id)
        if previous.status != "failed":
            raise InvalidModelStateError(
                "Only failed training runs can be retried."
            )
        return self.create_training_run(
            model_definition_id=previous.model_definition_id,
            preprocessing_run_id=previous.preprocessing_run_id,
            config_snapshot=previous.config_snapshot or {},
        )

    def get_training_run(self, training_run_id: UUID) -> MLTrainingRun:
        run = self.repository.get_training_run(training_run_id)
        if run is None:
            raise TrainingRunNotFoundError(
                f"Training run '{training_run_id}' was not found."
            )
        return run

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
        if offset < 0 or limit < 1:
            raise ValueError("Invalid pagination values.")

        if status is not None and status not in self.ALLOWED_TRAINING_STATUSES:
            raise ValueError(f"Unsupported training status: {status}")

        return self.repository.list_training_runs(
            model_definition_id=model_definition_id,
            dataset_version_id=dataset_version_id,
            preprocessing_run_id=preprocessing_run_id,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
        )

    def count_training_runs(
        self,
        *,
        model_definition_id: UUID | None = None,
        dataset_version_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        return self.repository.count_training_runs(
            model_definition_id=model_definition_id,
            dataset_version_id=dataset_version_id,
            preprocessing_run_id=preprocessing_run_id,
            status=status,
            search=search,
        )

    def update_training_run(
        self,
        training_run_id: UUID,
        **changes: Any,
    ) -> MLTrainingRun:
        run = self.get_training_run(training_run_id)

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
        unknown = set(changes) - allowed_fields
        if unknown:
            raise ValueError(
                f"Unsupported training fields: {', '.join(sorted(unknown))}"
            )

        if "status" in changes:
            status = changes["status"]
            if status not in self.ALLOWED_TRAINING_STATUSES:
                raise ValueError(f"Unsupported training status: {status}")

            if run.status in {"completed", "failed", "cancelled"}:
                raise InvalidModelStateError(
                    f"Cannot update a terminal training run ({run.status})."
                )

            allowed_transitions = {
                "pending": {"queued", "running", "failed", "cancelled"},
                "queued": {"running", "failed", "cancelled"},
                "running": {"completed", "failed", "cancelled"},
            }
            if status != run.status and status not in allowed_transitions.get(
                run.status, set()
            ):
                raise InvalidModelStateError(
                    f"Invalid training transition: {run.status} -> {status}"
                )

        if "progress_percent" in changes:
            value = changes["progress_percent"]
            if not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError("Progress must be an integer from 0 to 100.")

        for field in ("training_sample_count", "validation_sample_count"):
            if field in changes and changes[field] < 0:
                raise ValueError(f"{field} cannot be negative.")

        if "duration_ms" in changes:
            value = changes["duration_ms"]
            if value is not None and value < 0:
                raise ValueError("Duration cannot be negative.")

        if "result_summary" in changes:
            value = changes["result_summary"]
            if value is not None and not isinstance(value, dict):
                raise ValueError("Result summary must be a JSON object.")

        self.repository.update_training_run(run, **changes)
        return run

    # ------------------------------------------------------------------
    # Model versions / registry
    # ------------------------------------------------------------------

    def get_model_version(self, version_id: UUID) -> MLModelVersion:
        version = self.repository.get_model_version(version_id)
        if version is None:
            raise ModelVersionNotFoundError(
                f"Model version '{version_id}' was not found."
            )
        return version

    def get_model_version_by_training_run(
        self,
        training_run_id: UUID,
    ) -> MLModelVersion:
        version = self.repository.get_version_by_training_run(training_run_id)
        if version is None:
            raise ModelVersionNotFoundError(
                f"No model version is registered for training run '{training_run_id}'."
            )
        return version

    def list_model_versions(
        self,
        *,
        model_definition_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLModelVersion]:
        if offset < 0 or limit < 1:
            raise ValueError("Invalid pagination values.")

        if status is not None and status not in self.ALLOWED_VERSION_STATUSES:
            raise ValueError(f"Unsupported version status: {status}")

        return self.repository.list_model_versions(
            model_definition_id=model_definition_id,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
        )

    def count_model_versions(
        self,
        *,
        model_definition_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        return self.repository.count_model_versions(
            model_definition_id=model_definition_id,
            status=status,
            search=search,
        )

    def register_model_version(
        self,
        *,
        training_run_id: UUID,
        artifact_filename: str,
        storage_path: str,
        media_type: str | None = None,
        size_bytes: int = 0,
        checksum_sha256: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> MLModelVersion:
        run = self.get_training_run(training_run_id)

        if run.status != "completed":
            raise InvalidModelStateError(
                "Only completed training runs can be registered."
            )

        existing = self.repository.get_version_by_training_run(run.id)
        if existing is not None:
            raise InvalidModelStateError(
                "This training run already has a registered model version."
            )

        if not artifact_filename.strip():
            raise ValueError("Artifact filename cannot be empty.")
        if not storage_path.strip():
            raise ValueError("Artifact storage path cannot be empty.")
        if size_bytes < 0:
            raise ValueError("Artifact size cannot be negative.")
        if metadata_json is not None and not isinstance(metadata_json, dict):
            raise ValueError("Artifact metadata must be a JSON object.")

        next_version = self.repository.get_next_version_number(
            run.model_definition_id
        )

        return self.repository.create_model_version(
            model_definition_id=run.model_definition_id,
            training_run_id=run.id,
            version=next_version,
            artifact_filename=artifact_filename,
            storage_path=storage_path,
            media_type=media_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            metadata_json=metadata_json or {},
        )

    def activate_model_version(self, version_id: UUID) -> MLModelVersion:
        version = self.get_model_version(version_id)

        if version.status == "archived":
            raise InvalidModelStateError(
                "An archived model version cannot be activated."
            )

        current_versions = self.repository.list_model_versions(
            model_definition_id=version.model_definition_id,
            status="active",
            offset=0,
            limit=1000,
        )

        # Keep one active version per model definition.
        for current in current_versions:
            if current.id != version.id:
                self.repository.update_model_version(
                    current,
                    status="registered",
                    activated_at=None,
                )

        from datetime import datetime, timezone

        self.repository.update_model_version(
            version,
            status="active",
            activated_at=datetime.now(timezone.utc),
            archived_at=None,
        )
        return version

    def archive_model_version(self, version_id: UUID) -> MLModelVersion:
        version = self.get_model_version(version_id)

        if version.status == "active":
            raise InvalidModelStateError(
                "Deactivate the active version before archiving it."
            )

        from datetime import datetime, timezone

        self.repository.update_model_version(
            version,
            status="archived",
            archived_at=datetime.now(timezone.utc),
        )
        return version

    def restore_model_version(self, version_id: UUID) -> MLModelVersion:
        """Restore an archived version to registered (inactive) state."""
        version = self.get_model_version(version_id)
        if version.status != "archived":
            raise InvalidModelStateError(
                "Only archived model versions can be restored."
            )
        from datetime import datetime, timezone

        self.repository.update_model_version(
            version,
            status="registered",
            archived_at=None,
            activated_at=None,
        )
        return version

    # ------------------------------------------------------------------
    # Evaluation runs
    # ------------------------------------------------------------------

    def create_evaluation_run(
        self,
        *,
        model_version_id: UUID,
        preprocessing_run_id: UUID,
        evaluation_split: str,
    ) -> MLEvaluationRun:
        version = self.get_model_version(model_version_id)

        if version.status == "archived":
            raise InvalidModelStateError(
                "Archived model versions cannot be evaluated."
            )

        if evaluation_split not in {"validation", "testing"}:
            raise ValueError(
                "Evaluation split must be 'validation' or 'testing'."
            )
        source_training_run = self.get_training_run(version.training_run_id)
        if source_training_run.status != "completed":
            raise InvalidModelStateError(
                "Only versions from completed training runs can be evaluated."
            )
        if source_training_run.preprocessing_run_id != preprocessing_run_id:
            raise InvalidModelStateError(
                "Evaluation preprocessing run must match the version's source training run."
            )
        preprocessing_run = self._validate_preprocessing_run(
            preprocessing_run_id
        )
        available_count = (
            preprocessing_run.validation_count
            if evaluation_split == "validation"
            else preprocessing_run.testing_count
        )
        if available_count < 1:
            raise InvalidModelStateError(
                f"The selected {evaluation_split} split contains no samples."
            )

        return self.repository.create_evaluation_run(
            model_version_id=version.id,
            preprocessing_run_id=preprocessing_run_id,
            evaluation_split=evaluation_split,
        )

    def get_evaluation_run(self, evaluation_run_id: UUID) -> MLEvaluationRun:
        run = self.repository.get_evaluation_run(evaluation_run_id)
        if run is None:
            raise EvaluationRunNotFoundError(
                f"Evaluation run '{evaluation_run_id}' was not found."
            )
        return run

    def list_evaluation_runs(
        self,
        *,
        model_version_id: UUID | None = None,
        model_definition_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        evaluation_split: str | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLEvaluationRun]:
        if offset < 0 or limit < 1:
            raise ValueError("Invalid pagination values.")

        if status is not None and status not in self.ALLOWED_EVALUATION_STATUSES:
            raise ValueError(f"Unsupported evaluation status: {status}")

        if evaluation_split is not None and evaluation_split not in {
            "validation",
            "testing",
        }:
            raise ValueError("Invalid evaluation split.")

        return self.repository.list_evaluation_runs(
            model_version_id=model_version_id,
            model_definition_id=model_definition_id,
            preprocessing_run_id=preprocessing_run_id,
            evaluation_split=evaluation_split,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
        )

    def count_evaluation_runs(
        self,
        *,
        model_version_id: UUID | None = None,
        model_definition_id: UUID | None = None,
        preprocessing_run_id: UUID | None = None,
        evaluation_split: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        return self.repository.count_evaluation_runs(
            model_version_id=model_version_id,
            model_definition_id=model_definition_id,
            preprocessing_run_id=preprocessing_run_id,
            evaluation_split=evaluation_split,
            status=status,
            search=search,
        )

    def update_evaluation_run(
        self,
        evaluation_run_id: UUID,
        **changes: Any,
    ) -> MLEvaluationRun:
        run = self.get_evaluation_run(evaluation_run_id)

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
        unknown = set(changes) - allowed_fields
        if unknown:
            raise ValueError(
                f"Unsupported evaluation fields: {', '.join(sorted(unknown))}"
            )

        if "status" in changes:
            status = changes["status"]
            if status not in self.ALLOWED_EVALUATION_STATUSES:
                raise ValueError(f"Unsupported evaluation status: {status}")

            if run.status in {"completed", "failed", "cancelled"}:
                raise InvalidModelStateError(
                    f"Cannot update a terminal evaluation run ({run.status})."
                )

            allowed_transitions = {
                "pending": {"running", "failed", "cancelled"},
                "running": {"completed", "failed", "cancelled"},
            }
            if status != run.status and status not in allowed_transitions.get(
                run.status, set()
            ):
                raise InvalidModelStateError(
                    f"Invalid evaluation transition: {run.status} -> {status}"
                )

        if "sample_count" in changes and changes["sample_count"] < 0:
            raise ValueError("Sample count cannot be negative.")

        for field in ("accuracy", "precision", "recall", "f1_score", "roc_auc"):
            if field in changes:
                value = changes[field]
                if value is not None and not 0 <= value <= 1:
                    raise ValueError(f"{field} must be between 0 and 1.")

        if "duration_ms" in changes:
            value = changes["duration_ms"]
            if value is not None and value < 0:
                raise ValueError("Duration cannot be negative.")

        for field in (
            "confusion_matrix",
            "classification_report",
            "result_summary",
        ):
            if field in changes and changes[field] is not None:
                if not isinstance(changes[field], (dict, list)):
                    raise ValueError(f"{field} must be a JSON object or array.")

        self.repository.update_evaluation_run(run, **changes)
        return run
