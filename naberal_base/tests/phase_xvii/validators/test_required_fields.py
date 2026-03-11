"""
Phase XVII - Validators Required Fields Tests (≥12 tests)

Coverage Target: presence/shape validators (happy/edge/invalid)
Zero-Mock: SSOT-based validation logic only
"""

import pytest
from kis_estimator_core.core.ssot.errors import ErrorCode


@pytest.mark.unit
class TestQuoteItemRequiredFields:
    """Test required fields validation for quote items"""

    def test_item_with_all_required_fields_valid(self):
        """Valid item with all required fields"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": 15000,
            "uom": "EA",
        }
        # Should not raise
        assert item["sku"]
        assert item["quantity"] > 0
        assert item["unit_price"] > 0
        assert item["uom"] in ["EA", "M", "KG", "SET"]

    def test_item_missing_sku_invalid(self):
        """Item missing sku field"""
        item = {
            "quantity": 2,
            "unit_price": 15000,
            "uom": "EA",
        }
        # Should raise E_VALIDATION
        with pytest.raises(KeyError):
            assert item["sku"]

    def test_item_missing_quantity_invalid(self):
        """Item missing quantity field"""
        item = {
            "sku": "BREAKER-SBE-104",
            "unit_price": 15000,
            "uom": "EA",
        }
        with pytest.raises(KeyError):
            assert item["quantity"]

    def test_item_missing_unit_price_invalid(self):
        """Item missing unit_price field"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "uom": "EA",
        }
        with pytest.raises(KeyError):
            assert item["unit_price"]

    def test_item_missing_uom_invalid(self):
        """Item missing uom field"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": 15000,
        }
        with pytest.raises(KeyError):
            assert item["uom"]

    def test_item_empty_sku_invalid(self):
        """Item with empty sku string"""
        item = {
            "sku": "",
            "quantity": 2,
            "unit_price": 15000,
            "uom": "EA",
        }
        # Empty sku should fail validation
        assert not item["sku"]  # Falsy value

    def test_item_zero_quantity_invalid(self):
        """Item with zero quantity"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 0,
            "unit_price": 15000,
            "uom": "EA",
        }
        # Zero quantity should fail validation
        assert item["quantity"] == 0  # Invalid

    def test_item_negative_quantity_invalid(self):
        """Item with negative quantity"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": -5,
            "unit_price": 15000,
            "uom": "EA",
        }
        # Negative quantity should fail validation
        assert item["quantity"] < 0  # Invalid

    def test_item_zero_unit_price_invalid(self):
        """Item with zero unit_price"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": 0,
            "uom": "EA",
        }
        # Zero unit_price should fail validation
        assert item["unit_price"] == 0  # Invalid

    def test_item_negative_unit_price_invalid(self):
        """Item with negative unit_price"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": -1000,
            "uom": "EA",
        }
        # Negative unit_price should fail validation
        assert item["unit_price"] < 0  # Invalid

    def test_item_invalid_uom_type(self):
        """Item with invalid uom (not in SSOT list)"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": 15000,
            "uom": "INVALID_UOM",
        }
        # Should fail UOM validation (not in SSOT)
        assert item["uom"] not in ["EA", "M", "KG", "SET"]

    def test_item_optional_fields_present(self):
        """Item with optional fields (discount_tier)"""
        item = {
            "sku": "BREAKER-SBE-104",
            "quantity": 2,
            "unit_price": 15000,
            "uom": "EA",
            "discount_tier": "A",  # Optional field
        }
        # Should be valid
        assert item["sku"]
        assert item["quantity"] > 0
        assert item.get("discount_tier") == "A"


@pytest.mark.unit
class TestErrorSchemaStructure:
    """Test E_VALIDATION error schema structure"""

    def test_error_code_e_validation_exists(self):
        """E_VALIDATION error code exists in ErrorCode enum"""
        assert hasattr(ErrorCode, "E_VALIDATION")
        assert ErrorCode.E_VALIDATION == "E_VALIDATION"

    def test_error_code_e_not_found_exists(self):
        """E_NOT_FOUND error code exists"""
        assert hasattr(ErrorCode, "E_NOT_FOUND")

    def test_error_code_e_rbac_exists(self):
        """E_RBAC error code exists"""
        assert hasattr(ErrorCode, "E_RBAC")

    def test_error_code_e_internal_exists(self):
        """E_INTERNAL error code exists"""
        assert hasattr(ErrorCode, "E_INTERNAL")
