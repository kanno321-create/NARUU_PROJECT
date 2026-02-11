"""Health check endpoints"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from naruu_api.config import config
from naruu_api.db import check_db_health

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "live",
            "version": config.APP_VERSION,
            "service": "naruu-platform",
            "environment": config.APP_ENV,
        },
    )


@router.get("/health/db")
async def db_health():
    result = await check_db_health()
    status_code = 200 if result["connected"] else 503
    return JSONResponse(status_code=status_code, content=result)
