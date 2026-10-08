from sqlalchemy import func, select

from app.modules.ml_models.models import MLEvaluationRun, MLModelDefinition, MLModelVersion, MLTrainingRun
from app.modules.datasets.models import Dataset, DatasetVersion
from app.modules.preprocessing.models import PreprocessingRun
from .models import Experiment, ExperimentRun


class ExperimentRepository:
    def __init__(self, db): self.db = db

    def get(self, experiment_id, include_deleted=False):
        statement = select(Experiment).where(Experiment.id == experiment_id)
        if not include_deleted: statement = statement.where(Experiment.deleted_at.is_(None))
        return self.db.scalar(statement)

    def get_run(self, run_id): return self.db.get(ExperimentRun, run_id)

    def create(self, experiment):
        self.db.add(experiment); self.db.flush(); return experiment

    def create_run(self, run):
        self.db.add(run); self.db.flush(); return run

    def latest_run(self, experiment_id):
        return self.db.scalar(select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id).order_by(ExperimentRun.created_at.desc()).limit(1))

    def list(self, *, page, page_size, search=None, status=None, model_definition_id=None, dataset_version_id=None, from_date=None, to_date=None, sort="newest"):
        statement = select(Experiment).where(Experiment.deleted_at.is_(None))
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(Experiment.name.ilike(pattern) | Experiment.code.ilike(pattern))
        if status: statement = statement.where(Experiment.status == status)
        if model_definition_id: statement = statement.where(Experiment.model_definition_id == model_definition_id)
        if dataset_version_id: statement = statement.where(Experiment.dataset_version_id == dataset_version_id)
        if from_date: statement = statement.where(Experiment.created_at >= from_date)
        if to_date: statement = statement.where(Experiment.created_at <= to_date)
        total = int(self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        if sort == "oldest": statement = statement.order_by(Experiment.created_at.asc())
        elif sort == "name": statement = statement.order_by(Experiment.name.asc())
        elif sort == "f1_score":
            latest_id = select(ExperimentRun.id).where(ExperimentRun.experiment_id == Experiment.id).order_by(ExperimentRun.created_at.desc()).limit(1).scalar_subquery()
            score = select(MLEvaluationRun.f1_score).where(MLEvaluationRun.id == select(ExperimentRun.evaluation_run_id).where(ExperimentRun.id == latest_id).scalar_subquery()).scalar_subquery()
            statement = statement.order_by(score.desc().nullslast(), Experiment.created_at.desc())
        else: statement = statement.order_by(Experiment.created_at.desc())
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return items, total

    def runs(self, experiment_id):
        return self.db.scalars(select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id).order_by(ExperimentRun.created_at.desc())).all()

    def active_run(self, experiment_id):
        return self.db.scalar(select(ExperimentRun).where(ExperimentRun.experiment_id == experiment_id, ExperimentRun.status.in_(("queued", "running"))).limit(1))

    def summary(self):
        rows = self.db.execute(select(Experiment.status, func.count(Experiment.id)).where(Experiment.deleted_at.is_(None)).group_by(Experiment.status)).all()
        counts = {key: 0 for key in ("draft", "queued", "running", "completed", "failed", "cancelled")}
        counts.update({key: int(value) for key, value in rows})
        counts["total"] = sum(counts.values())
        return counts

    def comparison(self, experiment_ids):
        latest_successful_run_id = (
            select(ExperimentRun.id)
            .join(MLEvaluationRun, MLEvaluationRun.id == ExperimentRun.evaluation_run_id)
            .where(
                ExperimentRun.experiment_id == Experiment.id,
                ExperimentRun.status == "completed",
                MLEvaluationRun.status == "completed",
            )
            .order_by(ExperimentRun.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        statement = select(Experiment, ExperimentRun, MLEvaluationRun, MLModelDefinition, MLModelVersion, DatasetVersion, Dataset).join(ExperimentRun, ExperimentRun.id == latest_successful_run_id).join(MLEvaluationRun, MLEvaluationRun.id == ExperimentRun.evaluation_run_id).join(MLModelDefinition, MLModelDefinition.id == Experiment.model_definition_id).join(MLModelVersion, MLModelVersion.id == MLEvaluationRun.model_version_id).join(DatasetVersion, DatasetVersion.id == Experiment.dataset_version_id).join(Dataset, Dataset.id == DatasetVersion.dataset_id).where(Experiment.id.in_(experiment_ids), Experiment.deleted_at.is_(None))
        return self.db.execute(statement).all()

    def list_items(self, experiments):
        return [self.item(experiment) for experiment in experiments]

    def item(self, experiment):
        model = self.db.get(MLModelDefinition, experiment.model_definition_id)
        version = self.db.get(DatasetVersion, experiment.dataset_version_id)
        dataset = self.db.get(Dataset, version.dataset_id) if version else None
        prep = self.db.get(PreprocessingRun, experiment.preprocessing_run_id)
        run = self.latest_run(experiment.id)
        evaluation = self.db.get(MLEvaluationRun, run.evaluation_run_id) if run and run.evaluation_run_id else None
        model_version = self.db.get(MLModelVersion, evaluation.model_version_id) if evaluation else None
        training = self.db.get(MLTrainingRun, run.training_run_id) if run else None
        return {"id": str(experiment.id), "code": experiment.code, "name": experiment.name, "description": experiment.description, "status": experiment.status, "model_definition_id": str(experiment.model_definition_id), "model_name": model.name if model else None, "algorithm": model.algorithm if model else None, "dataset_version_id": str(experiment.dataset_version_id), "dataset_id": str(version.dataset_id) if version else None, "dataset_name": dataset.name if dataset else None, "dataset_version_name": version.name if version else None, "dataset_version_number": version.version_number if version else None, "preprocessing_run_id": str(experiment.preprocessing_run_id), "feature_set": experiment.feature_set_snapshot.get("features", []), "feature_count": len(experiment.feature_set_snapshot.get("features", [])), "training_config": experiment.training_config, "evaluation_split": (experiment.evaluation_config or {}).get("split", "validation"), "latest_run": self.run_item(run, evaluation, model_version, training) if run else None, "accuracy": evaluation.accuracy if evaluation else None, "f1_score": evaluation.f1_score if evaluation else None, "created_at": experiment.created_at.isoformat() if experiment.created_at else None, "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None}

    @staticmethod
    def run_item(run, evaluation=None, model_version=None, training=None):
        progress = training.progress_percent if training and training.status == "running" and run.evaluation_run_id is None else run.progress_percent
        return {"id": str(run.id), "training_run_id": str(run.training_run_id), "evaluation_run_id": str(run.evaluation_run_id) if run.evaluation_run_id else None, "model_version_id": str(model_version.id) if model_version else None, "status": run.status, "progress_percent": progress, "error_summary": run.error_summary, "logs": run.logs or [], "metrics": {"accuracy": evaluation.accuracy, "precision": evaluation.precision, "recall": evaluation.recall, "f1_score": evaluation.f1_score} if evaluation else None, "evaluation_split": evaluation.evaluation_split if evaluation else None, "created_at": run.created_at.isoformat() if run.created_at else None, "completed_at": run.completed_at.isoformat() if run.completed_at else None}
