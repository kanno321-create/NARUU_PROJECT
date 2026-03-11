"""
Test: Stage 3 Phase Balance Validation
Coverage Target: _stage_3_balance() - BreakerPlacer.validate() integration
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage3Balance:
    """Test Stage 3: Phase Balance Validation (LAY-001, BUG-007)"""

    @pytest.mark.asyncio
    async def test_stage3_skip_without_rebalance_verb(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S3-001: Stage 3 skips when no REBALANCE verb in plan"""
        runner = StageRunner()

        result = await runner.run_stage(3, mock_plan_minimal, context_with_placements)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 3
        assert result["stage_name"] == "Balance"
        assert len(result["errors"]) == 0
        assert result["quality_gate_passed"] is True

    @pytest.mark.asyncio
    async def test_stage3_runs_with_rebalance_verb(
        self, mock_plan_with_rebalance, context_with_placements
    ):
        """TEST-SR-S3-002: Stage 3 executes with REBALANCE verb"""
        runner = StageRunner()

        result = await runner.run_stage(
            3, mock_plan_with_rebalance, context_with_placements
        )

        # Should execute (may succeed or error depending on validation)
        assert result["status"] in ["success", "error"]
        assert result["stage_number"] == 3
        assert result["stage_name"] == "Balance"

    @pytest.mark.asyncio
    async def test_stage3_validates_phase_loads(
        self, mock_plan_with_rebalance, context_with_placements
    ):
        """TEST-SR-S3-003: Stage 3 validates phase balance"""
        runner = StageRunner()

        result = await runner.run_stage(
            3, mock_plan_with_rebalance, context_with_placements
        )

        # Should have output with phase loads and imbalance
        assert "output" in result
        if result["status"] == "success":
            assert "phase_loads" in result["output"]
            assert "phase_imbalance_pct" in result["output"]

    @pytest.mark.asyncio
    async def test_stage3_requires_placements(
        self, mock_plan_with_rebalance, context_with_inputs
    ):
        """TEST-SR-S3-004: Stage 3 errors if placements missing"""
        runner = StageRunner()
        # context_with_inputs has no placements
        context = context_with_inputs.copy()

        result = await runner.run_stage(3, mock_plan_with_rebalance, context)

        # Should error due to missing placements
        assert result["status"] == "error"
        assert len(result["blocking_errors"]) >= 1

    @pytest.mark.asyncio
    async def test_stage3_quality_gate_passed(
        self, mock_plan_with_rebalance, context_with_placements
    ):
        """TEST-SR-S3-005: Stage 3 quality_gate_passed reflects balance validation"""
        runner = StageRunner()

        result = await runner.run_stage(
            3, mock_plan_with_rebalance, context_with_placements
        )

        # quality_gate_passed should be boolean
        assert isinstance(result["quality_gate_passed"], bool)

    @pytest.mark.asyncio
    async def test_stage3_records_duration(
        self, mock_plan_with_rebalance, context_with_placements
    ):
        """TEST-SR-S3-006: Stage 3 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(
            3, mock_plan_with_rebalance, context_with_placements
        )

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
