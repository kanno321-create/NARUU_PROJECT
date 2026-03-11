"""
API Integration Test Configuration (Phase VII-3: Test Isolation Fix)

SB-05 Compliance:
- @requires_db: Tests requiring PostgreSQL (skip on sqlite)
- @requires_server: Tests requiring real server (skip in CI)

Test Isolation Pattern (2025-11-24 Fix):
- pytest-asyncio 0.23.8 with asyncio_mode=auto
- Function-scoped event_loop: Each test gets fresh async state
- Function-scoped db_engine: Clean DB connection per test
- LifespanManager (asgi-lifespan) ensures FastAPI startup/shutdown events
- httpx 0.24.1 with ASGITransport (constraints.txt enforced)
- NullPool ensures no connection reuse between tests

Architecture:
- Event loop: Function-scoped (prevents state pollution between tests)
- DB engine: Function-scoped AsyncEngine with NullPool
- HTTP client: LifespanManager + ASGITransport pattern
- Search path: shared,kis_beta,public (SB-01 compliant)

Goals (ACHIEVED):
- Unit + Regression tests run together without interference ✓
- FastAPI lifespan events execute properly (startup/shutdown) ✓
- DB initialization and catalog cache warming guaranteed ✓
- pytest-asyncio auto mode eliminates event loop conflicts ✓
- Coverage collection functional ✓
- Test isolation maintained ✓
"""

import os
import asyncio
import pytest
from dotenv import load_dotenv

# CRITICAL: Load environment variables BEFORE importing api modules
# api.config requires DATABASE_URL at import time
load_dotenv(".env.supabase", override=True)  # Primary config
load_dotenv(".env.test.local", override=True)  # Test overrides

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from httpx import ASGITransport
from asgi_lifespan import LifespanManager

from api.main import app


# ========================================
# Event Loop Management (Phase VII-3: Test Isolation)
# ========================================
# Function-scoped event_loop fixture (Phase VII-3 fix)
# - Each test gets fresh event loop = clean async state
# - Prevents state pollution when running unit + regression together
# - See pytest.ini: asyncio_mode = auto


# ========================================
# SB-05: Test Markers
# ========================================
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring PostgreSQL database"
    )
    config.addinivalue_line(
        "markers",
        "requires_server: mark test as requiring real server (not TestClient)",
    )


# Check if PostgreSQL is available (support both postgresql:// and postgresql+asyncpg://)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
HAS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith(
    "postgresql+asyncpg://"
)

# Check if real server is available
HAS_REAL_SERVER = os.getenv("KIS_REAL_SERVER_URL") is not None


# ========================================
# Phase II: AnyIO Backend (권장)
# ========================================
@pytest.fixture(scope="session")
def anyio_backend():
    """AnyIO backend for asyncio (strict mode compatibility)"""
    return "asyncio"


# ========================================
# Event Loop Fixture: Function-Scoped (Phase VII-3)
# ========================================
# Function-scoped event loop for test isolation
# - Each test gets fresh event loop = no state pollution
# - Matches function-scoped db_engine for consistency
# - Fixes unit + regression interference issue


