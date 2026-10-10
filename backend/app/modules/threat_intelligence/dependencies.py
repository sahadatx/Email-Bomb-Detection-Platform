from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from .service import ThreatService


def get_threat_service(db: Annotated[Session, Depends(get_db)]) -> ThreatService:
    return ThreatService(db)
