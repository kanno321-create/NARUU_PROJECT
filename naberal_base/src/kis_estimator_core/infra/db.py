"""
Database connection and session management (Async SQLAlchemy + asyncpg)

REBUILD Phase C (T2): DB 드라이버 단일화
- AsyncEngine + asyncpg only
- DATABASE_URL single source of truth
- Supabase PostgreSQL (Pooler or Direct)
- UTC timezone enforcement
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import QueuePool

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration handler (Async only)"""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")

        if not self.database_url:
            raise_error(ErrorCode.E_INTERNAL, "DATABASE_URL not configured")

        self._parse_url()
        self._convert_to_async_url()

    def _parse_url(self):
        """Parse database URL to determine type and settings"""
        parsed = urlparse(self.database_url)
        self.db_type = parsed.scheme.split("+")[0]  # Remove driver suffix

        # Determine if PostgreSQL
        self.is_postgres = self.db_type in ["postgresql", "postgres"]

    def _convert_to_async_url(self):
        """Convert sync URL to async URL (postgresql+asyncpg://)"""
        if self.is_postgres:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace(
                    "postgres://", "postgresql+asyncpg://", 1
                )
            elif self.database_url.startswith("postgresql://"):
                self.database_url = self.database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            elif not self.database_url.startswith("postgresql+asyncpg://"):
                raise_error(
                    ErrorCode.E_INTERNAL,
                    f"Unsupported PostgreSQL URL format: {self.database_url[:30]}...",
                )
        else:
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Only PostgreSQL is supported (got: {self.db_type})",
            )

    def get_engine_kwargs(self) -> dict:
        """Get engine configuration for PostgreSQL with Supabase SB-01 compliance"""
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_pre_ping": True,  # Check connection health
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "connect_args": {
                # ROOT CAUSE FIX: Disable asyncpg prepared statement cache
                # Issue: asyncpg cached old schema before price column was added
                # Solution: Set cache size to 0 to force fresh schema introspection
                "prepared_statement_cache_size": 0,
                "statement_cache_size": 0,
                "server_settings": {
                    "search_path": "kis_beta,public"  # SB-01: Schema search path enforcement
                }
            },
        }


class Database:
    """Async Database connection manager"""

    def __init__(self, database_url: str | None = None):
        self.config = DatabaseConfig(database_url)
        self.engine: AsyncEngine | None = None
        self.SessionLocal: async_sessionmaker | None = None
        self._initialize()

    def _initialize(self):
        """Initialize async database engine and session factory"""
        engine_kwargs = self.config.get_engine_kwargs()

        # Create async engine
        self.engine = create_async_engine(
            self.config.database_url,
            echo=os.getenv("APP_DEBUG", "false").lower() == "true",
            **engine_kwargs,
        )

        # Set UTC timezone for PostgreSQL connections
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_timezone(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("SET timezone='UTC'")
            cursor.close()

        # Create async session factory
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    def get_session(self) -> AsyncSession:
        """Get a new async database session"""
        if not self.SessionLocal:
            raise_error(ErrorCode.E_INTERNAL, "Database not initialized")
        return self.SessionLocal()

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            async with db.session_scope() as session:
                await session.execute(...)
        """
        session = self.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def test_connection(self) -> bool:
        """Test database connection (async)"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()


# Global database instance (singleton pattern)
_db_instance: Database | None = None


def get_db_instance() -> Database:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


async def close_db_instance():
    """Close and reset global database instance (for test cleanup)"""
    global _db_instance
    if _db_instance is not None:
        await _db_instance.close()
        _db_instance = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            return await db.execute(...)
    """
    db = get_db_instance()
    async with db.session_scope() as session:
        yield session


# Utility functions for common queries
async def execute_query(query: str, params: dict | None = None) -> list:
    """Execute a raw SQL query and return results (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchall()


async def execute_scalar(query: str, params: dict | None = None):
    """Execute a raw SQL query and return scalar result (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(text(query), params or {})
        return result.scalar()


# Health check function
async def check_database_health() -> dict:
    """Check database health and return status (async)"""
    db = get_db_instance()

    health = {
        "status": "unknown",
        "database_type": db.config.db_type,
        "database_url": (
            db.config.database_url.split("@")[-1]
            if "@" in db.config.database_url
            else "local"
        ),
        "connected": False,
        "tables": [],
        "timezone": None,
        "transaction_test": False,
    }

    try:
        # Test connection
        health["connected"] = await db.test_connection()

        if health["connected"]:
            # Get timezone setting
            tz_result = await execute_scalar("SHOW timezone")
            health["timezone"] = tz_result

            # Test timezone UTC enforcement
            health["timezone_utc"] = tz_result.upper() == "UTC"

            # Get table count
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """

            tables = await execute_query(query)
            health["tables"] = [t[0] for t in tables]
            health["table_count"] = len(health["tables"])

            # Test transaction roundtrip
            try:
                async with db.session_scope() as session:
                    await session.execute(text("SELECT 1"))
                health["transaction_test"] = True
            except Exception:
                health["transaction_test"] = False

            health["status"] = "healthy" if health["table_count"] > 0 else "empty"
        else:
            health["status"] = "disconnected"

    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)

    return health