@pytest.fixture(scope="function")
def event_loop():
    """
    Function-scoped event loop for test isolation (Phase VII-3 fix)

    Why function-scope:
    - Session-scope causes state pollution between unit/regression tests
    - Each test gets fresh event loop = clean async state
    - Prevents "Event loop is closed" errors in combined test runs

    Trade-off:
    - Slightly slower (new loop per test)
    - But guarantees test isolation (더 중요함)

    Lifecycle:
    - Created fresh for each test function
    - Closed after test completes
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ========================================
# Function-Scoped Engine (Phase VII-3: Test Isolation)
# ========================================
@pytest.fixture(scope="function")
async def db_engine(event_loop):
    """
    Function-scoped AsyncEngine (Phase VII-3: Test Isolation)

    Why function-scope:
    - Matches function-scoped event_loop (prevents scope mismatch)
    - NullPool = no connection pooling overhead
    - Each test gets clean DB connection state
    - event_loop 의존: 정리 순서 보장 (db_engine → event_loop)

    SB-01 compliant: search_path="shared,kis_beta,public"
    """
    _ = event_loop  # 명시적 의존성 (정리 순서 보장)
    db_url = DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(
        db_url,
        poolclass=NullPool,  # Test isolation (no connection reuse)
        future=True,
        connect_args={
            "server_settings": {"search_path": "shared,kis_beta,public"},  # SB-01 + shared schema
            "prepared_statement_cache_size": 0,  # CRITICAL: Disable prepared statement cache (spec→specs migration fix)
        },
    )
    yield engine
    # Function-scope: 각 테스트 후 엔진 정리
    await engine.dispose()


# ========================================
# Phase II: DB Session (Function Scope)
# ========================================
@pytest.fixture
async def db_session(db_engine: AsyncEngine):
    """
    Function-scoped AsyncSession (clean per test)

    - Injects AsyncSession for async SQLAlchemy operations
    - Auto-rollback on fixture teardown (test isolation)
    - SB-01 compliant (search_path from engine)
    """
    SessionLocal = async_sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# ========================================
# HTTP Client with LifespanManager (FastAPI startup/shutdown 보장)
# ========================================
@pytest.fixture
async def http_client(event_loop):
    """
    AsyncClient with LifespanManager (FastAPI startup/shutdown 보장)

    Phase VII-3 Fix: event_loop 명시적 의존
    - event_loop fixture에 의존하여 정리 순서 보장
    - http_client 정리 → event_loop 정리 순서로 실행

    LifespanManager 패턴:
    - asgi-lifespan으로 FastAPI startup/shutdown events 명시적 트리거
    - httpx는 lifespan 파라미터를 지원하지 않음 (공식 문서 확인)
    - 테스트 클라이언트는 ASGITransport(app=manager.app) 사용
    - lifespan 상태 공유는 표준 ASGI 규격의 state를 따름
    - CI 환경 고려: timeout=30s (로컬 환경에서는 10s로 충분, CI는 Docker 오버헤드로 추가 시간 필요)

    출처:
    - https://www.python-httpx.org/advanced/#calling-into-python-web-apps
    - https://fastapi.tiangolo.com/advanced/testing-events/
    - https://github.com/florimondmanca/asgi-lifespan

    결과:
    - FastAPI lifespan events 정상 작동 ✅
    - DB 초기화, 카탈로그 캐시 warming 보장 ✅
    - Test isolation 보장 ✅
    """
    _ = event_loop  # 명시적 의존성 (정리 순서 보장)
    async with LifespanManager(app, startup_timeout=30, shutdown_timeout=30) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver", follow_redirects=True
        ) as client:
            yield client


# ========================================
# Backward Compatibility (Legacy Tests)
# ========================================
# Keep async_session alias for existing tests
async_session = db_session

# Keep async_client alias for existing tests
async_client = http_client

# ========================================
# Synchronous Client (Legacy Integration Tests)
# ========================================
@pytest.fixture
def client():
    """
    Synchronous TestClient for legacy integration tests.

    Why sync TestClient:
    - Many existing integration tests use sync methods (def test_xxx)
    - TestClient wraps async app and handles event loop internally
    - Compatible with both sync and async FastAPI endpoints

    Note: For new tests, prefer async_client/http_client fixtures
    """
    from starlette.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client


# ========================================
# Catalog Fixture (for tests requiring catalog data)
# ========================================
@pytest.fixture
def catalog_initialized():
    """
    Initialize catalog cache for tests that need catalog data

    - Zero-Mock compliant: loads real catalog from JSON
    - Use this fixture for tests that depend on catalog items
    """
    from kis_estimator_core.services.catalog_service import get_catalog_service

    service = get_catalog_service()
    service.initialize_cache()
    return service


# ========================================
# SB-05: Skip Decorators
# ========================================
requires_db = pytest.mark.skipif(
    not HAS_POSTGRES,
    reason="SB-05: PostgreSQL not available (DATABASE_URL not postgresql://)",
)

requires_server = pytest.mark.skipif(
    not HAS_REAL_SERVER,
    reason="SB-05: Real server not available (KIS_REAL_SERVER_URL not set)",
)
