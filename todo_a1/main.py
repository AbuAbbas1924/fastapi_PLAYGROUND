from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from todo_a1.auth import router as auth_router
from todo_a1.db import Base, engine

# from fastapi.templating import Jinja2Templates
from todo_a1.todo import router as todo_router

# run server
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/todo_a1", tags=["todo_a1"])
router.include_router(todo_router)
router.include_router(auth_router)


@router.get("/root", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content="root page", status_code=200)
