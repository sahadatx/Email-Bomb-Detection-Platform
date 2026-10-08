from __future__ import annotations

import logging
from uuid import UUID

from app.core.database import SessionLocal
from app.modules.datasets.repository import DatasetRepository
from app.modules.preprocessing.repository import PreprocessingRepository
from app.modules.preprocessing.service import PreprocessingService

logger = logging.getLogger(__name__)


def execute_run_in_background(run_id: UUID) -> None:
    """Run preprocessing with its own DB session (not the request's)."""
    db = SessionLocal()
    try:
        service = PreprocessingService(
            preprocessing_repository=PreprocessingRepository(db),
            dataset_repository=DatasetRepository(db),
        )
        service.execute_run(run_id)
    except Exception:
        logger.exception("Preprocessing run %s crashed", run_id)
        db.rollback()
    finally:
        db.close()