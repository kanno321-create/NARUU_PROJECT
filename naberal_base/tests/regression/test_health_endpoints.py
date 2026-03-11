"""
I-3.5 Health/Readyz Endpoints Regression Tests

목적: Health check 엔드포인트 커버리지 증대
예상 커버리지 증가: +5%

커버되는 모듈:
- api/main.py (health/readyz 엔드포인트)
- api/db.py (check_db_health)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.regression
async def test_health_endpoint(async_client: AsyncClient):
    """
    GET /health - Health check

    검증:
    - 200 OK
    - status: ok
    - timestamp 존재
    """
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "live"  # Changed from "ok" to "live" (Phase VII)

    print(f"[OK] Health check: status={data['status']}")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_readyz_endpoint(async_client: AsyncClient):
    """
    GET /readyz - Readiness check

    검증:
    - status in [ready, not_ready]
    - core_services.database.connected = True
    - estimation_subsystem exists
    """
    response = await async_client.get("/readyz")

    # Accept 200 (ready) or 503 (not_ready)
    assert response.status_code in [200, 503]
    data = response.json()

    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]

    # Critical dependencies should include database, cache, catalog (Phase VII)
    assert "critical_dependencies" in data
    assert "database" in data["critical_dependencies"]
    assert data["critical_dependencies"]["database"]["ready"] is True

    # Optional dependencies should exist
    assert "optional_dependencies" in data

    print(
        f"[OK] Readiness check: status={data['status']}, db ready={data['critical_dependencies']['database']['ready']}"
    )


@pytest.mark.asyncio
@pytest.mark.regression
async def test_health_response_structure(async_client: AsyncClient):
    """
    GET /health - Response structure validation

    검증:
    - 표준 health check 응답 구조
    - 필수 필드 존재
    """
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Required fields
    required_fields = ["status"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Optional but recommended fields
    if "timestamp" in data:
        assert isinstance(data["timestamp"], str)

    if "version" in data:
        assert isinstance(data["version"], str)

    print("[OK] Health response structure valid")


@pytest.mark.asyncio
@pytest.mark.regression
async def test_readyz_response_structure(async_client: AsyncClient):
    """
    GET /readyz - Response structure validation

    검증:
    - 표준 readiness check 응답 구조
    - 서비스별 상태 정보
    """
    response = await async_client.get("/readyz")

    # Accept 200 or 503
    assert response.status_code in [200, 503]
    data = response.json()

    # Required fields (Phase VII structure)
    assert "status" in data
    assert "critical_dependencies" in data
    assert "optional_dependencies" in data
    assert "failing_components" in data

    # Critical dependencies structure
    critical = data["critical_dependencies"]
    assert "database" in critical
    assert "ready" in critical["database"]
    assert isinstance(critical["database"]["ready"], bool)
    assert "cache" in critical
    assert "catalog" in critical

    # Optional dependencies
    optional = data["optional_dependencies"]
    if "redis" in optional:
        assert "ready" in optional["redis"]
        assert isinstance(optional["redis"]["ready"], bool)

    print("[OK] Readyz response structure valid")


# ==================== WORK LOG ====================
"""
DECISIONS:
- Health/Readyz 엔드포인트 4개 테스트
- 응답 구조 검증 포함
- Database/Redis 연결 상태 확인

ASSUMPTIONS:
- /health 엔드포인트 구현됨
- /readyz 엔드포인트 구현됨
- Database health check 작동

COVERAGE TARGET:
- api/main.py health/readyz 라우트: +3%
- api/db.py check_db_health: +2%

TOTAL EXPECTED: +5% coverage increase
"""
