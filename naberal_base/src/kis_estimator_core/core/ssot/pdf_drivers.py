"""
PDF Generation Drivers - SSOT Module
Contract-First + Evidence-Gated + Zero-Mock

Driver Priority:
1. LibreOffice (unoconv/soffice) - Best quality
2. Excel COM (win32com) - Windows only, requires Excel
3. openpyxl + ReportLab - Fallback, cross-platform
"""

import subprocess
import sys
from enum import Enum
from importlib.util import find_spec
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


class PDFDriver(str, Enum):
    """PDF generation driver types"""

    LIBREOFFICE = "libreoffice"
    EXCEL_COM = "excel_com"
    OPENPYXL_REPORTLAB = "openpyxl_reportlab"


def check_libreoffice() -> bool:
    """Check if LibreOffice is available"""
    try:
        result = subprocess.run(
            ["soffice", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_excel_com() -> bool:
    """Check if Excel COM is available (Windows only)"""
    if sys.platform != "win32":
        return False

    # Use importlib.util.find_spec to check module availability
    # This avoids actually importing the module
    return find_spec("win32com.client") is not None


def check_openpyxl_reportlab() -> bool:
    """Check if openpyxl + ReportLab are available"""
    # Use importlib.util.find_spec to check module availability
    return (
        find_spec("openpyxl") is not None and find_spec("reportlab.pdfgen") is not None
    )


def choose_driver() -> tuple[PDFDriver, str]:
    """
    Choose best available PDF driver

    Returns:
        Tuple[PDFDriver, str]: (driver_type, driver_description)

    Raises:
        RuntimeError: If no PDF driver is available
    """
    # Priority 1: LibreOffice
    if check_libreoffice():
        return PDFDriver.LIBREOFFICE, "LibreOffice (unoconv/soffice)"

    # Priority 2: openpyxl + ReportLab (Fallback but reliable)

    if check_openpyxl_reportlab():
        return PDFDriver.OPENPYXL_REPORTLAB, "openpyxl + ReportLab (Fallback)"

    # Priority 3: Excel COM (Windows only) - can be slow
    if check_excel_com():
        return PDFDriver.EXCEL_COM, "Excel COM (win32com)"

    raise_error(
        ErrorCode.E_INTERNAL,
        "No PDF driver available. Install one of:\n"
        "  1. LibreOffice (recommended)\n"
        "  2. pip install openpyxl reportlab\n"
        "  3. Microsoft Excel (Windows only)",
    )


def convert_xlsx_to_pdf_libreoffice(xlsx_path: Path, pdf_path: Path) -> None:
    """Convert XLSX to PDF using LibreOffice"""
    result = subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(xlsx_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise_error(
            ErrorCode.E_INTERNAL, f"LibreOffice conversion failed: {result.stderr}"
        )

    # LibreOffice creates PDF with same name as XLSX
    generated_pdf = xlsx_path.parent / f"{xlsx_path.stem}.pdf"
    if generated_pdf.exists() and generated_pdf != pdf_path:
        generated_pdf.rename(pdf_path)


def convert_xlsx_to_pdf_excel_com(xlsx_path: Path, pdf_path: Path) -> None:
    """Convert XLSX to PDF using Excel COM (Windows only)"""
    import win32com.client

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        workbook = excel.Workbooks.Open(str(xlsx_path.absolute()))
        workbook.ExportAsFixedFormat(0, str(pdf_path.absolute()))  # 0 = xlTypePDF
        workbook.Close(False)

    finally:
        if excel:
            excel.Quit()


def convert_xlsx_to_pdf_openpyxl(xlsx_path: Path, pdf_path: Path) -> None:
    """
    Convert XLSX to PDF using openpyxl + ReportLab (Fallback)

    Warning: Basic rendering, formulas may not be preserved
    """
    import openpyxl
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    y = height - 50  # Start from top
    for row in ws.iter_rows(values_only=True):
        text = " | ".join(str(cell) if cell else "" for cell in row)
        c.drawString(50, y, text[:100])  # Limit text width
        y -= 20
        if y < 50:  # New page
            c.showPage()
            y = height - 50

    c.save()
