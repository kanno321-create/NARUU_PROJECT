"""
AI Estimate Storage - AI Chat용 견적 데이터 저장소

AI Manager에서 생성한 견적 데이터를 저장하고 조회합니다.
- 메모리 기반 캐시 (세션 동안 유지)
- 선택적 DB 저장 (영구 저장)

Contract-First + Zero-Mock
NO MOCKS - Real data storage only
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StoredEstimate:
    """저장된 견적 데이터"""
    estimate_id: str
    created_at: str
    form_data: dict
    panel_data: dict | None = None  # 도면 생성용
    placement_result: dict | None = None  # 배치 결과
    pdf_path: str | None = None  # 생성된 PDF 경로
    drawings: dict | None = None  # 생성된 도면들


class AIEstimateStorage:
    """
    AI Chat용 견적 저장소

    싱글톤 패턴으로 세션 동안 데이터 유지
    """

    _instance: Optional['AIEstimateStorage'] = None
    _estimates: dict[str, StoredEstimate] = {}

    def __new__(cls) -> 'AIEstimateStorage':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._estimates = {}
            logger.info("AIEstimateStorage initialized")
        return cls._instance

    def save_estimate(
        self,
        estimate_id: str,
        form_data: dict,
    ) -> StoredEstimate:
        """
        견적 데이터 저장

        Args:
            estimate_id: 견적 ID (EST-YYYYMMDDHHMMSS)
            form_data: EstimateParserService에서 생성한 폼 데이터

        Returns:
            StoredEstimate: 저장된 견적 객체
        """
        # form_data에서 panel_data 구성
        panel_data = self._build_panel_data(estimate_id, form_data)
        placement_result = self._build_placement_result(form_data)

        stored = StoredEstimate(
            estimate_id=estimate_id,
            created_at=datetime.now(UTC).isoformat(),
            form_data=form_data,
            panel_data=panel_data,
            placement_result=placement_result,
        )

        self._estimates[estimate_id] = stored
        logger.info(f"Estimate saved: {estimate_id}")

        return stored

    def get_estimate(self, estimate_id: str) -> StoredEstimate | None:
        """
        견적 데이터 조회

        Args:
            estimate_id: 견적 ID

        Returns:
            StoredEstimate or None if not found
        """
        estimate = self._estimates.get(estimate_id)
        if estimate:
            logger.debug(f"Estimate found: {estimate_id}")
        else:
            logger.debug(f"Estimate not found: {estimate_id}")
        return estimate

    def update_drawings(
        self,
        estimate_id: str,
        drawings: dict,
    ) -> bool:
        """
        견적에 도면 정보 업데이트

        Args:
            estimate_id: 견적 ID
            drawings: 생성된 도면 정보

        Returns:
            bool: 성공 여부
        """
        estimate = self._estimates.get(estimate_id)
        if estimate:
            estimate.drawings = drawings
            logger.info(f"Drawings updated for: {estimate_id}")
            return True
        return False

    def update_pdf_path(
        self,
        estimate_id: str,
        pdf_path: str,
    ) -> bool:
        """
        견적에 PDF 경로 업데이트

        Args:
            estimate_id: 견적 ID
            pdf_path: 생성된 PDF 파일 경로

        Returns:
            bool: 성공 여부
        """
        estimate = self._estimates.get(estimate_id)
        if estimate:
            estimate.pdf_path = pdf_path
            logger.info(f"PDF path updated for: {estimate_id}")
            return True
        return False

    def list_estimates(self, limit: int = 10) -> list:
        """
        최근 견적 목록 조회

        Args:
            limit: 최대 반환 개수

        Returns:
            list: 견적 ID 목록 (최신순)
        """
        sorted_estimates = sorted(
            self._estimates.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return [e.estimate_id for e in sorted_estimates[:limit]]

    def _build_panel_data(self, estimate_id: str, form_data: dict) -> dict:
        """
        form_data에서 도면 생성용 panel_data 구성

        Args:
            estimate_id: 견적 ID
            form_data: 파싱된 폼 데이터

        Returns:
            dict: 도면 서비스용 패널 데이터
        """
        enclosure = form_data.get("enclosure", {})
        main_breaker = form_data.get("main_breaker", {})

        # 차단기 치수 매핑 (CLAUDE.md 참조)
        breaker_dimensions = {
            50: {"width": {"2P": 50, "3P": 75, "4P": 100}, "height": 130},
            100: {"width": {"2P": 50, "3P": 75, "4P": 100}, "height": 130},
            125: {"width": {"2P": 60, "3P": 90, "4P": 120}, "height": 155},
            200: {"width": {"2P": 70, "3P": 105, "4P": 140}, "height": 165},
            250: {"width": {"2P": 70, "3P": 105, "4P": 140}, "height": 165},
            400: {"width": {"3P": 140, "4P": 187}, "height": 257},
            600: {"width": {"3P": 210, "4P": 280}, "height": 280},
            800: {"width": {"3P": 210, "4P": 280}, "height": 280},
        }

        # 메인 차단기 프레임 결정
        current_a = main_breaker.get("current_a", 50)
        if current_a <= 50:
            frame = 50
        elif current_a <= 100:
            frame = 100
        elif current_a <= 125:
            frame = 125
        elif current_a <= 250:
            frame = 250
        elif current_a <= 400:
            frame = 400
        else:
            frame = 600

        poles = main_breaker.get("poles", 4)
        poles_key = f"{poles}P"
        dims = breaker_dimensions.get(frame, breaker_dimensions[100])

        main_width = dims["width"].get(poles_key, dims["width"].get("4P", 100))
        main_height = dims["height"]

        panel_data = {
            "name": estimate_id,
            "enclosure": {
                "width": enclosure.get("width", 600),
                "height": enclosure.get("height", 800),
                "depth": enclosure.get("depth", 200),
                "material": enclosure.get("material", "STEEL 1.6T"),
                "type": enclosure.get("type", "옥내노출"),
                "ip_rating": "IP44",
                "classification": enclosure.get("classification", "주문제작함"),
            },
            "main_breaker": {
                "model": main_breaker.get("model", "SBE-104"),
                "brand": main_breaker.get("brand", "상도"),
                "series": main_breaker.get("series", "경제형"),
                "category": main_breaker.get("category", "MCCB"),
                "poles": poles,
                "rating": f"{current_a}A",
                "frame": frame,
                "width": main_width,
                "height": main_height,
                "price": main_breaker.get("price", 0),
            },
            "customer": form_data.get("customer"),
        }

        return panel_data

    def _build_placement_result(self, form_data: dict) -> dict:
        """
        form_data에서 배치 결과 구성

        Args:
            form_data: 파싱된 폼 데이터

        Returns:
            dict: 차단기 배치 결과
        """
        branch_breakers = form_data.get("branch_breakers", [])

        # 차단기 치수 매핑
        breaker_dimensions = {
            50: {"width": {"2P": 50, "3P": 75, "4P": 100}, "height": 130},
            100: {"width": {"2P": 50, "3P": 75, "4P": 100}, "height": 130},
        }

        breakers = []
        side = "left"

        for br in branch_breakers:
            current_a = br.get("current_a", 30)
            poles = br.get("poles", 3)
            quantity = br.get("quantity", 1)

            # 프레임 결정
            frame = 50 if current_a <= 50 else 100
            poles_key = f"{poles}P"
            dims = breaker_dimensions.get(frame, breaker_dimensions[50])

            br_width = dims["width"].get(poles_key, 75)
            br_height = dims["height"]

            for _ in range(quantity):
                breakers.append({
                    "model": br.get("model", f"SBE-{frame}{poles}"),
                    "category": br.get("category", "ELB"),
                    "poles": poles,
                    "rating": f"{current_a}A",
                    "frame": frame,
                    "side": side,
                    "width": br_width,
                    "height": br_height,
                    "price": br.get("price", 0),
                })
                # 좌우 번갈아 배치
                side = "right" if side == "left" else "left"

        return {
            "breakers": breakers,
            "total_count": len(breakers),
            "left_count": sum(1 for b in breakers if b["side"] == "left"),
            "right_count": sum(1 for b in breakers if b["side"] == "right"),
        }


# 싱글톤 인스턴스 접근
_storage: AIEstimateStorage | None = None


def get_ai_estimate_storage() -> AIEstimateStorage:
    """AIEstimateStorage 싱글톤"""
    global _storage
    if _storage is None:
        _storage = AIEstimateStorage()
    return _storage
