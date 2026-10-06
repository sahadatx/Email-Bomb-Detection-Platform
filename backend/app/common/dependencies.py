from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


def database_session(
    db: Session = Depends(get_db),
) -> Session:
    """
    Standard database dependency.

    Authentication dependencies will be added at the
    authentication layer rather than coupling them to
    the database foundation.
    """

    return db