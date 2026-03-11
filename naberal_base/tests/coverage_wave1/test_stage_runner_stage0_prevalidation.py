"""
Test: Stage 0 Pre-Validation
Coverage Target: _stage_0_pre_validation() - Input validation logic
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage0PreValidation:
    """Test Stage 0: Pre-Validation (INP-001~005)"""

    @pytest.mark.asyncio
    async def test_stage0_missing_enclosure_type_error(self, mock_plan_minimal):
        """TEST-SR-S0-001: Stage 0 detects missing enclosure_type (INP-001)"""
        runner = StageRunner()
        context = {
            "install_location": "지하1층",
            "main_breaker": {"model": "SBS-404"},
            "branch_breakers": [{"model": "SBE-52"}],
        }

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert len(result["errors"]) >= 1
        assert any(e.error_code.code == "INP-001" for e in result["errors"])
        assert len(result["blocking_errors"]) >= 1
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_missing_install_location_error(self, mock_plan_minimal):
        """TEST-SR-S0-002: Stage 0 detects missing install_location (INP-002)"""
        runner = StageRunner()
        context = {
            "enclosure_type": "옥내노출",
            "main_breaker": {"model": "SBS-404"},
            "branch_breakers": [{"model": "SBE-52"}],
        }

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert any(e.error_code.code == "INP-002" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_stage0_missing_main_breaker_error(self, mock_plan_minimal):
        """TEST-SR-S0-003: Stage 0 detects missing main_breaker (INP-004)"""
        runner = StageRunner()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지하1층",
            "branch_breakers": [{"model": "SBE-52"}],
        }

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert any(e.error_code.code == "INP-004" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_stage0_missing_branch_breakers_error(self, mock_plan_minimal):
        """TEST-SR-S0-004: Stage 0 detects missing branch_breakers (INP-005)"""
        runner = StageRunner()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지하1층",
            "main_breaker": {"model": "SBS-404"},
        }

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert any(e.error_code.code == "INP-005" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_stage0_empty_branch_breakers_error(self, mock_plan_minimal):
        """TEST-SR-S0-005: Stage 0 detects empty branch_breakers list (INP-005)"""
        runner = StageRunner()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지하1층",
            "main_breaker": {"model": "SBS-404"},
            "branch_breakers": [],
        }

        result = await runner.run_stage(0, mock_plan_minimal, context)

        assert result["status"] == "error"
        assert any(e.error_code.code == "INP-005" for e in result["errors"])

    @pytest.mark.asyncio
    async def test_stage0_all_inputs_valid_success(
        self, mock_plan_minimal, context_with_inputs
    ):
        """TEST-SR-S0-006: Stage 0 passes with all valid inputs"""
        runner = StageRunner()

        result = await runner.run_stage(0, mock_plan_minimal, context_with_inputs)

        assert result["status"] == "success"
        assert len(result["errors"]) == 0
        assert len(result["blocking_errors"]) == 0
        assert result["quality_gate_passed"] is True
        assert result["stage_number"] == 0
        assert result["stage_name"] == "Pre-Validation"
