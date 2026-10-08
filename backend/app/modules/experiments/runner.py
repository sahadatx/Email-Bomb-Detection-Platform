"""Orchestrate existing ML training/evaluation workers for experiment runs."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.ml_models.models import MLModelVersion, MLTrainingRun
from app.modules.ml_models.runtime import execute_evaluation_run_in_background, execute_training_run_in_background
from app.modules.ml_models.service import MLModelService
from .models import Experiment, ExperimentRun


def _log(run, message):
    logs = list(run.logs or [])
    logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": message})
    run.logs = logs


def execute_experiment_run(experiment_run_id: UUID):
    db = SessionLocal()
    try:
        run = db.get(ExperimentRun, experiment_run_id)
        if run is None or run.status not in {"queued", "running"}: return
        experiment = db.get(Experiment, run.experiment_id)
        if experiment is None: return
        run.status = "running"; run.progress_percent = 2; experiment.status = "running"
        _log(run, "Training started through ML Model Management.")
        db.commit()
        training_id = run.training_run_id
        experiment_id = experiment.id
        db.close()

        execute_training_run_in_background(training_id)

        db = SessionLocal()
        run = db.get(ExperimentRun, experiment_run_id)
        experiment = db.get(Experiment, experiment_id)
        training = db.get(MLTrainingRun, training_id)
        if run is None or experiment is None or training is None: return
        if training.status != "completed":
            run.status = "failed" if training.status == "failed" else training.status
            run.error_summary = training.error_message or f"Training finished with status '{training.status}'."
            run.progress_percent = training.progress_percent
            experiment.status = run.status
            run.completed_at = datetime.now(timezone.utc)
            _log(run, "Training did not complete; evaluation was skipped.")
            db.commit(); return

        version = db.scalar(select(MLModelVersion).where(MLModelVersion.training_run_id == training.id))
        if version is None:
            raise RuntimeError("Completed training did not register a model version.")
        evaluation = MLModelService(db).create_evaluation_run(model_version_id=version.id, preprocessing_run_id=experiment.preprocessing_run_id, evaluation_split=(experiment.evaluation_config or {}).get("split", "validation"))
        run.evaluation_run_id = evaluation.id
        run.progress_percent = 70
        _log(run, f"Training completed; evaluating on the {evaluation.evaluation_split} split.")
        db.commit()
        evaluation_id = evaluation.id
        db.close()

        execute_evaluation_run_in_background(evaluation_id)

        db = SessionLocal()
        run = db.get(ExperimentRun, experiment_run_id)
        experiment = db.get(Experiment, experiment_id)
        evaluation = db.get(type(evaluation), evaluation_id)
        if run is None or experiment is None or evaluation is None: return
        run.status = "completed" if evaluation.status == "completed" else "failed"
        run.progress_percent = 100 if run.status == "completed" else 99
        run.error_summary = evaluation.error_message
        run.completed_at = datetime.now(timezone.utc)
        experiment.status = run.status
        _log(run, f"Evaluation {run.status} on the {evaluation.evaluation_split} split.")
        db.commit()
    except Exception as exc:
        if db.is_active:
            db.rollback()
        db2 = SessionLocal()
        try:
            run = db2.get(ExperimentRun, experiment_run_id)
            if run:
                run.status = "failed"; run.error_summary = str(exc)[:2000]; run.completed_at = datetime.now(timezone.utc)
                _log(run, "Experiment run failed.")
                experiment = db2.get(Experiment, run.experiment_id)
                if experiment: experiment.status = "failed"
                db2.commit()
        finally:
            db2.close()
    finally:
        try: db.close()
        except Exception: pass
