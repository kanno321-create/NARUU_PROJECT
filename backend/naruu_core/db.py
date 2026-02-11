"""데이터베이스 관리 — AsyncEngine + 세션 팩토리."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class Database:
    """비동기 데이터베이스 매니저.

    SQLAlchemy AsyncEngine 기반. PostgreSQL(asyncpg) 또는 SQLite(aiosqlite) 지원.
    """

    def __init__(self, database_url: str) -> None:
        self._url = database_url
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """트랜잭션 스코프 세션. 자동 커밋/롤백."""
        async with self.session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    async def test_connection(self) -> bool:
        """DB 연결 테스트. 성공 시 True."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            return True
        except Exception as e:
            logger.error("DB 연결 실패: %s", e)
            return False

    async def close(self) -> None:
        """엔진 종료, 모든 커넥션 풀 정리."""
        await self.engine.dispose()
        logger.info("DB 엔진 종료 완료.")


# -- 글로벌 싱글턴 --

_db: Database | None = None


def get_database() -> Database:
    """글로벌 Database 인스턴스 반환. init_database() 호출 후 사용."""
    if _db is None:
        raise RuntimeError("Database가 초기화되지 않았습니다. init_database()를 먼저 호출하세요.")
    return _db


def init_database(database_url: str) -> Database:
    """글로벌 Database 인스턴스 초기화."""
    global _db
    _db = Database(database_url)
    host = database_url.split("@")[-1] if "@" in database_url else "local"
    logger.info("DB 초기화 완료: %s", host)
    return _db


async def close_database() -> None:
    """글로벌 Database 인스턴스 종료."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def reset_database() -> None:
    """테스트용 글로벌 상태 리셋."""
    global _db
    _db = None
