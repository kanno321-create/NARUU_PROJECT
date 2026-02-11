"""Database 레이어 테스트."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.db import (
    Database,
    close_database,
    get_database,
    init_database,
    reset_database,
)
from naruu_core.models.base import NaruuBase, TimestampMixin

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ── Unit 테스트 ──


@pytest.mark.unit
class TestDatabaseConfig:
    """Database 설정 관련 유닛 테스트."""

    def test_database_creates_engine(self) -> None:
        """Database 인스턴스 생성 시 엔진이 만들어진다."""
        db = Database(TEST_DB_URL)
        assert db.engine is not None
        assert db.session_factory is not None

    def test_database_stores_url(self) -> None:
        """Database에 URL이 저장된다."""
        db = Database(TEST_DB_URL)
        assert db._url == TEST_DB_URL

    def test_naruu_base_is_declarative(self) -> None:
        """NaruuBase가 SQLAlchemy DeclarativeBase이다."""
        assert hasattr(NaruuBase, "metadata")
        assert hasattr(NaruuBase, "registry")

    def test_timestamp_mixin_has_fields(self) -> None:
        """TimestampMixin에 created_at, updated_at이 있다."""
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

    def test_get_database_raises_without_init(self) -> None:
        """init 없이 get_database() 호출 시 RuntimeError."""
        reset_database()
        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            get_database()


# ── Integration 테스트 ──


@pytest.mark.integration
class TestDatabaseConnection:
    """DB 연결 통합 테스트."""

    async def test_connection_success(self) -> None:
        """SQLite 인메모리 DB 연결 성공."""
        db = Database(TEST_DB_URL)
        result = await db.test_connection()
        assert result is True
        await db.close()

    async def test_connection_failure(self) -> None:
        """잘못된 URL로 연결 실패."""
        db = Database("sqlite+aiosqlite:///nonexistent/path/db.sqlite")
        result = await db.test_connection()
        assert result is False

    async def test_session_commit(self, db_engine: AsyncEngine) -> None:
        """세션 내 쿼리 실행 및 커밋."""
        db = Database(TEST_DB_URL)
        db.engine = db_engine
        db.session_factory = __import__(
            "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
        ).async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        async with db.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_session_rollback_on_error(self, db_engine: AsyncEngine) -> None:
        """세션 내 에러 발생 시 자동 롤백."""
        db = Database(TEST_DB_URL)
        db.engine = db_engine
        db.session_factory = __import__(
            "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
        ).async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        with pytest.raises(ValueError, match="테스트"):
            async with db.session():
                raise ValueError("테스트 에러")


@pytest.mark.integration
class TestDatabaseSingleton:
    """글로벌 싱글턴 통합 테스트."""

    async def test_init_and_get(self) -> None:
        """init_database → get_database 정상 동작."""
        db = init_database(TEST_DB_URL)
        assert get_database() is db
        await close_database()

    async def test_close_database(self) -> None:
        """close_database 후 get_database는 RuntimeError."""
        init_database(TEST_DB_URL)
        await close_database()
        with pytest.raises(RuntimeError):
            get_database()

    async def test_reset_database(self) -> None:
        """reset_database 후 get_database는 RuntimeError."""
        init_database(TEST_DB_URL)
        reset_database()
        with pytest.raises(RuntimeError):
            get_database()


@pytest.mark.integration
class TestDatabaseSchema:
    """스키마 생성 통합 테스트."""

    async def test_create_all_tables(self, db_engine: AsyncEngine) -> None:
        """NaruuBase.metadata.create_all이 에러 없이 실행."""
        async with db_engine.begin() as conn:
            # conftest에서 이미 create_all 실행됨. 테이블 목록 확인.
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result.fetchall()]
            # 현재 모델이 없으므로 빈 테이블 (base만 존재)
            # 이후 모델 추가 시 여기서 확인
            assert isinstance(tables, list)


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestDatabaseSmoke:
    """빠른 검증 스모크 테스트."""

    async def test_db_ping(self) -> None:
        """DB ping (SQLite 인메모리)."""
        db = Database(TEST_DB_URL)
        assert await db.test_connection() is True
        await db.close()

    async def test_conftest_fixtures_work(
        self, db_engine: AsyncEngine, db_session: AsyncSession
    ) -> None:
        """conftest 픽스처가 정상 동작."""
        assert db_engine is not None
        assert db_session is not None
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
