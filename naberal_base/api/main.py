"""
KIS Estimator API - FastAPI Main Application
Contract-First + Evidence-Gated + Zero-Mock System
"""

import logging
import json
import os
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.db import init_db, close_db, check_db_health
from api.config import config
from api.cache import cache
from api.middleware import RateLimitMiddleware, IdempotencyMiddleware
from api.middleware.performance import PerformanceMiddleware
from api.routers import catalog, estimate, kpew, quotes, drawings, public
from api.routers.erp import (
    customers_router,
    products_router,
    vouchers_router,
    reports_router,
    carryover_router,
    # 추가 ERP 라우터
    company_router,
    employees_router,
    payroll_router,
    orders_router,
    statements_router,
    inventory_router,
    settings_router,
    accounting_router,
    audit_router,
    bank_accounts_router,
    estimate_files_router,
    drawing_files_router,
    # FE-BE 경로 어댑터 라우터
    sales_adapter_router,
    purchases_adapter_router,
    payments_adapter_router,
    dashboard_adapter_router,
    tax_invoices_router,
)
from api.error_handler import register_error_handlers
from kis_estimator_core.infra.redis_driver import RedisDriver
from kis_estimator_core.services.catalog_service import get_catalog_service
from kis_estimator_core.infra.db import get_db_instance
from kis_estimator_core.rag.api import router as rag_router
from kis_estimator_core.api.routes.auth import router as auth_router
from kis_estimator_core.api.routes.email import router as email_router
from kis_estimator_core.api.routes.ai_manager import router as ai_manager_router
from kis_estimator_core.api.routes.ai_chat import router as ai_chat_router
from kis_estimator_core.api.routes.ai_sessions import router as ai_sessions_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.APP_LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Redis driver instance (for rate limiting, idempotency, health checks)
redis_driver = None

# SSOT files directory
SSOT_DIR = Path(__file__).parent.parent / "knowledge_consolidation" / "output"
SSOT_FILES = [
    "estimates.json",
    "standards.json",
    "formulas.json",
    "enclosures.json",
    "breakers.json",
    "accessories.json",
]


