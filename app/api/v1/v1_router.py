from fastapi import APIRouter

from .books import router as books_router
from .export import router as export_router
from .healthcheck_router import router as healthcheck_router


router = APIRouter(
    prefix="/v1",
)

router.include_router(healthcheck_router)
router.include_router(books_router)
router.include_router(export_router)
