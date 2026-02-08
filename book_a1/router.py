from fastapi import APIRouter

router = APIRouter(prefix="/book_a1", tags=["book_a1"])

@router.get("/")
async def read_root():
    return {"message": "Hello from the router!"}