def check_ssot_health() -> Dict[str, Any]:
    """
    Check SSOT 6종 JSON 파일 존재 및 버전 확인

    Returns:
        {
            "status": "ok" | "partial" | "error",
            "files_found": 6,
            "files_total": 6,
            "files": {
                "estimates.json": {"exists": True, "version": "...", "size": 12345},
                ...
            }
        }
    """
    result = {
        "status": "ok",
        "files_found": 0,
        "files_total": len(SSOT_FILES),
        "files": {},
    }

    for filename in SSOT_FILES:
        file_path = SSOT_DIR / filename

        if file_path.exists():
            try:
                # 파일 크기
                size = file_path.stat().st_size

                # 버전 정보 추출 (JSON에서 version 필드 읽기)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version = (
                        data.get("version")
                        or data.get("meta", {}).get("version")
                        or "unknown"
                    )

                result["files"][filename] = {
                    "exists": True,
                    "version": version,
                    "size": size,
                }
                result["files_found"] += 1
            except Exception as e:
                result["files"][filename] = {
                    "exists": True,
                    "version": "error",
                    "size": 0,
                    "error": str(e),
                }
        else:
            result["files"][filename] = {"exists": False, "version": None, "size": 0}

    # 전체 상태 결정
    if result["files_found"] == result["files_total"]:
        result["status"] = "ok"
    elif result["files_found"] > 0:
        result["status"] = "partial"
    else:
        result["status"] = "error"

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup timeline tracking"""
    global redis_driver

    # Startup timeline tracking
    startup_start = time.time()
    startup_status = {
        "db": {"ready": False, "elapsed_ms": 0, "error": None},
        "cache": {"ready": False, "elapsed_ms": 0, "error": None},
        "catalog": {"ready": False, "elapsed_ms": 0, "error": None},
        "redis": {"ready": False, "elapsed_ms": 0, "error": None},
    }

    logger.info(f"[STARTUP][T00] Starting KIS Estimator API v1.0.0 [{config.APP_ENV}]")

    # 1. Database initialization
    logger.info("[STARTUP][T01] Connecting to database...")
    t0 = time.time()
    try:
        await init_db()
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["db"] = {"ready": True, "elapsed_ms": elapsed_ms, "error": None}
        logger.info(f"[DONE][T01] Database OK in {elapsed_ms}ms")
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["db"] = {
            "ready": False,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }
        logger.error(f"[FAIL][T01] Database failed in {elapsed_ms}ms: {e}")
        raise  # Fatal: DB is critical

    # 2. Cache initialization
    logger.info("[STARTUP][T02] Connecting to cache...")
    t0 = time.time()
    try:
        cache_health = cache.health_check()
        elapsed_ms = int((time.time() - t0) * 1000)
        if cache_health.get("connected") is True:
            startup_status["cache"] = {
                "ready": True,
                "elapsed_ms": elapsed_ms,
                "error": None,
            }
            logger.info(f"[DONE][T02] Cache OK in {elapsed_ms}ms")
        else:
            startup_status["cache"] = {
                "ready": False,
                "elapsed_ms": elapsed_ms,
                "error": "Not connected",
            }
            logger.warning(f"[WARN][T02] Cache not connected in {elapsed_ms}ms")
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["cache"] = {
            "ready": False,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }
        logger.error(f"[FAIL][T02] Cache failed in {elapsed_ms}ms: {e}")

    # 3. Catalog cache preload (JSON only, no Supabase)
    logger.info("[STARTUP][T03] Preloading catalog cache from JSON...")
    t0 = time.time()
    try:
        service = get_catalog_service()
        service.initialize_cache()
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["catalog"] = {
            "ready": True,
            "elapsed_ms": elapsed_ms,
            "error": None,
        }
        logger.info(f"[DONE][T03] Catalog cache OK in {elapsed_ms}ms")
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["catalog"] = {
            "ready": False,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }
        logger.warning(
            f"[WARN][T03] Catalog cache failed (non-fatal) in {elapsed_ms}ms: {e}"
        )
        logger.info("Tests will use catalog_initialized fixture for catalog data")

    # 4. Redis driver initialization
    logger.info("[STARTUP][T04] Connecting to Redis...")
    t0 = time.time()
    try:
        redis_driver = RedisDriver()
        if redis_driver.ping():
            elapsed_ms = int((time.time() - t0) * 1000)
            startup_status["redis"] = {
                "ready": True,
                "elapsed_ms": elapsed_ms,
                "error": None,
            }
            logger.info(f"[DONE][T04] Redis OK in {elapsed_ms}ms")
        else:
            elapsed_ms = int((time.time() - t0) * 1000)
            startup_status["redis"] = {
                "ready": False,
                "elapsed_ms": elapsed_ms,
                "error": "Ping failed",
            }
            logger.warning(f"[WARN][T04] Redis ping failed in {elapsed_ms}ms")
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        startup_status["redis"] = {
            "ready": False,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }
        logger.warning(f"[WARN][T04] Redis failed (non-fatal) in {elapsed_ms}ms: {e}")
        redis_driver = None

    # Final startup summary
    total_elapsed_ms = int((time.time() - startup_start) * 1000)
    db_status = "OK" if startup_status["db"]["ready"] else "FAIL"
    cache_status = "OK" if startup_status["cache"]["ready"] else "WARN"
    catalog_status = "OK" if startup_status["catalog"]["ready"] else "WARN"
    redis_status = "OK" if startup_status["redis"]["ready"] else "WARN"

    logger.info(
        f"[STARTUP] complete in {total_elapsed_ms}ms "
        f"(db={db_status}, cache={cache_status}, catalog={catalog_status}, redis={redis_status})"
    )

    # Store startup status in app.state for /readyz endpoint
    app.state.startup_status = startup_status

    yield

    # Shutdown
    logger.info("[SHUTDOWN] Shutting down...")
    await close_db()
    # Note: RedisDriver uses redis.Redis which auto-closes on GC
    logger.info("[SHUTDOWN] Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="KIS Estimator API",
    version="1.0.0",
    description="전기 패널 견적 자동화 시스템 - Contract-First + Evidence-Gated + Zero-Mock",
    lifespan=lifespan,
    debug=config.APP_DEBUG,
)

# Rate Limiting middleware (100 req/10s, 300 req/min)
# IMPORTANT: Must be registered BEFORE CORS
app.add_middleware(
    RateLimitMiddleware, requests_per_10_seconds=100, requests_per_minute=300
)

# Idempotency middleware (24 hour TTL)
app.add_middleware(IdempotencyMiddleware, ttl_seconds=86400)

# Performance tracking middleware (Phase VII-4: Background Task 최적화)
# Redis 저장을 응답 후 백그라운드에서 실행 → 0 latency
app.add_middleware(PerformanceMiddleware, redis_cache=cache)

# CORS middleware (must be last)
def _get_cors_origins() -> list[str]:
    origins_str = os.getenv("CORS_ORIGINS", "")
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
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "Idempotency-Key"],
)

# Register error handlers (BEFORE routers)
register_error_handlers(app)

# Include routers
app.include_router(catalog.router)
app.include_router(estimate.router)
app.include_router(kpew.router)
app.include_router(quotes.router)  # Phase X: Quote Lifecycle & Approval Pack
app.include_router(drawings.router)
app.include_router(public.router)  # Public API (hkkor.com 공개 사이트)
app.include_router(rag_router)

# Auth Router (인증/사용자 관리)
app.include_router(auth_router, prefix="/v1")

# ERP Routers (Phase 2: ERP 기초 구축)
app.include_router(customers_router, prefix="/v1/erp")
app.include_router(products_router, prefix="/v1/erp")
app.include_router(vouchers_router, prefix="/v1/erp")
app.include_router(reports_router, prefix="/v1/erp")
app.include_router(carryover_router, prefix="/v1/erp")

# 추가 ERP Routers (Phase 2.5: ERP 스켈레톤 완성)
app.include_router(company_router, prefix="/v1/erp")
app.include_router(employees_router, prefix="/v1/erp")
app.include_router(payroll_router, prefix="/v1/erp")
app.include_router(orders_router, prefix="/v1/erp")
app.include_router(statements_router, prefix="/v1/erp")
app.include_router(inventory_router, prefix="/v1/erp")
app.include_router(settings_router, prefix="/v1/erp")
app.include_router(accounting_router, prefix="/v1/erp")
app.include_router(audit_router, prefix="/v1/erp")
app.include_router(bank_accounts_router, prefix="/v1/erp")

# 파일 저장 Routers (견적/도면 DB 저장)
app.include_router(estimate_files_router, prefix="/v1/erp")
app.include_router(drawing_files_router, prefix="/v1/erp")

# FE-BE 경로 어댑터 Routers (프론트엔드 호출 경로 대응)
app.include_router(sales_adapter_router, prefix="/v1/erp")
app.include_router(purchases_adapter_router, prefix="/v1/erp")
app.include_router(payments_adapter_router, prefix="/v1/erp")
app.include_router(dashboard_adapter_router, prefix="/v1/erp")
app.include_router(tax_invoices_router, prefix="/v1/erp")

# 이메일 Router (SMTP 발송 + IMAP 수신)
app.include_router(email_router, prefix="/v1")

# AI Manager / Chat / Sessions Routers
app.include_router(ai_manager_router, prefix="/v1/ai-manager")
app.include_router(ai_chat_router, prefix="/v1/ai")
app.include_router(ai_sessions_router)

# NOTE: GET / endpoint removed (T3 - Contract Fixation)
# Not part of the 9 required endpoints per REBUILD specification
# Clients should use /health for service status checks


@app.get("/health")
async def health_check():
    """
    Simple liveness health check endpoint.

    Returns 200 if the process is alive and can respond to requests.
    For detailed dependency checks, use /readyz instead.

    Returns:
        {"status": "live", "version": "1.0.0"}
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "live",
            "version": "1.0.0",
            "environment": config.APP_ENV,
        },
    )


