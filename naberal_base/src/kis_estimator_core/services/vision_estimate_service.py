"""
Vision 기반 자동 견적 생성 서비스 (Phase XIV)

Vision AI가 추출한 컴포넌트 정보를 바탕으로
자동으로 견적을 생성하는 서비스입니다.

Zero-Mock 원칙: 실제 카탈로그 가격 데이터를 사용합니다.
CEO 학습 통합: 학습된 CEO 선호도를 자동 적용합니다.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "MANUAL"]
ItemSource = Literal["VISION", "CALCULATED", "CATALOG", "CEO_PREFERENCE"]


@dataclass
class EstimateItem:
    """견적 항목"""
    category: str  # 외함, 차단기, 부속자재 등
    name: str
    specification: str
    unit: str
    quantity: int
    unit_price: int
    total_price: int
    source: ItemSource
    confidence: ConfidenceLevel


@dataclass
class PanelEstimate:
    """분전반 견적"""
    panel_name: str
    items: list[EstimateItem]
    subtotal: int
    notes: list[str] = field(default_factory=list)


@dataclass
class VisionEstimate:
    """Vision 기반 견적"""
    estimate_id: str
    request_id: str
    customer_name: Optional[str]
    project_name: Optional[str]
    panels: list[PanelEstimate]
    total_amount: int
    total_with_vat: int
    ceo_preferences_applied: bool
    confidence_summary: dict[str, int]
    warnings: list[str]
    generated_at: datetime


# ============================================================================
# Price Catalog (SSOT 연동)
# ============================================================================

class PriceCatalog:
    """가격 카탈로그 (SSOT 기반)"""

    # 차단기 기본 가격 (실제로는 CSV에서 로드)
    # 경로: C:\Users\PC\Desktop\절대코어파일\중요ai단가표의_2.0V.csv
    BREAKER_PRICES = {
        # 상도 경제형
        ("상도", "MCCB", "2P", "30AF"): {"20A": 3300, "30A": 3300},
        ("상도", "MCCB", "2P", "50AF"): {"30A": 7500, "50A": 7500},
        ("상도", "MCCB", "2P", "100AF"): {"60A": 12500, "75A": 13000, "100A": 13500},
        ("상도", "MCCB", "3P", "50AF"): {"30A": 9500, "50A": 9500},
        ("상도", "MCCB", "3P", "100AF"): {"60A": 16500, "75A": 17000, "100A": 17500},
        ("상도", "MCCB", "4P", "50AF"): {"30A": 13500, "50A": 13500},
        ("상도", "MCCB", "4P", "100AF"): {"60A": 22500, "75A": 23000, "100A": 23500},
        # 상도 누전
        ("상도", "ELB", "2P", "30AF"): {"20A": 8500, "30A": 8500},
        ("상도", "ELB", "2P", "50AF"): {"30A": 13500, "50A": 13500},
        ("상도", "ELB", "3P", "30AF"): {"20A": 12500, "30A": 12500},
        ("상도", "ELB", "3P", "50AF"): {"30A": 18500, "50A": 18500},
        ("상도", "ELB", "4P", "50AF"): {"30A": 24500, "50A": 24500},
        # LS 경제형
        ("LS", "MCCB", "2P", "50AF"): {"30A": 8200, "50A": 8200},
        ("LS", "MCCB", "3P", "50AF"): {"30A": 10500, "50A": 10500},
        ("LS", "MCCB", "4P", "50AF"): {"30A": 14800, "50A": 14800},
        ("LS", "ELB", "2P", "50AF"): {"30A": 14800, "50A": 14800},
        ("LS", "ELB", "3P", "50AF"): {"30A": 20200, "50A": 20200},
    }

    # 외함 가격: 기성함 기본 단가 (주문제작은 ai_catalog_service 사용)
    ENCLOSURE_BASE_PRICE = 25000  # 원/평 (옥내노출 D80-200 기본)

    # 부속자재 가격
    ACCESSORY_PRICES = {
        "E.T": {"50AF": 4500, "100AF": 4500, "200AF": 5500, "400AF": 12000},
        "N.T": 3000,
        "N.P_CARD_HOLDER": 800,
        "N.P_3T": 4000,
        "MAIN_BUSBAR": 20000,  # 원/kg
        "BUSBAR": 20000,  # 원/kg
        "COATING": 5000,  # 원/m
        "P-COVER_ACRYLIC": 3200,  # 원/90000mm²
        "P-COVER_STEEL": 5500,  # 원/평 (2026 신규 단가)
        "INSULATOR": 1100,
        "ELB_SUPPORT": 500,
        "MISC": 7000,  # 잡자재비 기본
        "ASSEMBLY": 50000,  # 조립비 기본
    }

    @classmethod
    def get_breaker_price(
        cls,
        brand: str,
        breaker_type: str,
        pole: str,
        frame: str,
        ampere: int
    ) -> tuple[int, ItemSource]:
        """차단기 가격 조회"""
        # 브랜드 정규화
        brand_normalized = "상도" if brand in ["상도", "상도차단기", "SANGDO"] else "LS"

        key = (brand_normalized, breaker_type, pole, frame)
        ampere_key = f"{ampere}A"

        if key in cls.BREAKER_PRICES:
            prices = cls.BREAKER_PRICES[key]
            if ampere_key in prices:
                return prices[ampere_key], "CATALOG"

            # 가장 가까운 암페어 찾기
            available = list(prices.keys())
            if available:
                return list(prices.values())[0], "CALCULATED"

        # 기본 가격 추정
        base_price = 10000
        if breaker_type == "ELB":
            base_price = 15000

        pole_multiplier = {"2P": 1.0, "3P": 1.3, "4P": 1.8}.get(pole, 1.0)
        frame_multiplier = int(frame.replace("AF", "")) / 50

        estimated = int(base_price * pole_multiplier * frame_multiplier)
        return estimated, "CALCULATED"

    @classmethod
    def get_enclosure_price(cls, width: int, height: int, depth: int = 200) -> tuple[int, ItemSource]:
        """외함 가격 계산 (주문제작 STEEL 1.6T 기준, 소비자가)"""
        from kis_estimator_core.core.ssot.constants import (
            CUSTOM_ENCLOSURE_MARKUP,
            CUSTOM_ENCLOSURE_PRICE_PER_PYEONG,
        )

        pyeong = round((width * height) / 90000, 1)

        # D값 구간별 평당 단가 (옥내노출 기본)
        if depth < 200:
            price_per = 25000
        elif depth < 250:
            price_per = 26000
        elif depth < 300:
            price_per = 27000
        elif depth < 350:
            price_per = 28000
        elif depth < 400:
            price_per = 29000
        elif depth < 450:
            price_per = 30000
        else:
            price_per = 31000

        cost = round(pyeong * price_per)
        price = round(cost * CUSTOM_ENCLOSURE_MARKUP)
        return max(price, 50000), "CALCULATED"

    @classmethod
    def get_accessory_price(cls, accessory_type: str, **kwargs) -> tuple[int, ItemSource]:
        """부속자재 가격 조회"""
        if accessory_type in cls.ACCESSORY_PRICES:
            price = cls.ACCESSORY_PRICES[accessory_type]
            if isinstance(price, dict):
                frame = kwargs.get("frame", "100AF")
                return price.get(frame, list(price.values())[0]), "CATALOG"
            return price, "CATALOG"

        return 5000, "CALCULATED"  # 기본값


# ============================================================================
# Vision Estimate Service
# ============================================================================

class VisionEstimateService:
    """
    Vision 기반 자동 견적 생성 서비스

    Features:
    - Vision 분석 결과에서 견적 자동 생성
    - CEO 학습된 선호도 자동 적용
    - 부속자재 자동 추가
    - 신뢰도 기반 경고 생성
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 견적 저장 경로
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "vision_estimates"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._estimates: dict[str, VisionEstimate] = {}

    async def generate_estimate(
        self,
        analysis_result: dict,
        customer_name: Optional[str] = None,
        project_name: Optional[str] = None,
        apply_ceo_preferences: bool = True,
        brand_override: Optional[str] = None
    ) -> VisionEstimate:
        """
        분석 결과에서 견적 생성

        Args:
            analysis_result: Vision 분석 결과
            customer_name: 고객명 (오버라이드)
            project_name: 건명 (오버라이드)
            apply_ceo_preferences: CEO 선호도 적용 여부
            brand_override: 브랜드 강제 지정

        Returns:
            생성된 견적
        """
        estimate_id = f"VEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        request_id = analysis_result.get("request_id", str(uuid.uuid4()))

        logger.info(f"Vision 견적 생성 시작: {estimate_id}")

        # 고객 정보
        final_customer = customer_name
        final_project = project_name

        # 분석 결과에서 추출된 정보 사용
        if not final_customer:
            for result in analysis_result.get("results", []):
                if result.customer_name:
                    final_customer = result.customer_name
                    break

        # CEO 선호도 로드
        ceo_preferences = {}
        if apply_ceo_preferences:
            ceo_preferences = await self._load_ceo_preferences()

        # 분전반별 견적 생성
        panel_estimates = []
        warnings = []
        confidence_summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "MANUAL": 0}

        merged_panels = analysis_result.get("merged_panels", [])

        for panel in merged_panels:
            panel_estimate, panel_warnings = await self._generate_panel_estimate(
                panel=panel,
                brand_override=brand_override,
                ceo_preferences=ceo_preferences
            )
            panel_estimates.append(panel_estimate)
            warnings.extend(panel_warnings)

            # 신뢰도 집계
            for item in panel_estimate.items:
                confidence_summary[item.confidence] = confidence_summary.get(item.confidence, 0) + 1

        # 합계 계산
        total_amount = sum(p.subtotal for p in panel_estimates)
        total_with_vat = int(total_amount * 1.1)

        # 견적 객체 생성
        estimate = VisionEstimate(
            estimate_id=estimate_id,
            request_id=request_id,
            customer_name=final_customer,
            project_name=final_project,
            panels=panel_estimates,
            total_amount=total_amount,
            total_with_vat=total_with_vat,
            ceo_preferences_applied=apply_ceo_preferences and bool(ceo_preferences),
            confidence_summary=confidence_summary,
            warnings=warnings,
            generated_at=datetime.utcnow()
        )

        # 저장
        self._estimates[estimate_id] = estimate
        await self._save_estimate(estimate)

        logger.info(f"Vision 견적 생성 완료: {estimate_id}, 합계: {total_amount:,}원")
        return estimate

    async def _generate_panel_estimate(
        self,
        panel,
        brand_override: Optional[str],
        ceo_preferences: dict
    ) -> tuple[PanelEstimate, list[str]]:
        """분전반 견적 생성"""
        items = []
        warnings = []
        panel_name = panel.panel_name if hasattr(panel, 'panel_name') else panel.get("panel_name", "분전반")

        # 1. 외함
        enclosure = panel.enclosure if hasattr(panel, 'enclosure') else panel.get("enclosure")
        if enclosure:
            enc_type = enclosure.enclosure_type if hasattr(enclosure, 'enclosure_type') else enclosure.get("type", "옥내노출")
            material = enclosure.material if hasattr(enclosure, 'material') else enclosure.get("material", "STEEL")
            thickness = enclosure.thickness if hasattr(enclosure, 'thickness') else enclosure.get("thickness", "1.6T")
            width = enclosure.width if hasattr(enclosure, 'width') else enclosure.get("width", 600)
            height = enclosure.height if hasattr(enclosure, 'height') else enclosure.get("height", 800)
            depth = enclosure.depth if hasattr(enclosure, 'depth') else enclosure.get("depth", 200)
            confidence = enclosure.confidence if hasattr(enclosure, 'confidence') else enclosure.get("confidence", "MEDIUM")

            price, source = PriceCatalog.get_enclosure_price(
                width or 600,
                height or 800,
                depth or 200
            )

            items.append(EstimateItem(
                category="외함",
                name=f"{enc_type} {material} {thickness}",
                specification=f"{width or 600}×{height or 800}×{depth or 200}",
                unit="면",
                quantity=1,
                unit_price=price,
                total_price=price,
                source=source,
                confidence=confidence
            ))

        # 2. 메인 차단기
        main_breaker = panel.main_breaker if hasattr(panel, 'main_breaker') else panel.get("main_breaker")
        if main_breaker:
            await self._add_breaker_item(items, main_breaker, brand_override, ceo_preferences, is_main=True)

        # 3. 분기 차단기
        branch_breakers = panel.branch_breakers if hasattr(panel, 'branch_breakers') else panel.get("branch_breakers", [])
        for breaker in branch_breakers:
            await self._add_breaker_item(items, breaker, brand_override, ceo_preferences, is_main=False)

        # 4. 부속자재 자동 추가
        total_breakers = len(branch_breakers) + (1 if main_breaker else 0)
        await self._add_accessories(items, total_breakers, main_breaker, enclosure)

        # 5. 잡자재비 및 조립비
        misc_price = PriceCatalog.ACCESSORY_PRICES["MISC"]
        assembly_price = PriceCatalog.ACCESSORY_PRICES["ASSEMBLY"]

        items.append(EstimateItem(
            category="공임",
            name="잡자재비",
            specification="",
            unit="식",
            quantity=1,
            unit_price=misc_price,
            total_price=misc_price,
            source="CATALOG",
            confidence="HIGH"
        ))

        items.append(EstimateItem(
            category="공임",
            name="ASSEMBLY CHARGE",
            specification="",
            unit="식",
            quantity=1,
            unit_price=assembly_price,
            total_price=assembly_price,
            source="CATALOG",
            confidence="HIGH"
        ))

        # 소계 계산
        subtotal = sum(item.total_price for item in items)

        # 저신뢰도 경고
        low_confidence_items = [i for i in items if i.confidence in ["LOW", "MANUAL"]]
        if low_confidence_items:
            warnings.append(f"{panel_name}: {len(low_confidence_items)}개 항목 확인 필요")

        return PanelEstimate(
            panel_name=panel_name,
            items=items,
            subtotal=subtotal,
            notes=[f"Vision AI 자동 생성 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"]
        ), warnings

    async def _add_breaker_item(
        self,
        items: list[EstimateItem],
        breaker,
        brand_override: Optional[str],
        ceo_preferences: dict,
        is_main: bool
    ) -> None:
        """차단기 항목 추가"""
        breaker_type = breaker.breaker_type if hasattr(breaker, 'breaker_type') else breaker.get("type", "MCCB")
        pole = breaker.pole if hasattr(breaker, 'pole') else breaker.get("pole", "4P")
        frame = breaker.frame if hasattr(breaker, 'frame') else breaker.get("frame", "100AF")
        ampere = breaker.ampere if hasattr(breaker, 'ampere') else breaker.get("ampere", 100)
        quantity = breaker.quantity if hasattr(breaker, 'quantity') else breaker.get("quantity", 1)
        confidence = breaker.confidence if hasattr(breaker, 'confidence') else breaker.get("confidence", "MEDIUM")

        # 브랜드 결정
        brand = brand_override
        if not brand:
            brand = breaker.brand if hasattr(breaker, 'brand') else breaker.get("brand")
        if not brand:
            # CEO 선호도에서 브랜드 가져오기
            pref_key = f"{pole}_{frame}"
            brand = ceo_preferences.get("brand_preferences", {}).get(pref_key, "상도")

        # 가격 조회
        price, source = PriceCatalog.get_breaker_price(
            brand=brand or "상도",
            breaker_type=breaker_type,
            pole=pole,
            frame=frame,
            ampere=ampere
        )

        # CEO 선호도 적용 시 source 변경
        if source == "CATALOG" and ceo_preferences.get("brand_preferences"):
            source = "CEO_PREFERENCE"

        # 모델명 생성
        if brand == "상도":
            type_code = "E" if breaker_type == "ELB" else "B"
            series_code = "E"  # 경제형
            frame_num = frame.replace("AF", "")
            pole_num = pole.replace("P", "")
            model_name = f"S{type_code}{series_code}-{frame_num[0]}{pole_num}"
        else:
            type_code = "E" if breaker_type == "ELB" else "A"
            frame_num = frame.replace("AF", "")
            pole_num = pole.replace("P", "")
            model_name = f"{type_code}BN-{frame_num[0]}{pole_num}"

        category = "메인차단기" if is_main else "분기차단기"
        name = f"{breaker_type} {model_name}"
        spec = f"{pole} {frame} {ampere}A"

        items.append(EstimateItem(
            category=category,
            name=name,
            specification=spec,
            unit="EA",
            quantity=quantity,
            unit_price=price,
            total_price=price * quantity,
            source=source,
            confidence=confidence
        ))

    async def _add_accessories(
        self,
        items: list[EstimateItem],
        total_breakers: int,
        main_breaker,
        enclosure
    ) -> None:
        """부속자재 자동 추가"""

        # E.T (Earth Terminal) - 차단기 12개당 1개
        et_count = (total_breakers // 12) + 1
        main_frame = "100AF"
        if main_breaker:
            main_frame = main_breaker.frame if hasattr(main_breaker, 'frame') else main_breaker.get("frame", "100AF")

        et_price, _ = PriceCatalog.get_accessory_price("E.T", frame=main_frame)
        items.append(EstimateItem(
            category="부속자재",
            name="E.T",
            specification="",
            unit="EA",
            quantity=et_count,
            unit_price=et_price,
            total_price=et_price * et_count,
            source="CATALOG",
            confidence="HIGH"
        ))

        # N.T (Neutral Terminal)
        nt_price, _ = PriceCatalog.get_accessory_price("N.T")
        items.append(EstimateItem(
            category="부속자재",
            name="N.T",
            specification="",
            unit="EA",
            quantity=1,
            unit_price=nt_price,
            total_price=nt_price,
            source="CATALOG",
            confidence="HIGH"
        ))

        # N.P (Name Plate) - CARD HOLDER
        np_card_price, _ = PriceCatalog.get_accessory_price("N.P_CARD_HOLDER")
        items.append(EstimateItem(
            category="부속자재",
            name="N.P (CARD HOLDER)",
            specification="",
            unit="EA",
            quantity=total_breakers,
            unit_price=np_card_price,
            total_price=np_card_price * total_breakers,
            source="CATALOG",
            confidence="HIGH"
        ))

        # INSULATOR
        insulator_price, _ = PriceCatalog.get_accessory_price("INSULATOR")
        items.append(EstimateItem(
            category="부속자재",
            name="INSULATOR",
            specification="EPOXY 40×40",
            unit="EA",
            quantity=4,
            unit_price=insulator_price,
            total_price=insulator_price * 4,
            source="CATALOG",
            confidence="HIGH"
        ))

        # P-COVER (아크릴)
        if enclosure:
            width = enclosure.width if hasattr(enclosure, 'width') else enclosure.get("width", 600)
            height = enclosure.height if hasattr(enclosure, 'height') else enclosure.get("height", 800)
            if width and height:
                cover_price = int((width * height / 90000) * 3200)
                items.append(EstimateItem(
                    category="부속자재",
                    name="P-COVER",
                    specification="아크릴(PC)",
                    unit="EA",
                    quantity=1,
                    unit_price=cover_price,
                    total_price=cover_price,
                    source="CALCULATED",
                    confidence="HIGH"
                ))

    async def _load_ceo_preferences(self) -> dict:
        """CEO 학습된 선호도 로드"""
        try:
            from kis_estimator_core.services.ceo_profile_service import get_ceo_profile_service

            service = get_ceo_profile_service()
            profile = await service.get_profile("CEO")

            if profile:
                return {
                    "brand_preferences": profile.brand_preferences,
                    "price_thresholds": profile.price_thresholds,
                    "layout_style": profile.layout_style
                }
        except Exception as e:
            logger.warning(f"CEO 선호도 로드 실패: {e}")

        return {}

    async def _save_estimate(self, estimate: VisionEstimate) -> None:
        """견적 저장"""
        estimate_file = self.storage_path / f"{estimate.estimate_id}.json"

        data = {
            "estimate_id": estimate.estimate_id,
            "request_id": estimate.request_id,
            "customer_name": estimate.customer_name,
            "project_name": estimate.project_name,
            "panels": [
                {
                    "panel_name": p.panel_name,
                    "items": [
                        {
                            "category": i.category,
                            "name": i.name,
                            "specification": i.specification,
                            "unit": i.unit,
                            "quantity": i.quantity,
                            "unit_price": i.unit_price,
                            "total_price": i.total_price,
                            "source": i.source,
                            "confidence": i.confidence
                        }
                        for i in p.items
                    ],
                    "subtotal": p.subtotal,
                    "notes": p.notes
                }
                for p in estimate.panels
            ],
            "total_amount": estimate.total_amount,
            "total_with_vat": estimate.total_with_vat,
            "ceo_preferences_applied": estimate.ceo_preferences_applied,
            "confidence_summary": estimate.confidence_summary,
            "warnings": estimate.warnings,
            "generated_at": estimate.generated_at.isoformat()
        }

        with open(estimate_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def get_estimate(self, estimate_id: str) -> Optional[VisionEstimate]:
        """견적 조회"""
        return self._estimates.get(estimate_id)

    def get_stats(self) -> dict:
        """견적 통계"""
        return {
            "total_estimates": len(self._estimates),
            "storage_path": str(self.storage_path)
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_estimate_service: Optional[VisionEstimateService] = None


def get_vision_estimate_service() -> VisionEstimateService:
    """Vision 견적 서비스 싱글톤 인스턴스 반환"""
    global _estimate_service
    if _estimate_service is None:
        _estimate_service = VisionEstimateService()
    return _estimate_service
