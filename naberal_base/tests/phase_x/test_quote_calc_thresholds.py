"""
Phase X CI Lift - Approval Threshold Boundary Tests

Data-driven tests for SSOT approval_threshold (from discount_rules.json)

Contract-First / SSOT / Zero-Mock / Evidence-Gated
"""

import pytest
import json
from decimal import Decimal
from pathlib import Path


# Load SSOT approval threshold from discount_rules.json
def load_approval_threshold():
    """Load approval threshold from SSOT discount_rules.json"""
    ssot_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "kis_estimator_core"
        / "core"
        / "ssot"
        / "data"
        / "discount_rules.json"
    )
    with open(ssot_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data["approval_threshold"]["amount"]


APPROVAL_THRESHOLD = load_approval_threshold()

# Test cases: (items, expected_approval_required)
THRESHOLD_CASES = [
    # Case 1: Total < threshold → approval NOT required
    (
        [
            {
                "sku": "ENC-600",
                "quantity": 1,
                "unit_price": 45_000_000,
                "uom": "EA",
            }
        ],
        False,  # 45M < 50M
    ),
    # Case 2: Total == threshold → approval required
    (
        [
            {
                "sku": "ENC-600",
                "quantity": 1,
                "unit_price": 45_454_545,  # After VAT: exactly 50M
                "uom": "EA",
            }
        ],
        True,  # ~50M (with VAT rounding)
    ),
    # Case 3: Total > threshold → approval required
    (
        [
            {
                "sku": "LARGE-PANEL",
                "quantity": 2,
                "unit_price": 30_000_000,
                "uom": "EA",
            }
        ],
        True,  # 60M > 50M
    ),
    # Case 4: Multiple items, total < threshold
    (
        [
            {
                "sku": "BREAKER-1",
                "quantity": 10,
                "unit_price": 1_000_000,
                "uom": "EA",
            },
            {
                "sku": "BREAKER-2",
                "quantity": 20,
                "unit_price": 1_500_000,
                "uom": "EA",
            },
        ],
        False,  # 10M + 30M = 40M < 50M
    ),
    # Case 5: Multiple items, total > threshold
    (
        [
            {
                "sku": "PANEL-A",
                "quantity": 3,
                "unit_price": 20_000_000,
                "uom": "EA",
            },
            {
                "sku": "PANEL-B",
                "quantity": 2,
                "unit_price": 15_000_000,
                "uom": "EA",
            },
        ],
        True,  # 60M + 30M = 90M > 50M
    ),
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteApprovalThresholdBoundary:
    """Test approval_required flag based on SSOT threshold (50M KRW)"""

    @pytest.mark.parametrize("items,expected_approval", THRESHOLD_CASES)
    async def test_approval_threshold_boundary(
        self, items, expected_approval, db_session
    ):
        """
        Test approval_required calculation for various total amounts

        SSOT Rule: total >= 50,000,000 KRW → approval_required = true

        Validates:
        - Threshold enforcement (exactly at, above, below)
        - Multi-item totals
        - VAT and rounding applied correctly
        """
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Create quote
        result = await service.create_quote(
            items=items, client="TestClient", terms_ref="NET30"
        )

        # Verify approval_required matches expected
        assert "approval_required" in result
        assert (
            result["approval_required"] == expected_approval
        ), f"Expected approval={expected_approval}, got {result['approval_required']} for total={result['totals']['total']}"

        # Verify totals structure
        assert "totals" in result
        assert "total" in result["totals"]
        assert result["totals"]["currency"] == "KRW"

    async def test_approval_threshold_exact_boundary(self, db_session):
        """
        Test exact threshold boundary (SSOT approval_threshold)

        This test verifies the >= comparison (not just >)
        VAT rounding: ROUND_HALF_UP (0 precision)
        """
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Calculate item price that results in exactly threshold after VAT
        # Formula: (subtotal - discount) * 1.1 = threshold
        # With no discount: subtotal * 1.1 = threshold
        # subtotal = threshold / 1.1 (Decimal for precision)
        target_subtotal = int(Decimal(APPROVAL_THRESHOLD) / Decimal("1.1"))

        items = [
            {
                "sku": "THRESHOLD-TEST",
                "quantity": 1,
                "unit_price": target_subtotal,
                "uom": "EA",
            }
        ]

        result = await service.create_quote(items=items, client="ThresholdTest")

        # Total should be ~50M (with rounding)
        total = result["totals"]["total"]
        assert (
            abs(total - APPROVAL_THRESHOLD) <= 100
        ), f"Total {total} should be ~{APPROVAL_THRESHOLD}"

        # Approval should be required (>= threshold)
        assert result["approval_required"] is True


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteCalculationEdgeCases:
    """Test edge cases in quote calculation (zero, negative prevention)"""

    async def test_zero_quantity_rejected(self, db_session):
        """Verify quantity=0 is rejected (SSOT validation)"""
        from kis_estimator_core.services.quote_service import QuoteService
        from kis_estimator_core.core.ssot.errors import ErrorCode

        service = QuoteService(db_session)

        items = [
            {
                "sku": "TEST",
                "quantity": 0,  # Invalid
                "unit_price": 1000,
                "uom": "EA",
            }
        ]

        with pytest.raises(Exception) as exc_info:
            await service.create_quote(items=items, client="Test")

        assert ErrorCode.E_VALIDATION in str(exc_info.value)

    async def test_negative_price_rejected(self, db_session):
        """Verify negative unit_price is rejected (SSOT validation)"""
        from kis_estimator_core.services.quote_service import QuoteService
        from kis_estimator_core.core.ssot.errors import ErrorCode

        service = QuoteService(db_session)

        items = [
            {
                "sku": "TEST",
                "quantity": 1,
                "unit_price": -1000,  # Invalid
                "uom": "EA",
            }
        ]

        with pytest.raises(Exception) as exc_info:
            await service.create_quote(items=items, client="Test")

        assert ErrorCode.E_VALIDATION in str(exc_info.value)
