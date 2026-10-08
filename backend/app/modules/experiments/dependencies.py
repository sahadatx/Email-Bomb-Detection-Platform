from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from .service import ExperimentService


def get_experiment_service(db: Annotated[Session, Depends(get_db)]) -> ExperimentService:
    return ExperimentService(db)
