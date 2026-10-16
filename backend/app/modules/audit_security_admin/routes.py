from fastapi import APIRouter

from .audit.router import router as audit_router
from .security_monitoring.router import router as security_router
from .administration.router import router as administration_router

router = APIRouter()
router.include_router(audit_router)
router.include_router(security_router)
router.include_router(administration_router)
