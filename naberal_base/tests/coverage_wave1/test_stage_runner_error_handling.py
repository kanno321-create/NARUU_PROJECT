"""
Test: StageRunner Error Handling and Edge Cases
Coverage Target: Exception handling, blocking errors, status transitions
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStageRunnerErrorHandling:
    """Test StageRunner error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_multiple_blocking_errors_stage0(self, mock_plan_minimal):
        """TEST-SR-ERR-001: Stage 0 collects multiple blocking errors"""
        runner = StageRunner()
        # Empty context triggers all INP-00X errors
        context = {}

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert len(result["errors"]) >= 4  # INP-001, 002, 004, 005
        assert len(result["blocking_errors"]) >= 4
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_error_status_vs_success_status(
        self, mock_plan_minimal, context_with_inputs
    ):
        """TEST-SR-ERR-002: Status is 'error' with blocking errors, 'success' without"""
        runner = StageRunner()

        # With errors
        result_error = await runner.run_stage(0, mock_plan_minimal, {})
        assert result_error["status"] == "error"
        assert len(result_error["blocking_errors"]) > 0

        # Without errors
        result_success = await runner.run_stage(
            0, mock_plan_minimal, context_with_inputs
        )
        assert result_success["status"] == "success"
        assert len(result_success["blocking_errors"]) == 0

    @pytest.mark.asyncio
    async def test_blocking_vs_non_blocking_errors(self, mock_plan_minimal):
        """TEST-SR-ERR-003: blocking_errors filtered from errors list"""
        runner = StageRunner()
        context = {}

        result = await runner.run_stage(0, mock_plan_minimal, context)

        # All INP errors should be blocking
        assert len(result["blocking_errors"]) > 0
        for blocking_error in result["blocking_errors"]:
            assert blocking_error.error_code.blocking is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_exception_caught_and_returned(self, context_with_inputs):
        """TEST-SR-ERR-004: Stage exceptions caught and returned as errors

        NOTE: Marked as integration test - requires full verb validation
        """
        runner = StageRunner()
        # Invalid plan to trigger exception in Stage 1
        bad_plan = {"steps": [{"PICK_ENCLOSURE": None}]}  # Will cause exception

        result = await runner.run_stage(1, bad_plan, context_with_inputs)

        assert result["status"] == "error"
        assert len(result["errors"]) > 0
        assert len(result["blocking_errors"]) > 0

    @pytest.mark.asyncio
    async def test_skipped_status_when_no_verb(
        self, mock_plan_minimal, context_with_inputs
    ):
        """TEST-SR-ERR-005: Status is 'skipped' when stage has no applicable verb"""
        runner = StageRunner()

        # Stage 1 without PICK_ENCLOSURE verb
        result = await runner.run_stage(1, mock_plan_minimal, context_with_inputs)

        assert result["status"] == "skipped"
        assert len(result["errors"]) == 0
        assert len(result["blocking_errors"]) == 0
        assert result["quality_gate_passed"] is True

    @pytest.mark.asyncio
    async def test_duration_always_recorded(self, mock_plan_minimal):
        """TEST-SR-ERR-006: duration_ms recorded even on error/skip"""
        runner = StageRunner()

        # Error case
        result_error = await runner.run_stage(0, mock_plan_minimal, {})
        assert "duration_ms" in result_error
        assert result_error["duration_ms"] >= 0

        # Skip case
        result_skip = await runner.run_stage(1, mock_plan_minimal, {})
        assert "duration_ms" in result_skip
        assert result_skip["duration_ms"] >= 0
