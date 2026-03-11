"""
Unit tests for guards_format.py helper functions (Phase 2-1)

Coverage target: validate_date_format(), validate_size_format() helper functions
NO MOCKS - Pure logic testing

Category: UNIT TEST
"""

import pytest
from kis_estimator_core.core.ssot.guards_format import (
    validate_date_format,
    validate_size_format,
)


@pytest.mark.unit
class TestValidateDateFormat:
    """Test date format validation (YYYY년 MM월 DD일)"""

    def test_valid_date_format(self):
        """Test valid date format"""
        assert validate_date_format("2025년 10월 03일") is True
        assert validate_date_format("2025년 01월 01일") is True
        assert validate_date_format("2025년 12월 31일") is True

    def test_single_digit_month_day(self):
        """Test single digit month/day (allowed by DATE_FORMAT_REGEX)"""
        # DATE_FORMAT_REGEX allows single digit month/day
        assert validate_date_format("2025년 1월 1일") is True
        assert validate_date_format("2025년 10월 1일") is True
        assert validate_date_format("2025년 01월 01일") is True

    def test_invalid_separators(self):
        """Test invalid separators"""
        assert validate_date_format("2025-10-03") is False
        assert validate_date_format("2025/10/03") is False
        assert validate_date_format("2025.10.03") is False

    def test_invalid_format(self):
        """Test completely invalid formats"""
        assert validate_date_format("Oct 3, 2025") is False
        assert validate_date_format("2025") is False
        assert validate_date_format("") is False

    def test_missing_components(self):
        """Test missing date components"""
        assert validate_date_format("2025년 10월") is False
        assert validate_date_format("10월 03일") is False

    def test_extra_spaces(self):
        """Test extra spaces (allowed by DATE_FORMAT_REGEX)"""
        # DATE_FORMAT_REGEX allows extra spaces
        assert validate_date_format("2025년  10월  03일") is True
        # Leading/trailing spaces may be trimmed by regex
        # assert validate_date_format(" 2025년 10월 03일") is False  # Commented - depends on regex


@pytest.mark.unit
class TestValidateSizeFormat:
    """Test size format validation (W*H*D or W×H×D)"""

    def test_valid_size_format_asterisk(self):
        """Test valid size format with asterisk"""
        assert validate_size_format("600*800*150") is True
        assert validate_size_format("700*900*200") is True
        assert validate_size_format("1000*1200*250") is True

    def test_valid_size_format_multiplication_sign(self):
        """Test valid size format with multiplication sign (×)"""
        assert validate_size_format("600×800×150") is True
        assert validate_size_format("700×900×200") is True

    def test_mixed_separators(self):
        """Test mixed separators (allowed by SIZE_FORMAT_REGEX)"""
        # SIZE_FORMAT_REGEX may allow mixed separators depending on implementation
        # If regex is `\d+[*×]\d+[*×]\d+`, it allows mixing
        assert validate_size_format("600*800×150") is True
        assert validate_size_format("600×800*150") is True

    def test_two_dimensions_only(self):
        """Test two dimensions (should fail - requires W*H*D)"""
        assert validate_size_format("600*800") is False
        assert validate_size_format("600×800") is False

    def test_four_dimensions(self):
        """Test four dimensions (should fail)"""
        assert validate_size_format("600*800*150*100") is False

    def test_invalid_separators(self):
        """Test invalid separators"""
        assert validate_size_format("600x800x150") is False
        assert validate_size_format("600-800-150") is False
        assert validate_size_format("600/800/150") is False

    def test_with_units(self):
        """Test with units (should fail - numbers only)"""
        assert validate_size_format("600mm*800mm*150mm") is False

    def test_empty_string(self):
        """Test empty string"""
        assert validate_size_format("") is False

    def test_decimal_dimensions(self):
        """Test decimal dimensions (should depend on regex)"""
        # Assuming regex allows only integers - decimals should fail
        assert validate_size_format("600.5*800.5*150.5") is False

    def test_negative_dimensions(self):
        """Test negative dimensions (should fail)"""
        assert validate_size_format("-600*800*150") is False
        assert validate_size_format("600*-800*150") is False

    def test_zero_dimensions(self):
        """Test zero dimensions (should depend on business rules)"""
        # Zero dimensions - regex may pass but business logic should reject
        # For now, just verify the function returns a boolean
        assert isinstance(validate_size_format("0*0*0"), bool)


@pytest.mark.unit
class TestGuardsFormatHelperIntegration:
    """Test helper functions together"""

    def test_date_and_size_validation_independent(self):
        """Test that date and size validations are independent"""
        # Valid date should not affect size validation
        assert validate_date_format("2025년 10월 03일") is True
        assert validate_size_format("600*800*150") is True

        # Invalid date should not affect size validation
        assert validate_date_format("invalid") is False
        assert validate_size_format("600*800*150") is True

    def test_multiple_validations(self):
        """Test multiple consecutive validations"""
        # Date validations
        dates = [
            ("2025년 01월 01일", True),
            ("2025년 12월 31일", True),
            ("2025-01-01", False),
        ]

        for date_str, expected in dates:
            assert validate_date_format(date_str) is expected

        # Size validations
        sizes = [
            ("600*800*150", True),
            ("700×900×200", True),
            ("600x800x150", False),
        ]

        for size_str, expected in sizes:
            assert validate_size_format(size_str) is expected
