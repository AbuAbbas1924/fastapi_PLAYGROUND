from fastapi import APIRouter

from book_a1.auth import router as auth_router
from book_a1.book import router as book_router
from book_a1.db import db

db = db

router = APIRouter(prefix="/book_a1", tags=["book_a1"])
router.include_router(book_router)
router.include_router(auth_router)
