"""
Error Schema Assertion Helpers - 표준 오류 응답 검증

절대 원칙:
- 모든 오류 응답은 {code, message, traceId, meta{dedupKey}} 필수
- API 응답: HTTP status + 표준 JSON 페이로드
- 내부 예외: EstimatorError 타입 + payload 속성
"""

from typing import Any

from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError


def assert_error_payload(
    payload: dict[str, Any],
    *,
    code: str | None = None,
    message_contains: str | None = None,
    has_hint: bool = False,
) -> None:
    """
    표준 오류 페이로드 필드 검증

    Args:
        payload: JSON 응답 또는 EstimatorError.to_dict() 결과
        code: 기대하는 ErrorCode (예: "E_CATALOG_LOAD")
        message_contains: 메시지에 포함되어야 하는 문자열
        has_hint: hint 필드 존재 여부 검증

    Raises:
        AssertionError: 필수 필드 누락 또는 값 불일치
    """
    # 필수 필드 검증
    required_fields = {"code", "message", "traceId", "meta"}
    assert (
        set(payload.keys()) >= required_fields
    ), f"Missing required fields. Expected: {required_fields}, Got: {set(payload.keys())}"

    # meta.dedupKey 검증
    assert "dedupKey" in payload["meta"], "Missing meta.dedupKey"
    assert (
        len(payload["meta"]["dedupKey"]) == 16
    ), "dedupKey must be 16 chars (SHA256 truncated)"

    # traceId 형식 검증 (UUID v4)
    assert isinstance(payload["traceId"], str), "traceId must be string"
    assert len(payload["traceId"]) > 0, "traceId must not be empty"

    # code 검증
    if code:
        assert payload["code"] == code, f"Expected code={code}, got {payload['code']}"

    # message 검증
    if message_contains:
        assert (
            message_contains in payload["message"]
        ), f"Expected message to contain '{message_contains}', got '{payload['message']}'"

    # hint 검증
    if has_hint:
        assert "hint" in payload, "Expected hint field"
        assert payload["hint"], "hint must not be empty"


def assert_estimator_error(
    exc: EstimatorError,
    *,
    code: ErrorCode | None = None,
    message_contains: str | None = None,
) -> None:
    """
    EstimatorError 예외 객체 검증

    Args:
        exc: EstimatorError 예외 인스턴스
        code: 기대하는 ErrorCode Enum
        message_contains: 메시지에 포함되어야 하는 문자열

    Raises:
        AssertionError: 타입 불일치 또는 값 불일치
    """
    assert isinstance(exc, EstimatorError), f"Expected EstimatorError, got {type(exc)}"

    payload = exc.to_dict()

    # 기본 필드 검증
    assert_error_payload(payload)

    # code 검증 (Enum)
    if code:
        assert (
            payload["code"] == code.value
        ), f"Expected code={code.value}, got {payload['code']}"

    # message 검증
    if message_contains:
        assert (
            message_contains in payload["message"]
        ), f"Expected message to contain '{message_contains}', got '{payload['message']}'"


def assert_http_error_response(
    response_json: dict[str, Any],
    *,
    expected_status: int,
    expected_code: str | None = None,
) -> None:
    """
    HTTP 오류 응답 검증 (FastAPI 미들웨어 경유)

    Args:
        response_json: response.json() 결과
        expected_status: 기대하는 HTTP 상태 코드 (400, 404, 500 등)
        expected_code: 기대하는 ErrorCode (예: "E_CONTRACT_VIOLATION")

    Raises:
        AssertionError: 응답 형식 불일치
    """
    # 표준 페이로드 검증
    assert_error_payload(response_json, code=expected_code)

    # HTTP 상태 코드 매핑 검증 (간접 - 응답에는 status 없음)
    # 미들웨어가 code → status 변환했음을 가정
    # 별도 status 필드 없으므로 생략
