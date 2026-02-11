"""NARUU 테스트 인프라 — 공통 픽스처 및 마커."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from naruu_core.models.base import NaruuBase
from naruu_core.models.user import User  # noqa: F401 — metadata 등록 필수


# -- SQLite 기반 테스트 DB (PostgreSQL 불필요) --

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """테스트용 인메모리 SQLite 엔진. 함수마다 새 DB."""
    engine = create_async_engine(
        TEST_DB_URL,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(NaruuBase.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(NaruuBase.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """테스트용 DB 세션. 자동 롤백으로 격리."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
def _reset_deps() -> None:
    """매 테스트마다 DI 싱글턴 리셋."""
    from naruu_api.deps import reset_all
    from naruu_core.db import reset_database

    from naruu_core.auth.middleware import reset_jwt_handler

    reset_all()
    reset_database()
    reset_jwt_handler()
