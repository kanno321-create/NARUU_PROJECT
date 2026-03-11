"""
Unit Tests for infra/db.py
Coverage target: >70% for Database connection and session management

Zero-Mock exception: Unit tests may use unittest.mock for external database calls
to avoid requiring real database connection in CI environment.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseConfig:
    """Tests for DatabaseConfig class"""

    def test_init_without_url_raises_error(self):
        """Test that missing DATABASE_URL raises error"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with patch.dict(os.environ, {}, clear=True):
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

            with pytest.raises(EstimatorError):
                from kis_estimator_core.infra.db import DatabaseConfig

                DatabaseConfig(database_url=None)

    def test_init_with_postgres_url(self):
        """Test initialization with postgres:// URL"""
        from kis_estimator_core.infra.db import DatabaseConfig

        config = DatabaseConfig(database_url="postgres://user:pass@localhost/db")

        assert "postgresql+asyncpg://" in config.database_url
        assert config.is_postgres is True

    def test_init_with_postgresql_url(self):
        """Test initialization with postgresql:// URL"""
        from kis_estimator_core.infra.db import DatabaseConfig

        config = DatabaseConfig(database_url="postgresql://user:pass@localhost/db")

        assert "postgresql+asyncpg://" in config.database_url
        assert config.is_postgres is True

    def test_init_with_asyncpg_url(self):
        """Test initialization with postgresql+asyncpg:// URL"""
        from kis_estimator_core.infra.db import DatabaseConfig

        url = "postgresql+asyncpg://user:pass@localhost/db"
        config = DatabaseConfig(database_url=url)

        assert config.database_url == url
        assert config.is_postgres is True

    def test_non_postgres_raises_error(self):
        """Test that non-PostgreSQL URL raises error"""
        from kis_estimator_core.core.ssot.errors import EstimatorError
        from kis_estimator_core.infra.db import DatabaseConfig

        with pytest.raises(EstimatorError):
            DatabaseConfig(database_url="mysql://user:pass@localhost/db")

    def test_get_engine_kwargs_returns_dict(self):
        """Test get_engine_kwargs returns proper configuration"""
        from kis_estimator_core.infra.db import DatabaseConfig

        config = DatabaseConfig(database_url="postgresql://user:pass@localhost/db")
        kwargs = config.get_engine_kwargs()

        assert "pool_size" in kwargs
        assert "max_overflow" in kwargs
        assert "pool_timeout" in kwargs
        assert "pool_pre_ping" in kwargs
        assert kwargs["pool_pre_ping"] is True
        assert "connect_args" in kwargs

    def test_engine_kwargs_has_search_path(self):
        """Test engine kwargs includes search_path for Supabase SB-01"""
        from kis_estimator_core.infra.db import DatabaseConfig

        config = DatabaseConfig(database_url="postgresql://user:pass@localhost/db")
        kwargs = config.get_engine_kwargs()

        connect_args = kwargs["connect_args"]
        assert "server_settings" in connect_args
        assert "search_path" in connect_args["server_settings"]


