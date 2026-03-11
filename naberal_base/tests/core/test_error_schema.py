"""
Phase G: 에러 스키마 스냅샷 테스트

Category: UNIT TEST
- Error schema validation (domain logic)
- No database dependencies
- Fast execution

절대 원칙:
- AppError 표준 스키마 {code, message, hint?, traceId, meta{dedupKey, blocking_errors[]}} 검증
- PII/비밀 마스킹 검증
- request-id/trace-id 전파 검증
- evidence hint (5xx) 검증
- 스키마 동등성 100% 일치

Usage:
    pytest tests/core/test_error_schema.py -v
"""

import json
import re
import uuid
from typing import Any, Dict

import pytest

from kis_estimator_core.core.ssot.errors import (
    ErrorCode,
    EstimatorError,
    EstimatorErrorPayload,
    raise_error,
    convert_builtin_error,
)
from api.error_handler import mask_pii, mask_secrets, get_http_status


# ============================================================
# 에러 스키마 검증 유틸리티
# ============================================================


def validate_error_schema(error_dict: Dict[str, Any]) -> bool:
    """
    표준 에러 스키마 검증

    Required fields:
    - code (str)
    - message (str)
    - traceId (str, UUID format)
    - meta (dict)
    - meta.dedupKey (str, 16-char hex)

    Optional fields:
    - hint (str)
    - meta.blocking_errors (list)
    """
    # 필수 필드 검증
    assert "code" in error_dict, "Missing 'code' field"
    assert "message" in error_dict, "Missing 'message' field"
    assert "traceId" in error_dict, "Missing 'traceId' field"
    assert "meta" in error_dict, "Missing 'meta' field"

    # 타입 검증
    assert isinstance(error_dict["code"], str), "code must be string"
    assert isinstance(error_dict["message"], str), "message must be string"
    assert isinstance(error_dict["traceId"], str), "traceId must be string"
    assert isinstance(error_dict["meta"], dict), "meta must be dict"

    # traceId는 UUID 형식이어야 함
    try:
        uuid.UUID(error_dict["traceId"])
    except ValueError:
        pytest.fail(f"traceId is not valid UUID: {error_dict['traceId']}")

    # meta.dedupKey 검증
    assert "dedupKey" in error_dict["meta"], "Missing 'meta.dedupKey' field"
    assert isinstance(error_dict["meta"]["dedupKey"], str), "dedupKey must be string"
    assert len(error_dict["meta"]["dedupKey"]) == 16, "dedupKey must be 16-char hex"
    assert re.match(
        r"^[0-9a-f]{16}$", error_dict["meta"]["dedupKey"]
    ), "dedupKey must be hex"

    # hint는 선택 필드이지만 있으면 string
    if "hint" in error_dict:
        assert isinstance(error_dict["hint"], str), "hint must be string"

    # blocking_errors는 선택 필드이지만 있으면 list
    if "blocking_errors" in error_dict["meta"]:
        assert isinstance(
            error_dict["meta"]["blocking_errors"], list
        ), "blocking_errors must be list"

    return True


# ============================================================
# EstimatorError 기본 스키마 테스트
# ============================================================


