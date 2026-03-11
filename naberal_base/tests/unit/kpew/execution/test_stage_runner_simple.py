"""
Unit Tests: kpew/execution/stage_runner.py (Simplified)

Zero-Mock 원칙: 실제 엔진 로직만 테스트, 외부 의존성(DB/API)만 mock
"""

import pytest
from unittest.mock import Mock
from kis_estimator_core.kpew.execution.stage_runner import StageRunner

pytestmark = pytest.mark.unit


class TestStageRunnerInit:
    def test_init_creates_gate_validator(self):
        """초기화: GateValidator 생성"""
        runner = StageRunner()
        assert runner.gate_validator is not None


class TestStageRunnerStage0:
    """Stage 0: Pre-Validation"""

    def test_stage_0_success(self):
        """Stage 0: 정상 입력"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "실내",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20}],
        }

        result = runner._stage_0_pre_validation(plan, context)

        assert result["status"] == "success"
        assert result["stage_number"] == 0

    def test_stage_0_missing_enclosure_type(self):
        """Stage 0: enclosure_type 누락"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "install_location": "실내",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20}],
        }

        result = runner._stage_0_pre_validation(plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) > 0

    def test_stage_0_missing_main_breaker(self):
        """Stage 0: main_breaker 누락"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "실내",
            "branch_breakers": [{"poles": 2, "current": 20}],
        }

        result = runner._stage_0_pre_validation(plan, context)

        assert result["status"] == "error"

    def test_stage_0_missing_install_location(self):
        """Stage 0: install_location 누락 (INP-002)"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "enclosure_type": "옥내노출",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20}],
        }

        result = runner._stage_0_pre_validation(plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) > 0

    def test_stage_0_empty_branch_breakers(self):
        """Stage 0: branch_breakers 빈 리스트 (INP-005)"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "실내",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [],  # Empty list
        }

        result = runner._stage_0_pre_validation(plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) > 0


class TestStageRunnerStage1:
    """Stage 1: Enclosure - PICK_ENCLOSURE verb 테스트"""

    @pytest.mark.asyncio
    async def test_stage_1_no_pick_verb(self):
        """Stage 1: PICK_ENCLOSURE verb 없음 (스킵)"""
        runner = StageRunner()
        plan = {"steps": []}  # No PICK_ENCLOSURE verb
        context = {}

        result = await runner._stage_1_enclosure(plan, context)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 1
        assert result["stage_name"] == "Enclosure"

    @pytest.mark.asyncio
    async def test_stage_1_pick_verb_missing_context(self):
        """Stage 1: PICK_ENCLOSURE verb 있지만 context 불충분 (에러)"""
        runner = StageRunner()
        plan = {"steps": [{"PICK_ENCLOSURE": {"main_af": 100}}]}
        context = {}  # Missing required fields

        result = await runner._stage_1_enclosure(plan, context)

        # Should fail due to missing context
        assert result["status"] == "error"
        assert len(result["errors"]) > 0


class TestStageRunnerStage3:
    """Stage 3: Balance - REBALANCE verb 테스트"""

    def test_stage_3_no_rebalance_verb(self):
        """Stage 3: REBALANCE verb 없음 (스킵)"""
        runner = StageRunner()
        plan = {"steps": []}  # No REBALANCE verb
        context = {}

        result = runner._stage_3_balance(plan, context)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 3
        assert result["stage_name"] == "Balance"

    def test_stage_3_perfect_balance(self):
        """Stage 3: 완벽한 상평형 (diff ≤ 0%)"""
        runner = StageRunner()
        plan = {"steps": [{"REBALANCE": {}}]}

        # Create mock placements with perfect balance (30A each phase)
        # Note: BreakerPlacer.validate()._validate_clearance() requires 'x', 'y' in position
        from types import SimpleNamespace

        placements = [
            # Main breaker (row 0, excluded from balance calc)
            SimpleNamespace(
                breaker_id="MAIN",
                position={"row": 0, "col": 0, "x": 300, "y": 50},
                poles=3,
                current_a=100,
                phase="L1",
            ),
            # Branch breakers with perfect balance (각 상에 1개씩)
            SimpleNamespace(
                breaker_id="BR1",
                position={"row": 1, "col": 0, "x": 100, "y": 200},
                poles=2,
                current_a=30,
                phase="L1",
            ),
            SimpleNamespace(
                breaker_id="BR2",
                position={"row": 2, "col": 0, "x": 100, "y": 350},
                poles=2,
                current_a=30,
                phase="L2",
            ),
            SimpleNamespace(
                breaker_id="BR3",
                position={"row": 3, "col": 0, "x": 100, "y": 500},
                poles=2,
                current_a=30,
                phase="L3",
            ),
        ]

        context = {"placements": placements}

        result = runner._stage_3_balance(plan, context)

        assert result["status"] == "success"
        assert result["stage_number"] == 3
        assert result["quality_gate_passed"] is True

    def test_stage_3_high_imbalance(self):
        """Stage 3: 높은 불균형 (>4%)"""
        runner = StageRunner()
        plan = {"steps": [{"REBALANCE": {}}]}

        # Create mock placements with high imbalance
        from types import SimpleNamespace

        placements = [
            # Main breaker (row 0, excluded)
            SimpleNamespace(
                position={"row": 0, "col": 0},
                poles=3,
                current_a=100,
                phase="L1",
            ),
            # Imbalanced: L1=60A, L2=10A, L3=10A
            SimpleNamespace(
                position={"row": 1, "col": 0},
                poles=2,
                current_a=60,
                phase="L1",
            ),
            SimpleNamespace(
                position={"row": 2, "col": 0},
                poles=2,
                current_a=10,
                phase="L2",
            ),
            SimpleNamespace(
                position={"row": 3, "col": 0},
                poles=2,
                current_a=10,
                phase="L3",
            ),
        ]

        context = {"placements": placements}

        result = runner._stage_3_balance(plan, context)

        # Should have errors due to imbalance > 4%
        assert len(result["errors"]) > 0 or result["status"] != "success"

    def test_stage_3_no_placements_error(self):
        """Stage 3: placements 없음 (에러)"""
        runner = StageRunner()
        plan = {"steps": [{"REBALANCE": {}}]}
        context = {}  # No placements

        result = runner._stage_3_balance(plan, context)

        assert result["status"] == "error"
        assert len(result["errors"]) > 0


class TestStageRunnerStage2:
    """Stage 2: Layout - PLACE verb 테스트"""

    @pytest.mark.asyncio
    async def test_stage_2_no_place_verb(self):
        """Stage 2: PLACE verb 없음 (스킵)"""
        runner = StageRunner()
        plan = {"steps": []}  # No PLACE verb
        context = {}

        result = await runner._stage_2_layout(plan, context)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 2
        assert result["stage_name"] == "Layout"


class TestStageRunnerStage4:
    """Stage 4: BOM - GENERATE_BOM verb 테스트"""

    def test_stage_4_missing_enclosure_prerequisite(self):
        """Stage 4: enclosure 선행조건 누락 (에러)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}  # No enclosure

        result = runner._stage_4_bom(plan, context)

        # Stage 4 always checks enclosure prerequisite, returns error if missing
        assert result["status"] == "error"
        assert result["stage_number"] == 4
        assert result["stage_name"] == "BOM"


