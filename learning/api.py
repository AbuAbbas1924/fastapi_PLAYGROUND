from fastapi import APIRouter

from learning import json_db

router = APIRouter(prefix="/learning", tags=["learning"])
router.include_router(json_db.router, prefix="/json_db", tags=["json_db"])
