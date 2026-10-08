
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.core.rbac import require_module_access
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select

from app.modules.ml_models.dependencies import MLModelServiceDependency
from app.modules.ml_models.models import MLModelVersion, MLTrainingRun
from app.modules.ml_models.schemas import (
    MLEvaluationRunCreate,
    MLEvaluationRunList,
    MLEvaluationRunRead,
    MLModelCreate,
    MLModelRead,
    MLModelStatusUpdate,
    MLModelUpdate,
    MLModelVersionList,
    MLModelVersionRead,
    MLTrainingRunCreate,
    MLTrainingRunList,
    MLTrainingRunRead,
)
from app.modules.ml_models.storage.artifact_store import ModelArtifactStore
from app.modules.ml_models.runtime import (
    execute_evaluation_run_in_background,
    execute_training_run_in_background,
)
from app.modules.ml_models.service import (
    EvaluationRunNotFoundError,
    InvalidModelStateError,
    MLModelNotFoundError,
    ModelVersionNotFoundError,
    TrainingRunNotFoundError,
)

router = APIRouter(
    tags=["ML Model Management"],
    dependencies=[Depends(require_module_access("models"))],
)


def _raise_http_error(exc: Exception) -> None:
    """Translate service exceptions into HTTP responses."""

    if isinstance(
        exc,
        (
            MLModelNotFoundError,
            TrainingRunNotFoundError,
            ModelVersionNotFoundError,
            EvaluationRunNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, FileNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InvalidModelStateError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected ML model management error occurred.",
    ) from exc


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------


@router.post(
    "/models",
    response_model=MLModelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_model(
    payload: MLModelCreate,
    service: MLModelServiceDependency,
) -> Any:
    """Create an ML model definition."""

    try:
        return service.create_model(
            name=payload.name,
            description=payload.description,
            algorithm=payload.algorithm,
            hyperparameters=payload.hyperparameters,
            status=payload.status,
        )
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/models",
    response_model=list[MLModelRead],
)
def list_models(
    service: MLModelServiceDependency,
    model_status: str | None = Query(default=None, alias="status"),
    algorithm: str | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=200),
) -> Any:
    """List model definitions."""

    return service.list_models(
        status=model_status,
        algorithm=algorithm,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/models/count",
)
def count_models(
    service: MLModelServiceDependency,
    model_status: str | None = Query(default=None, alias="status"),
    algorithm: str | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=150),
) -> dict[str, int]:
    """Return the number of model definitions."""

    return {
        "total": service.count_models(
            status=model_status, algorithm=algorithm, search=search
        )
    }


@router.get("/algorithms")
def list_supported_algorithms() -> dict[str, Any]:
    """Return the trainer's supported classifiers and default parameters."""
    from app.modules.ml_models.config.validator import ALGORITHM_DEFAULTS

    return {
        "items": [
            {
                "algorithm": algorithm,
                "model_type": "classifier",
                "default_hyperparameters": defaults,
            }
            for algorithm, defaults in sorted(ALGORITHM_DEFAULTS.items())
        ]
    }


@router.get("/models/summary")
def get_models_summary(
    service: MLModelServiceDependency,
) -> dict[str, Any]:
    """Return model totals and per-model run/version summaries from the database."""
    run_counts = dict(service.db.execute(
        select(MLTrainingRun.model_definition_id, func.count(MLTrainingRun.id))
        .group_by(MLTrainingRun.model_definition_id)
    ).all())
    version_counts = dict(service.db.execute(
        select(MLModelVersion.model_definition_id, func.count(MLModelVersion.id))
        .group_by(MLModelVersion.model_definition_id)
    ).all())

    ranked_runs = select(
        MLTrainingRun.id.label("id"),
        MLTrainingRun.model_definition_id.label("model_id"),
        MLTrainingRun.status.label("status"),
        func.row_number().over(
            partition_by=MLTrainingRun.model_definition_id,
            order_by=(MLTrainingRun.created_at.desc(), MLTrainingRun.id.desc()),
        ).label("row_number"),
    ).subquery()
    latest_runs = {
        model_id: {"id": run_id, "status": run_status}
        for run_id, model_id, run_status in service.db.execute(
            select(ranked_runs.c.id, ranked_runs.c.model_id, ranked_runs.c.status)
            .where(ranked_runs.c.row_number == 1)
        ).all()
    }
    latest_versions = dict(service.db.execute(
        select(MLModelVersion.model_definition_id, func.max(MLModelVersion.version))
        .group_by(MLModelVersion.model_definition_id)
    ).all())
    models = service.list_models(offset=0, limit=200)
    return {
        "total_models": service.count_models(),
        "active_models": service.count_models(status="active"),
        "inactive_models": service.count_models(status="inactive"),
        "trained_versions": service.count_model_versions(),
        "items": [
            {
                "model_definition_id": model.id,
                "training_run_count": run_counts.get(model.id, 0),
                "latest_training_run": latest_runs.get(model.id),
                "version_count": version_counts.get(model.id, 0),
                "latest_version": latest_versions.get(model.id),
            }
            for model in models
        ],
    }


