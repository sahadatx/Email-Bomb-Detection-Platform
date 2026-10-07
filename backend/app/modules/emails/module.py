from __future__ import annotations

from app.core.registry import module_registry

from .routes import router


MODULE_NAME = "emails"
MODULE_PREFIX = "/emails"
MODULE_TAGS = ("Email Collection",)


def register_module() -> None:
    """
    Register the Email Collection & Ingestion module
    with the central application registry.

    Registration is idempotent so the module can safely be
    initialized multiple times without duplicate registration.
    """

    if module_registry.get(MODULE_NAME) is not None:
        return

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )