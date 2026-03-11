"""
Unit Tests for services/pdf_utils.py
Coverage target: >80% for QuotePDFGenerator
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestQuotePDFGenerator:
    """Tests for QuotePDFGenerator class"""

    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    @patch("kis_estimator_core.services.pdf_utils.TTFont")
    def test_init_with_font(self, mock_ttfont, mock_pdfmetrics):
        """Test initialization with available font"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=True):
            generator = QuotePDFGenerator()

        assert generator.font_name == "MalgunGothic"
        mock_pdfmetrics.registerFont.assert_called_once()

    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_init_without_font(self, mock_pdfmetrics):
        """Test initialization when font not available"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        assert generator.font_name == "Helvetica"

    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_init_font_exception(self, mock_pdfmetrics):
        """Test initialization when font registration fails"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        mock_pdfmetrics.registerFont.side_effect = Exception("Font error")

        with patch.object(Path, "exists", return_value=True):
            generator = QuotePDFGenerator()

        assert generator.font_name == "Helvetica"

    @patch("kis_estimator_core.services.pdf_utils.canvas")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_generate_quote_pdf(self, mock_pdfmetrics, mock_canvas):
        """Test PDF generation with quote data"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_canvas_instance = MagicMock()
        mock_canvas.Canvas.return_value = mock_canvas_instance

        quote_data = {
            "quote_id": "QT-001",
            "client": "Test Client",
            "status": "APPROVED",
            "created_at": "2025-01-01",
            "evidence_hash": "abc12345678",
            "totals": {
                "subtotal": 100000,
                "discount": 0,
                "vat": 10000,
                "total": 110000,
                "currency": "KRW",
            },
            "items": [
                {"sku": "ITEM-001", "quantity": 5, "line_total": 50000},
                {"sku": "ITEM-002", "quantity": 3, "line_total": 30000},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_quote.pdf"

            result = generator.generate_quote_pdf(
                quote_data, output_path, build_tag="v1.0.0", git_hash="12345678"
            )

        assert result == output_path
        mock_canvas_instance.save.assert_called_once()

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_build_tag_success(self, mock_pdfmetrics, mock_run):
        """Test _get_build_tag returns git tag"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.return_value = MagicMock(returncode=0, stdout="v1.2.3\n")

        result = generator._get_build_tag()
        assert result == "v1.2.3"

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_build_tag_failure(self, mock_pdfmetrics, mock_run):
        """Test _get_build_tag returns 'unknown' on failure"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.return_value = MagicMock(returncode=1)

        result = generator._get_build_tag()
        assert result == "unknown"

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_build_tag_exception(self, mock_pdfmetrics, mock_run):
        """Test _get_build_tag returns 'unknown' on exception"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.side_effect = Exception("Git not found")

        result = generator._get_build_tag()
        assert result == "unknown"

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_git_hash_success(self, mock_pdfmetrics, mock_run):
        """Test _get_git_hash returns git hash"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.return_value = MagicMock(returncode=0, stdout="abc12345\n")

        result = generator._get_git_hash()
        assert result == "abc12345"

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_git_hash_failure(self, mock_pdfmetrics, mock_run):
        """Test _get_git_hash returns default on failure"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.return_value = MagicMock(returncode=1)

        result = generator._get_git_hash()
        assert result == "00000000"

    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_get_git_hash_exception(self, mock_pdfmetrics, mock_run):
        """Test _get_git_hash returns default on exception"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_run.side_effect = Exception("Git not found")

        result = generator._get_git_hash()
        assert result == "00000000"

    @patch("kis_estimator_core.services.pdf_utils.canvas")
    @patch("kis_estimator_core.services.pdf_utils.subprocess.run")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_generate_quote_pdf_auto_git_info(
        self, mock_pdfmetrics, mock_run, mock_canvas
    ):
        """Test PDF generation with auto-detected git info"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_canvas_instance = MagicMock()
        mock_canvas.Canvas.return_value = mock_canvas_instance
        mock_run.return_value = MagicMock(returncode=0, stdout="v1.0.0\n")

        quote_data = {
            "quote_id": "QT-002",
            "client": "Auto Client",
            "status": "DRAFT",
            "created_at": "2025-01-02",
            "evidence_hash": "def67890123",
            "totals": {
                "subtotal": 50000,
                "discount": 5000,
                "vat": 4500,
                "total": 49500,
                "currency": "KRW",
            },
            "items": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_quote2.pdf"

            result = generator.generate_quote_pdf(quote_data, output_path)

        assert result == output_path

    @patch("kis_estimator_core.services.pdf_utils.canvas")
    @patch("kis_estimator_core.services.pdf_utils.pdfmetrics")
    def test_generate_quote_pdf_many_items(self, mock_pdfmetrics, mock_canvas):
        """Test PDF generation with many items (pagination limit)"""
        from kis_estimator_core.services.pdf_utils import QuotePDFGenerator

        with patch.object(Path, "exists", return_value=False):
            generator = QuotePDFGenerator()

        mock_canvas_instance = MagicMock()
        mock_canvas.Canvas.return_value = mock_canvas_instance

        # Create 15 items (more than the 10 item limit)
        items = [
            {"sku": f"ITEM-{i:03d}", "quantity": i, "line_total": i * 1000}
            for i in range(1, 16)
        ]

        quote_data = {
            "quote_id": "QT-003",
            "client": "Many Items Client",
            "status": "PENDING",
            "created_at": "2025-01-03",
            "evidence_hash": "ghi01234567",
            "totals": {
                "subtotal": 120000,
                "discount": 0,
                "vat": 12000,
                "total": 132000,
                "currency": "KRW",
            },
            "items": items,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_quote3.pdf"

            result = generator.generate_quote_pdf(
                quote_data, output_path, build_tag="v1.0.0", git_hash="12345678"
            )

        assert result == output_path
        mock_canvas_instance.save.assert_called_once()
