"""
Health Check Router - Phase VII-4: 9개 API 프로브 완성

시스템 상태 확인 엔드포인트 (Contract: spec_kit/api/openapi.yaml#/health)

프로브 목록 (9개):
1. /health - 전체 시스템 헬스
2. /health/live - Kubernetes liveness probe
3. /readyz - Kubernetes readiness probe
4. /health/redis - Redis 연결 상태
5. /health/catalog - 카탈로그 서비스 상태
6. /health/estimate - 견적 서비스 상태
7. /health/drawings - 도면 서비스 상태
8. /health/ai - AI 서비스 상태
9. /health/uptime - 서버 가동 시간

성능 목표:
- liveness: < 50ms
- readiness: < 100ms
- full health: < 500ms

NOTE: Supabase/DB 완전 폐기됨 - 파일 기반 저장소 사용
"""

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from kis_estimator_core.api.schemas.health import HealthResponse
from kis_estimator_core.services.cache import get_global_cache_metrics

logger = logging.getLogger(__name__)

router = APIRouter()

# 서버 시작 시간 (uptime 계산용)
_SERVER_START_TIME = time.time()

# 배포 버전 (디버깅용)
_CODE_VERSION = "2026.02.06-file-path-fix-v4"


def check_knowledge_files() -> Literal["ok", "degraded", "error"]:
    """Phase 0 지식 파일 5개 존재 확인"""
    try:
        knowledge_dir = Path(__file__).parent.parent.parent.parent.parent / "spec_kit" / "knowledge"
        required_files = [
            "1_breakers.json",
            "2_enclosures.json",
            "3_accessories.json",
            "4_calculations.json",
            "5_validation.json"
        ]

        missing_files = []
        for filename in required_files:
            file_path = knowledge_dir / filename
            if not file_path.exists():
                missing_files.append(filename)

        if not missing_files:
            return "ok"
        elif len(missing_files) < len(required_files):
            logger.warning(f"Some knowledge files missing: {missing_files}")
            return "degraded"
        else:
            logger.error("All knowledge files missing")
            return "error"
    except Exception as e:
        logger.error(f"Knowledge files check failed: {e}")
        return "error"


def check_memory_storage() -> Literal["ok", "degraded", "error"]:
    """AI 메모리 저장소 상태 확인 (파일 기반)"""
    try:
        memory_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "ai_memory"
        if memory_dir.exists():
            return "ok"
        else:
            logger.warning("AI memory directory not found")
            return "degraded"
    except Exception as e:
        logger.error(f"Memory storage check failed: {e}")
        return "error"


@router.get(
    "",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "시스템 정상",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-11-18T10:30:00+09:00",
                        "checks": {
                            "knowledge_files": "ok",
                            "memory_storage": "ok"
                        },
                        "uptime_seconds": 86400
                    }
                }
            }
        },
        503: {
            "description": "시스템 비정상",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-11-18T10:30:00+09:00",
                        "checks": {
                            "knowledge_files": "error",
                            "memory_storage": "ok"
                        },
                        "errors": ["Knowledge files missing"]
                    }
                }
            }
        }
    },
    summary="Health check",
    description="시스템 상태를 확인합니다 (Knowledge Files, Memory Storage)",
    operation_id="healthCheck",
)
async def health_check() -> JSONResponse:
    """
    시스템 상태 확인

    ## 확인 항목
    - Phase 0 knowledge files (5개)
    - AI memory storage (파일 기반)

    ## 응답
    - 200: healthy (모든 체크 ok)
    - 503: unhealthy (하나라도 error)
    """
    checks: dict[str, Literal["ok", "degraded", "error"]] = {}
    errors: list[str] = []

    # Knowledge files check
    kf_status = check_knowledge_files()
    checks["knowledge_files"] = kf_status
    if kf_status == "error":
        errors.append("Knowledge files missing")
    elif kf_status == "degraded":
        errors.append("Some knowledge files missing")

    # Memory storage check (파일 기반)
    ms_status = check_memory_storage()
    checks["memory_storage"] = ms_status
    if ms_status == "error":
        errors.append("Memory storage error")
    elif ms_status == "degraded":
        errors.append("Memory storage degraded")

    # Determine overall status
    if all(v == "ok" for v in checks.values()):
        overall_status = "healthy"
        http_status = status.HTTP_200_OK
    elif any(v == "error" for v in checks.values()):
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK

    response_data = HealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC),
        checks=checks,
        errors=errors if errors else None
    )

    response_content = response_data.model_dump(mode="json")
    response_content["code_version"] = _CODE_VERSION  # 배포 버전 확인용

    return JSONResponse(
        status_code=http_status,
        content=response_content
    )


