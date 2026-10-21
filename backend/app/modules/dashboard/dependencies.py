"""Dashboard dependency providers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from .services.dashboard_service import DashboardService


def get_dashboard_service(
    db: Annotated[Session, Depends(get_db)],
) -> DashboardService:
    """Create a request-scoped dashboard service over the shared DB session."""
    return DashboardService(db)
