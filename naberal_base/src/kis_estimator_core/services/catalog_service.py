"""
Catalog Service - JSON 카탈로그 서비스

로컬 JSON 파일(ai_catalog_v1.json)을 유일한 데이터 소스로 사용.
Supabase 의존 완전 제거.

절대 원칙:
- 카탈로그에 없는 모델 사용 금지
- 목업/더미 데이터 생성 금지
- 차단기/외함/부속자재 모두 카탈로그 검증 필수

데이터 소스:
- 절대코어파일/ai_catalog_v1.json (유일한 소스)
"""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error
from kis_estimator_core.services.cache import ttl_cache

logger = logging.getLogger(__name__)


@dataclass
class BreakerCatalogItem:
    """차단기 카탈로그 항목"""

    sku: str
    name: str
    brand: str
    model: str
    poles: int
    ampere_range: list[int]  # [20, 30, 40, 50]
    frame_af: int
    capacity_ka: float
    unit_price: float
    type: str  # "Standard/Economy"
    size_mm: list[int]  # [W, H, D]


@dataclass
class EnclosureCatalogItem:
    """외함 카탈로그 항목"""

    sku: str
    name: str
    size_mm: list[int]  # [W, H, D]
    material: str
    thickness_mm: float
    install_location: str
    unit_price: float
    grade: str | None


