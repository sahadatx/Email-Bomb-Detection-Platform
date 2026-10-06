"""
Email Bomb Detection Platform

Application entry point.

Responsibilities:
    - Configure application logging.
    - Register application modules.
    - Include registered module routers.
    - Configure CORS.
    - Configure global exception handlers.
    - Expose system health endpoints.
    - Manage application lifecycle.

API structure:
    /health
    /api/v1/health
    /api/v1/auth/*
    /api/v1/users/*
    /api/v1/emails/*
    /api/v1/parsing/*
    /api/v1/features/*
    /api/v1/datasets/*
    /api/v1/preprocessing/*
    /api/v1/ml-models/*
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.schemas import HealthResponse
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.core.registry import module_registry

# ---------------------------------------------------------------------------
# Module registration imports
# ---------------------------------------------------------------------------

from app.modules.auth.module import (
    register_module as register_auth_module,
)

from app.modules.users.module import (
    register_module as register_users_module,
)

from app.modules.emails.module import (
    register_module as register_emails_module,
)

from app.modules.parsing.module import (
    register_module as register_parsing_module,
)

from app.modules.features.module import (
    register_module as register_features_module,
)

from app.modules.datasets.module import (
    register_module as register_datasets_module,
)

from app.modules.preprocessing.module import (
    register_module as register_preprocessing_module,
)

from app.modules.ml_models.module import (
    register_module as register_ml_models_module,
)
from app.modules.detection.module import register_module as register_detection_module
from app.modules.investigation_reporting.module import (
    register_module as register_investigation_reporting_module,
)
from app.modules.audit_security_admin.module import (
    register_module as register_audit_security_admin_module,
)
from app.modules.analytics.module import register_module as register_analytics_module
from app.modules.experiments.module import (
    register_module as register_experiments_module,
)
from app.modules.threat_intelligence.module import (
    register_module as register_threat_intelligence_module,
)
from app.modules.dashboard.module import register_module as register_dashboard_module
from app.modules.settings.module import register_module as register_settings_module
from app.modules.threat_intelligence.service import run_feed_scheduler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

configure_logging()

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------


def register_application_modules() -> None:
    """
    Register all application modules with the central registry.

    Each module owns its:
        - Module name
        - Module version
        - API prefix
        - Router
        - Tags

    Registration order:
        1. Authentication
        2. User Management
        3. Email Collection & Ingestion
        4. Email Parsing & Normalization
        5. Feature Engineering
        6. Dataset Management
        7. Preprocessing Pipeline
        8. ML Model Management

    Each module is responsible for idempotent registration.
    """

    register_auth_module()
    register_users_module()
    register_emails_module()
    register_parsing_module()
    register_features_module()
    register_datasets_module()
    register_preprocessing_module()
    register_ml_models_module()
    register_detection_module()
    register_investigation_reporting_module()
    register_audit_security_admin_module()
    register_analytics_module()
    register_experiments_module()
    register_threat_intelligence_module()
    register_dashboard_module()
    register_settings_module()


# ---------------------------------------------------------------------------
# Router inclusion
# ---------------------------------------------------------------------------


def include_registered_modules(app: FastAPI) -> None:
    """
    Include all registered module routers in the FastAPI application.

    The application owns the global API prefix.

    Example:
        settings.api_v1_prefix = "/api/v1"
        module.prefix = "/datasets"

    Final endpoint:
        /api/v1/datasets
    """

    for module in module_registry.all():
        full_prefix = f"{settings.api_v1_prefix}" f"{module.prefix}"

        app.include_router(
            module.router,
            prefix=full_prefix,
            tags=list(module.tags),
        )

        logger.info(
            "Registered module: %s | prefix=%s",
            module.name,
            full_prefix,
        )


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Application lifecycle handler.

    Startup and shutdown operations should be added here only
    when they are genuinely application-wide.
    """

    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )

    logger.info(
        "Registered modules: %s",
        ", ".join(module.name for module in module_registry.all()),
    )

    scheduler_stop = asyncio.Event()
    scheduler_task = asyncio.create_task(run_feed_scheduler(scheduler_stop))
    try:
        yield
    finally:
        scheduler_stop.set()
        await scheduler_task

    logger.info(
        "Stopping %s",
        settings.app_name,
    )


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Email Bomb Detection Platform API",
    debug=settings.debug,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """
    Handle application-level exceptions.
    """

    logger.warning(
        "Application error: %s %s -> %s",
        request.method,
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": jsonable_encoder(exc.details),
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI and Pydantic request validation errors.

    Pydantic may include exception objects inside error context.
    jsonable_encoder converts them before JSONResponse serialization.
    """

    logger.warning(
        "Request validation error: %s %s",
        request.method,
        request.url.path,
    )

    validation_errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={
            ValueError: str,
            TypeError: str,
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "request_validation_error",
                "message": "Request validation failed.",
                "details": validation_errors,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application errors.

    Full exception details are logged server-side.
    Sensitive internal details are not exposed to clients.
    """

    logger.exception(
        "Unhandled application error: %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "internal_server_error",
                "message": ("An unexpected server error occurred."),
                "details": None,
            },
        },
    )


# ---------------------------------------------------------------------------
# System health endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health_check() -> HealthResponse:
    """
    Global application health endpoint.
    """

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@app.get(
    f"{settings.api_v1_prefix}/health",
    response_model=HealthResponse,
    tags=["System"],
)
def api_health_check() -> HealthResponse:
    """
    API health endpoint.
    """

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


# ---------------------------------------------------------------------------
# Application module registration
# ---------------------------------------------------------------------------

# Register all modules before including their routers.
register_application_modules()
include_registered_modules(app)
