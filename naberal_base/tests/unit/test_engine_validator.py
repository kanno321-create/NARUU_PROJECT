"""
Unit Tests for engine/validator.py
Coverage target: >68% for Validator class

Zero-Mock exception: Unit tests may use unittest.mock for external Excel operations
to avoid requiring actual Excel files in CI environment.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestValidatorInit:
    """Tests for Validator initialization"""

    def test_init_with_valid_template(self, tmp_path):
        """Test initialization with valid template path"""
        # Create a dummy template file
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            from kis_estimator_core.engine.validator import Validator

            validator = Validator(template_path=template_path)

            assert validator.template_path == template_path

    def test_init_with_nonexistent_template_raises_error(self):
        """Test initialization with nonexistent template raises error"""
        from kis_estimator_core.core.ssot.errors import EstimatorError
        from kis_estimator_core.engine.validator import Validator

        with pytest.raises(EstimatorError):
            Validator(template_path=Path("/nonexistent/template.xlsx"))


class TestValidatorValidate:
    """Tests for Validator.validate method"""

    def test_validate_with_nonexistent_file(self, tmp_path):
        """Test validation with non-existent Excel file"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.core.ssot.errors import EstimatorError

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            from kis_estimator_core.engine.validator import Validator

            validator = Validator(template_path=template_path)

            with pytest.raises(EstimatorError):
                validator.validate(Path("/nonexistent/file.xlsx"))

    def test_validate_workbook_load_failure(self, tmp_path):
        """Test validation when workbook load fails"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()
        excel_path = tmp_path / "test.xlsx"
        excel_path.touch()

        from kis_estimator_core.engine.validator import Validator

        # Mock load_workbook to raise exception
        with patch("kis_estimator_core.engine.validator.load_workbook") as mock_load:
            # First call for template (in __init__), second for validation
            mock_load.side_effect = [MagicMock(), Exception("Load failed")]

            validator = Validator(template_path=template_path)
            report = validator.validate(excel_path)

            assert report.formula_preservation is False
            assert report.merged_cells_intact is False
            assert "워크북 로드 실패" in report.violations[0]


class TestValidatorValidateFormulas:
    """Tests for Validator._validate_formulas method"""

    def test_validate_formulas_success(self, tmp_path):
        """Test formula validation success"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        # Mock workbooks
        mock_ws_estimate = MagicMock()
        mock_ws_cover = MagicMock()

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = lambda self, key: (
            mock_ws_estimate if key == "견적서" else mock_ws_cover
        )

        mock_wb_template = MagicMock()

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            with patch(
                "kis_estimator_core.engine.validator.formula_guard"
            ) as mock_guard:
                mock_guard.return_value = (True, [], 1.0)  # valid, no errors, 100%

                validator = Validator(template_path=template_path)
                violations = []
                warnings = []
                error_codes = []

                result = validator._validate_formulas(
                    mock_wb_generated,
                    mock_wb_template,
                    violations,
                    warnings,
                    error_codes,
                )

                assert result is True
                assert len(violations) == 0
                assert len(error_codes) == 0

    def test_validate_formulas_failure(self, tmp_path):
        """Test formula validation failure"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_estimate = MagicMock()
        mock_ws_cover = MagicMock()

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = lambda self, key: (
            mock_ws_estimate if key == "견적서" else mock_ws_cover
        )

        mock_wb_template = MagicMock()

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            with patch(
                "kis_estimator_core.engine.validator.formula_guard"
            ) as mock_guard:
                # First call fails
                mock_guard.return_value = (
                    False,
                    ["Formula missing in G10"],
                    0.8,
                )

                validator = Validator(template_path=template_path)
                violations = []
                warnings = []
                error_codes = []

                result = validator._validate_formulas(
                    mock_wb_generated,
                    mock_wb_template,
                    violations,
                    warnings,
                    error_codes,
                )

                assert result is False
                assert "CAL-001" in error_codes
                assert len(violations) > 0


class TestValidatorValidateMergedCells:
    """Tests for Validator._validate_merged_cells method"""

    def test_validate_merged_cells_match(self, tmp_path):
        """Test merged cells validation when counts match"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        # Mock worksheets with same merged ranges
        mock_range = MagicMock()

        mock_ws_gen = MagicMock()
        mock_ws_gen.merged_cells.ranges = [mock_range]

        mock_ws_tpl = MagicMock()
        mock_ws_tpl.merged_cells.ranges = [mock_range]

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = lambda self, key: mock_ws_gen

        mock_wb_template = MagicMock()
        mock_wb_template.__getitem__ = lambda self, key: mock_ws_tpl

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            validator = Validator(template_path=template_path)
            violations = []
            warnings = []

            result = validator._validate_merged_cells(
                mock_wb_generated, mock_wb_template, violations, warnings
            )

            assert result is True
            assert len(violations) == 0

    def test_validate_merged_cells_count_mismatch(self, tmp_path):
        """Test merged cells validation when counts don't match"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_range1 = MagicMock()
        mock_range2 = MagicMock()

        mock_ws_gen = MagicMock()
        mock_ws_gen.merged_cells.ranges = [mock_range1]  # Only 1

        mock_ws_tpl = MagicMock()
        mock_ws_tpl.merged_cells.ranges = [mock_range1, mock_range2]  # 2

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = lambda self, key: mock_ws_gen

        mock_wb_template = MagicMock()
        mock_wb_template.__getitem__ = lambda self, key: mock_ws_tpl

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            validator = Validator(template_path=template_path)
            violations = []
            warnings = []

            result = validator._validate_merged_cells(
                mock_wb_generated, mock_wb_template, violations, warnings
            )

            assert result is False
            assert "병합 셀 개수 불일치" in violations[0]


class TestValidatorValidateCrossReferences:
    """Tests for Validator._validate_cross_references method"""

    def test_validate_cross_references_found(self, tmp_path):
        """Test cross-reference validation with valid references"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_cover = MagicMock()

        # Create cells with cross-references
        def get_cell(cell_ref):
            mock_cell = MagicMock()
            if cell_ref == "H17":
                mock_cell.value = "=+견적서!G48"
            elif cell_ref == "H18":
                mock_cell.value = "=견적서!G49"
            else:
                mock_cell.value = None
            return mock_cell

        mock_ws_cover.__getitem__ = MagicMock(side_effect=get_cell)

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = MagicMock(return_value=mock_ws_cover)

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            validator = Validator(template_path=template_path)
            violations = []
            warnings = []

            result = validator._validate_cross_references(
                mock_wb_generated, violations, warnings
            )

            assert result is True

    def test_validate_cross_references_not_found(self, tmp_path):
        """Test cross-reference validation with no references"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_cover = MagicMock()

        # No cross-references
        def get_cell(cell_ref):
            mock_cell = MagicMock()
            mock_cell.value = None
            return mock_cell

        mock_ws_cover.__getitem__ = MagicMock(side_effect=get_cell)

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = MagicMock(return_value=mock_ws_cover)

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            validator = Validator(template_path=template_path)
            violations = []
            warnings = []

            result = validator._validate_cross_references(
                mock_wb_generated, violations, warnings
            )

            # Still passes but with warning
            assert result is True
            assert len(warnings) > 0
            assert "크로스 참조 없음" in warnings[0]


class TestValidatorValidateTotalConsistency:
    """Tests for Validator._validate_total_consistency method"""

    def test_validate_total_consistency_success(self, tmp_path):
        """Test total consistency validation success"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_estimate = MagicMock()
        mock_ws_cover = MagicMock()

        # Setup cells for estimate sheet
        def get_estimate_cell(cell_ref):
            mock_cell = MagicMock()
            if cell_ref == "B48":
                mock_cell.value = "소  계"
            elif cell_ref == "B49":
                mock_cell.value = "합  계"
            else:
                mock_cell.value = None
            return mock_cell

        mock_ws_estimate.__getitem__ = MagicMock(side_effect=get_estimate_cell)

        # Setup cells for cover sheet
        def get_cover_cell(cell_ref):
            mock_cell = MagicMock()
            if cell_ref == "B18":
                mock_cell.value = "소  계"
            elif cell_ref == "B19":
                mock_cell.value = "합  계"
            else:
                mock_cell.value = None
            return mock_cell

        mock_ws_cover.__getitem__ = MagicMock(side_effect=get_cover_cell)

        def get_sheet(key):
            return mock_ws_estimate if key == "견적서" else mock_ws_cover

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = MagicMock(side_effect=get_sheet)

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            with patch(
                "kis_estimator_core.engine.validator.totals_guard"
            ) as mock_guard:
                mock_guard.return_value = (True, [])

                validator = Validator(template_path=template_path)
                violations = []
                warnings = []
                error_codes = []

                result = validator._validate_total_consistency(
                    mock_wb_generated, violations, warnings, error_codes
                )

                assert result is True

    def test_validate_total_consistency_failure(self, tmp_path):
        """Test total consistency validation failure"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_estimate = MagicMock()
        mock_ws_cover = MagicMock()

        def get_estimate_cell(cell_ref):
            mock_cell = MagicMock()
            if cell_ref == "B48":
                mock_cell.value = "소  계"
            elif cell_ref == "B49":
                mock_cell.value = "합  계"
            else:
                mock_cell.value = None
            return mock_cell

        mock_ws_estimate.__getitem__ = MagicMock(side_effect=get_estimate_cell)

        def get_sheet_2(key):
            return mock_ws_estimate if key == "견적서" else mock_ws_cover

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = MagicMock(side_effect=get_sheet_2)

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            with patch(
                "kis_estimator_core.engine.validator.totals_guard"
            ) as mock_guard:
                mock_guard.return_value = (False, ["Total mismatch"])

                validator = Validator(template_path=template_path)
                violations = []
                warnings = []
                error_codes = []

                result = validator._validate_total_consistency(
                    mock_wb_generated, violations, warnings, error_codes
                )

                assert result is False
                assert "CAL-002" in error_codes

    def test_validate_total_consistency_exception_handling(self, tmp_path):
        """Test total consistency handles exceptions gracefully"""
        template_path = tmp_path / "template.xlsx"
        template_path.touch()

        from kis_estimator_core.engine.validator import Validator

        mock_ws_estimate = MagicMock()

        def get_estimate_cell(cell_ref):
            raise Exception("Cell access error")

        mock_ws_estimate.__getitem__ = MagicMock(side_effect=get_estimate_cell)

        mock_wb_generated = MagicMock()
        mock_wb_generated.__getitem__ = MagicMock(return_value=mock_ws_estimate)

        with patch("kis_estimator_core.engine.validator.load_workbook"):
            validator = Validator(template_path=template_path)
            violations = []
            warnings = []
            error_codes = []

            # Should not raise, returns True with warning
            result = validator._validate_total_consistency(
                mock_wb_generated, violations, warnings, error_codes
            )

            assert result is True
            assert len(warnings) > 0
            assert "합계 검증 중 오류" in warnings[0]


class TestValidationReport:
    """Tests for ValidationReport model"""

    def test_validation_report_passed_property(self):
        """Test ValidationReport.passed property"""
        from kis_estimator_core.engine.models import ValidationReport

        # All True, no violations -> passed
        report = ValidationReport(
            formula_preservation=True,
            merged_cells_intact=True,
            cross_references_valid=True,
            violations=[],
        )

        assert report.passed is True

    def test_validation_report_not_passed_with_violations(self):
        """Test ValidationReport.passed is False with violations"""
        from kis_estimator_core.engine.models import ValidationReport

        report = ValidationReport(
            formula_preservation=True,
            merged_cells_intact=True,
            cross_references_valid=True,
            violations=["Some violation"],
        )

        assert report.passed is False

    def test_validation_report_not_passed_with_failed_check(self):
        """Test ValidationReport.passed is False with failed check"""
        from kis_estimator_core.engine.models import ValidationReport

        report = ValidationReport(
            formula_preservation=False,  # Failed
            merged_cells_intact=True,
            cross_references_valid=True,
            violations=[],
        )

        assert report.passed is False
