"""Background execution for ML training and evaluation runs."""
from __future__ import annotations

import csv
import io
import logging
import os
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import UUID

from app.core.database import SessionLocal
from app.modules.ml_models.engine.base import TrainingConfig, TrainingDataset
from app.modules.ml_models.engine.evaluator import ModelEvaluator
from app.modules.ml_models.engine.trainer import ModelTrainer
from app.modules.ml_models.models import (
    MLEvaluationRun,
    MLModelDefinition,
    MLModelVersion,
    MLTrainingRun,
)
from app.modules.ml_models.registry.manager import ModelRegistryManager
from app.modules.ml_models.service import MLModelService
from app.modules.ml_models.storage.artifact_store import ModelArtifactStore
from app.modules.preprocessing.config.validator import FEATURE_TYPES
from app.modules.preprocessing.models import (
    PreprocessingArtifact,
    PreprocessingRun,
)
from app.modules.preprocessing.storage.artifact_store import (
    ArtifactStore as PreprocessingArtifactStore,
)

logger = logging.getLogger(__name__)


def _model_artifact_store() -> ModelArtifactStore:
    return ModelArtifactStore(
        os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models")
    )


class ProcessedDatasetLoader:
    """Load and verify the processed CSV splits for a completed run."""

    # ML engines currently accept numeric vectors. F1 is the sender email
    # address (a high-cardinality string), so it is deliberately excluded;
    # the remaining canonical features are boolean/integer and numeric.
    NON_NUMERIC_LABELS = {"normal": 0, "bombing": 1}

    REQUIRED_ARTIFACTS = {
        "train_processed": "train",
        "validation_processed": "validation",
        "test_processed": "testing",
    }

    def __init__(self, db: Any) -> None:
        self.db = db
        self.store = PreprocessingArtifactStore()

    @classmethod
    def _read_split(
        cls,
        payload: bytes,
        split: str,
        feature_names: list[str] | None,
    ) -> tuple[list[list[float]], list[int], list[str]]:
        try:
            rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
        except (UnicodeDecodeError, csv.Error) as exc:
            raise ValueError(f"The {split} artifact is not valid CSV.") from exc

        if not rows:
            if split == "testing":
                return [], [], feature_names or []
            raise ValueError(f"The {split} artifact contains no rows.")

        columns = list(rows[0])
        requested_names = feature_names or [
            name for name in columns
            if name not in {"email_id", "ground_truth"}
        ]
        names = [
            name for name in requested_names
            if FEATURE_TYPES.get(name) in {"boolean", "integer", "float"}
        ]
        if not names or "ground_truth" not in columns:
            raise ValueError(
                f"The {split} artifact has no supported numeric features or is missing labels."
            )

        features: list[list[float]] = []
        labels: list[int] = []
        for index, row in enumerate(rows, start=2):
            try:
                features.append([float(row[name]) for name in names])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"The {split} artifact row {index} has an invalid numeric feature."
                ) from exc

            raw_label = str(row.get("ground_truth", "")).strip().lower()
            if raw_label in cls.NON_NUMERIC_LABELS:
                labels.append(cls.NON_NUMERIC_LABELS[raw_label])
                continue
            try:
                label_value = float(raw_label)
                if not label_value.is_integer():
                    raise ValueError
                labels.append(int(label_value))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"The {split} artifact row {index} has an unsupported ground_truth label."
                ) from exc

        return features, labels, names

    def load(self, preprocessing_run_id: UUID, feature_names: list[str] | None = None) -> TrainingDataset:
        run = self.db.get(PreprocessingRun, preprocessing_run_id)
        if run is None:
            raise ValueError("Preprocessing run was not found.")
        if run.status != "completed":
            raise ValueError("Only completed preprocessing runs can be used.")

        artifacts = self.db.query(PreprocessingArtifact).filter(
            PreprocessingArtifact.preprocessing_run_id == preprocessing_run_id
        ).all()
        by_type = {artifact.artifact_type: artifact for artifact in artifacts}
        missing = set(self.REQUIRED_ARTIFACTS) - set(by_type)
        if missing:
            raise ValueError(
                "Preprocessing run is missing required artifacts: "
                + ", ".join(sorted(missing))
            )

        loaded: dict[str, tuple[list[list[float]], list[int]]] = {}
        feature_names: list[str] | None = None
        for artifact_type, split in self.REQUIRED_ARTIFACTS.items():
            artifact = by_type[artifact_type]
            expected_checksum = artifact.checksum_sha256
            if expected_checksum and not self.store.verify_checksum(
                preprocessing_run_id, artifact.filename, expected_checksum
            ):
                raise ValueError(
                    f"Checksum verification failed for {artifact.filename}."
                )

            metadata = artifact.metadata_json or {}
            artifact_features = metadata.get("feature_order")
            if artifact_features:
                artifact_features = [
                    name for name in artifact_features
                    if name not in {"email_id", "ground_truth"}
                ]
            if feature_names:
                available = set(artifact_features or [])
                missing_features = set(feature_names) - available
                if missing_features:
                    raise ValueError("Selected feature set is not present in the processed artifact: " + ", ".join(sorted(missing_features)))
                artifact_features = list(feature_names)
            x_values, y_values, names = self._read_split(
                self.store.read_bytes(preprocessing_run_id, artifact.filename),
                split,
                artifact_features,
            )
            if feature_names is None:
                feature_names = names
            elif names != feature_names:
                raise ValueError("Processed splits have different feature order.")
            loaded[split] = (x_values, y_values)

        training, training_labels = loaded["train"]
        validation, validation_labels = loaded["validation"]
        testing, testing_labels = loaded["testing"]
        if len(set(training_labels)) < 2:
            raise ValueError(
                "The training split must contain both Normal and Bombing samples "
                "to train a binary classifier. Choose a dataset version containing "
                "both classes, then preprocess it again."
            )
        return TrainingDataset(
            feature_names=tuple(feature_names or ()),
            training_features=training,
            training_labels=training_labels,
            validation_features=validation,
            validation_labels=validation_labels,
            testing_features=testing,
            testing_labels=testing_labels,
        )


