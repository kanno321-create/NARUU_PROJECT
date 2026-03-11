"""
EnclosureSolver 유닛 테스트

Task 10: Stage 1 (Enclosure Solver) 품질 검증
- calculate_height() 높이 계산 검증
- calculate_width() 폭 계산 검증
- calculate_depth() 깊이 계산 검증
- solve() 통합 계산 검증
- 품질 게이트 (fit_score ≥ 0.90)
- 예외 처리 검증

목업 없음: 실제 core_rules.json + enclosures.json 사용
"""

import pytest
from pathlib import Path

from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.models.enclosure import (
    BreakerSpec,
    AccessorySpec,
    CustomerRequirements,
)


@pytest.fixture
def knowledge_path():
    """실제 지식파일 경로"""
    return (
        Path(__file__).parent.parent.parent / "temp_basic_knowledge" / "core_rules.json"
    )


@pytest.fixture
def solver(knowledge_path):
    """EnclosureSolver 인스턴스"""
    return EnclosureSolver(knowledge_path=knowledge_path)


@pytest.fixture
def sample_main_breaker():
    """샘플 메인 차단기 (100AF 2P 100A)"""
    return BreakerSpec(
        id="main-1",
        model="SBS-102",
        poles=2,
        current_a=100,
        frame_af=100,
    )


