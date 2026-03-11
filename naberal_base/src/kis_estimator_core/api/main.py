"""
FastAPI Application Entry Point

Contract-First + Evidence-Gated + SSOT 기반 KIS Estimator API v2.0

Phase 1 구현:
- OpenAPI 3.1 스키마 연동 (spec_kit/api/openapi.yaml)
- Phase 0 지식 JSON 연계 (spec_kit/knowledge/*.json)
- 7가지 필수 검증 체크 연결
- 목업 절대 금지 (Zero-Mock)
- SSOT 전용 (core/ssot/** 기반)
"""

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from kis_estimator_core.api.routes import ai_chat, ai_manager, ai_sessions, assistant, auth, calendar, catalog, drawings, email, erp, estimates, health, learning, negotiation, prediction, public, quotes, vision
from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError

# Logging 설정
logging.basicConfig(
    level=logging.INFO if os.getenv("APP_DEBUG", "false").lower() != "true" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="NABERAL KIS Estimator API",
    version="2.0.0",
    description="""
    전기 패널 견적 AI 시스템 API (Contract-First + Evidence-Gated)

    ## 핵심 원칙
    - **Contract-First**: 계약이 구현보다 우선
    - **Evidence-Gated**: 모든 계산은 증거 생성 필수
    - **SSOT 전용**: core/ssot/** 기반 데이터 처리
    - **Zero-Mock**: 목업/가짜 데이터 절대 금지
    - **FIX-4 Pipeline**: 5단계 필수 (Enclosure → Breaker → Critic → Format → Cover)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_version="3.1.0"
)

# Rate Limiting 설정
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정
def _get_cors_origins() -> list[str]:
    """CORS 허용 오리진 목록 조회"""
    origins_str = os.getenv("CORS_ORIGINS", "")
    if not origins_str:
        # 개발 모드에서는 모든 오리진 허용 (Tauri 앱 지원)
        if os.getenv("APP_ENV", "development").lower() == "development":
            logger.warning("⚠️ CORS_ORIGINS 미설정 - 개발 모드: 모든 오리진 허용")
            return ["*"]  # Tauri의 tauri:// 스킴 지원을 위해 와일드카드 사용
        # 프로덕션에서는 와일드카드 금지, 명시적 설정 필요
        logger.error("❌ CORS_ORIGINS 환경변수가 설정되지 않았습니다. 프로덕션에서는 필수입니다.")
        return []  # 빈 목록 = 모든 CORS 요청 차단
    # 와일드카드 사용 금지 (프로덕션 환경)
    origins = [o.strip() for o in origins_str.split(",") if o.strip()]
    if "*" in origins and os.getenv("APP_ENV", "development").lower() != "development":
        logger.error("❌ 프로덕션 환경에서 CORS_ORIGINS에 '*'는 사용할 수 없습니다.")
        origins = [o for o in origins if o != "*"]
    return origins

# 개발 환경에서 credentials와 와일드카드 동시 사용을 위한 설정
_cors_origins = _get_cors_origins()
_allow_all = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _allow_all,  # 와일드카드 사용 시 credentials 비활성화
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

# 정적 파일 서빙 (outputs 디렉토리 - Excel/PDF 다운로드용)
outputs_dir = Path(__file__).parent.parent.parent.parent / "outputs"
if not outputs_dir.exists():
    outputs_dir.mkdir(parents=True, exist_ok=True)

# /outputs 경로 마운트
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")
# /v1/documents 경로도 동일한 디렉토리로 마운트 (document_service의 URL 패턴 지원)
app.mount("/v1/documents", StaticFiles(directory=str(outputs_dir)), name="documents")
logger.info(f"✅ Static files enabled: /outputs, /v1/documents -> {outputs_dir}")

# 라우터 등록
app.include_router(
    estimates.router,
    prefix="/v1/estimates",
    tags=["estimates"]
)

app.include_router(
    catalog.router,
    prefix="/v1/catalog",
    tags=["catalog"]
)

app.include_router(
    quotes.router,
    prefix="/v1/quotes",
    tags=["quotes"]
)

app.include_router(
    health.router,
    prefix="/v1/health",
    tags=["health"]
)

app.include_router(
    drawings.router,
    prefix="/v1/drawings",
    tags=["drawings"]
)

# AI Chat 라우터 (자연어 기반 통합 처리)
app.include_router(
    ai_chat.router,
    prefix="/v1/ai",
    tags=["ai-chat"]
)

# AI Manager 라우터 (탭 통합 제어 + 시각화)
app.include_router(
    ai_manager.router,
    prefix="/v1/ai-manager",
    tags=["ai-manager"]
)

# AI Sessions 라우터 (대화 세션 및 영구 메모리)
app.include_router(
    ai_sessions.router,
    tags=["ai-sessions"]
)

# ERP 라우터 (상품/거래처/전표 관리)
app.include_router(erp.router, prefix="/v1")  # router has prefix="/erp", final: /v1/erp

# Calendar 라우터 (일정 관리)
app.include_router(
    calendar.router,
    prefix="/v1",
    tags=["calendar"]
)

# Email 라우터 (이메일 발송)
app.include_router(
    email.router,
    prefix="/v1",
    tags=["email"]
)

# Auth 라우터 (인증/사용자 관리)
app.include_router(
    auth.router,
    prefix="/v1",
    tags=["auth"]
)

# Learning 라우터 (AI Self-Learning System - Phase XIII)
app.include_router(
    learning.router,
    prefix="/v1",
    tags=["ai-learning"]
)

# Vision 라우터 (도면/사진 → 자동 견적 - Phase XIV)
app.include_router(
    vision.router,
    prefix="/v1",
    tags=["vision-ai"]
)

# Prediction 라우터 (예측 분석 대시보드 - Phase XV)
app.include_router(
    prediction.router,
    prefix="/v1",
    tags=["prediction-analytics"]
)

# Assistant 라우터 (AI 업무 비서 - Phase XVI)
app.include_router(
    assistant.router,
    prefix="/v1",
    tags=["ai-assistant"]
)

# Negotiation 라우터 (AI 협상 어시스턴트 - Phase XVII)
app.include_router(
    negotiation.router,
    prefix="/v1",
    tags=["ai-negotiation"]
)

# Public 라우터 (비인증 공개 API - hkkor.com)
app.include_router(
    public.router,
    prefix="/v1/public",
    tags=["public"]
)

# RAG 라우터 (선택적 - chromadb 설치 시에만)
try:
    from kis_estimator_core.rag.api import router as rag_router
    app.include_router(rag_router)  # prefix already set in router (/v1/rag)
    logger.info("RAG API enabled")
except ImportError:
    logger.info("RAG API disabled (chromadb not installed)")


# 전역 예외 핸들러
@app.exception_handler(EstimatorError)
async def estimator_error_handler(request: Request, exc: EstimatorError) -> JSONResponse:
    """
    SSOT EstimatorError 전역 핸들러

    core/ssot/errors.py의 EstimatorError를 JSON 응답으로 변환
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # ErrorCode별 HTTP 상태 코드 매핑
    error_code = exc.payload.code
    if error_code == ErrorCode.E_VALIDATION.value or error_code == ErrorCode.E_VALIDATION_FAILED.value:
        status_code = status.HTTP_400_BAD_REQUEST
    elif error_code == ErrorCode.E_NOT_FOUND.value:
        status_code = status.HTTP_404_NOT_FOUND
    elif error_code.startswith("E_AUTH_"):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif error_code == ErrorCode.E_RBAC.value:
        status_code = status.HTTP_403_FORBIDDEN
    elif error_code == ErrorCode.E_REDIS_RATE.value:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS

    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    일반 예외 핸들러 (예상치 못한 오류)

    보안 고려사항:
    - 프로덕션에서는 내부 오류 상세 정보 노출 금지
    - 고유 에러 ID로 로그 추적 가능하게 함
    - 스택 트레이스는 서버 로그에만 기록
    """
    import uuid

    # 고유 에러 ID 생성 (로그 추적용)
    error_id = str(uuid.uuid4())[:8]

    # 서버 로그에만 상세 정보 기록 (에러 ID 포함)
    logger.error(f"[ERR-{error_id}] Unhandled exception: {exc}", exc_info=True)

    # 개발 모드에서만 상세 정보 포함
    is_development = os.getenv("APP_ENV", "development").lower() == "development"

    response_content = {
        "code": ErrorCode.E_INTERNAL.value,
        "message": "Internal server error",
        "hint": "예상치 못한 오류가 발생했습니다. 관리자에게 문의하세요.",
        "errorId": f"ERR-{error_id}",  # 추적용 ID만 노출
        "meta": {}
    }

    # 개발 모드에서만 상세 에러 정보 추가
    if is_development:
        response_content["debug"] = {
            "exception": type(exc).__name__,
            "detail": str(exc)[:200]  # 최대 200자로 제한
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content
    )


# OpenAPI 스키마 커스터마이징
def custom_openapi() -> dict[str, Any]:
    """
    OpenAPI 3.1 스키마 커스터마이징

    spec_kit/api/openapi.yaml과 일치하도록 수정
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.1.0"
    )

    # Security Schemes 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT 인증 (JWKS 검증)"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key 인증 (서비스 간 통신용)"
        }
    }

    # Global security 설정
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]

    # Servers 추가 (환경변수 기반)
    import os
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    openapi_schema["servers"] = [
        {
            "url": f"{api_base}/v1",
            "description": "Current server"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Startup/Shutdown 이벤트
@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 초기화
    """
    logger.info("🚀 KIS Estimator API v2.0 starting...")

    # Phase 0 지식 JSON 로드 확인
    knowledge_dir = Path(__file__).parent.parent.parent.parent / "spec_kit" / "knowledge"
    required_files = [
        "1_breakers.json",
        "2_enclosures.json",
        "3_accessories.json",
        "4_calculations.json",
        "5_validation.json"
    ]

    for filename in required_files:
        file_path = knowledge_dir / filename
        if not file_path.exists():
            logger.error(f"❌ Missing required knowledge file: {filename}")
            raise FileNotFoundError(f"Phase 0 지식 파일이 없습니다: {filename}")

    logger.info("✅ Phase 0 지식 파일 검증 완료 (5개)")

    # DB 연결 확인
    # NOTE: kis_estimator_core prefix 사용 (싱글톤 일관성)
    try:
        from kis_estimator_core.infra.db import get_db_instance
        db = get_db_instance()
        is_connected = await db.test_connection()

        if is_connected:
            logger.info("✅ Database connection established")
        else:
            logger.warning("⚠️ Database connection failed (will retry)")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization skipped: {e}")

    # 카탈로그 캐시 초기화 (JSON only, no Supabase)
    try:
        from kis_estimator_core.services.catalog_service import get_catalog_service

        catalog_service = get_catalog_service()
        catalog_service.initialize_cache()
        logger.info("✅ Catalog cache initialized from JSON")
    except Exception as e:
        logger.warning(f"⚠️ Catalog cache initialization failed: {e}")

    logger.info("🎯 KIS Estimator API v2.0 ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 시 정리
    """
    logger.info("🛑 KIS Estimator API v2.0 shutting down...")

    # DB 연결 종료
    # NOTE: kis_estimator_core prefix 사용 (싱글톤 일관성)
    try:
        from kis_estimator_core.infra.db import get_db_instance
        db = get_db_instance()
        await db.close()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.warning(f"⚠️ Database cleanup skipped: {e}")

    logger.info("👋 KIS Estimator API v2.0 stopped")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    API 루트 엔드포인트
    """
    return {
        "name": "NABERAL KIS Estimator API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/v1/health"
    }