def _append_log(run: MLTrainingRun | MLEvaluationRun, message: str) -> None:
    summary = dict(run.result_summary or {})
    logs = list(summary.get("logs") or [])
    logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": message})
    summary["logs"] = logs
    run.result_summary = summary


def execute_training_run_in_background(training_run_id: UUID) -> None:
    """Run training in an independent database session and register output."""
    db = SessionLocal()
    try:
        run = db.get(MLTrainingRun, training_run_id)
        if run is None or run.status not in {"pending", "queued"}:
            return
        model = db.get(MLModelDefinition, run.model_definition_id)
        if model is None:
            raise ValueError("The model definition was not found.")

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        _append_log(run, "Training started.")
        db.commit()

        snapshot = dict(run.config_snapshot or {})
        selected_features = snapshot.pop("feature_names", None)
        dataset = ProcessedDatasetLoader(db).load(run.preprocessing_run_id, selected_features)
        hyperparameters = dict(model.hyperparameters or {})
        overrides = snapshot.pop("hyperparameters", {})
        if overrides and not isinstance(overrides, dict):
            raise ValueError("Training hyperparameters must be a JSON object.")
        hyperparameters.update(overrides or {})
        random_state = snapshot.pop("random_state", 42)
        if isinstance(random_state, bool) or not isinstance(random_state, int):
            raise ValueError("random_state must be an integer.")
        if snapshot:
            raise ValueError(
                "Unsupported training configuration fields: "
                + ", ".join(sorted(snapshot))
            )

        trainer = ModelTrainer()
        engine = trainer.get_engine(model.algorithm)
        engine.validate_config(
            TrainingConfig(
                hyperparameters=hyperparameters,
                random_state=random_state,
            )
        )
        started = perf_counter()
        result = trainer.train(
            algorithm=model.algorithm,
            dataset=dataset,
            hyperparameters=hyperparameters,
            random_state=random_state,
        )
        duration_ms = max(0, round((perf_counter() - started) * 1000))

        run = db.get(MLTrainingRun, training_run_id)
        if run is None:
            raise ValueError("Training run disappeared during execution.")
        run.status = "completed"
        run.progress_percent = 100
        run.training_sample_count = len(dataset.training_labels)
        run.validation_sample_count = len(dataset.validation_labels)
        run.duration_ms = duration_ms
        run.completed_at = datetime.now(timezone.utc)
        run.config_snapshot = {
            "random_state": random_state,
            "hyperparameters": hyperparameters,
        }
        run.result_summary = {
            "metrics": dict(result.metrics),
            "metadata": dict(result.metadata),
            "feature_count": len(dataset.feature_names),
            "testing_sample_count": len(dataset.testing_labels),
            "logs": list((run.result_summary or {}).get("logs") or []),
        }
        _append_log(run, "Training completed; registering model artifact.")
        db.flush()

        service = MLModelService(db)
        manager = ModelRegistryManager(
            service=service,
            artifact_store=_model_artifact_store(),
        )
        manager.register(
            training_run_id=training_run_id,
            model=result.model,
            metadata={
                "algorithm": model.algorithm,
                "training_metrics": dict(result.metrics),
                "feature_names": list(dataset.feature_names),
            },
        )
        _append_log(run, "Model artifact registered successfully.")
        db.commit()
    except Exception as exc:
        logger.exception("Training run %s failed", training_run_id)
        db.rollback()
        run = db.get(MLTrainingRun, training_run_id)
        if run is not None and run.status not in {"completed", "cancelled"}:
            run.status = "failed"
            run.error_code = type(exc).__name__
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            _append_log(run, f"Training failed: {exc}")
            db.commit()
    finally:
        db.close()


