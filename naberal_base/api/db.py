"""
KIS Estimator Database Module
Async SQLAlchemy connection using asyncpg for PostgreSQL
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from kis_estimator_core.core.ssot.errors import raise_error, ErrorCode
from sqlalchemy import text, MetaData
from contextlib import asynccontextmanager
import logging
import ssl
import os

from api.config import config

logger = logging.getLogger(__name__)

# Global flag for database availability (graceful degradation)
_db_available = False

# Convert postgres:// to postgresql+asyncpg://
db_url = config.DATABASE_URL
# Remove sslmode from URL if present (will be handled by connect_args)
if "?sslmode=" in db_url:
    db_url = db_url.split("?sslmode=")[0]
elif "&sslmode=" in db_url:
    db_url = db_url.replace("&sslmode=require", "").replace("&sslmode=disable", "")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Detect Railway environment and configure SSL accordingly
is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
is_remote_db = "railway" in db_url.lower() or "proxy.rlwy.net" in db_url.lower()

# Configure connect_args based on environment
connect_args = {
    "server_settings": {
        "search_path": "shared,kis_beta,public"  # SB-01: Schema search path enforcement
    },
    "prepared_statement_cache_size": 0,  # CRITICAL: Disable prepared statement cache
}

# Add SSL for Railway remote connections
if is_railway and is_remote_db:
    # Railway PostgreSQL requires SSL for external connections
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Railway uses self-signed certs
    connect_args["ssl"] = ssl_context
    logger.info("Railway SSL mode enabled for database connection")

# Create async engine with SB-01 compliance (local PostgreSQL or Supabase)
# SB-01: search_path="shared,kis_beta,public" runtime enforcement (shared schema first for catalog_items)
# Phase VII-4: QueuePool optimization for remote DB (Supabase) performance
# asyncpg는 QueuePool과 완벽히 호환됨 (이전 주석은 오류)
engine: AsyncEngine = create_async_engine(
    db_url,
    echo=config.DB_ECHO,
    poolclass=AsyncAdaptedQueuePool,  # Phase VII-4: Async-compatible connection pooling
    pool_size=20,  # 동시 연결 수 (기본 5 → 20)
    max_overflow=30,  # 추가 연결 허용 (기본 10 → 30)
    pool_pre_ping=True,  # 연결 검증 (stale connection 방지)
    pool_recycle=3600,  # 1시간마다 연결 재생성 (connection timeout 방지)
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Metadata for schema introspection
metadata = MetaData()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> dict:
    """
    Check database connection and basic health.

    Phase VII-4 optimization: Single query only (SELECT 1) for <100ms target.
    Removed timestamp query to reduce latency from ~600ms to ~50ms.

    Returns:
        dict with status, connected, latency_ms, and optional error
    """
    import time

    try:
        start = time.perf_counter()
        async with AsyncSessionLocal() as session:
            # Simple connectivity check (single query for speed)
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "status": "ok",
            "connected": True,
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
        }


async def init_db() -> None:
    """
    Initialize database connection pool and verify connectivity.
    Called on application startup.

    Railway deployment: Graceful degradation - app starts even if DB unavailable.
    DB-dependent endpoints will return 503 Service Unavailable.
    """
    global _db_available
    try:
        health = await check_db_health()
        if health["status"] == "ok":
            latency = health.get("latency_ms", 0)
            logger.info(
                f"Database connected successfully (latency: {latency:.2f}ms)"
            )
            _db_available = True
        else:
            logger.warning(f"Database connection failed: {health.get('error')}")
            logger.warning("App starting in degraded mode - DB endpoints will return 503")
            _db_available = False
    except Exception as e:
        logger.warning(f"Database initialization error: {e}")
        logger.warning("App starting in degraded mode - DB endpoints will return 503")
        _db_available = False


def is_db_available() -> bool:
    """Check if database is available for use."""
    return _db_available


async def close_db() -> None:
    """
    Close database connection pool.
    Called on application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


@asynccontextmanager
async def db_transaction():
    """
    Context manager for database transactions with automatic rollback on error.

    Usage:
        async with db_transaction() as session:
            # do work
            await session.execute(...)
            # auto-commit on exit, auto-rollback on exception
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
