"""
PDF Utilities - Simple Quote PDF Generation
Phase X 최소 구현: Quote 데이터 기반 간소화 PDF
"""

import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class QuotePDFGenerator:
    """간소화된 Quote PDF 생성기 (Phase X 최소 DoD)"""

    def __init__(self):
        # 맑은 고딕 폰트 등록 시도
        try:
            font_path = r"C:\Windows\Fonts\malgun.ttf"
            if Path(font_path).exists():
                pdfmetrics.registerFont(TTFont("MalgunGothic", font_path))
                self.font_name = "MalgunGothic"
            else:
                self.font_name = "Helvetica"
        except Exception:
            self.font_name = "Helvetica"

        self.page_width, self.page_height = A4
        self.margin = 20 * mm

    def generate_quote_pdf(
        self,
        quote_data: dict,
        output_path: Path,
        build_tag: str = None,
        git_hash: str = None,
    ) -> Path:
        """
        Quote 데이터 기반 PDF 생성

        Args:
            quote_data: get_quote() 반환 데이터
            output_path: PDF 출력 경로
            build_tag: Git tag (자동 추출 가능)
            git_hash: Git hash (자동 추출 가능)

        Returns:
            Path: 생성된 PDF 경로
        """
        if not build_tag:
            build_tag = self._get_build_tag()
        if not git_hash:
            git_hash = self._get_git_hash()

        timestamp = datetime.now(UTC).isoformat()

        c = canvas.Canvas(str(output_path), pagesize=A4)

        # 메타데이터
        c.setAuthor("KIS Estimator System")
        c.setTitle(f"Quote {quote_data['quote_id']}")
        c.setSubject("Quote Document")

        # 제목
        y = self.page_height - self.margin - 30 * mm
        c.setFont(self.font_name, 20)
        c.drawCentredString(self.page_width / 2, y, "견적서")
        y -= 20 * mm

        # Quote 정보
        c.setFont(self.font_name, 12)
        c.drawString(self.margin, y, f"Quote ID: {quote_data['quote_id']}")
        y -= 7 * mm
        c.drawString(self.margin, y, f"고객사: {quote_data['client']}")
        y -= 7 * mm
        c.drawString(self.margin, y, f"상태: {quote_data['status']}")
        y -= 7 * mm
        c.drawString(self.margin, y, f"생성일: {quote_data['created_at']}")
        y -= 15 * mm

        # 금액 정보
        totals = quote_data["totals"]
        c.setFont(self.font_name, 14)
        c.drawString(
            self.margin, y, f"소계: {totals['subtotal']:,.0f} {totals['currency']}"
        )
        y -= 7 * mm
        c.drawString(
            self.margin, y, f"할인: {totals['discount']:,.0f} {totals['currency']}"
        )
        y -= 7 * mm
        c.drawString(
            self.margin, y, f"부가세: {totals['vat']:,.0f} {totals['currency']}"
        )
        y -= 7 * mm
        c.setFont(self.font_name, 16)
        c.drawString(
            self.margin, y, f"총액: {totals['total']:,.0f} {totals['currency']}"
        )
        y -= 15 * mm

        # 품목 목록 (간소화)
        c.setFont(self.font_name, 10)
        c.drawString(self.margin, y, "품목 목록:")
        y -= 5 * mm

        for i, item in enumerate(quote_data["items"][:10]):  # 최대 10개
            line = f"{i+1}. {item.get('sku', 'N/A')} x {item.get('quantity', 0)} = {item.get('line_total', 0):,.0f}"
            c.drawString(self.margin, y, line)
            y -= 5 * mm

            if y < self.margin + 30 * mm:
                break

        # Evidence Footer
        footer_y = self.margin - 5 * mm
        c.setFont("Helvetica", 8)
        footer_text = f"Build:{build_tag}  Hash:{git_hash}  Evidence:{quote_data['evidence_hash'][:8]}  TS:{timestamp}"
        c.drawCentredString(self.page_width / 2, footer_y, footer_text)

        c.save()

        logger.info(f"Quote PDF generated: {output_path}")
        return output_path

    def _get_build_tag(self) -> str:
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def _get_git_hash(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short=8", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "00000000"
