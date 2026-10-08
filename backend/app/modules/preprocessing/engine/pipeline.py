
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Mapping, Sequence
from uuid import UUID

from app.modules.preprocessing.config.validator import (
    PreprocessingConfigValidator,
)
from app.modules.preprocessing.engine.schema_validator import (
    FeatureSchemaValidator,
)
from app.modules.preprocessing.engine.missing_values import (
    MissingValueProcessor,
)
from app.modules.preprocessing.engine.scaler import FeatureScaler
from app.modules.preprocessing.storage.artifact_store import (
    ArtifactStore,
    StoredArtifact,
)


class PreprocessingPipelineError(RuntimeError):
    """Raised when preprocessing cannot be completed."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "PREPROCESSING_FAILED",
        stage: str = "unknown",
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.stage = stage


@dataclass(frozen=True)
class PreprocessingResult:
    """Summary of a successfully completed preprocessing run."""

    run_id: str
    input_sample_count: int
    output_sample_count: int
    training_count: int
    validation_count: int
    testing_count: int
    feature_count: int
    duration_ms: int
    artifacts: tuple[StoredArtifact, ...]
    config_snapshot: dict[str, Any]
    result_summary: dict[str, Any]


class PreprocessingPipeline:
    """
    Execute preprocessing for a validated dataset version.

    Input rows must contain:
        email_id
        ground_truth
        F1 ... F12 (or the selected feature order)

    Only feature fields are imputed and scaled.
    Email IDs and ground-truth labels are preserved unchanged.

    Imputation and scaling are fitted exclusively on training data.
    Validation and testing data use the fitted training parameters.
    """

    ID_FIELD = "email_id"
    LABEL_FIELD = "ground_truth"

    def __init__(
        self,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.artifact_store = artifact_store or ArtifactStore()

    @staticmethod
    def _validate_rows(
        rows: Sequence[Mapping[str, Any]],
        split_name: str,
    ) -> None:
        if not isinstance(rows, Sequence) or isinstance(
            rows, (str, bytes)
        ):
            raise PreprocessingPipelineError(
                f"{split_name} data must be a sequence of rows.",
                error_code="INVALID_INPUT_DATA",
                stage="input_validation",
            )

        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} must be a mapping.",
                    error_code="INVALID_INPUT_DATA",
                    stage="input_validation",
                )

            if "email_id" not in row:
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} is missing email_id.",
                    error_code="MISSING_RECORD_ID",
                    stage="input_validation",
                )

            if row["email_id"] is None or str(row["email_id"]).strip() == "":
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} has an empty email_id.",
                    error_code="INVALID_RECORD_ID",
                    stage="input_validation",
                )

            if "ground_truth" not in row:
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} is missing ground_truth.",
                    error_code="MISSING_GROUND_TRUTH",
                    stage="input_validation",
                )

            if row["ground_truth"] not in {"normal", "bombing"}:
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} has an invalid ground_truth.",
                    error_code="INVALID_GROUND_TRUTH",
                    stage="input_validation",
                )

    @classmethod
    def _prepare_rows(
        cls,
        rows: Sequence[Mapping[str, Any]],
        feature_order: Sequence[str],
        split_name: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Separate record metadata from feature values.

        Returns:
            features: rows containing only selected features
            metadata: rows containing email_id and ground_truth
        """
        features: list[dict[str, Any]] = []
        metadata: list[dict[str, Any]] = []

        for index, row in enumerate(rows):
            missing = set(feature_order) - set(row)
            if missing:
                raise PreprocessingPipelineError(
                    f"{split_name} row {index} is missing features: "
                    + ", ".join(sorted(missing)),
                    error_code="FEATURE_SCHEMA_MISMATCH",
                    stage="schema_validation",
                )

            features.append(
                {feature: row[feature] for feature in feature_order}
            )
            metadata.append(
                {
                    cls.ID_FIELD: str(row[cls.ID_FIELD]),
                    cls.LABEL_FIELD: row[cls.LABEL_FIELD],
                }
            )

        return features, metadata

    @staticmethod
    def _duplicate_key(row: Mapping[str, Any]) -> str:
        """Identify the source sample, independent of its feature values."""
        return str(row["email_id"])

    @classmethod
    def _check_duplicates(
        cls,
        splits: Mapping[
            str, Sequence[Mapping[str, Any]]
        ],
    ) -> dict[str, Any]:
        """
        Detect repeated source samples within and across splits.

        The first occurrence is retained for reporting only.
        No records are removed.
        """
        seen: dict[str, tuple[str, int]] = {}
        duplicates: list[dict[str, Any]] = []

        for split_name, rows in splits.items():
            for index, row in enumerate(rows):
                key = cls._duplicate_key(row)

                if key in seen:
                    first_split, first_index = seen[key]
                    duplicates.append(
                        {
                            "first_split": first_split,
                            "first_row": first_index,
                            "duplicate_split": split_name,
                            "duplicate_row": index,
                        }
                    )
                else:
                    seen[key] = (split_name, index)

        if duplicates:
            cross_split_count = sum(
                1
                for item in duplicates
                if item["first_split"] != item["duplicate_split"]
            )

            raise PreprocessingPipelineError(
                "Duplicate samples detected (repeated email_id): "
                f"{len(duplicates)} duplicate occurrence(s), "
                f"including {cross_split_count} cross-split "
                "duplicate(s).",
                error_code="DUPLICATE_RECORDS_FOUND",
                stage="duplicate_check",
            )

        return {
            "enabled": True,
            "duplicate_count": 0,
            "cross_split_duplicate_count": 0,
        }

    @staticmethod
    def _restore_metadata(
        transformed_rows: Sequence[Mapping[str, Any]],
        metadata_rows: Sequence[Mapping[str, Any]],
        feature_order: Sequence[str],
    ) -> list[dict[str, Any]]:
        """Combine transformed features with unchanged record metadata."""

        if len(transformed_rows) != len(metadata_rows):
            raise PreprocessingPipelineError(
                "Preprocessing changed the number of rows; "
                "record metadata cannot be aligned safely.",
                error_code="ROW_COUNT_MISMATCH",
                stage="metadata_alignment",
            )

        output: list[dict[str, Any]] = []

        for features, metadata in zip(
            transformed_rows, metadata_rows
        ):
            row = {
                "email_id": metadata["email_id"],
                "ground_truth": metadata["ground_truth"],
            }
            row.update(
                {
                    feature: features[feature]
                    for feature in feature_order
                }
            )
            output.append(row)

        return output

    @staticmethod
    def _state_metadata(
        imputer: MissingValueProcessor,
        scaler: FeatureScaler,
    ) -> dict[str, Any]:
        """Create JSON-compatible transformer metadata."""

        imputer_state = imputer.state
        scaler_state = scaler.state

        return {
            "imputer": {
                "strategy": imputer_state.strategy,
                "feature_values": imputer_state.feature_values,
                "dropped_features": list(
                    imputer_state.dropped_features
                ),
            },
            "scaler": {
                "strategy": scaler_state.strategy,
                "feature_order": list(scaler_state.feature_order),
                "feature_states": {
                    feature: {
                        "strategy": state.strategy,
                        "minimum": state.minimum,
                        "maximum": state.maximum,
                        "mean": state.mean,
                        "scale": state.scale,
                    }
                    for feature, state
                    in scaler_state.feature_states.items()
                },
            },
        }

    def run(
        self,
        *,
        run_id: str | UUID,
        dataset_schema: Mapping[str, Any],
        training_rows: Sequence[Mapping[str, Any]],
        validation_rows: Sequence[Mapping[str, Any]],
        testing_rows: Sequence[Mapping[str, Any]],
        config: Mapping[str, Any],
    ) -> PreprocessingResult:
        """Execute preprocessing and persist its artifacts."""

        started = perf_counter()
        stage = "configuration_validation"

        try:
            if not isinstance(config, Mapping):
                raise PreprocessingPipelineError(
                    "Configuration must be a mapping.",
                    error_code="INVALID_CONFIGURATION",
                    stage=stage,
                )

            config_snapshot = PreprocessingConfigValidator.validate(
                dict(config)
            )
            feature_order = tuple(
                config_snapshot["feature_order"]
            )

            stage = "input_validation"

            self._validate_rows(training_rows, "Training")
            self._validate_rows(validation_rows, "Validation")
            self._validate_rows(testing_rows, "Testing")

            if not training_rows:
                raise PreprocessingPipelineError(
                    "Training data cannot be empty.",
                    error_code="EMPTY_TRAINING_DATA",
                    stage=stage,
                )

            input_count = (
                len(training_rows)
                + len(validation_rows)
                + len(testing_rows)
            )

            stage = "schema_validation"

            schema_result = FeatureSchemaValidator.validate(
                dataset_schema,
                expected_features=feature_order,
            )

            train, train_metadata = self._prepare_rows(
                training_rows,
                schema_result.feature_order,
                "Training",
            )
            validation, validation_metadata = self._prepare_rows(
                validation_rows,
                schema_result.feature_order,
                "Validation",
            )
            testing, testing_metadata = self._prepare_rows(
                testing_rows,
                schema_result.feature_order,
                "Testing",
            )

            stage = "duplicate_check"

            if config_snapshot.get("check_duplicates", True):
                duplicate_summary = self._check_duplicates(
                    {
                        "train": training_rows,
                        "validation": validation_rows,
                        "test": testing_rows,
                    }
                )
            else:
                duplicate_summary = {
                    "enabled": False,
                    "duplicate_count": None,
                    "cross_split_duplicate_count": None,
                }

            stage = "missing_value_processing"

            missing_strategy = config_snapshot[
                "missing_value_strategy"
            ]

            imputer = MissingValueProcessor(
                strategy=missing_strategy,
                constant_value=config_snapshot.get(
                    "missing_value_constant"
                ),
                feature_order=feature_order,
            )

            # Fit only on training rows.
            imputer.fit(train)

            train = imputer.transform(train)
            validation = imputer.transform(validation)
            testing = imputer.transform(testing)

            stage = "scaling"

            scaling_strategy = config_snapshot[
                "scaling_strategy"
            ]
            scaling_features = config_snapshot.get(
                "scaling_features", []
            )

            scaler = FeatureScaler(
                strategy=scaling_strategy,
                scaling_features=scaling_features,
                feature_order=feature_order,
            )

            # Fit only on the imputed training split.
            scaler.fit(train)

            train = scaler.transform(train)
            validation = scaler.transform(validation)
            testing = scaler.transform(testing)

            # The "drop" strategy may remove rows. Align metadata
            # using the same retained email IDs.
            def align_metadata(
                transformed: Sequence[Mapping[str, Any]],
                original: Sequence[Mapping[str, Any]],
            ) -> list[dict[str, Any]]:
                remaining_ids = [
                    str(row["email_id"])
                    for row in original
                ]
                transformed_count = len(transformed)

                if transformed_count == len(remaining_ids):
                    return [dict(row) for row in original]

                # Drop strategy retains rows without missing values.
                retained: list[dict[str, Any]] = []
                for row, metadata in zip(original, remaining_ids):
                    retained.append(dict(row))
                    if len(retained) == transformed_count:
                        break
                return retained

            # Rebuild the retained metadata correctly by applying
            # the same drop predicate to the original feature rows.
            if missing_strategy == "drop":
                def retained_metadata(
                    original_features: Sequence[Mapping[str, Any]],
                    original_metadata: Sequence[Mapping[str, Any]],
                ) -> list[dict[str, Any]]:
                    retained = []
                    for features, metadata in zip(
                        original_features, original_metadata
                    ):
                        if not any(
                            value is None
                            or (
                                isinstance(value, str)
                                and not value.strip()
                            )
                            for value in features.values()
                        ):
                            retained.append(dict(metadata))
                    return retained

                # Use the pre-imputation source rows to identify
                # exactly which records survived dropping.
                train_metadata = retained_metadata(
                    self._prepare_rows(
                        training_rows, feature_order, "Training"
                    )[0],
                    train_metadata,
                )
                validation_metadata = retained_metadata(
                    self._prepare_rows(
                        validation_rows, feature_order, "Validation"
                    )[0],
                    validation_metadata,
                )
                testing_metadata = retained_metadata(
                    self._prepare_rows(
                        testing_rows, feature_order, "Testing"
                    )[0],
                    testing_metadata,
                )

            train_output = self._restore_metadata(
                train, train_metadata, feature_order
            )
            validation_output = self._restore_metadata(
                validation, validation_metadata, feature_order
            )
            testing_output = self._restore_metadata(
                testing, testing_metadata, feature_order
            )

            stage = "artifact_storage"

            artifacts: list[StoredArtifact] = []

            artifacts.append(
                self.artifact_store.save_dataset(
                    run_id,
                    "train_processed",
                    train_output,
                    ("email_id", "ground_truth", *feature_order),
                )
            )
            artifacts.append(
                self.artifact_store.save_dataset(
                    run_id,
                    "validation_processed",
                    validation_output,
                    ("email_id", "ground_truth", *feature_order),
                )
            )
            artifacts.append(
                self.artifact_store.save_dataset(
                    run_id,
                    "test_processed",
                    testing_output,
                    ("email_id", "ground_truth", *feature_order),
                )
            )

            artifacts.append(
                self.artifact_store.save_transformer(
                    run_id, "imputer", imputer.state
                )
            )
            artifacts.append(
                self.artifact_store.save_transformer(
                    run_id, "scaler", scaler.state
                )
            )

            duration_ms = int(
                (perf_counter() - started) * 1000
            )

            output_count = (
                len(train_output)
                + len(validation_output)
                + len(testing_output)
            )

            def class_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
                """Count the persisted ground-truth classes for one split."""
                counts = {"normal": 0, "bombing": 0}
                for row in rows:
                    label = str(row.get(self.LABEL_FIELD, "")).strip().lower()
                    if label in counts:
                        counts[label] += 1
                return counts

            class_distribution = {
                "train": class_counts(train_output),
                "validation": class_counts(validation_output),
                "test": class_counts(testing_output),
            }

            result_summary = {
                "status": "completed",
                "input_sample_count": input_count,
                "output_sample_count": output_count,
                "training_count": len(train_output),
                "validation_count": len(validation_output),
                "testing_count": len(testing_output),
                "class_distribution": class_distribution,
                "feature_count": len(feature_order),
                "duration_ms": duration_ms,
                "missing_value_strategy": missing_strategy,
                "scaling_strategy": scaling_strategy,
                "duplicate_check": duplicate_summary,
            }

            metadata = {
                "run_id": str(run_id),
                "status": "completed",
                "config": config_snapshot,
                "feature_order": list(feature_order),
                "feature_types": schema_result.feature_types,
                "input_sample_count": input_count,
                "output_sample_count": output_count,
                "training_count": len(train_output),
                "validation_count": len(validation_output),
                "testing_count": len(testing_output),
                "class_distribution": class_distribution,
                "feature_count": len(feature_order),
                "duration_ms": duration_ms,
                "duplicate_check": duplicate_summary,
                "transformers": self._state_metadata(
                    imputer, scaler
                ),
                "artifacts": [
                    {
                        "artifact_type": artifact.artifact_type,
                        "filename": artifact.filename,
                        "size_bytes": artifact.size_bytes,
                        "checksum_sha256": (
                            artifact.checksum_sha256
                        ),
                    }
                    for artifact in artifacts
                ],
            }

            artifacts.append(
                self.artifact_store.save_metadata(
                    run_id, metadata
                )
            )

            return PreprocessingResult(
                run_id=str(run_id),
                input_sample_count=input_count,
                output_sample_count=output_count,
                training_count=len(train_output),
                validation_count=len(validation_output),
                testing_count=len(testing_output),
                feature_count=len(feature_order),
                duration_ms=duration_ms,
                artifacts=tuple(artifacts),
                config_snapshot=config_snapshot,
                result_summary=result_summary,
            )

        except PreprocessingPipelineError:
            try:
                self.artifact_store.delete_run_artifacts(run_id)
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                self.artifact_store.delete_run_artifacts(run_id)
            except Exception:
                pass

            raise PreprocessingPipelineError(
                str(exc),
                error_code="PREPROCESSING_FAILED",
                stage=stage,
            ) from exc
