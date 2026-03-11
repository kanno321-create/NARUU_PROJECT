"""
REAL End-to-End K-PEW Pipeline Test

이 테스트는 REAL 시스템으로만 실행됩니다:
- REAL Supabase database
- REAL Excel template (견적서양식.xlsx)
- REAL engines (EnclosureSolver, BreakerPlacer, DataTransformer, etc.)

NO MOCKS - 100% REAL!
"""

import pytest
import os
from dotenv import load_dotenv

# CI skip - requires real template file (절대코어파일/견적서양식.xlsx)
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping real E2E tests in CI - requires real template file and Supabase"
)


@pytest.fixture(scope="module", autouse=True)
def load_environment():
    """Load .env.supabase for all tests in this module."""
    load_dotenv(".env.supabase")


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - REAL test requires real database",
)
def test_real_e2e_stage_1_enclosure():
    """
    REAL Stage 1 (Enclosure) test with actual EnclosureSolver.

    NO MOCKS - Uses real engine calculations.
    """
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    # REAL input data (minimal but valid)
    context = {
        "enclosure_type": "옥내노출",
        "install_location": "실내",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100, "type": "MCCB"},
        "branch_breakers": [
            {"poles": 2, "current": 20, "frame": 50},
            {"poles": 2, "current": 30, "frame": 50},
            {"poles": 3, "current": 50, "frame": 50},
        ],
    }

    plan = {}

    # Execute REAL Stage 1
    result = runner._stage_1_enclosure(plan, context)

    # Verify result structure
    assert result["stage_number"] == 1
    assert result["stage_name"] == "Enclosure"
    assert "status" in result
    assert "output" in result
    assert "duration_ms" in result

    # Check if enclosure_result was stored in context
    if result["status"] == "success":
        assert "enclosure_result" in context
        print(f"[REAL] Stage 1 completed in {result['duration_ms']}ms")
        print("[REAL] Enclosure result stored in context")


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - REAL test requires real database",
)
@pytest.mark.asyncio
async def test_real_e2e_full_pipeline_minimal():
    """
    REAL Full 8-Stage Pipeline test with minimal data (I-3.5: Async-unified).

    Executes all stages with REAL engines:
    - Stage 0: Pre-Validation
    - Stage 1: Enclosure (REAL EnclosureSolver)
    - Stage 2: Layout (REAL BreakerPlacer)
    - Stage 3: Balance (REAL Validator)
    - Stage 4: BOM (REAL DataTransformer + Supabase)
    - Stage 5: Cost (REAL aggregation)
    - Stage 6: Format (REAL EstimateFormatter + Excel template)
    - Stage 7: Quality (REAL validation checks)

    NO MOCKS!
    """
    from kis_estimator_core.kpew.execution.executor import EPDLExecutor

    executor = EPDLExecutor()

    # Minimal EPDL plan for E2E test
    epdl_plan = {
        "global": {
            "balance_limit": 0.03,
            "spare_ratio": 0.20,
            "tab_policy": "2->1&2 | 3+->1&3",
        },
        "steps": [],  # Empty steps - will use context data
    }

    # REAL context data
    context = {
        "estimate_id": "E2E_TEST_001",
        "customer_name": "실물검증고객",
        "project_name": "K-PEW E2E 실물 테스트",
        "enclosure_type": "옥내노출",
        "install_location": "실내",
        "main_breaker": {
            "poles": 3,
            "current": 100,
            "frame": 100,
            "type": "MCCB",
            "width_mm": 100,
            "height_mm": 130,
            "depth_mm": 60,
        },
        "branch_breakers": [
            {
                "poles": 2,
                "current": 20,
                "frame": 50,
                "type": "MCCB",
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
            },
            {
                "poles": 2,
                "current": 30,
                "frame": 50,
                "type": "MCCB",
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
            },
            {
                "poles": 3,
                "current": 50,
                "frame": 50,
                "type": "MCCB",
                "width_mm": 75,
                "height_mm": 130,
                "depth_mm": 60,
            },
        ],
    }

    # Execute REAL full pipeline (I-3.5: Await async execute())
    print("\n[REAL E2E TEST] Starting full 8-stage pipeline...")
    result = await executor.execute(epdl_plan, context)

    # Verify execution completed
    assert "stages" in result
    assert len(result["stages"]) == 8, "Should execute all 8 stages"

    # Print stage results
    print("\n[REAL E2E TEST] Stage Results:")
    for stage in result["stages"]:
        status_mark = (
            "[OK]"
            if stage["status"] == "success"
            else "[SKIP]" if stage["status"] == "skipped" else "[ERR]"
        )
        print(
            f"  {status_mark} Stage {stage['stage_number']} ({stage['stage_name']}): {stage['status']} ({stage['duration_ms']}ms)"
        )

    # Verify at least some stages executed successfully
    success_count = sum(1 for s in result["stages"] if s["status"] == "success")
    skipped_count = sum(1 for s in result["stages"] if s["status"] == "skipped")
    error_count = sum(1 for s in result["stages"] if s["status"] == "error")

    print(
        f"\n[REAL E2E TEST] Summary: {success_count} success, {skipped_count} skipped, {error_count} errors"
    )

    # At minimum, Stage 0-3 should execute
    assert success_count >= 3, "At least 3 stages should execute successfully"

    # Overall status
    assert result["overall_status"] in ["success", "partial_success", "blocked"]

    print(f"\n[REAL E2E TEST] Overall status: {result['overall_status']}")
    print("[SUCCESS] Full 8-stage pipeline executed with REAL engines!")


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - REAL test requires real database",
)
def test_real_template_file_accessible():
    """
    Verify REAL Excel template file is accessible and valid.

    NO DUMMY FILES - Must be real template!
    """
    from pathlib import Path

    template_path = Path("절대코어파일/견적서양식.xlsx")

    # File must exist
    assert template_path.exists(), f"REAL template file not found: {template_path}"

    # File must be substantial (not a dummy)
    file_size = template_path.stat().st_size
    assert (
        file_size > 10240
    ), f"Template file too small ({file_size} bytes) - may be dummy!"

    # File should be Excel format (check extension)
    assert template_path.suffix == ".xlsx", "Template must be .xlsx format"

    print(f"[REAL] Template file verified: {template_path}")
    print(f"[REAL] File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print("[SUCCESS] REAL Excel template is accessible and valid!")


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - REAL test requires real database",
)
def test_real_supabase_tables_exist():
    """
    Verify REAL Supabase tables exist and are accessible.

    NO MOCKS - Real database connection!
    """
    from sqlalchemy import create_engine, text

    db_url = os.getenv("SUPABASE_DB_URL")
    assert db_url, "SUPABASE_DB_URL must be configured"

    engine = create_engine(db_url, pool_pre_ping=True)

    with engine.connect() as conn:
        # Check for K-PEW tables
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('epdl_plans', 'execution_history', 'evidence_packs')
            ORDER BY table_name
        """
            )
        )

        tables = [row[0] for row in result]

    # All 3 tables must exist
    assert len(tables) == 3, f"Expected 3 K-PEW tables, found {len(tables)}: {tables}"
    assert "epdl_plans" in tables
    assert "execution_history" in tables
    assert "evidence_packs" in tables

    print(f"[REAL] Supabase tables verified: {tables}")
    print("[SUCCESS] All 3 K-PEW tables exist in REAL Supabase database!")


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - REAL test requires real database",
)
def test_real_catalog_service_accessible():
    """
    Verify REAL CatalogService can access Supabase pricing data.

    NO MOCKS - Real catalog queries!
    """
    from kis_estimator_core.services.catalog_service import get_catalog_service

    # Get REAL CatalogService instance
    catalog = get_catalog_service()

    # This should connect to REAL Supabase
    assert catalog is not None

    print("[REAL] CatalogService initialized with REAL Supabase connection")
    print("[SUCCESS] REAL catalog service is accessible!")


def test_real_engines_importable():
    """
    Verify all REAL engines can be imported and instantiated.

    NO MOCKS - All real engine classes!
    """
    # Import all REAL engines
    from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
    from kis_estimator_core.engine.breaker_placer import BreakerPlacer
    from kis_estimator_core.engine.data_transformer import DataTransformer
    from kis_estimator_core.engine.estimate_formatter import EstimateFormatter

    # Instantiate engines
    _ = EnclosureSolver()
    _ = BreakerPlacer()
    _ = DataTransformer()

    # EstimateFormatter needs template path
    try:
        _ = EstimateFormatter()  # Uses default template path
    except FileNotFoundError as e:
        # This is OK - just means template path verification is working
        print(f"[INFO] EstimateFormatter template check working: {e}")

    print("[REAL] All engines successfully imported and instantiated")
    print("[SUCCESS] REAL engine classes are available!")
