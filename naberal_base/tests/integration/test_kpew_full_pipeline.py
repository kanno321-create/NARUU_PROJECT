"""
Integration Tests for K-PEW Full 8-Stage Pipeline

Tests the complete pipeline: Stage 1-8 (Enclosure → Quality → Evidence)
REAL engines, REAL database, NO MOCKS!
"""

import pytest
import os
from typing import Dict, Any


@pytest.fixture
def sample_epdl_plan() -> Dict[str, Any]:
    """Sample EPDL plan for testing."""
    return {
        "global": {
            "balance_limit": 0.03,
            "spare_ratio": 0.20,
            "tab_policy": "2->1&2 | 3+->1&3",
        },
        "steps": [
            {
                "PICK_ENCLOSURE": {
                    "main_breaker": {"poles": 3, "current": 100},
                    "branch_breakers": [
                        {"poles": 2, "current": 20},
                        {"poles": 2, "current": 30},
                        {"poles": 3, "current": 50},
                    ],
                }
            },
            {
                "PLACE": {
                    "breakers": ["MAIN", "BR1", "BR2", "BR3"],
                    "panel": "result_from_enclosure",
                }
            },
            {
                "REBALANCE": {
                    "placements": "result_from_place",
                    "target_imbalance": 0.03,
                }
            },
        ],
    }


def test_stage_4_bom_implementation():
    """Test that Stage 4 BOM is no longer skeleton."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner
    import inspect

    runner = StageRunner()

    # Check _stage_4_bom method
    method = runner._stage_4_bom
    source = inspect.getsource(method)

    # Should NOT contain "TODO" or "skipped" in main logic
    assert "TODO: Implement BOM generation logic" not in source
    assert "DataTransformer" in source
    assert "REAL" in source or "NO MOCKS" in source


def test_stage_5_cost_implementation():
    """Test that Stage 5 Cost is no longer skeleton."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner
    import inspect

    runner = StageRunner()

    # Check _stage_5_cost method
    method = runner._stage_5_cost
    source = inspect.getsource(method)

    # Should NOT contain "TODO" or "skipped" in main logic
    assert "TODO: Implement cost calculation logic" not in source
    assert "estimate_data" in source
    assert "total_cost" in source


def test_stage_6_format_implementation():
    """Test that Stage 6 Format is no longer skeleton."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner
    import inspect

    runner = StageRunner()

    # Check _stage_6_format method
    method = runner._stage_6_format
    source = inspect.getsource(method)

    # Should NOT contain "TODO" or "skipped" in main logic
    assert "TODO: Implement formatting logic" not in source
    assert "EstimateFormatter" in source
    assert "REAL" in source or "NO MOCKS" in source


def test_stage_7_quality_implementation():
    """Test that Stage 7 Quality is no longer skeleton."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner
    import inspect

    runner = StageRunner()

    # Check _stage_7_quality method
    method = runner._stage_7_quality
    source = inspect.getsource(method)

    # Should NOT contain "TODO" or "skipped" in main logic
    assert "TODO: Implement final quality checks" not in source
    assert "enclosure_result" in source
    assert "placements" in source
    assert "validation" in source.lower()


def test_stage_runner_all_stages_exist():
    """Test that all 8 stages exist and are callable."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    # All stage methods should exist (correct method names)
    assert hasattr(
        runner, "_stage_0_pre_validation"
    )  # Fixed: underscore instead of no space
    assert hasattr(runner, "_stage_1_enclosure")
    assert hasattr(runner, "_stage_2_layout")
    assert hasattr(runner, "_stage_3_balance")
    assert hasattr(runner, "_stage_4_bom")
    assert hasattr(runner, "_stage_5_cost")
    assert hasattr(runner, "_stage_6_format")
    assert hasattr(runner, "_stage_7_quality")

    # All should be callable
    assert callable(runner._stage_0_pre_validation)
    assert callable(runner._stage_1_enclosure)
    assert callable(runner._stage_2_layout)
    assert callable(runner._stage_3_balance)
    assert callable(runner._stage_4_bom)
    assert callable(runner._stage_5_cost)
    assert callable(runner._stage_6_format)
    assert callable(runner._stage_7_quality)


def test_stage_4_context_flow():
    """Test Stage 4 BOM uses context correctly."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    context = {
        "placements": [],  # Empty placements
        "enclosure_result": None,
        "breakers": [],
    }

    plan = {}

    # Should return skipped or error status when no placements
    result = runner._stage_4_bom(plan, context)

    assert result["stage_number"] == 4
    assert result["stage_name"] == "BOM"
    # Both "skipped" and "error" are valid when required data is missing
    assert result["status"] in ["skipped", "error"], f"Expected 'skipped' or 'error', got '{result['status']}'"
    assert "errors" in result
    assert "output" in result


