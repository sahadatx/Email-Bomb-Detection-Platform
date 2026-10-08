
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID
from math import isfinite

from app.modules.preprocessing.engine.missing_values import (
    ImputationState,
)
from app.modules.preprocessing.engine.scaler import ScalerState


class ArtifactStoreError(RuntimeError):
    """Raised when artifact storage operations fail."""


@dataclass(frozen=True)
class StoredArtifact:
    """Metadata returned after successfully storing an artifact."""

    artifact_type: str
    filename: str
    storage_path: str
    media_type: str
    size_bytes: int
    checksum_sha256: str
    metadata: dict[str, Any]


class ArtifactStore:
    """
    Store preprocessing artifacts on the local filesystem.

    Artifacts are organized by preprocessing run ID:

        <root>/
            <run_id>/
                train_processed.csv
                validation_processed.csv
                test_processed.csv
                imputer.json
                scaler.json
                preprocessing_metadata.json

    The storage root can be configured with the
    PREPROCESSING_ARTIFACT_DIR environment variable.
    """

    DATASET_ARTIFACTS = {
        "train_processed": "train_processed.csv",
        "validation_processed": "validation_processed.csv",
        "test_processed": "test_processed.csv",
    }

    TRANSFORMER_ARTIFACTS = {
        "imputer": "imputer.json",
        "scaler": "scaler.json",
    }

    METADATA_ARTIFACT = "preprocessing_metadata.json"

    def __init__(
        self,
        root_dir: str | Path | None = None,
    ) -> None:
        configured_root = (
            root_dir
            or os.getenv("PREPROCESSING_ARTIFACT_DIR")
            or "data/processed/preprocessing"
        )

        self.root_dir = Path(configured_root).expanduser().resolve()

    @staticmethod
    def _normalize_run_id(run_id: str | UUID) -> str:
        try:
            return str(UUID(str(run_id)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ArtifactStoreError(
                "Invalid preprocessing run ID."
            ) from exc

    def _run_directory(self, run_id: str | UUID) -> Path:
        normalized_id = self._normalize_run_id(run_id)
        directory = (self.root_dir / normalized_id).resolve()

        if not directory.is_relative_to(self.root_dir):
            raise ArtifactStoreError(
                "Artifact directory escapes the storage root."
            )

        return directory

    @staticmethod
    def _safe_filename(filename: str) -> str:
        if (
            not isinstance(filename, str)
            or not filename
            or filename in {".", ".."}
            or Path(filename).name != filename
            or "/" in filename
            or "\\" in filename
        ):
            raise ArtifactStoreError(
                "Invalid artifact filename."
            )

        return filename

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, (UUID, Path)):
            return str(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if hasattr(value, "value"):
            return value.value

        raise TypeError(
            f"Object of type {type(value).__name__} "
            "is not JSON serializable."
        )

    @classmethod
    def _json_bytes(cls, value: Any) -> bytes:
        try:
            serialized = json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
                default=cls._json_default,
            )
        except (TypeError, ValueError) as exc:
            raise ArtifactStoreError(
                f"Could not serialize artifact as JSON: {exc}"
            ) from exc

        return (serialized + "\n").encode("utf-8")

    @staticmethod
    def _checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        """
        Write through a temporary file and atomically replace
        the destination to avoid partially written artifacts.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=path.parent,
                prefix=".artifact-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(data)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)

            os.replace(temporary_path, path)
            temporary_path = None

        except OSError as exc:
            raise ArtifactStoreError(
                f"Failed to write artifact {path.name}: {exc}"
            ) from exc

        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _store_bytes(
        self,
        run_id: str | UUID,
        artifact_type: str,
        filename: str,
        data: bytes,
        media_type: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> StoredArtifact:
        safe_filename = self._safe_filename(filename)
        run_directory = self._run_directory(run_id)
        path = run_directory / safe_filename

        if not path.resolve().is_relative_to(run_directory):
            raise ArtifactStoreError(
                "Artifact path escapes its run directory."
            )

        self._atomic_write(path, data)

        return StoredArtifact(
            artifact_type=artifact_type,
            filename=safe_filename,
            storage_path=str(path),
            media_type=media_type,
            size_bytes=len(data),
            checksum_sha256=self._checksum(data),
            metadata=dict(metadata or {}),
        )

    def save_dataset(
        self,
        run_id: str | UUID,
        split: str,
        rows: Sequence[Mapping[str, Any]],
        feature_order: Sequence[str],
    ) -> StoredArtifact:
        """Save one processed dataset split as a CSV file."""

        if split not in self.DATASET_ARTIFACTS:
            raise ArtifactStoreError(
                f"Unsupported dataset split: {split}"
            )

        if not feature_order:
            raise ArtifactStoreError(
                "Feature order cannot be empty."
            )

        if len(feature_order) != len(set(feature_order)):
            raise ArtifactStoreError(
                "Feature order contains duplicate fields."
            )

        if not isinstance(rows, Sequence):
            raise ArtifactStoreError(
                "Dataset rows must be a sequence."
            )

        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ArtifactStoreError(
                    f"Dataset row {index} must be a mapping."
                )

            missing = set(feature_order) - set(row)
            if missing:
                raise ArtifactStoreError(
                    f"Dataset row {index} is missing fields: "
                    + ", ".join(sorted(missing))
                )

        try:
            import io

            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(
                buffer,
                fieldnames=list(feature_order),
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()

            for row in rows:
                writer.writerow(
                    {
                        feature: self._csv_value(row[feature])
                        for feature in feature_order
                    }
                )

            data = buffer.getvalue().encode("utf-8")
        except (TypeError, ValueError, csv.Error) as exc:
            raise ArtifactStoreError(
                f"Could not serialize processed dataset: {exc}"
            ) from exc

        filename = self.DATASET_ARTIFACTS[split]

        return self._store_bytes(
            run_id=run_id,
            artifact_type=split,
            filename=filename,
            data=data,
            media_type="text/csv",
            metadata={
                "row_count": len(rows),
                "feature_count": len(feature_order),
                "feature_order": list(feature_order),
                "format": "csv",
            },
        )

    @staticmethod
    def _csv_value(value: Any) -> Any:
        if value is None:
            return ""

        if isinstance(value, bool):
            return str(value).lower()

        if isinstance(value, (dict, list, tuple)):
            raise ArtifactStoreError(
                "Nested values must be encoded before CSV storage."
            )

        if isinstance(value, float) and not isfinite(value):
            raise ArtifactStoreError(
                "CSV cannot contain non-finite numeric values."
            )

        return value

    def save_json(
        self,
        run_id: str | UUID,
        artifact_type: str,
        filename: str,
        payload: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> StoredArtifact:
        """Save a JSON artifact."""

        data = self._json_bytes(payload)

        return self._store_bytes(
            run_id=run_id,
            artifact_type=artifact_type,
            filename=filename,
            data=data,
            media_type="application/json",
            metadata=metadata,
        )

    def save_transformer(
        self,
        run_id: str | UUID,
        transformer_type: str,
        state: ImputationState | ScalerState | Mapping[str, Any],
    ) -> StoredArtifact:
        """
        Save fitted transformer parameters as JSON.

        This stores learned parameters, not executable Python objects.
        """

        if transformer_type not in self.TRANSFORMER_ARTIFACTS:
            raise ArtifactStoreError(
                f"Unsupported transformer type: {transformer_type}"
            )

        if isinstance(state, ImputationState):
            payload = {
                "transformer": "imputer",
                "strategy": state.strategy,
                "feature_values": state.feature_values,
                "dropped_features": list(state.dropped_features),
            }
        elif isinstance(state, ScalerState):
            payload = {
                "transformer": "scaler",
                "strategy": state.strategy,
                "feature_order": list(state.feature_order),
                "feature_states": {
                    feature: {
                        "strategy": feature_state.strategy,
                        "minimum": feature_state.minimum,
                        "maximum": feature_state.maximum,
                        "mean": feature_state.mean,
                        "scale": feature_state.scale,
                    }
                    for feature, feature_state
                    in state.feature_states.items()
                },
            }
        elif isinstance(state, Mapping):
            payload = dict(state)
        else:
            raise ArtifactStoreError(
                "Unsupported transformer state."
            )

        filename = self.TRANSFORMER_ARTIFACTS[transformer_type]

        return self.save_json(
            run_id=run_id,
            artifact_type=transformer_type,
            filename=filename,
            payload=payload,
            metadata={
                "transformer_type": transformer_type,
                "serialization": "json",
            },
        )

    def save_metadata(
        self,
        run_id: str | UUID,
        metadata: Mapping[str, Any],
    ) -> StoredArtifact:
        """Save preprocessing run metadata."""

        if not isinstance(metadata, Mapping):
            raise ArtifactStoreError(
                "Preprocessing metadata must be a mapping."
            )

        return self.save_json(
            run_id=run_id,
            artifact_type="preprocessing_metadata",
            filename=self.METADATA_ARTIFACT,
            payload=dict(metadata),
            metadata={
                "format": "json",
                "purpose": "preprocessing_run_metadata",
            },
        )

    def read_bytes(
        self,
        run_id: str | UUID,
        filename: str,
    ) -> bytes:
        """Read an artifact from a specific run directory."""

        safe_filename = self._safe_filename(filename)
        run_directory = self._run_directory(run_id)
        path = run_directory / safe_filename

        if not path.resolve().is_relative_to(run_directory):
            raise ArtifactStoreError(
                "Artifact path escapes its run directory."
            )

        try:
            return path.read_bytes()
        except OSError as exc:
            raise ArtifactStoreError(
                f"Could not read artifact {safe_filename}: {exc}"
            ) from exc

    def verify_checksum(
        self,
        run_id: str | UUID,
        filename: str,
        expected_checksum: str,
    ) -> bool:
        """Verify the SHA-256 checksum of a stored artifact."""

        if (
            not isinstance(expected_checksum, str)
            or len(expected_checksum) != 64
        ):
            raise ArtifactStoreError(
                "Expected checksum must be a SHA-256 hex digest."
            )

        try:
            int(expected_checksum, 16)
        except ValueError as exc:
            raise ArtifactStoreError(
                "Expected checksum is not valid hexadecimal."
            ) from exc

        data = self.read_bytes(run_id, filename)
        actual = self._checksum(data)

        return actual == expected_checksum.lower()

    def delete_run_artifacts(
        self,
        run_id: str | UUID,
    ) -> None:
        """Delete all files belonging to a run."""

        directory = self._run_directory(run_id)

        if not directory.exists():
            return

        try:
            for path in directory.iterdir():
                if path.is_file() or path.is_symlink():
                    path.unlink()
                else:
                    raise ArtifactStoreError(
                        "Unexpected directory found inside run artifacts."
                    )

            directory.rmdir()
        except OSError as exc:
            raise ArtifactStoreError(
                f"Could not delete run artifacts: {exc}"
            ) from exc