# ============================================
# Probe 2: /health/live - Kubernetes Liveness
# ============================================
@router.get(
    "/live",
    summary="Liveness probe",
    description="Kubernetes liveness probe (< 50ms)",
    operation_id="livenessProbe",
)
async def liveness_probe() -> dict[str, Any]:
    """
    Liveness probe - 애플리케이션이 살아있는지 확인

    성능 목표: < 50ms
    용도: Kubernetes가 Pod를 재시작할지 결정
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get(
    "/livez",
    summary="Liveness probe (k8s convention)",
    description="Kubernetes liveness probe alias (/livez)",
    operation_id="livenessProbeZ",
)
async def liveness_probe_z() -> dict[str, Any]:
    """Alias for /live using Kubernetes /livez convention."""
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ============================================
# Probe 3: /readyz - Kubernetes Readiness
# ============================================
@router.get(
    "/readyz",
    summary="Readiness probe",
    description="Kubernetes readiness probe (< 100ms)",
    operation_id="readinessProbe",
)
async def readiness_probe() -> JSONResponse:
    """
    Readiness probe - 트래픽을 받을 준비가 되었는지 확인

    성능 목표: < 100ms
    용도: Kubernetes가 트래픽을 라우팅할지 결정
    """
    try:
        # 메모리 저장소 빠른 체크
        ms_status = check_memory_storage()
        is_ready = ms_status in ("ok", "degraded")

        if is_ready:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ready",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "reason": "Memory storage not available",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 4: /health/redis - Redis Health
# ============================================
@router.get(
    "/redis",
    summary="Redis health",
    description="Redis 연결 상태 확인",
    operation_id="redisHealth",
)
async def redis_health() -> JSONResponse:
    """Redis 연결 상태 확인"""
    try:
        # Redis 드라이버 연결 체크 시도
        from kis_estimator_core.infra.redis_driver import get_redis_client
        client = get_redis_client()

        if client:
            start_time = time.time()
            pong = await client.ping() if hasattr(client, 'ping') else True
            latency_ms = (time.time() - start_time) * 1000

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ok" if pong else "error",
                    "latency_ms": round(latency_ms, 2),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "disabled",
                    "message": "Redis not configured",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
    except ImportError:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "disabled",
                "message": "Redis driver not installed",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 5: /health/catalog - Catalog Service
# ============================================
@router.get(
    "/catalog",
    summary="Catalog health",
    description="카탈로그 서비스 및 캐시 상태 확인",
    operation_id="catalogHealth",
)
async def catalog_health() -> JSONResponse:
    """카탈로그 서비스 상태 및 캐시 메트릭"""
    try:
        cache_metrics = get_global_cache_metrics()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "cache": cache_metrics,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Catalog health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 6: /health/estimate - Estimate Service
# ============================================
@router.get(
    "/estimate",
    summary="Estimate health",
    description="견적 서비스 상태 확인",
    operation_id="estimateHealth",
)
async def estimate_health() -> JSONResponse:
    """견적 서비스 상태 확인"""
    try:
        # FIX-4 파이프라인 모듈 존재 확인
        from kis_estimator_core.engine import fix4_pipeline  # noqa: F401

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "pipeline": "FIX-4",
                "stages": ["enclosure", "breaker", "critic", "format", "cover"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except ImportError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": f"Pipeline module not available: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Estimate health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 7: /health/drawings - Drawings Service
# ============================================
@router.get(
    "/drawings",
    summary="Drawings health",
    description="도면 서비스 상태 확인",
    operation_id="drawingsHealth",
)
async def drawings_health() -> JSONResponse:
    """도면 서비스 상태 확인"""
    try:
        from kis_estimator_core.services.drawing_service import DrawingService  # noqa: F401

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "service": "DrawingService",
                "formats": ["single_line", "layout", "panel_schedule"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except ImportError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": f"Drawing service not available: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Drawings health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 8: /health/ai - AI Service
# ============================================
@router.get(
    "/ai",
    summary="AI health",
    description="AI 서비스 상태 확인",
    operation_id="aiHealth",
)
async def ai_health() -> JSONResponse:
    """AI 서비스 상태 확인"""
    try:
        # AI Chat 서비스 모듈 존재 확인
        from kis_estimator_core.services.estimate_parser_service import (
            EstimateParserService,  # noqa: F401
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "services": ["EstimateParserService", "AICatalogService"],
                "intents": ["estimate", "drawing", "email", "erp", "catalog", "help"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except ImportError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": f"AI service not available: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================
# Probe 9: /health/uptime - Server Uptime
# ============================================
@router.get(
    "/uptime",
    summary="Server uptime",
    description="서버 가동 시간 확인",
    operation_id="serverUptime",
)
async def server_uptime() -> dict[str, Any]:
    """서버 가동 시간 확인"""
    uptime_seconds = time.time() - _SERVER_START_TIME

    return {
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": _format_uptime(uptime_seconds),
        "started_at": datetime.fromtimestamp(_SERVER_START_TIME, tz=UTC).isoformat(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _format_uptime(seconds: float) -> str:
    """Uptime을 사람이 읽기 쉬운 형식으로 변환"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
