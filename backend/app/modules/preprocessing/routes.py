"""API routes for the preprocessing pipeline."""

from __future__ import annotations

from math import ceil
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
from sqlalchemy import func, select

from app.modules.datasets.models import DatasetVersion
from app.modules.datasets.repository import DatasetRepository
from app.modules.preprocessing.config.validator import (
    PreprocessingConfigValidator,
)
from app.modules.preprocessing.dependencies import (
    get_dataset_repository,
    get_preprocessing_repository,
    get_preprocessing_service,
)
from app.modules.preprocessing.executor import (
    execute_run_in_background,
)
from app.modules.preprocessing.models import PreprocessingRun
from app.modules.preprocessing.repository import PreprocessingRepository
from app.modules.preprocessing.schemas import (
    DatasetSplitInfoResponse,
    DatasetVersionSelectionResponse,
    PreprocessingArtifactResponse,
    PreprocessingConfigRequest,
    PreprocessingErrorResponse,
    PreprocessingRunCreateRequest,
    PreprocessingRunListResponse,
    PreprocessingRunResponse,
)
from app.modules.preprocessing.service import (
    DatasetSplitError,
    DatasetVersionNotFoundError,
    DatasetVersionNotValidatedError,
    PreprocessingConfigurationError,
    PreprocessingRunNotFoundError,
    PreprocessingService,
    PreprocessingServiceError,
)

router = APIRouter(
    tags=["Preprocessing Pipeline"],
    dependencies=[Depends(require_module_access("preprocessing"))],
)


# ============================================================
# RESPONSE SERIALIZATION
# ============================================================


def _artifact_response(
    artifact: Any,
) -> PreprocessingArtifactResponse:
    """Convert an artifact database model to an API response."""
    return PreprocessingArtifactResponse(
        id=artifact.id,
        preprocessing_run_id=artifact.preprocessing_run_id,
        artifact_type=artifact.artifact_type,
        filename=artifact.filename,
        media_type=artifact.media_type,
        size_bytes=artifact.size_bytes,
        checksum_sha256=artifact.checksum_sha256,
        metadata_json=artifact.metadata_json or {},
        created_at=artifact.created_at,
    )


def _version_info(
    dataset_repository: DatasetRepository,
    version_id: UUID,
    cache: dict[UUID, dict[str, Any]],
) -> dict[str, Any]:
    """Look up display details for a dataset version (cached)."""
    if version_id in cache:
        return cache[version_id]

    info: dict[str, Any] = {
        "dataset_id": None,
        "dataset_name": None,
        "dataset_version_number": None,
        "dataset_version_name": None,
    }

    try:
        version = dataset_repository.get_dataset_version(version_id)
    except Exception:
        version = None

    if version is not None:
        dataset_id = getattr(version, "dataset_id", None)
        dataset_name = None

        if dataset_id is not None:
            try:
                from app.modules.datasets.models import Dataset

                dataset = dataset_repository.db.get(
                    Dataset, dataset_id
                )
                dataset_name = getattr(dataset, "name", None)
            except Exception:
                dataset_name = None

        info = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "dataset_version_number": getattr(
                version, "version_number", None
            ),
            "dataset_version_name": getattr(version, "name", None),
        }

    cache[version_id] = info
    return info


def _run_response(
    run: Any,
    repository: PreprocessingRepository,
    dataset_repository: DatasetRepository,
    cache: dict[UUID, dict[str, Any]] | None = None,
) -> PreprocessingRunResponse:
    """Convert a run model and its artifacts to an API response."""
    artifacts = repository.list_artifacts(run.id)
    version_info = _version_info(
        dataset_repository,
        run.dataset_version_id,
        cache if cache is not None else {},
    )

    return PreprocessingRunResponse(
        id=run.id,
        dataset_version_id=run.dataset_version_id,
        dataset_id=version_info["dataset_id"],
        dataset_name=version_info["dataset_name"],
        dataset_version_number=version_info["dataset_version_number"],
        dataset_version_name=version_info["dataset_version_name"],
        status=run.status,
        config_snapshot=run.config_snapshot or {},
        input_sample_count=run.input_sample_count,
        output_sample_count=run.output_sample_count,
        training_count=run.training_count,
        validation_count=run.validation_count,
        testing_count=run.testing_count,
        feature_count=run.feature_count,
        duration_ms=run.duration_ms,
        error_code=run.error_code,
        error_message=run.error_message,
        result_summary=run.result_summary or {},
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        artifacts=[
            _artifact_response(artifact)
            for artifact in artifacts
        ],
    )


# ============================================================
# RUN QUERY HELPERS
# ============================================================


