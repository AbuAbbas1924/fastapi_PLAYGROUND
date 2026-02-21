from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth_a1 import main as auth_a1_main
from auth_b1.main import router as auth_b1_router
from book_a1 import api as book_a1_api
from htmx_todo_a1.main import router as htmx_todo_a1_main
from learning import api as learning_api
from shipping_a1 import api as shipping_a1_api
from todo_a1 import main as todo_a1_main

# print(f"___{auth_a1_main}")

@asynccontextmanager
async def async_lifespan(app: FastAPI):
    try:
        await book_a1_api.db.init()
        print("book_a1 started")
        async with auth_a1_main.engine.begin() as connection:
            await connection.run_sync(auth_a1_main.auth_a1_meta.create_all)
        print("run shipping_a1")
        await shipping_a1_api.db()
    except RuntimeError as e:
        print("❌ STARTUP FAILED\n" + "=" * 50)
        print(f"\nReason: {str(e)}")
        print("=" * 50)
        raise
    yield
    print("shutdown ALL_APPS")
    await book_a1_api.db.close()
    await auth_a1_main.engine.dispose()

app = FastAPI(
    title="playground",
    description="to test every aspect of fastapi",
    version="0.1",
    lifespan=async_lifespan,
)
app.include_router(book_a1_api.router)
app.include_router(htmx_todo_a1_main)
app.include_router(auth_b1_router)
app.mount(
    "/htmx_todo_a1/static",
    StaticFiles(directory="htmx_todo_a1/static"),
    name="htmx_todo_a1_static",
)
app.include_router(auth_a1_main.router)
app.include_router(shipping_a1_api.router)
app.include_router(learning_api.router)
app.include_router(todo_a1_main.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        workers=1,
    )
