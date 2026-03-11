"""
Unit Tests for engine/pdf_generator.py
Coverage target: >68% for PDFGenerator class

Zero-Mock exception: Unit tests may use unittest.mock for external dependencies
to avoid requiring actual PDF generation infrastructure in CI environment.
"""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPDFGeneratorInit:
    """Tests for PDFGenerator initialization"""

    def test_init_with_malgun_font(self):
        """Test initialization with MalgunGothic font

        NOTE: This test requires proper module isolation due to Python's import caching.
        We must patch both TTFont (which reads the actual file) and pdfmetrics.registerFont.
        """
        import sys

        # Remove cached module to ensure fresh import with patches
        modules_to_remove = [k for k in sys.modules if "pdf_generator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            # Mock Path().exists() to return True
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # Must also patch TTFont - it tries to open the actual file in its constructor
            with patch(
                "kis_estimator_core.engine.pdf_generator.TTFont"
            ) as mock_ttfont:
                mock_ttfont.return_value = MagicMock()

                with patch(
                    "kis_estimator_core.engine.pdf_generator.pdfmetrics.registerFont"
                ):
                    from kis_estimator_core.engine.pdf_generator import PDFGenerator

                    generator = PDFGenerator()

                    # Should use MalgunGothic when Path.exists() returns True
                    assert generator.font_name == "MalgunGothic"
                    # Verify TTFont was called with correct arguments
                    mock_ttfont.assert_called_once()

    def test_init_fallback_to_helvetica(self):
        """Test initialization falls back to Helvetica when font not found"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            # Should fallback to Helvetica
            assert generator.font_name == "Helvetica"

    def test_init_font_registration_error(self):
        """Test initialization handles font registration error"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = True

            with patch(
                "kis_estimator_core.engine.pdf_generator.pdfmetrics.registerFont"
            ) as mock_register:
                mock_register.side_effect = Exception("Font registration failed")

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()

                # Should fallback to Helvetica
                assert generator.font_name == "Helvetica"

    def test_init_page_dimensions(self):
        """Test initialization sets correct A4 dimensions"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            assert generator.page_width == A4[0]
            assert generator.page_height == A4[1]
            assert generator.margin == 20 * mm


class TestPDFGeneratorGetBuildTag:
    """Tests for PDFGenerator._get_build_tag method"""

    def test_get_build_tag_success(self):
        """Test getting build tag from git"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v1.0.0\n"

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                tag = generator._get_build_tag()

                assert tag == "v1.0.0"

    def test_get_build_tag_failure(self):
        """Test getting build tag when git fails"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.return_value.returncode = 1

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                tag = generator._get_build_tag()

                assert tag == "unknown"

    def test_get_build_tag_exception(self):
        """Test getting build tag handles exception"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.side_effect = Exception("Git not found")

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                tag = generator._get_build_tag()

                assert tag == "unknown"


class TestPDFGeneratorGetGitHash:
    """Tests for PDFGenerator._get_git_hash method"""

    def test_get_git_hash_success(self):
        """Test getting git hash"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "abcd1234\n"

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                git_hash = generator._get_git_hash()

                assert git_hash == "abcd1234"

    def test_get_git_hash_failure(self):
        """Test getting git hash when git fails"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.return_value.returncode = 1

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                git_hash = generator._get_git_hash()

                assert git_hash == "00000000"

    def test_get_git_hash_exception(self):
        """Test getting git hash handles exception"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.subprocess.run"
            ) as mock_run:
                mock_run.side_effect = Exception("Git not found")

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()
                git_hash = generator._get_git_hash()

                assert git_hash == "00000000"


class TestPDFGeneratorCalculateContentHash:
    """Tests for PDFGenerator._calculate_content_hash method"""

    def test_calculate_content_hash_basic(self):
        """Test content hash calculation"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            # Mock estimate data
            mock_data = MagicMock()
            mock_data.customer_name = "Test Customer"
            mock_data.project_name = "Test Project"
            mock_data.panels = []

            content_hash = generator._calculate_content_hash(
                mock_data, build_tag="v1.0", git_hash="abcd1234"
            )

            # Should return 8 character hex string
            assert len(content_hash) == 8
            assert all(c in "0123456789abcdef" for c in content_hash)

    def test_calculate_content_hash_with_panels(self):
        """Test content hash calculation with panels"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            # Mock estimate data with panels
            mock_panel = MagicMock()
            mock_panel.total_price = 100000
            mock_panel.all_items_sorted = []

            mock_data = MagicMock()
            mock_data.customer_name = "Test"
            mock_data.project_name = ""
            mock_data.panels = [mock_panel]

            content_hash = generator._calculate_content_hash(mock_data)

            assert len(content_hash) == 8

    def test_calculate_content_hash_deterministic(self):
        """Test content hash is deterministic"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_data = MagicMock()
            mock_data.customer_name = "Test"
            mock_data.project_name = "Project"
            mock_data.panels = []

            hash1 = generator._calculate_content_hash(
                mock_data, build_tag="v1", git_hash="abc"
            )
            hash2 = generator._calculate_content_hash(
                mock_data, build_tag="v1", git_hash="abc"
            )

            assert hash1 == hash2

    def test_calculate_content_hash_different_inputs(self):
        """Test different inputs produce different hashes"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_data1 = MagicMock()
            mock_data1.customer_name = "Customer A"
            mock_data1.project_name = "Project"
            mock_data1.panels = []

            mock_data2 = MagicMock()
            mock_data2.customer_name = "Customer B"
            mock_data2.project_name = "Project"
            mock_data2.panels = []

            hash1 = generator._calculate_content_hash(mock_data1)
            hash2 = generator._calculate_content_hash(mock_data2)

            assert hash1 != hash2

    def test_calculate_content_hash_exception_handling(self):
        """Test content hash handles exceptions"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            # Mock data that raises exception
            mock_data = MagicMock()
            mock_data.customer_name = property(lambda: None)  # Will raise

            # Should return default hash on error
            content_hash = generator._calculate_content_hash(mock_data)

            # Either calculated or default
            assert len(content_hash) == 8


class TestPDFGeneratorDrawFooter:
    """Tests for PDFGenerator._draw_footer method"""

    def test_draw_footer_content(self):
        """Test footer draws correct content"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            generator._draw_footer(
                mock_canvas,
                build_tag="v1.0.0",
                git_hash="abcd1234",
                content_hash="12345678",
                timestamp="2025-01-01T00:00:00",
            )

            # Should call setFont and drawCentredString
            mock_canvas.setFont.assert_called()
            mock_canvas.drawCentredString.assert_called()

            # Check footer contains expected elements
            call_args = mock_canvas.drawCentredString.call_args
            footer_text = call_args[0][2]  # Third positional arg is text
            assert "Build:v1.0.0" in footer_text
            assert "Hash:abcd1234" in footer_text
            assert "Content:12345678" in footer_text


class TestPDFGeneratorGenerate:
    """Tests for PDFGenerator.generate method"""

    def test_generate_creates_pdf(self, tmp_path):
        """Test generate creates PDF file"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path_class:
            # Only mock the font path check
            mock_path_class.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.canvas.Canvas"
            ) as mock_canvas_class:
                mock_canvas = MagicMock()
                mock_canvas_class.return_value = mock_canvas

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()

                # Mock estimate data
                mock_data = MagicMock()
                mock_data.customer_name = "Test Customer"
                mock_data.project_name = "Test Project"
                mock_data.panels = []

                output_path = tmp_path / "test.pdf"

                with patch.object(generator, "_get_build_tag", return_value="v1.0"):
                    with patch.object(
                        generator, "_get_git_hash", return_value="abcd1234"
                    ):
                        result = generator.generate(mock_data, output_path)

                # Should return the output path
                assert result == output_path

                # Canvas should be saved
                mock_canvas.save.assert_called_once()

    def test_generate_with_custom_build_info(self, tmp_path):
        """Test generate with custom build tag and git hash"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path_class:
            mock_path_class.return_value.exists.return_value = False

            with patch(
                "kis_estimator_core.engine.pdf_generator.canvas.Canvas"
            ) as mock_canvas_class:
                mock_canvas = MagicMock()
                mock_canvas_class.return_value = mock_canvas

                from kis_estimator_core.engine.pdf_generator import PDFGenerator

                generator = PDFGenerator()

                mock_data = MagicMock()
                mock_data.customer_name = "Test"
                mock_data.project_name = ""
                mock_data.panels = []

                output_path = tmp_path / "test.pdf"

                result = generator.generate(
                    mock_data,
                    output_path,
                    build_tag="custom-tag",
                    git_hash="custom123",
                )

                assert result == output_path


class TestPDFGeneratorDrawCoverPage:
    """Tests for PDFGenerator._draw_cover_page method"""

    def test_draw_cover_page_basic(self):
        """Test drawing cover page with basic data"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            mock_data = MagicMock()
            mock_data.customer_name = "Test Customer"
            mock_data.project_name = "Test Project"
            mock_data.panels = []

            generator._draw_cover_page(
                mock_canvas,
                mock_data,
                build_tag="v1",
                git_hash="abc",
                content_hash="123",
                timestamp="2025-01-01",
            )

            # Should draw title, date, customer name
            assert mock_canvas.drawCentredString.called
            assert mock_canvas.drawString.called

    def test_draw_cover_page_with_panels(self):
        """Test drawing cover page with panel data"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            # Mock panel
            mock_panel = MagicMock()
            mock_panel.panel_name = "LP-M"
            mock_panel.total_price = 500000
            mock_panel.quantity = 1
            mock_panel.enclosure = None
            mock_panel.remarks = ""
            mock_panel.main_breaker = None

            mock_data = MagicMock()
            mock_data.customer_name = "Test"
            mock_data.project_name = ""
            mock_data.panels = [mock_panel]

            generator._draw_cover_page(
                mock_canvas,
                mock_data,
                build_tag="v1",
                git_hash="abc",
                content_hash="123",
                timestamp="2025-01-01",
            )

            # Should draw panel info
            assert mock_canvas.drawString.called


class TestPDFGeneratorDrawTermsPage:
    """Tests for PDFGenerator._draw_terms_page method"""

    def test_draw_terms_page(self):
        """Test drawing terms page"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            generator._draw_terms_page(
                mock_canvas,
                build_tag="v1",
                git_hash="abc",
                content_hash="123",
                timestamp="2025-01-01",
            )

            # Should draw terms
            assert mock_canvas.drawString.called
            assert mock_canvas.setFont.called


class TestPDFGeneratorDrawEstimateDetails:
    """Tests for PDFGenerator._draw_estimate_details method"""

    def test_draw_estimate_details_empty(self):
        """Test drawing estimate details with no items"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            mock_data = MagicMock()
            mock_data.panels = []

            generator._draw_estimate_details(
                mock_canvas,
                mock_data,
                build_tag="v1",
                git_hash="abc",
                content_hash="123",
                timestamp="2025-01-01",
            )

            # Should still draw title
            assert mock_canvas.setFont.called

    def test_draw_estimate_details_with_items(self):
        """Test drawing estimate details with items"""
        with patch("kis_estimator_core.engine.pdf_generator.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            from kis_estimator_core.engine.pdf_generator import PDFGenerator

            generator = PDFGenerator()

            mock_canvas = MagicMock()

            # Mock item
            mock_item = MagicMock()
            mock_item.item_name = "MCCB 100AF"
            mock_item.quantity = 1
            mock_item.amount = 50000

            mock_panel = MagicMock()
            mock_panel.all_items_sorted = [mock_item]

            mock_data = MagicMock()
            mock_data.panels = [mock_panel]

            generator._draw_estimate_details(
                mock_canvas,
                mock_data,
                build_tag="v1",
                git_hash="abc",
                content_hash="123",
                timestamp="2025-01-01",
            )

            # Should draw item details
            assert mock_canvas.drawString.called
