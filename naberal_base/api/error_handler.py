"""
FastAPI Error Handler - 표준 오류 응답 미들웨어 (Phase G: Logging + Masking)

절대 원칙:
- EstimatorError → 표준 JSON 응답 (code, message, hint?, traceId, meta{dedupKey,blocking_errors[]})
- 내장 예외 → E_INTERNAL 변환 (최소 정보만 노출)
- HTTP 상태 코드 매핑 (ErrorCode → status_code)
- PII/비밀 정보 마스킹 (Phase G)
- request-id/trace-id 전파 (Phase G)

Usage:
    from api.error_handler import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)
"""

import logging
import re
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kis_estimator_core.core.ssot.errors import (
    EstimatorError,
    ErrorCode,
    convert_builtin_error,
)

# ============================================================
# Logging Configuration (Phase G)
# ============================================================

logger = logging.getLogger("kis_estimator.error_handler")

# PII Masking Patterns
PII_PATTERNS = [
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "***EMAIL***",
    ),  # Email
    (re.compile(r"\b\d{3}-\d{4}-\d{4}\b"), "***PHONE***"),  # Phone (xxx-xxxx-xxxx)
    (re.compile(r"\b\d{6}-\d{7}\b"), "***SSN***"),  # SSN (xxxxxx-xxxxxxx)
    (
        re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b"),
        "***CARD***",
    ),  # Card (xxxx-xxxx-xxxx-xxxx)
]

# Secret Keywords to Mask
SECRET_KEYWORDS = ["password", "token", "secret", "key", "api_key", "auth"]


