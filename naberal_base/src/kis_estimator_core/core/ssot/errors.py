"""
SSOT Error Schema - 표준 오류 스키마 및 코드 정의

절대 원칙:
- 모든 도메인 오류는 EstimatorError로 통일
- 표준 페이로드: {code, message, hint?, traceId, meta{dedupKey}}
- 매직 리터럴 금지 → ErrorCode Enum 사용
- 내장 예외(Exception/ValueError/RuntimeError) 사용 금지

Usage:
    from kis_estimator_core.core.ssot.errors import raise_error, ErrorCode

    # 표준 오류 발생
    raise_error(
        ErrorCode.E_CATALOG_LOAD,
        "카탈로그 파일 로드 실패",
        hint="파일 경로 및 권한 확인 필요",
        meta={"file": "catalog.csv", "line": 42}
    )
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NoReturn

# ============================================================
# Role Enum - 사용자 역할 정의 (SSOT) - Phase XI
# ============================================================


class Role(str, Enum):
    """User roles for RBAC (Phase XI)"""

    APPROVER = "APPROVER"  # Can approve quotes
    USER = "USER"  # Can create and view quotes (cannot approve)
    ADMIN = "ADMIN"  # Full access (future use)


# ============================================================
# ErrorCode Enum - 표준 오류 코드 정의 (SSOT)
# ============================================================


class ErrorCode(str, Enum):
    """표준 오류 코드 (절대 하드코딩 금지)"""

    # 카탈로그/데이터 로드
    E_CATALOG_LOAD = "E_CATALOG_LOAD"
    E_DATA_TRANSFORM = "E_DATA_TRANSFORM"
    E_CATALOG_NOT_FOUND = "E_CATALOG_NOT_FOUND"
    E_CATALOG_INVALID = "E_CATALOG_INVALID"

    # 비즈니스 규칙 위반
    E_BRANCH_RULE = "E_BRANCH_RULE"
    E_PHASE_IMBALANCE = "E_PHASE_IMBALANCE"
    E_CLEARANCE_VIOLATION = "E_CLEARANCE_VIOLATION"
    E_THERMAL_VIOLATION = "E_THERMAL_VIOLATION"

    # 계약/검증 위반
    E_CONTRACT_VIOLATION = "E_CONTRACT_VIOLATION"
    E_VALIDATION = "E_VALIDATION"  # Phase XI: Added for generic validation errors
    E_VALIDATION_FAILED = "E_VALIDATION_FAILED"
    E_SCHEMA_MISMATCH = "E_SCHEMA_MISMATCH"
    E_NOT_FOUND = "E_NOT_FOUND"  # Phase XI: Added for generic not found errors
    E_CONFLICT = "E_CONFLICT"  # Phase XI: Added for state conflicts
    E_PDF_POLICY = "E_PDF_POLICY"  # Phase XII: PDF standard policy violation (422)

    # 인증/인가 오류 (Phase XIV: 6-Axis Unification)
    E_AUTH_MISSING = "E_AUTH_MISSING"  # 401: Authorization header missing
    E_AUTH_INVALID = "E_AUTH_INVALID"  # 401: Invalid JWT/credentials
    E_AUTH_EXPIRED = "E_AUTH_EXPIRED"  # 401: Token expired
    E_RBAC = "E_RBAC"  # 403: Insufficient permissions (Role-Based Access Control)

    # I/O 오류
    E_IO = "E_IO"
    E_FILE_NOT_FOUND = "E_FILE_NOT_FOUND"
    E_FILE_READ_ERROR = "E_FILE_READ_ERROR"
    E_FILE_WRITE_ERROR = "E_FILE_WRITE_ERROR"

    # 인프라 오류
    E_REDIS_RATE = "E_REDIS_RATE"
    E_REDIS_CONNECTION = "E_REDIS_CONNECTION"
    E_DB_CONNECTION = "E_DB_CONNECTION"
    E_DB_QUERY = "E_DB_QUERY"

    # 템플릿/포맷 오류
    E_TEMPLATE_DAMAGED = "E_TEMPLATE_DAMAGED"
    E_FORMULA_MISSING = "E_FORMULA_MISSING"
    E_NAMED_RANGE_BROKEN = "E_NAMED_RANGE_BROKEN"

    # 내부 오류
    E_INTERNAL = "E_INTERNAL"
    E_NOT_IMPLEMENTED = "E_NOT_IMPLEMENTED"
    E_ASSERTION_FAILED = "E_ASSERTION_FAILED"

    # ============================================================
    # 도메인별 에러 코드 (Phase G: SSOT 통합)
    # ============================================================

    # Input Errors (INP-001 ~ INP-005)
    E_INPUT_ENCLOSURE_TYPE_MISSING = "E_INPUT_ENCLOSURE_TYPE_MISSING"
    E_INPUT_LOCATION_MISSING = "E_INPUT_LOCATION_MISSING"
    E_INPUT_BREAKER_BRAND_MISSING = "E_INPUT_BREAKER_BRAND_MISSING"
    E_INPUT_MAIN_BREAKER_MISSING = "E_INPUT_MAIN_BREAKER_MISSING"
    E_INPUT_BRANCH_BREAKER_MISSING = "E_INPUT_BRANCH_BREAKER_MISSING"

    # 7대 치명적 버그 (BUG-001 ~ BUG-007)
    E_BREAKER_TYPE_CONFUSION = "E_BREAKER_TYPE_CONFUSION"  # BUG-001: MCCB/ELB 구분
    E_BREAKER_NOT_IN_CATALOG = "E_BREAKER_NOT_IN_CATALOG"  # BUG-002
    E_COMPACT_BREAKER_SELECTION = "E_COMPACT_BREAKER_SELECTION"  # BUG-003/004
    E_BREAKER_CONSOLIDATION = "E_BREAKER_CONSOLIDATION"  # BUG-005
    E_BRANCH_BUSBAR_MISSING = "E_BRANCH_BUSBAR_MISSING"  # BUG-006
    E_LAYOUT_CALCULATION_ERROR = "E_LAYOUT_CALCULATION_ERROR"  # BUG-007

    # Busbar Errors (BUS-001 ~ BUS-004)
    E_BUSBAR_SPEC_MISMATCH = "E_BUSBAR_SPEC_MISMATCH"

    # Enclosure Errors (ENC-001 ~ ENC-003)
    E_ENCLOSURE_HEIGHT_FORMULA = "E_ENCLOSURE_HEIGHT_FORMULA"
    E_ENCLOSURE_WIDTH_CALC = "E_ENCLOSURE_WIDTH_CALC"
    E_ENCLOSURE_FACING_HEIGHT = "E_ENCLOSURE_FACING_HEIGHT"

    # Accessory Errors (ACC-001 ~ ACC-004)
    E_ACCESSORY_ET_QUANTITY = "E_ACCESSORY_ET_QUANTITY"
    E_ACCESSORY_PCOVER_PRICE = "E_ACCESSORY_PCOVER_PRICE"
    E_ACCESSORY_ASSEMBLY_CHARGE = "E_ACCESSORY_ASSEMBLY_CHARGE"
    E_ACCESSORY_MAGNET_BUNDLE = "E_ACCESSORY_MAGNET_BUNDLE"

    # Layout Errors (LAY-001 ~ LAY-004)
    E_PHASE_IMBALANCE_EXCEEDED = "E_PHASE_IMBALANCE_EXCEEDED"  # LAY-001
    E_BREAKER_INTERFERENCE = "E_BREAKER_INTERFERENCE"  # LAY-002
    E_4P_NEUTRAL_FACING = "E_4P_NEUTRAL_FACING"  # LAY-004

    # Calculation Errors (CAL-001 ~ CAL-002)
    E_FORMULA_PRESERVATION_FAILED = "E_FORMULA_PRESERVATION_FAILED"
    E_TOTAL_MISMATCH = "E_TOTAL_MISMATCH"

    # Verb Errors (VERB-001 ~ VERB-002, I-3.3)
    VALIDATION_VERB_001 = "VALIDATION_VERB_001"  # Verb params 검증 실패
    VERB_002 = "VERB_002"  # 미등록 verb_name


# ============================================================
# EstimatorErrorPayload - 표준 오류 페이로드
# ============================================================


@dataclass
class EstimatorErrorPayload:
    """
    표준 오류 페이로드 (Contract-First)

    필수 필드:
    - code: ErrorCode (Enum 강제)
    - message: 사용자 친화적 오류 메시지
    - traceId: UUID v4 (전역 추적용)
    - meta.dedupKey: SHA256 (중복 제거용)

    선택 필드:
    - hint: 해결 방법 제안
    - meta: 추가 컨텍스트 (file, line, context 등)
    - meta.blocking_errors: 하위 차단 오류 리스트 (Phase G)
    """

    code: str  # ErrorCode.value
    message: str
    traceId: str
    meta: dict[str, Any] = field(default_factory=dict)
    hint: str | None = None

    def __post_init__(self):
        """dedupKey 자동 생성 (code + message 기반)"""
        if "dedupKey" not in self.meta:
            dedup_input = f"{self.code}:{self.message}"
            self.meta["dedupKey"] = hashlib.sha256(
                dedup_input.encode("utf-8")
            ).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        result = {
            "code": self.code,
            "message": self.message,
            "traceId": self.traceId,
            "meta": self.meta,
        }
        if self.hint:
            result["hint"] = self.hint
        return result

    def add_blocking_error(self, error_dict: dict[str, Any]) -> None:
        """
        Blocking error 추가 (Phase G)

        Args:
            error_dict: 차단 오류 딕셔너리 (code, message, hint 포함)
        """
        if "blocking_errors" not in self.meta:
            self.meta["blocking_errors"] = []
        self.meta["blocking_errors"].append(error_dict)


# ============================================================
# EstimatorError - 표준 예외 클래스
# ============================================================


class EstimatorError(Exception):
    """
    표준 도메인 예외 (내장 예외 사용 금지)

    Usage:
        raise EstimatorError(payload)
    """

    def __init__(self, payload: EstimatorErrorPayload):
        self.payload = payload
        super().__init__(payload.message)

    def to_dict(self) -> dict[str, Any]:
        """JSON 응답용 딕셔너리"""
        return self.payload.to_dict()


# ============================================================
# raise_error - 표준 오류 발생 함수 (SSOT)
# ============================================================


def raise_error(
    code: ErrorCode,
    message: str,
    *,
    hint: str | None = None,
    meta: dict[str, Any] | None = None,
) -> NoReturn:
    """
    표준 오류 발생 (EstimatorError)

    Args:
        code: ErrorCode (Enum from errors.py OR dataclass from error_codes.py)
        message: 사용자 친화적 오류 메시지
        hint: 해결 방법 제안 (선택)
        meta: 추가 컨텍스트 (file, line, context 등)

    Raises:
        EstimatorError: 표준 페이로드와 함께 발생

    Example:
        raise_error(
            ErrorCode.E_CATALOG_LOAD,
            "카탈로그 파일 로드 실패",
            hint="파일 경로 및 권한 확인 필요",
            meta={"file": "catalog.csv", "line": 42}
        )
    """
    trace_id = str(uuid.uuid4())

    # Handle both ErrorCode Enum (has .value) and dataclass (has .code)
    if isinstance(code, str):
        code_str = code
    elif hasattr(code, "value"):
        # Enum from errors.py
        code_str = code.value
    elif hasattr(code, "code"):
        # dataclass from error_codes.py
        code_str = code.code
    else:
        code_str = str(code)

    payload = EstimatorErrorPayload(
        code=code_str,
        message=message,
        traceId=trace_id,
        hint=hint,
        meta=meta or {},
    )
    raise EstimatorError(payload)


# ============================================================
# 내장 예외 변환 유틸리티
# ============================================================


def convert_builtin_error(
    exc: Exception, *, context: str | None = None
) -> EstimatorError:
    """
    내장 예외 → EstimatorError 변환 (최소 정보만 노출)

    Args:
        exc: 원본 내장 예외
        context: 추가 컨텍스트 (선택)

    Returns:
        EstimatorError: 표준 오류로 변환
    """
    trace_id = str(uuid.uuid4())

    # 예외 타입별 매핑
    if isinstance(exc, ValueError):
        code = ErrorCode.E_VALIDATION_FAILED
    elif isinstance(exc, FileNotFoundError):
        code = ErrorCode.E_FILE_NOT_FOUND
    elif isinstance(exc, IOError):
        code = ErrorCode.E_IO
    elif isinstance(exc, AssertionError):
        code = ErrorCode.E_ASSERTION_FAILED
    else:
        code = ErrorCode.E_INTERNAL

    payload = EstimatorErrorPayload(
        code=code.value,
        message=str(exc) or "내부 오류 발생",
        traceId=trace_id,
        hint="시스템 관리자에게 문의하세요",
        meta={
            "exception_type": type(exc).__name__,
            "context": context or "unknown",
        },
    )

    return EstimatorError(payload)
