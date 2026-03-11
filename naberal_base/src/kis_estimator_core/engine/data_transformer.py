"""
Stage 3: Data Transformer
CriticResult → EstimateData 변환

입력: Stage 2.1 Breaker Critic 출력
출력: EstimateData (Excel 생성용 데이터)

변환 로직:
1. BreakerPlacement → BreakerItem (가격표 매칭)
2. 그룹화: 메인/분기 차단기 분리
3. 부속자재 계산 (estimate_rag_bundle 규칙)
4. 부스바 계산 (중량 기반)
5. 가공비 계산 (AF별 tier)
6. 품목 정렬 (priority_map)

SPEC KIT 기준:
- estimate_rag_bundle_v1.0.0.json 규칙 100% 준수
- 가격표 매칭 (중요ai단가표의_2.0V.csv)
- 실물 견적서 순서 재현
"""

import logging

from kis_estimator_core.core.ssot.constants import (
    # Assembly Charge - CEO 규칙 (2024-12-05 수정) - H값 기반 계산
    # 50~100AF
    ASSEMBLY_BASE_H_50_100AF,
    ASSEMBLY_BASE_PRICE_50_100AF,
    ASSEMBLY_H_INCREMENT_50_100AF,
    ASSEMBLY_SIE_BONUS_50_100AF,
    # 125~250AF
    ASSEMBLY_BASE_H_125_250AF,
    ASSEMBLY_BASE_PRICE_125_250AF,
    ASSEMBLY_H_INCREMENT_125_250AF,
    ASSEMBLY_SIE_BONUS_125_250AF,
    # 400AF
    ASSEMBLY_BASE_H_400AF,
    ASSEMBLY_BASE_PRICE_400AF,
    ASSEMBLY_H_INCREMENT_400AF,
    ASSEMBLY_SIE_BONUS_400AF,
    # 600~800AF
    ASSEMBLY_BASE_H_600_800AF,
    ASSEMBLY_BASE_PRICE_600_800AF,
    ASSEMBLY_H_INCREMENT_600_800AF,
    ASSEMBLY_SIE_BONUS_600_800AF,
    # Assembly Charge - Main Only
    ASSEMBLY_MAIN_ONLY_50_250AF,
    ASSEMBLY_MAIN_ONLY_400AF,
    ASSEMBLY_MAIN_ONLY_600_800AF,
    ASSEMBLY_MAIN_ONLY_BUSBAR_400AF,
    ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF,
    # Calculation Coefficients - Main Busbar
    BUSBAR_COEFF_20_250A,
    BUSBAR_COEFF_300_400A,
    BUSBAR_COEFF_500_800A,
    # Calculation Coefficients - Branch Busbar (분기용)
    BRANCH_BUSBAR_COEFF_20_250A,
    BRANCH_BUSBAR_COEFF_300_400A,
    BRANCH_BUSBAR_COEFF_500_800A,
    BUSBAR_SPEC_3T_15,
    BUSBAR_SPEC_5T_20,
    BUSBAR_SPEC_6T_30,
    BUSBAR_SPEC_8T_40,
    # Custom Enclosure Pricing (주문제작함)
    CUSTOM_ENCLOSURE_MARKUP,
    CUSTOM_ENCLOSURE_PRICE_PER_PYEONG,
    MISC_ACCESSORY_INCREMENT,
    MISC_BASE_PRICE,
    MISC_BUSBAR_OPTION_400_800AF,
    MISC_H_INCREMENT_PER_100MM,
    MISC_MAX_PRICE,
    PCOVER_AREA_DIVISOR,
    PCOVER_MIN_PRICE,
    PCOVER_PRICE_MULTIPLIER,
    PRICE_BUSBAR_PER_KG,
    PRICE_COATING,
    PRICE_ELB_SUPPORT,
    # Accessory Prices
    PRICE_ET_50_125AF,
    PRICE_ET_200_250AF,
    PRICE_ET_400AF,
    PRICE_ET_600_800AF,
    PRICE_INSULATOR_50_250AF,
    PRICE_INSULATOR_400_800AF,
    PRICE_NP_3T_40_200,
    PRICE_NP_CARD_HOLDER,
    PRICE_NP_CARD_HOLDER_MAIN_ONLY,
    PRICE_NT,
    # 고AF 단품 분전반 (400~800AF 차단기 1개, 동관단자 직결)
    SINGLE_BREAKER_ASSEMBLY_400AF,
    SINGLE_BREAKER_ASSEMBLY_600_800AF,
    SINGLE_BREAKER_MISC_PRICE,
    TERMINAL_LUG_WEIGHT_KG,
    # SIE 보너스 적용 조건 (대표님 피드백 2024-12-10)
    SIE_BONUS_MIN_ENCLOSURE_H,
    SIE_BONUS_MIN_ENCLOSURE_W,
    SIE_BONUS_MIN_SMALL_BREAKER_COUNT,
    # Rounding Utility
    apply_rounding,
)
from kis_estimator_core.core.ssot.constants_format import (
    UNIT_ACCESSORY,
    UNIT_ASSEMBLY,
    UNIT_BUSBAR,
    UNIT_COATING,
)
from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

from ..services.catalog_service import get_catalog_service
from ..infra.knowledge_loader import get_knowledge_loader
from .models import (
    AccessoryItem,
    AssemblyItem,
    BreakerItem,
    BusbarItem,
    EnclosureItem,
    EstimateData,
    PanelEstimate,
)

logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Stage 2.1 출력을 견적서 데이터로 변환

    설계 문서: STAGE3_FORMAT_DESIGN_20251003.md
    참조: ESTIMATE_TEMPLATE_ANALYSIS_20251003.md
    """

    def __init__(self):
        """
        실물 Supabase CatalogService 사용 (목업 금지)
        """
        self.catalog_service = get_catalog_service()
        logger.info("DataTransformer initialized with real Supabase CatalogService")

    def transform(
        self,
        placements: list,  # Stage 2 Breaker Placements
        enclosure_result,  # EnclosureResult from Stage 1
        breakers: list,  # Original breaker inputs
        customer_name: str,
        project_name: str = "",
    ) -> EstimateData:
        """
        메인 변환 메서드

        Args:
            placements: Stage 2 Breaker Placer 출력 (List[PlacementResult])
            enclosure_result: Stage 1 Enclosure Solver 출력
            breakers: 원본 차단기 입력 (List[BreakerInput])
            customer_name: 고객명
            project_name: 프로젝트명

        Returns:
            EstimateData: Excel 생성용 데이터
        """
        logger.info(f"Starting data transformation: {len(placements)} placements")

        # breakers를 딕셔너리로 변환 (id → breaker)
        breaker_map = {b.id: b for b in breakers}
        self._breaker_map = breaker_map

        # 1. 차단기 그룹화 (메인/분기 분리)
        main_breakers, branch_breakers = self._group_breakers(placements)

        # 2. 외함 품목 생성
        enclosure_item = self._create_enclosure_item(enclosure_result)

        # 2.1 매입함인 경우 SUSCOVER 자동 추가 (견적조건 9번)
        # CEO 규칙: 매입함은 무조건 같은 사이즈의 SUSCOVER가 따라옴
        suscover_item = None
        enclosure_type = enclosure_result.enclosure_type
        if enclosure_type in ["매입함", "embedded", "EMBEDDED"]:
            dimensions = enclosure_result.dimensions
            suscover_item = self._create_suscover_item(dimensions)
            logger.info(f"[매입함] SUSCOVER 자동 추가: {suscover_item.item_name}")

        # 3. 차단기 품목 생성
        main_breaker_item = (
            self._create_breaker_item(main_breakers[0], is_main=True)
            if main_breakers
            else None
        )

        # 분기 차단기 그룹화: 동일한 (model, poles, current_a)별로 수량 합산
        branch_breaker_items = self._group_branch_breakers(branch_breakers)

        # 메인차단기만 있는지 확인
        is_main_only = len(branch_breaker_items) == 0

        # 고AF 단품 분전반 감지 (400AF 이상 메인차단기 1개만, 분기 없음)
        is_single_high_af = False
        if is_main_only and main_breaker_item:
            main_af = getattr(main_breaker_item, "frame_af", 0)
            if main_af >= 400:
                is_single_high_af = True
                logger.info(f"[고AF 단품] 감지: {main_af}AF 단품 분전반 — 동관단자 직결 모드")

        assembly_charge: AssemblyItem | None = None
        if is_single_high_af and main_breaker_item:
            # ===== 고AF 단품 분전반 전용 로직 =====
            # 자재: 외함 + 차단기 + 동관단자 + N.P(3T×40×200) + 잡자재비 + ASSEMBLY
            # E.T, P-COVER, COATING, INSULATOR, BUS-BAR 등 불포함
            accessories = self._calculate_single_high_af_accessories(main_breaker_item)
            main_busbar = None

            # 잡자재비 (28,300원 고정)
            accessories.append(
                AccessoryItem(
                    item_name="잡자재비",
                    spec="",
                    unit=UNIT_ASSEMBLY,
                    quantity=1,
                    unit_price=SINGLE_BREAKER_MISC_PRICE,
                    accessory_type="잡자재비",
                )
            )

            # ASSEMBLY CHARGE (400AF=70,000원, 600~800AF=100,000원)
            if main_af == 400:
                assembly_price = SINGLE_BREAKER_ASSEMBLY_400AF
            else:  # 600~800AF
                assembly_price = SINGLE_BREAKER_ASSEMBLY_600_800AF

            assembly_charge = AssemblyItem(
                item_name="ASSEMBLY CHARGE",
                spec="조립비",
                unit=UNIT_ASSEMBLY,
                quantity=1,
                unit_price=assembly_price,
                assembly_type="ASSEMBLY CHARGE",
            )
        else:
            # ===== 일반 견적 로직 (기존) =====
            # 4. 부속자재 계산 (견적조건 7번)
            accessories = self._calculate_accessories(
                enclosure_result, main_breaker_item, branch_breaker_items
            )

            # 4.1 매입함 SUSCOVER 추가 (accessories 맨 앞에)
            if suscover_item:
                accessories.insert(0, suscover_item)

            # 5. MAIN BUS-BAR 계산
            # CEO 규칙 (2024-12-03): 분기차단기 없으면 부스바도 없음
            if is_main_only:
                main_busbar = None
                has_busbar_option = False
            else:
                main_busbar = self._calculate_busbar(enclosure_result, main_breaker_item)
                has_busbar_option = False

            # 6. BUS-BAR (분기용) 계산 (accessories에 추가) - 일반 견적만
            if not is_main_only:
                branch_busbar = self._calculate_branch_busbar(
                    enclosure_result, branch_breaker_items
                )
                if branch_busbar:
                    # BusbarItem을 AccessoryItem으로 변환해서 accessories에 추가
                    branch_busbar_accessory = AccessoryItem(
                        item_name=branch_busbar.item_name,
                        spec=branch_busbar.spec,
                        unit=branch_busbar.unit,
                        quantity=branch_busbar.quantity,
                        unit_price=branch_busbar.unit_price,
                        accessory_type="BUS-BAR",
                    )
                    accessories.insert(len(accessories), branch_busbar_accessory)

            # 7. 잡자재비 계산
            # TODO[KIS-007]: 특수 부속자재(마그네트, 타이머) 입력 처리 시 카운트 추가
            special_accessories_count = 0
            misc_materials = self._calculate_misc_materials(
                enclosure_result,
                special_accessories_count,
                main_breaker=main_breaker_item,
                is_main_only=is_main_only,
                has_busbar_option=has_busbar_option if not is_main_only else False,
            )
            if misc_materials:
                accessories.append(misc_materials)

            # 8. 가공비 계산 (enclosure_result 전달)
            assembly_charge = self._calculate_assembly_charge(
                enclosure_result,
                main_breaker_item,
                branch_breakers=branch_breaker_items,
                is_main_only=is_main_only,
                has_busbar_option=has_busbar_option if not is_main_only else False,
            )

        # 9. PanelEstimate 구성
        panel = PanelEstimate(
            panel_id=f"LP-{len(placements)}",  # 실제 배치 수량 기반 ID
            quantity=1,
            enclosure=enclosure_item,
            main_breaker=main_breaker_item,
            branch_breakers=branch_breaker_items,
            accessories=accessories,
            busbar=main_busbar,  # MAIN BUS-BAR (singular, PanelEstimate.busbar)
            assembly_charge=assembly_charge,
        )

        # 8. EstimateData 구성
        estimate_data = EstimateData(
            customer_name=customer_name,
            project_name=project_name,
            panels=[panel],
        )

        logger.info(
            f"Data transformation completed: {len(estimate_data.panels)} panels, "
            f"{len(panel.all_items_sorted)} total items"
        )
        return estimate_data

    def _group_breakers(self, placements: list) -> tuple:
        """
        차단기 그룹화: 메인/분기 분리

        기준: position["row"] == 0 → 메인 차단기
        지원 형식: dict 또는 PlacementResult 객체
        """
        main_breakers = []
        branch_breakers = []

        for placement in placements:
            # dict 또는 객체 모두 지원
            if isinstance(placement, dict):
                position = placement.get("position", {})
            else:
                position = getattr(placement, "position", {})

            row = position.get("row", -1)

            if row == 0:
                main_breakers.append(placement)
            else:
                branch_breakers.append(placement)

        logger.debug(
            f"Grouped breakers: {len(main_breakers)} main, {len(branch_breakers)} branch"
        )
        return main_breakers, branch_breakers

    def _get_placement_attr(self, placement, attr: str, default=None):
        """placement에서 속성값 가져오기 (dict/object 모두 지원)"""
        if isinstance(placement, dict):
            return placement.get(attr, default)
        return getattr(placement, attr, default)

    def _group_branch_breakers(self, branch_placements: list) -> list[BreakerItem]:
        """
        동일한 분기 차단기 그룹화

        동일한 (model, poles, current_a)를 가진 차단기를 그룹화하여
        수량을 합산한 BreakerItem 목록 반환

        예: SIB-32 2P 20A가 3개면 → quantity=3인 BreakerItem 1개
        """
        from collections import defaultdict

        # (model, poles, current_a) → 개수 카운트
        grouped = defaultdict(list)

        for placement in branch_placements:
            # placement에서 키 생성 (dict/object 모두 지원)
            model = self._get_placement_attr(placement, "model", "")
            poles = self._get_placement_attr(placement, "poles", 4)
            current_a = self._get_placement_attr(placement, "current_a", 60)

            # original_breaker에서도 확인 (fallback)
            breaker_id = self._get_placement_attr(placement, "breaker_id", None)
            original_breaker = self._breaker_map.get(breaker_id) if breaker_id else None

            if not model and original_breaker:
                model = getattr(original_breaker, "model", "")
            if poles == 4 and original_breaker:  # 기본값이면 original에서 가져옴
                poles = getattr(original_breaker, "poles", poles)
            if current_a == 60 and original_breaker:  # 기본값이면 original에서 가져옴
                current_a = getattr(original_breaker, "current_a", current_a)

            key = (model, poles, current_a)
            grouped[key].append(placement)

        # 그룹별로 BreakerItem 생성 (수량 합산)
        # FIX: workflow_engine에서 차단기를 quantity만큼 펼쳐서 배치하므로
        # len(placements)가 실제 수량임 (각 placement는 개별 차단기)
        result = []
        for (model, poles, current_a), placements in grouped.items():
            # 펼쳐진 placement 개수 = 실제 수량
            quantity = len(placements)

            # 첫 번째 placement로 BreakerItem 생성
            first_placement = placements[0]

            # 실제 BreakerItem 생성 (quantity 포함)
            breaker_item = self._create_breaker_item_with_quantity(
                first_placement, quantity=quantity
            )
            result.append(breaker_item)

        logger.debug(f"Grouped {len(branch_placements)} placements into {len(result)} breaker items")
        return result

    def _create_breaker_item_with_quantity(self, placement, quantity: int) -> BreakerItem:
        """
        수량을 지정하여 차단기 품목 생성

        _create_breaker_item과 동일하지만 quantity 파라미터 지원
        dict/object 모두 지원
        """
        # placement.breaker_id로 원본 breaker 정보 조회
        breaker_id = self._get_placement_attr(placement, "breaker_id", None)
        original_breaker = self._breaker_map.get(breaker_id) if breaker_id else None

        # model 정보 (placement > original_breaker > 기본값)
        model = self._get_placement_attr(placement, "model", "")
        if not model and original_breaker and hasattr(original_breaker, "model"):
            model = original_breaker.model
        if not model:
            model = "AUTO"  # 자동 선택

        poles = self._get_placement_attr(placement, "poles", 4)
        current_a = self._get_placement_attr(placement, "current_a", 60.0)

        # original_breaker에서 값 보정 (placement 값이 기본값인 경우)
        if original_breaker:
            if poles == 4:
                poles = getattr(original_breaker, "poles", poles)
            if current_a == 60.0:
                current_a = getattr(original_breaker, "current_a", current_a)

        # 차단기 유형 판정 (ELB vs MCCB) - 모델 분석으로 정확히 판정
        # SIE-32, SEE-*, 32GRHS, EB*, = ELB
        # SIB-32, SBS-*, SBE-*, AB*, BS-32 = MCCB
        is_elb_model = False
        model_upper = model.upper() if model else ""
        if model_upper.startswith("SIE") or model_upper.startswith("SEE"):
            is_elb_model = True
        elif model_upper.startswith("EB") or "GRHS" in model_upper:
            is_elb_model = True
        elif model_upper.startswith("SE") and "SEB" not in model_upper and len(model_upper) > 2:
            # SE로 시작하지만 SEB는 MCCB
            is_elb_model = True

        breaker_type = "ELB" if is_elb_model else "MCCB"

        # placement에서 is_elb 정보 확인 (우선순위 높음)
        placement_is_elb = self._get_placement_attr(placement, "is_elb", None)
        if placement_is_elb is not None:
            breaker_type = "ELB" if placement_is_elb else "MCCB"

        # FIX: knowledge_loader에서 차단기 조회 (catalog_service와 데이터 소스 일관성)
        # Supabase 캐시 대신 ai_estimation_core.json 사용
        loader = get_knowledge_loader()
        ai_core = loader.get_ai_core()
        breakers_raw = ai_core.get("catalog", {}).get("breakers", {}).get("items", [])

        # DEBUG: Railway 배포 확인용 로그
        logger.info(f"[DATA_TRANSFORMER] Searching breaker: model={model}, poles={poles}, current_a={current_a}, breaker_type={breaker_type}")
        logger.info(f"[DATA_TRANSFORMER] Total breakers in knowledge: {len(breakers_raw)}")

        catalog_item = None

        # 1. 먼저 모델명으로 검색 시도 (AUTO가 아닌 경우)
        if model and model != "AUTO":
            model_upper = model.upper().replace("-", "").replace(" ", "")
            for item in breakers_raw:
                item_model = item.get("model", "").upper().replace("-", "").replace(" ", "")
                item_poles = item.get("poles", 0)
                item_ampere = item.get("ampere", [])
                if isinstance(item_ampere, int):
                    item_ampere = [item_ampere]

                if item_model == model_upper and item_poles == poles and int(current_a) in item_ampere:
                    catalog_item = item
                    break

        # 2. 모델명 검색 실패 시 또는 AUTO인 경우, breaker_type으로 검색
        if not catalog_item:
            candidates = []
            for item in breakers_raw:
                item_category = item.get("category", "")
                item_poles = item.get("poles", 0)
                item_ampere = item.get("ampere", [])
                item_frame = item.get("frame_AF", 0)
                if isinstance(item_ampere, int):
                    item_ampere = [item_ampere]

                # FIX (2026-02-06): 프레임 >= 암페어 조건 추가 (전기 안전 규칙)
                # 분기 차단기도 동일하게 적용
                if (item_category == breaker_type and
                    item_poles == poles and
                    int(current_a) in item_ampere and
                    item_frame >= int(current_a)):
                    candidates.append(item)

            # 경제형 우선
            if candidates:
                economy = [c for c in candidates if "economy" in (c.get("type", "") or "").lower()]
                if economy:
                    catalog_item = economy[0]
                else:
                    catalog_item = candidates[0]

        if not catalog_item:
            # DEBUG: 검색 실패 시 상세 로그
            logger.error(f"[DATA_TRANSFORMER] FAILED to find: {breaker_type} {poles}P {current_a}A")
            # 4P MCCB 목록 출력
            mccb_4p = [i for i in breakers_raw if i.get("poles") == 4 and i.get("category") == "MCCB"]
            logger.error(f"[DATA_TRANSFORMER] Available 4P MCCB: {[(i.get('model'), i.get('ampere')) for i in mccb_4p[:5]]}")
            raise_error(
                ErrorCode.E_DATA_TRANSFORM,
                f"카탈로그에 없는 차단기: {breaker_type} {poles}P {current_a}A (목업 금지!)",
            )

        # 카탈로그에서 찾은 모델명과 용량 사용 (BUG-003 수정)
        model = catalog_item.get("model", model)
        # 카탈로그 결과에서 breaker_type도 업데이트
        if catalog_item.get("category"):
            breaker_type = "ELB" if "ELB" in str(catalog_item.get("category")).upper() else "MCCB"
        # FIX: JSON 키가 "capacity_kA" (대문자 A)임
        breaking_capacity = catalog_item.get("capacity_kA", catalog_item.get("capacity_ka", 14.0))
        spec = f"{poles}P {int(current_a)}AT {breaking_capacity}kA"

        # 가격 추출 (price가 리스트인 경우 첫 번째 값)
        price_val = catalog_item.get("price", 0)
        if isinstance(price_val, list):
            # ampere 인덱스에 맞는 가격 찾기
            item_ampere = catalog_item.get("ampere", [])
            if isinstance(item_ampere, list) and int(current_a) in item_ampere:
                price_idx = item_ampere.index(int(current_a))
                unit_price = price_val[price_idx] if price_idx < len(price_val) else price_val[0]
            else:
                unit_price = price_val[0] if price_val else 0
        else:
            unit_price = price_val

        # 카탈로그에서 frame_af 추출 (BUG-004 수정: 분기 BUS-BAR 계산용)
        frame_af = catalog_item.get("frame_AF", 0)
        if frame_af == 0:
            # frame_af가 없으면 current_a에서 계산
            if current_a <= 50:
                frame_af = 50
            elif current_a <= 100:
                frame_af = 100
            elif current_a <= 125:
                frame_af = 125
            elif current_a <= 250:
                frame_af = 250
            elif current_a <= 400:
                frame_af = 400
            elif current_a <= 600:
                frame_af = 600
            else:
                frame_af = 800

        return BreakerItem(
            item_name=model,  # BUG-003 수정: 모델명 표시 (SIB-32)
            spec=spec,
            unit=UNIT_ACCESSORY,
            quantity=quantity,  # 그룹화된 수량 사용
            unit_price=unit_price,
            breaker_type=breaker_type,
            model=model,
            is_main=False,
            poles=poles,
            current_a=current_a,
            breaking_capacity_ka=breaking_capacity,
            frame_af=frame_af,  # BUG-004 수정: frame_af 전달
        )

    # 외함 타입별 기본 시리즈 매핑 (2_enclosures.json 기반)
    ENCLOSURE_SERIES_MAP = {
        "옥내노출": "HDS",
        "옥외노출": "HT",
        "옥내자립": "HDS",
        "옥외자립": "HT",
        "전주부착형": "HT",
        "FRP함": "FRP",
        "하이박스": "HB",
        "매입함": "HDS",
    }

    def _create_enclosure_item(self, enclosure_result) -> EnclosureItem:
        """
        외함 품목 생성

        Stage 1 출력 → EnclosureItem
        """
        # Stage 1 출력 구조 (가정):
        # enclosure_result.enclosure_sku: "HDS-700*1450*200-옥외자립-STEEL1.6T"
        # enclosure_result.dimensions: {"W": 700, "H": 1450, "D": 200}

        dimensions = getattr(enclosure_result, "dimensions", None)
        if dimensions is None:
            raise_error(
                ErrorCode.E_DATA_TRANSFORM,
                "enclosure_result.dimensions가 없습니다 (목업 금지)",
            )

        # EnclosureResult.enclosure_type, material은 필수 필드 (default 제거됨)
        enclosure_type = enclosure_result.enclosure_type
        material = enclosure_result.material

        # EnclosureDimensions는 pydantic 모델이므로 속성 접근
        dimensions_whd = (
            f"{dimensions.width_mm}*{dimensions.height_mm}*{dimensions.depth_mm}"
        )

        # HDS 모델명 생성 (예: "HDS-600*700*150")
        series_prefix = self.ENCLOSURE_SERIES_MAP.get(enclosure_type, "HDS")
        model_name = f"{series_prefix}-{dimensions_whd}"

        # 실물 Supabase 카탈로그에서 가격 조회 (재질 포함 엄격 검색)
        catalog_item = self.catalog_service.find_enclosure_strict(
            install_location=enclosure_type,
            material=material,
            width=dimensions.width_mm,
            height=dimensions.height_mm,
            depth=dimensions.depth_mm,
        )

        if not catalog_item:
            # 주문제작함 처리 — 대표님 공식 (절대코어파일/주문제작외함계산식.txt)
            # 평수 = (W × H) / 90,000 → 소수 1자리 반올림
            # 원가 = 평수 × 평당단가(D구간별)
            # 최종가격 = 원가 × 1.3
            w = dimensions.width_mm
            h = dimensions.height_mm
            d = dimensions.depth_mm
            pyeong = apply_rounding((w * h) / 90000, decimal_places=1)

            # 외함 타입 → 단가표 키 매핑
            price_key = None
            if enclosure_type in ["옥외노출", "옥외자립", "전주부착형"]:
                price_key = "옥외방수"
            elif enclosure_type in ["옥내노출", "옥내자립"]:
                price_key = "옥내노출"
            elif enclosure_type in ["매입함", "embedded", "EMBEDDED"]:
                price_key = "매입"

            per_pyeong_price = 25000  # 기본값 (옥내노출 D80-200)
            if price_key and price_key in CUSTOM_ENCLOSURE_PRICE_PER_PYEONG:
                d_ranges = CUSTOM_ENCLOSURE_PRICE_PER_PYEONG[price_key]
                # D값 구간별 평당단가 탐색
                if d <= 200:
                    per_pyeong_price = d_ranges.get("D80-200", 25000)
                elif d <= 250:
                    per_pyeong_price = d_ranges.get("D200-250", 26000)
                elif d <= 300:
                    per_pyeong_price = d_ranges.get("D250-300", 27000)
                elif d <= 350:
                    per_pyeong_price = d_ranges.get("D300-350", 28000)
                elif d <= 400:
                    per_pyeong_price = d_ranges.get("D350-400", 29000)
                elif d <= 450:
                    per_pyeong_price = d_ranges.get("D400-450", 30000)
                else:
                    per_pyeong_price = d_ranges.get("D450-500", 31000)

            raw_price = pyeong * per_pyeong_price
            unit_price = int(raw_price * CUSTOM_ENCLOSURE_MARKUP)
            logger.warning(
                f"주문제작함: {model_name} ({enclosure_type}), "
                f"평수={pyeong}, 평당={per_pyeong_price:,}원, "
                f"원가={raw_price:,.0f}원 × {CUSTOM_ENCLOSURE_MARKUP} = {unit_price:,}원"
            )
        else:
            unit_price = catalog_item.unit_price
            logger.info(
                f"기성함 매칭: {catalog_item.name} (요청: {model_name}, "
                f"실제: {catalog_item.size_mm[0]}x{catalog_item.size_mm[1]}x{catalog_item.size_mm[2]})"
            )

        return EnclosureItem(
            item_name=model_name,
            spec=f"{enclosure_type} {material}",
            unit=UNIT_ACCESSORY,
            quantity=1,
            unit_price=unit_price,
            enclosure_type=enclosure_type,
            material=material,
            dimensions_whd=dimensions_whd,
        )

    def _create_suscover_item(self, dimensions) -> AccessoryItem:
        """
        SUSCOVER 품목 생성 (매입함 전용)

        CEO 규칙 (견적조건 9번):
        - 매입함은 무조건 같은 사이즈의 SUSCOVER가 따라옴
        - 단위: 면
        - 수량: 1
        - 단가: SUS201 1.2T 외함 기준 (일반 외함과 동일)
        """
        dimensions_whd = (
            f"{dimensions.width_mm}*{dimensions.height_mm}*{dimensions.depth_mm}"
        )

        # SUSCOVER 가격 계산 (SUS201 1.2T 기준)
        # 간단 공식: W*H*D / 1000 * 2.0원/cm³ (SUS는 STEEL보다 비쌈)
        volume_cm3 = (
            dimensions.width_mm * dimensions.height_mm * dimensions.depth_mm
        ) / 1000
        unit_price = int(volume_cm3 * 2.0)

        logger.info(f"[SUSCOVER] {dimensions_whd} → {unit_price:,}원")

        return AccessoryItem(
            item_name="SUSCOVER",
            spec=f"SUS201 1.2T {dimensions_whd}",
            unit=UNIT_ACCESSORY,  # "면"
            quantity=1,
            unit_price=unit_price,
            accessory_type="SUSCOVER",
        )

    def _create_breaker_item(self, placement, is_main: bool) -> BreakerItem:
        """
        차단기 품목 생성 (메인 차단기용)

        BreakerPlacement → BreakerItem
        dict/object 모두 지원

        FIX (2026-02-06): catalog_service 대신 knowledge_loader 사용
        - 데이터 소스 통일 (ai_estimation_core.json)
        - 분기 차단기와 동일한 검색 로직 적용
        """
        # placement.breaker_id로 원본 breaker 정보 조회
        breaker_id = self._get_placement_attr(placement, "breaker_id", None)
        original_breaker = self._breaker_map.get(breaker_id) if breaker_id else None

        # model 정보 (placement > original_breaker > 기본값)
        model = self._get_placement_attr(placement, "model", "")
        if not model and original_breaker and hasattr(original_breaker, "model"):
            model = original_breaker.model
        if not model:
            model = "AUTO"  # 자동 선택

        poles = self._get_placement_attr(placement, "poles", 4)
        current_a = self._get_placement_attr(placement, "current_a", 60.0)

        # 차단기 유형 판정 (ELB vs MCCB) - 모델 분석으로 정확히 판정
        is_elb_model = False
        model_upper = model.upper() if model else ""
        if model_upper.startswith("SIE") or model_upper.startswith("SEE"):
            is_elb_model = True
        elif model_upper.startswith("EB") or "GRHS" in model_upper:
            is_elb_model = True
        elif model_upper.startswith("SE") and "SEB" not in model_upper and len(model_upper) > 2:
            is_elb_model = True

        breaker_type = "ELB" if is_elb_model else "MCCB"

        # placement에서 is_elb 정보 확인 (우선순위 높음)
        placement_is_elb = self._get_placement_attr(placement, "is_elb", None)
        if placement_is_elb is not None:
            breaker_type = "ELB" if placement_is_elb else "MCCB"

        # FIX: knowledge_loader에서 차단기 조회 (데이터 소스 통일)
        # catalog_service 대신 ai_estimation_core.json 직접 사용
        loader = get_knowledge_loader()
        ai_core = loader.get_ai_core()
        breakers_raw = ai_core.get("catalog", {}).get("breakers", {}).get("items", [])

        # DEBUG: Railway 배포 확인용 로그
        logger.info(f"[MAIN_BREAKER] Searching: model={model}, poles={poles}, current_a={current_a}, type={breaker_type}")
        logger.info(f"[MAIN_BREAKER] Total breakers in knowledge: {len(breakers_raw)}")

        catalog_item = None

        # 1. 먼저 모델명으로 검색 시도 (AUTO가 아닌 경우)
        if model and model != "AUTO":
            model_search = model.upper().replace("-", "").replace(" ", "")
            for item in breakers_raw:
                item_model = item.get("model", "").upper().replace("-", "").replace(" ", "")
                item_poles = item.get("poles", 0)
                item_ampere = item.get("ampere", [])
                item_frame = item.get("frame_AF", 0)
                if isinstance(item_ampere, int):
                    item_ampere = [item_ampere]

                # FIX (2026-02-06 v3): 모델명 검색에도 프레임 >= 암페어 조건 추가
                if (item_model == model_search and
                    item_poles == poles and
                    int(current_a) in item_ampere and
                    item_frame >= int(current_a)):
                    catalog_item = item
                    logger.info(f"[MAIN_BREAKER] Found by model: {item.get('model')} frame={item_frame}AF {item_poles}P")
                    break
                elif item_model == model_search and item_poles == poles and int(current_a) in item_ampere:
                    logger.warning(f"[MAIN_BREAKER] Model {item.get('model')} skipped: frame={item_frame}AF < {current_a}A")

        # 2. 모델명 검색 실패 시 또는 AUTO인 경우, breaker_type으로 검색
        if not catalog_item:
            candidates = []
            for item in breakers_raw:
                item_category = item.get("category", "")
                item_poles = item.get("poles", 0)
                item_ampere = item.get("ampere", [])
                item_frame = item.get("frame_AF", 0)
                if isinstance(item_ampere, int):
                    item_ampere = [item_ampere]

                # FIX (2026-02-06 v2): 프레임 >= 암페어 조건 추가 (전기 안전 규칙)
                # 250A 요청 시 200AF 선택되는 버그 수정
                frame_check = item_frame >= int(current_a)
                if (item_category == breaker_type and
                    item_poles == poles and
                    int(current_a) in item_ampere and
                    frame_check):
                    candidates.append(item)
                    logger.info(f"[MAIN_FIX_V2] Candidate: {item.get('model')} frame={item_frame}AF >= {current_a}A ✓")
                elif item_category == breaker_type and item_poles == poles and int(current_a) in item_ampere:
                    logger.warning(f"[MAIN_FIX_V2] SKIPPED: {item.get('model')} frame={item_frame}AF < {current_a}A ✗")

            # 경제형 우선
            if candidates:
                economy = [c for c in candidates if "economy" in (c.get("type", "") or "").lower()]
                if economy:
                    catalog_item = economy[0]
                else:
                    catalog_item = candidates[0]
                logger.info(f"[MAIN_BREAKER] Found by type: {catalog_item.get('model')} frame={catalog_item.get('frame_AF')}AF (candidates: {len(candidates)})")

        if not catalog_item:
            # DEBUG: 검색 실패 시 상세 로그
            logger.error(f"[MAIN_BREAKER] FAILED to find: {model} {breaker_type} {poles}P {current_a}A")
            mccb_samples = [i for i in breakers_raw if i.get("category") == "MCCB"][:5]
            logger.error(f"[MAIN_BREAKER] Sample MCCB: {[(i.get('model'), i.get('poles'), i.get('ampere')) for i in mccb_samples]}")
            raise_error(
                ErrorCode.E_DATA_TRANSFORM,
                f"카탈로그에 없는 차단기: {model} {poles}P {current_a}A (목업 금지!)",
            )

        # 카탈로그에서 찾은 모델명과 용량 사용
        model = catalog_item.get("model", model)
        if catalog_item.get("category"):
            breaker_type = "ELB" if "ELB" in str(catalog_item.get("category")).upper() else "MCCB"
        # FIX: JSON 키가 "capacity_kA" (대문자 A)임
        breaking_capacity = catalog_item.get("capacity_kA", catalog_item.get("capacity_ka", 14.0))
        spec = f"{poles}P {int(current_a)}AT {breaking_capacity}kA"

        # 가격 추출 (price가 리스트인 경우 ampere 인덱스에 맞는 가격)
        price_val = catalog_item.get("price", 0)
        if isinstance(price_val, list):
            item_ampere = catalog_item.get("ampere", [])
            if isinstance(item_ampere, list) and int(current_a) in item_ampere:
                price_idx = item_ampere.index(int(current_a))
                unit_price = price_val[price_idx] if price_idx < len(price_val) else price_val[0]
            else:
                unit_price = price_val[0] if price_val else 0
        else:
            unit_price = price_val

        # frame_af 추출
        frame_af = catalog_item.get("frame_AF", 0)
        if frame_af == 0:
            if current_a <= 50:
                frame_af = 50
            elif current_a <= 100:
                frame_af = 100
            elif current_a <= 125:
                frame_af = 125
            elif current_a <= 250:
                frame_af = 250
            elif current_a <= 400:
                frame_af = 400
            elif current_a <= 600:
                frame_af = 600
            else:
                frame_af = 800

        return BreakerItem(
            item_name=model,
            spec=spec,
            unit=UNIT_ACCESSORY,
            quantity=1,
            unit_price=unit_price,
            breaker_type=breaker_type,
            model=model,
            is_main=is_main,
            poles=poles,
            current_a=current_a,
            breaking_capacity_ka=breaking_capacity,
            frame_af=frame_af,
        )

    def _calculate_single_high_af_accessories(
        self, main_breaker: BreakerItem
    ) -> list[AccessoryItem]:
        """
        고AF 단품 분전반 부속자재 (400~800AF 차단기 1개, 분기 없음)

        대표님 규칙 (2026-03-09):
        - 동관단자: 극수 × 2(상하) × 개당 450g, 단위=KG, 단가=부스바 단가
        - N.P (3T×40×200): 1개
        - E.T, N.T, P-COVER, COATING, INSULATOR, BUS-BAR 등 불포함
        """
        accessories: list[AccessoryItem] = []
        poles = getattr(main_breaker, "poles", 4)

        # 동관단자: 수량 = 극수 × 2(상하) × 개당무게(kg)
        lug_count = poles * 2
        total_kg = apply_rounding(
            lug_count * TERMINAL_LUG_WEIGHT_KG, decimal_places=1
        )

        accessories.append(
            AccessoryItem(
                item_name="동관단자",
                spec="2HOLE 150SQ",
                unit="KG",
                quantity=total_kg,
                unit_price=PRICE_BUSBAR_PER_KG,
                accessory_type="동관단자",
            )
        )

        # N.P (3T×40×200)
        accessories.append(
            AccessoryItem(
                item_name="N.P",
                spec="3T*40*200",
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=PRICE_NP_3T_40_200,
                accessory_type="N.P",
            )
        )

        logger.info(
            f"[고AF 단품] 동관단자: {poles}P × 2 × {TERMINAL_LUG_WEIGHT_KG}kg = {total_kg}KG, "
            f"N.P: 1EA"
        )
        return accessories

    def _calculate_accessories(
        self,
        enclosure_result,
        main_breaker: BreakerItem | None,
        branch_breakers: list[BreakerItem],
    ) -> list[AccessoryItem]:
        """
        부속자재 계산 (견적조건 7번 - 반드시 따라오는 자재)

        메인차단기만 있는 경우 (분기 없음):
        - 외함 + 메인차단기 + E.T + N.P + 잡자재비 + ASSEMBLY CHARGE
        - ASSEMBLY CHARGE 디폴트: 50~250AF=15,000원, 400AF=20,000원, 600~800AF=30,000원
        - 400~800AF 부스바 처리 옵션: BUS-BAR 추가 시 인건비/잡자재비 증가

        일반 견적 (분기 있음) - 견적조건 7번 필수 자재 순서:
        1. E.T
        2. N.T
        3. N.P (CARD HOLDER)
        4. N.P (3T*40*200)
        5. MAIN BUS-BAR (별도 함수)
        6. BUS-BAR (별도 함수)
        7. COATING
        8. P-COVER
        9. 차단기지지대 (400AF 이상만)
        10. ELB지지대
        11. INSULATOR
        12. 잡자재비 (별도 함수)
        13. ASSEMBLY CHARGE (별도 함수)
        """
        accessories: list[AccessoryItem] = []

        if not main_breaker:
            return accessories

        # 메인차단기만 있는 경우 감지
        is_main_only = len(branch_breakers) == 0

        # 차단기 총수량 (메인 + 분기) - BUG FIX: 각 BreakerItem의 quantity 합산
        # branch_breakers는 그룹화된 BreakerItem 리스트 (각각 quantity 속성 보유)
        branch_count = sum(getattr(b, "quantity", 1) for b in branch_breakers)
        total_breaker_count = 1 + branch_count  # 메인(1) + 분기 총수량

        # 메인 차단기 AF
        main_af = getattr(main_breaker, "frame_af", 100)

        # 외함 치수
        dimensions = getattr(enclosure_result, "dimensions", None)
        if dimensions is None:
            raise_error(
                ErrorCode.E_DATA_TRANSFORM,
                "enclosure_result.dimensions가 없습니다 (목업 금지)",
            )
        w = dimensions.width_mm
        h = dimensions.height_mm

        # ===== 메인차단기만 있는 경우 간소화 로직 =====
        if is_main_only:
            # E.T (항상 1개)
            if main_af <= 125:
                et_price = PRICE_ET_50_125AF
            elif main_af <= 250:
                et_price = PRICE_ET_200_250AF
            elif main_af == 400:
                et_price = PRICE_ET_400AF
            else:  # 600~800AF
                et_price = PRICE_ET_600_800AF

            accessories.append(
                AccessoryItem(
                    item_name="E.T",
                    spec="",
                    unit=UNIT_ACCESSORY,
                    quantity=1,
                    unit_price=et_price,
                    accessory_type="E.T",
                )
            )

            # N.P (CARD HOLDER) - 1개
            accessories.append(
                AccessoryItem(
                    item_name="N.P",
                    spec="CARD HOLDER",
                    unit=UNIT_ACCESSORY,
                    quantity=1,
                    unit_price=PRICE_NP_CARD_HOLDER_MAIN_ONLY,
                    accessory_type="N.P",
                )
            )

            # 메인차단기만 있는 경우 여기서 종료 (잡자재비, ASSEMBLY CHARGE는 별도 함수)
            return accessories

        # ===== 일반 견적 (분기 있음) =====
        # 1. E.T (Earth Terminal)
        # 수량 공식 (실측 보정 - CLAUDE_KNOWLEDGE 14.2):
        # 400AF+ 대형반: 차단기 수 × 0.7 (넉넉히 산정)
        # 200~250AF: 기존 구간 공식
        # ≤125AF 소형 2P 다수: 차단기 수 ÷ 6
        if main_af >= 400:
            # 400AF 대형반: 약 70% 비율 (실측: 14개→10EA)
            et_quantity = max(1, round(total_breaker_count * 0.7))
        elif main_af >= 200:
            # 200~250AF: 기존 구간 공식 유지
            if total_breaker_count < 12:
                et_quantity = 1
            elif total_breaker_count < 23:
                et_quantity = 2
            elif total_breaker_count < 36:
                et_quantity = 3
            elif total_breaker_count < 48:
                et_quantity = 4
            else:
                et_quantity = (total_breaker_count // 12) + 1
        else:
            # ≤125AF 소형: 차단기 수 ÷ 6 (실측 기반)
            et_quantity = max(1, total_breaker_count // 6)

        # 단가: 메인차단기 AF별 (견적요령.txt)
        if main_af <= 125:
            et_price = PRICE_ET_50_125AF
        elif main_af <= 250:
            et_price = PRICE_ET_200_250AF  # 200~250AF
        elif main_af == 400:
            et_price = PRICE_ET_400AF
        else:  # 600~800AF
            et_price = PRICE_ET_600_800AF

        accessories.append(
            AccessoryItem(
                item_name="E.T",
                spec="",
                unit=UNIT_ACCESSORY,
                quantity=et_quantity,
                unit_price=et_price,
                accessory_type="E.T",
            )
        )

        # 2. N.T (Neutral Terminal)
        accessories.append(
            AccessoryItem(
                item_name="N.T",
                spec="",
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=PRICE_NT,
                accessory_type="N.T",
            )
        )

        # 3. N.P (CARD HOLDER)
        # 수량: 분기차단기 총수량
        accessories.append(
            AccessoryItem(
                item_name="N.P",
                spec="CARD HOLDER",
                unit=UNIT_ACCESSORY,
                quantity=branch_count,
                unit_price=PRICE_NP_CARD_HOLDER,
                accessory_type="N.P",
            )
        )

        # 4. N.P (3T*40*200)
        accessories.append(
            AccessoryItem(
                item_name="N.P",
                spec="3T*40*200",
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=PRICE_NP_3T_40_200,
                accessory_type="N.P",
            )
        )

        # 5. MAIN BUS-BAR (별도 함수 _calculate_busbar에서 처리)

        # 6. BUS-BAR (분기용) (별도 함수 _calculate_branch_busbar에서 처리)

        # 7. COATING
        accessories.append(
            AccessoryItem(
                item_name="COATING",
                spec="PVC(20mm)",
                unit=UNIT_COATING,
                quantity=1,
                unit_price=PRICE_COATING,
                accessory_type="COATING",
            )
        )

        # 8. P-COVER
        # 수량: 1면 외함내 분전반 총수량 (현재는 1)
        # 단가: max(((W*H)/PCOVER_AREA_DIVISOR)*PCOVER_PRICE_MULTIPLIER, PCOVER_MIN_PRICE)
        # 최소 가격 12,000원 적용 (대표님 피드백 2024-12-10)
        p_cover_price = max(
            int(((w * h) / PCOVER_AREA_DIVISOR) * PCOVER_PRICE_MULTIPLIER),
            PCOVER_MIN_PRICE
        )
        accessories.append(
            AccessoryItem(
                item_name="P-COVER",
                spec="아크릴(PC)",
                unit=UNIT_ACCESSORY,
                quantity=1,
                unit_price=p_cover_price,
                accessory_type="P-COVER",
            )
        )

        # 9. 차단기지지대 (400~800AF만)
        # 실측 보정 (CLAUDE_KNOWLEDGE 14.7): 2EA × 28,000원 고정
        if 400 <= main_af <= 800:
            accessories.append(
                AccessoryItem(
                    item_name="차단기지지대",
                    spec="",
                    unit=UNIT_ACCESSORY,
                    quantity=2,
                    unit_price=28000,
                    accessory_type="차단기지지대",
                )
            )

        # 10. ELB지지대 (견적요령.txt: D = 작은타입차단기 총합)
        # 소형차단기: SIE-32, SIB-32, 32GRHS, BS-32, BS32
        # BUG FIX: 각 BreakerItem의 quantity 합산 (1개가 아닌 실제 수량)
        # BUG FIX-2: 정규화된 모델명 비교 (대소문자/하이픈 무시)
        # BUG FIX-3: 소형 차단기는 반드시 2P여야 함 (4P MCCB 제외)
        small_breaker_count = 0
        # 소형 차단기 모델명 정규화 리스트 (하이픈 제거, 대문자)
        SMALL_BREAKER_MODELS_NORMALIZED = {"SIE32", "SIB32", "SBW32", "32GRHS", "BS32"}
        for b in branch_breakers:
            model = getattr(b, "model", "")
            poles = getattr(b, "poles", 4)  # 기본값 4P (소형 아님)
            # 정규화: 하이픈 제거, 대문자 변환
            model_normalized = model.upper().replace("-", "")
            # 소형 차단기는 반드시 2P여야 함 (4P는 소형 차단기가 아님)
            if model_normalized in SMALL_BREAKER_MODELS_NORMALIZED and poles == 2:
                small_breaker_count += getattr(b, "quantity", 1)  # 수량 합산

        if small_breaker_count > 0:
            accessories.append(
                AccessoryItem(
                    item_name="ELB지지대",
                    spec="",
                    unit=UNIT_ACCESSORY,
                    quantity=small_breaker_count,
                    unit_price=PRICE_ELB_SUPPORT,
                    accessory_type="ELB지지대",
                )
            )

        # 11. INSULATOR
        # 수량: MAIN BUS-BAR용 지지대 총합 * 4 (일반적으로 4개)
        # 단가: 메인차단기 AF별 (견적요령.txt)
        if main_af <= 250:
            insulator_price = PRICE_INSULATOR_50_250AF
        else:  # 400~800AF
            insulator_price = PRICE_INSULATOR_400_800AF

        accessories.append(
            AccessoryItem(
                item_name="INSULATOR",
                spec="EPOXY 40*40",
                unit=UNIT_ACCESSORY,
                quantity=4,
                unit_price=insulator_price,
                accessory_type="INSULATOR",
            )
        )

        # 12. 잡자재비 (별도 함수 _calculate_misc_materials에서 처리)

        # 13. ASSEMBLY CHARGE (별도 함수 _calculate_assembly_charge에서 처리)

        logger.debug(f"Calculated {len(accessories)} accessories (견적조건 7번)")
        return accessories

    def _calculate_busbar(
        self, enclosure_result, main_breaker: BreakerItem | None
    ) -> BusbarItem | None:
        """
        MAIN BUS-BAR (주부스바) 계산

        주부스바 중량(kg) = (W×H) × 계수 (소수점 1자리)
        계수: BUSBAR_COEFF_* (SSOT 참조)
        단가: PRICE_BUSBAR_PER_KG (SSOT 참조)
        """
        if not main_breaker:
            return None

        # 외함 치수 (EnclosureDimensions는 pydantic 모델)
        dimensions = getattr(enclosure_result, "dimensions", None)
        if dimensions is None:
            raise_error(
                ErrorCode.E_DATA_TRANSFORM,
                "enclosure_result.dimensions가 없습니다 (목업 금지)",
            )

        w = dimensions.width_mm
        h = dimensions.height_mm

        # 메인 차단기 전류
        current_a = main_breaker.current_a

        # 계수 선택 (SSOT) - CEO 규칙 (부스바 산출공식.txt)
        # 규격: 0~100A → 3T*15, 125A~250A → 5T*20, 300A~400A → 6T*30, 500A~800A → 8T*40
        # 계수: 20A~250A → 0.000007, 300A~400A → 0.000013, 500A~800A → 0.000015
        if current_a <= 100:
            coefficient = BUSBAR_COEFF_20_250A
            thickness_width = BUSBAR_SPEC_3T_15
        elif current_a <= 250:
            coefficient = BUSBAR_COEFF_20_250A
            thickness_width = BUSBAR_SPEC_5T_20
        elif current_a <= 400:
            coefficient = BUSBAR_COEFF_300_400A
            thickness_width = BUSBAR_SPEC_6T_30
        else:  # 500~800A
            coefficient = BUSBAR_COEFF_500_800A
            thickness_width = BUSBAR_SPEC_8T_40

        # 중량 계산 (소수점 1자리, HALF_EVEN rounding)
        weight_kg = apply_rounding((w * h) * coefficient, decimal_places=1)

        # 단가 계산 (SSOT)
        unit_price = PRICE_BUSBAR_PER_KG

        return BusbarItem(
            item_name="MAIN BUS-BAR",
            spec=thickness_width,
            unit=UNIT_BUSBAR,
            quantity=weight_kg,
            unit_price=unit_price,
            busbar_type="MAIN BUS-BAR",
            thickness_width=thickness_width,
            weight_kg=weight_kg,
        )

    def _calculate_branch_busbar(
        self, enclosure_result, branch_breakers: list[BreakerItem]
    ) -> BusbarItem | None:
        """
        BUS-BAR (분기용) 계산

        규격: 분기차단기 중 AF 가장 높은 것 기준 (MAIN BUS-BAR와 동일 스펙)
        단위: KG
        수량: (W×H) × 계수 (소수점 2자리) - BRANCH_BUSBAR_COEFF_* 사용
        단가: PRICE_BUSBAR_PER_KG (SSOT 참조)
        """
        logger.info(f"[BUS-BAR DEBUG] _calculate_branch_busbar called: branch_breakers count={len(branch_breakers) if branch_breakers else 0}")

        if not branch_breakers:
            logger.warning("[BUS-BAR DEBUG] No branch_breakers - returning None")
            return None

        # 외함 치수
        dimensions = getattr(enclosure_result, "dimensions", None)
        logger.info(f"[BUS-BAR DEBUG] enclosure_result={enclosure_result}, dimensions={dimensions}")

        if dimensions is None:
            logger.warning("[BUS-BAR DEBUG] dimensions is None - returning None")
            return None

        w = dimensions.width_mm
        h = dimensions.height_mm

        # 분기차단기 중 AF 가장 높은 것 찾기
        max_af = 0
        for b in branch_breakers:
            af = getattr(b, "frame_af", 0)
            logger.info(f"[DEBUG] Branch breaker: model={getattr(b, 'model', '?')}, frame_af={af}, current_a={getattr(b, 'current_a', 0)}")
            if af > max_af:
                max_af = af

        logger.info(f"[DEBUG] max_af for branch BUS-BAR: {max_af}")

        if max_af == 0:
            # BUG-004: frame_af가 0이면 current_a에서 계산 (fallback)
            for b in branch_breakers:
                current_a = getattr(b, "current_a", 0)
                if current_a <= 50:
                    af = 50
                elif current_a <= 100:
                    af = 100
                elif current_a <= 125:
                    af = 125
                elif current_a <= 250:
                    af = 250
                elif current_a <= 400:
                    af = 400
                elif current_a <= 600:
                    af = 600
                else:
                    af = 800
                if af > max_af:
                    max_af = af
            logger.info(f"[DEBUG] max_af (fallback from current_a): {max_af}")

        if max_af == 0:
            return None

        # AF에 따른 규격 및 계수 (SSOT - 분기용 계수 사용)
        # CEO 규칙 (2024-12-02): 분기 최대 AF 기준
        #   100AF_이하: 3T×15
        #   125AF~250AF: 5T×20
        #   300AF~400AF: 6T×30
        #   500AF~800AF: 8T×40
        if max_af <= 100:
            coefficient = BRANCH_BUSBAR_COEFF_20_250A
            thickness_width = BUSBAR_SPEC_3T_15
        elif max_af <= 250:
            coefficient = BRANCH_BUSBAR_COEFF_20_250A
            thickness_width = BUSBAR_SPEC_5T_20
        elif max_af <= 400:
            coefficient = BRANCH_BUSBAR_COEFF_300_400A
            thickness_width = BUSBAR_SPEC_6T_30
        else:  # 500~800AF
            coefficient = BRANCH_BUSBAR_COEFF_500_800A
            thickness_width = BUSBAR_SPEC_8T_40

        # 중량 계산 (소수점 1자리, HALF_EVEN rounding)
        weight_kg = apply_rounding((w * h) * coefficient, decimal_places=1)

        # 단가 (SSOT)
        unit_price = PRICE_BUSBAR_PER_KG

        return BusbarItem(
            item_name="BUS-BAR",
            spec=thickness_width,
            unit=UNIT_BUSBAR,
            quantity=weight_kg,
            unit_price=unit_price,
            busbar_type="BUS-BAR",
            thickness_width=thickness_width,
            weight_kg=weight_kg,
        )

    def _calculate_misc_materials(
        self,
        enclosure_result,
        accessories_count: int,
        main_breaker: BreakerItem | None = None,
        is_main_only: bool = False,
        has_busbar_option: bool = False,
    ) -> AccessoryItem | None:
        """
        잡자재비 계산

        일반 견적:
        - 기본값: 7,000원
        - 외함 H값 100mm 증가마다: +1,500원 (실측 보정, CLAUDE_KNOWLEDGE 14.3)
        - 부속자재 1개 추가마다: +10,000원
        - 최대: 55,000원 (대형반+STEEL P-COVER 반영)

        메인차단기만 있는 경우:
        - 400~800AF 부스바 처리 옵션: +15,000원
        """
        dimensions = getattr(enclosure_result, "dimensions", None)
        if dimensions is None:
            return None

        h = dimensions.height_mm

        # 기본값 (SSOT)
        price = MISC_BASE_PRICE

        # CEO 규칙: 기준 H=700mm, 800mm부터 100mm당 +1,000원
        if h > 700:
            h_increment = ((h - 700) // 100) * MISC_H_INCREMENT_PER_100MM
        else:
            h_increment = 0
        price += h_increment

        # 부속자재 1개당 증분 (SSOT)
        accessory_increment = accessories_count * MISC_ACCESSORY_INCREMENT
        price += accessory_increment

        # 최대값 제한 (SSOT)
        price = min(price, MISC_MAX_PRICE)

        # 메인차단기만 + 부스바 처리 옵션 (SSOT)
        if is_main_only and has_busbar_option and main_breaker:
            main_af = getattr(main_breaker, "frame_af", 100)
            if main_af >= 400:
                price += MISC_BUSBAR_OPTION_400_800AF

        return AccessoryItem(
            item_name="잡자재비",
            spec="",
            unit=UNIT_ASSEMBLY,
            quantity=1,
            unit_price=price,
            accessory_type="잡자재비",
        )

    def _calculate_assembly_charge(
        self,
        enclosure_result,
        main_breaker: BreakerItem | None,
        branch_breakers: list[BreakerItem] | None = None,
        is_main_only: bool = False,
        has_busbar_option: bool = False,
    ) -> AssemblyItem | None:
        """
        ASSEMBLY CHARGE (인건비) 계산

        CEO 규칙 (2024-12-02):
        - 공식: 기본가격(50,000원) + (총차단기수 × 차단기당단가)
        - 차단기당 단가는 메인 AF 기준 (분기 AF 무시!)
          - 100AF까지: 2,000원
          - 125AF~250AF: 3,000원
          - 400AF: 5,000원
          - 600~800AF: 6,000원

        메인차단기만 있는 경우 (is_main_only=True):
        - 디폴트: 50~250AF=15,000원, 400AF=20,000원, 600~800AF=30,000원
        - 부스바 처리 옵션: 400AF=+40,000원, 600~800AF=+70,000원
        """
        if not main_breaker:
            return None

        # AF 값 추출
        af_value = getattr(main_breaker, "frame_af", 100)

        # ===== 메인차단기만 있는 경우 (SSOT) =====
        if is_main_only:
            # 디폴트 인건비 (SSOT)
            if af_value <= 250:
                charge = ASSEMBLY_MAIN_ONLY_50_250AF
            elif af_value == 400:
                charge = ASSEMBLY_MAIN_ONLY_400AF
            else:  # 600~800AF
                charge = ASSEMBLY_MAIN_ONLY_600_800AF

            # 부스바 처리 옵션 추가 인건비 (SSOT)
            if has_busbar_option:
                if af_value == 400:
                    charge += ASSEMBLY_MAIN_ONLY_BUSBAR_400AF
                elif af_value >= 600:
                    charge += ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF

            return AssemblyItem(
                item_name="ASSEMBLY CHARGE",
                spec="조립비",
                unit=UNIT_ASSEMBLY,
                quantity=1,
                unit_price=charge,
                assembly_type="ASSEMBLY CHARGE",
            )

        # ===== 일반 견적 (분기 있음) - CEO 규칙 (2024-12-05 수정) =====
        # 외함 H값 기반 계산
        # 공식: 기본가격 + ((외함H - 기준H) / 100) × H당추가금액
        # SIE-32/32GRHS 대부분인 경우 추가 인건비 적용

        # 외함 치수 조회
        dimensions = getattr(enclosure_result, "dimensions", None)
        enclosure_w = dimensions.width_mm if dimensions else 600  # 기본값 600mm
        enclosure_h = dimensions.height_mm if dimensions else 700  # 기본값 700mm

        # SIE-32/32GRHS 소형 차단기 수량 계산
        small_breaker_count = 0
        total_branch_count = 0
        if branch_breakers:
            for b in branch_breakers:
                qty = getattr(b, "quantity", 1)
                total_branch_count += qty
                model = getattr(b, "model", "").upper()
                if "SIE-32" in model or "32GRHS" in model or "SIB-32" in model or "SBW-32" in model or "BS-32" in model:
                    small_breaker_count += qty

        # SIE 보너스 적용 조건 (대표님 피드백 2024-12-10):
        # 외함 600×700 이상 AND 소형 14개 이상일 때만 적용
        enclosure_size_ok = (
            enclosure_w >= SIE_BONUS_MIN_ENCLOSURE_W  # 600mm 이상
            and enclosure_h >= SIE_BONUS_MIN_ENCLOSURE_H  # 700mm 이상
        )
        small_count_ok = small_breaker_count >= SIE_BONUS_MIN_SMALL_BREAKER_COUNT  # 14개 이상
        is_mostly_small = enclosure_size_ok and small_count_ok

        # AF별 기준값 및 계수 적용
        if af_value <= 100:
            base_h = ASSEMBLY_BASE_H_50_100AF  # 700mm
            base_price = ASSEMBLY_BASE_PRICE_50_100AF  # 50,000원
            h_increment = ASSEMBLY_H_INCREMENT_50_100AF  # 15,000원/100mm
            sie_bonus = ASSEMBLY_SIE_BONUS_50_100AF if is_mostly_small else 0  # 10,000원
        elif af_value <= 250:
            base_h = ASSEMBLY_BASE_H_125_250AF  # 800mm
            base_price = ASSEMBLY_BASE_PRICE_125_250AF  # 60,000원
            h_increment = ASSEMBLY_H_INCREMENT_125_250AF  # 15,000원/100mm
            sie_bonus = ASSEMBLY_SIE_BONUS_125_250AF if is_mostly_small else 0  # 10,000원
        elif af_value <= 400:
            base_h = ASSEMBLY_BASE_H_400AF  # 1200mm
            base_price = ASSEMBLY_BASE_PRICE_400AF  # 130,000원
            h_increment = ASSEMBLY_H_INCREMENT_400AF  # 20,000원/100mm
            sie_bonus = ASSEMBLY_SIE_BONUS_400AF if is_mostly_small else 0  # 15,000원
        else:  # 600~800AF
            base_h = ASSEMBLY_BASE_H_600_800AF  # 1600mm
            base_price = ASSEMBLY_BASE_PRICE_600_800AF  # 250,000원
            h_increment = ASSEMBLY_H_INCREMENT_600_800AF  # 40,000원/100mm
            sie_bonus = ASSEMBLY_SIE_BONUS_600_800AF if is_mostly_small else 0  # 15,000원

        # CEO 공식: 기본가격 + ((외함H - 기준H) / 100) × H당추가금액 + SIE보너스
        h_diff = max(0, enclosure_h - base_h)  # 기준보다 작으면 0
        h_increments = h_diff // 100  # 100mm 단위
        charge = base_price + (h_increments * h_increment) + sie_bonus

        return AssemblyItem(
            item_name="ASSEMBLY CHARGE",
            spec="조립비",
            unit=UNIT_ASSEMBLY,
            quantity=1,
            unit_price=charge,
            assembly_type="ASSEMBLY CHARGE",
        )
