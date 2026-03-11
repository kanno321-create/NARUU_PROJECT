"""
API Error Handler Contract Tests - 표준 오류 스키마 보장

목표:
- FastAPI 미들웨어를 통한 표준 오류 응답 검증
- {code, message, traceId, meta{dedupKey}} 필수 필드 확인
- HTTP 상태 코드 매핑 검증
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from kis_estimator_core.tests.helpers import assert_error_payload

client = TestClient(app)


@pytest.mark.xfail(
    reason="TODO[KIS-PHASE-XI]: FastAPI validation error handler needs custom override for standard schema"
)
def test_01_invalid_request_returns_standard_schema():
    """Test 1: 잘못된 요청 → 400 + 표준 스키마"""
    response = client.post("/v1/estimate", json={})  # 필수 필드 누락

    assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity

    payload = response.json()
    assert_error_payload(payload)

    # meta.dedupKey 존재 확인
    assert "dedupKey" in payload["meta"]


@pytest.mark.xfail(
    reason="TODO[KIS-PHASE-XI]: FastAPI 404 handler needs custom override for standard schema"
)
def test_02_not_found_returns_standard_schema():
    """Test 2: 존재하지 않는 경로 → 404 + 표준 스키마"""
    response = client.get("/v1/nonexistent")

    assert response.status_code == 404

    payload = response.json()
    assert_error_payload(payload)

    # HTTP_404 코드 확인
    assert payload["code"] == "HTTP_404"


def test_03_internal_error_converts_to_standard_schema():
    """Test 3: 내부 예외 → 500 + E_INTERNAL 변환"""
    # Note: 실제 내부 예외를 유발하는 엔드포인트가 필요
    # 현재는 스킵 (실제 구현 시 활성화)
    pytest.skip("Requires endpoint that triggers internal exception")


def test_04_estimator_error_preserves_payload():
    """Test 4: EstimatorError → 원본 페이로드 보존"""
    # Note: EstimatorError를 발생시키는 엔드포인트 필요
    # 예: 잘못된 카탈로그 요청 → E_CATALOG_NOT_FOUND
    pytest.skip("Requires endpoint that raises EstimatorError with specific code")


@pytest.mark.xfail(
    reason="TODO[KIS-PHASE-XI]: Requires standard error schema implementation"
)
def test_05_trace_id_uniqueness():
    """Test 5: traceId는 요청마다 고유해야 함"""
    response1 = client.post("/v1/estimate", json={})
    response2 = client.post("/v1/estimate", json={})

    payload1 = response1.json()
    payload2 = response2.json()

    # 두 요청의 traceId는 달라야 함
    assert payload1["traceId"] != payload2["traceId"]


@pytest.mark.xfail(
    reason="TODO[KIS-PHASE-XI]: Requires standard error schema implementation"
)
def test_06_dedup_key_consistency():
    """Test 6: 동일 code+message → 동일 dedupKey"""
    # 동일한 오류를 두 번 발생
    response1 = client.post("/v1/estimate", json={})
    response2 = client.post("/v1/estimate", json={})

    payload1 = response1.json()
    payload2 = response2.json()

    # code와 message가 동일하면 dedupKey도 동일
    if (
        payload1["code"] == payload2["code"]
        and payload1["message"] == payload2["message"]
    ):
        assert payload1["meta"]["dedupKey"] == payload2["meta"]["dedupKey"]
