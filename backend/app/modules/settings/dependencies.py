"""FastAPI dependency providers for settings operations."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from .repositories.settings_repository import SettingsRepository
from .services.settings_service import SettingsService


def get_settings_service(db: Annotated[Session, Depends(get_db)]) -> SettingsService:
    return SettingsService(db, SettingsRepository(db))
