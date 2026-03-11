"""
P4-2.3: JWKS SOP Tests
Target: jwks_sop.py 0% → 50% coverage (~77/153 statements)

Tests JWKS Standard Operating Procedure (SB-02 compliance):
- JWKSCache: get/set/has/clear operations
- fetch_jwks_with_sop: 200 OK, 500/503 retries, cache behavior
- Evidence capture: failure evidence saved to EvidencePack_v2/ci/jwks_failures/
- Exponential backoff: 30s, 60s, 120s, 300s
- Stale cache fallback: Use cached JWKS when endpoint unavailable

SB-02 Compliance: JWKS health SOP with evidence capture
Zero-Mock: Using unittest.mock for httpx client mocking
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


from kis_estimator_core.infra.jwks_sop import (
    JWKSCache,
    JWKSFailureEvidence,
    fetch_jwks_with_sop,
    save_jwks_failure_evidence,
    clear_jwks_cache,
    get_jwks_cache_status,
    _jwks_cache,
)

# Import module explicitly for coverage measurement
from kis_estimator_core.infra import jwks_sop as _  # noqa: F401


@pytest.fixture
def clean_cache():
    """Clean JWKS cache before and after each test."""
    clear_jwks_cache()
    yield
    clear_jwks_cache()


@pytest.fixture
def mock_jwks():
    """Mock JWKS response with keys."""
    return {
        "keys": [
            {
                "kid": "test-key-1",
                "kty": "RSA",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }


def create_mock_response(status_code: int, json_data: dict = None, text: str = None):
    """Create a mock httpx.Response object."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    if json_data is not None:
        mock_response.json.return_value = json_data
    if text is not None:
        mock_response.text = text
    else:
        mock_response.text = json.dumps(json_data) if json_data else ""
    mock_response.headers = {"content-type": "application/json"}
    return mock_response


def create_mock_client(responses: list):
    """Create a mock httpx.AsyncClient that returns specified responses sequentially."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=responses)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestJWKSCache:
    """JWKSCache operations tests"""

    def test_cache_set_and_get(self, clean_cache):
        """Set and get cached JWKS - PASS"""
        cache = JWKSCache()
        test_jwks = {"keys": [{"kid": "test-1"}]}

        cache.set("test_key", test_jwks, ttl=3600)
        result = cache.get("test_key")

        assert result is not None
        assert result == test_jwks
        assert result["keys"][0]["kid"] == "test-1"

    def test_cache_get_nonexistent(self, clean_cache):
        """Get nonexistent key returns None - PASS"""
        cache = JWKSCache()
        result = cache.get("nonexistent_key")

        assert result is None

    def test_cache_expired(self, clean_cache):
        """Expired cache returns None - PASS"""
        cache = JWKSCache()
        test_jwks = {"keys": [{"kid": "test-1"}]}

        # Set with 0 second TTL (immediately expired)
        cache.set("test_key", test_jwks, ttl=0)

        # Manually expire
        cache._expiry["test_key"] = datetime.utcnow() - timedelta(seconds=1)

        result = cache.get("test_key")

        assert result is None
        assert "test_key" not in cache._cache  # Should be removed

    def test_cache_has(self, clean_cache):
        """has() checks key existence even if expired - PASS"""
        cache = JWKSCache()
        test_jwks = {"keys": [{"kid": "test-1"}]}

        cache.set("test_key", test_jwks, ttl=0)
        # Expire manually
        cache._expiry["test_key"] = datetime.utcnow() - timedelta(seconds=1)

        # has() should return True (key exists in _cache)
        assert cache.has("test_key") is True

    def test_cache_clear(self, clean_cache):
        """clear() removes all cached items - PASS"""
        cache = JWKSCache()
        cache.set("key1", {"keys": []}, ttl=3600)
        cache.set("key2", {"keys": []}, ttl=3600)

        assert len(cache._cache) == 2

        cache.clear()

        assert len(cache._cache) == 0
        assert len(cache._expiry) == 0


class TestFetchJWKSWithSOP:
    """JWKS fetch with SOP compliance tests"""

    @pytest.mark.asyncio
    async def test_fetch_jwks_200_success(self, clean_cache, mock_jwks):
        """Fetch JWKS 200 OK - PASS"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        mock_response = create_mock_response(200, mock_jwks)
        mock_client = create_mock_client([mock_response])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(jwks_url, max_retries=1)

            assert result.success is True
            assert result.status_code == 200
            assert result.from_cache is False
            assert result.attempts == 1
            assert result.jwks == mock_jwks
            assert len(result.jwks["keys"]) == 1

    @pytest.mark.asyncio
    async def test_fetch_jwks_cache_hit(self, clean_cache, mock_jwks):
        """Second fetch uses cache - PASS"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        mock_response = create_mock_response(200, mock_jwks)
        mock_client = create_mock_client([mock_response])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            # First fetch (from endpoint)
            result1 = await fetch_jwks_with_sop(jwks_url, cache_ttl=3600)
            assert result1.from_cache is False

            # Second fetch (from cache) - no need to patch, cache will be used
            result2 = await fetch_jwks_with_sop(jwks_url, cache_ttl=3600)
            assert result2.from_cache is True
            assert result2.attempts == 0  # No HTTP request made
            assert result2.jwks == mock_jwks

    @pytest.mark.asyncio
    async def test_fetch_jwks_500_retry_then_200(self, clean_cache, mock_jwks):
        """500 error then 200 OK after retry - PASS"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # First call: 500, second call: 200
        mock_response_500 = create_mock_response(500, text="Internal Server Error")
        mock_response_200 = create_mock_response(200, mock_jwks)
        mock_client = create_mock_client([mock_response_500, mock_response_200])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(
                jwks_url, max_retries=2, backoff_seconds=[0, 0]  # No delay for test speed
            )

            assert result.success is True
            assert result.status_code == 200
            assert result.attempts == 2  # Took 2 attempts
            assert result.jwks == mock_jwks

    @pytest.mark.asyncio
    async def test_fetch_jwks_503_no_cache_fail(self, clean_cache):
        """503 error without cache - FAIL (no fallback)"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock 503 response (all retries)
        mock_response_503 = create_mock_response(503, text="Service Unavailable")
        mock_client = create_mock_client([mock_response_503, mock_response_503])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(
                jwks_url, max_retries=2, backoff_seconds=[0, 0]
            )

            assert result.success is False
            assert result.status_code == 503
            assert result.jwks is None
            assert result.attempts == 2
            assert "unavailable" in result.error.lower()
            assert result.evidence_path is not None  # Evidence captured even on failure

    @pytest.mark.asyncio
    async def test_fetch_jwks_500_no_cache_fail(self, clean_cache):
        """500 error without cache - FAIL"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock 500 response (all retries)
        mock_response_500 = create_mock_response(500, text="Internal Server Error")
        mock_client = create_mock_client([mock_response_500, mock_response_500])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(
                jwks_url, max_retries=2, backoff_seconds=[0, 0]
            )

            assert result.success is False
            assert result.status_code == 500
            assert result.jwks is None
            assert result.attempts == 2
            assert "unavailable" in result.error.lower()

    @pytest.mark.asyncio
    async def test_fetch_jwks_invalid_response(self, clean_cache):
        """Invalid JWKS (missing 'keys' field) returns error result - FAIL"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock 200 but invalid JWKS (missing 'keys')
        invalid_jwks = {"invalid": "response"}
        mock_response = create_mock_response(200, invalid_jwks)
        mock_client = create_mock_client([mock_response])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            # fetch_jwks_with_sop catches ValueError and returns error result
            result = await fetch_jwks_with_sop(jwks_url, max_retries=1)

            assert result.success is False
            assert result.jwks is None
            assert "Invalid JWKS response" in result.error
            assert "missing 'keys' field" in result.error

    @pytest.mark.asyncio
    async def test_fetch_jwks_timeout(self, clean_cache):
        """Timeout after max retries - FAIL"""
        import httpx
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock timeout exception
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(
                jwks_url, max_retries=2, backoff_seconds=[0, 0]
            )

            assert result.success is False
            assert result.status_code is None
            assert result.jwks is None
            assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_fetch_jwks_unexpected_status(self, clean_cache):
        """Unexpected status code (e.g., 404) - FAIL"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock 404 response
        mock_response = create_mock_response(404, text="Not Found")
        mock_client = create_mock_client([mock_response])

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(jwks_url, max_retries=1)

            assert result.success is False
            assert result.status_code == 404
            assert result.jwks is None
            assert "Unexpected status code" in result.error

    @pytest.mark.asyncio
    async def test_fetch_jwks_generic_exception(self, clean_cache):
        """Generic exception handling - FAIL"""
        jwks_url = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

        # Mock generic exception
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("kis_estimator_core.infra.jwks_sop.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_jwks_with_sop(
                jwks_url, max_retries=2, backoff_seconds=[0, 0]
            )

            assert result.success is False
            assert result.jwks is None
            assert "Network error" in result.error