class CatalogService:
    """
    JSON 카탈로그 서비스

    절대 원칙:
    - 카탈로그에 없는 모델 사용 금지
    - 목업/더미 데이터 생성 금지
    - ai_catalog_v1.json이 유일한 데이터 소스
    """

    def __init__(self):
        """초기화 (JSON에서 즉시 로드)"""
        self._breaker_cache: list[BreakerCatalogItem] | None = None
        self._enclosure_cache: list[EnclosureCatalogItem] | None = None
        self._initialized = False

    def initialize_cache(self, session=None):
        """
        카탈로그 캐시 초기화 (JSON 로드)

        session 파라미터는 하위 호환을 위해 유지하지만 사용하지 않음.
        """
        if self._initialized:
            return

        self._load_from_json()
        self._initialized = True

    def _load_from_json(self):
        """JSON 파일에서 카탈로그 로드 (Fallback)"""
        import json

        # 절대코어파일 경로 찾기
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / "절대코어파일" / "ai_catalog_v1.json"

        logger.info("=" * 60)
        logger.info(f"[CATALOG] Loading from JSON fallback")
        logger.info(f"[CATALOG] __file__: {__file__}")
        logger.info(f"[CATALOG] project_root: {project_root}")
        logger.info(f"[CATALOG] json_path: {json_path}")
        logger.info(f"[CATALOG] json_path.exists(): {json_path.exists()}")

        if not json_path.exists():
            # JSON이 없으면 오류 발생 (목업 금지)
            logger.error(f"[CATALOG] ❌ AI catalog JSON not found: {json_path}")
            # 디버깅: 상위 디렉토리 목록 출력
            try:
                if project_root.exists():
                    logger.error(f"[CATALOG] project_root contents: {list(project_root.iterdir())}")
                core_path = project_root / "절대코어파일"
                if core_path.exists():
                    logger.error(f"[CATALOG] 절대코어파일 contents: {list(core_path.iterdir())}")
            except Exception as e:
                logger.error(f"[CATALOG] Directory listing failed: {e}")

        if not json_path.exists():
            raise RuntimeError(f"JSON catalog not found at {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"[CATALOG] JSON loaded: version={data.get('version', 'unknown')}")
        logger.info(f"[CATALOG] breakers count: {len(data.get('breakers', []))}")
        logger.info(f"[CATALOG] enclosures count: {len(data.get('enclosures', []))}")

        # === Breaker 로딩 ===
        self._breaker_cache = []
        for item in data.get("breakers", []):
            self._breaker_cache.append(
                BreakerCatalogItem(
                    sku=item.get("model", ""),  # SKU가 없으면 모델명 사용
                    name=item.get("model", ""),
                    brand=item.get("brand", ""),
                    model=item.get("model", ""),
                    poles=item.get("poles", 0),
                    ampere_range=[item.get("current_a", 0)],  # JSON은 단일 전류값
                    frame_af=item.get("frame_af", 0),
                    capacity_ka=item.get("breaking_capacity_ka", 0.0),
                    unit_price=float(item.get("price", 0)),
                    type=item.get("series", ""),
                    size_mm=[
                        item.get("dimensions", {}).get("width_mm", 0),
                        item.get("dimensions", {}).get("height_mm", 0),
                        item.get("dimensions", {}).get("depth_mm", 0)
                    ],
                )
            )

        # === Enclosure 로딩 (대표님 제안 + 수정) ===
        self._enclosure_cache = []

        # 설치 장소 매핑 테이블 (완전판) - 각 타입별 고유 키
        location_map = {
            "옥내노출": "indoor",
            "옥내": "indoor",  # 축약형 추가
            "옥외노출": "outdoor",
            "옥외": "outdoor",  # 축약형 추가 (JSON 카탈로그 호환)
            "옥내자립": "indoor_standalone",
            "옥외자립": "outdoor_standalone",
            "매입함": "embedded",  # indoor와 구분되어야 함!
            "전주부착형": "pole_mount",
            "FRP함": "frp",  # outdoor와 구분
            "하이박스": "highbox",  # outdoor와 구분
        }

        for item in data.get("enclosures", []):
            korean_type = item.get("type", "")
            install_location = location_map.get(korean_type, "indoor")

            # Thickness 파싱 (예: "STEEL 1.0T" → 1.0)
            material_str = item.get("material", "steel")
            thickness = 1.6  # 기본값
            match = re.search(r"(\d+\.?\d*)T", material_str, re.IGNORECASE)
            if match:
                thickness = float(match.group(1))

            self._enclosure_cache.append(
                EnclosureCatalogItem(
                    sku=item.get("model", ""),
                    name=item.get("model", ""),
                    size_mm=[
                        item.get("width_mm", 0),
                        item.get("height_mm", 0),
                        item.get("depth_mm", 0)
                    ],
                    material=material_str,
                    thickness_mm=thickness,
                    install_location=install_location,
                    unit_price=float(item.get("price", 0)),
                    grade=item.get("grade")  # JSON에 없으면 None
                )
            )

        logger.info(f"[CATALOG] ✅ JSON loading complete: {len(self._breaker_cache)} breakers, {len(self._enclosure_cache)} enclosures")
        logger.info("=" * 60)

    def find_breaker(
        self, model: str, poles: int, current_a: int
    ) -> BreakerCatalogItem | None:
        """
        차단기 카탈로그 검색 (점수 기반 매칭)

        매칭 우선순위:
        1. 정확 일치 (score=100): model == item.model
        2. 접두사 일치 (score=80): item.model.startswith(model)
        3. 부분 포함 (score=50): model in item.model
        같은 점수 내에서는 가격 오름차순.

        Args:
            model: 모델명 (예: SBS-52, AUTO=자동선택)
            poles: 극수 (2, 3, 4)
            current_a: 정격전류 (A)

        Returns:
            매칭된 카탈로그 항목 (없으면 None)
        """
        if self._breaker_cache is None:
            # 캐시 미초기화 시 자동 로드
            self._load_from_json()
            if self._breaker_cache is None:
                raise_error(
                    ErrorCode.E_INTERNAL,
                    "Catalog cache failed to initialize from JSON",
                )

        if model == "AUTO":
            # AUTO: 스펙 기반 자동 매칭 (frame_AF 작은 순, 가격 낮은 순)
            for item in self._breaker_cache:
                if item.poles != poles:
                    continue
                if current_a not in item.ampere_range:
                    continue
                return item  # 첫 번째 매칭 (이미 정렬됨)
        else:
            # 점수 기반 모델명 매칭
            candidates = []
            model_upper = model.upper()
            for item in self._breaker_cache:
                if item.poles != poles:
                    continue
                if current_a not in item.ampere_range:
                    continue

                item_model_upper = item.model.upper()
                # 1) 정확 일치
                if item_model_upper == model_upper:
                    score = 100
                # 2) 접두사 일치
                elif item_model_upper.startswith(model_upper):
                    score = 80
                # 3) 부분 포함
                elif model_upper in item_model_upper:
                    score = 50
                else:
                    continue

                candidates.append((score, item))

            if candidates:
                # 점수 내림차순 → 같은 점수면 가격 오름차순
                candidates.sort(key=lambda x: (-x[0], x[1].unit_price))
                best = candidates[0]
                if best[0] < 100:
                    logger.warning(
                        f"[CATALOG] 부분 매칭: '{model}' → '{best[1].model}' "
                        f"(score={best[0]}, 후보 {len(candidates)}개)"
                    )
                return best[1]

        return None  # 카탈로그에 없음

    def find_breaker_by_type(
        self, breaker_type: str, poles: int, ampere: int, prefer_economy: bool = True
    ) -> BreakerCatalogItem | None:
        """
        차단기 종류(MCCB/ELB) + 극수 + 전류로 모델 조회

        Frontend가 모델명 없이 type/poles/ampere만 전송하면
        Backend가 카탈로그에서 최적 모델을 찾아 반환.

        차단기 선택 규칙 (CLAUDE.md 기반):
        1. 기본 원칙: 경제형 우선 (prefer_economy=True)
        2. 2P 20A/30A: 소형 차단기 사용 (SIE-32, SIB-32)
        3. 4P 50AF (20~50A): 경제형 없으므로 표준형 사용

        Args:
            breaker_type: "MCCB" or "ELB"
            poles: 극수 (2, 3, 4)
            ampere: 정격전류 (A)
            prefer_economy: 경제형 우선 여부 (기본 True)

        Returns:
            매칭된 카탈로그 항목 (없으면 None)
        """
        if self._breaker_cache is None:
            # Auto-initialize from JSON if not yet done (defensive fallback)
            logger.warning("Catalog cache not initialized - auto-loading from JSON")
            self._load_from_json()
            if self._breaker_cache is None:
                raise_error(
                    ErrorCode.E_INTERNAL,
                    "Catalog cache failed to initialize from JSON",
                )

        # 모델명 패턴으로 breaker_type 필터링
        # MCCB: SB*, AB*, SIB* (배선용)
        # ELB: SE*, EB*, SIE*, *GRHS (누전)
        is_mccb = breaker_type.upper() == "MCCB"

        # 디버그 로깅
        logger.info(f"[CATALOG] find_breaker_by_type: type={breaker_type}, poles={poles}, ampere={ampere}")
        logger.info(f"[CATALOG] breaker_cache size: {len(self._breaker_cache) if self._breaker_cache else 0}")

        # 소형 차단기 특수 규칙: 2P 20A/30A
        if poles == 2 and ampere in [20, 30]:
            target_model = "SIB-32" if is_mccb else "SIE-32"
            logger.info(f"[CATALOG] Searching for small breaker: target_model={target_model}")
            for item in self._breaker_cache:
                if item.model == target_model:
                    logger.info(f"[CATALOG] Found model {target_model}: ampere_range={item.ampere_range}")
                    if ampere in item.ampere_range:
                        logger.info(f"[CATALOG] ✅ Match found: {item.model} {item.poles}P {item.ampere_range}")
                        return item
            logger.warning(f"[CATALOG] ❌ No match for small breaker {target_model} {ampere}A")

        # 일반 차단기 검색
        candidates = []
        for item in self._breaker_cache:
            # 극수 체크
            if item.poles != poles:
                continue
            # 전류 체크
            if ampere not in item.ampere_range:
                continue

            # breaker_type 체크 (모델명 패턴)
            model_upper = item.model.upper()
            is_item_mccb = (
                model_upper.startswith("SB")
                or model_upper.startswith("AB")
                or model_upper.startswith("SIB")
                or model_upper.startswith("BS")
            )
            is_item_elb = (
                model_upper.startswith("SE")
                or model_upper.startswith("EB")
                or model_upper.startswith("SIE")
                or "GRHS" in model_upper
            )

            if is_mccb and not is_item_mccb:
                continue
            if not is_mccb and not is_item_elb:
                continue

            candidates.append(item)

        if not candidates:
            logger.warning(f"[CATALOG] ❌ No candidates found for {breaker_type} {poles}P {ampere}A")
            return None

        logger.info(f"[CATALOG] Found {len(candidates)} candidates for {breaker_type} {poles}P {ampere}A")

        # 정렬: 경제형 우선 (type 필드에 "Economy" 포함) → 가격 낮은 순
        if prefer_economy:
            # 경제형 (Economy/경제) 먼저
            economy = [c for c in candidates if "economy" in (c.type or "").lower() or "경제" in (c.type or "")]
            standard = [c for c in candidates if c not in economy]

            if economy:
                economy.sort(key=lambda x: x.unit_price)
                return economy[0]
            if standard:
                standard.sort(key=lambda x: x.unit_price)
                return standard[0]
        else:
            candidates.sort(key=lambda x: x.unit_price)
            return candidates[0]

        return None

    def find_enclosure(
        self, width: int, height: int, depth: int
    ) -> EnclosureCatalogItem | None:
        """
        외함 카탈로그 검색 (메모리 캐시 전용, sync 유지)
        정확 매칭 → 가까운 기성함 → 주문제작

        Phase C: 캐시는 startup에서 async로 초기화됨
        이 메서드는 순수 메모리 연산 (DB 접근 0)

        Args:
            width: 폭 (mm)
            height: 높이 (mm)
            depth: 깊이 (mm)

        Returns:
            매칭된 카탈로그 항목 (없으면 None = 주문제작)

        Raises:
            RuntimeError: 캐시 미초기화 (startup 실패)
        """
        if self._enclosure_cache is None:
            raise_error(
                ErrorCode.E_INTERNAL,
                "Catalog cache not initialized (check FastAPI startup hook)",
            )

        # 1. 정확한 크기 매칭 시도
        exact_matches = []
        for item in self._enclosure_cache:
            if (
                item.size_mm[0] == width
                and item.size_mm[1] == height
                and item.size_mm[2] == depth
            ):
                exact_matches.append(item)

        if exact_matches:
            # 가격 낮은 순으로 정렬 후 첫 번째 반환
            exact_matches.sort(key=lambda x: x.unit_price)
            return exact_matches[0]

        # 2. 가까운 기성함 검색 (여유 ±50mm)
        margin = 50
        candidates = []

        for item in self._enclosure_cache:
            w, h, d = item.size_mm

            # ±50mm 범위 체크
            if not (width - margin <= w <= width + margin):
                continue
            if not (height - margin <= h <= height + margin):
                continue
            if not (depth - margin <= d <= depth + margin):
                continue

            # distance 계산
            distance = abs(w - width) + abs(h - height) + abs(d - depth)
            candidates.append((distance, item))

        if candidates:
            # distance 작은 순, 가격 낮은 순으로 정렬
            candidates.sort(key=lambda x: (x[0], x[1].unit_price))
            return candidates[0][1]

        return None  # 주문제작 필요

    def find_enclosure_strict(
        self,
        install_location: str,
        material: str,
        width: int,
        height: int,
        depth: int,
    ) -> EnclosureCatalogItem | None:
        """
        엄격한 외함 카탈로그 검색 (install_location + material 필수 일치)

        옥내/옥외 혼동 방지를 위한 엄격한 검색.
        install_location과 material이 정확히 일치해야만 매칭.

        Args:
            install_location: 설치장소 (indoor, outdoor, indoor_standalone 등)
            material: 재질 (steel, SUS201 등)
            width: 폭 (mm)
            height: 높이 (mm)
            depth: 깊이 (mm)

        Returns:
            매칭된 카탈로그 항목 (없으면 None = 주문제작)
        """
        if self._enclosure_cache is None:
            raise_error(
                ErrorCode.E_INTERNAL,
                "Catalog cache not initialized (check FastAPI startup hook)",
            )

        # install_location 매핑 (입력 정규화) - 각 타입별 고유 키
        location_map = {
            "옥내노출": "indoor",
            "옥내": "indoor",
            "indoor": "indoor",
            "indoor_exposed": "indoor",
            "옥외노출": "outdoor",
            "옥외": "outdoor",
            "outdoor": "outdoor",
            "outdoor_exposed": "outdoor",
            "옥내자립": "indoor_standalone",
            "indoor_standalone": "indoor_standalone",
            "옥외자립": "outdoor_standalone",
            "outdoor_standalone": "outdoor_standalone",
            "매입함": "embedded",  # indoor와 구분
            "embedded": "embedded",
            "FRP함": "frp",  # outdoor와 구분
            "frp": "frp",
            "하이박스": "highbox",  # outdoor와 구분
            "highbox": "highbox",
            "전주부착형": "pole_mount",
            "pole_mount": "pole_mount",
        }
        normalized_location = location_map.get(install_location.lower(), install_location.lower())

        # material 매핑 (입력 정규화)
        material_map = {
            "steel 1.6t": "steel",
            "steel": "steel",
            "스틸": "steel",
            "스틸 1.6t": "steel",
            "steel 1.0t": "steel_1.0t",
            "sus201": "sus201",
            "sus201 1.2t": "sus201",
            "sus": "sus201",
            "스테인레스": "sus201",
        }
        normalized_material = material_map.get(material.lower(), material.lower())

        # 1. 정확한 크기 + install_location + material 매칭
        exact_matches = []
        for item in self._enclosure_cache:
            # install_location 엄격 비교
            item_location = item.install_location.lower() if item.install_location else ""
            if item_location != normalized_location:
                continue

            # material 엄격 비교 (양쪽 모두 정규화해서 비교)
            item_material_raw = item.material.lower() if item.material else ""
            item_material = material_map.get(item_material_raw, item_material_raw)
            if item_material != normalized_material:
                continue

            # 크기 정확 매칭
            if (
                item.size_mm[0] == width
                and item.size_mm[1] == height
                and item.size_mm[2] == depth
            ):
                exact_matches.append(item)

        if exact_matches:
            exact_matches.sort(key=lambda x: x.unit_price)
            return exact_matches[0]

        # 2. install_location + material 일치 + 근사 크기 (±50mm)
        margin = 50
        candidates = []

        for item in self._enclosure_cache:
            # install_location 엄격 비교
            item_location = item.install_location.lower() if item.install_location else ""
            if item_location != normalized_location:
                continue

            # material 엄격 비교 (양쪽 모두 정규화해서 비교)
            item_material_raw = item.material.lower() if item.material else ""
            item_material = material_map.get(item_material_raw, item_material_raw)
            if item_material != normalized_material:
                continue

            w, h, d = item.size_mm
            # ±50mm 범위 체크
            if not (width - margin <= w <= width + margin):
                continue
            if not (height - margin <= h <= height + margin):
                continue
            if not (depth - margin <= d <= depth + margin):
                continue

            distance = abs(w - width) + abs(h - height) + abs(d - depth)
            candidates.append((distance, item))

        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1].unit_price))
            return candidates[0][1]

        return None  # 주문제작 필요 (install_location + material 일치 항목 없음)


