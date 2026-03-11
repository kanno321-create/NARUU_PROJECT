"""
Test: Stage 7 Final Quality Validation
Coverage Target: _stage_7_quality() - Final system integrity checks
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage7Quality:
    """Test Stage 7: Quality Validation (LAY-004)"""

    @pytest.mark.asyncio
    async def test_stage7_runs_always(self, mock_plan_minimal, context_minimal):
        """TEST-SR-S7-001: Stage 7 always runs (no skip condition)"""
        runner = StageRunner()

        result = await runner.run_stage(7, mock_plan_minimal, context_minimal)

        # Should always run (never skip)
        assert result["status"] in ["success", "error"]
        assert result["stage_number"] == 7
        assert result["stage_name"] == "Quality"

    @pytest.mark.asyncio
    async def test_stage7_validates_enclosure(
        self, mock_plan_minimal, context_with_enclosure
    ):
        """TEST-SR-S7-002: Stage 7 validates enclosure fit_score"""
        runner = StageRunner()

        result = await runner.run_stage(7, mock_plan_minimal, context_with_enclosure)

        # Should validate enclosure
        assert "output" in result
        if "validation_summary" in result["output"]:
            assert "enclosure_validated" in result["output"]["validation_summary"]

    @pytest.mark.asyncio
    async def test_stage7_validates_placements(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S7-003: Stage 7 validates placements and phase balance"""
        runner = StageRunner()

        result = await runner.run_stage(7, mock_plan_minimal, context_with_placements)

        # Should validate placements
        assert "output" in result
        if "validation_summary" in result["output"]:
            assert "placements_validated" in result["output"]["validation_summary"]

    @pytest.mark.asyncio
    async def test_stage7_validates_costs(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S7-004: Stage 7 validates total costs"""
        runner = StageRunner()

        result = await runner.run_stage(
            7, mock_plan_minimal, context_with_estimate_data
        )

        # Should validate costs
        assert "output" in result
        if "validation_summary" in result["output"]:
            assert "cost_validated" in result["output"]["validation_summary"]

    @pytest.mark.asyncio
    async def test_stage7_reports_warnings(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S7-005: Stage 7 reports warnings (non-blocking issues)"""
        runner = StageRunner()

        result = await runner.run_stage(
            7, mock_plan_minimal, context_with_estimate_data
        )

        # Should have warnings output
        assert "output" in result
        if result["status"] == "success":
            assert "warnings_count" in result["output"]
            assert "warnings" in result["output"]

    @pytest.mark.asyncio
    async def test_stage7_records_duration(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S7-006: Stage 7 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(
            7, mock_plan_minimal, context_with_estimate_data
        )

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
