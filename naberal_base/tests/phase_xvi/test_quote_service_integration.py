"""
Phase XVI: Quote Service Integration Testing
Target: quote_service.py coverage improvement (+0.8~1.5%p)

Test Focus:
- UOM/할인/VAT/라운딩 조합 totals 일치
- 승인 임계 경계
- RBAC 연계 (403/200)
- Evidence hash 재현성
- Invalid inputs (E_VALIDATION)

NO SYNTHETIC DATA - All tests use SSOT constants

Note: Error message format aligned with validators/items.py
(commit 56f68405: Phase X CI lift)
"""

import pytest
from unittest.mock import MagicMock
from kis_estimator_core.services.quote_service import QuoteService


class TestQuoteServiceInitialization:
    """Test QuoteService initialization"""

    def test_init_with_db_session(self):
        """Test initialization with database session"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)
        assert service.db == mock_db


class TestQuoteServiceCalculateTotals:
    """Test _calculate_totals() with UOM/discount/VAT"""

    def test_calculate_totals_simple(self):
        """Test simple totals calculation (no discount)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items = [
            {"sku": "ITEM1", "quantity": 2, "unit_price": 10000, "uom": "EA"},
            {"sku": "ITEM2", "quantity": 1, "unit_price": 5000, "uom": "EA"},
        ]

        totals = service._calculate_totals(items)

        assert totals["subtotal"] == 25000  # 2*10000 + 1*5000
        # VAT 10%: 25000 * 0.10 = 2500
        assert totals["vat"] == 2500
        assert totals["total"] == 27500  # 25000 + 2500

    def test_calculate_totals_with_discount(self):
        """Test totals with discount tier (SSOT)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items = [
            {
                "sku": "ITEM1",
                "quantity": 1,
                "unit_price": 10000,
                "uom": "EA",
                "discount_tier": "A",  # SSOT: 5% discount
            }
        ]

        totals = service._calculate_totals(items)

        assert totals["subtotal"] == 10000
        assert totals["discount"] == 500  # 5% of 10000 (tier "A")
        # VAT 10% on (subtotal - discount): (10000 - 500) * 0.10 = 950
        assert totals["vat"] == 950
        assert totals["total"] == 10450  # 10000 - 500 + 950

    def test_calculate_totals_consistency(self):
        """Test totals calculation consistency (same input → same output)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items = [
            {"sku": "ITEM1", "quantity": 3, "unit_price": 15000, "uom": "EA"},
            {"sku": "ITEM2", "quantity": 2, "unit_price": 8000, "uom": "EA"},
        ]

        totals1 = service._calculate_totals(items)
        totals2 = service._calculate_totals(items)

        # Same input should produce identical results
        assert totals1 == totals2
        assert totals1["subtotal"] == 61000  # 3*15000 + 2*8000


class TestQuoteServiceApprovalThreshold:
    """Test _is_approval_required() threshold boundaries (SSOT: 50M KRW)"""

    def test_approval_required_above_threshold(self):
        """Test approval required for high value quotes (>50M KRW)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        # SSOT threshold: 50,000,000 KRW
        total = 55_000_000  # Above threshold
        result = service._is_approval_required(total)

        assert result is True  # Should require approval

    def test_approval_not_required_below_threshold(self):
        """Test approval not required for low value quotes (<50M KRW)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        total = 45_000_000  # Below threshold
        result = service._is_approval_required(total)

        assert result is False  # Should NOT require approval

    def test_approval_boundary_at_threshold(self):
        """Test approval at exact threshold boundary (=50M KRW)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        # SSOT threshold: exactly 50,000,000 KRW
        total = 50_000_000
        result = service._is_approval_required(total)

        assert result is True  # At threshold: requires approval (>=)


class TestQuoteServiceEvidenceHash:
    """Test _generate_evidence_hash() reproducibility"""

    def test_evidence_hash_reproducible(self):
        """Test evidence hash is reproducible (same input → same hash)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items = [
            {"sku": "ITEM1", "quantity": 1, "unit_price": 10000},
            {"sku": "ITEM2", "quantity": 2, "unit_price": 5000},
        ]

        hash1 = service._generate_evidence_hash(items)
        hash2 = service._generate_evidence_hash(items)

        # Same items should produce same hash
        assert hash1 == hash2
        assert len(hash1) > 0

    def test_evidence_hash_different_inputs(self):
        """Test different items produce different hashes"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items1 = [{"sku": "ITEM1", "quantity": 1, "unit_price": 10000}]
        items2 = [{"sku": "ITEM2", "quantity": 1, "unit_price": 10000}]

        hash1 = service._generate_evidence_hash(items1)
        hash2 = service._generate_evidence_hash(items2)

        # Different items should produce different hashes
        assert hash1 != hash2


class TestQuoteServiceValidation:
    """Test _validate_items() input validation"""

    def test_validate_items_valid(self):
        """Test validation passes for valid items (SSOT UOM)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        items = [{"sku": "ITEM1", "quantity": 1, "unit_price": 10000, "uom": "EA"}]

        try:
            service._validate_items(items)
            # Should not raise exception (all required fields present)
        except Exception as e:
            pytest.fail(f"Valid items should not raise exception: {e}")

    def test_validate_items_missing_required_field(self):
        """Test validation fails for missing required fields"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        # Missing 'sku'
        items = [{"quantity": 1, "unit_price": 10000}]

        with pytest.raises(Exception):
            service._validate_items(items)

    def test_validate_items_invalid_quantity(self):
        """Test validation fails for invalid quantity (E_VALIDATION)"""
        mock_db = MagicMock()
        service = QuoteService(db=mock_db)

        # Negative quantity (should raise E_VALIDATION)
        items = [{"sku": "ITEM1", "quantity": -1, "unit_price": 10000, "uom": "EA"}]

        with pytest.raises(Exception) as exc_info:
            service._validate_items(items)

        # Verify error contains validation message (validators/items.py format)
        assert "qty>=1 required" in str(exc_info.value)