# 싱글톤 인스턴스
_global_service: CatalogService | None = None


def get_catalog_service() -> CatalogService:
    """글로벌 CatalogService 인스턴스 반환 (싱글톤)"""
    global _global_service
    if _global_service is None:
        _global_service = CatalogService()
    return _global_service


# ===== Phase VII: TTL Cached Helper Functions =====


@ttl_cache(ttl=int(os.getenv("KIS_CATALOG_CACHE_TTL", "900")))
def get_catalog_items(kind: str):
    """
    Get catalog items by kind with TTL caching (Phase VII).

    Args:
        kind: Item kind ("breaker", "enclosure", "accessory")

    Returns:
        List of catalog items

    Cache TTL: 900s (env: KIS_CATALOG_CACHE_TTL)
    """
    service = get_catalog_service()

    if kind == "breaker":
        if service._breaker_cache is None:
            raise_error(
                ErrorCode.E_INTERNAL, "Catalog cache not initialized (check startup)"
            )
        return service._breaker_cache

    elif kind == "enclosure":
        if service._enclosure_cache is None:
            raise_error(
                ErrorCode.E_INTERNAL, "Catalog cache not initialized (check startup)"
            )
        return service._enclosure_cache

    else:
        raise_error(ErrorCode.E_VALIDATION, f"Unknown catalog kind: {kind}")


@ttl_cache(ttl=int(os.getenv("KIS_PRICE_CACHE_TTL", "300")))
def get_price(sku: str):
    """
    Get price for SKU with TTL caching (Phase VII).

    Args:
        sku: Stock keeping unit code

    Returns:
        float: Unit price

    Cache TTL: 300s (env: KIS_PRICE_CACHE_TTL)
    """
    service = get_catalog_service()

    # Check breaker cache
    if service._breaker_cache:
        for breaker_item in service._breaker_cache:
            if breaker_item.sku == sku:
                return breaker_item.unit_price

    # Check enclosure cache
    if service._enclosure_cache:
        for enclosure_item in service._enclosure_cache:
            if enclosure_item.sku == sku:
                return enclosure_item.unit_price

    raise_error(ErrorCode.E_NOT_FOUND, f"SKU not found in catalog: {sku}")
