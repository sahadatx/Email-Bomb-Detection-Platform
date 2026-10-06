from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """
    Root SQLAlchemy declarative base.

    All application models inherit from this base.
    """


# ============================================================
# DATABASE ENGINE
# ============================================================

database_url = settings.database_url
parsed_database_url = make_url(database_url)

# SQLite URLs such as ``sqlite:///./email_bomb_detection.db`` are normally
# resolved against the process working directory. The API can be launched
# from either the repository root or ``backend/``, which would silently open
# two different databases. Resolve relative SQLite paths against the project
# root so both launch locations use the same persisted data.
if parsed_database_url.get_backend_name() == "sqlite":
    database_path = parsed_database_url.database
    if (
        database_path
        and database_path != ":memory:"
        and not Path(database_path).is_absolute()
    ):
        project_root = Path(__file__).resolve().parents[3]
        database_url = parsed_database_url.set(
            database=str((project_root / database_path).resolve())
        ).render_as_string(hide_password=False)

connect_args: dict[str, object] = {}

if parsed_database_url.get_backend_name() == "sqlite":
    connect_args["check_same_thread"] = False


engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)


# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================
# REQUEST DATABASE SESSION
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide one transactional database session per request.

    Transaction lifecycle:

        Request starts
            ↓
        Open session
            ↓
        Route/service performs database operations
            ↓
        Successful request → COMMIT
            ↓
        Failed request → ROLLBACK
            ↓
        Close session

    Individual repositories may still call flush() when they
    need generated database values immediately. The transaction
    itself is committed centrally at the end of a successful
    request.
    """

    db = SessionLocal()

    try:
        yield db

        # ----------------------------------------------------
        # Successful request
        # ----------------------------------------------------
        db.commit()

    except Exception:
        # ----------------------------------------------------
        # Failed request
        # ----------------------------------------------------
        db.rollback()
        raise

    finally:
        # ----------------------------------------------------
        # Always release the database session
        # ----------------------------------------------------
        db.close()
