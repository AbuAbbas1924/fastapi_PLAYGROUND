from fastapi import FastAPI

from book_a1.router import router

app = FastAPI()
app.include_router(router)
# def main():
#     print("Hello from playground!")


if __name__ == "__main__":
    # main()
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info", workers=1)