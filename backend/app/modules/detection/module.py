from app.core.registry import module_registry
from app.modules.detection.routes import router

MODULE_NAME = "detection"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/detection"
MODULE_TAGS = ("Detection & Risk Analysis",)


def register_module() -> None:
    if module_registry.get(MODULE_NAME) is None:
        module_registry.register(name=MODULE_NAME, router=router, prefix=MODULE_PREFIX, tags=MODULE_TAGS)
