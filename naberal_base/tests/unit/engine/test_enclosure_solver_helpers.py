"""
Test enclosure_solver.py - Private helper methods
Phase I-5 Wave 8b (4/6)

Zero-Mock 준수: 실제 지식파일 사용
"""

import pytest
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver


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


@pytest.mark.unit
class TestEnclosureSolverHelperMethods:
    """Private helper methods 테스트"""

    @pytest.fixture
    def solver(self):
        return EnclosureSolver()

    # _get_top_margin 테스트
    def test_get_top_margin_50af(self, solver):
        """50AF: 상단 여유 조회."""
        margin = solver._get_top_margin(50)
        assert margin > 0

    def test_get_top_margin_100af(self, solver):
        """100AF: 상단 여유 조회."""
        margin = solver._get_top_margin(100)
        assert margin > 0

    def test_get_top_margin_200af(self, solver):
        """200AF: 상단 여유 조회."""
        margin = solver._get_top_margin(200)
        assert margin > 0

    def test_get_top_margin_400af(self, solver):
        """400AF: 상단 여유 조회."""
        margin = solver._get_top_margin(400)
        assert margin > 0

    def test_get_top_margin_600af(self, solver):
        """600AF: 상단 여유 조회."""
        margin = solver._get_top_margin(600)
        assert margin > 0

    # _get_bottom_margin 테스트
    def test_get_bottom_margin_50af(self, solver):
        """50AF: 하단 여유 조회."""
        margin = solver._get_bottom_margin(50)
        assert margin > 0

    def test_get_bottom_margin_100af(self, solver):
        """100AF: 하단 여유 조회."""
        margin = solver._get_bottom_margin(100)
        assert margin > 0

    def test_get_bottom_margin_200af(self, solver):
        """200AF: 하단 여유 조회."""
        margin = solver._get_bottom_margin(200)
        assert margin > 0

    def test_get_bottom_margin_400af(self, solver):
        """400AF: 하단 여유 조회."""
        margin = solver._get_bottom_margin(400)
        assert margin > 0

    def test_get_bottom_margin_600af(self, solver):
        """600AF: 하단 여유 조회."""
        margin = solver._get_bottom_margin(600)
        assert margin > 0

    # _get_breaker_height 테스트
    def test_get_breaker_height_2p_50af(self, solver):
        """2P 50AF 차단기 높이."""
        breaker = MockBreakerSpec(poles=2, frame_af=50)
        height = solver._get_breaker_height(breaker)
        assert height > 0

    def test_get_breaker_height_3p_100af(self, solver):
        """3P 100AF 차단기 높이."""
        breaker = MockBreakerSpec(poles=3, frame_af=100)
        height = solver._get_breaker_height(breaker)
        assert height > 0

    def test_get_breaker_height_4p_200af(self, solver):
        """4P 200AF 차단기 높이."""
        breaker = MockBreakerSpec(poles=4, frame_af=200)
        height = solver._get_breaker_height(breaker)
        assert height > 0

    def test_get_breaker_height_4p_400af(self, solver):
        """4P 400AF 차단기 높이."""
        breaker = MockBreakerSpec(poles=4, frame_af=400)
        height = solver._get_breaker_height(breaker)
        assert height > 0

    def test_get_breaker_height_4p_600af(self, solver):
        """4P 600AF 차단기 높이."""
        breaker = MockBreakerSpec(poles=4, frame_af=600)
        height = solver._get_breaker_height(breaker)
        assert height > 0

    # _calculate_branches_height 테스트
    def test_calculate_branches_height_empty(self, solver):
        """분기 없음: 높이 = 0."""
        branches = []
        height = solver._calculate_branches_height(branches)
        assert height == 0.0

    def test_calculate_branches_height_single(self, solver):
        """분기 1개."""
        branches = [MockBreakerSpec(poles=2, frame_af=50)]
        height = solver._calculate_branches_height(branches)
        assert height > 0

    def test_calculate_branches_height_multiple(self, solver):
        """분기 5개."""
        branches = [
            MockBreakerSpec(poles=2, frame_af=50),
            MockBreakerSpec(poles=2, frame_af=50),
            MockBreakerSpec(poles=3, frame_af=100),
            MockBreakerSpec(poles=3, frame_af=100),
            MockBreakerSpec(poles=4, frame_af=200),
        ]
        height = solver._calculate_branches_height(branches)
        assert height > 0

    def test_calculate_branches_height_large_estimate(self, solver):
        """분기 20개: 마주보기 배치 (20+1)//2 = 10행 × 50mm = 500mm"""
        branches = [MockBreakerSpec(poles=2, frame_af=50) for _ in range(20)]
        height = solver._calculate_branches_height(branches)
        assert height >= 500.0  # 10행 × 50mm = 500mm

    # _calculate_accessory_margin 테스트
    def test_calculate_accessory_margin_empty(self, solver):
        """부속자재 없음: 여유 = 0."""
        accessories = []
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0

    def test_calculate_accessory_margin_1_magnet(self, solver):
        """마그네트 1개: 메인 옆 배치 (H 변화 없음)."""
        accessories = [MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1)]
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0  # 메인 옆 빈 공간 배치

    def test_calculate_accessory_margin_2_magnets(self, solver):
        """마그네트 2개: +250mm (하단 배치)."""
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
        ]
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 250.0

    def test_calculate_accessory_margin_3_magnets(self, solver):
        """마그네트 3개: +250mm (하단 배치)."""
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-40", quantity=1),
        ]
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 250.0

    def test_calculate_accessory_margin_terminal(self, solver):
        """터미널만: 여유 = 0."""
        accessories = [MockAccessorySpec(type_name="TERMINAL", quantity=5)]
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0

    def test_calculate_accessory_margin_mixed(self, solver):
        """혼합 (마그네트 1개 + 터미널): H 변화 없음."""
        accessories = [
            MockAccessorySpec(type_name="TERMINAL", quantity=3),
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
        ]
        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0  # 마그네트 1개는 메인 옆 배치
