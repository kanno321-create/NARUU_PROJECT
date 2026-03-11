"""
Test enclosure_solver.py - Edge cases and error paths
Phase I-5 Wave 8b (6/6)

Zero-Mock 준수: 실제 지식파일 사용, 오류 조건 검증
"""

import pytest
from pathlib import Path
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.errors import ValidationError
from kis_estimator_core.core.ssot.errors import EstimatorError


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
class TestEnclosureSolverEdgeCases:
    """Edge cases and error paths 테스트"""

    @pytest.fixture
    def solver(self):
        return EnclosureSolver()

    # ==================== __init__ 오류 케이스 ====================

    def test_init_with_missing_knowledge_file(self):
        """지식파일이 없을 때 오류."""
        fake_path = Path("/nonexistent/core_rules.json")

        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=fake_path)

        assert "지식파일을 찾을 수 없습니다" in str(exc_info.value)

    def test_init_with_incomplete_knowledge(self, tmp_path):
        """필수 섹션이 없는 지식파일."""
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text('{"breaker_dimensions_mm": {}}', encoding="utf-8")

        with pytest.raises(EstimatorError) as exc_info:
            EnclosureSolver(knowledge_path=incomplete_file)

        assert "필수 섹션이 없습니다" in str(exc_info.value)

    # ==================== calculate_height 오류 케이스 ====================

    def test_calculate_height_with_invalid_af(self, solver):
        """잘못된 AF 값 (지원하지 않는 프레임)."""
        main = MockBreakerSpec(frame_af=999, poles=4, current_a=60.0)
        branches = []
        accessories = []

        # 지원하지 않는 AF는 helper 메서드에서 오류 발생
        with pytest.raises(EstimatorError):
            solver.calculate_height(main, branches, accessories)

    def test_calculate_height_with_empty_branches_and_accessories(self, solver):
        """분기/부속자재 없음 (정상 케이스)."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        assert H_total > 0
        assert breakdown["branches_total_height_mm"] == 0.0
        assert breakdown["accessory_margin_mm"] == 0.0

    # ==================== calculate_width 오류 케이스 ====================

    def test_calculate_width_with_invalid_af(self, solver):
        """잘못된 AF 값 (지원하지 않는 프레임)."""
        main = MockBreakerSpec(frame_af=999, poles=4, current_a=60.0)
        branches = []

        with pytest.raises(ValidationError) as exc_info:
            solver.calculate_width(main, branches)

        assert exc_info.value.error_code.code == "ENC-002"

    def test_calculate_width_with_no_branches(self, solver):
        """분기 없음 (정상 케이스)."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert W_total > 0
        assert not breakdown["width_bumped"]

    # ==================== calculate_depth 오류 케이스 ====================

    def test_calculate_depth_with_empty_accessories(self, solver):
        """부속자재 없음 (정상 케이스)."""
        accessories = []

        D_total, breakdown = solver.calculate_depth(accessories)

        assert D_total > 0
        assert not breakdown["has_pbl"]

    # ==================== _get_breaker_height 오류 케이스 ====================

    def test_get_breaker_height_with_unsupported_af_poles(self, solver):
        """지원하지 않는 AF/Poles 조합."""
        breaker = MockBreakerSpec(frame_af=999, poles=5)  # 5P는 지원 안 함

        with pytest.raises(EstimatorError):
            solver._get_breaker_height(breaker)

    def test_get_breaker_height_with_fb_type(self, solver):
        """FB 타입 차단기."""
        breaker = MockBreakerSpec(model="FB-104", poles=4, frame_af=100)

        height = solver._get_breaker_height(breaker)
        assert height > 0

    # ==================== _calculate_branches_height 오류 케이스 ====================

    def test_calculate_branches_height_with_empty_list(self, solver):
        """빈 리스트 (정상 케이스)."""
        branches = []

        height = solver._calculate_branches_height(branches)
        assert height == 0.0

    def test_calculate_branches_height_with_invalid_breaker(self, solver):
        """잘못된 차단기 스펙."""
        branches = [MockBreakerSpec(frame_af=999, poles=5)]

        with pytest.raises(EstimatorError):
            solver._calculate_branches_height(branches)

    # ==================== _calculate_accessory_margin 경계값 테스트 ====================

    def test_calculate_accessory_margin_with_zero_magnets(self, solver):
        """마그네트 0개."""
        accessories = [MockAccessorySpec(type_name="TERMINAL", quantity=5)]

        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0

    def test_calculate_accessory_margin_with_1_magnet(self, solver):
        """마그네트 1개 (메인 옆 배치)."""
        accessories = [MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1)]

        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 0.0

    def test_calculate_accessory_margin_with_2_magnets(self, solver):
        """마그네트 2개 (하단 배치 시작)."""
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
        ]

        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 250.0

    def test_calculate_accessory_margin_with_5_magnets(self, solver):
        """마그네트 5개 (1줄 가득)."""
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-40", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-50", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-65", quantity=1),
        ]

        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 250.0  # 1줄

    def test_calculate_accessory_margin_with_6_magnets(self, solver):
        """마그네트 6개 (2줄 시작)."""
        accessories = [
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-32", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-40", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-50", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-65", quantity=1),
            MockAccessorySpec(type_name="MAGNET_MC-75", quantity=1),
        ]

        margin = solver._calculate_accessory_margin(accessories)
        assert margin == 500.0  # 2줄

    # ==================== 극한 케이스 (Extreme cases) ====================

    def test_extreme_large_estimate(self, solver):
        """극한 대규모 견적 (분기 100개)."""
        main = MockBreakerSpec(frame_af=600, poles=4, current_a=400.0)
        branches = [
            MockBreakerSpec(frame_af=50, poles=2, current_a=20.0) for _ in range(100)
        ]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # 100개 차단기 → H ≥ 2000mm
        assert H_total >= 2000
        assert breakdown["branches_total_height_mm"] > 1500

    def test_extreme_high_af(self, solver):
        """극한 AF (800AF)."""
        main = MockBreakerSpec(frame_af=800, poles=4, current_a=600.0)
        branches = []
        accessories = []

        H_total, _ = solver.calculate_height(main, branches, accessories)
        W_total, _ = solver.calculate_width(main, branches)

        assert H_total > 0
        assert W_total > 0

    def test_extreme_many_magnets(self, solver):
        """극한 마그네트 수량 (20개)."""
        accessories = [
            MockAccessorySpec(type_name=f"MAGNET_MC-{i}", quantity=1) for i in range(20)
        ]

        margin = solver._calculate_accessory_margin(accessories)
        # 20개 → (20+4)//5 = 4줄 → 4*250 = 1000mm
        assert margin == 1000.0