class TestDatabase:
    """Tests for Database class"""

    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    def test_init_creates_engine(self, mock_sessionmaker, mock_create_engine, mock_event):
        """Test Database initialization creates engine"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database(database_url="postgresql://user:pass@localhost/db")

        mock_create_engine.assert_called_once()
        assert db.engine is not None

    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    def test_get_session_returns_session(self, mock_sessionmaker, mock_create_engine, mock_event):
        """Test get_session returns AsyncSession"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        db = Database(database_url="postgresql://user:pass@localhost/db")
        session = db.get_session()

        assert session is not None

    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    def test_get_session_without_init_raises_error(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test get_session raises error if not initialized"""
        from kis_estimator_core.core.ssot.errors import EstimatorError
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database(database_url="postgresql://user:pass@localhost/db")
        db.SessionLocal = None  # Force uninitialized state

        with pytest.raises(EstimatorError):
            db.get_session()


class TestDatabaseAsync:
    """Async tests for Database class"""

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    async def test_session_scope_commits_on_success(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test session_scope commits on successful operation"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_session = AsyncMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        db = Database(database_url="postgresql://user:pass@localhost/db")

        async with db.session_scope() as session:
            pass  # Successful operation

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    async def test_session_scope_rollbacks_on_error(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test session_scope rollbacks on error"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_session = AsyncMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        db = Database(database_url="postgresql://user:pass@localhost/db")

        with pytest.raises(ValueError):
            async with db.session_scope() as session:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    async def test_test_connection_success(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test test_connection returns True on success"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_engine.connect = MagicMock(return_value=mock_conn)
        mock_create_engine.return_value = mock_engine

        db = Database(database_url="postgresql://user:pass@localhost/db")

        result = await db.test_connection()

        assert result is True

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    async def test_test_connection_failure(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test test_connection returns False on failure"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = MagicMock()
        mock_engine.sync_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Connection failed")
        mock_create_engine.return_value = mock_engine

        db = Database(database_url="postgresql://user:pass@localhost/db")

        result = await db.test_connection()

        assert result is False

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.event")
    @patch("kis_estimator_core.infra.db.create_async_engine")
    @patch("kis_estimator_core.infra.db.async_sessionmaker")
    async def test_close_disposes_engine(
        self, mock_sessionmaker, mock_create_engine, mock_event
    ):
        """Test close disposes engine"""
        from kis_estimator_core.infra.db import Database

        # Mock event.listens_for to return a pass-through decorator
        mock_event.listens_for.return_value = lambda fn: fn

        mock_engine = AsyncMock()
        mock_engine.sync_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db = Database(database_url="postgresql://user:pass@localhost/db")

        await db.close()

        mock_engine.dispose.assert_called_once()


class TestGetDbInstance:
    """Tests for get_db_instance function"""

    @patch("kis_estimator_core.infra.db.Database")
    def test_get_db_instance_singleton(self, mock_database_class):
        """Test get_db_instance returns singleton"""
        import kis_estimator_core.infra.db as db_module

        # Reset singleton
        db_module._db_instance = None

        mock_db = MagicMock()
        mock_database_class.return_value = mock_db

        # First call creates instance
        db1 = db_module.get_db_instance()
        # Second call returns same instance
        db2 = db_module.get_db_instance()

        assert db1 is db2
        # Database constructor called only once
        mock_database_class.assert_called_once()

        # Cleanup
        db_module._db_instance = None


class TestUtilityFunctions:
    """Tests for utility functions"""

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.get_db_instance")
    async def test_execute_query(self, mock_get_db):
        """Test execute_query function"""
        from kis_estimator_core.infra.db import execute_query

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("row1",), ("row2",)]
        mock_session.execute.return_value = mock_result

        # Create async context manager
        async_ctx = AsyncMock()
        async_ctx.__aenter__.return_value = mock_session
        async_ctx.__aexit__.return_value = None
        mock_db.session_scope.return_value = async_ctx

        mock_get_db.return_value = mock_db

        result = await execute_query("SELECT * FROM test")

        assert len(result) == 2

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.get_db_instance")
    async def test_execute_scalar(self, mock_get_db):
        """Test execute_scalar function"""
        from kis_estimator_core.infra.db import execute_scalar

        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        # Create async context manager
        async_ctx = AsyncMock()
        async_ctx.__aenter__.return_value = mock_session
        async_ctx.__aexit__.return_value = None
        mock_db.session_scope.return_value = async_ctx

        mock_get_db.return_value = mock_db

        result = await execute_scalar("SELECT COUNT(*) FROM test")

        assert result == 42


class TestCheckDatabaseHealth:
    """Tests for check_database_health function"""

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.execute_query")
    @patch("kis_estimator_core.infra.db.execute_scalar")
    @patch("kis_estimator_core.infra.db.get_db_instance")
    async def test_health_check_success(
        self, mock_get_db, mock_scalar, mock_query
    ):
        """Test health check returns healthy status"""
        from kis_estimator_core.infra.db import check_database_health

        mock_db = MagicMock()
        mock_db.config.db_type = "postgresql"
        mock_db.config.database_url = "user:pass@localhost/db"
        mock_db.test_connection = AsyncMock(return_value=True)

        # Create async context manager for session_scope
        mock_session = AsyncMock()
        async_ctx = AsyncMock()
        async_ctx.__aenter__.return_value = mock_session
        async_ctx.__aexit__.return_value = None
        mock_db.session_scope.return_value = async_ctx

        mock_get_db.return_value = mock_db
        mock_scalar.return_value = "UTC"
        mock_query.return_value = [("table1",), ("table2",)]

        result = await check_database_health()

        assert result["connected"] is True
        assert result["database_type"] == "postgresql"

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.get_db_instance")
    async def test_health_check_disconnected(self, mock_get_db):
        """Test health check returns disconnected status"""
        from kis_estimator_core.infra.db import check_database_health

        mock_db = MagicMock()
        mock_db.config.db_type = "postgresql"
        mock_db.config.database_url = "user:pass@localhost/db"
        mock_db.test_connection = AsyncMock(return_value=False)

        mock_get_db.return_value = mock_db

        result = await check_database_health()

        assert result["connected"] is False
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    @patch("kis_estimator_core.infra.db.get_db_instance")
    async def test_health_check_error(self, mock_get_db):
        """Test health check returns error status on exception"""
        from kis_estimator_core.infra.db import check_database_health

        mock_db = MagicMock()
        mock_db.config.db_type = "postgresql"
        mock_db.config.database_url = "user:pass@localhost/db"
        mock_db.test_connection = AsyncMock(side_effect=Exception("Test error"))

        mock_get_db.return_value = mock_db

        result = await check_database_health()

        assert result["status"] == "error"
        assert "error" in result
