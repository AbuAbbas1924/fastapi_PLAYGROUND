from contextlib import asynccontextmanager

from fastapi import FastAPI

from book_a1.auth import router as book_a1_auth
from book_a1.book import router as book_a1_book
from book_a1.postgres import db as book_a1_db

# import book_a1


@asynccontextmanager
async def async_lifespan(app: FastAPI):
    print("STARTING DB")
    # await book_a1.postgres.db.init()
    await book_a1_db.init()
    yield

app = FastAPI(
    title="playground",
    description="to test every aspect of fastapi",
    version="0.1",
    lifespan=async_lifespan,
)
# app.include_router(book_a1.router.router)
app.include_router(book_a1_book)
app.include_router(book_a1_auth)


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
