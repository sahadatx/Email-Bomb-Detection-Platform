"""
Preprocessing Pipeline Module
=============================

Responsibilities:
    - Define Preprocessing module metadata.
    - Expose the Preprocessing router.
    - Register the module with the central application registry.

The application entry point is responsible for calling
register_module().

The central registry is responsible for mounting the module
router on the FastAPI application using MODULE_PREFIX
and MODULE_TAGS.
"""

from __future__ import annotations

from app.core.registry import module_registry
from app.modules.preprocessing.routes import router


# ---------------------------------------------------------------------------
# Module Metadata
# ---------------------------------------------------------------------------

MODULE_NAME = "preprocessing"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/preprocessing"
MODULE_TAGS = ("Preprocessing Pipeline",)


# ---------------------------------------------------------------------------
# Module Registration
# ---------------------------------------------------------------------------

def register_module() -> None:
    """
    Register the Preprocessing module.

    Registration is idempotent: repeated calls do not register
    the same module more than once.

    The central registry is responsible for mounting the router
    in the FastAPI application.
    """

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

__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "MODULE_PREFIX",
    "MODULE_TAGS",
    "router",
    "register_module",
]