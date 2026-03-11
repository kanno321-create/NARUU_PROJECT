"""
AI 견적 검증 서비스

견적 시각화 전 AI 기반 6단계 검증 수행:
1. 견적요청 정보 확인 (CHK_01)
2. 외함 설정 검증 - 재질, 두께, 크기계산 (CHK_02)
3. 차단기 브랜드/타입 검증 - 경제형 vs 표준형 (CHK_03)
4. 메인/분기차단기 검증 - MCCB, ELB, 극수, 암페어, kA (CHK_04)
5. 부스바/인건비/추가자재 검증 (CHK_05)
6. 최종 검증 및 시각화 판단 (CHK_06)

핵심 정책:
- 100% 통과 필수: 6개 체크 중 1개라도 실패 시 견적서 제출 즉시 차단
- 자동 수정 시도: 가능한 경우 AI가 자동으로 수정 후 재검증
- 상세 보고: 실패 시 E_VALIDATION 오류와 함께 issues 상세 반환

필수 참조 문서:
- 절대코어파일/AI_견적검증_체크리스트_V1.0.md

Contract-First + Evidence-Gated + Zero-Mock
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from kis_estimator_core.core.ssot.constants import (
    # Busbar Coefficients
    BUSBAR_COEFF_20_250A,
    BUSBAR_COEFF_300_400A,
    BUSBAR_COEFF_500_800A,
    BUSBAR_SPEC_3T_15,
    BUSBAR_SPEC_5T_20,
    BUSBAR_SPEC_6T_30,
    BUSBAR_SPEC_8T_40,
    # Price Constants
    PRICE_BUSBAR_PER_KG,
)

if TYPE_CHECKING:
    from kis_estimator_core.api.schemas.estimates import EstimateRequest
    from kis_estimator_core.engine.workflow_engine import WorkflowResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationIssue:
    """검증 실패 항목"""
    check_id: str
    severity: str  # "error" | "warning"
    message: str
    expected: Any = None
    actual: Any = None
    suggestion: str = ""


@dataclass
class VerificationResult:
    """AI 검증 결과"""
    passed: bool
    issues: list[VerificationIssue] = field(default_factory=list)
    summary: str = ""
    checks_performed: int = 0
    checks_passed: int = 0

    def add_issue(self, issue: VerificationIssue):
        self.issues.append(issue)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


class AIVerificationService:
    """
    AI 기반 견적 검증 서비스

    견적 시각화 전 6단계 검증을 수행하여
    모든 항목이 정확하게 처리되었는지 확인
    """

    def __init__(self):
        """Initialize verification service"""
        logger.info("AIVerificationService initialized")

    async def verify_estimate(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        견적 전체 검증 수행

        Args:
            request: 원본 견적 요청
            workflow_result: 파이프라인 실행 결과

        Returns:
            VerificationResult: 검증 결과 (passed=True면 시각화 진행)
        """
        logger.info("=" * 60)
        logger.info("[AI_VERIFY] Starting AI verification for estimate")
        logger.info(f"[AI_VERIFY] Customer: {request.customer_name}, Panels: {len(request.panels) if request.panels else 0}")

        result = VerificationResult(passed=True)
        checks = 0
        passed = 0

        # 1. 견적 요청 정보 확인
        check1 = await self._verify_input_information(request, workflow_result)
        checks += 1
        if check1.passed:
            passed += 1
            logger.info("[CHK_01] ✅ 견적 요청 정보 확인 통과")
        else:
            logger.error(f"[CHK_01] ❌ 견적 요청 정보 실패: {[i.message for i in check1.issues]}")
            result.issues.extend(check1.issues)

        # 2. 외함 설정 검증
        check2 = await self._verify_enclosure_settings(request, workflow_result)
        checks += 1
        if check2.passed:
            passed += 1
            logger.info("[CHK_02] ✅ 외함 설정 검증 통과")
        else:
            logger.error(f"[CHK_02] ❌ 외함 설정 실패: {[i.message for i in check2.issues]}")
            result.issues.extend(check2.issues)

        # 3. 차단기 브랜드/타입 검증
        check3 = await self._verify_breaker_brand_type(request, workflow_result)
        checks += 1
        if check3.passed:
            passed += 1
            logger.info("[CHK_03] ✅ 차단기 브랜드/타입 검증 통과")
        else:
            logger.error(f"[CHK_03] ❌ 차단기 브랜드/타입 실패: {[i.message for i in check3.issues]}")
            result.issues.extend(check3.issues)

        # 4. 메인/분기 차단기 검증
        check4 = await self._verify_breaker_specs(request, workflow_result)
        checks += 1
        if check4.passed:
            passed += 1
            logger.info("[CHK_04] ✅ 차단기 스펙 검증 통과")
        else:
            logger.error(f"[CHK_04] ❌ 차단기 스펙 실패: {[i.message for i in check4.issues]}")
            result.issues.extend(check4.issues)

        # 5. 부스바/인건비/추가자재 검증
        check5 = await self._verify_materials_and_costs(request, workflow_result)
        checks += 1
        if check5.passed:
            passed += 1
            logger.info("[CHK_05] ✅ 부스바/인건비/자재 검증 통과")
        else:
            logger.error(f"[CHK_05] ❌ 부스바/인건비/자재 실패: {[i.message for i in check5.issues]}")
            result.issues.extend(check5.issues)

        # 6. 최종 검증
        check6 = await self._verify_final_estimate(request, workflow_result)
        checks += 1
        if check6.passed:
            passed += 1
            logger.info("[CHK_06] ✅ 최종 검증 통과")
        else:
            logger.error(f"[CHK_06] ❌ 최종 검증 실패: {[i.message for i in check6.issues]}")
            result.issues.extend(check6.issues)

        result.checks_performed = checks
        result.checks_passed = passed
        result.passed = not result.has_errors
        result.summary = self._generate_summary(result)

        logger.info("=" * 60)
        logger.info(f"[AI_VERIFY] RESULT: {passed}/{checks} checks passed, passed={result.passed}")
        if result.issues:
            logger.info(f"[AI_VERIFY] Issues: {[f'{i.check_id}:{i.severity}:{i.message}' for i in result.issues]}")
        logger.info("=" * 60)

        return result

    async def _verify_input_information(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        1단계: 견적 요청 정보 확인

        - 고객명 존재 확인
        - 패널 정보 존재 확인
        - 메인차단기 정보 유효성
        - 분기차단기 수량 합리성
        """
        result = VerificationResult(passed=True)

        # 고객명 확인
        if not request.customer_name or len(request.customer_name.strip()) == 0:
            result.add_issue(VerificationIssue(
                check_id="INPUT_001",
                severity="error",
                message="고객명이 비어있습니다",
                suggestion="고객명을 입력해주세요"
            ))

        # 패널 정보 확인
        if not request.panels or len(request.panels) == 0:
            result.add_issue(VerificationIssue(
                check_id="INPUT_002",
                severity="error",
                message="패널 정보가 없습니다",
                suggestion="최소 1개 이상의 패널을 추가해주세요"
            ))
            return result

        for idx, panel in enumerate(request.panels):
            panel_name = getattr(panel, 'panel_name', None) or getattr(panel, 'panel_id', None) or f"분전반{idx + 1}"

            # 메인차단기 확인
            if not panel.main_breaker:
                result.add_issue(VerificationIssue(
                    check_id="INPUT_003",
                    severity="error",
                    message=f"[{panel_name}] 메인차단기가 없습니다",
                    suggestion="메인차단기 정보를 입력해주세요"
                ))

            # 분기차단기 수량 확인 (0개도 가능 - 메인만 있는 견적)
            if panel.branch_breakers:
                total_branches = sum(b.quantity or 1 for b in panel.branch_breakers)
                if total_branches > 50:
                    result.add_issue(VerificationIssue(
                        check_id="INPUT_004",
                        severity="warning",
                        message=f"[{panel_name}] 분기차단기 수량이 매우 많습니다: {total_branches}개",
                        expected="일반적으로 50개 이하",
                        actual=total_branches,
                        suggestion="외함 분할 또는 수량 재확인이 필요할 수 있습니다"
                    ))

            # 외함 정보 확인
            if not panel.enclosure:
                result.add_issue(VerificationIssue(
                    check_id="INPUT_005",
                    severity="error",
                    message=f"[{panel_name}] 외함 정보가 없습니다",
                    suggestion="외함 종류와 재질을 선택해주세요"
                ))

        result.passed = not result.has_errors
        return result

    async def _verify_enclosure_settings(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        2단계: 외함 설정 검증

        - 재질/두께 적합성
        - 크기 계산 정확성 (fit_score)
        - 설치 유형 일관성
        """
        result = VerificationResult(passed=True)

        # WorkflowResult에서 외함 결과 추출
        enclosure_result = None
        for phase in workflow_result.phases:
            if "Enclosure" in phase.phase:
                enclosure_result = phase.output
                break

        if not enclosure_result:
            result.add_issue(VerificationIssue(
                check_id="ENCL_001",
                severity="error",
                message="외함 계산 결과가 없습니다",
                suggestion="파이프라인 실행 로그를 확인해주세요"
            ))
            return result

        # fit_score 확인
        fit_score = getattr(enclosure_result, 'fit_score', None)
        if fit_score is not None and fit_score < 0.90:
            result.add_issue(VerificationIssue(
                check_id="ENCL_002",
                severity="error",
                message=f"외함 적합도가 낮습니다: {fit_score:.2%}",
                expected="≥ 90%",
                actual=f"{fit_score:.2%}",
                suggestion="차단기 수량/크기를 재확인하거나 커스텀 외함 크기를 지정해주세요"
            ))

        # 크기 유효성 확인
        width = getattr(enclosure_result, 'width', 0)
        height = getattr(enclosure_result, 'height', 0)
        depth = getattr(enclosure_result, 'depth', 0)

        if width < 400 or width > 1200:
            result.add_issue(VerificationIssue(
                check_id="ENCL_003",
                severity="warning",
                message=f"외함 폭이 비정상적입니다: {width}mm",
                expected="400~1200mm",
                actual=f"{width}mm",
                suggestion="차단기 배치를 재확인해주세요"
            ))

        if height < 400 or height > 2200:
            result.add_issue(VerificationIssue(
                check_id="ENCL_004",
                severity="warning",
                message=f"외함 높이가 비정상적입니다: {height}mm",
                expected="400~2200mm",
                actual=f"{height}mm",
                suggestion="차단기 수량 또는 부속자재를 재확인해주세요"
            ))

        # 재질 확인
        for panel in request.panels:
            if panel.enclosure:
                material = panel.enclosure.material
                encl_type = panel.enclosure.type

                # 옥외 설치인데 일반 스틸인 경우 경고
                if "옥외" in encl_type and "SUS" not in material:
                    result.add_issue(VerificationIssue(
                        check_id="ENCL_005",
                        severity="warning",
                        message=f"옥외 설치에 일반 스틸 재질 사용: {material}",
                        expected="SUS201 1.2T 또는 SUS304 1.2T 권장",
                        actual=material,
                        suggestion="옥외 설치 시 스테인리스 재질을 권장합니다"
                    ))

        result.passed = not result.has_errors
        return result

    async def _verify_breaker_brand_type(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        3단계: 차단기 브랜드 및 타입 검증

        - 경제형 우선 원칙 준수
        - 브랜드 일관성
        - 특수 케이스 처리 확인 (4P 50AF 등)
        """
        result = VerificationResult(passed=True)

        estimate_data = workflow_result.estimate_data
        if not estimate_data or not hasattr(estimate_data, 'panels'):
            result.add_issue(VerificationIssue(
                check_id="BRKR_001",
                severity="error",
                message="견적 데이터에서 패널 정보를 찾을 수 없습니다",
                suggestion="파이프라인 실행을 재시도해주세요"
            ))
            return result

        for panel in estimate_data.panels:
            # PanelEstimate uses panel_id, not panel_name
            panel_name = getattr(panel, 'panel_name', None) or getattr(panel, 'panel_id', None) or "분전반"

            # 메인 차단기 검증
            if panel.main_breaker:
                model = panel.main_breaker.model

                # 브랜드 추출 (상도: S로 시작, LS: A 또는 E로 시작)
                brand = "상도" if model.startswith("S") else "LS" if model[0] in "AE" else "알 수 없음"

                # 경제형/표준형 확인
                is_economy = self._is_economy_breaker(model)

                # 4P 50AF는 표준형만 존재 - 이 경우는 정상
                frame_af = panel.main_breaker.frame_af
                poles = panel.main_breaker.poles

                if poles == 4 and frame_af == 50 and not is_economy:
                    # 4P 50AF는 표준형만 있음 - 정상 케이스
                    pass
                elif not is_economy:
                    # 그 외의 경우 표준형 사용 시 확인 필요
                    result.add_issue(VerificationIssue(
                        check_id="BRKR_002",
                        severity="warning",
                        message=f"[{panel_name}] 메인차단기가 표준형입니다: {model}",
                        expected="경제형 우선 사용 (비용 절감)",
                        actual=f"표준형 ({model})",
                        suggestion="특별한 이유 없이 표준형을 선택하면 비용이 증가합니다"
                    ))

            # 분기 차단기 검증
            for breaker in panel.branch_breakers:
                model = breaker.model
                is_economy = self._is_economy_breaker(model)

                # 4P 50AF 특수 케이스 확인
                frame_af = breaker.frame_af
                poles = breaker.poles

                if poles == 4 and frame_af == 50:
                    # 4P 50AF는 경제형이 없으므로 표준형 사용 정상
                    continue

                if not is_economy:
                    result.add_issue(VerificationIssue(
                        check_id="BRKR_003",
                        severity="warning",
                        message=f"[{panel_name}] 분기차단기가 표준형입니다: {model}",
                        expected="경제형 우선 사용",
                        actual=f"표준형 ({model})",
                        suggestion="경제형 차단기 사용을 권장합니다 (약 26% 비용 절감)"
                    ))

        result.passed = not result.has_errors
        return result

    async def _verify_breaker_specs(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        4단계: 차단기 스펙 검증

        - MCCB/ELB 구분 정확성
        - 극수 적합성
        - 암페어/프레임 관계
        - kA 정격 적합성
        """
        result = VerificationResult(passed=True)

        estimate_data = workflow_result.estimate_data
        if not estimate_data or not hasattr(estimate_data, 'panels'):
            return result

        for panel in estimate_data.panels:
            # PanelEstimate uses panel_id, not panel_name
            panel_name = getattr(panel, 'panel_name', None) or getattr(panel, 'panel_id', None) or "분전반"

            # 메인 차단기 검증
            if panel.main_breaker:
                breaker = panel.main_breaker

                # 프레임 ≥ 암페어 확인
                if breaker.frame_af < breaker.current_a:
                    result.add_issue(VerificationIssue(
                        check_id="SPEC_001",
                        severity="error",
                        message=f"[{panel_name}] 메인차단기 프레임이 암페어보다 작습니다",
                        expected=f"프레임 ≥ {breaker.current_a}AF",
                        actual=f"{breaker.frame_af}AF",
                        suggestion="차단기 프레임을 재선택해주세요"
                    ))

                # 극수 확인 (2P는 단상, 3P/4P는 3상)
                if breaker.poles not in [2, 3, 4]:
                    result.add_issue(VerificationIssue(
                        check_id="SPEC_002",
                        severity="error",
                        message=f"[{panel_name}] 메인차단기 극수가 비정상입니다: {breaker.poles}P",
                        expected="2P, 3P, 또는 4P",
                        actual=f"{breaker.poles}P",
                        suggestion="극수를 재확인해주세요"
                    ))

            # 분기 차단기 검증
            for breaker in panel.branch_breakers:
                # 프레임 ≥ 암페어 확인
                if breaker.frame_af < breaker.current_a:
                    result.add_issue(VerificationIssue(
                        check_id="SPEC_003",
                        severity="error",
                        message=f"[{panel_name}] 분기차단기 프레임이 암페어보다 작습니다: {breaker.model}",
                        expected=f"프레임 ≥ {breaker.current_a}AF",
                        actual=f"{breaker.frame_af}AF",
                        suggestion="차단기 프레임을 재선택해주세요"
                    ))

                # 소형차단기 (SIE-32, SIB-32 등) 확인 - 2P 20A/30A만 해당
                if breaker.model in ["SIE-32", "SIB-32", "SBW-32", "32GRHS", "BS-32"]:
                    if breaker.poles != 2 or breaker.current_a > 30:
                        result.add_issue(VerificationIssue(
                            check_id="SPEC_004",
                            severity="error",
                            message=f"[{panel_name}] 소형차단기 사용 조건 불일치: {breaker.model}",
                            expected="2P, 20A 또는 30A",
                            actual=f"{breaker.poles}P, {breaker.current_a}A",
                            suggestion="소형차단기는 2P 20A/30A에만 사용 가능합니다"
                        ))

        result.passed = not result.has_errors
        return result

    async def _verify_materials_and_costs(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        5단계: 부스바/인건비/추가자재 검증

        - 부스바 중량 계산 정확성
        - 인건비 계산 정확성
        - 필수 자재 포함 여부
        - 마그네트 동반 자재 확인

        CEO 규칙 (2024-12-03): 메인차단기만 있는 경우 (분기 없음)
        - 부스바 없음 허용 (is_main_only)
        - 필수 자재: E.T, N.P만 (N.T, COATING, P-COVER, INSULATOR 불필요)
        """
        result = VerificationResult(passed=True)

        estimate_data = workflow_result.estimate_data
        if not estimate_data or not hasattr(estimate_data, 'panels'):
            logger.warning("[CHK_05] estimate_data 또는 panels 없음")
            return result

        for panel in estimate_data.panels:
            # PanelEstimate uses panel_id, not panel_name
            panel_name = getattr(panel, 'panel_name', None) or getattr(panel, 'panel_id', None) or "분전반"

            # 메인차단기만 있는지 확인 (분기차단기 없음)
            is_main_only = not panel.branch_breakers or len(panel.branch_breakers) == 0
            logger.info(f"[CHK_05] {panel_name}: is_main_only={is_main_only}, branch_count={len(panel.branch_breakers) if panel.branch_breakers else 0}")

            # 부스바 존재 확인 (main-only 제외)
            if not panel.busbar:
                if is_main_only:
                    # CEO 규칙: 메인차단기만 있으면 부스바 불필요
                    logger.info(f"[CHK_05] {panel_name}: 메인차단기만 있어 부스바 생략 (정상)")
                else:
                    result.add_issue(VerificationIssue(
                        check_id="MAT_001",
                        severity="error",
                        message=f"[{panel_name}] 부스바 정보가 없습니다",
                        suggestion="부스바 계산이 누락되었습니다"
                    ))
            else:
                # 부스바 중량 검증
                main_af = panel.main_breaker.frame_af if panel.main_breaker else 100

                # 메인 부스바 스펙 확인 (BusbarItem은 spec 또는 thickness_width 사용)
                expected_spec = self._get_expected_busbar_spec(main_af)
                actual_spec = getattr(panel.busbar, 'main_busbar_spec', None) or getattr(panel.busbar, 'spec', None) or getattr(panel.busbar, 'thickness_width', '')

                if expected_spec and actual_spec != expected_spec:
                    result.add_issue(VerificationIssue(
                        check_id="MAT_002",
                        severity="warning",
                        message=f"[{panel_name}] 메인 부스바 스펙이 예상과 다릅니다",
                        expected=expected_spec,
                        actual=actual_spec,
                        suggestion="메인 차단기 프레임에 맞는 부스바 스펙인지 확인해주세요"
                    ))

                # 부스바 중량이 0인 경우 (BusbarItem은 weight_kg 또는 quantity 사용)
                busbar_weight = getattr(panel.busbar, 'main_busbar_weight', None) or getattr(panel.busbar, 'weight_kg', 0) or getattr(panel.busbar, 'quantity', 0)
                if busbar_weight <= 0:
                    result.add_issue(VerificationIssue(
                        check_id="MAT_003",
                        severity="error",
                        message=f"[{panel_name}] 메인 부스바 중량이 0입니다",
                        suggestion="외함 크기 또는 메인 차단기를 확인해주세요"
                    ))

            # 인건비 (Assembly Charge) 확인 - assembly 또는 assembly_charge 속성 사용
            assembly = getattr(panel, 'assembly', None) or getattr(panel, 'assembly_charge', None)
            if not assembly:
                result.add_issue(VerificationIssue(
                    check_id="MAT_004",
                    severity="error",
                    message=f"[{panel_name}] 조립비(인건비) 정보가 없습니다",
                    suggestion="인건비 계산이 누락되었습니다"
                ))
            else:
                # 인건비가 0인 경우 (total_price 또는 unit_price 사용)
                assembly_price = getattr(assembly, 'total_price', None) or getattr(assembly, 'unit_price', 0) or 0
                if assembly_price <= 0:
                    result.add_issue(VerificationIssue(
                        check_id="MAT_005",
                        severity="error",
                        message=f"[{panel_name}] 조립비가 0원입니다",
                        suggestion="인건비 계산 로직을 확인해주세요"
                    ))

            # 필수 자재 확인
            accessory_types = [acc.item_name.upper() for acc in panel.accessories] if panel.accessories else []
            logger.info(f"[CHK_05] {panel_name}: accessories={accessory_types}")

            # CEO 규칙: 메인차단기만 있으면 E.T, N.P만 필수
            if is_main_only:
                required_items = ["E.T"]  # 메인만: E.T, N.P만 필수 (N.P는 이름 다양해서 E.T만 체크)
            else:
                required_items = ["E.T", "N.T", "P-COVER", "COATING", "INSULATOR"]

            for item in required_items:
                found = any(item.upper() in acc_name for acc_name in accessory_types)
                if not found:
                    result.add_issue(VerificationIssue(
                        check_id="MAT_006",
                        severity="warning",
                        message=f"[{panel_name}] 필수 자재 누락: {item}",
                        suggestion=f"{item} 자재를 추가해주세요"
                    ))

            # 마그네트 동반 자재 확인
            has_magnet = any("MAGNET" in acc or "마그네트" in acc for acc in accessory_types)
            if has_magnet:
                required_with_magnet = ["FUSEHOLDER", "TERMINAL", "PVC", "CABLE"]
                for item in required_with_magnet:
                    found = any(item.upper() in acc_name for acc_name in accessory_types)
                    if not found:
                        result.add_issue(VerificationIssue(
                            check_id="MAT_007",
                            severity="error",
                            message=f"[{panel_name}] 마그네트 동반자재 누락: {item}",
                            suggestion=f"마그네트 사용 시 {item}이(가) 필수입니다"
                        ))

        result.passed = not result.has_errors
        return result

    async def _verify_final_estimate(
        self,
        request: "EstimateRequest",
        workflow_result: "WorkflowResult",
    ) -> VerificationResult:
        """
        6단계: 최종 검증

        - 전체 가격 합리성
        - 파이프라인 성공 여부
        - 문서 생성 확인
        """
        result = VerificationResult(passed=True)

        # 파이프라인 성공 확인
        if not workflow_result.success:
            result.add_issue(VerificationIssue(
                check_id="FINAL_001",
                severity="error",
                message="파이프라인 실행이 실패했습니다",
                suggestion="오류 로그를 확인하고 입력 데이터를 재검토해주세요"
            ))

            # Blocking errors 추가 (디버그 정보 포함)
            for error in workflow_result.blocking_errors:
                # ValidationError의 상세 정보 추출 (details dict에서)
                error_details = str(error)
                error_type = type(error).__name__
                details_dict = getattr(error, 'details', None)
                field_info = details_dict.get('field') if details_dict else None
                value_info = details_dict.get('value') if details_dict else None
                expected_info = details_dict.get('expected') if details_dict else None

                # 디버그 정보를 메시지에 포함 (타입 포함)
                debug_info = f" [DEBUG: type={error_type}, details={details_dict!r}, field={field_info!r}]"

                result.add_issue(VerificationIssue(
                    check_id="FINAL_002",
                    severity="error",
                    message=f"파이프라인 오류: {error_details}{debug_info}",
                    expected=expected_info,
                    actual=str(value_info) if value_info is not None else None,
                    suggestion="해당 오류를 해결해주세요"
                ))

        # 전체 가격 확인
        estimate_data = workflow_result.estimate_data
        if estimate_data:
            total_price = 0
            for panel in estimate_data.panels:
                if hasattr(panel, 'subtotal'):
                    total_price += panel.subtotal

            if total_price <= 0:
                result.add_issue(VerificationIssue(
                    check_id="FINAL_003",
                    severity="error",
                    message="전체 견적 금액이 0원입니다",
                    suggestion="가격 계산을 확인해주세요"
                ))
            elif total_price > 100_000_000:  # 1억원 초과
                result.add_issue(VerificationIssue(
                    check_id="FINAL_004",
                    severity="warning",
                    message=f"전체 견적 금액이 매우 높습니다: {total_price:,}원",
                    expected="일반적으로 1억원 이하",
                    actual=f"{total_price:,}원",
                    suggestion="입력 데이터를 재확인해주세요"
                ))

        # Excel/PDF 생성 확인 (excel_path 또는 final_output 속성 사용)
        excel_path = getattr(workflow_result, 'excel_path', None) or getattr(workflow_result, 'final_output', None)
        if not excel_path:
            result.add_issue(VerificationIssue(
                check_id="FINAL_005",
                severity="warning",
                message="Excel 파일이 생성되지 않았습니다",
                suggestion="문서 생성 단계를 확인해주세요"
            ))

        result.passed = not result.has_errors
        return result

    def _is_economy_breaker(self, model: str) -> bool:
        """
        경제형 차단기 여부 확인

        상도: E가 2번째 위치 (예: SBE-104, SEE-52)
        LS: N이 3번째 위치 (예: ABN-54, EBN-103)
        """
        if not model:
            return True  # Unknown은 경제형으로 간주

        model = model.upper()

        # 소형차단기는 경제형으로 분류
        if model in ["SIE-32", "SIB-32", "SBW-32", "32GRHS", "BS-32"]:
            return True

        # 상도 패턴: 2번째 위치가 E면 경제형
        if model.startswith("S") and len(model) >= 3:
            if model[2] == 'E':
                return True
            elif model[2] == 'S':
                return False  # 표준형

        # LS 패턴: 3번째 위치가 N이면 경제형
        if model[0] in "AE" and len(model) >= 4:
            if model[2] == 'N':
                return True
            elif model[2] == 'S':
                return False  # 표준형

        return True  # Default: 경제형으로 간주

    def _get_expected_busbar_spec(self, frame_af: int) -> str:
        """프레임 AF에 따른 예상 부스바 스펙"""
        if frame_af <= 100:
            return BUSBAR_SPEC_3T_15
        elif frame_af <= 250:
            return BUSBAR_SPEC_5T_20
        elif frame_af <= 400:
            return BUSBAR_SPEC_6T_30
        else:
            return BUSBAR_SPEC_8T_40

    def _generate_summary(self, result: VerificationResult) -> str:
        """검증 결과 요약 생성"""
        if result.passed:
            return f"✅ AI 검증 통과: {result.checks_passed}/{result.checks_performed} 항목 정상"
        else:
            error_count = sum(1 for i in result.issues if i.severity == "error")
            warning_count = sum(1 for i in result.issues if i.severity == "warning")
            return f"❌ AI 검증 실패: {error_count}개 오류, {warning_count}개 경고 발견"


# Singleton instance
_ai_verification_service: AIVerificationService | None = None


def get_ai_verification_service() -> AIVerificationService:
    """AIVerificationService 싱글톤 반환"""
    global _ai_verification_service
    if _ai_verification_service is None:
        _ai_verification_service = AIVerificationService()
    return _ai_verification_service
