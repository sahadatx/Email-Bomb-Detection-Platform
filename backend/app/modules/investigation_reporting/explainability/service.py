from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..errors import InvestigationError
from ..models import AnalystNote, AnalystNoteEvent
from .explainers.feature_contribution import FeatureContributionExplainer
from .explainers.rule_explainer import RuleExplainer
from .explainers.shap_explainer import ShapExplainer
from .repository import ExplainabilityRepository


class ExplainabilityService:
    """Build explanations from persisted analysis and manage analyst annotations."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.repository = ExplainabilityRepository(db) if db is not None else None
        self._model_background_cache: dict[UUID, tuple[Any, Any, list[str], UUID]] = {}
        self.feature = FeatureContributionExplainer()
        self.rules = RuleExplainer()
        self.shap = ShapExplainer()

    def explain(self, detection: dict[str, Any], *, model=None, model_input=None, background=None, feature_names=None) -> dict[str, Any]:
        baseline = background
        if background is not None:
            try:
                import numpy as np
                baseline = np.asarray(background, dtype=float).mean(axis=0)
            except (ImportError, TypeError, ValueError):
                baseline = None
        feature = self.feature.explain(detection, model=model, model_input=model_input, baseline=baseline, feature_names=feature_names)
        rules = self.rules.explain(detection)
        shap_result = self.shap.explain(detection, model=model, model_input=model_input, background=background, feature_names=feature_names)
        available = [item for item in (feature, rules, shap_result) if item["status"] != "unavailable"]
        return {
            "status": "partial" if available else "unavailable",
            "method": ",".join(item["method"] for item in available) or "none",
            "feature_contributions": feature["feature_contributions"],
            "triggered_rules": rules["triggered_rules"],
            "risk_breakdown": rules["risk_breakdown"],
            "behavioral_signals": rules["behavioral_signals"],
            "shap": shap_result,
            "limitations": " ".join(filter(None, (feature.get("limitations"), shap_result.get("limitations")))),
        }

    def list(self, *, page: int, page_size: int, **filters: Any) -> dict[str, Any]:
        repository = self._repository()
        records, total = repository.list_detections(page=page, page_size=page_size, **filters)
        return {"items": [self.explain_record(item) for item in records], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size)}

    def detail(self, detection_id: UUID) -> dict[str, Any]:
        repository = self._repository()
        detection = repository.get_detection(detection_id)
        if detection is None:
            raise InvestigationError("Detection record not found.")
        result = self.explain_record(detection, include_model_explanation=True)
        result["analyst_notes"] = repository.notes_for_detection(detection_id)
        return result

    def add_note(self, detection_id: UUID, actor_id: str, values: dict[str, Any]) -> AnalystNote:
        repository = self._repository()
        if not repository.detection_exists(detection_id):
            raise InvestigationError("Detection record not found.")
        body = str(values.get("body") or "").strip()
        if not body:
            raise InvestigationError("Analyst note body is required.")
        note = AnalystNote(detection_id=detection_id, author_id=actor_id, title=self._clean_title(values.get("title")), body=body, category=values.get("category", "observation"))
        repository.add_note(note)
        repository.flush()
        repository.add_note_event(AnalystNoteEvent(note_id=note.id, detection_id=detection_id, actor_id=actor_id, action="created", after_data=self._note_snapshot(note)))
        repository.flush()
        return note

    def update_note(self, note_id: UUID, actor_id: str, values: dict[str, Any], *, is_admin: bool = False) -> AnalystNote:
        repository = self._repository()
        note = repository.note(note_id)
        if note is None:
            raise InvestigationError("Analyst note not found.")
        if note.author_id != actor_id and not is_admin:
            raise PermissionError("Only the note author or an administrator may update this note.")
        body = str(values.get("body") or "").strip()
        if not body:
            raise InvestigationError("Analyst note body is required.")
        before = self._note_snapshot(note)
        note.title = self._clean_title(values.get("title"))
        note.body = body
        note.category = values["category"]
        note.updated_at = datetime.now(timezone.utc)
        repository.add_note_event(AnalystNoteEvent(note_id=note.id, detection_id=note.detection_id, actor_id=actor_id, action="updated", before_data=before, after_data=self._note_snapshot(note)))
        repository.flush()
        return note

    def delete_note(self, note_id: UUID, actor_id: str, *, is_admin: bool = False) -> None:
        repository = self._repository()
        note = repository.note(note_id)
        if note is None:
            raise InvestigationError("Analyst note not found.")
        if note.author_id != actor_id and not is_admin:
            raise PermissionError("Only the note author or an administrator may delete this note.")
        repository.add_note_event(AnalystNoteEvent(note_id=note.id, detection_id=note.detection_id, actor_id=actor_id, action="deleted", before_data=self._note_snapshot(note)))
        self.db.delete(note)

    def note_audit(self, note_id: UUID) -> list[AnalystNoteEvent]:
        repository = self._repository()
        if repository.note(note_id) is None:
            raise InvestigationError("Analyst note not found.")
        return repository.note_events(note_id)

    def explain_record(self, detection: dict[str, Any], *, include_model_explanation: bool = False) -> dict[str, Any]:
        if not include_model_explanation:
            return {**detection, "explanation": self.explain(detection)}
        try:
            model, model_input, background, names = self._model_context(detection)
            result = self.explain(detection, model=model, model_input=model_input, background=background, feature_names=names)
        except Exception as exc:
            result = self.explain(detection)
            result["limitations"] = f"{result['limitations']} Version-matched model explanation is unavailable: {exc}"
        return {**detection, "explanation": result}

    def _model_context(self, detection: dict[str, Any]):
        """Load the exact registered model and its training background safely."""
        if self.db is None:
            raise RuntimeError("A database session is required to load model context.")
        from app.modules.detection.service import DetectionService
        from app.modules.ml_models.models import MLModelVersion, MLTrainingRun
        from app.modules.ml_models.registry.manager import ModelRegistryManager
        from app.modules.ml_models.service import MLModelService
        from app.modules.ml_models.storage.artifact_store import ModelArtifactStore
        from app.modules.ml_models.runtime import ProcessedDatasetLoader
        import numpy as np

        version_id = detection.get("model_version_id")
        version = self.db.get(MLModelVersion, version_id) if version_id else None
        if version is None:
            raise RuntimeError("The detection has no registered model version.")
        training_run = self.db.get(MLTrainingRun, version.training_run_id)
        if training_run is None or training_run.status != "completed":
            raise RuntimeError("The source training run is unavailable or incomplete.")
        cached = self._model_background_cache.get(version.id)
        if cached is None:
            feature_names = list((version.metadata_json or {}).get("feature_names") or [])
            if not feature_names:
                raise RuntimeError("The model version does not record its feature order.")
            dataset = ProcessedDatasetLoader(self.db).load(training_run.preprocessing_run_id)
            if list(dataset.feature_names) != feature_names:
                raise RuntimeError("Model feature order does not match its preprocessing artifacts.")
            training_rows = np.asarray(dataset.training_features, dtype=float)
            if training_rows.ndim != 2 or training_rows.shape[1] != len(feature_names) or not len(training_rows):
                raise RuntimeError("The training split does not contain a usable feature background.")
            # Deterministically sample both classes to keep model explanations bounded.
            background_indexes = []
            labels = np.asarray(dataset.training_labels)
            classes = np.unique(labels)
            per_class = max(1, 32 // max(1, len(classes)))
            for label in classes:
                candidates = np.flatnonzero(labels == label)
                chosen = np.linspace(0, len(candidates) - 1, min(per_class, len(candidates)), dtype=int)
                background_indexes.extend(candidates[chosen].tolist())
            if not background_indexes:
                raise RuntimeError("The training split has no background rows.")
            background = training_rows[background_indexes]
            storage = ModelArtifactStore(os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models"))
            registry = ModelRegistryManager(service=MLModelService(self.db), artifact_store=storage)
            model = registry.load_model(version.id)
            cached = (model, background, feature_names, training_run.preprocessing_run_id)
            self._model_background_cache[version.id] = cached
        model, background, feature_names, preprocessing_run_id = cached
        _, transformed = DetectionService.transform_feature_row(detection.get("feature_snapshot") or {}, preprocessing_run_id, feature_names)
        return model, np.asarray([transformed], dtype=float), background, feature_names

    def _repository(self) -> ExplainabilityRepository:
        if self.repository is None or self.db is None:
            raise RuntimeError("Database-backed explainability requires a database session.")
        return self.repository

    @staticmethod
    def _clean_title(value: str | None) -> str | None:
        normalized = value.strip() if value else ""
        return normalized or None

    @staticmethod
    def _note_snapshot(note: AnalystNote) -> dict[str, Any]:
        return {"title": note.title, "body": note.body, "category": note.category}
