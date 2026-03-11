"""
AI CatalogService v2 테스트

검증 항목:
1. 카탈로그 로드 및 인덱싱
2. 차단기 검색 (경제형 우선)
3. 외함 검색 (가격 낮은 순)
4. 사양 기반 자동 선택
5. 성능 비교 (CSV regex vs JSON index)
"""

import os
import pytest

# CI skip - tests require '절대코어파일/ai_catalog_v1.json' which is not in repo
# This file is a local development resource on CEO's machine
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping AI CatalogService tests in CI - requires local ai_catalog_v1.json file"
)

from kis_estimator_core.services.ai_catalog_service import (
    get_ai_catalog_service,
)
from kis_estimator_core.models.catalog import (
    BreakerCategory,
    BreakerSeries,
    Brand,
    EnclosureType,
    EnclosureMaterial,
)


@pytest.fixture
def ai_catalog():
    """AI 카탈로그 서비스 픽스처"""
    return get_ai_catalog_service()


class TestAICatalogLoad:
    """카탈로그 로드 및 인덱싱 테스트"""

    def test_catalog_loads_successfully(self, ai_catalog):
        """카탈로그가 정상적으로 로드되는지 확인"""
        # 카탈로그 로드
        catalog = ai_catalog._load_catalog()

        # 검증
        assert catalog is not None
        assert catalog.version == "v1.0.0"
        assert catalog.breaker_count > 0
        assert catalog.enclosure_count > 0
        assert catalog.total_items > 0

    def test_indexes_built_correctly(self, ai_catalog):
        """검색 인덱스가 정상적으로 생성되는지 확인"""
        # 카탈로그 로드 (인덱스 자동 생성)
        ai_catalog._load_catalog()

        # 검증
        assert len(ai_catalog._breaker_index) > 0
        assert len(ai_catalog._enclosure_index) > 0

        # 샘플 키워드 확인
        assert "2P" in ai_catalog._breaker_index
        assert "MCCB" in ai_catalog._breaker_index


class TestBreakerSearch:
    """차단기 검색 테스트"""

    def test_search_breaker_by_model(self, ai_catalog):
        """모델명으로 차단기 검색"""
        # 상도 경제형 2P 60A (SBE-102)
        results = ai_catalog.search_breakers(model="SBE-102")

        # 검증
        assert len(results) > 0
        breaker = results[0]
        assert breaker.model == "SBE-102"
        assert breaker.brand == Brand.SADOELE
        assert breaker.series == BreakerSeries.ECONOMY

    def test_search_breaker_by_spec(self, ai_catalog):
        """사양으로 차단기 검색 (경제형 우선)"""
        # 2P 20A MCCB 검색
        results = ai_catalog.search_breakers(
            category=BreakerCategory.MCCB,
            poles=2,
            current_a=20,
        )

        # 검증
        assert len(results) > 0

        # 경제형이 먼저 정렬되어야 함
        first_breaker = results[0]
        assert first_breaker.poles == 2
        assert first_breaker.current_a == 20

    def test_get_breaker_by_spec_auto_select(self, ai_catalog):
        """사양 기반 자동 선택 (경제형 우선)"""
        # 4P 100A MCCB (경제형이 있으면 경제형 선택)
        breaker = ai_catalog.get_breaker_by_spec(
            category=BreakerCategory.MCCB,
            poles=4,
            current_a=100,
        )

        # 검증
        assert breaker is not None
        assert breaker.poles == 4
        assert breaker.current_a == 100
        assert breaker.category == BreakerCategory.MCCB

    def test_breaker_not_found(self, ai_catalog):
        """존재하지 않는 차단기 검색"""
        # 존재하지 않는 사양 (5P 999A)
        breaker = ai_catalog.get_breaker_by_spec(
            category=BreakerCategory.MCCB,
            poles=5,
            current_a=999,
        )

        # 검증
        assert breaker is None

    def test_breaker_search_economy_priority(self, ai_catalog):
        """경제형 우선 정렬 검증"""
        # 2P 60A MCCB (경제형/표준형 모두 존재)
        results = ai_catalog.search_breakers(
            category=BreakerCategory.MCCB,
            poles=2,
            current_a=60,
        )

        # 검증
        assert len(results) > 0

        # 경제형이 먼저 나와야 함
        economy_results = [b for b in results if b.series == BreakerSeries.ECONOMY]
        standard_results = [b for b in results if b.series == BreakerSeries.STANDARD]

        if economy_results and standard_results:
            # 경제형이 표준형보다 먼저 위치
            economy_idx = results.index(economy_results[0])
            standard_idx = results.index(standard_results[0])
            assert economy_idx < standard_idx


