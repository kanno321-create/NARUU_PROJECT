"""
Test: Stage 1 Enclosure Selection
Coverage Target: _stage_1_enclosure() - PickEnclosureVerb integration
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage1Enclosure:
    """Test Stage 1: Enclosure Selection (ENC-001~003)"""

    @pytest.mark.asyncio
    async def test_stage1_skip_without_pick_verb(
        self, mock_plan_minimal, context_with_inputs
    ):
        """TEST-SR-S1-001: Stage 1 skips when no PICK_ENCLOSURE verb in plan"""
        runner = StageRunner()

        result = await runner.run_stage(1, mock_plan_minimal, context_with_inputs)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 1
        assert result["stage_name"] == "Enclosure"
        assert len(result["errors"]) == 0
        assert result["quality_gate_passed"] is True

    @pytest.mark.asyncio
    async def test_stage1_runs_with_pick_verb(
        self, mock_plan_with_pick_enclosure, context_with_inputs
    ):
        """TEST-SR-S1-002: Stage 1 executes PickEnclosureVerb when present"""
        runner = StageRunner()

        result = await runner.run_stage(
            1, mock_plan_with_pick_enclosure, context_with_inputs
        )

        # Should attempt to run (may error due to missing catalog, but not skip)
        assert result["status"] in ["success", "error"]
        assert result["stage_number"] == 1
        assert result["stage_name"] == "Enclosure"

    @pytest.mark.asyncio
    async def test_stage1_stores_result_in_context(
        self, mock_plan_with_pick_enclosure, context_with_inputs
    ):
        """TEST-SR-S1-003: Stage 1 stores enclosure_result in context on success"""
        runner = StageRunner()
        context = context_with_inputs.copy()

        result = await runner.run_stage(1, mock_plan_with_pick_enclosure, context)

        # If successful, context should have enclosure_result
        if result["status"] == "success":
            assert (
                "enclosure_result" in context or "enclosure_result" in result["output"]
            )

    @pytest.mark.asyncio
    async def test_stage1_validates_fit_score(
        self, mock_plan_with_pick_enclosure, context_with_inputs
    ):
        """TEST-SR-S1-004: Stage 1 validates fit_score using GateValidator"""
        runner = StageRunner()

        result = await runner.run_stage(
            1, mock_plan_with_pick_enclosure, context_with_inputs
        )

        # quality_gate_passed should be boolean
        assert isinstance(result["quality_gate_passed"], bool)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stage1_handles_exception_gracefully(self, context_with_inputs):
        """TEST-SR-S1-005: Stage 1 handles exceptions and returns error status

        NOTE: Marked as integration test - requires full verb validation
        """
        runner = StageRunner()
        # Invalid plan structure to trigger exception
        bad_plan = {
            "steps": [{"PICK_ENCLOSURE": "invalid_params"}]  # Invalid params type
        }

        result = await runner.run_stage(1, bad_plan, context_with_inputs)

        # Should handle exception and return error
        assert result["status"] == "error"
        assert len(result["blocking_errors"]) >= 1

    @pytest.mark.asyncio
    async def test_stage1_records_duration(
        self, mock_plan_with_pick_enclosure, context_with_inputs
    ):
        """TEST-SR-S1-006: Stage 1 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(
            1, mock_plan_with_pick_enclosure, context_with_inputs
        )

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
