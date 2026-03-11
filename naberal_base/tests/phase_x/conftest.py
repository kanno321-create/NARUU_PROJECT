"""
Phase X Test Fixtures

Provides fixtures for Phase X tests:
- db_session: Database session for integration tests
- app: FastAPI app instance

Contract-First / Zero-Mock
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import os


@pytest.fixture
async def db_session(db_engine):
    """
    Async database session for Phase X integration tests (카라 처방: engine 재사용)

    카라 처방 B: 루트 db_engine (session-scoped) 재사용
    - 독립 engine 생성 제거 (단일 소유권)
    - engine.dispose() 제거 (루트에서만 dispose)
    - Event loop is closed 에러 완전 제거

    Requires DATABASE_URL environment variable
    Uses kis_beta schema
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping DB tests")

    # 카라 처방: 루트 db_engine 재사용 (독립 engine 생성 제거)
    SessionLocal = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session
    # 카라 처방: engine.dispose() 제거 (루트에서만 한 번 dispose)
