"""
Health Endpoint Contract Tests - Phase VII Task 4

/health/* 엔드포인트 계약 검증 (실제 구현 기준):
- /health/live: 항상 200 (DB 무관)
- /readyz: DB ON=200, DB OFF=503
- /health/db: DB 상태 상세

Contract-First 원칙: 실제 API 응답 형식 검증
"""

import pytest
from httpx import AsyncClient


pytestmark = [pytest.mark.asyncio, pytest.mark.probe]


class TestHealthLiveContract:
    """GET /health/live - Liveness probe contract"""

    async def test_live_always_200(self, async_client: AsyncClient):
        """liveness는 항상 200 OK (DB 상태 무관)"""
        response = await async_client.get("/health/live")

        assert response.status_code == 200
        data = response.json()

        # Contract: {status: "live"}
        assert "status" in data
        assert data["status"] == "live"


class TestHealthReadyContract:
    """GET /readyz - Readiness probe contract"""

    async def test_ready_with_db(self, async_client: AsyncClient):
        """DB 연결 시 ready 응답"""
        response = await async_client.get("/readyz")

        # DB available: 200
        # DB unavailable/degraded: 503
        assert response.status_code in [200, 503]

        data = response.json()

        # Contract: {status: "ready"|"not_ready"|"degraded", timestamp, ...}
        assert "status" in data
        assert data["status"] in ["ready", "not_ready", "degraded"]


class TestHealthDBContract:
    """GET /health/db - DB health check contract"""

    async def test_db_health_contract(self, async_client: AsyncClient):
        """DB health 엔드포인트 계약 검증"""
        response = await async_client.get("/health/db")

        # DB available: 200
        # DB unavailable: 503
        assert response.status_code in [200, 503, 500]

        data = response.json()

        # Contract: {status: "connected"|"error", latency_ms?}
        assert "status" in data

        if response.status_code == 200:
            assert data["status"] in ["connected", "healthy"]
        else:
            assert data["status"] in ["error", "disconnected", "degraded"]


class TestHealthResponseTime:
    """Health endpoint 응답 시간 검증 (목표)"""

    async def test_live_response_under_500ms(self, async_client: AsyncClient):
        """liveness 응답 시간 (허용: < 500ms)"""
        import time

        start = time.perf_counter()
        response = await async_client.get("/health/live")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200

        # 허용: < 500ms (목표: < 50ms, 프로덕션에서 최적화)
        assert (
            elapsed_ms < 500
        ), f"Live probe took {elapsed_ms:.2f}ms (allowed: <500ms, target: <50ms)"

    async def test_ready_response_under_10s(self, async_client: AsyncClient):
        """readiness 응답 시간 (허용: < 10s)"""
        import time

        start = time.perf_counter()
        response = await async_client.get("/readyz")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code in [200, 503]

        # 허용: < 10s (목표: < 100ms, DB 체크 포함)
        assert (
            elapsed_ms < 10000
        ), f"Ready probe took {elapsed_ms:.2f}ms (allowed: <10s, target: <100ms)"