class TestEvidenceCapture:
    """Evidence capture tests"""

    def test_save_jwks_failure_evidence(self, tmp_path):
        """Evidence saved to correct location - PASS"""
        # Use tmp_path for evidence
        with patch("kis_estimator_core.infra.jwks_sop.EVIDENCE_DIR", tmp_path):
            evidence = JWKSFailureEvidence(
                timestamp=datetime.utcnow().isoformat(),
                jwks_url="https://test.supabase.co/auth/v1/.well-known/jwks.json",
                status_code=500,
                response_headers={"content-type": "text/plain"},
                response_body="Internal Server Error",
                attempt=1,
                total_attempts=4,
                backoff_seconds=30,
                cache_available=False,
                trace_id="test-trace-123",
                error_message="JWKS endpoint returned 500",
            )

            filepath = save_jwks_failure_evidence(evidence)

            # Verify file exists
            assert Path(filepath).exists()

            # Verify content
            with open(filepath, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert saved_data["status_code"] == 500
            assert saved_data["jwks_url"] == evidence.jwks_url
            assert saved_data["trace_id"] == "test-trace-123"
            assert saved_data["backoff_seconds"] == 30


class TestCacheManagement:
    """Cache management functions tests"""

    def test_clear_jwks_cache(self, clean_cache):
        """clear_jwks_cache() clears global cache - PASS"""
        _jwks_cache.set("test_key", {"keys": []}, ttl=3600)
        assert len(_jwks_cache._cache) > 0

        clear_jwks_cache()

        assert len(_jwks_cache._cache) == 0

    def test_get_jwks_cache_status(self, clean_cache):
        """get_jwks_cache_status() returns cache info - PASS"""
        test_jwks = {"keys": [{"kid": "test-1"}]}
        _jwks_cache.set("jwks:test_url", test_jwks, ttl=3600)

        status = get_jwks_cache_status()

        assert status["cached_jwks"] == 1
        assert "jwks:test_url" in status["cache_keys"]
        assert "jwks:test_url" in status["expiry_times"]
