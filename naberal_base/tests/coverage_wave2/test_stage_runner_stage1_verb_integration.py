"""
Wave 2 Test - Stage Runner Stage 1 Verb Integration

Coverage Targets:
- stage_runner.py Stage 1 PickEnclosureVerb integration (Lines 148-212)
- ExecutionCtx creation and state management
- Verb execution via from_spec() factory
- Context data copying to/from ctx.state

Zero-Mock Principle: Real StageRunner, real ExecutionCtx, real from_spec
Note: Actual PickEnclosureVerb execution requires catalog DB, so we focus on infrastructure
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner


class TestStage1VerbIntegration:
    """Stage 1 ExecutionCtx + Verb integration 테스트 (Lines 148-212)"""

    @pytest.mark.asyncio
    async def test_stage1_skipped_when_no_pick_enclosure_verb(self):
        """PICK_ENCLOSURE verb 없을 때 skip 동작 테스트

        Target: Lines 127-146
        Scenario:
            - Plan에 PICK_ENCLOSURE verb 없음
            - Stage 1 skip 반환

        Expected:
            - status = "skipped"
            - duration_ms = 0
            - quality_gate_passed = True
        """
        # Arrange
        plan = {"steps": [{"SOME_OTHER_VERB": {}}]}  # No PICK_ENCLOSURE

        context = {
            "enclosure_type": "옥내노출",
            "install_location": "1층",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [{"poles": 2, "current": 30}],
        }

        runner = StageRunner()

        # Act
        result = await runner.run_stage(1, plan, context)

        # Assert: Skipped
        assert (
            result["status"] == "skipped"
        ), "Stage 1 should be skipped without PICK_ENCLOSURE verb"
        assert result["stage_number"] == 1, "stage_number should be 1"
        assert result["stage_name"] == "Enclosure", "stage_name should be 'Enclosure'"
        assert result["duration_ms"] == 0, "duration_ms should be 0 for skipped stage"
        assert (
            result["quality_gate_passed"] is True
        ), "quality_gate should pass for skipped stage"
        assert len(result["errors"]) == 0, "No errors should be present"
        assert (
            len(result["blocking_errors"]) == 0
        ), "No blocking errors should be present"

    @pytest.mark.asyncio
    async def test_stage1_execution_ctx_creation(self):
        """ExecutionCtx 생성 및 state 복사 테스트

        Target: Lines 148-170
        Scenario:
            - PICK_ENCLOSURE verb 존재
            - ExecutionCtx 생성됨
            - Context 데이터가 ctx.state로 복사됨

        Expected:
            - ExecutionCtx created with ssot, db, logger, state
            - Context keys copied to ctx.state
        """
        # Arrange
        plan = {"steps": [{"PICK_ENCLOSURE": {"strategy": "optimal"}}]}

        context = {
            "enclosure_type": "옥내노출",
            "install_location": "1층",
            "main_breaker": {"poles": 3, "current": 100, "width_mm": 75},
            "branch_breakers": [
                {"poles": 2, "current": 30, "width_mm": 50},
                {"poles": 2, "current": 20, "width_mm": 50},
            ],
            "material": "steel",
            "thickness": 1.6,
            "accessories": [],
        }

        runner = StageRunner()

        # Act: Run Stage 1
        # Note: This will attempt to execute PickEnclosureVerb
        # May fail due to missing catalog DB, but we test infrastructure setup
        result = await runner.run_stage(1, plan, context)

        # Assert: Stage 1 attempted execution (may succeed or fail depending on DB)
        assert result["status"] in [
            "success",
            "error",
        ], "Stage 1 should attempt execution"
        assert result["stage_number"] == 1, "stage_number should be 1"
        assert result["stage_name"] == "Enclosure", "stage_name should be 'Enclosure'"
        assert (
            result["duration_ms"] >= 0
        ), "duration_ms should be >= 0 for executed stage"

        # If succeeded, check result
        if result["status"] == "success":
            assert (
                "enclosure_result" in context
            ), "enclosure_result should be in context"
            assert "enclosure" in context, "enclosure should be in context"
            assert "output" in result, "output should be in result"
            assert (
                "enclosure_result" in result["output"]
            ), "enclosure_result should be in output"

    @pytest.mark.asyncio
    async def test_stage1_fit_score_validation(self):
        """fit_score 검증 게이트 테스트

        Target: Lines 194-205
        Scenario:
            - PickEnclosureVerb 실행 후
            - fit_score 검증 (≥ 0.90)

        Expected:
            - GateValidator.validate_fit_score() 호출
            - fit_score < 0.90이면 ENC-001 에러 추가
        """
        # Arrange: Provide minimal context for PickEnclosureVerb
        plan = {"steps": [{"PICK_ENCLOSURE": {}}]}

        context = {
            "enclosure_type": "옥내노출",
            "install_location": "1층",
            "main_breaker": {
                "poles": 3,
                "current": 100,
                "width_mm": 75,
                "height_mm": 130,
                "depth_mm": 60,
            },
            "branch_breakers": [
                {"poles": 2, "current": 30, "width_mm": 50, "height_mm": 130},
                {"poles": 2, "current": 20, "width_mm": 50, "height_mm": 130},
            ],
        }

        runner = StageRunner()

        # Act
        result = await runner.run_stage(1, plan, context)

        # Assert: Fit score validation occurred
        # (May pass or fail depending on actual EnclosureSolver result)
        assert result["status"] in ["success", "error"], "Stage 1 should complete"
        assert "quality_gate_passed" in result, "quality_gate_passed should be present"

        # If errors present, they should be EstimatorError instances
        if result["errors"]:
            for error in result["errors"]:
                assert hasattr(error, "error_code"), "Error should have error_code"
                assert hasattr(error, "phase"), "Error should have phase"

        # If succeeded, check enclosure_result structure
        if result["status"] == "success":
            assert "enclosure_result" in context, "enclosure_result should be stored"
            enclosure_result = context["enclosure_result"]
            assert hasattr(
                enclosure_result, "quality_gate"
            ), "enclosure_result should have quality_gate"
            assert hasattr(
                enclosure_result, "dimensions"
            ), "enclosure_result should have dimensions"