def _list_runs(
    service: PreprocessingService,
    repository: PreprocessingRepository,
    *,
    page: int,
    page_size: int,
    dataset_id: UUID | None,
    dataset_version_id: UUID | None,
    run_status: str | None,
) -> tuple[list[Any], int]:
    """List runs, optionally filtered by dataset (all its versions)."""
    if dataset_id is None or dataset_version_id is not None:
        return service.list_runs(
            page=page,
            page_size=page_size,
            dataset_version_id=dataset_version_id,
            status=run_status,
        )

    db = repository.db

    version_ids = select(DatasetVersion.id).where(
        DatasetVersion.dataset_id == dataset_id
    )
    conditions = [
        PreprocessingRun.dataset_version_id.in_(version_ids)
    ]

    if run_status:
        conditions.append(PreprocessingRun.status == run_status)

    total = (
        db.scalar(
            select(func.count(PreprocessingRun.id)).where(*conditions)
        )
        or 0
    )

    runs = list(
        db.scalars(
            select(PreprocessingRun)
            .where(*conditions)
            .order_by(
                PreprocessingRun.created_at.desc(),
                PreprocessingRun.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )

    return runs, total


def _version_sort_key(version: dict[str, Any]) -> tuple[int, int]:
    number = version.get("number")

    try:
        return (0, int(number))
    except (TypeError, ValueError):
        return (1, 0)


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================


@router.post(
    "/config/validate",
    summary="Validate preprocessing configuration",
)
def validate_configuration(
    payload: PreprocessingConfigRequest,
) -> dict[str, Any]:
    """Validate the requested preprocessing configuration."""
    try:
        validated = PreprocessingConfigValidator().validate(
            payload.model_dump()
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PREPROCESSING_CONFIG",
                "message": str(exc),
            },
        ) from exc

    return {
        "valid": True,
        "config": validated,
    }


# ============================================================
# DATASET VERSION SELECTION
# ============================================================


@router.get(
    "/datasets/{dataset_version_id}",
    response_model=DatasetVersionSelectionResponse,
    summary="Get a dataset version for preprocessing",
    responses={
        404: {"model": PreprocessingErrorResponse},
        409: {"model": PreprocessingErrorResponse},
    },
)
def get_dataset_version(
    dataset_version_id: UUID,
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
) -> DatasetVersionSelectionResponse:
    """Return validated dataset details and immutable split settings."""
    try:
        selection = service.get_dataset_selection(
            dataset_version_id
        )
    except DatasetVersionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DATASET_VERSION_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc
    except DatasetVersionNotValidatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DATASET_VERSION_NOT_VALIDATED",
                "message": str(exc),
            },
        ) from exc
    except DatasetSplitError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DATASET_SPLIT_INVALID",
                "message": str(exc),
            },
        ) from exc

    version = selection.version

    return DatasetVersionSelectionResponse(
        dataset_version_id=version.id,
        dataset_id=version.dataset_id,
        version_number=version.version_number,
        name=version.name,
        status=version.status,
        validation_passed=version.validation_passed,
        sample_count=version.sample_count,
        feature_schema=version.feature_schema or {},
        split=DatasetSplitInfoResponse(
            training_percentage=version.training_percentage,
            validation_percentage=version.validation_percentage,
            testing_percentage=version.testing_percentage,
            training_count=version.training_count,
            validation_count=version.validation_count,
            testing_count=version.testing_count,
            random_seed=version.random_seed,
            stratified=version.stratified,
        ),
    )


# ============================================================
# RUN CREATION
# ============================================================


@router.post(
    "/runs",
    response_model=PreprocessingRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a preprocessing run",
    responses={
        404: {"model": PreprocessingErrorResponse},
        409: {"model": PreprocessingErrorResponse},
        422: {"model": PreprocessingErrorResponse},
    },
)
def create_preprocessing_run(
    payload: PreprocessingRunCreateRequest,
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> PreprocessingRunResponse:
    """Create a pending run using a validated dataset version."""
    try:
        config = PreprocessingConfigValidator().validate(
            payload.config.model_dump()
        )

        run = service.create_run(
            version_id=payload.dataset_version_id,
            config=config,
        )

    except DatasetVersionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DATASET_VERSION_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc

    except DatasetVersionNotValidatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DATASET_VERSION_NOT_VALIDATED",
                "message": str(exc),
            },
        ) from exc

    except DatasetSplitError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DATASET_SPLIT_INVALID",
                "message": str(exc),
            },
        ) from exc

    except (
        PreprocessingConfigurationError,
        ValueError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PREPROCESSING_CONFIG",
                "message": str(exc),
            },
        ) from exc

    except PreprocessingServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PREPROCESSING_RUN_CONFLICT",
                "message": str(exc),
            },
        ) from exc

    return _run_response(run, repository, dataset_repository)


# ============================================================
# RUN EXECUTION
# ============================================================


