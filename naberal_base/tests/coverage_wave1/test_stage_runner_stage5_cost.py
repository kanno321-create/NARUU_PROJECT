"""
Test: Stage 5 Cost Calculation
Coverage Target: _stage_5_cost() - Cost validation and aggregation
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage5Cost:
    """Test Stage 5: Cost Calculation (ACC-001~004, BUS-001~004)"""

    @pytest.mark.asyncio
    async def test_stage5_skip_without_estimate_data(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S5-001: Stage 5 skips when no estimate_data"""
        runner = StageRunner()
        # context_with_placements has no estimate_data
        context = context_with_placements.copy()
        # Ensure no estimate_data
        if "estimate_data" in context:
            del context["estimate_data"]

        result = await runner.run_stage(5, mock_plan_minimal, context)

        # Should skip due to missing estimate_data
        assert result["status"] == "skipped"
        assert result["stage_number"] == 5
        assert result["stage_name"] == "Cost"

    @pytest.mark.asyncio
    async def test_stage5_calculates_total_cost(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S5-002: Stage 5 calculates total cost from estimate_data"""
        runner = StageRunner()

        result = await runner.run_stage(
            5, mock_plan_minimal, context_with_estimate_data
        )

        # Should calculate costs
        assert result["status"] == "success"
        assert "output" in result
        assert "total_cost" in result["output"]
        assert "total_cost_with_vat" in result["output"]

    @pytest.mark.asyncio
    async def test_stage5_stores_costs_in_context(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S5-003: Stage 5 stores costs in context"""
        runner = StageRunner()
        context = context_with_estimate_data.copy()

        result = await runner.run_stage(5, mock_plan_minimal, context)

        # Should store costs in context
        if result["status"] == "success":
            assert "total_cost" in context
            assert "total_cost_with_vat" in context

    @pytest.mark.asyncio
    async def test_stage5_vat_calculation(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S5-004: Stage 5 VAT is 10% of total_cost"""
        runner = StageRunner()
        context = context_with_estimate_data.copy()

        result = await runner.run_stage(5, mock_plan_minimal, context)

        if result["status"] == "success":
            total = result["output"]["total_cost"]
            total_vat = result["output"]["total_cost_with_vat"]
            # VAT = 1.1 * total
            assert abs(total_vat - total * 1.1) < 0.01

    @pytest.mark.asyncio
    async def test_stage5_quality_gate_always_true(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S5-005: Stage 5 quality_gate_passed is True (no quality gates)"""
        runner = StageRunner()

        result = await runner.run_stage(
            5, mock_plan_minimal, context_with_estimate_data
        )

        # Cost stage has no quality gates
        if result["status"] == "success":
            assert result["quality_gate_passed"] is True

    @pytest.mark.asyncio
    async def test_stage5_records_duration(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S5-006: Stage 5 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(
            5, mock_plan_minimal, context_with_estimate_data
        )

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
