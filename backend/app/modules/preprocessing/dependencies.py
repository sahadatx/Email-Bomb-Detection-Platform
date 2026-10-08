"""FastAPI dependencies for the preprocessing module."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.datasets.repository import DatasetRepository
from app.modules.preprocessing.repository import PreprocessingRepository
from app.modules.preprocessing.service import PreprocessingService


def get_preprocessing_repository(
    db: Session = Depends(get_db),
) -> PreprocessingRepository:
    """Provide a preprocessing repository."""
    return PreprocessingRepository(db)


def get_dataset_repository(
    db: Session = Depends(get_db),
) -> DatasetRepository:
    """Provide a dataset repository."""
    return DatasetRepository(db)


def get_preprocessing_service(
    preprocessing_repository: PreprocessingRepository = Depends(
        get_preprocessing_repository
    ),
    dataset_repository: DatasetRepository = Depends(
        get_dataset_repository
    ),
) -> PreprocessingService:
    """Provide the preprocessing service."""
    return PreprocessingService(
        preprocessing_repository=preprocessing_repository,
        dataset_repository=dataset_repository,
    )