class TestStageRunnerStage5:
    """Stage 5: Cost - CALCULATE_COST verb 테스트"""

    def test_stage_5_no_cost_verb(self):
        """Stage 5: CALCULATE_COST verb 없음 (스킵)"""
        runner = StageRunner()
        plan = {"steps": []}  # No CALCULATE_COST verb
        context = {}

        result = runner._stage_5_cost(plan, context)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 5
        assert result["stage_name"] == "Cost"


class TestStageRunnerStage6:
    """Stage 6: Format - FORMAT_ESTIMATE verb 테스트"""

    def test_stage_6_no_format_verb(self):
        """Stage 6: FORMAT_ESTIMATE verb 없음 (스킵)"""
        runner = StageRunner()
        plan = {"steps": []}  # No FORMAT_ESTIMATE verb
        context = {}

        result = runner._stage_6_format(plan, context)

        assert result["status"] == "skipped"
        assert result["stage_number"] == 6
        assert result["stage_name"] == "Format"


class TestStageRunnerStage7:
    """Stage 7: Quality - QUALITY_CHECK verb 테스트"""

    def test_stage_7_always_runs_quality_checks(self):
        """Stage 7: verb 없어도 항상 품질 검사 실행 (성공)"""
        runner = StageRunner()
        plan = {"steps": []}  # No QUALITY_CHECK verb
        context = {}

        result = runner._stage_7_quality(plan, context)

        # Stage 7 always runs final quality checks regardless of verb
        assert result["status"] == "success"
        assert result["stage_number"] == 7
        assert result["stage_name"] == "Quality"


class TestStageRunnerRunStage:
    """run_stage 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_run_stage_0(self):
        """run_stage: Stage 0 실행"""
        runner = StageRunner()
        plan = Mock()
        context = {
            "enclosure_type": "옥내노출",
            "install_location": "실내",
            "main_breaker": {"poles": 3, "current": 100, "frame": 100},
            "branch_breakers": [{"poles": 2, "current": 20}],
        }

        result = await runner.run_stage(0, plan, context)

        assert result["stage_number"] == 0
        assert result["status"] == "success"
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_run_stage_1_skipped(self):
        """run_stage: Stage 1 스킵 (verb 없음)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(1, plan, context)

        assert result["stage_number"] == 1
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_stage_2_skipped(self):
        """run_stage: Stage 2 스킵 (verb 없음)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(2, plan, context)

        assert result["stage_number"] == 2
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_stage_3_skipped(self):
        """run_stage: Stage 3 스킵 (verb 없음)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(3, plan, context)

        assert result["stage_number"] == 3
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_stage_4_error_missing_enclosure(self):
        """run_stage: Stage 4 에러 (enclosure 선행조건 누락)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}  # No enclosure

        result = await runner.run_stage(4, plan, context)

        assert result["stage_number"] == 4
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_run_stage_5_skipped(self):
        """run_stage: Stage 5 스킵 (verb 없음)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(5, plan, context)

        assert result["stage_number"] == 5
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_stage_6_skipped(self):
        """run_stage: Stage 6 스킵 (verb 없음)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(6, plan, context)

        assert result["stage_number"] == 6
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_stage_7_always_runs(self):
        """run_stage: Stage 7 항상 실행 (verb 없어도 품질 검사)"""
        runner = StageRunner()
        plan = {"steps": []}
        context = {}

        result = await runner.run_stage(7, plan, context)

        assert result["stage_number"] == 7
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_run_stage_invalid_number(self):
        """run_stage: 잘못된 stage 번호"""
        runner = StageRunner()
        plan = Mock()
        context = {}

        with pytest.raises(KeyError):
            await runner.run_stage(99, plan, context)
