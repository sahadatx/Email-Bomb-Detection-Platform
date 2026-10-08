
from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import joblib


class ArtifactStoreError(Exception):
    """Base exception for model artifact storage errors."""


class ArtifactNotFoundError(ArtifactStoreError):
    """Raised when a requested artifact does not exist."""


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """Metadata describing a stored model artifact."""

    filename: str
    storage_path: str
    media_type: str
    size_bytes: int
    checksum_sha256: str


class ModelArtifactStore:
    """Persist and retrieve serialized machine-learning models."""

    MEDIA_TYPE = "application/x-joblib"
    FILE_EXTENSION = ".joblib"

    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir).expanduser().resolve()

    def _model_directory(
        self,
        model_definition_id: UUID,
        version: int,
    ) -> Path:
        if version < 1:
            raise ArtifactStoreError(
                "Model version must be a positive integer."
            )

        return (
            self.storage_dir
            / str(model_definition_id)
            / f"version_{version}"
        )

    @staticmethod
    def _calculate_checksum(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    def save(
        self,
        *,
        model: Any,
        model_definition_id: UUID,
        version: int,
    ) -> StoredArtifact:
        """Serialize and atomically save a trained model."""

        directory = self._model_directory(
            model_definition_id,
            version,
        )
        directory.mkdir(parents=True, exist_ok=True)

        filename = (
            f"model_{model_definition_id}_v{version}"
            f"{self.FILE_EXTENSION}"
        )
        destination = directory / filename

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                dir=directory,
                prefix=".model-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

            joblib.dump(model, temporary_path)

            # Atomic replacement within the same filesystem.
            os.replace(temporary_path, destination)
            temporary_path = None

            return StoredArtifact(
                filename=filename,
                storage_path=str(destination),
                media_type=self.MEDIA_TYPE,
                size_bytes=destination.stat().st_size,
                checksum_sha256=self._calculate_checksum(destination),
            )

        except Exception as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

            raise ArtifactStoreError(
                f"Failed to save model artifact: {exc}"
            ) from exc

    def load(
        self,
        storage_path: str | Path,
        *,
        expected_checksum: str | None = None,
    ) -> Any:
        """Load a model artifact, optionally verifying its checksum."""

        path = Path(storage_path).expanduser().resolve()

        if not path.is_relative_to(self.storage_dir):
            raise ArtifactStoreError(
                "Artifact path is outside the configured storage directory."
            )

        if not path.is_file():
            raise ArtifactNotFoundError(
                f"Model artifact not found: {path}"
            )

        if expected_checksum is not None:
            actual_checksum = self._calculate_checksum(path)

            if actual_checksum.lower() != expected_checksum.lower():
                raise ArtifactStoreError(
                    "Model artifact checksum verification failed."
                )

        try:
            return joblib.load(path)
        except Exception as exc:
            raise ArtifactStoreError(
                f"Failed to load model artifact: {exc}"
            ) from exc

    def delete(
        self,
        storage_path: str | Path,
    ) -> None:
        """Delete an artifact only if it belongs to this store."""

        path = Path(storage_path).expanduser().resolve()

        if not path.is_relative_to(self.storage_dir):
            raise ArtifactStoreError(
                "Artifact path is outside the configured storage directory."
            )

        if not path.is_file():
            raise ArtifactNotFoundError(
                f"Model artifact not found: {path}"
            )

        try:
            path.unlink()
        except OSError as exc:
            raise ArtifactStoreError(
                f"Failed to delete model artifact: {exc}"
            ) from exc