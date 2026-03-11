"""
SSOT Error Schema Guard Tests - 표준 오류 스키마 필드 검증

목표:
- raise_error() 직후 JSON 직렬화 5요소 존재 확인
- 내장 예외 변환 테스트 (ValueError → E_VALIDATION_FAILED)
- dedupKey 자동 생성 검증
- traceId UUID v4 형식 검증
"""

import pytest
import uuid
from kis_estimator_core.core.ssot.errors import (
    raise_error,
    ErrorCode,
    EstimatorError,
    EstimatorErrorPayload,
    convert_builtin_error,
)


def test_01_raise_error_basic():
    """Test 1: raise_error() → EstimatorError with full payload"""
    with pytest.raises(EstimatorError) as exc_info:
        raise_error(
            ErrorCode.E_CATALOG_LOAD,
            "카탈로그 파일 로드 실패",
            hint="파일 경로 및 권한 확인 필요",
            meta={"file": "catalog.csv", "line": 42},
        )

    error = exc_info.value
    payload = error.to_dict()

    # 필수 필드 5요소 검증
    assert "code" in payload
    assert "message" in payload
    assert "traceId" in payload
    assert "meta" in payload
    assert "hint" in payload

    # 값 검증
    assert payload["code"] == "E_CATALOG_LOAD"
    assert payload["message"] == "카탈로그 파일 로드 실패"
    assert payload["hint"] == "파일 경로 및 권한 확인 필요"
    assert payload["meta"]["file"] == "catalog.csv"
    assert payload["meta"]["line"] == 42

    # dedupKey 자동 생성 검증
    assert "dedupKey" in payload["meta"]
    assert len(payload["meta"]["dedupKey"]) == 16  # SHA256 16자

    # traceId UUID v4 형식 검증
    try:
        uuid_obj = uuid.UUID(payload["traceId"], version=4)
        assert uuid_obj.version == 4
    except ValueError:
        pytest.fail("traceId is not a valid UUID v4")


def test_02_raise_error_minimal():
    """Test 2: raise_error() 최소 필드만 (hint, meta 없음)"""
    with pytest.raises(EstimatorError) as exc_info:
        raise_error(ErrorCode.E_INTERNAL, "내부 오류 발생")

    error = exc_info.value
    payload = error.to_dict()

    # 필수 필드만 검증
    assert payload["code"] == "E_INTERNAL"
    assert payload["message"] == "내부 오류 발생"
    assert "traceId" in payload
    assert "meta" in payload

    # hint는 선택 필드이므로 없을 수 있음
    # dedupKey는 자동 생성됨
    assert "dedupKey" in payload["meta"]


def test_03_dedup_key_generation():
    """Test 3: dedupKey 자동 생성 (code + message 기반 SHA256)"""
    # 동일한 code + message → 동일한 dedupKey
    with pytest.raises(EstimatorError) as exc1:
        raise_error(ErrorCode.E_CATALOG_LOAD, "동일 메시지")

    with pytest.raises(EstimatorError) as exc2:
        raise_error(ErrorCode.E_CATALOG_LOAD, "동일 메시지")

    dedup1 = exc1.value.to_dict()["meta"]["dedupKey"]
    dedup2 = exc2.value.to_dict()["meta"]["dedupKey"]

    assert dedup1 == dedup2

    # 다른 message → 다른 dedupKey
    with pytest.raises(EstimatorError) as exc3:
        raise_error(ErrorCode.E_CATALOG_LOAD, "다른 메시지")

    dedup3 = exc3.value.to_dict()["meta"]["dedupKey"]
    assert dedup1 != dedup3


def test_04_convert_builtin_valueerror():
    """Test 4: ValueError → E_VALIDATION_FAILED 변환"""
    original = ValueError("잘못된 입력값")
    converted = convert_builtin_error(original, context="user_input")

    payload = converted.to_dict()

    assert payload["code"] == "E_VALIDATION_FAILED"
    assert payload["message"] == "잘못된 입력값"
    assert payload["meta"]["exception_type"] == "ValueError"
    assert payload["meta"]["context"] == "user_input"
    assert "dedupKey" in payload["meta"]
    assert "traceId" in payload


def test_05_convert_builtin_filenotfound():
    """Test 5: FileNotFoundError → E_FILE_NOT_FOUND 변환"""
    original = FileNotFoundError("파일을 찾을 수 없습니다")
    converted = convert_builtin_error(original)

    payload = converted.to_dict()

    assert payload["code"] == "E_FILE_NOT_FOUND"
    assert payload["message"] == "파일을 찾을 수 없습니다"
    assert payload["meta"]["exception_type"] == "FileNotFoundError"


def test_06_convert_builtin_ioerror():
    """Test 6: IOError → E_IO 변환"""
    original = IOError("I/O 오류")
    converted = convert_builtin_error(original)

    payload = converted.to_dict()

    assert payload["code"] == "E_IO"
    # Python 3에서 IOError는 OSError의 별칭
    assert payload["meta"]["exception_type"] in ["IOError", "OSError"]


def test_07_convert_builtin_assertionerror():
    """Test 7: AssertionError → E_ASSERTION_FAILED 변환"""
    original = AssertionError("어서션 실패")
    converted = convert_builtin_error(original)

    payload = converted.to_dict()

    assert payload["code"] == "E_ASSERTION_FAILED"
    assert payload["meta"]["exception_type"] == "AssertionError"


def test_08_convert_builtin_generic():
    """Test 8: RuntimeError → E_INTERNAL 변환 (기타 예외)"""
    original = RuntimeError("런타임 오류")
    converted = convert_builtin_error(original)

    payload = converted.to_dict()

    assert payload["code"] == "E_INTERNAL"
    assert payload["meta"]["exception_type"] == "RuntimeError"


def test_09_error_payload_dataclass():
    """Test 9: EstimatorErrorPayload 직접 생성"""
    payload = EstimatorErrorPayload(
        code="E_CATALOG_LOAD",
        message="테스트 메시지",
        traceId="test-trace-id",
        meta={"custom": "data"},
        hint="해결 방법",
    )

    # dedupKey 자동 생성 검증
    assert "dedupKey" in payload.meta
    assert payload.meta["custom"] == "data"

    # to_dict() 검증
    result = payload.to_dict()
    assert result["code"] == "E_CATALOG_LOAD"
    assert result["message"] == "테스트 메시지"
    assert result["traceId"] == "test-trace-id"
    assert result["hint"] == "해결 방법"
    assert "dedupKey" in result["meta"]
    assert result["meta"]["custom"] == "data"


def test_10_error_code_enum_values():
    """Test 10: ErrorCode Enum 값 검증"""
    # 주요 코드 존재 확인
    assert ErrorCode.E_CATALOG_LOAD.value == "E_CATALOG_LOAD"
    assert ErrorCode.E_DATA_TRANSFORM.value == "E_DATA_TRANSFORM"
    assert ErrorCode.E_BRANCH_RULE.value == "E_BRANCH_RULE"
    assert ErrorCode.E_CONTRACT_VIOLATION.value == "E_CONTRACT_VIOLATION"
    assert ErrorCode.E_IO.value == "E_IO"
    assert ErrorCode.E_REDIS_RATE.value == "E_REDIS_RATE"
    assert ErrorCode.E_TEMPLATE_DAMAGED.value == "E_TEMPLATE_DAMAGED"
    assert ErrorCode.E_INTERNAL.value == "E_INTERNAL"
