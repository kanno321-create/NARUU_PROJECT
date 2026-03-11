"""
T1: Stage 0 입력검증 유닛 테스트 (8케이스)

타겟 라인: stage_runner.py Lines 70-106
목적: 저비용 라인 집중 타격 (+8~10%p 예상)
"""

import pytest
from kis_estimator_core.kpew.execution.stage_runner import StageRunner
from kis_estimator_core.errors import error_codes


class TestStage0PreValidation:
    """Stage 0: Pre-Validation 입력검증 테스트

    INP-001: 외함 종류 정보 누락
    INP-002: 외함 설치 위치 정보 누락
    INP-004: 메인 차단기 정보 누락
    INP-005: 분기 차단기 정보 누락
    """

    @pytest.mark.asyncio
    async def test_stage0_missing_enclosure_type(self):
        """케이스 1: enclosure_type 누락 → INP-001 에러"""
        context = {
            # 'enclosure_type': '옥내노출',  # MISSING
            "install_location": "지상",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [{"poles": 2, "current": 30}],
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["stage_number"] == 0
        assert result["stage_name"] == "Pre-Validation"
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert len(result["blocking_errors"]) == 1
        assert result["errors"][0].error_code == error_codes.INP_001
        assert result["quality_gate_passed"] is False
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_stage0_missing_install_location(self):
        """케이스 2: install_location 누락 → INP-002 에러"""
        context = {
            "enclosure_type": "옥내노출",
            # 'install_location': '지상',  # MISSING
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [{"poles": 2, "current": 30}],
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0].error_code == error_codes.INP_002
        assert len(result["blocking_errors"]) == 1
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_missing_main_breaker(self):
        """케이스 3: main_breaker 누락 → INP-004 에러"""
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지상",
            # 'main_breaker': {'poles': 3, 'current': 100},  # MISSING
            "branch_breakers": [{"poles": 2, "current": 30}],
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0].error_code == error_codes.INP_004
        assert len(result["blocking_errors"]) == 1
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_missing_branch_breakers(self):
        """케이스 4: branch_breakers 누락 → INP-005 에러"""
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지상",
            "main_breaker": {"poles": 3, "current": 100},
            # 'branch_breakers': [...]  # MISSING
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0].error_code == error_codes.INP_005
        assert len(result["blocking_errors"]) == 1
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_empty_branch_breakers_array(self):
        """케이스 5: branch_breakers 빈 배열 → INP-005 에러

        Lines 96-100: len(context.get('branch_breakers', [])) == 0
        """
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지상",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [],  # EMPTY ARRAY
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert result["errors"][0].error_code == error_codes.INP_005
        assert len(result["blocking_errors"]) == 1
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_multiple_missing_fields(self):
        """케이스 6: 여러 필수 필드 누락 → 복합 에러 (4개)"""
        context = {}  # ALL MISSING
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 4  # INP-001, INP-002, INP-004, INP-005
        assert len(result["blocking_errors"]) == 4
        assert result["quality_gate_passed"] is False

        # Verify all error codes present (use list comprehension instead of set)
        error_codes_found = [err.error_code for err in result["errors"]]
        assert error_codes.INP_001 in error_codes_found
        assert error_codes.INP_002 in error_codes_found
        assert error_codes.INP_004 in error_codes_found
        assert error_codes.INP_005 in error_codes_found

    @pytest.mark.asyncio
    async def test_stage0_partial_success_two_missing(self):
        """케이스 7: 일부 필드만 제공 (2개 누락) → 부분 실패"""
        context = {
            "enclosure_type": "옥내노출",
            # 'install_location': '지상',  # MISSING
            # 'main_breaker': {'poles': 3, 'current': 100},  # MISSING
            "branch_breakers": [{"poles": 2, "current": 30}],
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) == 2  # INP-002, INP-004
        assert len(result["blocking_errors"]) == 2
        assert result["quality_gate_passed"] is False

    @pytest.mark.asyncio
    async def test_stage0_all_required_fields_provided_success(self):
        """케이스 8: 모든 필수 필드 제공 → 성공"""
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "지상",
            "main_breaker": {"poles": 3, "current": 100},
            "branch_breakers": [
                {"poles": 2, "current": 30},
                {"poles": 2, "current": 20},
            ],
        }
        plan = {}
        runner = StageRunner()

        result = await runner.run_stage(0, plan, context)

        assert result["status"] == "success"
        assert len(result["errors"]) == 0
        assert len(result["blocking_errors"]) == 0
        assert result["quality_gate_passed"] is True
        assert result["duration_ms"] >= 0
        assert result["output"] == {}
