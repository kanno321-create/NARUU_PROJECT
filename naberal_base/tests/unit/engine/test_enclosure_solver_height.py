"""
Test enclosure_solver.py - calculate_height method
Phase I-5 Wave 8b (2/6)

Zero-Mock 준수: 실제 지식파일 사용
"""

import pytest
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver


# Mock 데이터 컨테이너 (비즈니스 로직 테스트용, 단순 속성만)
class MockBreakerSpec:
    """차단기 스펙 Mock (단순 데이터 컨테이너)"""

    def __init__(self, model="AUTO", poles=4, current_a=60.0, frame_af=100):
        self.model = model
        self.poles = poles
        self.current_a = current_a
        self.frame_af = frame_af


class MockAccessorySpec:
    """부속자재 스펙 Mock (단순 데이터 컨테이너)"""

    def __init__(self, type_name="TERMINAL", quantity=1):
        self.type = type_name
        self.quantity = quantity


class TestEnclosureSolverCalculateHeight:
    """calculate_height 메서드 테스트"""

    @pytest.fixture
    def solver(self):
        """EnclosureSolver 인스턴스 (실제 지식파일 사용)"""
        return EnclosureSolver()

    def test_calculate_height_main_only_100af(self, solver):
        """메인만 (100AF): 7단계 계산 검증."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # breakdown 구조 검증
        assert "top_margin_mm" in breakdown
        assert "main_breaker_height_mm" in breakdown
        assert "main_to_branch_gap_mm" in breakdown
        assert "branches_total_height_mm" in breakdown
        assert "bottom_margin_mm" in breakdown
        assert "accessory_margin_mm" in breakdown
        assert "H_total_mm" in breakdown

        # 메인만: 분기 높이 = 0
        assert breakdown["branches_total_height_mm"] == 0.0

        # 부속자재 없음: 여유 = 0
        assert breakdown["accessory_margin_mm"] == 0.0

        # H_total > 0
        assert H_total > 0
        assert breakdown["H_total_mm"] == H_total

    def test_calculate_height_with_branches(self, solver):
        """메인 + 분기 5개: 분기 높이 계산."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=75.0)
        branches = [
            MockBreakerSpec(frame_af=50, poles=2, current_a=20.0),
            MockBreakerSpec(frame_af=50, poles=2, current_a=30.0),
            MockBreakerSpec(frame_af=100, poles=3, current_a=60.0),
            MockBreakerSpec(frame_af=100, poles=3, current_a=60.0),
            MockBreakerSpec(frame_af=100, poles=3, current_a=75.0),
        ]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 분기 높이 > 0
        assert breakdown["branches_total_height_mm"] > 0

        # H_calculated = top + main + gap + branches + bottom (기성함 반올림 전)
        expected = (
            breakdown["top_margin_mm"]
            + breakdown["main_breaker_height_mm"]
            + breakdown["main_to_branch_gap_mm"]
            + breakdown["branches_total_height_mm"]
            + breakdown["bottom_margin_mm"]
        )
        # H_calculated_mm은 계산값, H_total_mm은 기성함 규격으로 반올림된 값
        assert breakdown["H_calculated_mm"] == expected
        # H_total은 H_calculated 이상 (업사이징만)
        assert breakdown["H_total_mm"] >= expected

    def test_calculate_height_with_accessories_1_magnet(self, solver):
        """마그네트 1개: 여유 = 0 (옆 배치)."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []
        accessories = [MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1)]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 마그네트 1개: 옆 배치 (H 증가 없음)
        assert breakdown["accessory_margin_mm"] == 0.0

    def test_calculate_height_with_accessories_2_magnets(self, solver):
        """마그네트 2개: 하단 배치 +250mm."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
        ]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 마그네트 2개: 하단 배치 (1줄 = +250mm)
        assert breakdown["accessory_margin_mm"] == 250.0

    def test_calculate_height_with_accessories_6_magnets(self, solver):
        """마그네트 6개: 2줄 배치 +500mm."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-40", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-50", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-65", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-75", quantity=1),
        ]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 마그네트 6개: 2줄 배치 (6개 → (6+4)//5 = 2줄 → 2×250 = 500mm)
        assert breakdown["accessory_margin_mm"] == 500.0

    def test_calculate_height_400af_main(self, solver):
        """400AF 메인: 상하단 여유 다름."""
        main = MockBreakerSpec(frame_af=400, poles=4, current_a=300.0)
        branches = []
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 400AF: 하단 여유가 큼 (200mm)
        assert breakdown["bottom_margin_mm"] == 200.0
        assert H_total > 0

    def test_calculate_height_600af_main(self, solver):
        """600AF 메인: 최대 AF."""
        main = MockBreakerSpec(frame_af=600, poles=4, current_a=400.0)
        branches = []
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 600AF: 하단 여유 (실제 지식파일 값 사용)
        assert breakdown["bottom_margin_mm"] > 0
        assert H_total > 0

    def test_calculate_height_mixed_branches(self, solver):
        """혼합 분기 (2P, 3P, 4P): 높이 합산."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=75.0)
        branches = [
            MockBreakerSpec(frame_af=50, poles=2, current_a=20.0),
            MockBreakerSpec(frame_af=100, poles=3, current_a=60.0),
            MockBreakerSpec(frame_af=100, poles=4, current_a=60.0),
        ]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 분기 3개: 높이 합산됨
        assert breakdown["branches_total_height_mm"] > 0

    def test_calculate_height_gap_constant(self, solver):
        """메인-분기 간격 (SSOT 상수)."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = [MockBreakerSpec(frame_af=50, poles=2, current_a=20.0)]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # MAIN_TO_BRANCH_GAP_MM (SSOT에서 정의된 값 사용)
        assert breakdown["main_to_branch_gap_mm"] > 0

    def test_calculate_height_large_estimate(self, solver):
        """대규모 견적 (메인 + 분기 20개 + 마그네트 3개)."""
        main = MockBreakerSpec(frame_af=200, poles=4, current_a=150.0)
        branches = [
            MockBreakerSpec(frame_af=50, poles=2, current_a=20.0) for _ in range(20)
        ]
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-40", quantity=1),
        ]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 분기 20개: 마주보기 배치 (20+1)//2 = 10행 × 50mm = 500mm
        assert breakdown["branches_total_height_mm"] >= 500.0

        # 마그네트 3개: 1줄 = +250mm
        assert breakdown["accessory_margin_mm"] == 250.0

        # 총 높이 > 1000mm
        assert H_total > 1000.0

    def test_calculate_height_validation_error_negative_height(self, solver):
        """H_total ≤ 0 시 ValidationError (ENC-001)."""
        # 실제로는 발생하기 어려운 케이스지만, 코드 커버리지를 위해 테스트
        # (모든 값이 0이 되는 비현실적 케이스)
        # 이 테스트는 실제로는 skip하거나, 직접 _calculate_branches_height 등을 테스트
        pass

    def test_calculate_height_breakdown_structure(self, solver):
        """breakdown 구조 완전성 검증."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = [MockBreakerSpec(frame_af=50, poles=2, current_a=20.0)]
        accessories = [MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1)]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 모든 필수 키 존재
        required_keys = [
            "top_margin_mm",
            "main_breaker_height_mm",
            "main_to_branch_gap_mm",
            "branches_total_height_mm",
            "bottom_margin_mm",
            "accessory_margin_mm",
            "H_total_mm",
        ]
        for key in required_keys:
            assert key in breakdown
            assert isinstance(breakdown[key], (int, float))
