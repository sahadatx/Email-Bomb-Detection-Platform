
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.modules.ml_models.models import MLModelVersion
from app.modules.ml_models.service import (
    InvalidModelStateError,
    MLModelService,
    ModelVersionNotFoundError,
    TrainingRunNotFoundError,
)
from app.modules.ml_models.storage.artifact_store import (
    ArtifactStoreError,
    ModelArtifactStore,
)


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""


class ModelRegistrationError(ModelRegistryError):
    """Raised when model registration fails."""


class ModelActivationError(ModelRegistryError):
    """Raised when model activation fails."""


class ModelArchiveError(ModelRegistryError):
    """Raised when model archiving fails."""


class ModelArtifactLoadError(ModelRegistryError):
    """Raised when a registered model artifact cannot be loaded."""


@dataclass(frozen=True, slots=True)
class RegisteredModel:
    """A registered model version and its artifact metadata."""

    version: MLModelVersion
    artifact_exists: bool


class ModelRegistryManager:
    """Coordinate model registry operations."""

    def __init__(
        self,
        *,
        service: MLModelService,
        artifact_store: ModelArtifactStore,
    ) -> None:
        self.service = service
        self.artifact_store = artifact_store

    def register(
        self,
        *,
        training_run_id: UUID,
        model: Any,
        metadata: dict[str, Any] | None = None,
    ) -> MLModelVersion:
        """Persist a trained model and register its version."""

        try:
            run = self.service.get_training_run(training_run_id)

            if run.status != "completed":
                raise ModelRegistrationError(
                    "Only completed training runs can be registered."
                )

            # Prevent saving an artifact for a run that is already registered.
            existing = self.service.repository.get_version_by_training_run(
                training_run_id
            )
            if existing is not None:
                raise ModelRegistrationError(
                    "This training run already has a registered model version."
                )

            version_number = (
                self.service.repository.get_next_version_number(
                    run.model_definition_id
                )
            )

            artifact = self.artifact_store.save(
                model=model,
                model_definition_id=run.model_definition_id,
                version=version_number,
            )

            try:
                return self.service.register_model_version(
                    training_run_id=training_run_id,
                    artifact_filename=artifact.filename,
                    storage_path=artifact.storage_path,
                    media_type=artifact.media_type,
                    size_bytes=artifact.size_bytes,
                    checksum_sha256=artifact.checksum_sha256,
                    metadata_json=metadata or {},
                )
            except Exception:
                # Avoid leaving an unregistered artifact behind.
                self.artifact_store.delete(artifact.storage_path)
                raise

        except ModelRegistryError:
            raise
        except (InvalidModelStateError, TrainingRunNotFoundError) as exc:
            raise ModelRegistrationError(str(exc)) from exc
        except ArtifactStoreError as exc:
            raise ModelRegistrationError(
                f"Failed to persist model artifact: {exc}"
            ) from exc
        except Exception as exc:
            raise ModelRegistrationError(
                f"Failed to register model: {exc}"
            ) from exc

    def get_version(self, version_id: UUID) -> MLModelVersion:
        """Retrieve a registered model version."""

        try:
            return self.service.get_model_version(version_id)
        except ModelVersionNotFoundError:
            raise
        except Exception as exc:
            raise ModelRegistryError(
                f"Failed to retrieve model version: {exc}"
            ) from exc

    def list_versions(
        self,
        *,
        model_definition_id: UUID | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MLModelVersion]:
        """List registered model versions."""

        return self.service.list_model_versions(
            model_definition_id=model_definition_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    def activate(self, version_id: UUID) -> MLModelVersion:
        """Activate a registered model version."""

        try:
            version = self.service.activate_model_version(version_id)

            # Confirm that the stored artifact is present and valid.
            self.artifact_store.load(
                version.storage_path,
                expected_checksum=version.checksum_sha256,
            )

            return version
        except (InvalidModelStateError, ModelVersionNotFoundError) as exc:
            raise ModelActivationError(str(exc)) from exc
        except ArtifactStoreError as exc:
            raise ModelActivationError(
                f"Cannot activate model: artifact verification failed: {exc}"
            ) from exc
        except Exception as exc:
            raise ModelActivationError(
                f"Failed to activate model version: {exc}"
            ) from exc

    def archive(self, version_id: UUID) -> MLModelVersion:
        """Archive a registered model version."""

        try:
            return self.service.archive_model_version(version_id)
        except (InvalidModelStateError, ModelVersionNotFoundError) as exc:
            raise ModelArchiveError(str(exc)) from exc
        except Exception as exc:
            raise ModelArchiveError(
                f"Failed to archive model version: {exc}"
            ) from exc

    def load_model(self, version_id: UUID) -> Any:
        """Load a registered model and verify its checksum."""

        try:
            version = self.service.get_model_version(version_id)

            return self.artifact_store.load(
                version.storage_path,
                expected_checksum=version.checksum_sha256,
            )
        except ModelVersionNotFoundError:
            raise
        except ArtifactStoreError as exc:
            raise ModelArtifactLoadError(
                f"Failed to load model artifact: {exc}"
            ) from exc
        except Exception as exc:
            raise ModelArtifactLoadError(
                f"Failed to load registered model: {exc}"
            ) from exc