@router.post(
    "/runs/{run_id}/execute",
    response_model=PreprocessingRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a pending preprocessing run",
    responses={
        404: {"model": PreprocessingErrorResponse},
        409: {"model": PreprocessingErrorResponse},
    },
)
def execute_preprocessing_run(
    run_id: UUID,
    background_tasks: BackgroundTasks,
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> PreprocessingRunResponse:
    """
    Queue a pending run for execution.

    The run is processed in the background with its own database
    session. Poll GET /runs/{run_id} to follow its progress.
    """
    try:
        run = service.get_run(run_id)
    except PreprocessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PREPROCESSING_RUN_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc

    if run.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PREPROCESSING_RUN_NOT_PENDING",
                "message": (
                    f"Only pending runs can be started; this run "
                    f"is '{run.status}'."
                ),
            },
        )

    background_tasks.add_task(execute_run_in_background, run_id)

    return _run_response(run, repository, dataset_repository)


# ============================================================
# RUN SUMMARY AND FILTER OPTIONS
# ============================================================


@router.get(
    "/summary",
    summary="Preprocessing run counts by status",
)
def get_preprocessing_summary(
    dataset_id: UUID | None = Query(default=None),
    dataset_version_id: UUID | None = Query(default=None),
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
) -> dict[str, int]:
    """Return run totals per status in a single request."""

    def count(run_status: str | None) -> int:
        _, total = _list_runs(
            service,
            repository,
            page=1,
            page_size=1,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            run_status=run_status,
        )
        return total

    return {
        "total": count(None),
        "pending": count("pending"),
        "running": count("running"),
        "completed": count("completed"),
        "failed": count("failed"),
    }


@router.get(
    "/filters",
    summary="Datasets and versions used by preprocessing runs",
)
def get_preprocessing_filters(
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> dict[str, Any]:
    """Return only datasets/versions that have at least one run."""
    version_ids = repository.db.scalars(
        select(PreprocessingRun.dataset_version_id).distinct()
    ).all()

    cache: dict[UUID, dict[str, Any]] = {}
    datasets: dict[str, dict[str, Any]] = {}

    for version_id in version_ids:
        info = _version_info(dataset_repository, version_id, cache)
        key = str(info["dataset_id"] or "unknown")

        entry = datasets.setdefault(
            key,
            {
                "id": info["dataset_id"],
                "name": info["dataset_name"] or "Unknown dataset",
                "versions": [],
            },
        )

        entry["versions"].append(
            {
                "id": version_id,
                "number": info["dataset_version_number"],
                "name": info["dataset_version_name"],
            }
        )

    result = sorted(
        datasets.values(),
        key=lambda item: str(item["name"]).lower(),
    )

    for item in result:
        item["versions"].sort(key=_version_sort_key)

    return {"datasets": result}


# ============================================================
# RUN HISTORY
# ============================================================


@router.get(
    "/runs",
    response_model=PreprocessingRunListResponse,
    summary="List preprocessing runs",
)
def list_preprocessing_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    dataset_id: UUID | None = Query(default=None),
    dataset_version_id: UUID | None = Query(default=None),
    run_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(pending|running|completed|failed)$",
    ),
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> PreprocessingRunListResponse:
    """Return paginated preprocessing history."""
    runs, total = _list_runs(
        service,
        repository,
        page=page,
        page_size=page_size,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        run_status=run_status,
    )

    cache: dict[UUID, dict[str, Any]] = {}

    return PreprocessingRunListResponse(
        items=[
            _run_response(run, repository, dataset_repository, cache)
            for run in runs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


# ============================================================
# RUN DETAILS
# ============================================================


@router.get(
    "/runs/{run_id}",
    response_model=PreprocessingRunResponse,
    summary="Get preprocessing run details",
    responses={
        404: {"model": PreprocessingErrorResponse},
    },
)
def get_preprocessing_run(
    run_id: UUID,
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> PreprocessingRunResponse:
    """Return a run and its artifact metadata."""
    try:
        run = service.get_run(run_id)
    except PreprocessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PREPROCESSING_RUN_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc

    return _run_response(run, repository, dataset_repository)


# ============================================================
# ARTIFACTS
# ============================================================


@router.get(
    "/runs/{run_id}/artifacts",
    response_model=list[PreprocessingArtifactResponse],
    summary="List preprocessing artifacts",
    responses={
        404: {"model": PreprocessingErrorResponse},
    },
)
def list_preprocessing_artifacts(
    run_id: UUID,
    service: PreprocessingService = Depends(
        get_preprocessing_service
    ),
    repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
) -> list[PreprocessingArtifactResponse]:
    """Return artifact metadata for a preprocessing run."""
    try:
        service.get_run(run_id)
    except PreprocessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PREPROCESSING_RUN_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc

    artifacts = repository.list_artifacts(run_id)

    return [
        _artifact_response(artifact)
        for artifact in artifacts
    ]