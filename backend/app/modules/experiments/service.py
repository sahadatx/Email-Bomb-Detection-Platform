from datetime import datetime, timezone
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import select

from app.modules.audit_security_admin.audit.service import record_audit
from app.modules.audit_security_admin.models import AuditEvent
from app.modules.ml_models.models import MLModelDefinition, MLTrainingRun, MLEvaluationRun, MLModelVersion
from app.modules.ml_models.service import MLModelService
from app.modules.preprocessing.config.validator import FEATURE_TYPES
from .errors import ExperimentConflict, ExperimentNotFound, ExperimentValidationError
from .integrations.dataset_adapter import DatasetAdapter
from .integrations.model_adapter import ModelAdapter
from .models import Experiment, ExperimentRun
from .repository import ExperimentRepository
from .validators import validate_split_counts, validate_training_config


class ExperimentService:
    def __init__(self, db):
        self.db = db
        self.repo = ExperimentRepository(db)
        self.datasets = DatasetAdapter(db)
        self.models = ModelAdapter(db)

    def options(self):
        return {"models": self.models.active_models(), "preprocessing_runs": self.datasets.completed_sources(), "feature_types": ["boolean", "integer", "float"]}

    def create(self, payload, actor):
        model = self.db.get(MLModelDefinition, payload.model_definition_id)
        if model is None or model.status != "active": raise ExperimentValidationError("Select an active model definition.")
        version, prep, _dataset, available_features = self.datasets.validate_source(payload.dataset_version_id, payload.preprocessing_run_id)
        validate_split_counts(
            prep.training_count,
            prep.validation_count,
            prep.testing_count,
            payload.evaluation_split,
        )
        config = validate_training_config(payload.training_config)
        model_parameters = dict(model.hyperparameters or {})
        model_parameters.update(config["hyperparameters"])
        MLModelService._validate_model_configuration(model.algorithm, model_parameters)
        features = payload.feature_set or [name for name in available_features if FEATURE_TYPES.get(name) in {"boolean", "integer", "float"}]
        if not features: raise ExperimentValidationError("The preprocessing run has no supported numeric features.")
        if len(set(features)) != len(features) or set(features) - set(available_features): raise ExperimentValidationError("Feature set must contain unique features from the selected preprocessing run.")
        experiment = Experiment(id=uuid4(), code="EXP-" + uuid4().hex[:8].upper(), name=payload.name, description=payload.description, model_definition_id=model.id, dataset_version_id=version.id, preprocessing_run_id=prep.id, feature_set_snapshot={"features": features}, training_config=config, evaluation_config={"split": payload.evaluation_split}, status="draft", created_by_id=actor.id)
        self.repo.create(experiment)
        record_audit(self.db, actor=actor, action="experiment.created", target_type="experiment", target_id=experiment.id, target_label=experiment.name, source="Experiments", details={"code": experiment.code, "model_definition_id": str(model.id), "dataset_version_id": str(version.id)})
        self.db.flush()
        return self.repo.item(experiment)

    def get(self, experiment_id):
        item = self.repo.get(experiment_id)
        if item is None: raise ExperimentNotFound("Experiment was not found.")
        result = self.repo.item(item)
        result["runs"] = [self.repo.run_item(run, self.db.get(MLEvaluationRun, run.evaluation_run_id) if run.evaluation_run_id else None, self._model_version_for_evaluation(run.evaluation_run_id)) for run in self.repo.runs(item.id)]
        return result

    def _model_version_for_evaluation(self, evaluation_id):
        evaluation = self.db.get(MLEvaluationRun, evaluation_id) if evaluation_id else None
        return self.db.get(MLModelVersion, evaluation.model_version_id) if evaluation else None

    def list(self, *, page=1, page_size=30, search=None, status=None, model_definition_id=None, dataset_version_id=None, from_date=None, to_date=None, sort="newest"):
        rows, total = self.repo.list(page=page, page_size=page_size, search=search, status=status, model_definition_id=model_definition_id, dataset_version_id=dataset_version_id, from_date=from_date, to_date=to_date, sort=sort)
        return {"items": self.repo.list_items(rows), "total": total, "page": page, "page_size": page_size, "total_pages": max(1, ceil(total / page_size)), "summary": self.repo.summary()}

    def update(self, experiment_id, changes, actor):
        item = self.repo.get(experiment_id)
        if item is None: raise ExperimentNotFound("Experiment was not found.")
        if self.repo.runs(item.id): raise ExperimentConflict("Experiment configuration is locked after the first run is created.")
        if "name" in changes and changes["name"] is not None: item.name = changes["name"].strip()
        if "description" in changes: item.description = changes["description"]
        if "training_config" in changes and changes["training_config"] is not None:
            config = validate_training_config(changes["training_config"])
            model = self.db.get(MLModelDefinition, item.model_definition_id)
            model_parameters = dict(model.hyperparameters or {})
            model_parameters.update(config["hyperparameters"])
            MLModelService._validate_model_configuration(model.algorithm, model_parameters)
            item.training_config = config
        if "evaluation_split" in changes and changes["evaluation_split"]:
            _, prep, _, _ = self.datasets.validate_source(item.dataset_version_id, item.preprocessing_run_id)
            validate_split_counts(prep.training_count, prep.validation_count, prep.testing_count, changes["evaluation_split"])
            item.evaluation_config = {"split": changes["evaluation_split"]}
        if "feature_set" in changes and changes["feature_set"] is not None:
            _, _, _, available = self.datasets.validate_source(item.dataset_version_id, item.preprocessing_run_id)
            names = changes["feature_set"]
            if not names or len(set(names)) != len(names) or set(names) - set(available): raise ExperimentValidationError("Feature set must contain unique features from the selected preprocessing run.")
            item.feature_set_snapshot = {"features": names}
        item.updated_at = datetime.now(timezone.utc)
        record_audit(self.db, actor=actor, action="experiment.updated", target_type="experiment", target_id=item.id, target_label=item.name, source="Experiments", details={"changed_fields": sorted(changes)})
        return self.repo.item(item)

    def delete(self, experiment_id, actor):
        item = self.repo.get(experiment_id)
        if item is None: raise ExperimentNotFound("Experiment was not found.")
        if self.repo.active_run(item.id): raise ExperimentConflict("An experiment cannot be deleted while a run is active.")
        item.deleted_at = datetime.now(timezone.utc)
        record_audit(self.db, actor=actor, action="experiment.deleted", target_type="experiment", target_id=item.id, target_label=item.name, source="Experiments", details={"code": item.code})

    def create_run(self, experiment_id, actor):
        experiment = self.repo.get(experiment_id)
        if experiment is None: raise ExperimentNotFound("Experiment was not found.")
        if self.repo.active_run(experiment.id): raise ExperimentConflict("This experiment already has an active run.")
        model_service = MLModelService(self.db)
        config = dict(experiment.training_config or {})
        config["feature_names"] = experiment.feature_set_snapshot.get("features", [])
        training = model_service.create_training_run(model_definition_id=experiment.model_definition_id, preprocessing_run_id=experiment.preprocessing_run_id, config_snapshot=config)
        training = model_service.update_training_run(training.id, status="queued")
        run = ExperimentRun(experiment_id=experiment.id, training_run_id=training.id, status="queued", progress_percent=1, logs=[{"timestamp": datetime.now(timezone.utc).isoformat(), "message": "Experiment run queued; existing ML training workflow will execute."}])
        self.repo.create_run(run)
        experiment.status = "queued"
        experiment.updated_at = datetime.now(timezone.utc)
        record_audit(self.db, actor=actor, action="experiment.run_queued", target_type="experiment", target_id=experiment.id, target_label=experiment.code, source="Experiments", details={"experiment_run_id": str(run.id), "training_run_id": str(training.id)})
        self.db.flush()
        return run

    def run_detail(self, run_id):
        run = self.repo.get_run(run_id)
        if run is None: raise ExperimentNotFound("Experiment run was not found.")
        experiment = self.repo.get(run.experiment_id)
        evaluation = self.db.get(MLEvaluationRun, run.evaluation_run_id) if run.evaluation_run_id else None
        version = self.db.get(MLModelVersion, evaluation.model_version_id) if evaluation else None
        result = self.repo.run_item(run, evaluation, version)
        result.update({"experiment_id": str(experiment.id), "experiment_code": experiment.code, "experiment_name": experiment.name, "training_run": self._training_summary(run.training_run_id), "evaluation": self._evaluation_summary(evaluation)})
        return result

    def _training_summary(self, run_id):
        row = self.db.get(MLTrainingRun, run_id)
        return {"id": str(row.id), "status": row.status, "progress_percent": row.progress_percent, "error_message": row.error_message, "created_at": row.created_at.isoformat() if row.created_at else None} if row else None

    @staticmethod
    def _evaluation_summary(row):
        return {"id": str(row.id), "status": row.status, "split": row.evaluation_split, "accuracy": row.accuracy, "precision": row.precision, "recall": row.recall, "f1_score": row.f1_score, "sample_count": row.sample_count, "error_message": row.error_message} if row else None

    def compare(self, experiment_ids):
        rows = self.repo.comparison(experiment_ids)
        if len(rows) != len(set(experiment_ids)): raise ExperimentValidationError("Select at least two completed experiments with completed evaluations.")
        return {"items": [{"experiment_id": str(e.id), "code": e.code, "name": e.name, "model_name": model.name, "algorithm": model.algorithm, "model_version": version.version, "dataset_name": dataset.name, "dataset_version": dataset_version.version_number, "evaluation_split": evaluation.evaluation_split, "sample_count": evaluation.sample_count, "precision": evaluation.precision, "recall": evaluation.recall, "f1_score": evaluation.f1_score, "accuracy": evaluation.accuracy} for e, _run, evaluation, model, version, dataset_version, dataset in rows]}
