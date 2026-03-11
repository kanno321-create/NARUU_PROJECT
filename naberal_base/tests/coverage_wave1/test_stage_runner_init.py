"""
Test: StageRunner Initialization and Basic Methods
Coverage Target: stage_runner.py __init__, run_stage() basic flow
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStageRunnerInit:
    """Test StageRunner initialization and basic functionality"""

    def test_init_creates_gate_validator(self):
        """TEST-SR-001: StageRunner __init__ creates GateValidator instance"""
        runner = StageRunner()

        assert runner is not None
        assert hasattr(runner, "gate_validator")
        assert runner.gate_validator is not None

    @pytest.mark.asyncio
    async def test_run_stage_returns_dict(self, mock_plan_minimal, context_minimal):
        """TEST-SR-002: run_stage() returns dict with expected keys"""
        runner = StageRunner()

        result = await runner.run_stage(0, mock_plan_minimal, context_minimal)

        assert isinstance(result, dict)
        assert "stage_number" in result
        assert "stage_name" in result
        assert "status" in result
        assert "errors" in result
        assert "blocking_errors" in result
        assert "output" in result
        assert "quality_gate_passed" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_run_stage_invalid_stage_number_raises(
        self, mock_plan_minimal, context_minimal
    ):
        """TEST-SR-003: run_stage() with invalid stage number raises KeyError"""
        runner = StageRunner()

        with pytest.raises(KeyError):
            await runner.run_stage(99, mock_plan_minimal, context_minimal)

    @pytest.mark.asyncio
    async def test_run_stage_records_duration(self, mock_plan_minimal, context_minimal):
        """TEST-SR-004: run_stage() records execution duration in milliseconds"""
        runner = StageRunner()

        result = await runner.run_stage(0, mock_plan_minimal, context_minimal)

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_run_stage_all_stages_accessible(
        self, mock_plan_minimal, context_minimal
    ):
        """TEST-SR-005: run_stage() can access all 8 stages (0-7)"""
        runner = StageRunner()

        for stage_num in range(8):
            result = await runner.run_stage(
                stage_num, mock_plan_minimal, context_minimal
            )
            assert result["stage_number"] == stage_num
            assert isinstance(result["stage_name"], str)
