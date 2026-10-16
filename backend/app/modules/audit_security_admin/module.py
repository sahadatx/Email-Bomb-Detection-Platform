from app.core.registry import module_registry
from .routes import router

MODULE_NAME = "audit_security_admin"
MODULE_PREFIX = ""
MODULE_TAGS = ("Audit, Security Monitoring & Administration",)


def register_module():
    if module_registry.get(MODULE_NAME) is None:
        module_registry.register(name=MODULE_NAME, router=router, prefix=MODULE_PREFIX, tags=MODULE_TAGS)
