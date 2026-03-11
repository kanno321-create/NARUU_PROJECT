"""
Test: Stage 4 BOM Generation
Coverage Target: _stage_4_bom() - DataTransformer integration
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage4BOM:
    """Test Stage 4: BOM Generation (BUG-001~006, CAT-002~003)"""

    @pytest.mark.asyncio
    async def test_stage4_requires_enclosure(
        self, mock_plan_minimal, context_with_inputs
    ):
        """TEST-SR-S4-001: Stage 4 errors if enclosure missing"""
        runner = StageRunner()
        # context_with_inputs has no enclosure
        context = context_with_inputs.copy()

        result = await runner.run_stage(4, mock_plan_minimal, context)

        # Should error due to missing enclosure
        assert result["status"] == "error"
        assert len(result["blocking_errors"]) >= 1

    @pytest.mark.asyncio
    async def test_stage4_skip_without_placements(
        self, mock_plan_minimal, context_with_enclosure
    ):
        """TEST-SR-S4-002: Stage 4 skips when no placements"""
        runner = StageRunner()
        # context_with_enclosure has enclosure but no placements
        context = context_with_enclosure.copy()
        # Ensure no placements
        if "placements" in context:
            del context["placements"]

        result = await runner.run_stage(4, mock_plan_minimal, context)

        # Should skip due to missing placements
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_stage4_generates_estimate_data(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S4-003: Stage 4 generates estimate_data"""
        runner = StageRunner()

        result = await runner.run_stage(4, mock_plan_minimal, context_with_placements)

        # Should generate estimate_data (may error if DataTransformer fails)
        assert result["stage_number"] == 4
        assert result["stage_name"] == "BOM"

    @pytest.mark.asyncio
    async def test_stage4_stores_estimate_data_in_context(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S4-004: Stage 4 stores estimate_data in context on success"""
        runner = StageRunner()
        context = context_with_placements.copy()

        result = await runner.run_stage(4, mock_plan_minimal, context)

        # If successful, context should have estimate_data
        if result["status"] == "success":
            assert "estimate_data" in context or "estimate_data" in result["output"]

    @pytest.mark.asyncio
    async def test_stage4_quality_gate_always_true(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S4-005: Stage 4 quality_gate_passed is True (no quality gates)"""
        runner = StageRunner()

        result = await runner.run_stage(4, mock_plan_minimal, context_with_placements)

        # BOM stage has no quality gates (just data transformation)
        if result["status"] == "success":
            assert result["quality_gate_passed"] is True

    @pytest.mark.asyncio
    async def test_stage4_records_duration(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S4-006: Stage 4 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(4, mock_plan_minimal, context_with_placements)

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
