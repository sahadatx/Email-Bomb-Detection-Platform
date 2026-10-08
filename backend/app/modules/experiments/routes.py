from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.users.models import User
from .dependencies import get_experiment_service
from .errors import ExperimentConflict, ExperimentError, ExperimentNotFound, ExperimentValidationError
from .runner import execute_experiment_run
from .schemas import (
    ExperimentCompare,
    ExperimentComparison,
    ExperimentCreate,
    ExperimentDetail,
    ExperimentItem,
    ExperimentList,
    ExperimentLogs,
    ExperimentOptions,
    ExperimentRunDetail,
    ExperimentSummary,
    ExperimentUpdate,
)

router = APIRouter()
Read = Depends(require_permission(Permission.EXPERIMENTS_READ))
Manage = Depends(require_permission(Permission.EXPERIMENTS_MANAGE))


def call(fn):
    try: return fn()
    except ExperimentNotFound as exc: raise HTTPException(404, str(exc)) from exc
    except ExperimentConflict as exc: raise HTTPException(409, str(exc)) from exc
    except (ExperimentValidationError, ValueError) as exc: raise HTTPException(422, str(exc)) from exc
    except ExperimentError as exc: raise HTTPException(400, str(exc)) from exc


@router.get("/options", response_model=ExperimentOptions, dependencies=[Read])
def options(service=Depends(get_experiment_service)):
    return service.options()


@router.get("/summary", response_model=ExperimentSummary, dependencies=[Read])
def summary(service=Depends(get_experiment_service)):
    return service.repo.summary()


@router.post("/compare", response_model=ExperimentComparison, dependencies=[Read])
def compare(payload: ExperimentCompare, service=Depends(get_experiment_service)):
    return call(lambda: service.compare(payload.experiment_ids))


@router.get("/runs/{run_id}/logs", response_model=ExperimentLogs, dependencies=[Read])
def run_logs(run_id: UUID, service=Depends(get_experiment_service)):
    run = service.repo.get_run(run_id)
    if run is None: raise HTTPException(404, "Experiment run was not found.")
    return {"items": run.logs or []}


@router.get("/runs/{run_id}", response_model=ExperimentRunDetail, dependencies=[Read])
def run_details(run_id: UUID, service=Depends(get_experiment_service)):
    return call(lambda: service.run_detail(run_id))


@router.get("", response_model=ExperimentList, dependencies=[Read])
def list_experiments(service=Depends(get_experiment_service), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), search: str | None = Query(None, max_length=180), status_filter: Literal["draft", "queued", "running", "completed", "failed", "cancelled"] | None = Query(None, alias="status"), model_definition_id: UUID | None = None, dataset_version_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None, sort: Literal["newest", "oldest", "name", "f1_score"] = "newest"):
    if from_date and to_date and from_date > to_date: raise HTTPException(422, "from_date must be before or equal to to_date.")
    return service.list(page=page, page_size=page_size, search=search, status=status_filter, model_definition_id=model_definition_id, dataset_version_id=dataset_version_id, from_date=from_date, to_date=to_date, sort=sort)


@router.post("", response_model=ExperimentItem, status_code=status.HTTP_201_CREATED, dependencies=[Manage])
def create_experiment(payload: ExperimentCreate, user: Annotated[User, Depends(require_permission(Permission.EXPERIMENTS_MANAGE))], service=Depends(get_experiment_service)):
    return call(lambda: service.create(payload, user))


@router.get("/{experiment_id}", response_model=ExperimentDetail, dependencies=[Read])
def experiment_detail(experiment_id: UUID, service=Depends(get_experiment_service)):
    return call(lambda: service.get(experiment_id))


@router.patch("/{experiment_id}", response_model=ExperimentItem, dependencies=[Manage])
def update_experiment(experiment_id: UUID, payload: ExperimentUpdate, user: Annotated[User, Depends(require_permission(Permission.EXPERIMENTS_MANAGE))], service=Depends(get_experiment_service)):
    return call(lambda: service.update(experiment_id, payload.model_dump(exclude_unset=True), user))


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Manage])
def delete_experiment(experiment_id: UUID, user: Annotated[User, Depends(require_permission(Permission.EXPERIMENTS_MANAGE))], service=Depends(get_experiment_service)):
    call(lambda: service.delete(experiment_id, user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{experiment_id}/runs", response_model=ExperimentRunDetail, status_code=status.HTTP_202_ACCEPTED, dependencies=[Manage])
def create_experiment_run(experiment_id: UUID, background_tasks: BackgroundTasks, user: Annotated[User, Depends(require_permission(Permission.EXPERIMENTS_MANAGE))], service=Depends(get_experiment_service)):
    run = call(lambda: service.create_run(experiment_id, user))
    service.db.commit()
    background_tasks.add_task(execute_experiment_run, run.id)
    return service.run_detail(run.id)


@router.get("/{experiment_id}/runs", response_model=list[ExperimentRunDetail], dependencies=[Read])
def list_experiment_runs(experiment_id: UUID, service=Depends(get_experiment_service)):
    experiment = service.repo.get(experiment_id)
    if experiment is None: raise HTTPException(404, "Experiment was not found.")
    return [service.run_detail(run.id) for run in service.repo.runs(experiment.id)]