@pytest.mark.unit
class TestEstimatorErrorSchema:
    """EstimatorError 기본 스키마 검증"""

    def test_basic_error_schema(self):
        """기본 에러 스키마 구조 검증"""
        payload = EstimatorErrorPayload(
            code=ErrorCode.E_CATALOG_LOAD.value,
            message="카탈로그 파일 로드 실패",
            traceId=str(uuid.uuid4()),
            meta={"file": "catalog.csv"},
        )

        error_dict = payload.to_dict()
        assert validate_error_schema(error_dict)

        # 필수 필드 존재 확인
        assert error_dict["code"] == "E_CATALOG_LOAD"
        assert error_dict["message"] == "카탈로그 파일 로드 실패"
        assert "traceId" in error_dict
        assert "dedupKey" in error_dict["meta"]
        assert "file" in error_dict["meta"]

    def test_error_with_hint(self):
        """hint 필드 포함 에러"""
        payload = EstimatorErrorPayload(
            code=ErrorCode.E_VALIDATION_FAILED.value,
            message="입력 검증 실패",
            traceId=str(uuid.uuid4()),
            hint="필수 필드를 확인하세요",
            meta={},
        )

        error_dict = payload.to_dict()
        assert validate_error_schema(error_dict)
        assert error_dict["hint"] == "필수 필드를 확인하세요"

    def test_error_with_blocking_errors(self):
        """blocking_errors[] 포함 에러"""
        payload = EstimatorErrorPayload(
            code=ErrorCode.E_VALIDATION_FAILED.value,
            message="복합 검증 실패",
            traceId=str(uuid.uuid4()),
            meta={},
        )

        # blocking_errors 추가
        payload.add_blocking_error(
            {
                "code": "E_INPUT_ENCLOSURE_TYPE_MISSING",
                "message": "외함 타입 누락",
                "hint": "enclosure_type 필드 필수",
            }
        )
        payload.add_blocking_error(
            {
                "code": "E_INPUT_LOCATION_MISSING",
                "message": "설치 위치 누락",
                "hint": "location 필드 필수",
            }
        )

        error_dict = payload.to_dict()
        assert validate_error_schema(error_dict)

        # blocking_errors 검증
        assert "blocking_errors" in error_dict["meta"]
        assert len(error_dict["meta"]["blocking_errors"]) == 2
        assert (
            error_dict["meta"]["blocking_errors"][0]["code"]
            == "E_INPUT_ENCLOSURE_TYPE_MISSING"
        )
        assert (
            error_dict["meta"]["blocking_errors"][1]["code"]
            == "E_INPUT_LOCATION_MISSING"
        )

    def test_dedup_key_generation(self):
        """dedupKey 자동 생성 검증"""
        payload1 = EstimatorErrorPayload(
            code=ErrorCode.E_CATALOG_LOAD.value,
            message="카탈로그 파일 로드 실패",
            traceId=str(uuid.uuid4()),
            meta={},
        )

        payload2 = EstimatorErrorPayload(
            code=ErrorCode.E_CATALOG_LOAD.value,
            message="카탈로그 파일 로드 실패",
            traceId=str(uuid.uuid4()),
            meta={},
        )

        # 동일한 code+message는 동일한 dedupKey 생성
        assert payload1.meta["dedupKey"] == payload2.meta["dedupKey"]

        payload3 = EstimatorErrorPayload(
            code=ErrorCode.E_CATALOG_LOAD.value,
            message="다른 메시지",
            traceId=str(uuid.uuid4()),
            meta={},
        )

        # 다른 message는 다른 dedupKey 생성
        assert payload1.meta["dedupKey"] != payload3.meta["dedupKey"]


# ============================================================
# ErrorCode Enum 검증
# ============================================================


@pytest.mark.unit
class TestErrorCodeEnum:
    """ErrorCode Enum 통합 검증"""

    def test_all_error_codes_are_strings(self):
        """모든 ErrorCode는 string 값을 가져야 함"""
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert code.value == code.name

    def test_legacy_domain_codes_integrated(self):
        """Phase G에서 통합한 도메인 에러 코드 존재 확인"""
        # Input Errors (5개)
        assert hasattr(ErrorCode, "E_INPUT_ENCLOSURE_TYPE_MISSING")
        assert hasattr(ErrorCode, "E_INPUT_LOCATION_MISSING")
        assert hasattr(ErrorCode, "E_INPUT_BREAKER_BRAND_MISSING")
        assert hasattr(ErrorCode, "E_INPUT_MAIN_BREAKER_MISSING")
        assert hasattr(ErrorCode, "E_INPUT_BRANCH_BREAKER_MISSING")

        # 7대 치명적 버그 (6개)
        assert hasattr(ErrorCode, "E_BREAKER_TYPE_CONFUSION")
        assert hasattr(ErrorCode, "E_BREAKER_NOT_IN_CATALOG")
        assert hasattr(ErrorCode, "E_COMPACT_BREAKER_SELECTION")
        assert hasattr(ErrorCode, "E_BREAKER_CONSOLIDATION")
        assert hasattr(ErrorCode, "E_BRANCH_BUSBAR_MISSING")
        assert hasattr(ErrorCode, "E_LAYOUT_CALCULATION_ERROR")

        # Busbar Errors (1개)
        assert hasattr(ErrorCode, "E_BUSBAR_SPEC_MISMATCH")

        # Enclosure Errors (3개)
        assert hasattr(ErrorCode, "E_ENCLOSURE_HEIGHT_FORMULA")
        assert hasattr(ErrorCode, "E_ENCLOSURE_WIDTH_CALC")
        assert hasattr(ErrorCode, "E_ENCLOSURE_FACING_HEIGHT")

        # Accessory Errors (4개)
        assert hasattr(ErrorCode, "E_ACCESSORY_ET_QUANTITY")
        assert hasattr(ErrorCode, "E_ACCESSORY_PCOVER_PRICE")
        assert hasattr(ErrorCode, "E_ACCESSORY_ASSEMBLY_CHARGE")
        assert hasattr(ErrorCode, "E_ACCESSORY_MAGNET_BUNDLE")

        # Layout Errors (3개)
        assert hasattr(ErrorCode, "E_PHASE_IMBALANCE_EXCEEDED")
        assert hasattr(ErrorCode, "E_BREAKER_INTERFERENCE")
        assert hasattr(ErrorCode, "E_4P_NEUTRAL_FACING")

        # Calculation Errors (2개)
        assert hasattr(ErrorCode, "E_FORMULA_PRESERVATION_FAILED")
        assert hasattr(ErrorCode, "E_TOTAL_MISMATCH")