@pytest.fixture
def sample_branch_breakers():
    """샘플 분기 차단기 10개"""
    return [
        BreakerSpec(
            id=f"branch-{i}", model="SBE-52", poles=2, current_a=30, frame_af=50
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_accessories():
    """샘플 부속자재 (마그네트 2개)"""
    return [
        AccessorySpec(type="magnet", model="MC-22", quantity=1),
        AccessorySpec(type="magnet", model="MC-32", quantity=1),
    ]


@pytest.fixture
def customer_requirements():
    """고객 요구사항"""
    return CustomerRequirements(
        enclosure_type="옥내자립",
        ip_rating="IP44",
        material="steel",
    )


class TestEnclosureSolverInit:
    """초기화 테스트"""

    def test_init_with_valid_path(self, knowledge_path):
        """정상 경로로 초기화"""
        solver = EnclosureSolver(knowledge_path=knowledge_path)
        assert solver.knowledge is not None
        assert "breaker_dimensions_mm" in solver.knowledge
        assert "frame_clearances" in solver.knowledge

    def test_init_with_missing_file(self):
        """파일 없는 경로 → EstimatorError"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        invalid_path = Path("/nonexistent/path/core_rules.json")
        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=invalid_path)

        assert "지식파일을 찾을 수 없습니다" in str(exc_info.value)

    def test_init_validates_required_sections(self, tmp_path):
        """필수 섹션 누락 → EstimatorError"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        incomplete_json = tmp_path / "incomplete.json"
        incomplete_json.write_text('{"meta": {}}')

        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=incomplete_json)

        assert "필수 섹션" in str(exc_info.value)


class TestCalculateHeight:
    """높이 계산 테스트"""

    def test_height_basic_calculation(
        self, solver, sample_main_breaker, sample_branch_breakers
    ):
        """기본 높이 계산 (부속자재 없음)"""
        H_total, breakdown = solver.calculate_height(
            main_breaker=sample_main_breaker,
            branch_breakers=sample_branch_breakers,
            accessories=[],
        )

        # 구조 검증
        assert "top_margin_mm" in breakdown
        assert "main_breaker_height_mm" in breakdown
        assert "main_to_branch_gap_mm" in breakdown
        assert "branches_total_height_mm" in breakdown
        assert "bottom_margin_mm" in breakdown
        assert "accessory_margin_mm" in breakdown
        assert "H_total_mm" in breakdown

        # 값 검증
        assert breakdown["top_margin_mm"] > 0
        assert breakdown["main_breaker_height_mm"] == 130  # 100AF 2P
        assert breakdown["main_to_branch_gap_mm"] == 15
        # 마주보기 배치: 10개 → 5행 × (50AF 2P 폭 50mm) = 250mm
        assert breakdown["branches_total_height_mm"] == 5 * 50  # 5행 × 50mm
        assert breakdown["bottom_margin_mm"] > 0
        assert breakdown["accessory_margin_mm"] == 0  # 부속자재 없음

        # 총합 검증 (H_calculated_mm이 수식 합과 일치)
        expected = (
            breakdown["top_margin_mm"]
            + breakdown["main_breaker_height_mm"]
            + breakdown["main_to_branch_gap_mm"]
            + breakdown["branches_total_height_mm"]
            + breakdown["bottom_margin_mm"]
            + breakdown["accessory_margin_mm"]
        )
        # H_calculated_mm은 계산값, H_total_mm은 기성함 규격 반올림값
        assert breakdown["H_calculated_mm"] == expected
        assert H_total == breakdown["H_total_mm"]
        # H_total은 H_calculated 이상 (업사이징만)
        assert H_total >= expected

    def test_height_with_accessories(
        self, solver, sample_main_breaker, sample_branch_breakers, sample_accessories
    ):
        """부속자재 포함 시 높이 계산"""
        H_total, breakdown = solver.calculate_height(
            main_breaker=sample_main_breaker,
            branch_breakers=sample_branch_breakers,
            accessories=sample_accessories,
        )

        # 마그네트 2개 → 하단 배치 여유 250mm 추가
        assert breakdown["accessory_margin_mm"] == 250.0
        # H = top + main(130) + gap(15) + branches(250) + bottom + accessories(250) > 600
        assert H_total > 600

    def test_height_small_breaker(self, solver):
        """소형 차단기 (32AF 2P) 마주보기 규칙"""
        main = BreakerSpec(
            id="main", model="SBS-102", poles=2, current_a=100, frame_af=100
        )
        branches = [
            BreakerSpec(id=f"b{i}", model="SIE-32", poles=2, current_a=20, frame_af=32)
            for i in range(5)
        ]

        H_total, breakdown = solver.calculate_height(main, branches, [])

        # 소형 2P 마주보기: 5개 → 3행 × 40mm = 120mm
        assert breakdown["branches_total_height_mm"] == 3 * 40


class TestCalculateWidth:
    """폭 계산 테스트"""

    def test_width_50_100af(self, solver):
        """50~100AF: 기본 600mm"""
        main = BreakerSpec(
            id="main", model="SBE-102", poles=2, current_a=60, frame_af=100
        )
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 100
        assert breakdown["W_base_mm"] == 600
        assert breakdown["width_bumped"] is False
        assert W_total == 600

    def test_width_400af_with_large_branches(self, solver):
        """400AF + 200~250AF 분기 ≥2개 → 폭 증가"""
        main = BreakerSpec(
            id="main", model="SBS-403", poles=3, current_a=300, frame_af=400
        )
        branches = [
            BreakerSpec(id="b1", model="SBS-202", poles=2, current_a=125, frame_af=200),
            BreakerSpec(id="b2", model="SBS-203", poles=3, current_a=150, frame_af=200),
        ]

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 400
        assert breakdown["branch_200_250_count"] == 2
        assert breakdown["width_bumped"] is True
        assert W_total == 900  # 800 → 900 증가

    def test_width_600af(self, solver):
        """600~800AF: 기본 900mm"""
        main = BreakerSpec(
            id="main", model="SBS-603", poles=3, current_a=500, frame_af=600
        )
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 600
        assert W_total == 900


class TestCalculateDepth:
    """깊이 계산 테스트"""

    def test_depth_without_pbl(self, solver):
        """PBL 없음 → 기본 150mm"""
        accessories = [
            AccessorySpec(type="magnet", model="MC-22", quantity=1),
        ]

        D_total, breakdown = solver.calculate_depth(accessories)

        assert breakdown["has_pbl"] is False
        assert breakdown["D_total_mm"] == 150
        assert D_total == 150
        assert "기본 150mm" in breakdown["reason"]

    def test_depth_with_pbl(self, solver):
        """PBL 포함 → 200mm"""
        accessories = [
            AccessorySpec(type="pbl", model="PBL-LED", quantity=2),
        ]

        D_total, breakdown = solver.calculate_depth(accessories)

        assert breakdown["has_pbl"] is True
        assert breakdown["D_total_mm"] == 200
        assert D_total == 200
        assert "PBL 포함" in breakdown["reason"]


class TestSolveIntegration:
    """통합 계산 테스트"""

    @pytest.mark.asyncio
    async def test_solve_basic(
        self,
        solver,
        sample_main_breaker,
        customer_requirements,
    ):
        """기본 통합 계산 (fit_score ≥ 0.90 검증)"""
        # 카탈로그 매칭 가능한 작은 분기 (5개)
        branches = [
            BreakerSpec(id=f"b{i}", model="SBE-52", poles=2, current_a=30, frame_af=50)
            for i in range(5)
        ]

        result = await solver.solve(
            main_breaker=sample_main_breaker,
            branch_breakers=branches,
            accessories=[],
            customer_requirements=customer_requirements,
        )

        # 치수 검증
        assert result.dimensions.width_mm > 0
        assert result.dimensions.height_mm > 0
        assert result.dimensions.depth_mm > 0

        # 후보 검증 (기성함 찾아야 함)
        assert (
            len(result.candidates) > 0
        ), f"HDS 카탈로그에서 후보를 찾지 못함 (계산: {result.dimensions.width_mm}×{result.dimensions.height_mm}×{result.dimensions.depth_mm})"

        # 품질 게이트 검증
        assert result.quality_gate.name == "fit_score_check"
        assert result.quality_gate.threshold == 0.90
        assert result.quality_gate.operator == ">="
        assert result.quality_gate.critical is True

        # fit_score ≥ 0.90 (필수)
        assert result.quality_gate.actual >= 0.90, "fit_score 품질 게이트 실패"
        assert result.quality_gate.passed is True

        # 계산 상세 검증
        assert "H_breakdown" in result.calculation_details
        assert "W_breakdown" in result.calculation_details
        assert "D_breakdown" in result.calculation_details

    @pytest.mark.asyncio
    async def test_solve_finds_exact_match(
        self,
        solver,
        customer_requirements,
    ):
        """정확한 크기 매칭 시나리오"""
        # 600×1600×150 (카탈로그에 있는 크기 가정)
        main = BreakerSpec(
            id="main", model="SBE-102", poles=2, current_a=60, frame_af=100
        )
        branches = [
            BreakerSpec(id=f"b{i}", model="SBE-52", poles=2, current_a=30, frame_af=50)
            for i in range(8)
        ]

        result = await solver.solve(main, branches, [], customer_requirements)

        # 후보 확인
        assert len(result.candidates) > 0

        # exact 또는 nearest 매칭
        match_types = [c.match_type for c in result.candidates]
        assert "exact" in match_types or "nearest" in match_types

        # fit_score = 1.0 (기성함 찾음)
        assert result.quality_gate.actual == 1.0
        assert result.quality_gate.passed is True

    @pytest.mark.asyncio
    async def test_solve_no_catalog_match(
        self,
        solver,
        customer_requirements,
        monkeypatch,
    ):
        """카탈로그 매칭 실패 → fit_score = 0.0"""
        from kis_estimator_core.engine import catalog_loader

        # 카탈로그 로더를 목업으로 대체 (매칭 실패 시뮬레이션)
        class MockCatalogLoader:
            async def find_exact_match(self, *args, **kwargs):
                return None

            async def find_nearest_match(self, *args, **kwargs):
                return None

        async def async_mock_loader():
            return MockCatalogLoader()

        monkeypatch.setattr(catalog_loader, "get_catalog_loader", async_mock_loader)

        main = BreakerSpec(
            id="main", model="SBS-102", poles=2, current_a=100, frame_af=100
        )
        branches = []

        result = await solver.solve(main, branches, [], customer_requirements)

        # 후보 없음
        assert len(result.candidates) == 0

        # fit_score = 0.0 (주문제작)
        assert result.quality_gate.actual == 0.0
        assert result.quality_gate.passed is False


class TestEdgeCases:
    """엣지 케이스 및 예외 처리"""

    @pytest.mark.asyncio
    async def test_empty_branch_breakers(
        self, solver, sample_main_breaker, customer_requirements
    ):
        """분기 차단기 없음"""
        result = await solver.solve(
            main_breaker=sample_main_breaker,
            branch_breakers=[],
            accessories=[],
            customer_requirements=customer_requirements,
        )

        assert result.dimensions.height_mm > 0
        assert (
            result.calculation_details["H_breakdown"]["branches_total_height_mm"] == 0
        )

    @pytest.mark.asyncio
    async def test_many_magnets(
        self, solver, sample_main_breaker, customer_requirements
    ):
        """마그네트 10개 (2줄 배치)"""
        accessories = [
            AccessorySpec(type="magnet", model="MC-22", quantity=1) for _ in range(10)
        ]

        result = await solver.solve(
            main_breaker=sample_main_breaker,
            branch_breakers=[],
            accessories=accessories,
            customer_requirements=customer_requirements,
        )

        # 마그네트 10개 → 2줄 → +500mm
        H_breakdown = result.calculation_details["H_breakdown"]
        assert H_breakdown["accessory_margin_mm"] == 500.0

    @pytest.mark.asyncio
    async def test_invalid_breaker_af(self, solver, customer_requirements):
        """지원하지 않는 AF 값 → EstimatorError"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        invalid_main = BreakerSpec(
            id="main",
            model="UNKNOWN-999",
            poles=3,
            current_a=1000,
            frame_af=9999,  # 지원 안 됨
        )

        with pytest.raises(EstimatorError) as exc_info:
            await solver.solve(invalid_main, [], [], customer_requirements)

        assert "AF=9999" in str(exc_info.value)


@pytest.mark.integration
class TestRealScenarios:
    """실제 시나리오 테스트 (Task 9 기반)"""

    @pytest.mark.asyncio
    async def test_task9_scenario(self, solver, customer_requirements):
        """Task 9 통합 테스트 시나리오 재현"""
        # Main: SBS-102 100AF 2P 100A
        main = BreakerSpec(
            id="main", model="SBS-102", poles=2, current_a=100, frame_af=100
        )

        # Branches: 10개
        branches = [
            BreakerSpec(id=f"b{i}", model="SBE-52", poles=2, current_a=30, frame_af=50)
            for i in range(10)
        ]

        result = await solver.solve(main, branches, [], customer_requirements)

        # 계산 결과 검증: 마주보기 배치로 높이 크게 감소
        # 10개 분기 → 5행 × 50mm = 250mm, 전체 ~675mm → 기성함 700mm
        assert result.dimensions.width_mm == 600
        assert 600 <= result.dimensions.height_mm <= 800  # 마주보기 배치로 높이 감소
        assert result.dimensions.depth_mm == 150

        # HDS 카탈로그 매칭 (Task 9: 700×1800×250)
        assert len(result.candidates) > 0
        selected = result.candidates[0]
        assert selected.size_mm[0] >= 600  # 폭은 크거나 같음
        assert selected.size_mm[1] >= result.dimensions.height_mm  # 높이도 크거나 같음
        assert selected.price > 0

        # fit_score = 1.0 (기성함 찾음)
        assert result.quality_gate.actual == 1.0
        assert result.quality_gate.passed is True
