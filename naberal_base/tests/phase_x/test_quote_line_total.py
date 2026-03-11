"""
Phase X: Quote Line Total and Approval Required Tests

Tests for:
- QuoteService._add_line_totals() calculation logic
- get_quote() returning items with line_total
- get_quote() returning approval_required field

Contract-First / SSOT / Zero-Mock
"""

import os
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# Skip in CI if SSOT loaders not available
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true" and os.getenv("SKIP_QUOTE_LINE_TOTAL_TESTS") == "true",
    reason="Skipping Quote line_total tests in CI - requires full SSOT environment"
)


# ========================================================================
# Test Class 1: _add_line_totals() Unit Tests
# ========================================================================


class TestAddLineTotals:
    """Test QuoteService._add_line_totals() calculation logic"""

    @pytest.fixture
    def mock_service(self):
        """Create QuoteService with mocked SSOT loaders"""
        with patch(
            "kis_estimator_core.services.quote_service.load_uom"
        ) as mock_uom, patch(
            "kis_estimator_core.services.quote_service.load_discounts"
        ) as mock_discounts, patch(
            "kis_estimator_core.services.quote_service.load_rounding"
        ) as mock_rounding, patch(
            "kis_estimator_core.services.quote_service.load_approval_threshold"
        ) as mock_approval:
            from kis_estimator_core.services.quote_service import QuoteService

            mock_uom.return_value = ["EA", "KG", "M", "식", "면"]
            mock_discounts.return_value = [
                {"tier": "STANDARD", "rate": 0.05},
                {"tier": "VIP", "rate": 0.12},  # SSOT: 12% discount
                {"tier": "BULK", "rate": 0.15},
            ]
            mock_rounding.return_value = {
                "currency": "KRW",
                "precision": 0,
                "vat_pct": 0.10,
            }
            mock_approval.return_value = {"amount": 50000000}

            mock_db = AsyncMock()
            service = QuoteService(db=mock_db)
            yield service

    def test_line_total_no_discount(self, mock_service):
        """Test line_total = quantity × unit_price when no discount"""
        items = [
            {"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"},
            {"sku": "PANEL-001", "quantity": 1, "unit_price": 200000, "uom": "면"},
        ]

        result = mock_service._add_line_totals(items)

        assert len(result) == 2
        assert result[0]["line_total"] == 50000  # 10 × 5000
        assert result[1]["line_total"] == 200000  # 1 × 200000

    def test_line_total_with_vip_discount(self, mock_service):
        """Test line_total with VIP discount (12% per SSOT)"""
        items = [
            {
                "sku": "BRK-001",
                "quantity": 100,
                "unit_price": 10000,
                "uom": "EA",
                "discount_tier": "VIP",
            },
        ]

        result = mock_service._add_line_totals(items)

        # line_total = 100 × 10000 × (1 - 0.12) = 880,000
        assert result[0]["line_total"] == 880000

    def test_line_total_with_bulk_discount(self, mock_service):
        """Test line_total with BULK discount (15%)"""
        items = [
            {
                "sku": "CABLE-001",
                "quantity": 50,
                "unit_price": 20000,
                "uom": "M",
                "discount_tier": "BULK",
            },
        ]

        result = mock_service._add_line_totals(items)

        # line_total = 50 × 20000 × (1 - 0.15) = 850,000
        assert result[0]["line_total"] == 850000

    def test_line_total_with_standard_discount(self, mock_service):
        """Test line_total with STANDARD discount (5%)"""
        items = [
            {
                "sku": "BRK-002",
                "quantity": 20,
                "unit_price": 10000,
                "uom": "EA",
                "discount_tier": "STANDARD",
            },
        ]

        result = mock_service._add_line_totals(items)

        # line_total = 20 × 10000 × (1 - 0.05) = 190,000
        assert result[0]["line_total"] == 190000

    def test_line_total_mixed_items(self, mock_service):
        """Test line_total with mixed discount and non-discount items"""
        items = [
            {"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"},  # No discount
            {
                "sku": "BRK-002",
                "quantity": 20,
                "unit_price": 10000,
                "uom": "EA",
                "discount_tier": "VIP",  # 12% discount (SSOT)
            },
        ]

        result = mock_service._add_line_totals(items)

        assert result[0]["line_total"] == 50000  # 10 × 5000 × 1.0
        assert result[1]["line_total"] == 176000  # 20 × 10000 × 0.88

    def test_line_total_preserves_original_fields(self, mock_service):
        """Test _add_line_totals preserves all original item fields"""
        items = [
            {
                "sku": "BRK-001",
                "quantity": 10,
                "unit_price": 5000,
                "uom": "EA",
                "discount_tier": "VIP",
                "custom_field": "should_be_preserved",
            },
        ]

        result = mock_service._add_line_totals(items)

        assert result[0]["sku"] == "BRK-001"
        assert result[0]["quantity"] == 10
        assert result[0]["unit_price"] == 5000
        assert result[0]["uom"] == "EA"
        assert result[0]["discount_tier"] == "VIP"
        assert result[0]["custom_field"] == "should_be_preserved"
        assert "line_total" in result[0]

    def test_line_total_does_not_mutate_original(self, mock_service):
        """Test _add_line_totals does not mutate original items list"""
        original_items = [
            {"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"},
        ]

        result = mock_service._add_line_totals(original_items)

        # Original should not have line_total
        assert "line_total" not in original_items[0]
        # Result should have line_total
        assert "line_total" in result[0]

    def test_line_total_with_unknown_discount_tier(self, mock_service):
        """Test line_total defaults to 0% discount for unknown tier"""
        items = [
            {
                "sku": "BRK-001",
                "quantity": 10,
                "unit_price": 5000,
                "uom": "EA",
                "discount_tier": "UNKNOWN_TIER",  # Not in SSOT
            },
        ]

        result = mock_service._add_line_totals(items)

        # Should default to no discount
        assert result[0]["line_total"] == 50000  # 10 × 5000 × 1.0

    def test_line_total_empty_list(self, mock_service):
        """Test _add_line_totals handles empty list"""
        result = mock_service._add_line_totals([])
        assert result == []

    def test_line_total_missing_fields_defensive(self, mock_service):
        """Test _add_line_totals handles missing fields gracefully (backward compatibility)"""
        # Simulate old DB records with incomplete data
        items = [
            {"sku": "BRK-001", "quantity": 10},  # Missing unit_price
            {"sku": "BRK-002", "unit_price": 5000},  # Missing quantity
            {"sku": "BRK-003"},  # Missing both
        ]

        result = mock_service._add_line_totals(items)

        assert len(result) == 3
        # line_total = 10 * 0 = 0 (missing unit_price defaults to 0)
        assert result[0]["line_total"] == 0
        # line_total = 0 * 5000 = 0 (missing quantity defaults to 0)
        assert result[1]["line_total"] == 0
        # line_total = 0 * 0 = 0 (both missing)
        assert result[2]["line_total"] == 0


# ========================================================================
# Test Class 2: get_quote() Returns line_total and approval_required
# ========================================================================


class TestGetQuoteReturnsLineTotalAndApprovalRequired:
    """Test get_quote() returns items with line_total and approval_required flag"""

    @pytest.fixture
    def mock_service(self):
        """Create QuoteService with mocked SSOT loaders"""
        with patch(
            "kis_estimator_core.services.quote_service.load_uom"
        ) as mock_uom, patch(
            "kis_estimator_core.services.quote_service.load_discounts"
        ) as mock_discounts, patch(
            "kis_estimator_core.services.quote_service.load_rounding"
        ) as mock_rounding, patch(
            "kis_estimator_core.services.quote_service.load_approval_threshold"
        ) as mock_approval:
            from kis_estimator_core.services.quote_service import QuoteService

            mock_uom.return_value = ["EA", "KG", "M"]
            mock_discounts.return_value = [
                {"tier": "STANDARD", "rate": 0.05},
                {"tier": "VIP", "rate": 0.12},  # SSOT: 12% discount
            ]
            mock_rounding.return_value = {
                "currency": "KRW",
                "precision": 0,
                "vat_pct": 0.10,
            }
            mock_approval.return_value = {"amount": 50000000}

            mock_db = AsyncMock()
            service = QuoteService(db=mock_db)
            yield service

    @pytest.mark.asyncio
    async def test_get_quote_items_have_line_total(self, mock_service):
        """Test get_quote returns items with calculated line_total"""
        quote_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Mock DB row with items containing discount_tier
        mock_row = (
            quote_id,
            [
                {"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"},
                {"sku": "BRK-002", "quantity": 5, "unit_price": 10000, "uom": "EA", "discount_tier": "VIP"},
            ],
            "Test Client",
            "NET30",
            {"subtotal": 100000, "discount": 5000, "vat": 9500, "total": 104500, "currency": "KRW"},
            "DRAFT",
            "abc123hash",
            created_at,
            created_at,
            None,
            None,
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_service.db.execute.return_value = mock_result

        result = await mock_service.get_quote(quote_id)

        # Verify items have line_total
        assert "items" in result
        assert len(result["items"]) == 2
        assert "line_total" in result["items"][0]
        assert "line_total" in result["items"][1]

        # Verify line_total calculations
        assert result["items"][0]["line_total"] == 50000  # 10 × 5000 × 1.0
        assert result["items"][1]["line_total"] == 44000  # 5 × 10000 × 0.88 (VIP 12%)

    @pytest.mark.asyncio
    async def test_get_quote_returns_approval_required_false(self, mock_service):
        """Test get_quote returns approval_required=false for total < 50M"""
        quote_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Total = 49,000,000 KRW (< 50M threshold)
        mock_row = (
            quote_id,
            [{"sku": "BRK-001", "quantity": 1, "unit_price": 44545454, "uom": "EA"}],
            "Test Client",
            "NET30",
            {"subtotal": 44545454, "discount": 0, "vat": 4454546, "total": 49000000, "currency": "KRW"},
            "DRAFT",
            "abc123hash",
            created_at,
            created_at,
            None,
            None,
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_service.db.execute.return_value = mock_result

        result = await mock_service.get_quote(quote_id)

        assert "approval_required" in result
        assert result["approval_required"] is False

    @pytest.mark.asyncio
    async def test_get_quote_returns_approval_required_true(self, mock_service):
        """Test get_quote returns approval_required=true for total >= 50M"""
        quote_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Total = 55,000,000 KRW (>= 50M threshold)
        mock_row = (
            quote_id,
            [{"sku": "LARGE-001", "quantity": 1, "unit_price": 50000000, "uom": "EA"}],
            "Large Client",
            "NET30",
            {"subtotal": 50000000, "discount": 0, "vat": 5000000, "total": 55000000, "currency": "KRW"},
            "DRAFT",
            "abc123hash",
            created_at,
            created_at,
            None,
            None,
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_service.db.execute.return_value = mock_result

        result = await mock_service.get_quote(quote_id)

        assert "approval_required" in result
        assert result["approval_required"] is True

    @pytest.mark.asyncio
    async def test_get_quote_returns_approval_required_at_threshold(self, mock_service):
        """Test get_quote returns approval_required=true for total == 50M exactly"""
        quote_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Total = exactly 50,000,000 KRW (== 50M threshold)
        mock_row = (
            quote_id,
            [{"sku": "THRESHOLD-001", "quantity": 1, "unit_price": 45454545, "uom": "EA"}],
            "Threshold Client",
            "NET30",
            {"subtotal": 45454545, "discount": 0, "vat": 4545455, "total": 50000000, "currency": "KRW"},
            "DRAFT",
            "abc123hash",
            created_at,
            created_at,
            None,
            None,
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_service.db.execute.return_value = mock_result

        result = await mock_service.get_quote(quote_id)

        assert "approval_required" in result
        assert result["approval_required"] is True  # >= threshold

    @pytest.mark.asyncio
    async def test_get_quote_returns_all_required_fields(self, mock_service):
        """Test get_quote returns all required fields per schema"""
        quote_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        mock_row = (
            quote_id,
            [{"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"}],
            "Test Client",
            "NET30",
            {"subtotal": 50000, "discount": 0, "vat": 5000, "total": 55000, "currency": "KRW"},
            "DRAFT",
            "abc123hash",
            created_at,
            created_at,
            None,
            None,
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_service.db.execute.return_value = mock_result

        result = await mock_service.get_quote(quote_id)

        # Verify all QuoteDetailResponse required fields
        assert "quote_id" in result
        assert "items" in result
        assert "client" in result
        assert "terms_ref" in result
        assert "totals" in result
        assert "status" in result
        assert "approval_required" in result  # NEW: must be present
        assert "evidence_hash" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "approved_at" in result
        assert "approved_by" in result

        # Verify items have line_total
        for item in result["items"]:
            assert "line_total" in item


# ========================================================================
# Test Class 3: Integration Tests (require DB)
# ========================================================================


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteLineTotalIntegration:
    """Integration tests for line_total calculation with real DB"""

    async def test_create_and_get_quote_with_line_totals(self, db_session):
        """Test full flow: create quote → get quote with line_totals"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Create quote with items
        items = [
            {"sku": "BRK-001", "quantity": 10, "unit_price": 5000, "uom": "EA"},
            {
                "sku": "BRK-002",
                "quantity": 20,
                "unit_price": 10000,
                "uom": "EA",
                "discount_tier": "VIP",  # 10% discount
            },
        ]

        create_result = await service.create_quote(
            items=items, client="Integration Test", terms_ref="NET30"
        )

        quote_id = create_result["quote_id"]

        # Get quote and verify line_totals
        get_result = await service.get_quote(quote_id)

        assert len(get_result["items"]) == 2

        # Item 1: no discount
        item1 = next(i for i in get_result["items"] if i["sku"] == "BRK-001")
        assert item1["line_total"] == 50000  # 10 × 5000

        # Item 2: VIP discount (12% per SSOT)
        item2 = next(i for i in get_result["items"] if i["sku"] == "BRK-002")
        assert item2["line_total"] == 176000  # 20 × 10000 × 0.88

    async def test_create_and_get_quote_approval_required(self, db_session):
        """Test full flow: create large quote → get quote with approval_required=true"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Create large quote (> 50M threshold)
        items = [
            {"sku": "LARGE-PROJECT", "quantity": 1, "unit_price": 50000000, "uom": "EA"},
        ]

        create_result = await service.create_quote(
            items=items, client="Large Client", terms_ref="NET30"
        )

        assert create_result["approval_required"] is True

        # Get quote and verify approval_required
        get_result = await service.get_quote(create_result["quote_id"])

        assert get_result["approval_required"] is True
