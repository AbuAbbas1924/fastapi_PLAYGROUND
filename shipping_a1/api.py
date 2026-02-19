from fastapi import APIRouter

from shipping_a1.main import router as main_router
from shipping_a1.tests import router as tests_router

router = APIRouter(prefix="/shipping_a1", tags=["shipping_a1"])
router.include_router(main_router)
router.include_router(tests_router)