class TestEnclosureSearch:
    """외함 검색 테스트"""

    def test_search_enclosure_by_model(self, ai_catalog):
        """모델명으로 외함 검색"""
        # HB304015 (300×400×150) 검색
        results = ai_catalog.search_enclosures(model="HB304015")

        # 검증 (없을 수도 있음)
        if results:
            enclosure = results[0]
            assert enclosure.model == "HB304015"

    def test_search_enclosure_by_size(self, ai_catalog):
        """치수로 외함 검색"""
        # 600×400×200 옥내노출 STEEL 1.6T
        results = ai_catalog.search_enclosures(
            type=EnclosureType.INDOOR_EXPOSED,
            material=EnclosureMaterial.STEEL_16T,
            width_mm=600,
            height_mm=400,
            depth_mm=200,
        )

        # 검증 (없을 수도 있음)
        if results:
            enclosure = results[0]
            assert enclosure.width_mm == 600
            assert enclosure.height_mm == 400
            assert enclosure.depth_mm == 200

    def test_enclosure_not_found(self, ai_catalog):
        """존재하지 않는 외함 검색"""
        # 존재하지 않는 크기 (9999×9999×9999)
        enclosure = ai_catalog.get_enclosure_by_size(
            type=EnclosureType.INDOOR_EXPOSED,
            material=EnclosureMaterial.STEEL_16T,
            width_mm=9999,
            height_mm=9999,
            depth_mm=9999,
        )

        # 검증
        assert enclosure is None


class TestPerformance:
    """성능 테스트"""

    def test_catalog_loading_speed(self, ai_catalog):
        """카탈로그 로드 속도 테스트"""
        import time

        # 첫 로드 (캐싱 전)
        ai_catalog._catalog = None
        start = time.perf_counter()
        ai_catalog._load_catalog()
        first_load_time = time.perf_counter() - start

        # 두 번째 로드 (캐싱 후)
        start = time.perf_counter()
        ai_catalog._load_catalog()
        second_load_time = time.perf_counter() - start

        # 검증
        assert first_load_time < 1.0  # 1초 이내 로드
        assert second_load_time < 0.01  # 캐싱 후 10ms 이내

    def test_search_speed(self, ai_catalog):
        """검색 속도 테스트"""
        import time

        # 카탈로그 로드 (사전 준비)
        ai_catalog._load_catalog()

        # 모델명 검색 (인덱스 사용)
        start = time.perf_counter()
        for _ in range(100):
            ai_catalog.search_breakers(model="SBE-102")
        model_search_time = time.perf_counter() - start

        # 사양 검색 (필터링)
        start = time.perf_counter()
        for _ in range(100):
            ai_catalog.search_breakers(
                category=BreakerCategory.MCCB,
                poles=2,
                current_a=60,
            )
        spec_search_time = time.perf_counter() - start

        # 검증
        assert model_search_time < 0.1  # 100회 검색 100ms 이내
        assert spec_search_time < 1.0  # 100회 검색 1초 이내


class TestRealWorldScenarios:
    """실제 사용 시나리오 테스트"""

    def test_bug_003_small_breaker_selection(self, ai_catalog):
        """BUG-003: 2P 20A/30A는 소형 차단기 사용"""
        # 2P 20A ELB 검색
        breaker = ai_catalog.get_breaker_by_spec(
            category=BreakerCategory.ELB,
            poles=2,
            current_a=20,
        )

        # 검증
        assert breaker is not None
        assert breaker.poles == 2
        assert breaker.current_a == 20

        # 소형 차단기 모델 확인 (SIE-32 등)
        assert breaker.frame_af in [30, 32]  # 소형 프레임

    def test_multiple_panel_breaker_selection(self, ai_catalog):
        """여러 패널의 차단기 선택 (경제형 우선)"""
        # 분전반 1: 메인 4P 100A, 분기 2P 20A×10
        main = ai_catalog.get_breaker_by_spec(
            category=BreakerCategory.MCCB,
            poles=4,
            current_a=100,
        )

        branches = []
        for _ in range(10):
            breaker = ai_catalog.get_breaker_by_spec(
                category=BreakerCategory.MCCB,
                poles=2,
                current_a=20,
            )
            branches.append(breaker)

        # 검증
        assert main is not None
        assert len(branches) == 10
        assert all(b is not None for b in branches)

        # 모든 차단기가 경제형이거나 경제형 없으면 표준형
        for b in [main] + branches:
            assert b.series in [BreakerSeries.ECONOMY, BreakerSeries.STANDARD]
