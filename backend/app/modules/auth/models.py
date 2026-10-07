from app.core.registry import module_registry

from app.modules.auth.routes import router


MODULE_NAME = "auth"
MODULE_PREFIX = "/auth"
MODULE_TAGS = ("Authentication",)


def register_module() -> None:
    module_registry.register(
        name=MODULE_NAME,
        router=router,
        prefix=MODULE_PREFIX,
        tags=list(MODULE_TAGS),
    )