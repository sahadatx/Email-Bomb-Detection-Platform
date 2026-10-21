"""Register the independently permissioned Settings API."""

from app.core.registry import module_registry

from .api.routes import router

MODULE_NAME = "settings"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/settings"
MODULE_TAGS = ("System Settings",)


def register_module() -> None:
    if module_registry.get(MODULE_NAME) is None:
        module_registry.register(
            name=MODULE_NAME,
            router=router,
            prefix=MODULE_PREFIX,
            tags=MODULE_TAGS,
        )
