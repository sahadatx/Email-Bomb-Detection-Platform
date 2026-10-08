from sqlalchemy import select

from app.modules.datasets.models import Dataset, DatasetVersion
from app.modules.preprocessing.models import PreprocessingArtifact, PreprocessingRun
from app.modules.preprocessing.config.validator import FEATURE_TYPES


class DatasetAdapter:
    def __init__(self, db): self.db = db

    def validate_source(self, dataset_version_id, preprocessing_run_id):
        version = self.db.get(DatasetVersion, dataset_version_id)
        run = self.db.get(PreprocessingRun, preprocessing_run_id)
        if version is None: raise ValueError("Dataset version was not found.")
        if version.status not in {"ready", "validated"}: raise ValueError("Only ready or validated dataset versions can be used.")
        if run is None or run.status != "completed": raise ValueError("A completed preprocessing run is required.")
        if run.dataset_version_id != version.id: raise ValueError("The preprocessing run must use the selected dataset version.")
        dataset = self.db.get(Dataset, version.dataset_id)
        artifacts = self.db.scalars(select(PreprocessingArtifact).where(PreprocessingArtifact.preprocessing_run_id == run.id)).all()
        names = []
        for artifact in artifacts:
            if artifact.artifact_type != "train_processed": continue
            names = (artifact.metadata_json or {}).get("feature_order", [])
        return version, run, dataset, [name for name in names if name not in {"email_id", "ground_truth"} and FEATURE_TYPES.get(name) in {"boolean", "integer", "float"}]

    def completed_sources(self):
        rows = self.db.execute(select(PreprocessingRun, DatasetVersion, Dataset).join(DatasetVersion, DatasetVersion.id == PreprocessingRun.dataset_version_id).join(Dataset, Dataset.id == DatasetVersion.dataset_id).where(PreprocessingRun.status == "completed", DatasetVersion.status.in_(("ready", "validated"))).order_by(PreprocessingRun.created_at.desc()).limit(500)).all()
        by_run = {}
        artifacts = self.db.scalars(select(PreprocessingArtifact).where(PreprocessingArtifact.artifact_type == "train_processed", PreprocessingArtifact.preprocessing_run_id.in_([row[0].id for row in rows]))).all() if rows else []
        for artifact in artifacts:
            names = (artifact.metadata_json or {}).get("feature_order", [])
            by_run[artifact.preprocessing_run_id] = [name for name in names if name not in {"email_id", "ground_truth"} and FEATURE_TYPES.get(name) in {"boolean", "integer", "float"}]
        return [{"preprocessing_run_id": str(run.id), "dataset_version_id": str(version.id), "dataset_id": str(dataset.id), "dataset_name": dataset.name, "dataset_version_name": version.name, "dataset_version_number": version.version_number, "sample_count": run.output_sample_count, "feature_count": run.feature_count, "features": by_run.get(run.id, []), "training_count": run.training_count, "validation_count": run.validation_count, "testing_count": run.testing_count} for run, version, dataset in rows]
