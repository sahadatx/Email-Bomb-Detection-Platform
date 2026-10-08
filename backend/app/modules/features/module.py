from __future__ import annotations

from app.core.registry import module_registry

from .routes import router


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "features"

MODULE_PREFIX = "/features"

MODULE_TAGS = (
    "Feature Engineering",
)


# ============================================================
# MODULE REGISTRATION
# ============================================================


def register_module() -> None:
    """
    Register Module 04 — Feature Engineering.

    Registration is intentionally idempotent.

    If the module has already been registered, this function
    returns without modifying the existing registry entry.

    The central application registry is responsible for
    combining:

        API prefix
        +
        module prefix
        +
        module router

    Final API namespace:

        /api/v1/features
    """

    # --------------------------------------------------------
    # Prevent duplicate registration
    # --------------------------------------------------------

    if module_registry.get(
        MODULE_NAME,
    ) is not None:
        return

    # --------------------------------------------------------
    # Register module router
    # --------------------------------------------------------

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )


# ============================================================
# PUBLIC MODULE API
# ============================================================

__all__ = [
    "MODULE_NAME",
    "MODULE_PREFIX",
    "MODULE_TAGS",
    "register_module",
]