def mask_pii(text: str) -> str:
    """
    PII 정보 마스킹 (Phase G)

    Args:
        text: 원본 텍스트

    Returns:
        마스킹된 텍스트
    """
    masked = text
    for pattern, replacement in PII_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def mask_secrets(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감 정보 키 마스킹 (Phase G)

    Args:
        data: 원본 딕셔너리

    Returns:
        마스킹된 딕셔너리
    """
    masked = {}
    for key, value in data.items():
        if any(keyword in key.lower() for keyword in SECRET_KEYWORDS):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_secrets(value)
        elif isinstance(value, str):
            masked[key] = mask_pii(value)
        else:
            masked[key] = value
    return masked


# ============================================================
# HTTP 상태 코드 매핑 (ErrorCode → status_code)
# ============================================================

ERROR_CODE_TO_HTTP_STATUS = {
    # 400 Bad Request
    ErrorCode.E_CONTRACT_VIOLATION: 400,
    ErrorCode.E_VALIDATION_FAILED: 400,
    ErrorCode.E_SCHEMA_MISMATCH: 400,
    ErrorCode.E_BRANCH_RULE: 400,
    ErrorCode.E_PHASE_IMBALANCE: 400,
    ErrorCode.E_CLEARANCE_VIOLATION: 400,
    ErrorCode.E_THERMAL_VIOLATION: 400,
    ErrorCode.E_CATALOG_INVALID: 400,
    ErrorCode.E_ASSERTION_FAILED: 400,
    # 401 Unauthorized (Phase XIV: 6-Axis Unification)
    ErrorCode.E_AUTH_MISSING: 401,
    ErrorCode.E_AUTH_INVALID: 401,
    ErrorCode.E_AUTH_EXPIRED: 401,
    # 403 Forbidden (Phase XIV: RBAC)
    ErrorCode.E_RBAC: 403,
    # 404 Not Found
    ErrorCode.E_CATALOG_NOT_FOUND: 404,
    ErrorCode.E_FILE_NOT_FOUND: 404,
    ErrorCode.E_NOT_FOUND: 404,  # Phase XIV: Generic not found
    # 409 Conflict (Phase XIV: State conflicts)
    ErrorCode.E_CONFLICT: 409,
    # 422 Unprocessable Entity (Phase XIV: Semantic validation)
    ErrorCode.E_VALIDATION: 422,  # Generic validation (semantic, not syntactic)
    ErrorCode.E_PDF_POLICY: 422,  # PDF standard policy violation
    # 500 Internal Server Error
    ErrorCode.E_CATALOG_LOAD: 500,
    ErrorCode.E_DATA_TRANSFORM: 500,
    ErrorCode.E_IO: 500,
    ErrorCode.E_FILE_READ_ERROR: 500,
    ErrorCode.E_FILE_WRITE_ERROR: 500,
    ErrorCode.E_TEMPLATE_DAMAGED: 500,
    ErrorCode.E_FORMULA_MISSING: 500,
    ErrorCode.E_NAMED_RANGE_BROKEN: 500,
    ErrorCode.E_INTERNAL: 500,
    ErrorCode.E_NOT_IMPLEMENTED: 501,
    # 503 Service Unavailable
    ErrorCode.E_REDIS_RATE: 503,
    ErrorCode.E_REDIS_CONNECTION: 503,
    ErrorCode.E_DB_CONNECTION: 503,
    ErrorCode.E_DB_QUERY: 503,
}


def get_http_status(code_str: str) -> int:
    """ErrorCode → HTTP 상태 코드 변환"""
    try:
        code_enum = ErrorCode(code_str)
        return ERROR_CODE_TO_HTTP_STATUS.get(code_enum, 500)
    except ValueError:
        return 500


# ============================================================
# EstimatorError 핸들러
# ============================================================


async def estimator_error_handler(
    request: Request, exc: EstimatorError
) -> JSONResponse:
    """
    EstimatorError → 표준 JSON 응답 (Phase G: Logging + Masking)

    응답 형식:
    {
        "code": "E_CATALOG_LOAD",
        "message": "카탈로그 파일 로드 실패",
        "hint": "파일 경로 및 권한 확인 필요",  // optional
        "traceId": "uuid-v4",
        "meta": {
            "dedupKey": "sha256-16",
            "blocking_errors": [],  // Phase G
            "file": "catalog.csv",
            "line": 42
        }
    }
    """
    payload = exc.to_dict()
    status_code = get_http_status(payload["code"])

    # Phase G: request-id 전파
    request_id = request.headers.get("x-request-id", payload.get("traceId", "unknown"))
    payload["meta"]["request_id"] = request_id

    # Phase G: Evidence hint 추가
    if status_code >= 500:
        payload["meta"][
            "evidence_hint"
        ] = f"Check logs with traceId: {payload['traceId']}"

    # Phase G: 로깅 (PII 마스킹 적용)
    logger.error(
        f"EstimatorError [{payload['code']}]: {mask_pii(payload['message'])}",
        extra={
            "trace_id": payload["traceId"],
            "request_id": request_id,
            "status_code": status_code,
            "path": str(request.url),
            "method": request.method,
            "error_code": payload["code"],
        },
    )

    return JSONResponse(
        status_code=status_code,
        content=payload,
    )


# ============================================================
# 내장 예외 핸들러
# ============================================================


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    내장 예외 → E_INTERNAL 변환 (최소 정보만 노출)

    보안 원칙:
    - 상세 스택 트레이스 노출 금지
    - 예외 타입만 meta.exception_type에 기록
    - traceId로 내부 로그 추적 가능
    """
    # 내장 예외 → EstimatorError 변환
    converted = convert_builtin_error(exc, context=str(request.url))
    payload = converted.to_dict()
    status_code = get_http_status(payload["code"])

    # Phase G: request-id 전파
    request_id = request.headers.get("x-request-id", payload.get("traceId", "unknown"))
    payload["meta"]["request_id"] = request_id

    # Phase G: Evidence hint 추가
    if status_code >= 500:
        payload["meta"][
            "evidence_hint"
        ] = f"Check logs with traceId: {payload['traceId']}"

    # Phase G: 로깅 (PII 마스킹 적용)
    logger.error(
        f"UnhandledException [{payload.get('meta', {}).get('exception_type', 'Unknown')}]: {mask_pii(payload['message'])}",
        extra={
            "trace_id": payload["traceId"],
            "request_id": request_id,
            "status_code": status_code,
            "path": str(request.url),
            "method": request.method,
            "error_code": payload["code"],
            "exception_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content=payload,
    )


# ============================================================
# Starlette HTTPException 핸들러
# ============================================================


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Starlette HTTPException → 표준 JSON 응답 (Phase G: Logging + Masking)

    예: 404 Not Found, 422 Unprocessable Entity 등

    I-3.4: HTTPException with dict detail support
    - detail이 dict인 경우: custom error structure 그대로 사용
    - detail이 string인 경우: 기존 로직 유지 (HTTP_{status_code} 래핑)
    """
    import uuid

    trace_id = str(uuid.uuid4())
    request_id = request.headers.get("x-request-id", trace_id)

    # I-3.4: Check if detail is a dict (custom error structure)
    if isinstance(exc.detail, dict):
        # Use custom error structure as-is
        payload = exc.detail.copy()

        # Add traceId and meta if not present
        if "traceId" not in payload:
            payload["traceId"] = trace_id
        if "meta" not in payload:
            payload["meta"] = {}

        # Add request_id to meta
        payload["meta"]["request_id"] = request_id
        payload["meta"]["url"] = str(request.url)

        # Add dedupKey if not present
        if "dedupKey" not in payload.get("meta", {}):
            payload["meta"]["dedupKey"] = payload.get("code", f"http-{exc.status_code}")
    else:
        # Standard string detail - wrap in standard structure
        payload = {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail or "HTTP 오류",
            "traceId": trace_id,
            "meta": {
                "dedupKey": f"http-{exc.status_code}",
                "url": str(request.url),
                "request_id": request_id,
            },
        }

    # Phase G: Evidence hint 추가 (5xx 오류 시)
    if exc.status_code >= 500:
        payload["meta"]["evidence_hint"] = f"Check logs with traceId: {trace_id}"

    # Phase G: 로깅 (4xx는 warning, 5xx는 error)
    log_level = logger.error if exc.status_code >= 500 else logger.warning

    # I-3.4: Extract message for logging (handle dict detail)
    log_message = payload.get("message", str(exc.detail or "HTTP 오류"))

    log_level(
        f"HTTPException [{exc.status_code}]: {mask_pii(log_message)}",
        extra={
            "trace_id": trace_id,
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "error_code": payload.get("code", f"HTTP_{exc.status_code}"),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
    )


# ============================================================
# FastAPI 앱 등록
# ============================================================


def register_error_handlers(app: FastAPI) -> None:
    """
    FastAPI 앱에 오류 핸들러 등록

    Usage:
        from api.error_handler import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)
    """
    app.add_exception_handler(EstimatorError, estimator_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
