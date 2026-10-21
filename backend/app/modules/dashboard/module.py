"""Registration for the dashboard aggregation API."""

from app.core.registry import module_registry

from .api.routes import router

MODULE_NAME = "dashboard"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/dashboard"
MODULE_TAGS = ("Dashboard",)


def register_module() -> None:
    """Register this module once in the shared API registry."""
    if module_registry.get(MODULE_NAME) is None:
        module_registry.register(
            name=MODULE_NAME,
            router=router,
            prefix=MODULE_PREFIX,
            tags=MODULE_TAGS,
        )