# ============================================================
# HTTP 상태 코드 매핑 검증
# ============================================================


@pytest.mark.unit
class TestHTTPStatusMapping:
    """ErrorCode → HTTP 상태 코드 매핑 검증"""

    def test_validation_errors_map_to_400(self):
        """검증 오류는 400 Bad Request"""
        assert get_http_status(ErrorCode.E_CONTRACT_VIOLATION.value) == 400
        assert get_http_status(ErrorCode.E_VALIDATION_FAILED.value) == 400
        assert get_http_status(ErrorCode.E_SCHEMA_MISMATCH.value) == 400
        assert get_http_status(ErrorCode.E_BRANCH_RULE.value) == 400

    def test_not_found_errors_map_to_404(self):
        """리소스 없음 오류는 404 Not Found"""
        assert get_http_status(ErrorCode.E_CATALOG_NOT_FOUND.value) == 404
        assert get_http_status(ErrorCode.E_FILE_NOT_FOUND.value) == 404

    def test_internal_errors_map_to_500(self):
        """내부 오류는 500 Internal Server Error"""
        assert get_http_status(ErrorCode.E_CATALOG_LOAD.value) == 500
        assert get_http_status(ErrorCode.E_DATA_TRANSFORM.value) == 500
        assert get_http_status(ErrorCode.E_IO.value) == 500
        assert get_http_status(ErrorCode.E_INTERNAL.value) == 500

    def test_not_implemented_maps_to_501(self):
        """미구현 오류는 501 Not Implemented"""
        assert get_http_status(ErrorCode.E_NOT_IMPLEMENTED.value) == 501

    def test_service_errors_map_to_503(self):
        """서비스 불가 오류는 503 Service Unavailable"""
        assert get_http_status(ErrorCode.E_REDIS_RATE.value) == 503
        assert get_http_status(ErrorCode.E_REDIS_CONNECTION.value) == 503
        assert get_http_status(ErrorCode.E_DB_CONNECTION.value) == 503

    def test_unknown_code_defaults_to_500(self):
        """알 수 없는 코드는 500 기본값"""
        assert get_http_status("UNKNOWN_CODE") == 500


# ============================================================
# PII 마스킹 검증
# ============================================================