@router.get(
    "/models/{model_id}/training-runs",
    response_model=MLTrainingRunList,
)
def list_model_training_runs(
    model_id: UUID,
    service: MLModelServiceDependency,
    run_status: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=200),
) -> Any:
    """List training history for one model definition."""
    try:
        service.get_model(model_id)
        items = service.list_training_runs(
            model_definition_id=model_id,
            status=run_status,
            offset=offset,
            limit=limit,
        )
        total = service.count_training_runs(
            model_definition_id=model_id, status=run_status
        )
        return {"items": items, "total": total}
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/models/{model_id}",
    response_model=MLModelRead,
)
def get_model(
    model_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Retrieve a model definition."""

    try:
        return service.get_model(model_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.patch(
    "/models/{model_id}",
    response_model=MLModelRead,
)
def update_model(
    model_id: UUID,
    payload: MLModelUpdate,
    service: MLModelServiceDependency,
) -> Any:
    """Update a model definition."""

    try:
        changes = payload.model_dump(exclude_unset=True)
        return service.update_model(
            model_id=model_id,
            **changes,
        )
    except Exception as exc:
        _raise_http_error(exc)


@router.patch(
    "/models/{model_id}/status",
    response_model=MLModelRead,
)
def update_model_status(
    model_id: UUID,
    payload: MLModelStatusUpdate,
    service: MLModelServiceDependency,
) -> Any:
    """Activate or deactivate a model definition."""

    try:
        return service.set_model_status(
            model_id=model_id,
            status=payload.status,
        )
    except Exception as exc:
        _raise_http_error(exc)


@router.delete(
    "/models/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_model(
    model_id: UUID,
    service: MLModelServiceDependency,
) -> None:
    """Delete a model only when it has no runs or registered versions."""
    try:
        service.delete_model(model_id)
    except Exception as exc:
        _raise_http_error(exc)


# ---------------------------------------------------------------------------
# Training runs
# ---------------------------------------------------------------------------


@router.post(
    "/training-runs",
    response_model=MLTrainingRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_training_run(
    payload: MLTrainingRunCreate,
    background_tasks: BackgroundTasks,
    service: MLModelServiceDependency,
) -> Any:
    """Create a pending training run."""

    try:
        run = service.create_training_run(
            model_definition_id=payload.model_definition_id,
            preprocessing_run_id=payload.preprocessing_run_id,
            config_snapshot=payload.config_snapshot,
        )
        # Mark it queued in the committed transaction before the independent
        # background session attempts to claim it.
        run = service.update_training_run(run.id, status="queued")
        # Background tasks use a fresh DB session. Commit before scheduling so
        # that session can see the newly-created run (FastAPI may execute
        # BackgroundTasks before yielding dependencies are torn down).
        service.db.commit()
        background_tasks.add_task(
            execute_training_run_in_background, run.id
        )
        return run
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/training-runs",
    response_model=MLTrainingRunList,
)
def list_training_runs(
    service: MLModelServiceDependency,
    model_definition_id: UUID | None = None,
    dataset_version_id: UUID | None = None,
    preprocessing_run_id: UUID | None = None,
    run_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=200),
) -> Any:
    """List training runs."""

    items = service.list_training_runs(
        model_definition_id=model_definition_id,
        dataset_version_id=dataset_version_id,
        preprocessing_run_id=preprocessing_run_id,
        status=run_status,
        search=search,
        offset=offset,
        limit=limit,
    )
    total = service.count_training_runs(
        model_definition_id=model_definition_id,
        dataset_version_id=dataset_version_id,
        preprocessing_run_id=preprocessing_run_id,
        status=run_status,
        search=search,
    )

    return {"items": items, "total": total}


@router.get(
    "/training-runs/{training_run_id}",
    response_model=MLTrainingRunRead,
)
def get_training_run(
    training_run_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Retrieve a training run."""

    try:
        return service.get_training_run(training_run_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/training-runs/{training_run_id}/model-version",
    response_model=MLModelVersionRead,
)
def get_training_run_model_version(
    training_run_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Retrieve the model version registered from a training run."""
    try:
        return service.get_model_version_by_training_run(training_run_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/training-runs/{training_run_id}/retry",
    response_model=MLTrainingRunRead,
    status_code=status.HTTP_201_CREATED,
)
def retry_training_run(
    training_run_id: UUID,
    background_tasks: BackgroundTasks,
    service: MLModelServiceDependency,
) -> Any:
    """Create a new run from a failed run and schedule it."""
    try:
        run = service.retry_training_run(training_run_id)
        run = service.update_training_run(run.id, status="queued")
        service.db.commit()
        background_tasks.add_task(
            execute_training_run_in_background, run.id
        )
        return run
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/training-runs/{training_run_id}/resume",
    response_model=MLTrainingRunRead,
)
def resume_training_run(
    training_run_id: UUID,
    background_tasks: BackgroundTasks,
    service: MLModelServiceDependency,
) -> Any:
    """Schedule an existing pending run that was left undispatched."""
    try:
        run = service.get_training_run(training_run_id)
        if run.status != "pending":
            raise InvalidModelStateError("Only pending runs can be resumed.")
        run = service.update_training_run(run.id, status="queued")
        service.db.commit()
        background_tasks.add_task(execute_training_run_in_background, run.id)
        return run
    except Exception as exc:
        _raise_http_error(exc)


@router.get("/training-runs/{training_run_id}/logs")
def get_training_run_logs(
    training_run_id: UUID,
    service: MLModelServiceDependency,
) -> dict[str, Any]:
    """Return persisted lifecycle log entries for a training run."""
    try:
        run = service.get_training_run(training_run_id)
        return {
            "training_run_id": run.id,
            "items": (run.result_summary or {}).get("logs", []),
        }
    except Exception as exc:
        _raise_http_error(exc)


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------


@router.get(
    "/versions",
    response_model=MLModelVersionList,
)
def list_model_versions(
    service: MLModelServiceDependency,
    model_definition_id: UUID | None = None,
    version_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=200),
) -> Any:
    """List registered model versions."""

    items = service.list_model_versions(
        model_definition_id=model_definition_id,
        status=version_status,
        search=search,
        offset=offset,
        limit=limit,
    )
    total = service.count_model_versions(
        model_definition_id=model_definition_id,
        status=version_status,
        search=search,
    )

    return {"items": items, "total": total}


@router.get(
    "/versions/{version_id}",
    response_model=MLModelVersionRead,
)
def get_model_version(
    version_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Retrieve a registered model version."""

    try:
        return service.get_model_version(version_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/versions/{version_id}/activate",
    response_model=MLModelVersionRead,
)
def activate_model_version(
    version_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Activate a registered model version."""

    try:
        version = service.get_model_version(version_id)
        storage_root = Path(
            os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models")
        ).expanduser().resolve()
        ModelArtifactStore(storage_root).load(
            version.storage_path,
            expected_checksum=version.checksum_sha256,
        )
        return service.activate_model_version(version_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/versions/{version_id}/archive",
    response_model=MLModelVersionRead,
)
def archive_model_version(
    version_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Archive a registered model version."""

    try:
        return service.archive_model_version(version_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/versions/{version_id}/restore",
    response_model=MLModelVersionRead,
)
def restore_model_version(
    version_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Restore an archived version to registered, inactive state."""
    try:
        return service.restore_model_version(version_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.get("/versions/{version_id}/artifact")
def download_model_artifact(
    version_id: UUID,
    service: MLModelServiceDependency,
) -> FileResponse:
    """Download a registered artifact after path and checksum verification."""
    try:
        version = service.get_model_version(version_id)
        storage_root = Path(
            os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models")
        ).expanduser().resolve()
        artifact_path = Path(version.storage_path or "").expanduser().resolve()
        if not artifact_path.is_relative_to(storage_root):
            raise ValueError("Artifact path is outside the configured store.")
        if not artifact_path.is_file():
            raise FileNotFoundError("Model artifact was not found.")
        if version.checksum_sha256:
            import hashlib

            checksum = hashlib.sha256()
            with artifact_path.open("rb") as artifact_file:
                for chunk in iter(
                    lambda: artifact_file.read(1024 * 1024), b""
                ):
                    checksum.update(chunk)
            digest = checksum.hexdigest()
            if digest.lower() != version.checksum_sha256.lower():
                raise ValueError("Model artifact checksum verification failed.")
        return FileResponse(
            artifact_path,
            media_type=version.media_type or "application/octet-stream",
            filename=version.artifact_filename or artifact_path.name,
        )
    except Exception as exc:
        _raise_http_error(exc)


# ---------------------------------------------------------------------------
# Evaluation runs
# ---------------------------------------------------------------------------


@router.post(
    "/evaluation-runs",
    response_model=MLEvaluationRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation_run(
    payload: MLEvaluationRunCreate,
    background_tasks: BackgroundTasks,
    service: MLModelServiceDependency,
) -> Any:
    """Create a pending evaluation run."""

    try:
        run = service.create_evaluation_run(
            model_version_id=payload.model_version_id,
            preprocessing_run_id=payload.preprocessing_run_id,
            evaluation_split=payload.evaluation_split,
        )
        service.db.commit()
        background_tasks.add_task(
            execute_evaluation_run_in_background, run.id
        )
        return run
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/evaluation-runs",
    response_model=MLEvaluationRunList,
)
def list_evaluation_runs(
    service: MLModelServiceDependency,
    model_version_id: UUID | None = None,
    model_definition_id: UUID | None = None,
    preprocessing_run_id: UUID | None = None,
    run_status: str | None = Query(default=None, alias="status"),
    evaluation_split: str | None = Query(
        default=None, pattern="^(validation|testing)$"
    ),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=200),
) -> Any:
    """List evaluation runs."""

    items = service.list_evaluation_runs(
        model_version_id=model_version_id,
        model_definition_id=model_definition_id,
        preprocessing_run_id=preprocessing_run_id,
        status=run_status,
        evaluation_split=evaluation_split,
        search=search,
        offset=offset,
        limit=limit,
    )
    total = service.count_evaluation_runs(
        model_version_id=model_version_id,
        model_definition_id=model_definition_id,
        preprocessing_run_id=preprocessing_run_id,
        status=run_status,
        evaluation_split=evaluation_split,
        search=search,
    )

    return {"items": items, "total": total}


@router.get(
    "/evaluation-runs/{evaluation_run_id}",
    response_model=MLEvaluationRunRead,
)
def get_evaluation_run(
    evaluation_run_id: UUID,
    service: MLModelServiceDependency,
) -> Any:
    """Retrieve an evaluation run."""

    try:
        return service.get_evaluation_run(evaluation_run_id)
    except Exception as exc:
        _raise_http_error(exc)

@router.get("/evaluation-runs/{evaluation_run_id}/export")
def export_evaluation_report(
    evaluation_run_id: UUID,
    service: MLModelServiceDependency,
    report_format: str = Query(default="json", alias="format"),
) -> JSONResponse:
    """Export a completed evaluation report as JSON."""
    if report_format != "json":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only JSON report export is currently supported.",
        )
    try:
        run = service.get_evaluation_run(evaluation_run_id)
        if run.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only completed evaluations can be exported.",
            )
        from app.modules.ml_models.schemas import MLEvaluationRunRead

        payload = MLEvaluationRunRead.model_validate(run).model_dump(mode="json")
        return JSONResponse(
            content=payload,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="evaluation-{run.id}.json"'
                )
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_error(exc)
