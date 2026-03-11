"""
Stage 3: Estimate Formatter - FIX-4 Pipeline
Excel/PDF 견적서 생성 엔진

입력: Stage 1 (EnclosureResult) + Stage 2 (List[PlacementResult]) + 원본 차단기 정보
출력: Excel 견적서 + PDF (선택적) + ValidationReport

SPEC KIT 기준:
- 실물 템플릿 기반 (목업 절대 금지)
- 수식 보존 100% (openpyxl data_only=False)
- 네임드 범위 손상 0
- 크로스 시트 참조 정확성 100%

성능 목표:
- 전체: < 2s (목표), < 5s (최대)
- Excel 생성: < 1s
- PDF 변환: < 500ms
"""

import logging
from datetime import datetime
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

from .data_transformer import DataTransformer
from .excel_generator import ExcelGenerator
from .models import (
    EstimateOutput,
)
from .pdf_converter import PDFConverter
from .pdf_generator import PDFGenerator
from .validator import Validator

logger = logging.getLogger(__name__)


class EstimateFormatter:
    """
    견적서 생성 메인 클래스 (Stage 3)

    파이프라인:
    1. DataTransformer: Stage 출력 → EstimateData
    2. ExcelGenerator: EstimateData → Excel 파일
    3. PDFConverter: Excel → PDF (선택적)
    4. Validator: 품질 검증
    """

    def __init__(self, template_path: Path | None = None):
        """
        Args:
            template_path: Excel 템플릿 경로 (None이면 기본 경로 사용)

        실물 Supabase 카탈로그 사용 (목업 금지)
        """
        if template_path is None:
            # 프로젝트 루트 자동 감지 (Railway/로컬 모두 지원)
            # estimate_formatter.py 위치: src/kis_estimator_core/engine/estimate_formatter.py
            project_root = Path(__file__).parent.parent.parent.parent
            template_path = project_root / "절대코어파일" / "견적서양식.xlsx"

        if not template_path.exists():
            raise_error(
                ErrorCode.E_INTERNAL,
                f"템플릿 파일이 없습니다: {template_path}\n"
                f"실물 템플릿 파일이 필요합니다. (목업 절대 금지)",
            )

        self.template_path = template_path

        # 컴포넌트 초기화 (실물 Supabase CatalogService 사용)
        self.transformer = DataTransformer()  # 실물 Supabase 연동
        self.excel_generator = ExcelGenerator(template_path=self.template_path)
        self.pdf_converter = PDFConverter()  # 레거시 (Excel → PDF)
        self.pdf_generator = PDFGenerator()  # Phase X: reportlab 기반 PDF 생성
        self.validator = Validator(template_path=self.template_path)

        logger.info(f"EstimateFormatter initialized with template: {template_path}")

    def format(
        self,
        enclosure_result,  # Stage 1 출력
        placements: list,  # Stage 2 출력 (List[PlacementResult])
        breakers: list,  # 원본 차단기 입력 (BreakerInput)
        customer_name: str,
        project_name: str = "",
        output_dir: Path | None = None,
        generate_pdf: bool = False,
    ) -> EstimateOutput:
        """
        견적서 생성 메인 메서드

        Args:
            enclosure_result: Stage 1 Enclosure Solver 출력
            placements: Stage 2 Breaker Placer 출력
            breakers: 원본 차단기 입력 리스트
            customer_name: 고객명
            project_name: 프로젝트명
            output_dir: 출력 디렉토리 (None이면 evidence/ 사용)
            generate_pdf: PDF 생성 여부

        Returns:
            EstimateOutput: Excel/PDF 경로 + 검증 보고서
        """
        logger.info(
            f"Starting estimate generation: {customer_name}, {len(breakers)} breakers"
        )

        # 1. 데이터 변환 (Stage 출력 → EstimateData)
        # placements를 직접 사용 (CriticResult 불필요)
        estimate_data = self.transformer.transform(
            placements=placements,
            enclosure_result=enclosure_result,
            breakers=breakers,
            customer_name=customer_name,
            project_name=project_name,
        )

        # 2. 출력 경로 설정
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            output_dir = project_root / "spec_kit" / "evidence" / "estimates"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = output_dir / f"estimate_{timestamp}.xlsx"

        # 3. Excel 생성
        try:
            excel_path = self.excel_generator.generate(estimate_data, excel_path)
            logger.info(f"Excel 생성 완료: {excel_path}")
        except Exception as e:
            logger.error(f"Excel 생성 실패: {e}")
            raise

        # 4. 검증 (MANDATORY)
        try:
            validation_report = self.validator.validate(excel_path)

            # 검증 실패 시 차단
            if not validation_report.formula_preservation:
                raise_error(ErrorCode.E_INTERNAL, "수식 보존 실패: 견적 생성 차단")
            if not validation_report.cross_references_valid:
                raise_error(ErrorCode.E_INTERNAL, "크로스 참조 오류: 견적 생성 차단")

            logger.info("검증 통과 ✅")

        except Exception as e:
            logger.error(f"검증 실패: {e}")
            raise

        # 5. PDF 생성 (선택적) - Phase X: PDFGenerator 사용
        pdf_path = None
        if generate_pdf:
            try:
                # reportlab 기반 PDF 생성 (Evidence Footer 포함)
                pdf_path = output_dir / f"estimate_{timestamp}.pdf"
                pdf_path = self.pdf_generator.generate(
                    estimate_data=estimate_data,
                    output_path=pdf_path,
                    # build_tag와 git_hash는 PDFGenerator가 자동 추출
                )
                logger.info(f"PDF 생성 완료: {pdf_path}")
            except Exception as e:
                logger.warning(f"PDF 생성 실패: {e}")
                # PDF 생성 실패는 허용 (Excel만 생성)

        # 6. 출력 구성
        output = EstimateOutput(
            excel_path=excel_path,
            pdf_path=pdf_path,
            validation_report=validation_report,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "customer_name": customer_name,
                "project_name": project_name,
                "breaker_count": len(breakers),
                "panel_count": len(estimate_data.panels),
            },
        )

        logger.info(f"Estimate generation completed: {excel_path}")
        return output


# Phase 2 완료 체크리스트:
# [x] EstimateFormatter 메인 클래스 구조
# [x] format() 메인 메서드 (파이프라인 완성)
# [x] DataTransformer 클래스 (data_transformer.py)
# [x] ExcelGenerator 클래스 (excel_generator.py)
# [x] PDFConverter 클래스 (pdf_converter.py)
# [x] Validator 클래스 (validator.py)
# [ ] 유닛 테스트 작성 (다음 단계)
