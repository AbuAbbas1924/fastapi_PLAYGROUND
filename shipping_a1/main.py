from fastapi import APIRouter
from redis.asyncio import Redis
from scalar_fastapi import get_scalar_api_reference

router = APIRouter()

__all__ = ["Redis"]

@router.get("/scalar", include_in_schema=False)
async def scalar():
    return get_scalar_api_reference(
        # router.openapi_url doesn't work in router
        # openapi_url=router.openapi_url,
        openapi_url="/openapi.json",
        title="Scalar API Refernce",
    )
