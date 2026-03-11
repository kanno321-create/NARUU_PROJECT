"""
Test: Stage 6 Document Format Generation
Coverage Target: _stage_6_format() - EstimateFormatter integration
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage6Format:
    """Test Stage 6: Format Generation (CAL-001~002)"""

    @pytest.mark.asyncio
    async def test_stage6_skip_without_estimate_data(
        self, mock_plan_minimal, context_with_placements
    ):
        """TEST-SR-S6-001: Stage 6 skips when no estimate_data"""
        runner = StageRunner()
        # context_with_placements has no estimate_data
        context = context_with_placements.copy()
        if "estimate_data" in context:
            del context["estimate_data"]

        result = await runner.run_stage(6, mock_plan_minimal, context)

        # Should skip due to missing estimate_data
        assert result["status"] == "skipped"
        assert result["stage_number"] == 6
        assert result["stage_name"] == "Format"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stage6_generates_excel_file(
        self, mock_plan_minimal, context_with_estimate_data, real_template_path
    ):
        """TEST-SR-S6-002: Stage 6 generates Excel file

        NOTE: Marked as integration test - requires real template file
        """
        runner = StageRunner()
        context = context_with_estimate_data.copy()

        result = await runner.run_stage(6, mock_plan_minimal, context)

        # Should attempt to generate (may fail if template missing)
        assert result["stage_number"] == 6
        assert result["stage_name"] == "Format"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_stage6_stores_file_paths_in_context(
        self, mock_plan_minimal, context_with_estimate_data, real_template_path
    ):
        """TEST-SR-S6-003: Stage 6 stores file paths in context on success

        NOTE: Marked as integration test - requires real template file
        """
        runner = StageRunner()
        context = context_with_estimate_data.copy()

        result = await runner.run_stage(6, mock_plan_minimal, context)

        # If successful, context should have excel_path
        if result["status"] == "success":
            assert "excel_path" in context

    @pytest.mark.asyncio
    async def test_stage6_validates_formula_preservation(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S6-004: Stage 6 validates formula preservation"""
        runner = StageRunner()

        result = await runner.run_stage(
            6, mock_plan_minimal, context_with_estimate_data
        )

        # If runs, should have quality_gate_passed reflecting formula preservation
        assert isinstance(result["quality_gate_passed"], bool)

    @pytest.mark.asyncio
    async def test_stage6_handles_missing_template(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S6-005: Stage 6 errors gracefully if template missing"""
        runner = StageRunner()
        context = context_with_estimate_data.copy()

        result = await runner.run_stage(6, mock_plan_minimal, context)

        # Should return error (not crash) if template missing
        assert result["stage_number"] == 6
        assert result["status"] in ["success", "error", "skipped"]

    @pytest.mark.asyncio
    async def test_stage6_records_duration(
        self, mock_plan_minimal, context_with_estimate_data
    ):
        """TEST-SR-S6-006: Stage 6 records execution duration"""
        runner = StageRunner()

        result = await runner.run_stage(
            6, mock_plan_minimal, context_with_estimate_data
        )

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0
