"""
Stage 1: Enclosure Solver (외함 계산기)

외함 크기 계산 및 최적 후보 선정
- H_total, W_total, D_total 계산
- 실제 지식파일 사용 (core_rules.json)
- 품질 게이트: fit_score ≥ 0.90

절대 규칙:
- NO 목업/더미 데이터
- 실제 formulas.json + core_rules.json 사용
- 실패 시 명확한 오류 메시지
"""

import json
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# SSOT Integration
from ..core.ssot.constants import (
    ACCESSORY_MARGIN_PER_ROW_MM,
    DEPTH_WITH_PBL_MM,
    DEPTH_WITHOUT_PBL_MM,
    FACE_TO_FACE_SMALL_2P_MM,
    FIT_SCORE_THRESHOLD,
    MAIN_TO_BRANCH_GAP_MM,
    PHASE_1_NAME,
    SMALL_BREAKER_CURRENT_RANGE,
    SMALL_BREAKER_ONLY_WIDTH_MM,
    STANDARD_ENCLOSURE_WIDTHS_MM,
    STANDARD_ENCLOSURE_HEIGHTS_MM,
    STANDARD_ENCLOSURE_DEPTHS_MM,
    # 고AF 단품 분전반
    SINGLE_BREAKER_CABLE_CLEARANCE,
    SINGLE_BREAKER_D_400AF,
    SINGLE_BREAKER_D_600_800AF,
    SINGLE_BREAKER_W_400AF,
    SINGLE_BREAKER_W_600AF,
    SINGLE_BREAKER_W_800AF,
    TERMINAL_LUG_LENGTH_MM,
)

# Error System Integration (Phase 1)
from ..errors import ENC_001, ENC_002, ENC_003, ValidationError
from ..models.enclosure import (
    AccessorySpec,
    BreakerSpec,
    CustomerRequirements,
    EnclosureCandidate,
    EnclosureDimensions,
    EnclosureResult,
    QualityGateResult,
)


