from app.core.registry import module_registry
from .routes import router

MODULE_NAME = "experiments"
MODULE_VERSION = "1.0.0"
MODULE_PREFIX = "/experiments"
MODULE_TAGS = ("Experiments",)


def register_module():
    if module_registry.get(MODULE_NAME) is None:
        module_registry.register(name=MODULE_NAME, router=router, prefix=MODULE_PREFIX, tags=MODULE_TAGS)
