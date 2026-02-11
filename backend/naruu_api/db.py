"""
NARUU Tourism Platform - Database Module
Async SQLAlchemy connection using asyncpg for PostgreSQL (Supabase)
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text, MetaData
from contextlib import asynccontextmanager
import logging
import ssl
import os

from naruu_api.config import config

logger = logging.getLogger(__name__)

_db_available = False

# Convert postgres:// to postgresql+asyncpg://
db_url = config.DATABASE_URL
if "?sslmode=" in db_url:
    db_url = db_url.split("?sslmode=")[0]
elif "&sslmode=" in db_url:
    db_url = db_url.replace("&sslmode=require", "").replace("&sslmode=disable", "")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Railway environment detection
is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
is_remote_db = "railway" in db_url.lower() or "proxy.rlwy.net" in db_url.lower()

# Connect args with NARUU schema
connect_args = {
    "server_settings": {
        "search_path": "naruu,public"
    },
    "prepared_statement_cache_size": 0,
}

# SSL for Railway
if is_railway and is_remote_db:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
    logger.info("Railway SSL mode enabled")

engine: AsyncEngine = create_async_engine(
    db_url,
    echo=config.DB_ECHO,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

metadata = MetaData(schema="naruu")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> dict:
    """Check database connectivity"""
    import time
    try:
        start = time.perf_counter()
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        latency_ms = (time.perf_counter() - start) * 1000
        return {"status": "ok", "connected": True, "latency_ms": round(latency_ms, 2)}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "error", "connected": False, "error": str(e)}


async def init_db() -> None:
    """Initialize database and verify connectivity"""
    global _db_available
    try:
        health = await check_db_health()
        if health["status"] == "ok":
            logger.info(f"Database connected (latency: {health.get('latency_ms', 0):.2f}ms)")
            _db_available = True
        else:
            logger.warning(f"Database connection failed: {health.get('error')}")
            _db_available = False
    except Exception as e:
        logger.warning(f"Database init error: {e}")
        _db_available = False


def is_db_available() -> bool:
    return _db_available


async def close_db() -> None:
    """Close database connection pool"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing DB: {e}")


@asynccontextmanager
async def db_transaction():
    """Transaction context manager with auto-commit/rollback"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
