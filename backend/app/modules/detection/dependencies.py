from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.detection.service import DetectionService


def get_detection_service(db: Session = Depends(get_db)) -> DetectionService:
    return DetectionService(db)


DetectionServiceDependency = Annotated[DetectionService, Depends(get_detection_service)]
