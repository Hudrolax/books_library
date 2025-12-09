from fastapi import APIRouter

from .healthcheck_router import router as healthcheck_router


router = APIRouter(
    prefix="/v1",
)

router.include_router(healthcheck_router)
