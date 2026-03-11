"""

# Catalog dependency → requires DB
pytestmark = pytest.mark.requires_db

Tests for DataTransformer busbar calculation methods.

Zero-Mock Policy: Simple mock objects for testing business logic.
"""

import pytest
from kis_estimator_core.engine.data_transformer import DataTransformer


class MockDimensions:
    """Mock dimensions for testing."""

    def __init__(self, width: int, height: int, depth: int):
        self.width_mm = width
        self.height_mm = height
        self.depth_mm = depth


class MockEnclosureResult:
    """Mock enclosure result for testing."""

    def __init__(self, width: int, height: int, depth: int):
        self.dimensions = MockDimensions(width, height, depth)


class MockBreakerItem:
    """Mock breaker item for testing."""

    def __init__(self, current_a: float, frame_af: int = 100, model: str = "AUTO"):
        self.current_a = current_a
        self.frame_af = frame_af
        self.model = model


class TestDataTransformerBusbar:
    """Busbar calculation method tests."""

    def test_calculate_busbar_50af_breaker(self):
        """
        50AF 메인차단기 (20~250A 범위).
        계수: 0.000007, 규격: 5T*20
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(current_a=50.0, frame_af=50)

        busbar = transformer._calculate_busbar(enclosure_result, main_breaker)

        assert busbar is not None
        assert busbar.item_name == "MAIN BUS-BAR"
        # CEO 규칙: 0~100A → 3T*15 (50A는 100A 이하이므로 3T*15)
        assert busbar.thickness_width == "3T*15"
        assert busbar.unit == "kg"
        assert busbar.unit_price == 31000  # SSOT: PRICE_BUSBAR_PER_KG (2026-02-06 원자재 상승)
        # 중량: (600*800) * 0.000007 = 3.36kg → 반올림 3.4kg (SSOT: BUSBAR_COEFF_20_250A)
        expected_weight = round((600 * 800) * 0.000007, 1)
        assert busbar.quantity == expected_weight
        assert busbar.weight_kg == expected_weight

    def test_calculate_busbar_400af_breaker(self):
        """
        400AF 메인차단기 (300~400A 범위).
        계수: 0.000013, 규격: 6T*30
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=1000, depth=250)
        main_breaker = MockBreakerItem(current_a=300.0, frame_af=400)

        busbar = transformer._calculate_busbar(enclosure_result, main_breaker)

        assert busbar is not None
        assert busbar.thickness_width == "6T*30"
        # 중량: (800*1000) * 0.000013 = 10.4kg
        expected_weight = round((800 * 1000) * 0.000013, 1)
        assert busbar.weight_kg == expected_weight

    def test_calculate_busbar_600af_breaker(self):
        """
        600AF 메인차단기 (500~800A 범위).
        계수: 0.000015, 규격: 8T*40
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=900, height=1200, depth=300)
        main_breaker = MockBreakerItem(current_a=600.0, frame_af=600)

        busbar = transformer._calculate_busbar(enclosure_result, main_breaker)

        assert busbar is not None
        assert busbar.thickness_width == "8T*40"
        # 중량: (900*1200) * 0.000015 = 16.2kg
        expected_weight = round((900 * 1200) * 0.000015, 1)
        assert busbar.weight_kg == expected_weight

    def test_calculate_busbar_no_main_breaker(self):
        """
        메인차단기가 None인 경우 → None 반환.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)

        busbar = transformer._calculate_busbar(enclosure_result, None)

        assert busbar is None

    def test_calculate_busbar_no_dimensions(self):
        """
        dimensions가 None인 경우 → 에러 발생.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(600, 800, 200)
        enclosure_result.dimensions = None  # dimensions 제거
        main_breaker = MockBreakerItem(current_a=60.0)

        with pytest.raises(Exception) as exc_info:
            transformer._calculate_busbar(enclosure_result, main_breaker)

        assert "dimensions가 없습니다" in str(exc_info.value) or "목업 금지" in str(
            exc_info.value
        )

    def test_calculate_branch_busbar_single_branch(self):
        """
        분기 차단기 1개 (100AF).
        규격: 3T*15 (50~125AF 범위)
        계수: BRANCH_BUSBAR_COEFF_20_250A = 0.0000045 (SSOT)
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        branch_breakers = [MockBreakerItem(current_a=30.0, frame_af=100)]

        busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)

        assert busbar is not None
        assert busbar.item_name == "BUS-BAR"
        assert busbar.thickness_width == "3T*15"
        # 중량: (600*800) * 0.0000045 = 2.16kg → 2.2kg (SSOT: BRANCH_BUSBAR_COEFF_20_250A)
        expected_weight = round((600 * 800) * 0.0000045, 1)
        assert busbar.weight_kg == expected_weight

    def test_calculate_branch_busbar_multiple_branches(self):
        """
        여러 분기 차단기 중 AF 가장 높은 것 기준.
        200AF → 5T*20, 계수: BRANCH_BUSBAR_COEFF_20_250A = 0.0000045 (SSOT)
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=700, height=900, depth=250)
        branch_breakers = [
            MockBreakerItem(current_a=30.0, frame_af=50),
            MockBreakerItem(current_a=50.0, frame_af=100),
            MockBreakerItem(current_a=75.0, frame_af=200),  # 가장 높음
        ]

        busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)

        assert busbar is not None
        # 200AF → 5T*20, 계수 0.0000045 (SSOT: BRANCH_BUSBAR_COEFF_20_250A)
        assert busbar.thickness_width == "5T*20"
        expected_weight = round((700 * 900) * 0.0000045, 1)
        assert busbar.weight_kg == expected_weight

    def test_calculate_branch_busbar_no_branches(self):
        """
        분기 차단기가 없으면 None 반환.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        branch_breakers = []

        busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)

        assert busbar is None

    def test_calculate_branch_busbar_400af(self):
        """
        400AF 분기 차단기 → 6T*30, 계수: BRANCH_BUSBAR_COEFF_300_400A = 0.000007 (SSOT)
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=1000, depth=250)
        branch_breakers = [MockBreakerItem(current_a=300.0, frame_af=400)]

        busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)

        assert busbar is not None
        assert busbar.thickness_width == "6T*30"
        # 중량: (800*1000) * 0.000007 = 5.6kg (SSOT: BRANCH_BUSBAR_COEFF_300_400A)
        expected_weight = round((800 * 1000) * 0.000007, 1)
        assert busbar.weight_kg == expected_weight

    def test_calculate_branch_busbar_800af(self):
        """
        800AF 분기 차단기 → 8T*40, 계수: BRANCH_BUSBAR_COEFF_500_800A = 0.000009 (SSOT)
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=900, height=1200, depth=300)
        branch_breakers = [MockBreakerItem(current_a=800.0, frame_af=800)]

        busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)

        assert busbar is not None
        assert busbar.thickness_width == "8T*40"
        # 중량: (900*1200) * 0.000009 = 9.72kg → 9.7kg (SSOT: BRANCH_BUSBAR_COEFF_500_800A)
        expected_weight = round((900 * 1200) * 0.000009, 1)
        assert busbar.weight_kg == expected_weight
