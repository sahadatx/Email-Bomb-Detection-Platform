from fastapi import APIRouter

from .explainability.router import router as explainability_router
from .evidence.router import router as evidence_router
from .reporting.router import router as reporting_router

router = APIRouter()
router.include_router(explainability_router)
router.include_router(evidence_router)
router.include_router(reporting_router)