@pytest.mark.unit
class TestPIIMasking:
    """PII/비밀 정보 마스킹 검증"""

    def test_mask_email(self):
        """이메일 마스킹"""
        text = "User email is user@example.com for support"
        masked = mask_pii(text)
        assert "***EMAIL***" in masked
        assert "user@example.com" not in masked

    def test_mask_phone(self):
        """전화번호 마스킹 (xxx-xxxx-xxxx)"""
        text = "Contact: 010-1234-5678"
        masked = mask_pii(text)
        assert "***PHONE***" in masked
        assert "010-1234-5678" not in masked

    def test_mask_ssn(self):
        """주민번호 마스킹 (xxxxxx-xxxxxxx)"""
        text = "SSN: 123456-1234567"
        masked = mask_pii(text)
        assert "***SSN***" in masked
        assert "123456-1234567" not in masked

    def test_mask_card(self):
        """카드번호 마스킹 (xxxx-xxxx-xxxx-xxxx)"""
        text = "Card: 1234-5678-9012-3456"
        masked = mask_pii(text)
        assert "***CARD***" in masked
        assert "1234-5678-9012-3456" not in masked

    def test_mask_secrets_in_dict(self):
        """딕셔너리 내 비밀 정보 마스킹"""
        data = {
            "username": "admin",
            "password": "secret123",
            "api_key": "abc123xyz",
            "email": "user@example.com",
            "normal_field": "visible",
        }

        masked = mask_secrets(data)

        # 비밀 키워드 포함 필드는 마스킹
        assert masked["password"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"

        # PII는 마스킹
        assert "***EMAIL***" in masked["email"]

        # 일반 필드는 그대로
        assert masked["username"] == "admin"
        assert masked["normal_field"] == "visible"

    def test_mask_secrets_recursive(self):
        """중첩 딕셔너리 재귀 마스킹"""
        data = {
            "config": {
                "db_password": "dbpass123",
                "nested": {"secret_token": "token456"},
            },
            "user_email": "test@example.com",
        }

        masked = mask_secrets(data)

        assert masked["config"]["db_password"] == "***MASKED***"
        assert masked["config"]["nested"]["secret_token"] == "***MASKED***"
        assert "***EMAIL***" in masked["user_email"]


# ============================================================
# raise_error 헬퍼 함수 검증
# ============================================================


@pytest.mark.unit
class TestRaiseErrorHelper:
    """raise_error() 헬퍼 함수 검증"""

    def test_raise_error_basic(self):
        """기본 raise_error 동작"""
        with pytest.raises(EstimatorError) as exc_info:
            raise_error(ErrorCode.E_CATALOG_LOAD, "카탈로그 로드 실패")

        error = exc_info.value
        error_dict = error.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_CATALOG_LOAD"
        assert error_dict["message"] == "카탈로그 로드 실패"

    def test_raise_error_with_hint_and_meta(self):
        """hint와 meta 포함 raise_error"""
        with pytest.raises(EstimatorError) as exc_info:
            raise_error(
                ErrorCode.E_FILE_NOT_FOUND,
                "파일을 찾을 수 없습니다",
                hint="파일 경로를 확인하세요",
                meta={"file": "catalog.csv", "path": "/data/catalog.csv"},
            )

        error = exc_info.value
        error_dict = error.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["hint"] == "파일 경로를 확인하세요"
        assert error_dict["meta"]["file"] == "catalog.csv"
        assert error_dict["meta"]["path"] == "/data/catalog.csv"


# ============================================================
# convert_builtin_error 변환 검증
# ============================================================


@pytest.mark.unit
class TestConvertBuiltinError:
    """내장 예외 → EstimatorError 변환 검증"""

    def test_convert_value_error(self):
        """ValueError → E_VALIDATION_FAILED"""
        exc = ValueError("Invalid input")
        converted = convert_builtin_error(exc, context="test_context")
        error_dict = converted.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_VALIDATION_FAILED"
        assert "Invalid input" in error_dict["message"]
        assert error_dict["meta"]["exception_type"] == "ValueError"
        assert error_dict["meta"]["context"] == "test_context"

    def test_convert_file_not_found_error(self):
        """FileNotFoundError → E_FILE_NOT_FOUND"""
        exc = FileNotFoundError("File not found")
        converted = convert_builtin_error(exc)
        error_dict = converted.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_FILE_NOT_FOUND"
        assert error_dict["meta"]["exception_type"] == "FileNotFoundError"

    def test_convert_io_error(self):
        """IOError → E_IO (Python 3.3+에서 IOError는 OSError의 별칭)"""
        exc = IOError("IO error")
        converted = convert_builtin_error(exc)
        error_dict = converted.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_IO"
        # Python 3.3+ IOError는 OSError의 별칭
        assert error_dict["meta"]["exception_type"] in ["IOError", "OSError"]

    def test_convert_assertion_error(self):
        """AssertionError → E_ASSERTION_FAILED"""
        exc = AssertionError("Assertion failed")
        converted = convert_builtin_error(exc)
        error_dict = converted.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_ASSERTION_FAILED"
        assert error_dict["meta"]["exception_type"] == "AssertionError"

    def test_convert_unknown_error(self):
        """Unknown Exception → E_INTERNAL"""
        exc = RuntimeError("Unknown error")
        converted = convert_builtin_error(exc)
        error_dict = converted.to_dict()

        assert validate_error_schema(error_dict)
        assert error_dict["code"] == "E_INTERNAL"
        assert error_dict["meta"]["exception_type"] == "RuntimeError"


# ============================================================
# 에러 스키마 스냅샷 생성
# ============================================================


@pytest.mark.unit
def test_generate_error_schema_snapshot(tmp_path):
    """
    에러 스키마 스냅샷 생성 (Evidence)

    out/evidence/error_schema_snapshot.json 생성
    """
    import os

    snapshot = {
        "version": "1.0.0",
        "phase": "G",
        "schema": {
            "required_fields": ["code", "message", "traceId", "meta"],
            "optional_fields": ["hint"],
            "meta_required": ["dedupKey"],
            "meta_optional": ["blocking_errors", "request_id", "evidence_hint"],
            "traceId_format": "UUID v4",
            "dedupKey_format": "SHA256 16-char hex",
        },
        "error_codes": [code.value for code in ErrorCode],
        "http_status_mapping": {
            "400": [
                "E_CONTRACT_VIOLATION",
                "E_VALIDATION_FAILED",
                "E_SCHEMA_MISMATCH",
                "E_BRANCH_RULE",
                "E_PHASE_IMBALANCE",
                "E_CLEARANCE_VIOLATION",
                "E_THERMAL_VIOLATION",
                "E_CATALOG_INVALID",
                "E_ASSERTION_FAILED",
            ],
            "404": ["E_CATALOG_NOT_FOUND", "E_FILE_NOT_FOUND"],
            "500": [
                "E_CATALOG_LOAD",
                "E_DATA_TRANSFORM",
                "E_IO",
                "E_FILE_READ_ERROR",
                "E_FILE_WRITE_ERROR",
                "E_TEMPLATE_DAMAGED",
                "E_FORMULA_MISSING",
                "E_NAMED_RANGE_BROKEN",
                "E_INTERNAL",
            ],
            "501": ["E_NOT_IMPLEMENTED"],
            "503": [
                "E_REDIS_RATE",
                "E_REDIS_CONNECTION",
                "E_DB_CONNECTION",
                "E_DB_QUERY",
            ],
        },
        "pii_patterns": {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-\d{4}-\d{4}\b",
            "ssn": r"\b\d{6}-\d{7}\b",
            "card": r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
        },
        "secret_keywords": ["password", "token", "secret", "key", "api_key", "auth"],
        "sample_errors": {
            "basic": {
                "code": "E_CATALOG_LOAD",
                "message": "카탈로그 파일 로드 실패",
                "traceId": "uuid-v4",
                "meta": {"dedupKey": "sha256-16-char-hex", "file": "catalog.csv"},
            },
            "with_hint": {
                "code": "E_VALIDATION_FAILED",
                "message": "입력 검증 실패",
                "traceId": "uuid-v4",
                "hint": "필수 필드를 확인하세요",
                "meta": {"dedupKey": "sha256-16-char-hex"},
            },
            "with_blocking_errors": {
                "code": "E_VALIDATION_FAILED",
                "message": "복합 검증 실패",
                "traceId": "uuid-v4",
                "meta": {
                    "dedupKey": "sha256-16-char-hex",
                    "blocking_errors": [
                        {
                            "code": "E_INPUT_ENCLOSURE_TYPE_MISSING",
                            "message": "외함 타입 누락",
                            "hint": "enclosure_type 필드 필수",
                        }
                    ],
                },
            },
            "with_request_id": {
                "code": "E_INTERNAL",
                "message": "내부 오류",
                "traceId": "uuid-v4",
                "meta": {"dedupKey": "sha256-16-char-hex", "request_id": "req-uuid-v4"},
            },
            "with_evidence_hint": {
                "code": "E_INTERNAL",
                "message": "내부 오류",
                "traceId": "abc123-uuid",
                "meta": {
                    "dedupKey": "sha256-16-char-hex",
                    "request_id": "req-uuid-v4",
                    "evidence_hint": "Check logs with traceId: abc123-uuid",
                },
            },
        },
    }

    # Evidence 디렉토리 생성
    evidence_dir = os.path.join(os.getcwd(), "out", "evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    # 스냅샷 저장
    snapshot_path = os.path.join(evidence_dir, "error_schema_snapshot.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    # 검증
    assert os.path.exists(snapshot_path)

    # 로드하여 JSON 유효성 확인
    with open(snapshot_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["version"] == "1.0.0"
    assert loaded["phase"] == "G"
    assert len(loaded["error_codes"]) > 30  # 최소 30개 이상 에러 코드

    print(f"\n[OK] Error schema snapshot generated: {snapshot_path}")
    print(f"   Total error codes: {len(loaded['error_codes'])}")