def execute_evaluation_run_in_background(evaluation_run_id: UUID) -> None:
    """Evaluate a registered model against its source preprocessing split."""
    db = SessionLocal()
    try:
        run = db.get(MLEvaluationRun, evaluation_run_id)
        if run is None or run.status != "pending":
            return
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        version = db.get(MLModelVersion, run.model_version_id)
        if version is None:
            raise ValueError("Model version was not found.")
        model = _model_artifact_store().load(
            version.storage_path,
            expected_checksum=version.checksum_sha256,
        )
        training_run = db.get(MLTrainingRun, version.training_run_id)
        selected_features = (training_run.config_snapshot or {}).get("feature_names") if training_run else None
        dataset = ProcessedDatasetLoader(db).load(run.preprocessing_run_id, selected_features)
        started = perf_counter()
        result = ModelEvaluator().evaluate(
            model=model,
            dataset=dataset,
            split=run.evaluation_split,
        )
        metrics = result.metrics

        run = db.get(MLEvaluationRun, evaluation_run_id)
        if run is None:
            raise ValueError("Evaluation run disappeared during execution.")
        run.status = "completed"
        run.sample_count = result.sample_count
        run.accuracy = metrics.accuracy
        run.precision = metrics.precision
        run.recall = metrics.recall
        run.f1_score = metrics.f1_score
        run.roc_auc = metrics.roc_auc
        run.confusion_matrix = metrics.confusion_matrix
        run.classification_report = metrics.classification_report
        run.duration_ms = max(0, round((perf_counter() - started) * 1000))
        run.completed_at = datetime.now(timezone.utc)
        run.result_summary = {
            "split": result.split,
            "prediction_count": len(result.predictions),
        }
        db.commit()
    except Exception as exc:
        logger.exception("Evaluation run %s failed", evaluation_run_id)
        db.rollback()
        run = db.get(MLEvaluationRun, evaluation_run_id)
        if run is not None and run.status not in {"completed", "cancelled"}:
            run.status = "failed"
            run.error_code = type(exc).__name__
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
