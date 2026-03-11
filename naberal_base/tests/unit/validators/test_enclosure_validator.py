"""
Unit tests for validators/enclosure_validator.py - Enclosure Input Validator

Target: 80% coverage for enclosure_validator.py (44 lines)
Principles:
- Zero-Mock: Real validation logic with SSOT constants
- AF-Pole combination validation
- UOM normalization (mm/cm/inch)
- Dimension range checking

Test Count: 11 tests
"""

import pytest

from kis_estimator_core.validators.enclosure_validator import (
    validate_breaker_spec,
    normalize_dimension_uom,
    validate_dimension_range,
    validate_enclosure_input,
)
from kis_estimator_core.errors.exceptions import ValidationError


# ============================================================================
# Test 1-4: validate_breaker_spec (AF-Pole Combinations)
# ============================================================================


@pytest.mark.unit
def test_validate_breaker_spec_valid_combinations():
    """Test 1: Valid AF-Pole combinations pass"""
    # 50AF 2P (valid)
    breaker_50af_2p = {"frame_af": 50, "poles": 2, "model": "SBE-52"}
    validate_breaker_spec(breaker_50af_2p)  # Should not raise

    # 100AF 4P (valid)
    breaker_100af_4p = {"frame_af": 100, "poles": 4, "model": "SBE-104"}
    validate_breaker_spec(breaker_100af_4p)  # Should not raise

    # 400AF 3P (valid)
    breaker_400af_3p = {"frame_af": 400, "poles": 3, "model": "SBS-403"}
    validate_breaker_spec(breaker_400af_3p)  # Should not raise


@pytest.mark.unit
def test_validate_breaker_spec_32af_only_2p():
    """Test 2: 32AF small breakers only allow 2P"""
    # 32AF 2P (valid)
    breaker_32af_2p = {"frame_af": 32, "poles": 2, "model": "SIB-32"}
    validate_breaker_spec(breaker_32af_2p)  # Should not raise

    # 32AF 3P (INVALID - 32AF only supports 2P)
    breaker_32af_3p = {"frame_af": 32, "poles": 3, "model": "INVALID"}
    with pytest.raises(ValidationError):
        validate_breaker_spec(breaker_32af_3p)


@pytest.mark.unit
def test_validate_breaker_spec_400af_no_2p():
    """Test 3: 400AF and above do not support 2P"""
    # 400AF 2P (INVALID - 400AF+ only supports 3P/4P)
    breaker_400af_2p = {"frame_af": 400, "poles": 2, "model": "INVALID"}
    with pytest.raises(ValidationError):
        validate_breaker_spec(breaker_400af_2p)


@pytest.mark.unit
def test_validate_breaker_spec_invalid_af():
    """Test 4: Invalid AF values raise ValidationError"""
    # Invalid AF (not in VALID_AF_VALUES)
    breaker_invalid_af = {"frame_af": 999, "poles": 2, "model": "INVALID"}
    with pytest.raises(ValidationError):
        validate_breaker_spec(breaker_invalid_af)


# ============================================================================
# Test 5-7: normalize_dimension_uom (UOM Conversion)
# ============================================================================


@pytest.mark.unit
def test_normalize_dimension_uom_numeric():
    """Test 5: Numeric values passed through as mm"""
    # Integer
    result_int = normalize_dimension_uom(600, "width")
    assert result_int == 600.0

    # Float
    result_float = normalize_dimension_uom(450.5, "height")
    assert result_float == 450.5


@pytest.mark.unit
def test_normalize_dimension_uom_string_with_units():
    """Test 6: String values with units converted to mm"""
    # mm (no conversion)
    result_mm = normalize_dimension_uom("600mm", "width")
    assert result_mm == 600.0

    # cm (× 10)
    result_cm = normalize_dimension_uom("60cm", "width")
    assert result_cm == 600.0

    # inch (× 25.4)
    result_inch = normalize_dimension_uom("10inch", "depth")
    assert result_inch == 254.0


@pytest.mark.unit
def test_normalize_dimension_uom_invalid_format():
    """Test 7: Invalid format raises ValidationError"""
    # Invalid string (no unit)
    with pytest.raises(ValidationError):
        normalize_dimension_uom("invalid_value", "width")


# ============================================================================
# Test 8-9: validate_dimension_range
# ============================================================================


@pytest.mark.unit
def test_validate_dimension_range_within_bounds():
    """Test 8: Values within range pass"""
    # Within range
    validate_dimension_range(500.0, "width", 300.0, 1000.0)  # Should not raise
    validate_dimension_range(300.0, "width", 300.0, 1000.0)  # Boundary (min)
    validate_dimension_range(1000.0, "width", 300.0, 1000.0)  # Boundary (max)


@pytest.mark.unit
def test_validate_dimension_range_out_of_bounds():
    """Test 9: Values outside range raise ValidationError"""
    # Below minimum
    with pytest.raises(ValidationError):
        validate_dimension_range(200.0, "width", 300.0, 1000.0)

    # Above maximum
    with pytest.raises(ValidationError):
        validate_dimension_range(1500.0, "height", 400.0, 1200.0)


# ============================================================================
# Test 10-11: validate_enclosure_input (Full Validation)
# ============================================================================


@pytest.mark.unit
def test_validate_enclosure_input_all_valid():
    """Test 10: Full validation with all valid inputs"""
    main_breaker = {"frame_af": 100, "poles": 4, "model": "SBE-104"}
    branch_breakers = [
        {"frame_af": 50, "poles": 2, "model": "SBE-52"},
        {"frame_af": 100, "poles": 3, "model": "SBE-103"},
    ]

    # Should not raise
    validate_enclosure_input(main_breaker, branch_breakers)


@pytest.mark.unit
def test_validate_enclosure_input_invalid_branch():
    """Test 11: Full validation catches invalid branch breaker"""
    main_breaker = {"frame_af": 100, "poles": 4, "model": "SBE-104"}
    branch_breakers = [
        {"frame_af": 50, "poles": 2, "model": "SBE-52"},  # Valid
        {
            "frame_af": 32,
            "poles": 4,
            "model": "INVALID",
        },  # INVALID (32AF only supports 2P)
    ]

    with pytest.raises(ValidationError):
        validate_enclosure_input(main_breaker, branch_breakers)
