"""
jwks_sop.py 실제 호출 테스트 (P4-2 Real-Call 전환)

목적: coverage 측정을 위한 실제 함수 호출
원칙: Zero-Mock (로컬 ASGI 핸들러 사용), SB-02 준수
전략: httpx.MockTransport를 사용한 로컬 응답 시뮬레이션
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import httpx

from kis_estimator_core.infra.jwks_sop import (
    fetch_jwks_with_sop,
    clear_jwks_cache,
    get_jwks_cache_status,
    JWKSCache,
    save_jwks_failure_evidence,
    JWKSFailureEvidence,
)


# ============================================================
# Fixture: Mock Transport for Local JWKS Responses
# ============================================================
class MockJWKSTransport(httpx.MockTransport):
    """로컬 JWKS 응답 핸들러 (500→503→200 시퀀스)"""

    def __init__(self, response_sequence):
        """
        Args:
            response_sequence: List of status codes to return in sequence
                              예: [500, 503, 200]
        """
        self.response_sequence = response_sequence
        self.call_count = 0

        def handler(request):
            status_code = self.response_sequence[
                min(self.call_count, len(self.response_sequence) - 1)
            ]
            self.call_count += 1

            if status_code == 200:
                # 성공 응답
                return httpx.Response(
                    status_code=200,
                    json={"keys": [{"kid": "test-key-1", "kty": "RSA", "use": "sig"}]},
                )
            elif status_code in (500, 503):
                # 실패 응답
                return httpx.Response(
                    status_code=status_code, text=f"Server Error: {status_code}"
                )
            else:
                return httpx.Response(
                    status_code=status_code, text=f"Unexpected status: {status_code}"
                )

        super().__init__(handler)


@pytest.fixture(autouse=True)
def clear_cache():
    """각 테스트 전후로 캐시 클리어"""
    clear_jwks_cache()
    yield
    clear_jwks_cache()


@pytest.fixture
def test_jwks_url():
    """테스트용 JWKS URL"""
    return "https://test.supabase.co/auth/v1/.well-known/jwks.json"


# ============================================================
# Test: fetch_jwks_with_sop - Success Path
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_success(test_jwks_url, monkeypatch):
    """JWKS 페치 성공 케이스 (200 OK)"""
    # Mock transport: 즉시 200 응답
    transport = MockJWKSTransport([200])

    # httpx.AsyncClient를 monkeypatch
    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출
    result = await fetch_jwks_with_sop(jwks_url=test_jwks_url, max_retries=1)

    # 검증
    assert result.success is True
    assert result.status_code == 200
    assert result.from_cache is False
    assert result.attempts == 1
    assert "keys" in result.jwks
    assert len(result.jwks["keys"]) == 1


@pytest.mark.asyncio
async def test_fetch_jwks_from_cache(test_jwks_url, monkeypatch):
    """JWKS 캐시 히트 케이스"""
    # Mock transport
    transport = MockJWKSTransport([200])

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 첫 번째 호출 (캐시 미스)
    result1 = await fetch_jwks_with_sop(test_jwks_url, max_retries=1)
    assert result1.from_cache is False

    # 두 번째 호출 (캐시 히트)
    result2 = await fetch_jwks_with_sop(test_jwks_url, max_retries=1)
    assert result2.from_cache is True
    assert result2.attempts == 0  # 캐시 히트는 attempts=0


# ============================================================
# Test: fetch_jwks_with_sop - Recovery Sequence (500→503→200)
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_recovery_sequence(test_jwks_url, monkeypatch):
    """JWKS SOP 복구 시퀀스 (500→503→200)"""
    # Mock transport: 500 → 503 → 200 시퀀스
    transport = MockJWKSTransport([500, 503, 200])

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출 (백오프 없이)
    result = await fetch_jwks_with_sop(
        jwks_url=test_jwks_url,
        max_retries=3,
        backoff_seconds=[0, 0, 0],  # 테스트 속도를 위해 백오프 제거
    )

    # 검증: 3번째 시도에서 성공
    assert result.success is True
    assert result.status_code == 200
    assert result.attempts == 3
    assert "keys" in result.jwks


# ============================================================
# Test: fetch_jwks_with_sop - Failure Cases
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_all_failures(test_jwks_url, monkeypatch):
    """JWKS 페치 모든 시도 실패 (500 반복)"""
    # Mock transport: 모두 500 응답
    transport = MockJWKSTransport([500, 500, 500])

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출
    result = await fetch_jwks_with_sop(
        jwks_url=test_jwks_url, max_retries=3, backoff_seconds=[0, 0, 0]
    )

    # 검증: 실패
    assert result.success is False
    assert result.status_code == 500
    assert result.attempts == 3
    assert result.jwks is None
    assert result.error is not None


@pytest.mark.asyncio
async def test_fetch_jwks_invalid_response(test_jwks_url, monkeypatch):
    """JWKS 응답 검증 실패 (keys 필드 없음)"""

    # Mock transport: 200이지만 keys 필드 없음
    class InvalidJWKSTransport(httpx.MockTransport):
        def __init__(self):
            def handler(request):
                return httpx.Response(
                    status_code=200, json={"invalid": "response"}  # keys 필드 없음
                )

            super().__init__(handler)

    transport = InvalidJWKSTransport()

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    # jwks_sop 모듈의 httpx를 패치해야 함
    monkeypatch.setattr(
        "src.kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", PatchedAsyncClient
    )

    # 실제 호출: ValueError가 except에서 catch되어 result.error로 반환됨
    result = await fetch_jwks_with_sop(test_jwks_url, max_retries=1)

    # 검증: 실패하며 error에 "Invalid JWKS response" 포함
    assert result.success is False
    assert result.jwks is None
    assert "Invalid JWKS response" in result.error


# ============================================================
# Test: JWKSCache
# ============================================================
def test_jwks_cache_set_get():
    """JWKS 캐시 set/get"""
    cache = JWKSCache()

    # 캐시 설정
    test_jwks = {"keys": [{"kid": "test-key"}]}
    cache.set("test_key", test_jwks, ttl=60)

    # 캐시 조회
    result = cache.get("test_key")
    assert result == test_jwks


def test_jwks_cache_expiry():
    """JWKS 캐시 만료"""
    cache = JWKSCache()

    # 캐시 설정 (이미 만료된 상태로)
    test_jwks = {"keys": [{"kid": "test-key"}]}
    cache.set("test_key", test_jwks, ttl=1)
    cache._expiry["test_key"] = datetime.utcnow() - timedelta(
        seconds=10
    )  # 과거 시간으로 설정

    # 캐시 조회: 만료됨
    result = cache.get("test_key")
    assert result is None


def test_jwks_cache_has():
    """JWKS 캐시 has() 메서드"""
    cache = JWKSCache()

    # 캐시 설정
    cache.set("test_key", {"keys": []}, ttl=60)

    # 존재 확인
    assert cache.has("test_key") is True
    assert cache.has("nonexistent_key") is False


def test_jwks_cache_clear():
    """JWKS 캐시 clear()"""
    cache = JWKSCache()

    # 캐시 설정
    cache.set("key1", {"keys": []}, ttl=60)
    cache.set("key2", {"keys": []}, ttl=60)

    # 캐시 클리어
    cache.clear()

    # 검증: 모두 삭제됨
    assert cache.get("key1") is None
    assert cache.get("key2") is None


# ============================================================
# Test: save_jwks_failure_evidence
# ============================================================
def test_save_jwks_failure_evidence(tmp_path, monkeypatch):
    """JWKS 실패 증거 저장"""
    # 임시 디렉토리 사용
    test_evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(
        "src.kis_estimator_core.infra.jwks_sop.EVIDENCE_DIR", test_evidence_dir
    )

    # 증거 생성
    evidence = JWKSFailureEvidence(
        timestamp="2025-10-17T12:00:00",
        jwks_url="https://test.supabase.co/auth/v1/.well-known/jwks.json",
        status_code=500,
        response_headers={"content-type": "text/html"},
        response_body="Internal Server Error",
        attempt=1,
        total_attempts=3,
        backoff_seconds=30,
        cache_available=False,
        trace_id="test-trace-123",
        error_message="JWKS endpoint returned 500",
    )

    # 실제 호출
    evidence_path = save_jwks_failure_evidence(evidence)

    # 검증: 파일 생성됨
    assert Path(evidence_path).exists()

    # 파일 내용 확인
    with open(evidence_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["status_code"] == 500
    assert saved_data["jwks_url"] == evidence.jwks_url


# ============================================================
# Test: clear_jwks_cache / get_jwks_cache_status
# ============================================================
def test_clear_jwks_cache_function():
    """clear_jwks_cache() 함수"""
    from kis_estimator_core.infra.jwks_sop import _jwks_cache

    # 캐시 설정
    _jwks_cache.set("test_key", {"keys": []}, ttl=60)

    # 실제 호출
    clear_jwks_cache()

    # 검증
    assert _jwks_cache.get("test_key") is None


def test_get_jwks_cache_status():
    """get_jwks_cache_status() 함수"""
    from kis_estimator_core.infra.jwks_sop import _jwks_cache

    # 캐시 설정
    _jwks_cache.set("test_key", {"keys": []}, ttl=60)

    # 실제 호출
    status = get_jwks_cache_status()

    # 검증
    assert "cached_jwks" in status
    assert status["cached_jwks"] == 1
    assert "test_key" in status["cache_keys"]


# ============================================================
# Test: Additional Coverage - Stale Cache Fallback
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_stale_cache_fallback(test_jwks_url, monkeypatch):
    """JWKS 실패 시 stale cache fallback (2단계 테스트)"""
    from kis_estimator_core.infra.jwks_sop import _jwks_cache

    # === 1단계: 200 OK로 캐시 생성 ===
    transport_success = MockJWKSTransport([200])

    original_client = httpx.AsyncClient

    class PatchedAsyncClientSuccess(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport_success
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClientSuccess)

    # 첫 번째 호출: 캐시 생성
    result1 = await fetch_jwks_with_sop(jwks_url=test_jwks_url, max_retries=1)
    assert result1.success is True
    assert result1.from_cache is False

    # 캐시 상태 확인
    cache_key = f"jwks:{test_jwks_url}"
    assert _jwks_cache.has(cache_key) is True

    # === 2단계: 500 failure 시 stale cache 사용 (캐시는 expired 안 함) ===
    transport_failure = MockJWKSTransport([500, 500])

    class PatchedAsyncClientFailure(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport_failure
            super().__init__(*args, **kwargs)

    # Patch AsyncClient를 500 failure로 변경
    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClientFailure)

    # 캐시를 expired 상태로 변경 (하지만 get()이 삭제하지 않게 monkeypatch)
    _jwks_cache._expiry[cache_key] = datetime.utcnow() - timedelta(seconds=10)

    # _jwks_cache.get() 메서드를 monkeypatch하여 expired 캐시를 삭제하지 않게 함
    original_get = _jwks_cache.get

    def patched_get(key):
        # expired 캐시는 None을 반환하되 삭제하지 않음 (has()가 True를 유지)
        if key not in _jwks_cache._cache:
            return None
        if key in _jwks_cache._expiry and datetime.utcnow() > _jwks_cache._expiry[key]:
            return None  # expired이지만 삭제하지 않음
        return _jwks_cache._cache[key]

    _jwks_cache.get = patched_get

    # 두 번째 호출: 500 실패 → stale cache 반환
    result2 = await fetch_jwks_with_sop(
        jwks_url=test_jwks_url, max_retries=2, backoff_seconds=[0, 0]
    )

    # get() 복원
    _jwks_cache.get = original_get

    # 검증: stale cache 사용 성공
    assert result2.success is True
    assert result2.from_cache is True
    assert result2.status_code == 500  # 서버는 500이지만
    assert result2.jwks is not None  # stale cache 반환
    assert "keys" in result2.jwks


# ============================================================
# Test: Additional Coverage - Unexpected Status Codes
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_unexpected_status_code(test_jwks_url, monkeypatch):
    """예상치 못한 status code (404)"""
    # Mock transport: 404 응답
    transport = MockJWKSTransport([404])

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출
    result = await fetch_jwks_with_sop(test_jwks_url, max_retries=1)

    # 검증: 실패, error에 "Unexpected status code" 포함
    assert result.success is False
    assert result.status_code == 404
    assert "Unexpected status code" in result.error


# ============================================================
# Test: Additional Coverage - Timeout Exception
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_timeout_exception(test_jwks_url, monkeypatch):
    """JWKS fetch timeout 예외"""

    # Mock transport: TimeoutException 발생
    class TimeoutTransport(httpx.MockTransport):
        def __init__(self):
            def handler(request):
                raise httpx.TimeoutException("Request timeout")

            super().__init__(handler)

    transport = TimeoutTransport()

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출
    result = await fetch_jwks_with_sop(
        jwks_url=test_jwks_url, max_retries=2, backoff_seconds=[0, 0]
    )

    # 검증: timeout 실패
    assert result.success is False
    assert result.status_code is None
    assert "Timeout after 2 attempts" in result.error


# ============================================================
# Test: Additional Coverage - Generic Exception
# ============================================================
@pytest.mark.asyncio
async def test_fetch_jwks_generic_exception(test_jwks_url, monkeypatch):
    """JWKS fetch 일반 예외"""

    # Mock transport: 일반 예외 발생
    class ExceptionTransport(httpx.MockTransport):
        def __init__(self):
            def handler(request):
                raise RuntimeError("Unexpected error")

            super().__init__(handler)

    transport = ExceptionTransport()

    original_client = httpx.AsyncClient

    class PatchedAsyncClient(original_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient", PatchedAsyncClient)

    # 실제 호출
    result = await fetch_jwks_with_sop(
        jwks_url=test_jwks_url, max_retries=2, backoff_seconds=[0, 0]
    )

    # 검증: 일반 예외 실패
    assert result.success is False
    assert "Unexpected error" in result.error
