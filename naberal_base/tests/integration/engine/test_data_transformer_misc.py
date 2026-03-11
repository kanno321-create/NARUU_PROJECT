"""

# Catalog dependency → requires DB
pytestmark = pytest.mark.requires_db

Tests for DataTransformer misc materials and assembly charge calculation methods.

Zero-Mock Policy: Simple mock objects for testing business logic.
"""

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

    def __init__(self, frame_af: int = 100):
        self.frame_af = frame_af


class TestDataTransformerMiscMaterials:
    """_calculate_misc_materials method tests."""

    def test_calculate_misc_materials_basic(self):
        """
        기본 잡자재비 계산.
        CEO 규칙: 기본값 7,000원 + H값 증분 (기준 H=700mm, 800mm부터 100mm당 +1,000원)
        """
        transformer = DataTransformer()

        # 600×700×200 (H=700mm → 기준값이므로 증분 0)
        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        accessories_count = 0
        main_breaker = MockBreakerItem(frame_af=100)

        item = transformer._calculate_misc_materials(
            enclosure_result, accessories_count, main_breaker
        )

        assert item is not None
        assert item.item_name == "잡자재비"
        assert item.unit == "식"
        assert item.quantity == 1
        # 7000 (기본) + 0 (H=700mm 기준이므로 증분 없음) = 7,000원
        assert item.unit_price == 7000

    def test_calculate_misc_materials_with_accessories(self):
        """
        부속자재 포함 시: 1개당 +10,000원.
        CEO 규칙: 기준 H=700mm이므로 H증분 0
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        accessories_count = 3  # 3개 → 30,000원 추가

        item = transformer._calculate_misc_materials(
            enclosure_result, accessories_count
        )

        assert item is not None
        # 7000 (기본) + 0 (H=700mm 기준) + 30000 (부속 3개) = 37,000원
        assert item.unit_price == 37000

    def test_calculate_misc_materials_main_only_with_busbar(self):
        """
        메인차단기만 + 부스바 처리 옵션 (400AF 이상): +15,000원.
        CEO 규칙: 기준 H=700mm이므로 H증분 0
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        accessories_count = 0
        main_breaker = MockBreakerItem(frame_af=400)

        item = transformer._calculate_misc_materials(
            enclosure_result,
            accessories_count,
            main_breaker=main_breaker,
            is_main_only=True,
            has_busbar_option=True,
        )

        assert item is not None
        # 7000 (기본) + 0 (H=700mm 기준) + 15000 (부스바) = 22,000원
        assert item.unit_price == 22000

    def test_calculate_misc_materials_max_cap(self):
        """
        최대값 55,000원 cap 확인 (실측 보정: 40,000→55,000).
        """
        transformer = DataTransformer()

        # H=1500mm → ((1500-700)//100) × 1,500 = 12,000원 증분
        enclosure_result = MockEnclosureResult(width=600, height=1500, depth=200)
        accessories_count = 10  # 100,000원 추가

        item = transformer._calculate_misc_materials(
            enclosure_result, accessories_count
        )

        assert item is not None
        # 7000 + 12000 + 100000 = 119,000 → 55,000 (max cap)
        assert item.unit_price == 55000

    def test_calculate_misc_materials_no_dimensions(self):
        """
        dimensions가 None이면 None 반환.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(600, 700, 200)
        enclosure_result.dimensions = None

        item = transformer._calculate_misc_materials(enclosure_result, 0)

        assert item is None


class TestDataTransformerAssemblyCharge:
    """_calculate_assembly_charge method tests."""

    def test_assembly_charge_main_only_100af(self):
        """
        메인차단기만 (50~250AF): 15,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=True
        )

        assert item is not None
        assert item.item_name == "ASSEMBLY CHARGE"
        assert item.spec == "조립비"
        assert item.unit == "식"
        assert item.quantity == 1
        assert item.unit_price == 15000

    def test_assembly_charge_main_only_400af(self):
        """
        메인차단기만 (400AF): 20,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=400)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=True
        )

        assert item is not None
        assert item.unit_price == 20000

    def test_assembly_charge_main_only_600af(self):
        """
        메인차단기만 (600~800AF): 30,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=600)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=True
        )

        assert item is not None
        assert item.unit_price == 30000

    def test_assembly_charge_main_only_with_busbar_400af(self):
        """
        메인차단기만 + 부스바 처리 (400AF): 20,000 + 40,000 = 60,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=400)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=True, has_busbar_option=True
        )

        assert item is not None
        assert item.unit_price == 60000  # 20,000 + 40,000

    def test_assembly_charge_main_only_with_busbar_600af(self):
        """
        메인차단기만 + 부스바 처리 (600AF): 30,000 + 70,000 = 100,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=600)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=True, has_busbar_option=True
        )

        assert item is not None
        assert item.unit_price == 100000  # 30,000 + 70,000

    def test_assembly_charge_with_branches_100af(self):
        """
        일반 견적 (분기 있음, 100AF).
        CEO 규칙 (2024-12-05): base_price + ((H - base_H) / 100) × h_increment
        100AF: base_price=50,000, base_H=700, h_increment=15,000
        H=700 → 50,000 + 0 = 50,000원
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=False
        )

        assert item is not None
        assert item.unit_price == 50000

    def test_assembly_charge_with_branches_200af(self):
        """
        일반 견적 (200AF).
        CEO 규칙 (2024-12-05): base_price=60,000, base_H=800
        H=800 → 60,000 + 0 = 60,000원
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=700, height=800, depth=250)
        main_breaker = MockBreakerItem(frame_af=200)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=False
        )

        assert item is not None
        assert item.unit_price == 60000

    def test_assembly_charge_with_branches_400af(self):
        """
        일반 견적 (400AF).
        CEO 규칙 (2024-12-05): base_price=130,000, base_H=1200
        H=900 < base_H(1200) → 130,000 + 0 = 130,000원
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=900, depth=250)
        main_breaker = MockBreakerItem(frame_af=400)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=False
        )

        assert item is not None
        assert item.unit_price == 130000

    def test_assembly_charge_with_branches_600af(self):
        """
        일반 견적 (600AF).
        CEO 규칙 (2024-12-05): base_price=250,000, base_H=1600
        H=1000 < base_H(1600) → 250,000 + 0 = 250,000원
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=900, height=1000, depth=300)
        main_breaker = MockBreakerItem(frame_af=600)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=False
        )

        assert item is not None
        assert item.unit_price == 250000

    def test_assembly_charge_with_h_increment(self):
        """
        H 증분 테스트 (CEO 규칙 2024-12-05).
        100AF: base_price=50,000, base_H=700, h_increment=15,000
        H=1100 → 50,000 + ((1100-700)//100 × 15,000) = 50,000 + 60,000 = 110,000원
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=1100, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)

        item = transformer._calculate_assembly_charge(
            enclosure_result, main_breaker, is_main_only=False
        )

        assert item is not None
        assert item.unit_price == 110000

    def test_assembly_charge_no_main_breaker(self):
        """
        메인차단기가 None이면 None 반환.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)

        item = transformer._calculate_assembly_charge(enclosure_result, None)

        assert item is None