class EnclosureSolver:
    """외함 크기 계산 엔진"""

    # 2P 20A/30A → 30AF 자동 변환 규칙 (대표님 지식)
    SMALL_2P_MODEL_MAP = {
        "sangdo": {"ELB": "SIE-32", "MCCB": "SIB-32"},
        "LS": {"ELB": "32GRHS", "MCCB": "BS-32"},
    }

    def __init__(self, knowledge_path: Path | None = None):
        """
        초기화 - 실제 지식파일 로드

        Args:
            knowledge_path: 지식파일 경로 (기본: temp_basic_knowledge/core_rules.json)
        """
        if knowledge_path is None:
            # 기본 경로: 프로젝트 루트 기준
            knowledge_path = (
                Path(__file__).parent.parent.parent.parent
                / "temp_basic_knowledge"
                / "core_rules.json"
            )

        if not knowledge_path.exists():
            raise_error(
                ErrorCode.E_INTERNAL,
                f"지식파일을 찾을 수 없습니다: {knowledge_path}\n"
                "실제 지식파일이 필요합니다. 목업 데이터는 사용하지 않습니다.",
            )

        with open(knowledge_path, encoding="utf-8") as f:
            self.knowledge = json.load(f)

        # 필수 섹션 검증
        required_sections = [
            "breaker_dimensions_mm",
            "frame_clearances",
            "enclosure_width_rules_mm",
            "depth_rules_mm",
        ]
        for section in required_sections:
            if section not in self.knowledge:
                raise_error(
                    ErrorCode.E_INTERNAL,
                    f"지식파일에 필수 섹션이 없습니다: {section}\n"
                    "완전한 core_rules.json 파일이 필요합니다.",
                )

    def calculate_height(
        self,
        main_breaker: BreakerSpec,
        branch_breakers: list[BreakerSpec],
        accessories: list[AccessorySpec],
    ) -> tuple[float, dict]:
        """
        H_total 계산

        H_total = top_margin + main_height + gap + branches_height + bottom_margin + accessory_margin

        Args:
            main_breaker: 메인 차단기
            branch_breakers: 분기 차단기 리스트
            accessories: 부속자재 리스트 (magnet, timer 등)

        Returns:
            (H_total, breakdown): 총 높이와 상세 계산 내역

        Raises:
            ValidationError: ENC-001 외함 높이 계산 공식 오류
        """
        breakdown = {}

        try:
            # 1. 상단 여유 (top_margin)
            top_margin = self._get_top_margin(main_breaker.frame_af)
            breakdown["top_margin_mm"] = top_margin

            # 2. 메인 차단기 높이
            main_height = self._get_breaker_height(main_breaker)
            breakdown["main_breaker_height_mm"] = main_height

            # 3. 메인-분기 간격
            gap = MAIN_TO_BRANCH_GAP_MM  # SSOT
            breakdown["main_to_branch_gap_mm"] = gap

            # 4. 분기 차단기 총 높이
            branches_height = self._calculate_branches_height(branch_breakers)
            breakdown["branches_total_height_mm"] = branches_height

            # 5. 하단 여유 (bottom_margin)
            bottom_margin = self._get_bottom_margin(main_breaker.frame_af)
            breakdown["bottom_margin_mm"] = bottom_margin

            # 6. 부속자재 여유 (accessories)
            accessory_margin = self._calculate_accessory_margin(accessories)
            breakdown["accessory_margin_mm"] = accessory_margin

            # 7. 총 높이 (계산값)
            H_calculated = (
                top_margin
                + main_height
                + gap
                + branches_height
                + bottom_margin
                + accessory_margin
            )
            breakdown["H_calculated_mm"] = H_calculated

            # 8. 기성함 규격으로 반올림 (업사이징만 허용, 다운사이징 절대 금지)
            H_total = self._round_to_standard_size(
                H_calculated, STANDARD_ENCLOSURE_HEIGHTS_MM
            )
            breakdown["H_total_mm"] = H_total
            breakdown["H_rounded_reason"] = (
                f"계산값 {H_calculated:.0f}mm → 기성함 {H_total}mm (업사이징)"
                if H_total > H_calculated
                else f"계산값 {H_calculated:.0f}mm = 기성함 {H_total}mm (정확 일치)"
            )

            # ENC-001 검증: 계산 결과가 유효한지 확인
            if H_total <= 0:
                raise ValidationError(
                    error_code=ENC_001,
                    field="H_total",
                    value=H_total,
                    expected="> 0",
                    phase=PHASE_1_NAME,  # SSOT
                )

            return H_total, breakdown

        except (ValueError, KeyError) as e:
            # 계산 중 오류 발생 시 ENC-001 발생
            raise ValidationError(
                error_code=ENC_001,
                field="calculate_height",
                value=str(e),
                expected="Valid H_total calculation",
                phase=PHASE_1_NAME,  # SSOT
            ) from e

    def calculate_width(
        self,
        main_breaker: BreakerSpec,
        branch_breakers: list[BreakerSpec],
    ) -> tuple[float, dict]:
        """
        W_total 계산

        실제 enclosure_width_rules_mm 적용

        Args:
            main_breaker: 메인 차단기
            branch_breakers: 분기 차단기 리스트

        Returns:
            (W_total, breakdown): 총 폭과 상세 계산 내역

        Raises:
            ValidationError: ENC-002 외함 폭 계산 오류
        """
        breakdown = {}
        af = main_breaker.frame_af
        breakdown["main_af"] = af

        try:
            # 소형 메인 차단기 (30AF, 32AF) - 소형분전반, W=500mm 기본
            # 견적서작성법: 소형 차단기는 기본 폭 500mm
            if af in [30, 32]:
                W_base = SMALL_BREAKER_ONLY_WIDTH_MM  # 500mm
                rule_matched = {"main_af_exact": af, "W": 500, "note": "소형 메인 차단기 기본값"}
                breakdown["W_base_mm"] = W_base
                breakdown["small_main_breaker"] = True
            else:
                rules = self.knowledge["enclosure_width_rules_mm"]["rules"]

                # AF 범위별 기본 W 찾기
                W_base = None
                rule_matched = None

                for rule in rules:
                    if "main_af_range" in rule:
                        af_range = rule["main_af_range"]
                        min_af, max_af = map(int, af_range.split("-"))
                        if min_af <= af <= max_af:
                            W_base = rule["W"]
                            rule_matched = rule
                            break
                    elif "main_af_exact" in rule:
                        if af == rule["main_af_exact"]:
                            W_base = rule["W"]
                            rule_matched = rule
                            break

                if W_base is None:
                    raise ValidationError(
                        error_code=ENC_002,
                        field="main_breaker.frame_af",
                        value=af,
                        expected="50~800AF 범위 내 지원 프레임",
                        phase=PHASE_1_NAME,  # SSOT
                    )

        except (KeyError, ValueError) as e:
            raise ValidationError(
                error_code=ENC_002,
                field="calculate_width",
                value=str(e),
                expected="Valid W_total calculation",
                phase=PHASE_1_NAME,  # SSOT
            ) from e

        breakdown["W_base_mm"] = W_base

        # === 예외 1: 분기 전부 소형(2P 20~30A)이면 W=500 적용 (대표님 피드백) ===
        all_small = self._is_all_small_breakers(branch_breakers)
        breakdown["all_small_breakers"] = all_small

        if all_small and len(branch_breakers) > 0:
            # 분기가 모두 소형이면 W=500mm 고정
            W_total = SMALL_BREAKER_ONLY_WIDTH_MM  # SSOT = 500
            breakdown["width_small_exception"] = True
            breakdown["width_small_reason"] = (
                f"분기 전부 소형(2P {SMALL_BREAKER_CURRENT_RANGE[0]}~{SMALL_BREAKER_CURRENT_RANGE[1]}A) → W=500mm 적용"
            )
            breakdown["width_bumped"] = False
        else:
            breakdown["width_small_exception"] = False

            # bump_if 조건 확인 (200~250AF 분기 ≥2개)
            if rule_matched and "bump_if" in rule_matched:
                count_200_250 = sum(1 for b in branch_breakers if 200 <= b.frame_af <= 250)
                breakdown["branch_200_250_count"] = count_200_250

                if count_200_250 >= rule_matched["bump_if"].get(
                    "branch_200_250_count_gte", 999
                ):
                    W_total = rule_matched["bump_if"]["W"]
                    breakdown["width_bumped"] = True
                else:
                    W_total = W_base
                    breakdown["width_bumped"] = False
            else:
                W_total = W_base
                breakdown["width_bumped"] = False

        # 기성함 규격으로 최종 확인 (업사이징만 허용)
        W_final = self._round_to_standard_size(W_total, STANDARD_ENCLOSURE_WIDTHS_MM)
        breakdown["W_total_mm"] = W_final
        if W_final != W_total:
            breakdown["W_rounded_reason"] = (
                f"규칙값 {W_total}mm → 기성함 {W_final}mm (업사이징)"
            )
        return W_final, breakdown

    def calculate_depth(
        self,
        accessories: list[AccessorySpec],
    ) -> tuple[float, dict]:
        """
        D_total 계산

        PBL(푸시버튼램프) 포함 여부로 결정

        Args:
            accessories: 부속자재 리스트

        Returns:
            (D_total, breakdown): 총 깊이와 상세 계산 내역
        """
        breakdown = {}

        # PBL 포함 여부 확인
        has_pbl = any(
            "pbl" in acc.type.lower() or "push" in acc.type.lower()
            for acc in accessories
        )
        breakdown["has_pbl"] = has_pbl

        if has_pbl:
            D_total = DEPTH_WITH_PBL_MM  # SSOT
            breakdown["reason"] = f"PBL 포함 → D≥{DEPTH_WITH_PBL_MM}mm 필수"
        else:
            D_total = DEPTH_WITHOUT_PBL_MM  # SSOT
            breakdown["reason"] = f"PBL 없음 → 기본 {DEPTH_WITHOUT_PBL_MM}mm"

        breakdown["D_total_mm"] = D_total
        return D_total, breakdown

    async def solve(
        self,
        main_breaker: BreakerSpec,
        branch_breakers: list[BreakerSpec],
        accessories: list[AccessorySpec],
        customer_requirements: CustomerRequirements,
    ) -> EnclosureResult:
        """
        외함 크기 계산 및 최적 후보 선정 (I-2: Async)

        Args:
            main_breaker: 메인 차단기
            branch_breakers: 분기 차단기 리스트
            accessories: 부속자재 리스트
            customer_requirements: 고객 요구사항

        Returns:
            EnclosureResult: 계산 결과 및 후보 목록
        """
        # 0. 분기 차단기 정규화 (2P 20A/30A → 30AF)
        normalized_branches = self._normalize_breakers(branch_breakers)

        # === 메인차단기만 있는 경우 (분기 없음) ===
        # CEO 규칙: 외함 크기 300×400×150 (부속자재 없을 때 기본)
        is_main_only = len(normalized_branches) == 0
        has_accessories = len(accessories) > 0

        if is_main_only and not has_accessories:
            main_af = main_breaker.frame_af

            if main_af >= 400:
                # === 고AF 단품 분전반 (400~800AF 차단기 1개, 동관단자 직결) ===
                # 대표님 규칙 (2026-03-09)
                breaker_h = self._get_breaker_height(main_breaker)
                lug_total = TERMINAL_LUG_LENGTH_MM * 2  # 상단 + 하단

                # 전선 여유 (AF별)
                af_key = f"{main_af}AF"
                if af_key not in SINGLE_BREAKER_CABLE_CLEARANCE:
                    af_key = "800AF"  # fallback
                top_clearance, bottom_clearance = SINGLE_BREAKER_CABLE_CLEARANCE[af_key]
                cable_total = top_clearance + bottom_clearance

                H_raw = breaker_h + lug_total + cable_total
                # 반올림 (10단위)
                import math
                H_total = float(math.ceil(H_raw / 10) * 10)

                # W 디폴트
                if main_af <= 400:
                    W_total = float(SINGLE_BREAKER_W_400AF)
                elif main_af <= 600:
                    W_total = float(SINGLE_BREAKER_W_600AF)
                else:
                    W_total = float(SINGLE_BREAKER_W_800AF)

                # D 디폴트
                if main_af <= 400:
                    D_total = float(SINGLE_BREAKER_D_400AF)
                else:
                    D_total = float(SINGLE_BREAKER_D_600_800AF)

                H_breakdown = {
                    "single_breaker_panel": True,
                    "breaker_h_mm": breaker_h,
                    "terminal_lug_mm": lug_total,
                    "cable_clearance_top_mm": top_clearance,
                    "cable_clearance_bottom_mm": bottom_clearance,
                    "h_raw_mm": H_raw,
                    "h_rounded_mm": H_total,
                }
                W_breakdown = {"single_breaker_default": True, "main_af": main_af}
                D_breakdown = {"single_breaker_default": True, "main_af": main_af}
            else:
                # 메인차단기만 (400AF 미만), 부속자재 없음 → 300×400×150
                W_total = 300.0
                H_total = 400.0
                D_total = 150.0
                H_breakdown = {"main_only_default": True}
                W_breakdown = {"main_only_default": True}
                D_breakdown = {"main_only_default": True}
        else:
            # 1. 치수 계산 (일반 로직)
            H_total, H_breakdown = self.calculate_height(
                main_breaker, normalized_branches, accessories
            )
            W_total, W_breakdown = self.calculate_width(main_breaker, normalized_branches)
            D_total, D_breakdown = self.calculate_depth(accessories)

        dimensions = EnclosureDimensions(
            width_mm=W_total,
            height_mm=H_total,
            depth_mm=D_total,
        )

        # 2. HDS 카탈로그 조회 (Task 8 완료) - I-2: Async
        from .catalog_loader import get_catalog_loader

        catalog_loader = await get_catalog_loader()

        # 정확한 매칭 시도 - I-2: Async
        exact_match = await catalog_loader.find_exact_match(
            width=int(W_total),
            height=int(H_total),
            depth=int(D_total),
        )

        # 가까운 매칭 시도 (500mm 이내, 폭 증가 허용)
        # 예: 600x1675 계산 -> 700x1800 기성함 선택 (차이 325mm)
        # 주문제작보다 기성함이 훨씬 저렴하므로 여유 확대
        nearest_match = await catalog_loader.find_nearest_match(
            width=int(W_total),
            height=int(H_total),
            depth=int(D_total),
            max_diff_mm=500,
        )

        candidates = []
        if exact_match:
            candidates.append(
                EnclosureCandidate(
                    model=exact_match.model,
                    size_mm=(
                        exact_match.size_mm[0],
                        exact_match.size_mm[1],
                        exact_match.size_mm[2],
                    ),
                    price=exact_match.price,
                    match_type="exact",
                    material=exact_match.material,
                    install_location=exact_match.install_location,
                )
            )

        if nearest_match and (
            not exact_match or nearest_match.model != exact_match.model
        ):
            candidates.append(
                EnclosureCandidate(
                    model=nearest_match.model,
                    size_mm=(
                        nearest_match.size_mm[0],
                        nearest_match.size_mm[1],
                        nearest_match.size_mm[2],
                    ),
                    price=nearest_match.price,
                    match_type="nearest",
                    material=nearest_match.material,
                    install_location=nearest_match.install_location,
                )
            )

        # 3. 품질 게이트 (기성함 찾았으면 무조건 합격)
        if exact_match or nearest_match:
            fit_score = 1.0  # 기성함 찾음 -> 합격
        else:
            fit_score = 0.0  # 주문제작 필요

        quality_gate = QualityGateResult(
            name="fit_score_check",
            passed=(fit_score >= FIT_SCORE_THRESHOLD),  # SSOT
            actual=fit_score,
            threshold=FIT_SCORE_THRESHOLD,  # SSOT
            operator=">=",
            critical=True,
        )

        # customer_requirements에서 enclosure_type과 material 추출 (필수 필드)
        enc_type = customer_requirements.enclosure_type
        mat = customer_requirements.material or "STEEL 1.6T"

        return EnclosureResult(
            dimensions=dimensions,
            candidates=candidates,
            quality_gate=quality_gate,
            calculation_details={
                "H_breakdown": H_breakdown,
                "W_breakdown": W_breakdown,
                "D_breakdown": D_breakdown,
            },
            enclosure_type=enc_type,
            material=mat,
        )

    # === Private Helper Methods ===

    def _normalize_small_2p_breaker(self, breaker: BreakerSpec) -> BreakerSpec:
        """
        2P 20A/30A 차단기를 30AF(최소 타입)로 정규화

        대표님 지식:
        - ELB/MCCB 2P 20A, 2P 30A는 고객 요청 없으면 30AF 고정
        - 모델명: 상도 ELB=SIE-32, LS ELB=32GRHS, 상도 MCCB=SIB-32, LS MCCB=BS-32

        Args:
            breaker: 원본 차단기 스펙

        Returns:
            BreakerSpec: 정규화된 차단기 스펙 (30AF 적용)
        """
        # 2P 20A 또는 30A만 대상
        if breaker.poles != 2 or breaker.current_a not in [20, 30]:
            return breaker

        # 이미 30AF(또는 32AF로 표기)이면 유지
        if breaker.frame_af in [30, 32]:
            return breaker

        # 모델명에서 브랜드와 타입 추론
        model_upper = breaker.model.upper()

        # 상도 차단기
        if model_upper.startswith("S"):
            if "E" in model_upper[1:3]:  # SIE, SEE 등 = ELB
                new_model = "SIE-32"
            else:  # SIB, SBE 등 = MCCB
                new_model = "SIB-32"
        # LS 차단기
        elif model_upper.startswith(("A", "E", "3")):
            if "GR" in model_upper or model_upper.startswith("E"):  # ELB
                new_model = "32GRHS"
            else:  # MCCB
                new_model = "BS-32"
        else:
            # 기본값: 상도 MCCB
            new_model = "SIB-32"

        # 새로운 BreakerSpec 생성 (30AF 적용)
        return BreakerSpec(
            id=breaker.id,
            model=new_model,
            poles=breaker.poles,
            current_a=breaker.current_a,
            frame_af=30,  # 30AF로 고정
        )

    def _normalize_breakers(
        self, branch_breakers: list[BreakerSpec]
    ) -> list[BreakerSpec]:
        """
        분기 차단기 목록 정규화 (2P 20A/30A → 30AF)

        Args:
            branch_breakers: 원본 분기 차단기 목록

        Returns:
            list[BreakerSpec]: 정규화된 분기 차단기 목록
        """
        return [self._normalize_small_2p_breaker(b) for b in branch_breakers]

    def _is_all_small_breakers(self, branch_breakers: list[BreakerSpec]) -> bool:
        """
        분기 차단기가 모두 소형(2P 20~30A)인지 확인

        대표님 피드백:
        - 분기가 모두 소형이면 W=500 적용
        - 소형 정의: 2P, 20A 또는 30A

        Args:
            branch_breakers: 분기 차단기 목록

        Returns:
            bool: 모든 분기가 소형이면 True
        """
        if not branch_breakers:
            return False

        min_a, max_a = SMALL_BREAKER_CURRENT_RANGE  # (20, 30)

        for b in branch_breakers:
            # 2P가 아니면 소형 아님
            if b.poles != 2:
                return False
            # 전류가 20~30A 범위 밖이면 소형 아님
            if not (min_a <= b.current_a <= max_a):
                return False

        return True

    def _round_to_standard_size(
        self, calculated: float, standard_sizes: list[int]
    ) -> int:
        """
        계산값을 기성함 규격으로 반올림 (업사이징만 허용)

        대표님 지식:
        - 기성함이 저렴하여 가격경쟁력 매우 높음
        - 업사이징은 허용 (함이 조금 커지는 것은 괜찮음)
        - 다운사이징은 절대 금지 (차단기 설치 불가 = 대형사고)

        Args:
            calculated: 계산된 치수 (mm)
            standard_sizes: 기성함 규격 리스트 (오름차순)

        Returns:
            int: 계산값 이상인 가장 작은 기성함 규격
        """
        calc_int = int(calculated)

        # 계산값 이상인 가장 작은 기성함 규격 찾기
        for size in standard_sizes:
            if size >= calc_int:
                return size

        # 모든 기성함보다 크면 최대 규격 반환 (주문제작 필요)
        return standard_sizes[-1]

    def _get_top_margin(self, af: int) -> float:
        """AF 기준 상단 여유 반환"""
        # 소형 차단기 (30AF, 32AF) - 50AF 규칙과 동일하게 130mm 적용
        # 견적서작성법: 20~60A는 A1=130mm
        if af in [30, 32]:
            return 130.0

        rules = self.knowledge["frame_clearances"]["rules"]

        for rule in rules:
            if "af_range" in rule:
                min_af, max_af = map(int, rule["af_range"].split("-"))
                if min_af <= af <= max_af:
                    return rule["top"]
            elif "af_exact" in rule:
                if af == rule["af_exact"]:
                    return rule["top"]

        raise_error(
            ErrorCode.E_INTERNAL, f"AF={af}에 대한 상단 여유 규칙을 찾을 수 없습니다."
        )

    def _get_bottom_margin(self, af: int) -> float:
        """AF 기준 하단 여유 반환"""
        # 소형 차단기 (30AF, 32AF) - 50AF 규칙과 동일하게 150mm 적용
        # 견적서작성법: 20~225A는 하단 150mm
        if af in [30, 32]:
            return 150.0

        rules = self.knowledge["frame_clearances"]["rules"]

        for rule in rules:
            if "af_range" in rule:
                min_af, max_af = map(int, rule["af_range"].split("-"))
                if min_af <= af <= max_af:
                    return rule["bottom"]
            elif "af_exact" in rule:
                if af == rule["af_exact"]:
                    return rule["bottom"]

        raise_error(
            ErrorCode.E_INTERNAL, f"AF={af}에 대한 하단 여유 규칙을 찾을 수 없습니다."
        )

    def _get_breaker_width(self, breaker: BreakerSpec) -> float:
        """차단기 폭 반환 (W×H×D 중 W) - 눕혀서 배치 시 분전반 H 방향"""
        dimensions_db = self.knowledge["breaker_dimensions_mm"]

        af = breaker.frame_af
        poles = f"{breaker.poles}P"

        # 소형 차단기 (SIE-32, SIB-32 등) - 30AF 또는 32AF로 표기
        if af in [30, 32] and poles == "2P":
            return dimensions_db["small_32"]["2P"][0]  # W값 = 33mm

        # FB 타입
        if "FB" in breaker.model.upper():
            if poles in dimensions_db["FB"]:
                return dimensions_db["FB"][poles][0]  # W값

        # AF 범위별 검색
        section_map = {
            50: ["50AF_econ_std"],
            60: ["60AF_econ_std"],
            100: ["100AF_econ", "100_125AF_std"],
            125: ["100_125AF_std"],
            200: ["200_250AF"],
            250: ["200_250AF"],
            400: ["400AF"],
            600: ["600AF"],
            800: ["800AF"],
        }

        sections_to_try = section_map.get(af, [])
        for section_key in sections_to_try:
            if section_key in dimensions_db:
                if poles in dimensions_db[section_key]:
                    return dimensions_db[section_key][poles][0]  # W값

        raise_error(
            ErrorCode.E_INTERNAL,
            f"차단기 폭을 찾을 수 없습니다: AF={af}, poles={poles}\n"
            f"model={breaker.model}",
        )

    def _get_breaker_height(self, breaker: BreakerSpec) -> float:
        """차단기 높이 반환 (W×H×D 중 H)"""
        dimensions_db = self.knowledge["breaker_dimensions_mm"]

        # AF 기준으로 섹션 찾기
        af = breaker.frame_af
        poles = f"{breaker.poles}P"

        # 소형 차단기 (SIE-32, SIB-32 등) - 30AF 또는 32AF로 표기
        if af in [30, 32] and poles == "2P":
            return dimensions_db["small_32"]["2P"][1]  # H값 = 70mm

        # FB 타입
        if "FB" in breaker.model.upper():
            if poles in dimensions_db["FB"]:
                return dimensions_db["FB"][poles][1]

        # AF 범위별 검색 (with fallback)
        section_map = {
            50: ["50AF_econ_std"],
            60: ["60AF_econ_std"],
            100: ["100AF_econ", "100_125AF_std"],  # Fallback to std if econ not found
            125: ["100_125AF_std"],
            200: ["200_250AF"],
            250: ["200_250AF"],
            400: ["400AF"],
            600: ["600AF"],
            800: ["800AF"],
        }

        # Try all possible sections for this AF
        sections_to_try = section_map.get(af, [])
        for section_key in sections_to_try:
            if section_key in dimensions_db:
                if poles in dimensions_db[section_key]:
                    return dimensions_db[section_key][poles][1]

        raise_error(
            ErrorCode.E_INTERNAL,
            f"차단기 치수를 찾을 수 없습니다: AF={af}, poles={poles}\n"
            f"model={breaker.model}\n"
            f"Available sections: {list(dimensions_db.keys())}",
        )

    def _calculate_branches_height(self, branch_breakers: list[BreakerSpec]) -> float:
        """
        분기 차단기 총 높이 계산 (좌우 마주보기 배치 기준)

        핵심 원리:
        - 분기 차단기는 눕혀서 배치 (1차단자가 중앙 메인부스바를 향함)
        - 좌우 2개씩 마주보기 배치 → 같은 행에 2개
        - 차단기 W(폭) → 분전반 H(높이) 방향으로 누적

        배치 규칙:
        - 같은 극수/프레임끼리 같은 행에 배치 우선
        - 4P 차단기는 N상 위치 고려 (좌측: N상 하단, 우측: N상 상단)
        - 2P 소형(32AF): 마주보기 특수 규칙 40mm

        Raises:
            ValidationError: ENC-003 마주보기 배치 시 높이 계산 오류
        """
        total_height = 0.0

        try:
            # 차단기를 극수/프레임별로 그룹화 (같은 규격끼리 같은 행 배치)
            from collections import defaultdict
            groups = defaultdict(list)

            for breaker in branch_breakers:
                key = (breaker.poles, breaker.frame_af)
                groups[key].append(breaker)

            # 각 그룹별로 행 수 계산 (2개씩 마주보기)
            for (poles, af), breakers_in_group in groups.items():
                count = len(breakers_in_group)
                # 2개씩 마주보기 → 행 수 = ceil(count / 2)
                rows = (count + 1) // 2

                # 차단기 W(폭)를 사용 (눕혀서 배치하므로 W가 H 방향)
                breaker_width = self._get_breaker_width(breakers_in_group[0])

                # 2P 소형 마주보기 특수 규칙 (30AF 또는 32AF)
                if poles == 2 and af in [30, 32]:
                    breaker_width = FACE_TO_FACE_SMALL_2P_MM  # SSOT = 40mm

                group_height = rows * breaker_width
                total_height += group_height

            # ENC-003 검증: 계산 결과가 유효한지 확인
            if total_height < 0:
                raise ValidationError(
                    error_code=ENC_003,
                    field="branches_total_height",
                    value=total_height,
                    expected=">= 0",
                    phase=PHASE_1_NAME,  # SSOT
                )

            return total_height

        except (ValueError, AttributeError) as e:
            raise ValidationError(
                error_code=ENC_003,
                field="_calculate_branches_height",
                value=str(e),
                expected="Valid branches height calculation",
                phase=PHASE_1_NAME,  # SSOT
            ) from e

    def _calculate_accessory_margin(self, accessories: list[AccessorySpec]) -> float:
        """
        부속자재 여유 높이 계산

        마그네트 2개 이상 → 하단 배치 +250mm per row
        """
        magnet_count = sum(
            1
            for acc in accessories
            if "magnet" in acc.type.lower() or "mc" in acc.type.lower()
        )

        if magnet_count == 0:
            return 0.0
        elif magnet_count == 1:
            return 0.0  # 메인 옆 빈공간 배치 (H 변화 없음)
        else:
            # 마그네트 ≥2 → 하단 배치
            # 1줄당 +250mm (W=600 기준 5개까지)
            rows = (magnet_count + 4) // 5  # 5개씩 1줄
            return rows * ACCESSORY_MARGIN_PER_ROW_MM  # SSOT
