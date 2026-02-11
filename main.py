from contextlib import asynccontextmanager

from fastapi import FastAPI

from book_a1 import api as book_a1_api


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
        print("  2. Verify connection settings in book_a1/.env")
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
