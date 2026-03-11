"""
PDF Document Generator - Cover + Body Merge + Font Embed + Page Numbers + PDF/A
Contract-First + Evidence-Gated + Zero-Mock

Features:
- Cover merge: 1-page cover + N-page estimate body → final PDF
- Font embed: NanumGothic.ttf bundle or system font fallback
- Page numbers: all pages at bottom
- PDF metadata: Title, Author, Subject, Producer, Created
- PDF/A compliance: Simple XMP metadata check
"""

from datetime import datetime
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

from ..core.ssot.pdf_drivers import (
    PDFDriver,
    choose_driver,
    convert_xlsx_to_pdf_excel_com,
    convert_xlsx_to_pdf_libreoffice,
    convert_xlsx_to_pdf_openpyxl,
)


class DocGenerator:
    """PDF document generator with cover merge and formatting"""

    def __init__(self, font_path: Path | None = None):
        """
        Initialize PDF generator

        Args:
            font_path: Path to NanumGothic.ttf (optional, uses system font fallback)
        """
        self.font_path = font_path
        self._register_fonts()

    def _register_fonts(self):
        """Register Korean fonts for PDF generation"""
        if self.font_path and self.font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("NanumGothic", str(self.font_path)))
                self.font_name = "NanumGothic"
            except Exception:
                self.font_name = "Helvetica"  # Fallback
        else:
            # System font fallback
            self.font_name = "Helvetica"

    def generate_pdf(
        self,
        xlsx_path: Path,
        output_path: Path,
        cover_metadata: dict[str, str] | None = None,
    ) -> Path:
        """
        Generate final PDF from XLSX with cover, page numbers, and metadata

        Args:
            xlsx_path: Input XLSX file (build/estimate.xlsx)
            output_path: Output PDF file (build/estimate.pdf)
            cover_metadata: Cover page metadata (customer_name, project_name, date)

        Returns:
            Path: Generated PDF file path

        Raises:
            RuntimeError: If PDF generation fails
        """
        # Step 1: Convert XLSX to PDF
        body_pdf = self._convert_xlsx_to_pdf(xlsx_path)

        # Step 2: Generate cover page (if metadata provided)
        if cover_metadata:
            cover_pdf = self._generate_cover(cover_metadata)
        else:
            cover_pdf = None

        # Step 3: Merge cover + body
        if cover_pdf:
            merged_pdf = self._merge_cover_and_body(cover_pdf, body_pdf)
        else:
            merged_pdf = body_pdf

        # Step 4: Add page numbers
        numbered_pdf = self._add_page_numbers(merged_pdf)

        # Step 5: Add PDF metadata
        final_pdf = self._add_metadata(
            numbered_pdf,
            output_path,
            cover_metadata or {},
        )

        # Step 6: PDF/A compliance check (simple XMP check)
        self._check_pdfa_compliance(final_pdf)

        return final_pdf

    def _convert_xlsx_to_pdf(self, xlsx_path: Path) -> Path:
        """Convert XLSX to PDF using best available driver"""
        driver, driver_desc = choose_driver()

        temp_pdf = xlsx_path.parent / f"{xlsx_path.stem}_body.pdf"

        if driver == PDFDriver.LIBREOFFICE:
            convert_xlsx_to_pdf_libreoffice(xlsx_path, temp_pdf)
        elif driver == PDFDriver.EXCEL_COM:
            convert_xlsx_to_pdf_excel_com(xlsx_path, temp_pdf)
        elif driver == PDFDriver.OPENPYXL_REPORTLAB:
            convert_xlsx_to_pdf_openpyxl(xlsx_path, temp_pdf)
        else:
            raise_error(ErrorCode.E_INTERNAL, f"Unknown PDF driver: {driver}")

        if not temp_pdf.exists():
            raise_error(ErrorCode.E_INTERNAL, f"PDF conversion failed: {temp_pdf}")

        return temp_pdf

    def _generate_cover(self, metadata: dict[str, str]) -> Path:
        """Generate cover page PDF"""
        cover_path = Path("build") / "cover.pdf"
        cover_path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(cover_path), pagesize=A4)
        width, height = A4

        # Title
        c.setFont(self.font_name, 24)
        c.drawCentredString(width / 2, height - 100, "견적서")

        # Customer info
        c.setFont(self.font_name, 14)
        y = height - 200
        if "customer_name" in metadata:
            c.drawString(100, y, f"거래처: {metadata['customer_name']}")
            y -= 30
        if "project_name" in metadata:
            c.drawString(100, y, f"건명: {metadata['project_name']}")
            y -= 30
        if "date" in metadata:
            c.drawString(100, y, f"작성일: {metadata['date']}")

        c.save()
        return cover_path

    def _merge_cover_and_body(self, cover_path: Path, body_path: Path) -> Path:
        """Merge cover page and body PDF"""
        merged_path = Path("build") / "merged.pdf"

        writer = PdfWriter()

        # Add cover
        cover_reader = PdfReader(str(cover_path))
        for page in cover_reader.pages:
            writer.add_page(page)

        # Add body
        body_reader = PdfReader(str(body_path))
        for page in body_reader.pages:
            writer.add_page(page)

        with open(merged_path, "wb") as f:
            writer.write(f)

        return merged_path

    def _add_page_numbers(self, input_pdf: Path) -> Path:
        """Add page numbers to all pages"""
        numbered_path = Path("build") / "numbered.pdf"

        reader = PdfReader(str(input_pdf))
        writer = PdfWriter()

        total_pages = len(reader.pages)

        for page_num, page in enumerate(reader.pages, start=1):
            # Create page number overlay
            packet = Path("build") / f"page_num_{page_num}.pdf"
            c = canvas.Canvas(str(packet), pagesize=A4)
            width, height = A4

            c.setFont(self.font_name, 10)
            c.drawCentredString(
                width / 2,
                30,  # Bottom of page
                f"{page_num} / {total_pages}",
            )
            c.save()

            # Merge page number with original page
            overlay = PdfReader(str(packet))
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

            # Clean up temp file
            packet.unlink()

        with open(numbered_path, "wb") as f:
            writer.write(f)

        return numbered_path

    def _add_metadata(
        self,
        input_pdf: Path,
        output_pdf: Path,
        metadata: dict[str, str],
    ) -> Path:
        """Add PDF metadata (Title, Author, Subject, Producer, Created)"""
        reader = PdfReader(str(input_pdf))
        writer = PdfWriter()

        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)

        # Add metadata
        project_name = metadata.get("project_name", "")
        title = f"견적서 - {project_name}" if project_name else "견적서"

        writer.add_metadata(
            {
                "/Title": title,
                "/Author": "NABERAL KIS Estimator",
                "/Subject": f"전기 패널 견적서 - {metadata.get('customer_name', 'N/A')}",
                "/Producer": "NABERAL KIS Estimator v1.0",
                "/CreationDate": f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}",
            }
        )

        with open(output_pdf, "wb") as f:
            writer.write(f)

        return output_pdf

    def _check_pdfa_compliance(self, pdf_path: Path) -> bool:
        """
        Simple PDF/A compliance check (XMP metadata presence only)

        Returns:
            bool: True if basic PDF/A compliance rules are met
        """
        reader = PdfReader(str(pdf_path))

        # Check 1: XMP metadata present
        if reader.metadata and reader.xmp_metadata:
            return True

        # - Fonts embedded
        # - No transparency
        # - Color space compliance
        # - etc.
        # For now, just check XMP presence as a simple indicator

        return False
