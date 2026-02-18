from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth_b1.main import router as auth_b1_router
from book_a1 import api as book_a1_api
from htmx_todo_a1.main import router as htmx_todo_a1_router


@asynccontextmanager
async def async_lifespan(app: FastAPI):
    print("=" * 50)
    print("STARTING APPLICATION")
    print("=" * 50)
    try:
        await book_a1_api.db.init()
        print("\n✓ Application started successfully!\n")
    except RuntimeError as e:
        print("\n" + "=" * 50)
        print("❌ STARTUP FAILED")
        print("=" * 50)
        print(f"\nReason: {str(e)}")
        print("\nTo fix this:")
        print("  1. Start PostgreSQL server")
        print("  2. Verify connection settings in every .env files")
        print("  3. Restart the application\n")
        print("=" * 50)
        raise
    yield
    print("shutdown")
    await book_a1_api.db.close()

app = FastAPI(
    title="playground",
    description="to test every aspect of fastapi",
    version="0.1",
    lifespan=async_lifespan,
)
app.include_router(book_a1_api.router)
app.include_router(htmx_todo_a1_router)
app.include_router(auth_b1_router)
app.mount(
    "/htmx_todo_a1/static",
    StaticFiles(directory="htmx_todo_a1/static"),
    name="htmx_todo_a1_static",
)

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