@app.get("/health/live")
async def liveness_check():
    """
    Liveness probe endpoint (Phase VII-4 정석).

    Kubernetes liveness probe: 프로세스 생존 확인만.
    DB 체크 없음 → <10ms 목표 달성.

    Returns:
        {"status": "live", "timestamp": "2025-11-19T12:34:56Z"}
    """
    from datetime import datetime
    return {
        "status": "live",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/health/db")
async def database_health_check():
    """
    Database health probe endpoint (Phase VII).

    Checks database connectivity only.

    Returns:
        200 OK: {"status": "connected", "latency_ms": <float>}
        503 Service Unavailable: {"status": "disconnected", "error": "<message>"}
    """
    db_health = await check_db_health()

    if db_health["connected"]:
        return JSONResponse(
            status_code=200,
            content={
                "status": "connected",
                "latency_ms": db_health.get("latency_ms", 0),
            },
        )
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "disconnected",
                "error": db_health.get("error", "Database connection failed"),
            },
        )


# Phase VII-4 optimization: 1-second cache for readiness check
_readiness_cache = {"response": None, "expires_at": 0}


@app.get("/readyz")
async def readiness_check():
    """
    Strict readiness check endpoint for Kubernetes/production deployments.

    Phase VII-4 optimization: 1-second response cache to reduce p95 from ~344ms to <100ms.

    Returns 200 ONLY if ALL critical dependencies are ready:
    - Database: connected
    - Cache: connected
    - Catalog: preloaded

    Returns 503 if ANY critical dependency is not ready.

    Returns:
        {
            "status": "ready" | "not_ready",
            "timestamp": "2025-11-12T12:34:56Z",
            "critical_dependencies": {
                "database": {"ready": true, "elapsed_ms": 45, "error": null},
                "cache": {"ready": true, "elapsed_ms": 12, "error": null},
                "catalog": {"ready": true, "elapsed_ms": 234, "error": null}
            },
            "optional_dependencies": {
                "redis": {"ready": true, "elapsed_ms": 23, "error": null}
            },
            "failing_components": [],  // Non-empty if any critical dependency failed
            "version": "1.0.0"
        }
    """
    import time
    from datetime import datetime

    # Check cache (1-second TTL)
    now = time.time()
    if _readiness_cache["expires_at"] > now and _readiness_cache["response"]:
        return _readiness_cache["response"]

    try:
        # Get startup status from app.state (populated during lifespan)
        startup_status = getattr(app.state, "startup_status", {})

        # Critical dependencies: MUST be ready for 200 status
        critical_deps = {
            "database": startup_status.get(
                "db", {"ready": False, "elapsed_ms": 0, "error": "Not initialized"}
            ),
            "cache": startup_status.get(
                "cache", {"ready": False, "elapsed_ms": 0, "error": "Not initialized"}
            ),
            "catalog": startup_status.get(
                "catalog", {"ready": False, "elapsed_ms": 0, "error": "Not initialized"}
            ),
        }

        # Optional dependencies: Can be unavailable without failing readiness
        optional_deps = {
            "redis": startup_status.get(
                "redis", {"ready": False, "elapsed_ms": 0, "error": "Not initialized"}
            ),
        }

        # Determine overall readiness: ALL critical deps MUST be ready
        failing_components = [
            comp for comp, status in critical_deps.items() if not status["ready"]
        ]

        overall_status = "ready" if len(failing_components) == 0 else "not_ready"

        # HTTP status code: 200 if ready, 503 if not ready
        status_code = 200 if overall_status == "ready" else 503

        response = JSONResponse(
            status_code=status_code,
            content={
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "critical_dependencies": critical_deps,
                "optional_dependencies": optional_deps,
                "failing_components": failing_components,
                "version": "1.0.0",
                "environment": config.APP_ENV,
            },
        )

        # Update cache with 1-second TTL
        _readiness_cache["response"] = response
        _readiness_cache["expires_at"] = now + 1.0

        return response

    except Exception as e:
        # Exception during readiness evaluation → 503 with error details
        logger.error(f"Readiness check exception: {e}")

        response = JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "critical_dependencies": {},
                "optional_dependencies": {},
                "failing_components": ["readiness_check_exception"],
                "error": str(e),
                "version": "1.0.0",
                "environment": config.APP_ENV,
            },
        )

        # Update cache with 1-second TTL (even for errors)
        _readiness_cache["response"] = response
        _readiness_cache["expires_at"] = now + 1.0

        return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=config.APP_PORT,
        reload=config.is_development(),
        timeout_keep_alive=30,  # 5xx Fail Fast: 30초 타임아웃
    )
