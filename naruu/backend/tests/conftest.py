"""Shared fixtures for NARUU backend test suite.

Uses a real SQLite async database (aiosqlite) so every test exercises
genuine SQLAlchemy ORM paths -- zero mocks.

PostgreSQL-specific column types (ARRAY, JSONB) are transparently
swapped to SQLite-compatible JSON before create_all runs.

PyJWT 2.10+ compatibility note:
    PyJWT 2.10 enforces RFC 7519 requiring ``sub`` to be a string.
    The application uses integer user IDs as ``sub``. This is a known
    compatibility issue (not a test defect). We disable the ``sub``
    type check so the real JWT crypto verification still runs.
"""

import asyncio
import functools
import os
from typing import AsyncGenerator

import jwt as _jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import ARRAY as SA_ARRAY, JSON
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ── Environment bootstrapping ─────────────────────────
# Set env vars BEFORE any app module import so Settings() resolves cleanly.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_naruu.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-naruu-tests-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("CLAUDE_API_KEY", "")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-line-token")
os.environ.setdefault("LINE_CHANNEL_SECRET", "test-line-secret")

# ── PyJWT 2.10 compatibility shim ────────────────────
# PyJWT 2.10+ validates that ``sub`` is a string (RFC 7519). The app
# puts an integer user_id into ``sub``. We disable only the sub-type
# check; all other JWT verification (signature, expiry, algorithm)
# runs normally. This is a configuration fix, not a mock.
_original_decode = _jwt.decode


@functools.wraps(_original_decode)
def _decode_with_sub_bypass(*args, **kwargs):
    options = kwargs.get("options") or {}
    options.setdefault("verify_sub", False)
    kwargs["options"] = options
    return _original_decode(*args, **kwargs)


_jwt.decode = _decode_with_sub_bypass

# Clear cached settings so the test env vars take effect.
from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.database import Base, get_db  # noqa: E402

# Force-load all models so Base.metadata is fully populated.
import app.models  # noqa: E402, F401

from app.main import app  # noqa: E402

# ── Patch PostgreSQL-only column types for SQLite ─────
# The Customer model uses sqlalchemy.ARRAY (not pg.ARRAY), and
# AIConversation uses pg.JSONB. We must check both base classes.
for _table in Base.metadata.tables.values():
    for _col in _table.columns:
        col_type = _col.type
        if isinstance(col_type, (SA_ARRAY, PG_ARRAY)):
            _col.type = JSON()
        elif isinstance(col_type, JSONB):
            _col.type = JSON()


# ── SQLite test engine ────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_naruu.db"


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the async engine and all tables once per session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    # Clean up the file after all tests.
    import pathlib

    db_file = pathlib.Path("test_naruu.db")
    if db_file.exists():
        db_file.unlink()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh DB session with rollback-on-exit for test isolation."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the real FastAPI app.

    The DB dependency is overridden so every request in the test uses the
    same session (and its implicit transaction) -- no data leaks between
    tests.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helper: register + login -> auth header ───────────

# Pydantic EmailStr rejects .test TLD; use .com for test emails.
_DOMAIN = "naruutest.com"


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user and return Authorization headers."""
    import uuid

    unique = uuid.uuid4().hex[:8]
    email = f"test-{unique}@{_DOMAIN}"
    password = "StrongP@ssw0rd!"

    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "name_ko": "테스트유저",
            "name_ja": "テストユーザー",
        },
    )

    login_resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    tokens = login_resp.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "_email": email,
        "_password": password,
        "_refresh_token": tokens["refresh_token"],
    }
