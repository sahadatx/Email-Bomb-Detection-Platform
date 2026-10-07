from __future__ import annotations

from app.core.registry import module_registry
from app.modules.users.routes import router


MODULE_NAME = "users"
MODULE_PREFIX = "/users"
MODULE_TAGS = ("Users",)


def register_module() -> None:
    """
    Register the users module with the central application registry.
    """
    if module_registry.get(MODULE_NAME) is not None:
        return

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )