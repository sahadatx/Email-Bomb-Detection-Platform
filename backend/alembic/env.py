
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool


# ============================================================
# PYTHON PATH
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# APPLICATION IMPORTS
# ============================================================

from app.core.config import settings
from app.core.database import Base


# ============================================================
# MODEL REGISTRATION
# ============================================================
# Import all model modules before using Base.metadata.
# Keep these imports so Alembic can discover every table.

from app.modules.users import models as user_models  # noqa: F401
from app.modules.emails import models as email_models  # noqa: F401
from app.modules.emails import collection_models  # noqa: F401
from app.modules.parsing import models as parsing_models  # noqa: F401
from app.modules.features import models as feature_models  # noqa: F401
from app.modules.datasets import models as dataset_models  # noqa: F401
from app.modules.preprocessing import models as preprocessing_models  # noqa: F401
from app.modules.ml_models import models as ml_model_models  # noqa: F401
from app.modules.detection import models as detection_models  # noqa: F401
from app.modules.investigation_reporting import models as investigation_reporting_models  # noqa: F401
from app.modules.audit_security_admin import models as audit_security_admin_models  # noqa: F401
from app.modules.experiments import models as experiment_models  # noqa: F401
from app.modules.threat_intelligence import models as threat_intelligence_models  # noqa: F401


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# TARGET METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# DATABASE URL
# ============================================================

def get_database_url() -> str:
    """Return the database URL configured by the application."""
    return settings.database_url


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# MIGRATION ENTRYPOINT
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
