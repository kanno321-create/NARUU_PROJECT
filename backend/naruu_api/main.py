"""
NARUU AI Tourism Management Platform - FastAPI Main Application
Japanese Medical/Beauty/Tourism Agency Management System
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from naruu_api.config import config
from naruu_api.db import init_db, close_db, check_db_health

# Routers
from naruu_api.routers import health, auth, customers, partners, products, bookings

logging.basicConfig(
    level=getattr(logging, config.APP_LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with startup/shutdown"""
    startup_start = time.time()
    logger.info(f"[STARTUP] NARUU Platform v{config.APP_VERSION} [{config.APP_ENV}]")

    # 1. Database
    logger.info("[STARTUP] Connecting to database...")
    t0 = time.time()
    try:
        await init_db()
        logger.info(f"[STARTUP] Database OK in {int((time.time() - t0) * 1000)}ms")
    except Exception as e:
        logger.error(f"[STARTUP] Database FAILED: {e}")
        logger.warning("Starting in degraded mode")

    total_ms = int((time.time() - startup_start) * 1000)
    logger.info(f"[STARTUP] Complete in {total_ms}ms")

    yield

    # Shutdown
    logger.info("[SHUTDOWN] Closing connections...")
    await close_db()
    logger.info("[SHUTDOWN] Complete")


app = FastAPI(
    title="NARUU AI Tourism Platform",
    version=config.APP_VERSION,
    description="일본인 대상 대구 의료/뷰티/관광 종합 AI 관리 시스템",
    lifespan=lifespan,
    debug=config.APP_DEBUG,
)

# CORS
def _get_cors_origins() -> list[str]:
    origins_str = config.CORS_ORIGINS
    if not origins_str:
        if config.is_development():
            return ["*"]
        return []
    return [o.strip() for o in origins_str.split(",") if o.strip()]

_cors_origins = _get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials="*" not in _cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept-Language", "X-Request-ID"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/v1")
app.include_router(customers.router, prefix="/v1")
app.include_router(partners.router, prefix="/v1")
app.include_router(products.router, prefix="/v1")
app.include_router(bookings.router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "naruu_api.main:app",
        host="0.0.0.0",
        port=config.APP_PORT,
        reload=config.is_development(),
        timeout_keep_alive=30,
    )
