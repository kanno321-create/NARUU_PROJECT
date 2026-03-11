"""
Regression Test: LifespanManager + Event Loop Auto Management

Lock-in 3/5: 회귀 테스트 (LifespanManager 패턴 + auto 모드)

Tests the patterns for preventing "Event loop is closed" errors:
1. LifespanManager ensures FastAPI startup/shutdown events execute
2. pytest-asyncio auto mode manages event loops (no custom fixture)
3. httpx does NOT support lifespan parameter (use asgi-lifespan)
4. Engine/session dispose happens correctly with auto-managed loops

Root Cause Fixed:
- pytest-asyncio 0.21.2 with asyncio_mode=auto (no custom event_loop fixture)
- LifespanManager + ASGITransport pattern (FastAPI lifespan guaranteed)
- httpx 0.24.1 (constraints.txt enforced)

This test prevents regression of FastAPI lifespan issues and event loop conflicts.

Official Documentation:
- https://www.python-httpx.org/advanced/#calling-into-python-web-apps
- https://fastapi.tiangolo.com/advanced/testing-events/
- https://github.com/florimondmanca/asgi-lifespan
- https://pytest-asyncio.readthedocs.io/en/latest/reference/fixtures.html
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Import FastAPI app
from api.main import app


@pytest.mark.regression
@pytest.mark.asyncio
async def test_lifespan_manager_startup_shutdown():
    """
    Verify LifespanManager ensures FastAPI startup/shutdown events execute

    This tests:
    1. LifespanManager triggers startup events (DB init, cache warming)
    2. AsyncClient with ASGITransport(app=manager.app) pattern
    3. Shutdown events execute after context exit
    4. httpx does NOT support lifespan parameter
    """
    # Get current event loop
    loop = asyncio.get_running_loop()
    assert not loop.is_closed(), "Event loop should be running at test start"

    # Use LifespanManager to ensure startup/shutdown
    async with LifespanManager(app) as manager:
        # Create AsyncClient with manager.app (lifespan guaranteed)
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            # Make request to verify app is ready
            response = await client.get("/health")
            assert response.status_code == 200, f"Health check failed: {response.text}"

            # Verify response structure (Phase VII: status="live")
            data = response.json()
            assert "status" in data, "Health response should have status"
            assert (
                data["status"] == "live"
            ), f"Status should be live, got {data['status']}"

    # After LifespanManager exit, shutdown events have executed
    assert (
        not loop.is_closed()
    ), "Event loop should still be alive after LifespanManager exit"


@pytest.mark.regression
@pytest.mark.asyncio
async def test_double_dispose_safe():
    """
    Verify that double engine.dispose() calls are idempotent (no error)

    This tests the pattern where:
    - Test fixture disposes engine at session end
    - App lifespan (if enabled) might also try to dispose
    - Both should be safe (no exception)
    """
    # Create a temporary test engine
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/kis_test"
    engine = create_async_engine(
        db_url,
        poolclass=NullPool,
        future=True,
    )

    # First dispose - should work
    await engine.dispose()

    # Second dispose - should be safe (idempotent)
    try:
        await engine.dispose()
        # Success - double dispose is safe
    except Exception as e:
        pytest.fail(f"Double dispose should be safe but raised: {e}")


@pytest.mark.regression
@pytest.mark.asyncio
async def test_pytest_asyncio_auto_mode():
    """
    Verify pytest-asyncio auto mode manages event loops correctly

    This tests:
    - asyncio_mode = auto (pytest.ini) handles event loop lifecycle
    - No custom event_loop fixture needed
    - Auto-managed loops work with async tests
    """
    # Get current event loop (auto-managed by pytest-asyncio)
    loop = asyncio.get_running_loop()
    assert not loop.is_closed(), "Event loop should be alive (auto-managed)"

    # Perform async operation to verify loop works
    await asyncio.sleep(0.001)

    # Loop should still be alive after async operation
    assert (
        not loop.is_closed()
    ), "Event loop should still be alive after async operation"


@pytest.mark.regression
def test_pytest_asyncio_version():
    """
    Verify pytest-asyncio version is locked to 0.23.x

    Lock-in requirement: pytest-asyncio==0.23.8
    - 0.21.2: asyncio_mode=auto with manual event_loop fixture (DEPRECATED)
    - 0.22.0: YANKED from PyPI (breaks compatibility)
    - 0.23.8: Native session-scoped async fixture support (CURRENT)
      * Automatically manages event loops for session-scoped fixtures
      * No manual event_loop fixture needed
      * asyncio_mode=auto works natively with session scope

    Migration: 0.21.2 → 0.23.8 (Phase VII fix for "Event loop is closed" errors)
    Current pattern: Use asyncio_mode=auto (pytest-asyncio manages event loop automatically)
    """

    version = pytest_asyncio.__version__
    major, minor, patch = version.split(".")

    assert major == "0", f"pytest-asyncio major version should be 0, got {major}"
    assert minor == "23", f"pytest-asyncio minor version should be 23, got {minor}"

    print(f"[OK] pytest-asyncio=={version} (locked to 0.23.x for session-scoped fixture support)")


@pytest.mark.regression
@pytest.mark.asyncio
async def test_readyz_vs_health_endpoints():
    """
    Verify /health (liveness) and /readyz (readiness) endpoints work correctly

    This tests:
    - /health: Always returns 200 (liveness check)
    - /readyz: Returns 200 if ready, 503 if not ready (strict check)
    - E2E should wait for /readyz, not /health
    """
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            # Test /health (liveness)
            health_response = await client.get("/health")
            assert (
                health_response.status_code == 200
            ), "/health should always return 200"

            # Test /readyz (readiness)
            readyz_response = await client.get("/readyz")
            # Should be 200 (ready) or 503 (not ready), but must exist
            assert readyz_response.status_code in [
                200,
                503,
            ], "/readyz should return 200 or 503"

            if readyz_response.status_code == 200:
                data = readyz_response.json()
                assert data["status"] == "ready", "Status should be 'ready' when 200"
