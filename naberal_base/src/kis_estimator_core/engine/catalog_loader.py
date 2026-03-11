"""
Catalog Loader - HDS 카탈로그 로드 (로컬 JSON 우선)

Task 8: HDS 카탈로그 조회 로직 구현
Task 11: Supabase 실제 연결 추가
- 데이터 소스 우선순위:
  1. 로컬 파일: knowledge_consolidation/output/enclosures.json
  2. Supabase: shared.catalog_items (category='enclosure')

목업 없음 규칙: 실제 파일/DB 없으면 즉시 RuntimeError
"""

import json
from dataclasses import dataclass
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


@dataclass
class HDSCatalogItem:
    """HDS 카탈로그 항목"""

    model: str
    category: str
    material: str
    thickness_mm: float
    install_location: str
    size_mm: tuple[int, int, int]  # W, H, D
    price: int
    custom_required: bool
    grade: str | None


class CatalogLoader:
    """
    HDS 카탈로그 로더

    데이터 소스 우선순위:
    1. 로컬 JSON: knowledge_consolidation/output/enclosures.json
    2. Supabase: shared.catalog_items (category='enclosure')
    """

    def __init__(self, local_path: Path | None = None, use_supabase: bool = True):
        """
        Args:
            local_path: 로컬 JSON 파일 경로 (기본: knowledge_consolidation/output/enclosures.json)
            use_supabase: Supabase 사용 여부 (기본: True)
        """
        if local_path is None:
            # 프로젝트 루트 기준 상대 경로
            project_root = Path(__file__).parent.parent.parent.parent
            local_path = (
                project_root / "knowledge_consolidation" / "output" / "enclosures.json"
            )

        self.local_path = local_path
        self.use_supabase = use_supabase
        self._catalog: list[HDSCatalogItem] = []
        self._loaded = False
        self._supabase_available = False

    async def load(self) -> None:
        """
        HDS 카탈로그 로드 (로컬 우선, Supabase 백업) - Async

        우선순위:
        1. 로컬 JSON 파일
        2. Supabase (로컬 실패 시)

        Raises:
            RuntimeError: 모든 소스에서 로드 실패 시
            ValueError: 데이터 구조가 잘못된 경우
        """
        # 1. 로컬 JSON 시도
        if self.local_path.exists():
            try:
                self._load_from_local()
                print(f"[OK] HDS catalog loaded from LOCAL: {len(self._catalog)} items")
                return
            except Exception as e:
                print(f"[WARN] Local load failed: {e}")

        # 2. Supabase 시도 (로컬 실패 시)
        if self.use_supabase:
            try:
                await self._load_from_supabase_async()
                print(
                    f"[OK] HDS catalog loaded from SUPABASE: {len(self._catalog)} items"
                )
                return
            except Exception as e:
                print(f"[WARN] Supabase load failed: {e}")

        # 3. 모든 소스 실패
        raise_error(
            ErrorCode.E_CATALOG_LOAD,
            f"카탈로그 로드 실패: 로컬 파일({self.local_path}) 및 Supabase 연결 실패\n"
            "목업 금지 규칙: 가짜 데이터 생성 불가",
        )

    def _load_from_local(self) -> None:
        """로컬 JSON 파일에서 로드"""
        try:
            with open(self.local_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise_error(ErrorCode.E_CATALOG_LOAD, f"카탈로그 파일 읽기 실패: {e}")

        # 메타 검증
        if "meta" not in data:
            raise_error(ErrorCode.E_CATALOG_LOAD, "meta 섹션이 없습니다")

        meta = data["meta"]
        if meta.get("category") != "enclosures":
            raise_error(
                ErrorCode.E_CATALOG_LOAD, f"잘못된 카테고리: {meta.get('category')}"
            )

        # HDS 카탈로그 파싱
        if "hds_catalog" not in data:
            raise_error(ErrorCode.E_CATALOG_LOAD, "hds_catalog 섹션이 없습니다")

        catalog = data["hds_catalog"]

        # standard 항목 로드
        if "standard" in catalog and "items" in catalog["standard"]:
            for item in catalog["standard"]["items"]:
                parsed = self._parse_item(item)
                if parsed is not None:  # size_mm이 None인 항목 제외
                    self._catalog.append(parsed)

        self._loaded = True

    async def _load_from_supabase_async(self) -> None:
        """Supabase에서 HDS 카탈로그 로드 (비동기)"""
        try:
            # api 모듈 import (프로젝트 루트에 있음)
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from sqlalchemy import text

            from api.db import AsyncSessionLocal
        except ImportError as e:
            raise_error(ErrorCode.E_CATALOG_LOAD, f"Supabase 모듈 import 실패: {e}")

        async with AsyncSessionLocal() as session:
            # shared.catalog_items에서 enclosure 카테고리 조회 (실제 스키마 기반)
            query = text(
                """
                SELECT
                    sku as model,
                    kind,
                    name,
                    spec,
                    unit_price as price,
                    meta
                FROM shared.catalog_items
                WHERE kind = 'enclosure'
                AND sku LIKE 'HB%'
                ORDER BY sku
            """
            )

            result = await session.execute(query)
            rows = result.fetchall()

            if not rows:
                raise_error(
                    ErrorCode.E_CATALOG_LOAD, "Supabase에 enclosure 데이터가 없습니다"
                )

            # 파싱 (실제 스키마 기반)
            for row in rows:
                try:
                    # SKU에서 크기 추출 (예: HB607020 → 600×700×200)
                    sku = row.model
                    if len(sku) >= 8 and sku.startswith("HB"):
                        size_str = sku[2:]  # "607020"
                        if len(size_str) == 6:
                            w = int(size_str[0:2]) * 10  # 60 → 600
                            h = int(size_str[2:4]) * 10  # 70 → 700
                            d = int(size_str[4:6]) * 10  # 20 → 200

                            # meta에서 추가 정보 추출
                            meta = row.meta or {}
                            material = meta.get("material", "steel")
                            install_location = meta.get("install_location", "indoor")
                            thickness_mm = meta.get("thickness_mm", 1.6)

                            item = HDSCatalogItem(
                                model=sku,
                                category="enclosure",
                                material=material,
                                thickness_mm=thickness_mm,
                                install_location=install_location,
                                size_mm=(w, h, d),
                                price=int(row.price) if row.price else 0,
                                custom_required=False,
                                grade=None,
                            )
                            self._catalog.append(item)
                except Exception as e:
                    print(f"[WARN] Supabase 항목 파싱 실패: {row.model} - {e}")
                    continue

        self._loaded = True
        self._supabase_available = True

    def _parse_item(self, item: dict) -> HDSCatalogItem | None:
        """
        JSON 항목을 HDSCatalogItem으로 변환

        size_mm이 None인 항목은 스킵 (주문제작 전용)
        """
        size_mm = item.get("size_mm")

        # size_mm이 None인 항목은 스킵
        if size_mm is None:
            return None

        if not isinstance(size_mm, list) or len(size_mm) != 3:
            raise_error(ErrorCode.E_CATALOG_LOAD, f"잘못된 size_mm: {size_mm}")

        return HDSCatalogItem(
            model=item["model"],
            category=item["category"],
            material=item["material"],
            thickness_mm=item["thickness_mm"],
            install_location=item["install_location"],
            size_mm=(size_mm[0], size_mm[1], size_mm[2]),
            price=item["price"],
            custom_required=item["custom_required"],
            grade=item.get("grade"),
        )

    async def find_exact_match(
        self,
        width: int,
        height: int,
        depth: int,
        material: str | None = None,
        install_location: str | None = None,
    ) -> HDSCatalogItem | None:
        """
        정확한 크기 매칭 (W×H×D) - Async

        Args:
            width: 폭 (mm)
            height: 높이 (mm)
            depth: 깊이 (mm)
            material: 재질 필터 (옵션)
            install_location: 설치 위치 필터 (옵션)

        Returns:
            매칭된 항목 (없으면 None)
        """
        if not self._loaded:
            await self.load()

        for item in self._catalog:
            if item.size_mm != (width, height, depth):
                continue

            if material and item.material != material:
                continue

            if install_location and item.install_location != install_location:
                continue

            return item

        return None

    async def find_nearest_match(
        self,
        width: int,
        height: int,
        depth: int,
        max_diff_mm: int = 300,
    ) -> HDSCatalogItem | None:
        """
        가장 가까운 크기 매칭 (여유 있는 크기) - Async

        핵심 규칙 (대표님 지시):
        1. 함이 크게 → OK (단가만 올라감)
        2. 함이 작게 → 절대 금지 (대형 사고)
        3. 폭은 1단계만 증가 허용 (예: 600→700 OK, 600→800 금지)

        예시:
        - 계산: 600×1675×150
        - 추천: 700×1800×250 ✅ (폭 1단계, 함이 크므로 OK)
        - 추천: 800×1800×250 ❌ (폭 2단계, 금지)

        Args:
            width: 필요한 폭 (mm)
            height: 필요한 높이 (mm)
            depth: 필요한 깊이 (mm)
            max_diff_mm: 최대 허용 차이 (mm)

        Returns:
            매칭된 항목 (없으면 None = 주문제작)
        """
        if not self._loaded:
            await self.load()

        # 카탈로그의 모든 폭 값 추출 및 정렬
        all_widths = sorted({item.size_mm[0] for item in self._catalog})

        # 요구 폭의 다음 단계 찾기 (1단계만 허용)
        max_allowed_width = None
        for w in all_widths:
            if w >= width:
                # 첫 번째로 크거나 같은 폭 찾음
                idx = all_widths.index(w)
                if idx + 1 < len(all_widths):
                    # 1단계 위까지 허용
                    max_allowed_width = all_widths[idx + 1]
                else:
                    # 마지막 단계면 그대로
                    max_allowed_width = w
                break

        if max_allowed_width is None:
            # 요구 폭이 카탈로그 최대값보다 큼 → 주문제작
            return None

        candidates = []

        for item in self._catalog:
            w, h, d = item.size_mm

            # 크기가 충분한지 확인 (같거나 크면 OK)
            if w < width or h < height or d < depth:
                continue  # 작으면 절대 금지

            # 폭 1단계 제한 (대표님 규칙)
            if w > max_allowed_width:
                continue  # 폭 2단계 이상 금지

            # 차이 계산 (모두 양수 또는 0)
            diff = (w - width) + (h - height) + (d - depth)

            if diff <= max_diff_mm:
                candidates.append((diff, item))

        if not candidates:
            return None  # 주문제작

        # 차이가 가장 작은 것 선택
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    async def list_all(self) -> list[HDSCatalogItem]:
        """전체 카탈로그 반환 - Async"""
        if not self._loaded:
            await self.load()

        return self._catalog.copy()


# 싱글톤 인스턴스
_global_loader: CatalogLoader | None = None


async def get_catalog_loader() -> CatalogLoader:
    """글로벌 CatalogLoader 인스턴스 반환 - Async"""
    global _global_loader
    if _global_loader is None:
        _global_loader = CatalogLoader()
        await _global_loader.load()
    return _global_loader