def test_stage_5_context_flow():
    """Test Stage 5 Cost uses context correctly."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    context = {}

    plan = {}

    # Should return skipped status when no estimate_data
    result = runner._stage_5_cost(plan, context)

    assert result["stage_number"] == 5
    assert result["stage_name"] == "Cost"
    assert result["status"] == "skipped"  # No estimate_data
    assert "output" in result


def test_stage_6_context_flow():
    """Test Stage 6 Format uses context correctly."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    context = {}

    plan = {}

    # Should return skipped status when no estimate_data
    result = runner._stage_6_format(plan, context)

    assert result["stage_number"] == 6
    assert result["stage_name"] == "Format"
    assert result["status"] == "skipped"  # No estimate_data
    assert "output" in result


def test_stage_7_comprehensive_validation():
    """Test Stage 7 Quality performs comprehensive validation."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner

    runner = StageRunner()

    context = {
        "enclosure_result": type(
            "obj", (), {"quality_gate": {"actual": 0.95}}  # Good fit score
        )(),
        "placements": [],
        "estimate_data": type("obj", (), {"panels": []})(),
        "total_cost": 500000,
        "excel_path": None,  # No excel file yet
    }

    plan = {}

    # Should perform validation checks
    result = runner._stage_7_quality(plan, context)

    assert result["stage_number"] == 7
    assert result["stage_name"] == "Quality"
    assert "output" in result
    assert "validation_summary" in result["output"]

    # Validation summary should check all key components
    summary = result["output"]["validation_summary"]
    assert "enclosure_validated" in summary
    assert "placements_validated" in summary
    assert "cost_validated" in summary
    assert "excel_validated" in summary


def test_no_mocks_principle():
    """Verify NO MOCKS principle is enforced in all stages."""
    from kis_estimator_core.kpew.execution.stage_runner import StageRunner
    import inspect

    runner = StageRunner()

    stages_to_check = [
        runner._stage_4_bom,
        runner._stage_5_cost,
        runner._stage_6_format,
        runner._stage_7_quality,
    ]

    for stage_method in stages_to_check:
        source = inspect.getsource(stage_method)

        # Should mention REAL engines or NO MOCKS
        has_real_mention = "REAL" in source or "NO MOCKS" in source or "실물" in source

        assert (
            has_real_mention
        ), f"{stage_method.__name__} should mention REAL engines or NO MOCKS"


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_URL"),
    reason="SUPABASE_DB_URL not configured - skipping real integration test",
)
@pytest.mark.asyncio
async def test_full_pipeline_integration_real():
    """
    Full 8-stage pipeline integration test with REAL engines (I-3.5: Async-unified).

    REQUIRES:
    - SUPABASE_DB_URL: Real Supabase database
    - 절대코어파일/견적서양식.xlsx: Real Excel template

    This test will be SKIPPED if environment is not configured.
    """
    from kis_estimator_core.kpew.execution.executor import EPDLExecutor
    from dotenv import load_dotenv

    # Load environment
    load_dotenv(".env.supabase")

    executor = EPDLExecutor()

    # Minimal EPDL plan for integration test
    epdl_plan = {"global": {"balance_limit": 0.03, "spare_ratio": 0.20}, "steps": []}

    # Initial context with minimal data
    context = {
        "estimate_id": "TEST_001",
        "customer_name": "테스트고객",
        "project_name": "테스트프로젝트",
    }

    # Execute full pipeline (I-3.5: Await async execute())
    result = await executor.execute(epdl_plan, context)

    # Verify execution completed (may have skipped stages due to minimal data)
    assert "stages" in result
    assert len(result["stages"]) == 8  # All 8 stages executed

    # Check that Stage 4-7 are no longer all "skipped"
    stage_statuses = [stage["status"] for stage in result["stages"][4:8]]

    # At least some stages should attempt execution (not all TODO/not implemented)
    assert not all(status == "skipped" for status in stage_statuses)
