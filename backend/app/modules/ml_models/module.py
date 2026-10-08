from __future__ import annotations

from app.core.registry import module_registry
from app.modules.ml_models.routes import router as ml_models_router


# ---------------------------------------------------------------------------
# Module Metadata
# ---------------------------------------------------------------------------

MODULE_NAME = "ml_models"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/ml-models"
MODULE_TAGS = ("ML Model Management",)

router = ml_models_router


# ---------------------------------------------------------------------------
# Module Registration
# ---------------------------------------------------------------------------

def register_module() -> None:
    """Register the ML Model Management module."""

    if module_registry.get(MODULE_NAME) is not None:
        return

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_router():
    """Return the ML Model Management API router."""
    return router


__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "MODULE_PREFIX",
    "MODULE_TAGS",
    "router",
    "get_router",
    "register_module",
]