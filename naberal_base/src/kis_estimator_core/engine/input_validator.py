"""
Phase 0: Input Validator
견적 입력 데이터 검증 및 에러 게이트

필수 검증 항목:
1. INP-001~005: 필수 정보 누락 검증
2. BUG-001: MCCB/ELB 구분 검증
3. BUS-001~004: MAIN BUS-BAR 규격 검증
4. BUG-002: 카탈로그 존재 여부 검증 (AI Catalog v2)
5. BUG-003, BUG-004: 차단기 타입 자동 선택 검증

모든 BLOCKING 에러는 다음 Phase 진행 차단
"""

import logging
from pathlib import Path

from kis_estimator_core.core.ssot.enums import BreakerCategory

# SSOT Integration
from ..core.ssot.constants import PHASE_0_NAME
from ..errors import (
    # 7대 버그
    BUG_001,
    BUG_002,
    BUG_003,
    BUG_004,
    # BUS-BAR Errors
    BUS_001,
    BUS_002,
    BUS_003,
    BUS_004,
    # Input Errors
    INP_001,
    INP_002,
    INP_003,
    INP_004,
    INP_005,
    CatalogError,
    EstimatorError,
    ValidationError,
)
from ..services.ai_catalog_service import get_ai_catalog_service

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Phase 0: 입력 데이터 검증

    검증 순서:
    1. 필수 정보 존재 여부 (INP-001~005)
    2. MCCB/ELB 구분 (BUG-001)
    3. 카탈로그 검증 (BUG-002)
    4. 차단기 타입 검증 (BUG-003, BUG-004)
    5. MAIN BUS-BAR 규격 검증 (BUS-001~004)
    """

    def __init__(self, catalog_path: Path | None = None):
        """
        Args:
            catalog_path: AI 카탈로그 JSON 파일 경로 (v2)
        """
        # AI Catalog Service v2 사용
        self.ai_catalog = get_ai_catalog_service()
        logger.info("InputValidator initialized with AI Catalog v2")

    def validate(
        self,
        enclosure_material: str | None = None,
        enclosure_type: str | None = None,
        breaker_brand: str | None = None,
        main_breaker: dict | None = None,
        branch_breakers: list[dict] | None = None,
        accessories: list[dict] | None = None,
    ) -> tuple[bool, list[EstimatorError]]:
        """
        입력 데이터 전체 검증

        Args:
            enclosure_material: 외함 재질 (예: "SUS201 1.2T", "STEEL 1.6T")
            enclosure_type: 외함 종류 (예: "옥내노출", "옥외노출")
            breaker_brand: 차단기 브랜드 (예: "상도차단기")
            main_breaker: 메인 차단기 정보 {"poles": 4, "current": 60, "frame": 100}
            branch_breakers: 분기 차단기 목록 [{"type": "ELB", "poles": 2, "current": 20, ...}]
            accessories: 부속자재 목록 [{"name": "MAIN BUS-BAR", "spec": "3T*15", ...}]

        Returns:
            Tuple[bool, List[EstimatorError]]: (통과여부, 에러목록)
        """
        logger.info(f"{PHASE_0_NAME}: Input Validation 시작")  # SSOT
        errors = []

        # 1. 필수 정보 검증
        errors.extend(
            self._validate_required_info(
                enclosure_material,
                enclosure_type,
                breaker_brand,
                main_breaker,
                branch_breakers,
            )
        )

        # BLOCKING 에러가 있으면 즉시 중단
        if errors:
            logger.error(f"필수 정보 검증 실패: {len(errors)}개 에러")
            return False, errors

        # 2. MCCB/ELB 구분 검증
        if branch_breakers:
            errors.extend(self._validate_mccb_elb_distinction(branch_breakers))

        # 3. 카탈로그 검증
        if branch_breakers:
            errors.extend(
                self._validate_catalog_existence(branch_breakers, breaker_brand)
            )

        # 4. 차단기 타입 검증 (소형, 컴팩트)
        if branch_breakers:
            errors.extend(self._validate_breaker_type_selection(branch_breakers))

        # 5. MAIN BUS-BAR 규격 검증
        if main_breaker and accessories:
            errors.extend(self._validate_main_busbar_spec(main_breaker, accessories))

        # BLOCKING 에러 확인
        blocking_errors = [e for e in errors if e.error_code.blocking]

        if blocking_errors:
            logger.error(
                f"{PHASE_0_NAME} 검증 실패: {len(blocking_errors)}개 BLOCKING 에러"
            )  # SSOT
            return False, errors

        logger.info(f"{PHASE_0_NAME}: Input Validation 통과 ✅")  # SSOT
        return True, errors

    def _validate_required_info(
        self,
        enclosure_material: str | None,
        enclosure_type: str | None,
        breaker_brand: str | None,
        main_breaker: dict | None,
        branch_breakers: list[dict] | None,
    ) -> list[EstimatorError]:
        """필수 정보 누락 검증"""
        errors = []

        # 디버그 로깅: 전달받은 값 확인
        logger.debug(f"_validate_required_info 입력값:")
        logger.debug(f"  enclosure_material: {enclosure_material!r}")
        logger.debug(f"  enclosure_type: {enclosure_type!r}")
        logger.debug(f"  breaker_brand: {breaker_brand!r}")
        logger.debug(f"  main_breaker: {main_breaker!r}")
        logger.debug(f"  branch_breakers: {branch_breakers!r}")

        # INP-001: 외함 종류 (재질)
        if not enclosure_material:
            errors.append(
                ValidationError(
                    error_code=INP_001,
                    field="enclosure_material",
                    value=None,
                    expected="SUS201 1.2T 또는 STEEL 1.6T",
                    phase=PHASE_0_NAME,  # SSOT
                )
            )

        # INP-002: 외함 설치 위치
        if not enclosure_type:
            errors.append(
                ValidationError(
                    error_code=INP_002,
                    field="enclosure_type",
                    value=None,
                    expected="옥내노출, 옥외노출, 매입함, 옥내자립, 옥외자립 중 하나",
                    phase=PHASE_0_NAME,  # SSOT
                )
            )

        # INP-003: 차단기 브랜드 - Optional (API 스키마와 일치)
        # breaker_brand가 없으면 경제형 우선 원칙에 따라 자동 선택
        # if not breaker_brand:
        #     errors.append(
        #         ValidationError(
        #             error_code=INP_003,
        #             field="breaker_brand",
        #             value=None,
        #             expected="상도차단기, LS산전, 현대일렉트릭 중 하나",
        #             phase=PHASE_0_NAME,  # SSOT
        #         )
        #     )

        # INP-004: 메인 차단기
        if not main_breaker:
            errors.append(
                ValidationError(
                    error_code=INP_004,
                    field="main_breaker",
                    value=None,
                    expected="극수, 전류, 프레임 정보 필요",
                    phase=PHASE_0_NAME,  # SSOT
                )
            )

        # INP-005: 분기 차단기 (선택사항 - 메인차단기만 있는 경우도 허용)
        # 분기차단기 없이 메인차단기 1개만 있는 경우도 유효한 견적임
        # 예: 단독 차단기함, 소형 분전반 등

        return errors

    def _validate_mccb_elb_distinction(
        self, breakers: list[dict]
    ) -> list[EstimatorError]:
        """BUG-001: MCCB/ELB 구분 검증"""
        errors = []

        for i, breaker in enumerate(breakers):
            breaker_type = breaker.get("type", "").upper()
            description = breaker.get("description", "")

            # description이 비어있으면 검증 스킵 (API 요청은 is_elb로 명확히 지정)
            if not description:
                continue

            # "누전" 키워드 확인
            has_leakage_keyword = "누전" in description or "ELB" in description.upper()

            # MCCB인데 누전 키워드 있음
            if breaker_type == "MCCB" and has_leakage_keyword:
                errors.append(
                    ValidationError(
                        error_code=BUG_001,
                        field=f"branch_breakers[{i}].type",
                        value="MCCB",
                        expected="ELB",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

            # ELB인데 누전 키워드 없음
            elif breaker_type == "ELB" and not has_leakage_keyword:
                errors.append(
                    ValidationError(
                        error_code=BUG_001,
                        field=f"branch_breakers[{i}].type",
                        value="ELB",
                        expected="MCCB",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        return errors

    def _validate_catalog_existence(
        self, breakers: list[dict], brand: str | None
    ) -> list[EstimatorError]:
        """BUG-002: 카탈로그 존재 여부 검증 (AI Catalog v2)"""
        errors = []

        for _i, breaker in enumerate(breakers):
            poles = breaker.get("poles")
            current = breaker.get("current")
            breaker_type = breaker.get("type", "MCCB")

            # AI Catalog 검색 (빠른 인덱스 검색)
            category = (
                BreakerCategory.ELB if breaker_type == "ELB" else BreakerCategory.MCCB
            )

            result = self.ai_catalog.get_breaker_by_spec(
                category=category,
                poles=poles,
                current_a=current,
            )

            if not result:
                errors.append(
                    CatalogError(
                        error_code=BUG_002,
                        item_type="breaker",
                        search_params={
                            "brand": brand,
                            "poles": poles,
                            "current": current,
                            "type": breaker_type,
                        },
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        return errors

    def _validate_breaker_type_selection(
        self, breakers: list[dict]
    ) -> list[EstimatorError]:
        """BUG-003, BUG-004: 차단기 타입 검증"""
        errors = []

        for i, breaker in enumerate(breakers):
            poles = breaker.get("poles")
            current = breaker.get("current")
            model = breaker.get("model", "")

            # model이 AUTO이거나 비어있으면 검증 스킵 (자동 선택 모드)
            if not model or model == "AUTO":
                continue

            # BUG-003: 2P 20A/30A는 소형 차단기 사용
            if poles == 2 and current in [20, 30]:
                small_models = ["SIE-32", "SIB-32", "SBW-32", "32GRHS", "BS-32"]
                if not any(sm in model for sm in small_models):
                    errors.append(
                        ValidationError(
                            error_code=BUG_003,
                            field=f"branch_breakers[{i}].model",
                            value=model,
                            expected="SIE-32, SIB-32, SBW-32, 32GRHS, BS-32 중 하나",
                            phase=PHASE_0_NAME,  # SSOT
                        )
                    )

            # BUG-004: 2P 40~50A는 컴팩트 타입 사용
            if poles == 2 and 40 <= current <= 50:
                compact_models = ["SEC-52", "SBC-52", "52GRHS", "BS-52"]
                if not any(cm in model for cm in compact_models):
                    errors.append(
                        ValidationError(
                            error_code=BUG_004,
                            field=f"branch_breakers[{i}].model",
                            value=model,
                            expected="SEC-52, SBC-52, 52GRHS, BS-52 중 하나",
                            phase=PHASE_0_NAME,  # SSOT
                        )
                    )

        return errors

    def _validate_main_busbar_spec(
        self, main_breaker: dict, accessories: list[dict]
    ) -> list[EstimatorError]:
        """BUS-001~004: MAIN BUS-BAR 규격 검증"""
        errors = []

        # API와 레거시 호환성: frame_af 또는 frame 키 모두 지원
        frame = main_breaker.get("frame_af") or main_breaker.get("frame")
        if not frame:
            return errors

        # MAIN BUS-BAR 찾기
        main_busbar = None
        for acc in accessories:
            if acc.get("name") == "MAIN BUS-BAR":
                main_busbar = acc
                break

        if not main_busbar:
            return errors  # MAIN BUS-BAR 없으면 검증 스킵 (다른 에러에서 처리)

        spec = main_busbar.get("spec", "")

        # BUS-001: 50~125AF → 3T*15
        if 50 <= frame <= 125:
            if spec != "3T*15":
                errors.append(
                    ValidationError(
                        error_code=BUS_001,
                        field="accessories.MAIN BUS-BAR.spec",
                        value=spec,
                        expected="3T*15",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        # BUS-002: 200~250AF → 5T*20
        elif 200 <= frame <= 250:
            if spec != "5T*20":
                errors.append(
                    ValidationError(
                        error_code=BUS_002,
                        field="accessories.MAIN BUS-BAR.spec",
                        value=spec,
                        expected="5T*20",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        # BUS-003: 400AF → 6T*30
        elif frame == 400:
            if spec != "6T*30":
                errors.append(
                    ValidationError(
                        error_code=BUS_003,
                        field="accessories.MAIN BUS-BAR.spec",
                        value=spec,
                        expected="6T*30",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        # BUS-004: 600~800AF → 8T*40
        elif 600 <= frame <= 800:
            if spec != "8T*40":
                errors.append(
                    ValidationError(
                        error_code=BUS_004,
                        field="accessories.MAIN BUS-BAR.spec",
                        value=spec,
                        expected="8T*40",
                        phase=PHASE_0_NAME,  # SSOT
                    )
                )

        return errors
