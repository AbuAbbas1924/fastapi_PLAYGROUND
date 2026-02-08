from fastapi import FastAPI

from book_a1.postgres import db
from book_a1.router import router

app = FastAPI(
    title="playground",
    description="to test every aspect of fastapi",
    version="0.1",
    lifespan=db.async_lifespan,
)
app.include_router(router)


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
