from __future__ import annotations

from app.core.registry import module_registry

from .routes import router


MODULE_NAME = "parsing"
MODULE_PREFIX = "/parsing"
MODULE_TAGS = ("Email Parsing",)


def register_module() -> None:
    """
    Register Module 03 with the application registry.

    Registration is idempotent.
    """

    if module_registry.get(MODULE_NAME) is not None:
        return

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )