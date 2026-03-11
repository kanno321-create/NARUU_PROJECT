"""
Phase XVI: Core Validators Edge Case Testing
Target: guards_format.py coverage improvement (+0.6~1.0%p)

Test Focus:
- Date format validation (Korean format only)
- Size format validation (3D only)
- NO SYNTHETIC DATA

Simplified scope: Focus on helper validators only
"""

from kis_estimator_core.core.ssot.guards_format import (
    validate_date_format,
    validate_size_format,
)


class TestValidateDateFormat:
    """Test validate_date_format() - Korean format only"""

    def test_valid_korean_date(self):
        """Test valid Korean date formats"""
        assert validate_date_format("2025년 10월 31일") is True
        assert validate_date_format("2025년 1월 1일") is True
        assert validate_date_format("2025년  1월  1일") is True  # Extra spaces

    def test_invalid_iso8601_date(self):
        """Test ISO8601 format is NOT accepted (Korean only)"""
        assert validate_date_format("2025-10-31") is False
        assert validate_date_format("2025-01-01") is False

    def test_invalid_us_date(self):
        """Test US format is NOT accepted"""
        assert validate_date_format("10/31/2025") is False

    def test_invalid_date_formats(self):
        """Test invalid date formats"""
        assert validate_date_format("invalid") is False
        assert validate_date_format("") is False


class TestValidateSizeFormat:
    """Test validate_size_format() - 3D format only"""

    def test_valid_3d_sizes(self):
        """Test valid 3D size formats (W×H×D)"""
        assert validate_size_format("600×800×150") is True
        assert validate_size_format("1200×1600×300") is True
        assert validate_size_format("600*800*150") is True  # * also allowed

    def test_invalid_2d_sizes(self):
        """Test 2D format is NOT accepted (3D only)"""
        assert validate_size_format("600×800") is False
        assert validate_size_format("1200×1600") is False

    def test_boundary_sizes(self):
        """Test boundary size values"""
        assert validate_size_format("1×1×1") is True  # Minimum
        assert validate_size_format("9999×9999×9999") is True  # Large

    def test_invalid_size_formats(self):
        """Test invalid size formats"""
        assert validate_size_format("600x800x150") is False  # Lowercase x
        assert validate_size_format("invalid") is False
        assert validate_size_format("") is False


class TestValidationEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_date_format_empty_string(self):
        """Test empty string returns False"""
        assert validate_date_format("") is False

    def test_size_format_empty_string(self):
        """Test empty string returns False"""
        assert validate_size_format("") is False

    def test_date_format_whitespace(self):
        """Test whitespace-only string"""
        assert validate_date_format("   ") is False

    def test_size_format_whitespace(self):
        """Test whitespace-only string"""
        assert validate_size_format("   ") is False
