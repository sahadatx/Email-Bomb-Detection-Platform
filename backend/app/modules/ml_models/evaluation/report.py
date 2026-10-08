
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from app.modules.ml_models.engine.evaluator import EvaluationResult


class EvaluationReportError(Exception):
    """Base exception for evaluation report errors."""


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Serializable evaluation report."""

    model_version_id: str
    preprocessing_run_id: str
    split: str
    sample_count: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None
    confusion_matrix: Mapping[str, int]
    classification_report: Mapping[str, Any]
    predictions: list[int]
    generated_at: str
    metadata: Mapping[str, Any]


class EvaluationReportBuilder:
    """Build serializable reports from evaluation results."""

    @staticmethod
    def _validate_uuid(value: UUID, field_name: str) -> str:
        if not isinstance(value, UUID):
            raise EvaluationReportError(
                f"{field_name} must be a UUID."
            )
        return str(value)

    @staticmethod
    def _validate_result(result: EvaluationResult) -> None:
        if not isinstance(result, EvaluationResult):
            raise EvaluationReportError(
                "result must be an EvaluationResult instance."
            )

        if result.split not in {"validation", "testing"}:
            raise EvaluationReportError(
                "Evaluation split must be validation or testing."
            )

        if result.sample_count < 1:
            raise EvaluationReportError(
                "Evaluation sample_count must be positive."
            )

        if len(result.predictions) != result.sample_count:
            raise EvaluationReportError(
                "Prediction count does not match sample_count."
            )

    def build(
        self,
        *,
        result: EvaluationResult,
        model_version_id: UUID,
        preprocessing_run_id: UUID,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvaluationReport:
        """Build a report from an evaluation result."""

        self._validate_result(result)

        model_id = self._validate_uuid(
            model_version_id,
            "model_version_id",
        )
        preprocessing_id = self._validate_uuid(
            preprocessing_run_id,
            "preprocessing_run_id",
        )

        metrics = result.metrics

        report = EvaluationReport(
            model_version_id=model_id,
            preprocessing_run_id=preprocessing_id,
            split=result.split,
            sample_count=result.sample_count,
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            roc_auc=metrics.roc_auc,
            confusion_matrix=dict(metrics.confusion_matrix),
            classification_report=dict(
                metrics.classification_report
            ),
            predictions=list(result.predictions),
            generated_at=datetime.now(timezone.utc).isoformat(),
            metadata=dict(metadata or {}),
        )

        # Ensure the report contains JSON-compatible values.
        try:
            json.dumps(asdict(report), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise EvaluationReportError(
                "Evaluation report contains non-JSON-compatible values."
            ) from exc

        return report

    @staticmethod
    def to_dict(report: EvaluationReport) -> dict[str, Any]:
        """Convert a report into a JSON-compatible dictionary."""

        if not isinstance(report, EvaluationReport):
            raise EvaluationReportError(
                "report must be an EvaluationReport instance."
            )

        try:
            data = asdict(report)
            # Round-trip ensures JSON-compatible primitive values.
            return json.loads(
                json.dumps(data, allow_nan=False)
            )
        except (TypeError, ValueError) as exc:
            raise EvaluationReportError(
                "Unable to serialize evaluation report."
            ) from exc

    @staticmethod
    def to_json(
        report: EvaluationReport,
        *,
        indent: int = 2,
    ) -> str:
        """Serialize a report to a JSON string."""

        if not isinstance(report, EvaluationReport):
            raise EvaluationReportError(
                "report must be an EvaluationReport instance."
            )

        if (
            isinstance(indent, bool)
            or not isinstance(indent, int)
            or indent < 0
        ):
            raise EvaluationReportError(
                "indent must be a non-negative integer."
            )

        try:
            return json.dumps(
                asdict(report),
                indent=indent,
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise EvaluationReportError(
                "Unable to serialize evaluation report."
            ) from exc