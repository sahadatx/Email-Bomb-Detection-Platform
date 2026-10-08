
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.ml_models.service import MLModelService


def get_ml_model_service(
    db: Annotated[Session, Depends(get_db)],
) -> MLModelService:
    """Provide an MLModelService instance for API routes."""
    return MLModelService(db)


MLModelServiceDependency = Annotated[
    MLModelService,
    Depends(get_ml_model_service),
]