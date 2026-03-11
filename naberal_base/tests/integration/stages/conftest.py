"""
Integration Stages Fixtures
SB-01..05, Zero-Mock, Real DB/FS
"""

import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text


# Marker definition
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_db: mark test as requiring real database (skip if DB unavailable)",
    )


@pytest.fixture
async def mini_db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Mini DB fixture with real Supabase connection (카라 처방: engine 재사용)

    SB-01: search_path="kis_beta,public"
    SB-05: Skip if DATABASE_URL unavailable + reason logging

    카라 처방 B: 루트 db_engine (session-scoped) 재사용
    - 독립 engine 생성 제거 (단일 소유권)
    - engine.dispose() 제거 (루트에서만 dispose)
    - Event loop is closed 에러 완전 제거

    Provides:
    - Minimal catalog seed (5 breakers, 2 enclosures)
    - Transaction rollback capability
    - Real async session for verb execution
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.skip("DATABASE_URL not configured - real DB required (SB-05)")

    # 카라 처방: 루트 db_engine 재사용 (독립 engine 생성 제거)
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            # SB-01: Explicitly set search_path (Pooler workaround)
            await session.execute(text("SET search_path TO kis_beta, public"))

            # Verify search_path is active
            result = await session.execute(text("SELECT current_schema()"))
            schema = result.scalar()

            if schema != "kis_beta":
                pytest.skip(
                    f"Schema mismatch: expected 'kis_beta', got '{schema}' (SB-01)"
                )

            # Minimal seed verification (assume seed already exists)
            # Check if catalog tables have minimal data
            breaker_count = await session.execute(
                text("SELECT COUNT(*) FROM breakers LIMIT 1")
            )

            if breaker_count.scalar() < 5:
                pytest.skip("Insufficient catalog seed: breakers < 5 (SB-05)")

            yield session

        except Exception as e:
            pytest.skip(f"DB connection failed: {str(e)} (SB-05)")
        # 카라 처방: engine.dispose() 제거 (루트에서만 한 번 dispose)


@pytest.fixture(scope="session")
def fs_tmp(tmp_path_factory):
    """Temporary filesystem for Excel/PDF generation

    Returns:
        Path: Isolated tmp directory for evidence files
    """
    return tmp_path_factory.mktemp("evidence")


@pytest.fixture
def skip_if_no_db():
    """Skip test if DATABASE_URL not available"""
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured - integration test requires real DB")


@pytest.fixture
async def execution_context(mini_db):
    """Create ExecutionCtx with real DB session

    Returns:
        ExecutionCtx: Context with ssot, db session, logger, state
    """
    from types import SimpleNamespace
    from kis_estimator_core.engine.context import ExecutionCtx
    import logging

    logger = logging.getLogger("integration_test")
    ssot = SimpleNamespace()  # Minimal SSOT stub

    ctx = ExecutionCtx(
        ssot=ssot, db=mini_db, logger=logger, state={}  # Real async session
    )

    return ctx


@pytest.fixture
def minimal_plan_pick_enclosure():
    """Minimal plan with PICK_ENCLOSURE verb

    SSOT-based parameters (no hardcoded values)
    """
    return {
        "steps": [
            {
                "PICK_ENCLOSURE": {
                    "source": "catalog",
                    "enclosure_type": "옥내노출",
                    "material": "STEEL",
                    "thickness": "1.6T",
                }
            }
        ]
    }


@pytest.fixture
def minimal_plan_pick_and_place():
    """Minimal plan with PICK_ENCLOSURE + PLACE verbs

    Sequential execution: Stage 1 → Stage 2
    """
    return {
        "steps": [
            {
                "PICK_ENCLOSURE": {
                    "source": "catalog",
                    "enclosure_type": "옥내노출",
                    "material": "STEEL",
                    "thickness": "1.6T",
                }
            },
            {"PLACE": {"strategy": "optimal"}},
        ]
    }


@pytest.fixture
def minimal_context():
    """Minimal context for verb execution

    SSOT-compliant values + pre-seeded Stage 1/2 results for Stages 4-7
    """
    return {
        "enclosure_type": "옥내노출",
        "install_location": "지상",
        "main_breaker": {"poles": 3, "current": 100, "width_mm": 75},
        "branch_breakers": [
            {"poles": 2, "current": 30, "width_mm": 50},
            {"poles": 2, "current": 20, "width_mm": 50},
            {"poles": 3, "current": 50, "width_mm": 75},
        ],
        # Pre-seeded enclosure (Stage 1 output)
        "enclosure": {
            "code": "HB405015",
            "width_mm": 400,
            "height_mm": 500,
            "depth_mm": 150,
            "slots_total": 4,
            "fit_score": 0.92,
        },
        "dimensions": {"width_mm": 400, "height_mm": 500, "depth_mm": 150},
        # Pre-seeded placements (Stage 2 output)
        "placements": [
            {"breaker_id": "SBC-52-20A", "slot": "S1", "row": 1, "col": 1},
            {"breaker_id": "SBC-53-20A", "slot": "S2", "row": 1, "col": 2},
            {"breaker_id": "ABN-54-50A", "slot": "S3", "row": 1, "col": 3},
        ],
        "phase_loads": {"L1": 30, "L2": 20, "L3": 50},
    }
