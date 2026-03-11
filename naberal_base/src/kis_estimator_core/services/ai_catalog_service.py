"""
AI CatalogService v2 - AI 최적화 카탈로그 검색 서비스

원본(CSV): 622 lines, 느린 regex 검색
v2(JSON): 544 items, 빠른 인덱스 검색, 타입 안전

주요 개선점:
- 10-100배 빠른 검색 (인덱싱)
- Pydantic 타입 검증 (런타임 안전)
- 자동 경제형 우선 정렬
- 메모리 캐싱
"""

import json
import logging
from pathlib import Path

from ..models.catalog import (
    AICatalog,
    Brand,
    BreakerCategory,
    BreakerSeries,
    CatalogBreakerItem,
    CatalogEnclosureItem,
    EnclosureMaterial,
    EnclosureType,
)

logger = logging.getLogger(__name__)


class AICatalogService:
    """
    AI 최적화 카탈로그 서비스

    기능:
    - 빠른 검색 (search_keywords 인덱싱)
    - 타입 안전 (Pydantic 검증)
    - 캐싱 (메모리 효율)
    - 다중 검색 조건 (AND/OR)
    """

    def __init__(self, catalog_path: Path | None = None):
        """
        Args:
            catalog_path: AI 카탈로그 JSON 파일 경로
        """
        # 상대 경로 사용 (Railway 호환)
        project_root = Path(__file__).parent.parent.parent.parent
        self.catalog_path = catalog_path or (
            project_root / "절대코어파일" / "ai_catalog_v1.json"
        )

        self._catalog: AICatalog | None = None
        self._breaker_index: dict[str, list[CatalogBreakerItem]] = {}
        self._enclosure_index: dict[str, list[CatalogEnclosureItem]] = {}

        logger.info(f"AICatalogService initialized with: {self.catalog_path}")

    def _load_catalog(self) -> AICatalog:
        """카탈로그 로드 (캐싱)"""
        if self._catalog is not None:
            return self._catalog

        logger.info(f"Loading AI catalog from {self.catalog_path}")

        with open(self.catalog_path, encoding="utf-8") as f:
            catalog_data = json.load(f)

        # Pydantic 검증 + 파싱
        self._catalog = AICatalog(**catalog_data)

        # 검색 인덱스 생성
        self._build_indexes()

        logger.info(
            f"Catalog loaded: {self._catalog.breaker_count} breakers, {self._catalog.enclosure_count} enclosures"
        )

        return self._catalog

    def _build_indexes(self):
        """검색 인덱스 생성 (search_keywords 기반)"""
        if not self._catalog:
            return

        # 차단기 인덱스
        for breaker in self._catalog.breakers:
            for keyword in breaker.search_keywords:
                if keyword not in self._breaker_index:
                    self._breaker_index[keyword] = []
                self._breaker_index[keyword].append(breaker)

        # 외함 인덱스
        for enclosure in self._catalog.enclosures:
            for keyword in enclosure.search_keywords:
                if keyword not in self._enclosure_index:
                    self._enclosure_index[keyword] = []
                self._enclosure_index[keyword].append(enclosure)

        logger.info(
            f"Indexes built: {len(self._breaker_index)} breaker keywords, {len(self._enclosure_index)} enclosure keywords"
        )

    def search_breakers(
        self,
        category: BreakerCategory | None = None,
        brand: Brand | None = None,
        series: BreakerSeries | None = None,
        poles: int | None = None,
        current_a: int | None = None,
        frame_af: int | None = None,
        model: str | None = None,
    ) -> list[CatalogBreakerItem]:
        """
        차단기 검색 (빠른 인덱스 검색)

        Args:
            category: MCCB or ELB
            brand: 제조사
            series: 경제형 or 표준형
            poles: 극수 (2, 3, 4)
            current_a: 정격전류
            frame_af: 프레임 크기
            model: 모델명 (정확히 일치)

        Returns:
            검색 조건에 맞는 차단기 목록 (정렬됨: 경제형 우선 → 가격 낮은 순)
        """
        catalog = self._load_catalog()

        results = []

        # 인덱스 검색 (빠름)
        if model:
            # 모델명 정확 검색
            keyword = model.upper()
            results = self._breaker_index.get(keyword, [])
        else:
            # 전체 스캔 (조건 필터링)
            results = catalog.breakers

        # 필터링
        if category:
            results = [b for b in results if b.category == category]
        if brand:
            results = [b for b in results if b.brand == brand]
        if series:
            results = [b for b in results if b.series == series]
        if poles:
            results = [b for b in results if b.poles == poles]
        if current_a:
            results = [b for b in results if b.current_a == current_a]
        if frame_af:
            results = [b for b in results if b.frame_af == frame_af]

        # 정렬: 경제형 우선 → 가격 낮은 순
        results.sort(
            key=lambda b: (0 if b.series == BreakerSeries.ECONOMY else 1, b.price)
        )

        logger.debug(f"Breaker search: {len(results)} results")
        return results

    def search_enclosures(
        self,
        type: EnclosureType | None = None,
        material: EnclosureMaterial | None = None,
        brand: Brand | None = None,
        width_mm: int | None = None,
        height_mm: int | None = None,
        depth_mm: int | None = None,
        model: str | None = None,
    ) -> list[CatalogEnclosureItem]:
        """
        외함 검색 (빠른 인덱스 검색)

        Args:
            type: 외함 종류 (옥내노출, 옥외노출 등)
            material: 재질 (STEEL 1.6T, SUS201 1.2T 등)
            brand: 제조사
            width_mm, height_mm, depth_mm: 치수 (정확히 일치)
            model: 모델명 (정확히 일치)

        Returns:
            검색 조건에 맞는 외함 목록 (정렬됨: 가격 낮은 순)
        """
        catalog = self._load_catalog()

        results = []

        # 인덱스 검색
        if model:
            keyword = model.upper()
            results = self._enclosure_index.get(keyword, [])
        else:
            results = catalog.enclosures

        # 필터링
        if type:
            results = [e for e in results if e.type == type]
        if material:
            results = [e for e in results if e.material == material]
        if brand:
            results = [e for e in results if e.brand == brand]
        if width_mm:
            results = [e for e in results if e.width_mm == width_mm]
        if height_mm:
            results = [e for e in results if e.height_mm == height_mm]
        if depth_mm:
            results = [e for e in results if e.depth_mm == depth_mm]

        # 정렬: 가격 낮은 순
        results.sort(key=lambda e: e.price)

        logger.debug(f"Enclosure search: {len(results)} results")
        return results

    def get_breaker_by_spec(
        self,
        category: BreakerCategory,
        poles: int,
        current_a: int,
        brand: Brand | None = None,
        prefer_economy: bool = True,
    ) -> CatalogBreakerItem | None:
        """
        사양으로 차단기 검색 (단일 결과)

        Args:
            category: MCCB or ELB
            poles: 극수
            current_a: 정격전류
            brand: 제조사 (Optional)
            prefer_economy: 경제형 우선 (기본 True)

        Returns:
            최적 차단기 (경제형 우선 → 가격 낮은 순)
        """
        catalog = self._load_catalog()

        # 2P 소형 차단기 규칙 (15A, 20A, 30A는 30/32AF 소형 사용)
        if poles == 2 and current_a in [15, 20, 30]:
            logger.info(f"2P {current_a}A 소형 차단기 검색: {category.value}")
            small_results = []
            for breaker in catalog.breakers:
                if (
                    breaker.category == category
                    and breaker.poles == 2
                    and breaker.current_a == current_a
                    and breaker.frame_af in [30, 32]  # 소형 프레임
                ):
                    if brand is None or breaker.brand == brand:
                        small_results.append(breaker)

            if small_results:
                # 경제형 우선, 가격 낮은 순
                small_results.sort(
                    key=lambda b: (0 if b.series == BreakerSeries.ECONOMY else 1, b.price)
                )
                logger.info(f"소형 차단기 찾음: {small_results[0].model}")
                return small_results[0]

            # 소형 없으면 50AF 컴팩트 검색
            logger.info(f"소형 없음, 50AF 컴팩트 검색: {category.value} 2P {current_a}A")
            compact_results = self.search_breakers(
                category=category,
                brand=brand,
                poles=poles,
                current_a=current_a,
                frame_af=50,
            )
            if compact_results:
                logger.info(f"컴팩트 차단기 찾음: {compact_results[0].model}")
                return compact_results[0]

        # 일반 검색
        results = self.search_breakers(
            category=category,
            brand=brand,
            poles=poles,
            current_a=current_a,
        )

        if not results:
            logger.warning(f"No breaker found: {category.value} {poles}P {current_a}A")
            return None

        # 경제형 우선 이미 정렬됨
        return results[0]

    def get_breaker_by_full_spec(
        self,
        brand: Brand,
        series: BreakerSeries,
        category: BreakerCategory,
        poles: int,
        current_a: int,
    ) -> CatalogBreakerItem | None:
        """
        완전한 사양으로 차단기 검색 (견적 UI용)

        브랜드 → 등급(경제형/표준형) → 종류(MCCB/ELB) → 극수 → 용량
        → 카탈로그에서 정확히 일치하는 모델명 + 단가 반환

        특수 규칙:
        - 4P 50AF (20~50A): 경제형 없으므로 표준형으로 자동 대체
        - 2P 20A/30A 소형: 소형 모델 사용 (SIB-32, SIE-32, BS-32, 32GRHS)

        Args:
            brand: 제조사 (SANGDO, LS)
            series: 등급 (ECONOMY, STANDARD)
            category: 종류 (MCCB, ELB)
            poles: 극수 (2, 3, 4)
            current_a: 정격전류 (A)

        Returns:
            정확히 일치하는 차단기 (없으면 None)
            자동 대체 시 대체된 차단기 반환 (logs에 기록)
        """
        catalog = self._load_catalog()

        # 1. 정확한 조건으로 검색
        results = self.search_breakers(
            category=category,
            brand=brand,
            series=series,
            poles=poles,
            current_a=current_a,
        )

        if results:
            logger.info(
                f"Breaker found: {brand.value} {series.value} {category.value} "
                f"{poles}P {current_a}A → {results[0].model}"
            )
            return results[0]

        # 2. 4P 50AF 경제형 → 표준형 자동 대체
        if poles == 4 and series == BreakerSeries.ECONOMY:
            # 50AF 범위 (20~50A)
            if current_a <= 50:
                logger.info(
                    f"4P 50AF 경제형 없음 → 표준형 자동 대체 시도: "
                    f"{brand.value} {category.value} 4P {current_a}A"
                )
                fallback_results = self.search_breakers(
                    category=category,
                    brand=brand,
                    series=BreakerSeries.STANDARD,  # 표준형으로 대체
                    poles=poles,
                    current_a=current_a,
                )
                if fallback_results:
                    logger.info(
                        f"4P 50AF 표준형 대체 성공: {fallback_results[0].model}"
                    )
                    return fallback_results[0]

        # 3. 2P 20A/30A 소형 규칙 적용
        if poles == 2 and current_a in [20, 30]:
            # 소형 모델 검색 (frame_af=30 또는 32)
            logger.info(
                f"2P {current_a}A 소형 모델 검색: {brand.value} {category.value}"
            )
            small_results = []
            for breaker in catalog.breakers:
                if (
                    breaker.category == category
                    and breaker.brand == brand
                    and breaker.poles == 2
                    and breaker.current_a == current_a
                    and breaker.frame_af in [30, 32]  # 소형 프레임
                ):
                    small_results.append(breaker)

            if small_results:
                # 가격 낮은 순 정렬
                small_results.sort(key=lambda b: b.price)
                logger.info(f"소형 모델 찾음: {small_results[0].model}")
                return small_results[0]

        # 4. 경제형 실패 시 표준형 자동 대체 (일반)
        if series == BreakerSeries.ECONOMY:
            logger.info(
                f"경제형 없음 → 표준형 자동 대체 시도: "
                f"{brand.value} {category.value} {poles}P {current_a}A"
            )
            fallback_results = self.search_breakers(
                category=category,
                brand=brand,
                series=BreakerSeries.STANDARD,
                poles=poles,
                current_a=current_a,
            )
            if fallback_results:
                logger.info(
                    f"표준형 대체 성공: {fallback_results[0].model}"
                )
                return fallback_results[0]

        logger.warning(
            f"차단기를 찾을 수 없습니다: {brand.value} {series.value} "
            f"{category.value} {poles}P {current_a}A"
        )
        return None

    def get_breaker_model_and_price(
        self,
        brand: str,
        series: str,
        category: str,
        poles: int,
        current_a: int,
    ) -> dict | None:
        """
        문자열 입력으로 차단기 모델명 + 단가 조회 (프론트엔드 API용)

        Args:
            brand: "상도" 또는 "LS"
            series: "경제형" 또는 "표준형"
            category: "MCCB" 또는 "ELB"
            poles: 극수 (2, 3, 4)
            current_a: 정격전류 (A)

        Returns:
            {
                "model": "SBS-54",
                "price": 15800,
                "frame_af": 50,
                "breaking_capacity_ka": 50.0,
                "auto_substituted": False,
                "substitution_reason": None
            }
        """
        # 문자열 → Enum 변환 (SSOT enums.py 참조)
        brand_map = {
            "상도": Brand.SADOELE,
            "상도차단기": Brand.SADOELE,
            "SADOELE": Brand.SADOELE,
            "LS": Brand.LSIS,
            "ls": Brand.LSIS,
            "LS산전": Brand.LSIS,
            "LSIS": Brand.LSIS,
            "현대": Brand.HDELECTRIC,
            "현대일렉트릭": Brand.HDELECTRIC,
            "한국산업": Brand.KISCO,
            "KISCO": Brand.KISCO,
        }
        series_map = {
            "경제형": BreakerSeries.ECONOMY,
            "economy": BreakerSeries.ECONOMY,
            "ECONOMY": BreakerSeries.ECONOMY,
            "표준형": BreakerSeries.STANDARD,
            "standard": BreakerSeries.STANDARD,
            "STANDARD": BreakerSeries.STANDARD,
        }
        category_map = {
            "MCCB": BreakerCategory.MCCB,
            "mccb": BreakerCategory.MCCB,
            "배선용": BreakerCategory.MCCB,
            "배선용차단기": BreakerCategory.MCCB,
            "ELB": BreakerCategory.ELB,
            "elb": BreakerCategory.ELB,
            "누전": BreakerCategory.ELB,
            "누전차단기": BreakerCategory.ELB,
        }

        brand_enum = brand_map.get(brand)
        series_enum = series_map.get(series)
        category_enum = category_map.get(category)

        if not all([brand_enum, series_enum, category_enum]):
            logger.error(
                f"Invalid input: brand={brand}, series={series}, category={category}"
            )
            return None

        # 원본 시리즈 저장 (대체 여부 확인용)
        original_series = series_enum

        breaker = self.get_breaker_by_full_spec(
            brand=brand_enum,
            series=series_enum,
            category=category_enum,
            poles=poles,
            current_a=current_a,
        )

        if not breaker:
            return None

        # 자동 대체 여부 확인
        auto_substituted = breaker.series != original_series
        substitution_reason = None
        if auto_substituted:
            if poles == 4 and current_a <= 50:
                substitution_reason = "4P 50AF 경제형 미존재 → 표준형 자동 대체"
            else:
                substitution_reason = "경제형 미존재 → 표준형 자동 대체"

        return {
            "model": breaker.model,
            "price": breaker.price,
            "frame_af": breaker.frame_af,
            "breaking_capacity_ka": breaker.breaking_capacity_ka,
            "poles": breaker.poles,
            "current_a": breaker.current_a,
            "brand": breaker.brand.value,
            "series": breaker.series.value,
            "category": breaker.category.value,
            "dimensions": {
                "width_mm": breaker.dimensions.width_mm,
                "height_mm": breaker.dimensions.height_mm,
                "depth_mm": breaker.dimensions.depth_mm,
            },
            "auto_substituted": auto_substituted,
            "substitution_reason": substitution_reason,
        }

    def get_enclosure_by_size(
        self,
        type: EnclosureType,
        material: EnclosureMaterial,
        width_mm: int,
        height_mm: int,
        depth_mm: int,
    ) -> CatalogEnclosureItem | None:
        """
        치수로 외함 검색 (정확 일치)

        Args:
            type: 외함 종류
            material: 재질
            width_mm, height_mm, depth_mm: 치수

        Returns:
            일치하는 외함 (없으면 None)
        """
        results = self.search_enclosures(
            type=type,
            material=material,
            width_mm=width_mm,
            height_mm=height_mm,
            depth_mm=depth_mm,
        )

        if not results:
            logger.warning(
                f"No enclosure found: {type.value} {material.value} {width_mm}×{height_mm}×{depth_mm}"
            )
            return None

        return results[0]

    def get_enclosure_with_classification(
        self,
        enclosure_type: str,
        material: str,
        width_mm: int,
        height_mm: int,
        depth_mm: int,
        remarks: str | None = None,
    ) -> dict:
        """
        외함 검색 + 기성함/주문제작함 분류 (프론트엔드 API용)

        카탈로그에 정확히 일치하는 외함이 있으면 → 기성함
        없으면 → 주문제작함으로 분류

        Args:
            enclosure_type: "옥내노출", "옥외노출", "옥내자립", "옥외자립" 등
            material: "STEEL 1.6T", "SUS201 1.2T" 등
            width_mm: 폭 (mm)
            height_mm: 높이 (mm)
            depth_mm: 깊이 (mm)
            remarks: 특이사항 ("양문형", "단문형" 등)

        Returns:
            {
                "classification": "기성함" 또는 "주문제작함",
                "is_custom": False 또는 True,
                "model": "HDS-600x800x200" 또는 None,
                "price": 120000 또는 None (주문제작 시 별도 산정),
                "enclosure_type": "옥내노출",
                "material": "STEEL 1.6T",
                "width_mm": 600,
                "height_mm": 800,
                "depth_mm": 200,
                "remarks": "양문형" 또는 None,
                "nearest_standard": {...}  # 가까운 기성함 정보 (주문제작 시)
            }
        """
        # 문자열 → Enum 변환 (엄격한 매핑 - 옥내/옥외 혼동 방지)
        # 옥내(indoor) 계열
        indoor_types = {
            "옥내노출": EnclosureType.INDOOR_EXPOSED,
            "옥내": EnclosureType.INDOOR_EXPOSED,
            "indoor": EnclosureType.INDOOR_EXPOSED,
            "INDOOR": EnclosureType.INDOOR_EXPOSED,
            "indoor_exposed": EnclosureType.INDOOR_EXPOSED,
            "옥내자립": EnclosureType.INDOOR_STANDALONE,
            "indoor_standalone": EnclosureType.INDOOR_STANDALONE,
        }
        # 옥외(outdoor) 계열
        outdoor_types = {
            "옥외노출": EnclosureType.OUTDOOR_EXPOSED,
            "옥외": EnclosureType.OUTDOOR_EXPOSED,
            "outdoor": EnclosureType.OUTDOOR_EXPOSED,
            "OUTDOOR": EnclosureType.OUTDOOR_EXPOSED,
            "outdoor_exposed": EnclosureType.OUTDOOR_EXPOSED,
            "옥외자립": EnclosureType.OUTDOOR_STANDALONE,
            "outdoor_standalone": EnclosureType.OUTDOOR_STANDALONE,
        }
        # 기타 특수 유형 (주의: SSOT enums에 POLE_MOUNT 없음)
        special_types = {
            "매입함": EnclosureType.EMBEDDED,
            "매입": EnclosureType.EMBEDDED,
            "embedded": EnclosureType.EMBEDDED,
            # 전주부착형은 현재 Enum에 없음 - 옥외노출로 처리
            "전주부착": EnclosureType.OUTDOOR_EXPOSED,
            "전주부착형": EnclosureType.OUTDOOR_EXPOSED,
            # 하이박스 - 옥외노출로 처리 (방수함)
            "하이박스": EnclosureType.OUTDOOR_EXPOSED,
            "HIBOX": EnclosureType.OUTDOOR_EXPOSED,
            "hibox": EnclosureType.OUTDOOR_EXPOSED,
            # FRP함 - 옥외노출로 처리
            "FRP함": EnclosureType.OUTDOOR_EXPOSED,
            "FRP": EnclosureType.OUTDOOR_EXPOSED,
            "frp": EnclosureType.OUTDOOR_EXPOSED,
            # 속판제작 - 옥내노출로 처리
            "속판제작": EnclosureType.INDOOR_EXPOSED,
            "속판": EnclosureType.INDOOR_EXPOSED,
        }
        # 전체 매핑 (우선순위: 정확한 매핑만)
        type_map = {**indoor_types, **outdoor_types, **special_types}

        # SSOT enums: STEEL_16T, STEEL_10T, SUS201_12T
        material_map = {
            "STEEL 1.6T": EnclosureMaterial.STEEL_16T,
            "스틸 1.6T": EnclosureMaterial.STEEL_16T,
            "스틸1.6T": EnclosureMaterial.STEEL_16T,
            "steel 1.6t": EnclosureMaterial.STEEL_16T,
            "steel": EnclosureMaterial.STEEL_16T,
            "STEEL": EnclosureMaterial.STEEL_16T,
            "스틸": EnclosureMaterial.STEEL_16T,
            "STEEL 1.0T": EnclosureMaterial.STEEL_10T,
            "스틸 1.0T": EnclosureMaterial.STEEL_10T,
            "steel 1.0t": EnclosureMaterial.STEEL_10T,
            "SUS201 1.2T": EnclosureMaterial.SUS201_12T,
            "SUS201": EnclosureMaterial.SUS201_12T,
            "sus201": EnclosureMaterial.SUS201_12T,
            "스테인레스": EnclosureMaterial.SUS201_12T,
            "SUS": EnclosureMaterial.SUS201_12T,
            "sus": EnclosureMaterial.SUS201_12T,
        }

        type_enum = type_map.get(enclosure_type)
        material_enum = material_map.get(material)

        # 엄격한 검증: 알 수 없는 입력은 주문제작함으로 분류 (기본값 사용 안 함)
        if not type_enum:
            logger.error(
                f"[STRICT] Unknown enclosure type: '{enclosure_type}' - "
                f"Valid indoor: {list(indoor_types.keys())}, "
                f"Valid outdoor: {list(outdoor_types.keys())}"
            )
            # 기본값 사용 안 함 - 주문제작함으로 분류
            return {
                "classification": "주문제작함",
                "is_custom": True,
                "model": None,
                "price": None,
                "enclosure_type": enclosure_type,  # 원본 입력값 유지
                "material": material,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "depth_mm": depth_mm,
                "remarks": remarks,
                "nearest_standard": None,
                "error": f"알 수 없는 외함 종류: {enclosure_type}",
            }

        if not material_enum:
            logger.error(
                f"[STRICT] Unknown material: '{material}' - "
                f"Valid materials: {list(material_map.keys())}"
            )
            # 기본값 사용 안 함 - 주문제작함으로 분류
            return {
                "classification": "주문제작함",
                "is_custom": True,
                "model": None,
                "price": None,
                "enclosure_type": type_enum.value if type_enum else enclosure_type,
                "material": material,  # 원본 입력값 유지
                "width_mm": width_mm,
                "height_mm": height_mm,
                "depth_mm": depth_mm,
                "remarks": remarks,
                "nearest_standard": None,
                "error": f"알 수 없는 재질: {material}",
            }

        self._load_catalog()

        # 1. 정확한 매칭 시도 (기성함)
        exact_match = self.get_enclosure_by_size(
            type=type_enum,
            material=material_enum,
            width_mm=width_mm,
            height_mm=height_mm,
            depth_mm=depth_mm,
        )

        if exact_match:
            logger.info(
                f"기성함 찾음: {exact_match.model} "
                f"{width_mm}x{height_mm}x{depth_mm}"
            )
            return {
                "classification": "기성함",
                "is_custom": False,
                "model": exact_match.model,
                "price": exact_match.price,
                "enclosure_type": type_enum.value,
                "material": material_enum.value,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "depth_mm": depth_mm,
                "remarks": remarks,
                "nearest_standard": None,
            }

        # 2. 기성함 없음 → 주문제작함
        logger.info(
            f"주문제작함 분류: {type_enum.value} {material_enum.value} "
            f"{width_mm}x{height_mm}x{depth_mm}"
        )

        # 3. 가장 가까운 기성함 검색 (참고용)
        nearest = self._find_nearest_enclosure(
            type_enum, material_enum, width_mm, height_mm, depth_mm
        )

        return {
            "classification": "주문제작함",
            "is_custom": True,
            "model": None,
            "price": None,  # 주문제작 시 별도 산정 필요
            "enclosure_type": type_enum.value,
            "material": material_enum.value,
            "width_mm": width_mm,
            "height_mm": height_mm,
            "depth_mm": depth_mm,
            "remarks": remarks,
            "nearest_standard": nearest,
        }

    def _find_nearest_enclosure(
        self,
        type_enum: EnclosureType,
        material_enum: EnclosureMaterial,
        width_mm: int,
        height_mm: int,
        depth_mm: int,
        margin: int = 100,
    ) -> dict | None:
        """
        가장 가까운 기성함 검색 (주문제작 시 참고용)

        Args:
            type_enum: 외함 종류
            material_enum: 재질
            width_mm, height_mm, depth_mm: 목표 치수
            margin: 검색 범위 (mm)

        Returns:
            가장 가까운 기성함 정보 (없으면 None)
        """
        catalog = self._load_catalog()
        candidates = []

        for enc in catalog.enclosures:
            if enc.type != type_enum:
                continue
            if enc.material != material_enum:
                continue

            # 거리 계산
            w_diff = abs(enc.width_mm - width_mm)
            h_diff = abs(enc.height_mm - height_mm)
            d_diff = abs(enc.depth_mm - depth_mm)

            # margin 범위 내만 후보
            if w_diff <= margin and h_diff <= margin and d_diff <= margin:
                total_diff = w_diff + h_diff + d_diff
                candidates.append((total_diff, enc))

        if not candidates:
            return None

        # 거리 순 정렬, 가장 가까운 것 반환
        candidates.sort(key=lambda x: x[0])
        nearest = candidates[0][1]

        return {
            "model": nearest.model,
            "price": nearest.price,
            "width_mm": nearest.width_mm,
            "height_mm": nearest.height_mm,
            "depth_mm": nearest.depth_mm,
            "size_diff": f"W{nearest.width_mm - width_mm:+d}, H{nearest.height_mm - height_mm:+d}, D{nearest.depth_mm - depth_mm:+d}",
        }

    @staticmethod
    def _get_depth_bracket(depth_mm: int) -> str:
        """D값으로 가격 구간 키를 반환"""
        if depth_mm < 200:
            return "D80-200"
        elif depth_mm < 250:
            return "D200-250"
        elif depth_mm < 300:
            return "D250-300"
        elif depth_mm < 350:
            return "D300-350"
        elif depth_mm < 400:
            return "D350-400"
        elif depth_mm < 450:
            return "D400-450"
        else:
            return "D450-500"

    @staticmethod
    def _normalize_enclosure_type(enclosure_type: str) -> str:
        """외함 종류 문자열을 SSOT 키로 정규화"""
        if "양문" in enclosure_type:
            return "옥내노출_양문형"
        if "매입" in enclosure_type:
            return "매입"
        if "옥외" in enclosure_type or "방수" in enclosure_type:
            return "옥외방수"
        return "옥내노출"

    def get_custom_enclosure_price(
        self,
        enclosure_type: str,
        material: str,
        width_mm: int,
        height_mm: int,
        depth_mm: int,
    ) -> int:
        """
        주문제작함 STEEL 가격 산정 (2026 신규 공식)

        평수 = (W × H) / 90000 → 소수점 1자리 반올림
        원가 = 평수 × 평당단가(종류+D값 구간)
        최종가 = 원가 × 1.3

        Args:
            enclosure_type: 외함 종류 (옥내노출/양문형/매입/옥외방수)
            material: 재질 (STEEL 1.6T 기준)
            width_mm, height_mm, depth_mm: 치수 (mm)

        Returns:
            최종 소비자 가격 (원)
        """
        from kis_estimator_core.core.ssot.constants import (
            CUSTOM_ENCLOSURE_MARKUP,
            CUSTOM_ENCLOSURE_PRICE_PER_PYEONG,
        )

        pyeong = round((width_mm * height_mm) / 90000, 1)

        enc_key = self._normalize_enclosure_type(enclosure_type)
        depth_key = self._get_depth_bracket(depth_mm)

        type_table = CUSTOM_ENCLOSURE_PRICE_PER_PYEONG.get(enc_key, {})
        price_per_pyeong = type_table.get(depth_key)
        if price_per_pyeong is None:
            if type_table:
                price_per_pyeong = max(type_table.values())
            else:
                price_per_pyeong = 25000

        cost = round(pyeong * price_per_pyeong)
        final_price = round(cost * CUSTOM_ENCLOSURE_MARKUP)

        logger.info(
            f"주문제작함 가격: [{enc_key}] {width_mm}x{height_mm}x{depth_mm} "
            f"평수={pyeong} × {price_per_pyeong:,}원/평 = 원가 {cost:,}원 "
            f"→ 최종가 {final_price:,}원 (×{CUSTOM_ENCLOSURE_MARKUP})"
        )

        return final_price

    def get_custom_pcover_price(
        self,
        width_mm: int,
        height_mm: int,
    ) -> int:
        """STEEL P-COVER 가격 (사이즈: W-100 × H-100, 평당 5,500원)"""
        from kis_estimator_core.core.ssot.constants import (
            CUSTOM_ENCLOSURE_MARKUP,
            CUSTOM_PCOVER_STEEL_PRICE_PER_PYEONG,
        )

        pc_w, pc_h = width_mm - 100, height_mm - 100
        pyeong = round((pc_w * pc_h) / 90000, 1)
        cost = round(pyeong * CUSTOM_PCOVER_STEEL_PRICE_PER_PYEONG)
        final_price = round(cost * CUSTOM_ENCLOSURE_MARKUP)
        logger.info(f"STEEL P-COVER: {pc_w}x{pc_h} 평수={pyeong} → {final_price:,}원")
        return final_price

    def get_custom_inner_plate_price(
        self,
        width_mm: int,
        height_mm: int,
        finish: str = "분체도장",
    ) -> int:
        """속판 가격 (사이즈: W-100 × H-100, 아연도금/분체도장)"""
        from kis_estimator_core.core.ssot.constants import (
            CUSTOM_ENCLOSURE_MARKUP,
            CUSTOM_INNER_PLATE_PRICE_PER_PYEONG,
        )

        ip_w, ip_h = width_mm - 100, height_mm - 100
        pyeong = round((ip_w * ip_h) / 90000, 1)
        price_per = CUSTOM_INNER_PLATE_PRICE_PER_PYEONG.get(finish, 5700)
        cost = round(pyeong * price_per)
        final_price = round(cost * CUSTOM_ENCLOSURE_MARKUP)
        logger.info(f"속판({finish}): {ip_w}x{ip_h} 평수={pyeong} → {final_price:,}원")
        return final_price


# Singleton 인스턴스
_ai_catalog_service: AICatalogService | None = None


def get_ai_catalog_service() -> AICatalogService:
    """AICatalogService 싱글톤 인스턴스 반환"""
    global _ai_catalog_service
    if _ai_catalog_service is None:
        _ai_catalog_service = AICatalogService()
    return _ai_catalog_service
