from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from .service import InvestigationService


def get_investigation_service(db: Session = Depends(get_db)) -> InvestigationService:
    return InvestigationService(db)
