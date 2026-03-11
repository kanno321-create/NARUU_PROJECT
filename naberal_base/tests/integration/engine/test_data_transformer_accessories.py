"""

# Catalog dependency → requires DB
pytestmark = pytest.mark.requires_db

Tests for DataTransformer accessories calculation methods.

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

    def __init__(self, frame_af: int = 100, model: str = "AUTO", poles: int = 4):
        self.frame_af = frame_af
        self.model = model
        self.poles = poles


class TestDataTransformerAccessoriesMainOnly:
    """_calculate_accessories method tests - main-only scenario."""

    def test_calculate_accessories_main_only_100af(self):
        """
        메인차단기만 (100AF 이하): E.T(1개, 4,500원) + N.P(1개, 1,500원).
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=700, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = []

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        assert len(accessories) == 2

        # E.T 확인
        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert len(et_items) == 1
        assert et_items[0].quantity == 1
        assert et_items[0].unit_price == 4500  # 100AF 이하

        # N.P 확인
        np_items = [a for a in accessories if a.item_name == "N.P"]
        assert len(np_items) == 1
        assert np_items[0].spec == "CARD HOLDER"
        assert np_items[0].quantity == 1
        assert np_items[0].unit_price == 1500

    def test_calculate_accessories_main_only_200af(self):
        """
        메인차단기만 (200AF): E.T 가격 5,500원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=700, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=200)
        branch_breakers = []

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert et_items[0].unit_price == 5500  # 200~250AF

    def test_calculate_accessories_main_only_400af(self):
        """
        메인차단기만 (400AF): E.T 가격 12,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=900, depth=250)
        main_breaker = MockBreakerItem(frame_af=400)
        branch_breakers = []

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert et_items[0].unit_price == 12000  # 400AF

    def test_calculate_accessories_main_only_600af(self):
        """
        메인차단기만 (600AF): E.T 가격 18,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=900, height=1000, depth=300)
        main_breaker = MockBreakerItem(frame_af=600)
        branch_breakers = []

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert et_items[0].unit_price == 18000  # 600~800AF


class TestDataTransformerAccessoriesGeneral:
    """_calculate_accessories method tests - general estimate with branches."""

    def test_calculate_accessories_et_quantity_12_breakers(self):
        """
        E.T 수량 공식: 차단기 < 12개 → E.T 1개.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(10)]  # 10개

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert et_items[0].quantity == 1  # < 12개

    def test_calculate_accessories_et_quantity_24_breakers(self):
        """
        E.T 수량 공식 (실측 보정):
        ≤125AF 소형: 차단기 수 ÷ 6.
        100AF, 총 25개 → 25 // 6 = 4
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=700, height=900, depth=250)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(24)]  # 총 25개

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        assert et_items[0].quantity == 4  # 25 // 6 = 4 (≤125AF 소형 공식)

    def test_calculate_accessories_et_quantity_50_breakers(self):
        """
        E.T 수량 공식 (실측 보정):
        ≤125AF 소형: 차단기 수 ÷ 6.
        100AF, 총 51개 → 51 // 6 = 8
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=700, height=1000, depth=250)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(50)]  # 총 51개

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        et_items = [a for a in accessories if a.item_name == "E.T"]
        # 51 // 6 = 8 (≤125AF 소형 공식)
        assert et_items[0].quantity == 8

    def test_calculate_accessories_nt_basic(self):
        """
        N.T (Neutral Terminal): 항상 1개, 3,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        nt_items = [a for a in accessories if a.item_name == "N.T"]
        assert len(nt_items) == 1
        assert nt_items[0].quantity == 1
        assert nt_items[0].unit_price == 3000

    def test_calculate_accessories_np_card_holder(self):
        """
        N.P (CARD HOLDER): 분기차단기 수량만큼, 800원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(8)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        np_card_holder = [
            a for a in accessories if a.item_name == "N.P" and a.spec == "CARD HOLDER"
        ]
        assert len(np_card_holder) == 1
        assert np_card_holder[0].quantity == 8  # 분기 수량
        assert np_card_holder[0].unit_price == 800

    def test_calculate_accessories_np_3t(self):
        """
        N.P (3T*40*200): 항상 1개, 4,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        np_3t = [
            a for a in accessories if a.item_name == "N.P" and a.spec == "3T*40*200"
        ]
        assert len(np_3t) == 1
        assert np_3t[0].quantity == 1
        assert np_3t[0].unit_price == 4000

    def test_calculate_accessories_coating(self):
        """
        COATING: PVC(20mm), 1개, 5,000원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        coating_items = [a for a in accessories if a.item_name == "COATING"]
        assert len(coating_items) == 1
        assert coating_items[0].spec == "PVC(20mm)"
        assert coating_items[0].unit == "M"
        assert coating_items[0].quantity == 1
        assert coating_items[0].unit_price == 5000

    def test_calculate_accessories_p_cover_price_formula(self):
        """
        P-COVER: 단가 = ((W×H) ÷ 90,000) × 3,200원.
        """
        transformer = DataTransformer()

        # 예: 600×800 = 480,000
        # (480,000 ÷ 90,000) × 3,200 = 5.33 × 3,200 = 17,066원 (정수)
        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        p_cover_items = [a for a in accessories if a.item_name == "P-COVER"]
        assert len(p_cover_items) == 1
        assert p_cover_items[0].spec == "아크릴(PC)"
        assert p_cover_items[0].quantity == 1

        # 가격 계산 검증
        expected_price = int(((600 * 800) / 90000) * 3200)
        assert p_cover_items[0].unit_price == expected_price

    def test_calculate_accessories_breaker_support_400af(self):
        """
        차단기지지대 (실측 보정 - CLAUDE_KNOWLEDGE 14.7):
        400~800AF만 생성, 2EA × 28,000원 고정.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=1000, depth=250)
        main_breaker = MockBreakerItem(frame_af=400)
        branch_breakers = [MockBreakerItem() for _ in range(10)]  # 10개

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        support_items = [a for a in accessories if a.item_name == "차단기지지대"]
        assert len(support_items) == 1
        assert support_items[0].quantity == 2  # 2EA 고정
        assert support_items[0].unit_price == 28000  # 28,000원 고정

    def test_calculate_accessories_breaker_support_not_for_100af(self):
        """
        차단기지지대: 100AF에서는 생성되지 않음.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(10)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        support_items = [a for a in accessories if a.item_name == "차단기지지대"]
        assert len(support_items) == 0  # 100AF는 지지대 불필요

    def test_calculate_accessories_elb_support(self):
        """
        ELB지지대: 소형차단기 수량만큼 생성.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)

        # 소형차단기 3개 (소형 차단기는 반드시 2P)
        small_breaker1 = MockBreakerItem(frame_af=50, model="SIE-32", poles=2)
        small_breaker2 = MockBreakerItem(frame_af=50, model="SIB-32", poles=2)
        small_breaker3 = MockBreakerItem(frame_af=50, model="32GRHS", poles=2)
        normal_breaker = MockBreakerItem(frame_af=100, model="SBE-104", poles=4)

        branch_breakers = [
            small_breaker1,
            small_breaker2,
            small_breaker3,
            normal_breaker,
        ]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        elb_support_items = [a for a in accessories if a.item_name == "ELB지지대"]
        assert len(elb_support_items) == 1
        assert elb_support_items[0].quantity == 3  # 소형 3개
        assert elb_support_items[0].unit_price == 500

    def test_calculate_accessories_elb_support_no_small_breakers(self):
        """
        ELB지지대: 소형차단기가 없으면 생성되지 않음.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem(frame_af=100) for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        elb_support_items = [a for a in accessories if a.item_name == "ELB지지대"]
        assert len(elb_support_items) == 0

    def test_calculate_accessories_insulator_100af(self):
        """
        INSULATOR: 항상 4개, 100AF 이하는 1,100원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        insulator_items = [a for a in accessories if a.item_name == "INSULATOR"]
        assert len(insulator_items) == 1
        assert insulator_items[0].spec == "EPOXY 40*40"
        assert insulator_items[0].quantity == 4
        assert insulator_items[0].unit_price == 1100  # ≤250AF

    def test_calculate_accessories_insulator_400af(self):
        """
        INSULATOR: 400AF 이상은 4,400원.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=800, height=1000, depth=250)
        main_breaker = MockBreakerItem(frame_af=400)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        insulator_items = [a for a in accessories if a.item_name == "INSULATOR"]
        assert insulator_items[0].unit_price == 4400  # ≥400AF

    def test_calculate_accessories_no_main_breaker(self):
        """
        메인차단기가 None이면 빈 리스트 반환.
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        branch_breakers = [MockBreakerItem() for _ in range(5)]

        accessories = transformer._calculate_accessories(
            enclosure_result, None, branch_breakers
        )

        assert len(accessories) == 0

    def test_calculate_accessories_complete_general_estimate(self):
        """
        일반 견적 전체 품목 검증 (11가지 품목).
        """
        transformer = DataTransformer()

        enclosure_result = MockEnclosureResult(width=600, height=800, depth=200)
        main_breaker = MockBreakerItem(frame_af=100)
        branch_breakers = [MockBreakerItem() for _ in range(10)]

        accessories = transformer._calculate_accessories(
            enclosure_result, main_breaker, branch_breakers
        )

        # 필수 품목 확인
        item_names = [a.item_name for a in accessories]
        assert "E.T" in item_names
        assert "N.T" in item_names
        assert "N.P" in item_names  # 2개 (CARD HOLDER + 3T*40*200)
        assert "COATING" in item_names
        assert "P-COVER" in item_names
        assert "INSULATOR" in item_names

        # 총 품목 수: E.T(1) + N.T(1) + N.P(2) + COATING(1) + P-COVER(1) + INSULATOR(1) = 7
        # 차단기지지대(0, 100AF), ELB지지대(0, 일반차단기)
        assert len(accessories) == 7
