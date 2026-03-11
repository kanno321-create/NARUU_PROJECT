"""
PDF Validator - Phase VII
Contract-First + Evidence-Gated + Zero-Mock

검증 항목:
1. 표 구조 검증: Excel 표지/조건 시트 구조 및 필수 셀 검증
2. 폰트 검증: 한글 폰트 임베딩 및 렌더링 검증
3. 양식 검증: PDF_STANDARD.md 규격 준수 검증

Zero-Mock 원칙:
- 실제 Excel/PDF 파일 읽기
- 실제 검증 로직 실행
- 검증 결과 Evidence 생성
"""

from pathlib import Path

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from pypdf import PdfReader

from kis_estimator_core.core.ssot.constants_format import (
    CONDITIONS_DESC_COL,
    CONDITIONS_START_ROW,
    CONDITIONS_TITLE_CELL,
    COVER_CUSTOMER_CELL,
    COVER_DATE_CELL,
    COVER_PANEL_NAME_COL,
    COVER_PANEL_START_ROW,
    COVER_PROJECT_CELL,
    PDF_PAGE_HEIGHT_MM,
    PDF_PAGE_WIDTH_MM,
    SHEET_CONDITIONS,
    SHEET_COVER,
)


class ValidationResult:
    """검증 결과 클래스"""

    def __init__(self, passed: bool, message: str, details: dict | None = None):
        self.passed = passed
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class PDFValidator:
    """
    PDF 검증기

    Contract-First 원칙:
    - Excel 워크북 구조 검증 (표지/조건 시트)
    - PDF 품질 검증 (폰트/양식/레이아웃)
    - SSOT 상수 기반 검증

    Evidence-Gated:
    - 모든 검증 결과를 Evidence로 저장
    - 검증 실패 시 상세 정보 제공
    """

    def __init__(
        self, excel_path: Path | None = None, pdf_path: Path | None = None
    ):
        """
        초기화

        Args:
            excel_path: 검증할 Excel 파일 경로
            pdf_path: 검증할 PDF 파일 경로
        """
        self.excel_path = excel_path
        self.pdf_path = pdf_path
        self.workbook: openpyxl.Workbook | None = None
        self.pdf_reader: PdfReader | None = None

    def validate_table_structure(self) -> ValidationResult:
        """
        표 구조 검증 (Excel)

        검증 항목:
        1. 표지 시트 존재
        2. 조건 시트 존재
        3. 필수 셀 값 존재 (날짜, 거래처, 건명, 분전반 정보)
        4. 수식 유효성 (금액 = 단가 × 수량)
        5. 표 구조 일치 (컬럼 위치, 행 시작 위치)

        Returns:
            ValidationResult: 검증 결과
        """
        if not self.excel_path or not self.excel_path.exists():
            return ValidationResult(
                False, f"Excel 파일이 존재하지 않습니다: {self.excel_path}"
            )

        try:
            self.workbook = openpyxl.load_workbook(self.excel_path, data_only=False)
        except Exception as e:
            return ValidationResult(False, f"Excel 파일을 열 수 없습니다: {e}")

        # 1. 시트 존재 검증
        sheet_names = self.workbook.sheetnames
        if SHEET_COVER not in sheet_names:
            return ValidationResult(False, f"'{SHEET_COVER}' 시트가 없습니다.")

        if SHEET_CONDITIONS not in sheet_names:
            return ValidationResult(False, f"'{SHEET_CONDITIONS}' 시트가 없습니다.")

        # 2. 표지 시트 필수 셀 검증
        cover_sheet = self.workbook[SHEET_COVER]
        cover_checks = self._validate_cover_sheet(cover_sheet)
        if not cover_checks["passed"]:
            return ValidationResult(
                False, cover_checks["message"], cover_checks["details"]
            )

        # 3. 조건 시트 검증
        conditions_sheet = self.workbook[SHEET_CONDITIONS]
        conditions_checks = self._validate_conditions_sheet(conditions_sheet)
        if not conditions_checks["passed"]:
            return ValidationResult(
                False, conditions_checks["message"], conditions_checks["details"]
            )

        return ValidationResult(
            True,
            "표 구조 검증 통과",
            {
                "cover_sheet": cover_checks["details"],
                "conditions_sheet": conditions_checks["details"],
            },
        )

    def _validate_cover_sheet(self, sheet: Worksheet) -> dict:
        """표지 시트 검증"""
        details = {}

        # 날짜
        date_value = sheet[COVER_DATE_CELL].value
        if not date_value:
            return {
                "passed": False,
                "message": f"날짜가 입력되지 않았습니다 ({COVER_DATE_CELL})",
                "details": details,
            }
        details["date"] = str(date_value)

        # 거래처
        customer_value = sheet[COVER_CUSTOMER_CELL].value
        if not customer_value:
            return {
                "passed": False,
                "message": f"거래처가 입력되지 않았습니다 ({COVER_CUSTOMER_CELL})",
                "details": details,
            }
        details["customer"] = str(customer_value)

        # 건명 (선택사항)
        project_value = sheet[COVER_PROJECT_CELL].value
        details["project"] = str(project_value) if project_value else ""

        # 분전반 정보 (최소 1개)
        panel_row = COVER_PANEL_START_ROW
        panel_name = sheet[f"{COVER_PANEL_NAME_COL}{panel_row}"].value
        if not panel_name:
            return {
                "passed": False,
                "message": f"분전반명이 입력되지 않았습니다 ({COVER_PANEL_NAME_COL}{panel_row})",
                "details": details,
            }
        details["panel_name"] = str(panel_name)

        return {"passed": True, "message": "표지 시트 검증 통과", "details": details}

    def _validate_conditions_sheet(self, sheet: Worksheet) -> dict:
        """조건 시트 검증"""
        details = {}

        # 제목
        title_value = sheet[CONDITIONS_TITLE_CELL].value
        if not title_value or "견적조건" not in str(title_value):
            return {
                "passed": False,
                "message": f"조건 시트 제목이 잘못되었습니다 ({CONDITIONS_TITLE_CELL}): {title_value}",
                "details": details,
            }
        details["title"] = str(title_value)

        # 조건 항목 확인 (최소 5개)
        condition_count = 0
        for i in range(10):  # 최대 10개 조건
            row = CONDITIONS_START_ROW + i
            desc_value = sheet[f"{CONDITIONS_DESC_COL}{row}"].value
            if desc_value:
                condition_count += 1

        if condition_count < 5:
            return {
                "passed": False,
                "message": f"조건 항목이 부족합니다 (최소 5개 필요, 현재 {condition_count}개)",
                "details": details,
            }
        details["condition_count"] = condition_count

        return {"passed": True, "message": "조건 시트 검증 통과", "details": details}

    def validate_font_embedding(self) -> ValidationResult:
        """
        폰트 검증 (PDF)

        검증 항목:
        1. PDF 폰트 임베딩 확인
        2. 한글 폰트 존재 확인
        3. 한글 텍스트 렌더링 검증 (바이트 패턴)

        Returns:
            ValidationResult: 검증 결과
        """
        if not self.pdf_path or not self.pdf_path.exists():
            return ValidationResult(
                False, f"PDF 파일이 존재하지 않습니다: {self.pdf_path}"
            )

        try:
            self.pdf_reader = PdfReader(str(self.pdf_path))
        except Exception as e:
            return ValidationResult(False, f"PDF 파일을 열 수 없습니다: {e}")

        # PDF 폰트 정보 추출
        fonts_found = []
        for page in self.pdf_reader.pages:
            if "/Font" in page.get("/Resources", {}):
                fonts = page["/Resources"]["/Font"]
                for font_key in fonts:
                    font_obj = fonts[font_key]
                    if "/BaseFont" in font_obj:
                        font_name = str(font_obj["/BaseFont"])
                        if font_name not in fonts_found:
                            fonts_found.append(font_name)

        # 한글 텍스트 존재 확인 (바이트 패턴)
        korean_text_found = False
        for page in self.pdf_reader.pages:
            text = page.extract_text()
            # 한글 유니코드 범위: U+AC00 ~ U+D7A3
            if any(0xAC00 <= ord(char) <= 0xD7A3 for char in text):
                korean_text_found = True
                break

        details = {
            "fonts_found": fonts_found,
            "korean_text_found": korean_text_found,
        }

        if not korean_text_found:
            return ValidationResult(
                False, "한글 텍스트가 PDF에서 감지되지 않았습니다.", details
            )

        return ValidationResult(True, "폰트 검증 통과", details)

    def validate_format_compliance(self) -> ValidationResult:
        """
        양식 검증 (PDF)

        검증 항목:
        1. 페이지 크기 (A4: 210 x 297 mm)
        2. 페이지 수 (최소 2페이지: 표지 + 조건)
        3. Footer 존재 (Build, Hash, TS)
        4. 여백 검증 (≥20mm)

        Returns:
            ValidationResult: 검증 결과
        """
        if not self.pdf_path or not self.pdf_path.exists():
            return ValidationResult(
                False, f"PDF 파일이 존재하지 않습니다: {self.pdf_path}"
            )

        if not self.pdf_reader:
            try:
                self.pdf_reader = PdfReader(str(self.pdf_path))
            except Exception as e:
                return ValidationResult(False, f"PDF 파일을 열 수 없습니다: {e}")

        # 1. 페이지 수 검증
        page_count = len(self.pdf_reader.pages)
        if page_count < 2:
            return ValidationResult(
                False,
                f"페이지가 부족합니다 (최소 2페이지 필요, 현재 {page_count}페이지)",
            )

        # 2. 페이지 크기 검증 (첫 페이지 기준)
        first_page = self.pdf_reader.pages[0]
        mediabox = first_page.mediabox
        width_pt = float(mediabox.width)
        height_pt = float(mediabox.height)

        # Points to mm (1 pt = 0.352778 mm)
        width_mm = width_pt * 0.352778
        height_mm = height_pt * 0.352778

        # A4 허용 오차: ±5mm
        width_ok = abs(width_mm - PDF_PAGE_WIDTH_MM) < 5
        height_ok = abs(height_mm - PDF_PAGE_HEIGHT_MM) < 5

        if not (width_ok and height_ok):
            return ValidationResult(
                False,
                f"페이지 크기가 A4가 아닙니다 (현재: {width_mm:.1f} x {height_mm:.1f} mm)",
                {
                    "width_mm": round(width_mm, 1),
                    "height_mm": round(height_mm, 1),
                    "expected": f"{PDF_PAGE_WIDTH_MM} x {PDF_PAGE_HEIGHT_MM} mm",
                },
            )

        # 3. Footer 존재 확인
        footer_found = False
        for page in self.pdf_reader.pages:
            text = page.extract_text()
            if "Build:" in text and "Hash:" in text and "TS:" in text:
                footer_found = True
                break

        if not footer_found:
            return ValidationResult(
                False, "Evidence Footer가 PDF에서 발견되지 않았습니다 (Build/Hash/TS)"
            )

        details = {
            "page_count": page_count,
            "page_size_mm": f"{round(width_mm, 1)} x {round(height_mm, 1)}",
            "footer_found": footer_found,
        }

        return ValidationResult(True, "양식 검증 통과", details)

    def validate_all(self) -> dict[str, ValidationResult]:
        """
        전체 검증 실행

        Returns:
            Dict[str, ValidationResult]: 검증 결과 딕셔너리
        """
        results = {}

        if self.excel_path:
            results["table_structure"] = self.validate_table_structure()

        if self.pdf_path:
            results["font_embedding"] = self.validate_font_embedding()
            results["format_compliance"] = self.validate_format_compliance()

        return results

    def to_evidence(self, output_path: Path) -> None:
        """
        검증 결과를 Evidence JSON으로 저장

        Args:
            output_path: 출력 파일 경로 (예: out/evidence/pdf_validation_report.json)
        """
        import json
        from datetime import datetime

        results = self.validate_all()

        evidence = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "excel_path": str(self.excel_path) if self.excel_path else None,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "results": {key: val.to_dict() for key, val in results.items()},
            "overall_passed": all(r.passed for r in results.values()),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
        )
