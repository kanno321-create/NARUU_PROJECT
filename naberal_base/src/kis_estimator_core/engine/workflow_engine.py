"""
Workflow Engine: FIX-4 Pipeline Orchestration
Phase 0→1→2→3 자동 실행 및 에러 게이트

핵심 원칙:
1. Phase 순차 실행 (0→1→2→3)
2. 각 Phase 시작 전 에러 게이트 검증
3. BLOCKING 에러 발생 시 즉시 중단
4. 모든 Phase 결과 수집 및 반환
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kis_estimator_core.core.ssot.constants_format import UNIT_ACCESSORY

from ..errors import (
    EstimatorError,
    PhaseBlockedError,
    ValidationError,
)
from .breaker_placer import BreakerPlacer
from .enclosure_solver import EnclosureSolver
from .data_transformer import DataTransformer
from .excel_generator import ExcelGenerator
from .input_validator import InputValidator
from .validator import Validator

logger = logging.getLogger(__name__)


@dataclass
class PhaseResult:
    """각 Phase 실행 결과"""

    phase: str
    success: bool
    errors: list[EstimatorError]
    warnings: list[str]
    output: Any | None = None
    estimate_data: Any | None = None  # EstimateData 객체 (Phase 3 등에서 사용)


@dataclass
class WorkflowResult:
    """전체 Workflow 실행 결과"""

    success: bool
    phases: list[PhaseResult]
    final_output: Path | None = None
    blocking_errors: list[EstimatorError] = None
    estimate_data: Any | None = None  # 최종 EstimateData 객체

    def __post_init__(self):
        if self.blocking_errors is None:
            self.blocking_errors = []


class WorkflowEngine:
    """
    FIX-4 Pipeline 오케스트레이터

    실행 순서:
    Phase 0: Input Validation (InputValidator)
    Phase 1: Enclosure Calculation (EnclosureSolver)
    Phase 2: Breaker Placement (BreakerPlacer)
    Phase 3: Excel Generation & Validation (ExcelGenerator + Validator)
    """

    def __init__(
        self,
        catalog_path: Path | None = None,
        template_path: Path | None = None,
    ):
        """
        Args:
            catalog_path: 카탈로그 파일 경로 (Excel/CSV)
            template_path: Excel 템플릿 경로
        """
        # 프로젝트 루트 자동 감지 (Railway/로컬 모두 지원)
        # workflow_engine.py 위치: src/kis_estimator_core/engine/workflow_engine.py
        # 프로젝트 루트: 4단계 상위
        project_root = Path(__file__).parent.parent.parent.parent

        # 카탈로그 파일 경로 (Excel 또는 CSV)
        self.catalog_path = catalog_path
        if self.catalog_path is None:
            # 우선순위: Excel > CSV
            xlsx_path = project_root / "절대코어파일" / "중요ai단가표.xlsx"
            csv_path = project_root / "절대코어파일" / "중요ai단가표의_2.0V.csv"
            if xlsx_path.exists():
                self.catalog_path = xlsx_path
            elif csv_path.exists():
                self.catalog_path = csv_path
            else:
                # 폴백: ai_catalog_v1.json 사용
                json_path = project_root / "절대코어파일" / "ai_catalog_v1.json"
                if json_path.exists():
                    self.catalog_path = json_path
                else:
                    logger.warning(f"카탈로그 파일을 찾을 수 없습니다. 검색 경로: {project_root / '절대코어파일'}")
                    self.catalog_path = xlsx_path  # 기본값 (오류 발생 시 명확한 경로 표시)

        # 템플릿 경로
        self.template_path = template_path or (
            project_root / "절대코어파일" / "견적서양식.xlsx"
        )

        logger.info(f"WorkflowEngine paths - catalog: {self.catalog_path}, template: {self.template_path}")

        # Phase별 엔진 초기화
        self.input_validator = InputValidator(catalog_path=self.catalog_path)
        self.enclosure_solver = EnclosureSolver()
        self.breaker_placer = BreakerPlacer()
        self.data_transformer = DataTransformer()
        self.excel_generator = ExcelGenerator(template_path=self.template_path)
        self.validator = Validator(template_path=self.template_path)

        logger.info("WorkflowEngine initialized")

    async def execute(
        self,
        enclosure_material: str | None = None,
        enclosure_type: str | None = None,
        breaker_brand: str | None = None,
        main_breaker: dict | None = None,
        branch_breakers: list[dict] | None = None,
        accessories: list[dict] | None = None,
        output_path: Path | None = None,
        customer_name: str | None = None,
        project_name: str | None = None,
    ) -> WorkflowResult:
        """
        FIX-4 Pipeline 전체 실행

        Args:
            enclosure_material: 외함 재질 (예: "SUS201 1.2T")
            enclosure_type: 외함 종류 (예: "옥내노출")
            breaker_brand: 차단기 브랜드 (예: "상도차단기")
            main_breaker: 메인 차단기 정보
            branch_breakers: 분기 차단기 목록
            accessories: 부속자재 목록
            output_path: 출력 Excel 파일 경로
            customer_name: 고객사명 (표지에 사용)
            project_name: 프로젝트명 (표지에 사용)

        Returns:
            WorkflowResult: 전체 실행 결과
        """
        logger.info("=== FIX-4 Pipeline 시작 ===")

        phases: list[PhaseResult] = []
        blocking_errors: list[EstimatorError] = []

        # ================================
        # Phase 0: Input Validation
        # ================================
        phase0_result = self._execute_phase0(
            enclosure_material=enclosure_material,
            enclosure_type=enclosure_type,
            breaker_brand=breaker_brand,
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=accessories,
        )
        phases.append(phase0_result)

        if not phase0_result.success:
            blocking_errors.extend(phase0_result.errors)
            logger.error(f"Phase 0 실패: {len(blocking_errors)}개 BLOCKING 에러")
            return WorkflowResult(
                success=False,
                phases=phases,
                blocking_errors=blocking_errors,
            )

        logger.info("Phase 0: Input Validation ✅")

        # ================================
        # Phase 1: Enclosure Calculation
        # ================================
        phase1_result = await self._execute_phase1(
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            enclosure_type=enclosure_type,
        )
        phases.append(phase1_result)

        if not phase1_result.success:
            blocking_errors.extend(phase1_result.errors)
            logger.error(f"Phase 1 실패: {len(blocking_errors)}개 BLOCKING 에러")
            return WorkflowResult(
                success=False,
                phases=phases,
                blocking_errors=blocking_errors,
            )

        enclosure = phase1_result.output
        # EnclosureResult 객체에서 spec 문자열 생성
        spec_str = f"{enclosure.dimensions.width_mm}×{enclosure.dimensions.height_mm}×{enclosure.dimensions.depth_mm}"
        logger.info(f"Phase 1: Enclosure Calculation ✅ ({spec_str})")

        # ================================
        # Phase 2: Breaker Placement
        # ================================
        phase2_result = self._execute_phase2(
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            enclosure=enclosure,
        )
        phases.append(phase2_result)

        if not phase2_result.success:
            blocking_errors.extend(phase2_result.errors)
            logger.error(f"Phase 2 실패: {len(blocking_errors)}개 BLOCKING 에러")
            return WorkflowResult(
                success=False,
                phases=phases,
                blocking_errors=blocking_errors,
            )

        placement = phase2_result.output
        logger.info("Phase 2: Breaker Placement ✅")

        # ================================
        # Phase 3: Excel Generation & Validation
        # ================================
        phase3_result = self._execute_phase3(
            enclosure=enclosure,
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            placement=placement,
            accessories=accessories,
            output_path=output_path,
            customer_name=customer_name,
            project_name=project_name,
        )
        phases.append(phase3_result)

        if not phase3_result.success:
            blocking_errors.extend(phase3_result.errors)
            logger.error(f"Phase 3 실패: {len(blocking_errors)}개 BLOCKING 에러")
            return WorkflowResult(
                success=False,
                phases=phases,
                blocking_errors=blocking_errors,
            )

        final_excel_path = phase3_result.output
        estimate_data = phase3_result.estimate_data
        logger.info(f"Phase 3: Excel Generation & Validation ✅ ({final_excel_path})")

        # ================================
        # 최종 결과 반환
        # ================================
        logger.info("=== FIX-4 Pipeline 완료 ✅ ===")
        return WorkflowResult(
            success=True,
            phases=phases,
            final_output=final_excel_path,
            blocking_errors=[],
            estimate_data=estimate_data,
        )

    def _execute_phase0(
        self,
        enclosure_material: str | None,
        enclosure_type: str | None,
        breaker_brand: str | None,
        main_breaker: dict | None,
        branch_breakers: list[dict] | None,
        accessories: list[dict] | None,
    ) -> PhaseResult:
        """Phase 0: Input Validation"""
        logger.info("Phase 0: Input Validation 시작")

        try:
            passed, errors = self.input_validator.validate(
                enclosure_material=enclosure_material,
                enclosure_type=enclosure_type,
                breaker_brand=breaker_brand,
                main_breaker=main_breaker,
                branch_breakers=branch_breakers,
                accessories=accessories,
            )

            if not passed:
                return PhaseResult(
                    phase="phase_0",
                    success=False,
                    errors=errors,
                    warnings=[],
                )

            return PhaseResult(
                phase="phase_0",
                success=True,
                errors=[],
                warnings=[],
            )

        except Exception as e:
            logger.exception(f"Phase 0 실행 중 예외 발생: {e}")
            # 예외를 ValidationError로 래핑하여 blocking_errors에 포함
            from ..errors import INP_001
            wrapped_error = ValidationError(
                error_code=INP_001,
                field="phase0_execution",
                value=str(e),
                expected="No exceptions",
                phase="phase_0",
            )
            return PhaseResult(
                phase="phase_0",
                success=False,
                errors=[wrapped_error],
                warnings=[f"예외 발생: {e}"],
            )

    async def _execute_phase1(
        self,
        main_breaker: dict,
        branch_breakers: list[dict],
        enclosure_type: str,
    ) -> PhaseResult:
        """Phase 1: Enclosure Calculation (실물 EnclosureSolver 연동)"""
        logger.info("Phase 1: Enclosure Calculation 시작 (실물 엔진)")

        try:
            from ..models.enclosure import BreakerSpec, CustomerRequirements

            # Dict → BreakerSpec 변환
            main_spec = BreakerSpec(
                id=main_breaker.get("id", "MAIN"),
                model=main_breaker.get("model", "AUTO"),
                poles=main_breaker["poles"],
                current_a=main_breaker["current"],
                frame_af=main_breaker.get("frame") or main_breaker.get("frame_af", 100),
            )

            # quantity 만큼 BreakerSpec 확장 (외함 높이 계산에 개수 반영 필수)
            branch_specs = []
            spec_index = 0
            for b in branch_breakers:
                quantity = b.get("quantity", 1)
                for q in range(quantity):
                    branch_specs.append(
                        BreakerSpec(
                            id=b.get("id", f"B{spec_index+1}"),
                            model=b.get("model", "AUTO"),
                            poles=b["poles"],
                            current_a=b["current"],
                            frame_af=b.get("frame") or b.get("frame_af", 50),
                        )
                    )
                    spec_index += 1

            # CustomerRequirements 생성
            customer_req = CustomerRequirements(
                enclosure_type=enclosure_type,
                voltage_system="3상4선",
            )

            # 실물 EnclosureSolver 실행
            logger.info("EnclosureSolver.solve() 호출 (실물 지식파일 기반)")
            enclosure_result = await self.enclosure_solver.solve(
                main_breaker=main_spec,
                branch_breakers=branch_specs,
                accessories=[],
                customer_requirements=customer_req,
            )

            # Quality Gate 검증
            if not enclosure_result.quality_gate.passed:
                logger.warning(
                    f"Phase 1 Quality Gate 실패: {enclosure_result.quality_gate.name} "
                    f"(threshold: {enclosure_result.quality_gate.threshold} {enclosure_result.quality_gate.operator}, "
                    f"actual: {enclosure_result.quality_gate.actual})"
                )

            # EnclosureResult 객체 반환
            logger.info(
                f"Phase 1 완료: {enclosure_result.dimensions.width_mm}x{enclosure_result.dimensions.height_mm}, fit_score={enclosure_result.quality_gate.actual}"
            )

            # fit_score < 0.9는 WARNING (주문제작 가능하므로 BLOCKING 아님)
            phase1_warnings = []
            if not enclosure_result.quality_gate.passed:
                phase1_warnings.append(
                    f"Quality gate failed: {enclosure_result.quality_gate.name} "
                    f"(threshold: {enclosure_result.quality_gate.threshold}, actual: {enclosure_result.quality_gate.actual})"
                )

            return PhaseResult(
                phase="phase_1",
                success=True,  # fit_score < 0.9도 성공 (주문제작 가능)
                errors=[],
                warnings=phase1_warnings,
                output=enclosure_result,
            )

        except ValidationError as e:
            # ENC-001, ENC-002, ENC-003 에러 처리
            logger.error(f"Phase 1 ValidationError: {e.error_code.code}")
            return PhaseResult(
                phase="phase_1",
                success=False,
                errors=[e],
                warnings=[],
            )

        except Exception as e:
            logger.exception(f"Phase 1 실행 중 예외 발생: {e}")
            # 일반 예외를 ValidationError로 래핑
            from ..errors import ENC_001

            wrapped_error = ValidationError(
                error_code=ENC_001,
                field="phase1_execution",
                value=str(e),
                expected="No exceptions",
                phase="phase_1",
            )
            return PhaseResult(
                phase="phase_1",
                success=False,
                errors=[wrapped_error],
                warnings=[],
            )

    def _execute_phase2(
        self,
        main_breaker: dict,
        branch_breakers: list[dict],
        enclosure: Any,  # EnclosureResult object
    ) -> PhaseResult:
        """Phase 2: Breaker Placement (실물 BreakerPlacer 연동)"""
        logger.info("Phase 2: Breaker Placement 시작 (실물 엔진)")

        try:
            from .breaker_placer import BreakerInput, PanelSpec

            # 현재는 프레임별 표준 치수 사용 (임시)
            def get_breaker_dimensions(frame: int, poles: int) -> tuple:
                """프레임과 극수 기반 표준 치수 반환"""
                if frame <= 50:
                    width = 50 if poles == 2 else (75 if poles == 3 else 100)
                    height = 130
                    depth = 60
                elif frame <= 125:
                    width = 50 if poles == 2 else (75 if poles == 3 else 100)
                    height = 130
                    depth = 60
                elif frame <= 250:
                    width = 70 if poles == 2 else (105 if poles == 3 else 140)
                    height = 165
                    depth = 60
                elif frame <= 400:
                    width = 140 if poles == 3 else 187
                    height = 257
                    depth = 109
                else:  # 600~800AF
                    width = 210 if poles == 3 else 280
                    height = 280
                    depth = 109
                return width, height, depth

            # 모든 차단기 (메인 + 분기) BreakerInput 변환
            # quantity 확장: quantity=3이면 3개의 BreakerInput 생성
            all_breakers = [main_breaker] + branch_breakers
            breaker_inputs = []

            for breaker in all_breakers:
                frame_af = breaker.get("frame") or breaker.get("frame_af", 100)
                width, height, depth = get_breaker_dimensions(
                    frame_af, breaker["poles"]
                )
                model = breaker.get("model", "")  # 모델명 전달 (SIB-32, SBE-104 등)
                quantity = breaker.get("quantity", 1)  # 수량 (기본 1)

                # quantity만큼 BreakerInput 생성 (메인차단기는 항상 1개)
                is_main = (breaker == main_breaker)
                num_to_create = 1 if is_main else quantity

                for i in range(num_to_create):
                    breaker_inputs.append(
                        BreakerInput(
                            id=breaker.get("id", f"B{len(breaker_inputs)+1}"),
                            poles=breaker["poles"],
                            current_a=breaker["current"],
                            width_mm=width,
                            height_mm=height,
                            depth_mm=depth,
                            model=model,  # 모델명 전달 (DataTransformer로 전파)
                            is_main=is_main,  # FIX: 2P 메인차단기 정확히 인식
                        )
                    )

            # EnclosureResult Object → PanelSpec 변환
            panel_spec = PanelSpec(
                width_mm=enclosure.dimensions.width_mm,
                height_mm=enclosure.dimensions.height_mm,
                depth_mm=enclosure.dimensions.depth_mm,
                clearance_mm=20,
            )

            # 실물 BreakerPlacer 실행
            logger.info("BreakerPlacer.place() 호출 (실물 OR-Tools 또는 휴리스틱)")
            placements = self.breaker_placer.place(
                breakers=breaker_inputs,
                panel=panel_spec,
            )

            # 검증 (PhaseBlockedError 발생 가능)
            validation = self.breaker_placer.validate(placements)

            diff_max = (
                validation.phase_imbalance_pct
            )  # 개수 차이 (필드명 유지, 값은 diff_max)

            if not validation.is_valid:
                logger.warning(
                    f"Phase 2 검증 실패: "
                    f"diff_max={int(diff_max)} (개수 차이), "
                    f"clearance_violations={validation.clearance_violations}"
                )

            # PlacementResult → Dict 변환 (model 포함!)
            placement_dict = {
                "placements": [
                    {
                        "breaker_id": p.breaker_id,
                        "position": p.position,
                        "phase": p.phase,
                        "current_a": p.current_a,
                        "poles": p.poles,
                        "model": p.model,  # BUG-003: 모델명 전달 필수!
                    }
                    for p in placements
                ],
                "phase_balance": diff_max,  # 개수 기반 (diff_max, 필드명 유지)
                "clearance_violations": validation.clearance_violations,
                "is_valid": validation.is_valid,
            }

            logger.info(
                f"Phase 2 완료 (개수 기반): diff_max={int(diff_max)}, "
                f"clearance_violations={validation.clearance_violations}"
            )

            # Phase 2 성공 (BLOCKING 에러 없으면 성공, 경고만 있음)
            return PhaseResult(
                phase="phase_2",
                success=True,  # No BLOCKING errors (PhaseBlockedError 미발생)
                errors=[],
                warnings=validation.errors if not validation.is_valid else [],
                output=placement_dict,
            )

        except PhaseBlockedError as e:
            # LAY-001, LAY-002, LAY-004 BLOCKING 에러 처리
            logger.error(f"Phase 2 차단: {len(e.blocking_errors)}개 BLOCKING 에러")
            return PhaseResult(
                phase="phase_2",
                success=False,
                errors=e.blocking_errors,
                warnings=[],
            )

        except ValidationError as e:
            # LAY-003 또는 기타 ValidationError 처리
            logger.error(f"Phase 2 ValidationError: {e.error_code.code}")
            return PhaseResult(
                phase="phase_2",
                success=False,
                errors=[e],
                warnings=[],
            )

        except Exception as e:
            logger.exception(f"Phase 2 실행 중 예외 발생: {e}")
            # 일반 예외를 ValidationError로 래핑
            from ..errors import LAY_001

            wrapped_error = ValidationError(
                error_code=LAY_001,
                field="phase2_execution",
                value=str(e),
                expected="No exceptions",
                phase="phase_2",
            )
            return PhaseResult(
                phase="phase_2",
                success=False,
                errors=[wrapped_error],
                warnings=[],
            )

    def _execute_phase3(
        self,
        enclosure: Any,  # EnclosureResult object
        main_breaker: dict,
        branch_breakers: list[dict],
        placement: dict,
        accessories: list[dict] | None,
        output_path: Path | None,
        customer_name: str | None = None,
        project_name: str | None = None,
    ) -> PhaseResult:
        """Phase 3: Excel Generation & Validation (DataTransformer + ExcelGenerator)"""
        logger.info("Phase 3: Excel Generation & Validation 시작")

        try:
            from ..models.enclosure import BreakerSpec

            # Dict → BreakerSpec 변환 (DataTransformer용)
            # BUG-FIX: 메인 차단기 id를 BreakerInput과 일치시켜야 함
            # BreakerInput: B1(메인), B2(분기1), B3(분기2)...
            # BreakerSpec도 동일한 id 사용 (B1부터 시작)
            main_spec = BreakerSpec(
                id=main_breaker.get("id", "B1"),  # "MAIN" → "B1" 통일
                model=main_breaker.get("model", "AUTO"),
                poles=main_breaker["poles"],
                current_a=main_breaker["current"],
                frame_af=main_breaker.get("frame") or main_breaker.get("frame_af", 100),
            )

            # quantity 만큼 BreakerSpec 확장 (DataTransformer에도 실제 개수 반영 필수)
            branch_specs = []
            spec_index = 1  # 메인이 B1이므로 분기는 B2부터 시작
            for b in branch_breakers:
                quantity = b.get("quantity", 1)
                for q in range(quantity):
                    branch_specs.append(
                        BreakerSpec(
                            id=b.get("id", f"B{spec_index+1}"),
                            model=b.get("model", "AUTO"),
                            poles=b["poles"],
                            current_a=b["current"],
                            frame_af=b.get("frame") or b.get("frame_af", 50),
                        )
                    )
                    spec_index += 1

            # DataTransformer를 사용하여 EstimateData 생성 (Phase 2.1 -> 3)
            # placement는 dict 형태 {"placements": [...], ...}
            # transform()에는 placements 리스트만 전달
            placement_list = placement.get("placements", [])
            logger.info(f"DataTransformer.transform() 호출: {len(placement_list)} placements")
            estimate_data = self.data_transformer.transform(
                placements=placement_list,
                enclosure_result=enclosure,
                breakers=[main_spec] + branch_specs,
                customer_name=customer_name or "고객사",
                project_name=project_name or "프로젝트",
            )
            
            # Excel 생성
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(f"outputs/estimate_{timestamp}.xlsx")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info("ExcelGenerator.generate() 호출 (실물 템플릿 기반)")
            excel_path = self.excel_generator.generate(
                data=estimate_data,
                output_path=output_path,
            )

            # Validation 실행
            logger.info("Validator.validate() 호출 (CAL-001, CAL-002 검증)")
            validation_report = self.validator.validate(excel_path=excel_path)

            if not validation_report.passed:
                logger.warning(
                    f"Phase 3 검증 실패: "
                    f"violations={len(validation_report.violations)}, "
                    f"warnings={len(validation_report.warnings)}"
                )
                # ValidationError가 이미 raise되었을 것이므로 여기 도달하지 않음
                return PhaseResult(
                    phase="phase_3",
                    success=False,
                    errors=[],
                    warnings=validation_report.warnings,
                )

            logger.info(f"Phase 3 완료: {excel_path}")

            return PhaseResult(
                phase="phase_3",
                success=True,
                errors=[],
                warnings=validation_report.warnings,
                output=excel_path,
                estimate_data=estimate_data,  # EstimateData 반환
            )

        except ValidationError as e:
            # CAL-001 또는 CAL-002 에러
            logger.error(f"Phase 3 검증 실패: {e.error_code.code}")
            return PhaseResult(
                phase="phase_3",
                success=False,
                errors=[e],
                warnings=[],
            )

        except Exception as e:
            logger.exception(f"Phase 3 실행 중 예외 발생: {e}")
            # 일반 예외를 ValidationError로 래핑
            from ..errors import CAL_001

            wrapped_error = ValidationError(
                error_code=CAL_001,
                field="phase3_execution",
                value=str(e),
                expected="No exceptions",
                phase="phase_3",
            )
            return PhaseResult(
                phase="phase_3",
                success=False,
                errors=[wrapped_error],
                warnings=[],
            )
