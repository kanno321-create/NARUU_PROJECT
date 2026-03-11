"""
Test enclosure_solver.py - calculate_width and calculate_depth
Phase I-5 Wave 8b (3/6)

Zero-Mock 준수: 실제 지식파일 사용
"""

import pytest
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver


class MockBreakerSpec:
    def __init__(self, model="AUTO", poles=4, current_a=60.0, frame_af=100):
        self.model = model
        self.poles = poles
        self.current_a = current_a
        self.frame_af = frame_af


class MockAccessorySpec:
    def __init__(self, type_name="TERMINAL", quantity=1):
        self.type = type_name
        self.quantity = quantity


class TestEnclosureSolverCalculateWidth:
    """calculate_width 메서드 테스트"""

    @pytest.fixture
    def solver(self):
        return EnclosureSolver()

    def test_calculate_width_50af(self, solver):
        """50AF: W=600mm (기본)."""
        main = MockBreakerSpec(frame_af=50, poles=2, current_a=20.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 50
        assert breakdown["W_base_mm"] > 0
        assert not breakdown["width_bumped"]
        assert W_total == breakdown["W_total_mm"]

    def test_calculate_width_100af(self, solver):
        """100AF: W=600mm (기본)."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 100
        assert breakdown["W_total_mm"] > 0

    def test_calculate_width_200af(self, solver):
        """200AF: W=700mm (기본)."""
        main = MockBreakerSpec(frame_af=200, poles=4, current_a=150.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 200
        assert W_total > 600  # 200AF는 더 넓음

    def test_calculate_width_400af(self, solver):
        """400AF: W=800mm (기본)."""
        main = MockBreakerSpec(frame_af=400, poles=4, current_a=300.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 400
        assert W_total >= 800

    def test_calculate_width_400af_with_bump(self, solver):
        """400AF + 200~250AF 분기 ≥2개: W bump."""
        main = MockBreakerSpec(frame_af=400, poles=4, current_a=300.0)
        branches = [
            MockBreakerSpec(frame_af=200, poles=3, current_a=150.0),
            MockBreakerSpec(frame_af=250, poles=3, current_a=200.0),
        ]

        W_total, breakdown = solver.calculate_width(main, branches)

        # bump_if 조건 충족 시 W 증가
        assert "branch_200_250_count" in breakdown
        assert breakdown["branch_200_250_count"] == 2

    def test_calculate_width_600af(self, solver):
        """600AF: W=900mm (기본)."""
        main = MockBreakerSpec(frame_af=600, poles=4, current_a=400.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        assert breakdown["main_af"] == 600
        assert W_total >= 900

    def test_calculate_width_breakdown_structure(self, solver):
        """breakdown 구조 검증."""
        main = MockBreakerSpec(frame_af=100, poles=4, current_a=60.0)
        branches = []

        W_total, breakdown = solver.calculate_width(main, branches)

        # 필수 키
        assert "main_af" in breakdown
        assert "W_base_mm" in breakdown
        assert "width_bumped" in breakdown
        assert "W_total_mm" in breakdown


class TestEnclosureSolverCalculateDepth:
    """calculate_depth 메서드 테스트"""

    @pytest.fixture
    def solver(self):
        return EnclosureSolver()

    def test_calculate_depth_no_pbl(self, solver):
        """PBL 없음: D=200mm (기본)."""
        accessories = []

        D_total, breakdown = solver.calculate_depth(accessories)

        assert not breakdown["has_pbl"]
        assert D_total > 0
        assert breakdown["D_total_mm"] == D_total

    def test_calculate_depth_with_pbl(self, solver):
        """PBL 포함: D 계산."""
        accessories = [MockAccessorySpec(type_name="PBL_ON/OFF", quantity=2)]

        D_total, breakdown = solver.calculate_depth(accessories)

        assert breakdown["has_pbl"]
        assert D_total >= 200  # PBL 포함 (지식파일에 따라 200mm 또는 250mm)

    def test_calculate_depth_push_button(self, solver):
        """push button 키워드: PBL로 인식."""
        accessories = [MockAccessorySpec(type_name="PUSH_BUTTON_RED", quantity=1)]

        D_total, breakdown = solver.calculate_depth(accessories)

        assert breakdown["has_pbl"]

    def test_calculate_depth_mixed_accessories(self, solver):
        """혼합 부속자재: PBL 포함 여부만 확인."""
        accessories = [
            MockAccessorySpec(type_name="TERMINAL", quantity=3),
            MockAccessorySpec(type_name="MAGNET_MC-22", quantity=1),
            MockAccessorySpec(type_name="PBL_ON/OFF", quantity=1),
        ]

        D_total, breakdown = solver.calculate_depth(accessories)

        assert breakdown["has_pbl"]

    def test_calculate_depth_breakdown_structure(self, solver):
        """breakdown 구조 검증."""
        accessories = []

        D_total, breakdown = solver.calculate_depth(accessories)

        assert "has_pbl" in breakdown
        assert "reason" in breakdown
        assert "D_total_mm" in breakdown
