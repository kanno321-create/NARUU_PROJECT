"""
Unit Tests for utils/pdf_auditor.py
Coverage target: >80% for PDFAuditor
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPDFAuditResult:
    """Tests for PDFAuditResult dataclass"""

    def test_audit_result_passed(self):
        """Test PDFAuditResult with all checks passed"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditResult

        result = PDFAuditResult(
            passed=True,
            font_check=True,
            paper_check=True,
            margin_check=True,
            footer_check=True,
            errors=[],
            warnings=[],
        )

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_audit_result_failed(self):
        """Test PDFAuditResult with failures"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditResult

        result = PDFAuditResult(
            passed=False,
            font_check=False,
            paper_check=True,
            margin_check=True,
            footer_check=False,
            errors=["Font error", "Footer missing"],
            warnings=["Warning 1"],
        )

        assert result.passed is False
        assert len(result.errors) == 2
        assert result.font_check is False


class TestPDFAuditor:
    """Tests for PDFAuditor class"""

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader", None)
    def test_init_without_pypdf2(self):
        """Test initialization fails without PyPDF2"""
        # Need to reload the module to pick up the patched PdfReader
        import kis_estimator_core.utils.pdf_auditor as auditor_module

        original_reader = auditor_module.PdfReader
        auditor_module.PdfReader = None

        try:
            with pytest.raises(ImportError) as exc:
                auditor_module.PDFAuditor()
            assert "PyPDF2" in str(exc.value)
        finally:
            auditor_module.PdfReader = original_reader

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_init_with_pypdf2(self, mock_reader):
        """Test successful initialization with PyPDF2"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        auditor = PDFAuditor()
        assert auditor is not None

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_file_not_found(self, mock_reader):
        """Test audit with non-existent file"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        auditor = PDFAuditor()
        result = auditor.audit(Path("/nonexistent/file.pdf"))

        assert result.passed is False
        assert any("not found" in err for err in result.errors)

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_success(self, mock_reader_class):
        """Test successful audit with valid PDF"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        # Setup mock reader
        mock_page = MagicMock()
        mock_page.mediabox.width = 595.28
        mock_page.mediabox.height = 841.89
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = (
            "Build:v1.0.0  Hash:12345678  Evidence:abc  TS:2025-01-01T12:00:00"
        )

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        assert result.paper_check is True

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_wrong_paper_size(self, mock_reader_class):
        """Test audit with wrong paper size"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        # Setup mock reader with Letter size instead of A4
        mock_page = MagicMock()
        mock_page.mediabox.width = 612.0  # Letter width
        mock_page.mediabox.height = 792.0  # Letter height
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = "Build:v1.0.0  Hash:12345678  TS:2025-01-01T12:00:00"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        assert result.paper_check is False
        assert any("Paper size" in err for err in result.errors)

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_missing_footer(self, mock_reader_class):
        """Test audit with missing evidence footer"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        mock_page = MagicMock()
        mock_page.mediabox.width = 595.28
        mock_page.mediabox.height = 841.89
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = "No footer here"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        assert result.footer_check is False
        assert any("Footer" in err for err in result.errors)

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_no_text_extracted(self, mock_reader_class):
        """Test audit when text extraction fails"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        mock_page = MagicMock()
        mock_page.mediabox.width = 595.28
        mock_page.mediabox.height = 841.89
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = None

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        assert result.footer_check is False

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_exception(self, mock_reader_class):
        """Test audit with exception during processing"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        mock_reader_class.side_effect = Exception("PDF read error")

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        assert result.passed is False
        assert any("failed" in err.lower() for err in result.errors)

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_check_fonts_with_fonts(self, mock_reader_class):
        """Test font check with fonts in PDF"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        mock_font = MagicMock()
        mock_font.__getitem__ = MagicMock(return_value="/MalgunGothic")
        mock_font.__contains__ = MagicMock(return_value=True)

        mock_page = MagicMock()
        mock_page.mediabox.width = 595.28
        mock_page.mediabox.height = 841.89
        mock_page.__getitem__ = MagicMock(
            return_value={"/Font": {"F1": mock_font}}
        )
        mock_page.extract_text.return_value = (
            "Build:v1.0.0  Hash:12345678  TS:2025-01-01T12:00:00"
        )

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        with patch.object(Path, "exists", return_value=True):
            result = auditor.audit(Path("/test/file.pdf"))

        # Font check should pass
        assert result.font_check is True

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_paper_size_check_exception(self, mock_reader_class):
        """Test paper size check with exception"""
        from kis_estimator_core.utils.pdf_auditor import PDFAuditor

        mock_page = MagicMock()
        mock_page.mediabox.width = property(
            fget=lambda x: (_ for _ in ()).throw(Exception("Width error"))
        )
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = (
            "Build:v1.0.0  Hash:12345678  TS:2025-01-01T12:00:00"
        )

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        auditor = PDFAuditor()

        # Paper check should pass with warning on exception
        errors = []
        warnings = []
        result = auditor._check_paper_size(mock_reader, errors, warnings)

        # The function should handle exception gracefully
        assert result is True or len(warnings) > 0


class TestAuditPdfFunction:
    """Tests for audit_pdf convenience function"""

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_pdf_function(self, mock_reader_class):
        """Test audit_pdf convenience function"""
        from kis_estimator_core.utils.pdf_auditor import audit_pdf

        mock_page = MagicMock()
        mock_page.mediabox.width = 595.28
        mock_page.mediabox.height = 841.89
        mock_page.__getitem__ = MagicMock(return_value={})
        mock_page.extract_text.return_value = (
            "Build:v1.0.0  Hash:12345678  TS:2025-01-01T12:00:00"
        )

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        with patch.object(Path, "exists", return_value=True):
            result = audit_pdf(Path("/test/file.pdf"))

        assert result is not None
        assert hasattr(result, "passed")

    @patch("kis_estimator_core.utils.pdf_auditor.PdfReader")
    def test_audit_pdf_function_not_found(self, mock_reader_class):
        """Test audit_pdf with non-existent file"""
        from kis_estimator_core.utils.pdf_auditor import audit_pdf

        result = audit_pdf(Path("/nonexistent/file.pdf"))

        assert result.passed is False
