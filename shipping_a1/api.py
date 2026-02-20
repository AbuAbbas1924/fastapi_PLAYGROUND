from fastapi import APIRouter

from shipping_a1.db import create_db_and_tables
from shipping_a1.main import router as main_router
from shipping_a1.seller import router as seller_router
from shipping_a1.ship import router as ship_router
from shipping_a1.tests import router as tests_router

router = APIRouter(prefix="/shipping_a1", tags=["shipping_a1"])
router.include_router(main_router)
router.include_router(seller_router)
router.include_router(ship_router)
router.include_router(tests_router)

db = create_db_and_tables