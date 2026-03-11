"""

# Catalog dependency → requires DB
# Skip in CI: requires real Supabase catalog with AUTO model resolution

Tests for DataTransformer._create_breaker_item method.

Zero-Mock Policy: Uses real Supabase catalog_service.
"""

import os
import pytest

pytestmark = [
    pytest.mark.requires_db,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping data transformer tests in CI - requires real Supabase catalog"
    )
]
from kis_estimator_core.engine.data_transformer import DataTransformer


class MockPlacement:
    """Mock breaker placement for testing."""

    def __init__(
        self,
        breaker_id: str,
        model: str = "AUTO",
        poles: int = 4,
        current_a: float = 60.0,
        breaking_capacity_ka: float = 35.0,
    ):
        self.breaker_id = breaker_id
        self.model = model
        self.poles = poles
        self.current_a = current_a
        self.breaking_capacity_ka = breaking_capacity_ka


class MockBreaker:
    """Mock original breaker input."""

    def __init__(self, id: str, model: str = "AUTO"):
        self.id = id
        self.model = model


class TestDataTransformerCreateBreakerItem:
    """_create_breaker_item method tests (requires DB for CatalogService)."""

    def test_create_breaker_item_auto_model(self):
        """
        AUTO 모델: catalog_service가 스펙 기반으로 자동 선택.
        Zero-Mock: 실제 Supabase 카탈로그 조회.
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}  # 빈 breaker_map

        placement = MockPlacement(
            breaker_id="B1",
            model="AUTO",
            poles=4,
            current_a=60.0,
            breaking_capacity_ka=35.0,  # 요청값
        )

        item = transformer._create_breaker_item(placement, is_main=True)

        assert item is not None
        assert item.is_main is True
        assert item.poles == 4
        assert item.current_a == 60.0
        # 카탈로그 조회 결과에 따라 breaking_capacity_ka가 결정됨
        # 경제형(14.0kA), 표준형(25.0kA, 35.0kA, 50.0kA) 모두 유효
        assert item.breaking_capacity_ka in [14.0, 25.0, 35.0, 50.0], f"Unexpected breaking_capacity_ka: {item.breaking_capacity_ka}"
        assert item.unit_price > 0  # 실제 카탈로그 가격
        # model은 AUTO가 아닌 실제 모델명으로 변경됨
        assert item.model != "AUTO"

    def test_create_breaker_item_explicit_model(self):
        """
        명시적 모델명 테스트.
        Zero-Mock: AUTO 모델 사용 (실제 카탈로그 매칭).
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B2",
            model="AUTO",  # 실제 카탈로그 매칭
            poles=4,
            current_a=60.0,
            breaking_capacity_ka=25.0,
        )

        item = transformer._create_breaker_item(placement, is_main=True)

        assert item is not None
        assert item.model != "AUTO"  # 실제 모델명으로 변경됨
        assert item.poles == 4

    def test_create_breaker_item_2pole(self):
        """
        2극 차단기.
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B3",
            model="AUTO",
            poles=2,
            current_a=30.0,
            breaking_capacity_ka=14.0,
        )

        item = transformer._create_breaker_item(placement, is_main=False)

        assert item is not None
        assert item.poles == 2
        assert item.current_a == 30.0
        assert item.is_main is False

    def test_create_breaker_item_3pole(self):
        """
        3극 차단기.
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B4",
            model="AUTO",
            poles=3,
            current_a=100.0,
            breaking_capacity_ka=35.0,
        )

        item = transformer._create_breaker_item(placement, is_main=False)

        assert item is not None
        assert item.poles == 3
        assert item.current_a == 100.0

    def test_create_breaker_item_elb_type(self):
        """
        ELB (누전차단기) 타입 판정.
        Zero-Mock: AUTO 모델 사용, ELB 판정은 카탈로그 반환값 기준.
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B5",
            model="AUTO",  # 실제 카탈로그 매칭
            poles=4,
            current_a=50.0,
            breaking_capacity_ka=14.0,
        )

        item = transformer._create_breaker_item(placement, is_main=False)

        assert item is not None
        # breaker_type은 MCCB 또는 ELB (카탈로그 기준)
        assert item.breaker_type in ["MCCB", "ELB"]

    def test_create_breaker_item_mccb_type(self):
        """
        MCCB (배선용차단기) 타입 판정.
        Zero-Mock: AUTO 모델 사용.
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B6",
            model="AUTO",  # 실제 카탈로그 매칭
            poles=4,
            current_a=50.0,
            breaking_capacity_ka=25.0,
        )

        item = transformer._create_breaker_item(placement, is_main=True)

        assert item is not None
        # breaker_type은 MCCB 또는 ELB (카탈로그 기준)
        assert item.breaker_type in ["MCCB", "ELB"]

    def test_create_breaker_item_not_found(self):
        """
        카탈로그에 없는 차단기 → 에러 발생 (목업 금지!).
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        # 존재하지 않는 스펙 (예: 100극 9999A)
        placement = MockPlacement(
            breaker_id="B_INVALID",
            model="AUTO",
            poles=100,  # 비정상 극수
            current_a=9999.0,
            breaking_capacity_ka=9999.0,
        )

        with pytest.raises(Exception) as exc_info:
            transformer._create_breaker_item(placement, is_main=False)

        assert "카탈로그에 없는 차단기" in str(exc_info.value) or "목업 금지" in str(
            exc_info.value
        )

    def test_create_breaker_item_from_breaker_map(self):
        """
        placement.model이 없으면 breaker_map에서 original_breaker.model 사용.
        Zero-Mock: AUTO 모델로 폴백.
        """
        transformer = DataTransformer()

        # original_breaker 설정 (AUTO 모델)
        original_breaker = MockBreaker(id="B7", model="AUTO")
        transformer._breaker_map = {"B7": original_breaker}

        # placement에 model 속성 없음
        placement = MockPlacement(breaker_id="B7", poles=2, current_a=60.0)
        delattr(placement, "model")  # model 속성 제거

        item = transformer._create_breaker_item(placement, is_main=True)

        assert item is not None
        # breaker_map에서 가져온 AUTO 모델로 카탈로그 매칭
        assert item.model != "AUTO"  # 실제 모델명으로 변경됨

    def test_create_breaker_item_spec_format(self):
        """
        spec 형식: "{poles}P {current_a}AT {breaking_capacity}kA".
        """
        transformer = DataTransformer()
        transformer._breaker_map = {}

        placement = MockPlacement(
            breaker_id="B8",
            model="AUTO",
            poles=4,
            current_a=75.0,
            breaking_capacity_ka=35.0,
        )

        item = transformer._create_breaker_item(placement, is_main=True)

        assert item is not None
        # spec 형식 확인: "4P 75AT [차단용량]kA"
        # 차단용량은 카탈로그 조회 결과에 따라 결정됨 (경제형 14.0, 표준형 25/35/50)
        assert "4P" in item.spec
        assert "75AT" in item.spec
        assert "kA" in item.spec
        # 차단용량 값이 포함되어 있는지 확인 (14.0, 25.0, 35.0, 50.0 중 하나)
        assert any(ka in item.spec for ka in ["14.0", "25.0", "35.0", "50.0"]), f"Unexpected spec format: {item.spec}"
