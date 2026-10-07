from __future__ import annotations

from app.core.registry import module_registry
from app.modules.auth.routes import router


MODULE_NAME = "auth"
MODULE_PREFIX = "/auth"
MODULE_TAGS = ("Authentication",)


def register_module() -> None:
    """
    Register the authentication module with the central module registry.

    Registration is idempotent so repeated imports or development reloads
    do not create duplicate-registration errors.
    """
    if module_registry.get(MODULE_NAME) is not None:
        return

    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=MODULE_TAGS,
    )