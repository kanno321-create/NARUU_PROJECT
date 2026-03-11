"""
Unit Tests for validators/items.py
Coverage target: 100% for validate_qty and validate_price
"""

import pytest

from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError
from kis_estimator_core.validators.items import validate_price, validate_qty


class TestValidateQty:
    """Tests for validate_qty function"""

    def test_validate_qty_valid_one(self):
        """Test qty=1 passes validation"""
        validate_qty(1)  # Should not raise

    def test_validate_qty_valid_large(self):
        """Test large qty passes validation"""
        validate_qty(1000)  # Should not raise

    def test_validate_qty_valid_with_index(self):
        """Test with custom item_idx"""
        validate_qty(5, item_idx=10)  # Should not raise

    def test_validate_qty_zero_raises(self):
        """Test qty=0 raises E_VALIDATION"""
        with pytest.raises(EstimatorError) as exc:
            validate_qty(0)
        assert exc.value.payload.code == ErrorCode.E_VALIDATION.value
        assert "qty>=1 required" in str(exc.value)

    def test_validate_qty_negative_raises(self):
        """Test negative qty raises E_VALIDATION"""
        with pytest.raises(EstimatorError) as exc:
            validate_qty(-1)
        assert exc.value.payload.code == ErrorCode.E_VALIDATION.value
        assert "qty>=1 required" in str(exc.value)

    def test_validate_qty_none_raises(self):
        """Test None qty raises E_VALIDATION"""
        with pytest.raises(EstimatorError) as exc:
            validate_qty(None)
        assert exc.value.payload.code == ErrorCode.E_VALIDATION.value
        assert "qty>=1 required" in str(exc.value)

    def test_validate_qty_error_includes_item_idx(self):
        """Test error message includes item index"""
        with pytest.raises(EstimatorError) as exc:
            validate_qty(-5, item_idx=7)
        assert "Item 7" in str(exc.value)
        assert "-5" in str(exc.value)


class TestValidatePrice:
    """Tests for validate_price function"""

    def test_validate_price_zero(self):
        """Test price=0 passes (free items allowed)"""
        validate_price(0.0)  # Should not raise

    def test_validate_price_positive(self):
        """Test positive price passes"""
        validate_price(100.5)  # Should not raise

    def test_validate_price_large(self):
        """Test large price passes"""
        validate_price(999999999.99)  # Should not raise

    def test_validate_price_with_index(self):
        """Test with custom item_idx"""
        validate_price(50.0, item_idx=3)  # Should not raise

    def test_validate_price_negative_raises(self):
        """Test negative price raises E_VALIDATION"""
        with pytest.raises(EstimatorError) as exc:
            validate_price(-1.0)
        assert exc.value.payload.code == ErrorCode.E_VALIDATION.value
        assert "unit_price must be non-negative" in str(exc.value)

    def test_validate_price_negative_small_raises(self):
        """Test small negative price raises E_VALIDATION"""
        with pytest.raises(EstimatorError) as exc:
            validate_price(-0.01)
        assert exc.value.payload.code == ErrorCode.E_VALIDATION.value

    def test_validate_price_error_includes_item_idx(self):
        """Test error message includes item index"""
        with pytest.raises(EstimatorError) as exc:
            validate_price(-100.0, item_idx=5)
        assert "Item 5" in str(exc.value)
        assert "-100" in str(exc.value)
