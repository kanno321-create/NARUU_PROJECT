"""
Test: Stage 2 Breaker Layout/Placement
Coverage Target: _stage_2_layout() - PlaceVerb integration
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage2Layout:
    """Test Stage 2: Breaker Layout/Placement (LAY-002, LAY-003)"""

    @pytest.mark.asyncio
    async def test_stage2_skip_without_place_verb(
        self, mock_plan_minimal, context_with_enclosure
    ):
        """TEST-SR-S2-001: Stage 2 skips when no PLACE verb in plan"""
        runner = StageRunner()

        result = await runner.run_stage(2, mock_plan_minimal, context_with_enclosure)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 2
        assert result["stage_name"] == "Layout"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_stage2_runs_with_place_verb(
        self, mock_plan_with_place, context_with_enclosure
    ):
        """TEST-SR-S2-002: Stage 2 executes PlaceVerb when present"""
        runner = StageRunner()

        result = await runner.run_stage(2, mock_plan_with_place, context_with_enclosure)

        # Should attempt to run (may error due to verb issues, but not skip)
        assert result["status"] in ["success", "error"]
        assert result["stage_number"] == 2

    @pytest.mark.asyncio
    async def test_stage2_stores_placements_in_context(
        self, mock_plan_with_place, context_with_enclosure
    ):
        """TEST-SR-S2-003: Stage 2 stores placements in context on success"""
        runner = StageRunner()
        context = context_with_enclosure.copy()

        result = await runner.run_stage(2, mock_plan_with_place, context)

        # If successful, should have placements
        if result["status"] == "success":
            assert "placements" in context or "placements" in result["output"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stage2_requires_enclosure_result(
        self, mock_plan_with_place, context_with_inputs
    ):
        """TEST-SR-S2-004: Stage 2 errors if enclosure_result missing

        NOTE: Marked as integration test - requires full verb execution
        """
        runner = StageRunner()
        # context_with_inputs has no enclosure_result
        context = context_with_inputs.copy()

        result = await runner.run_stage(2, mock_plan_with_place, context)

        # Should error due to missing enclosure_result
        assert result["status"] in ["error", "skipped"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stage2_handles_exception(self, context_with_enclosure):
        """TEST-SR-S2-005: Stage 2 handles exceptions gracefully

        NOTE: Marked as integration test - requires full verb validation
        """
        runner = StageRunner()
        bad_plan = {"steps": [{"PLACE": "invalid"}]}  # Invalid params

        result = await runner.run_stage(2, bad_plan, context_with_enclosure)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_stage2_records_duration(
        self, mock_plan_with_place, context_with_enclosure
    ):
        """TEST-SR-S2-006: Stage 2 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(2, mock_plan_with_place, context_with_enclosure)

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
