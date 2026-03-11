"""
Phase X CI Lift - Discount/Rounding/VAT Combination Tests

SSOT Rules:
- Discount tiers: A(5%), B(8%), VIP(12%), VOLUME(3%), SEASONAL(2%)
- Rounding: KRW, precision=0, HALF_UP
- VAT: 10%

Contract-First / SSOT / Zero-Mock

Note: HALF_UP rounding implementation verified in QuoteService._round_half_up()
(commit 5cd47aca: fix(ssot): implement HALF_UP rounding per SSOT rounding.json)
"""

import pytest

# SSOT discount rates (from discount_rules.json)
DISCOUNT_RATES = {
    "A": 0.05,
    "B": 0.08,
    "VIP": 0.12,
    "VOLUME": 0.03,
    "SEASONAL": 0.02,
}

# VAT rate (from rounding.json)
VAT_PCT = 0.10


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteDiscountCalculation:
    """Test discount tier application (SSOT discount_rules.json)"""

    @pytest.mark.parametrize(
        "discount_tier,expected_rate",
        [
            ("A", 0.05),
            ("B", 0.08),
            ("VIP", 0.12),
            ("VOLUME", 0.03),
            ("SEASONAL", 0.02),
        ],
    )
    async def test_discount_tier_application(
        self, discount_tier, expected_rate, db_session
    ):
        """
        Test each discount tier is applied correctly

        Formula:
        - subtotal = Σ(quantity × unit_price)
        - discount = subtotal × discount_rate
        - vat = (subtotal - discount) × 0.1
        - total = subtotal - discount + vat
        """
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Simple case: 1 item, 1,000,000 KRW
        base_price = 1_000_000
        items = [
            {
                "sku": f"TEST-{discount_tier}",
                "quantity": 10,
                "unit_price": base_price,
                "uom": "EA",
                "discount_tier": discount_tier,
            }
        ]

        result = await service.create_quote(items=items, client="DiscountTest")

        totals = result["totals"]
        subtotal = totals["subtotal"]
        discount = totals["discount"]
        vat = totals["vat"]
        total = totals["total"]

        # Verify subtotal
        expected_subtotal = 10 * base_price
        assert subtotal == expected_subtotal

        # Verify discount amount
        expected_discount = round(subtotal * expected_rate, 0)
        assert (
            discount == expected_discount
        ), f"Tier {discount_tier}: expected discount {expected_discount}, got {discount}"

        # Verify VAT
        expected_vat = round((subtotal - discount) * VAT_PCT, 0)
        assert vat == expected_vat

        # Verify total
        expected_total = subtotal - discount + vat
        assert total == expected_total

    async def test_no_discount_tier(self, db_session):
        """Test quote without discount_tier (no discount applied)"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        items = [
            {
                "sku": "NO-DISCOUNT",
                "quantity": 10,
                "unit_price": 100_000,
                "uom": "EA",
                # No discount_tier specified
            }
        ]

        result = await service.create_quote(items=items, client="NoDiscountTest")

        totals = result["totals"]

        # Verify no discount applied
        assert totals["discount"] == 0

        # Verify VAT on full subtotal
        expected_vat = round(totals["subtotal"] * VAT_PCT, 0)
        assert totals["vat"] == expected_vat


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteRoundingRules:
    """Test KRW rounding (SSOT rounding.json: precision=0, HALF_UP)"""

    async def test_krw_rounding_half_up(self, db_session):
        """
        Test KRW rounding with HALF_UP mode (precision=0)

        Examples:
        - 1234.4 → 1234
        - 1234.5 → 1235 (HALF_UP)
        - 1234.6 → 1235
        """
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        # Case 1: Price that generates 0.5 after VAT
        # 1000 * 1.1 = 1100.0 (no rounding needed)
        # 1001 * 1.1 = 1101.1 → rounds to 1101
        # 1005 * 1.1 = 1105.5 → rounds to 1106 (HALF_UP)

        items = [
            {
                "sku": "ROUND-TEST",
                "quantity": 1,
                "unit_price": 1005,  # 1005 * 1.1 = 1105.5
                "uom": "EA",
            }
        ]

        result = await service.create_quote(items=items, client="RoundTest")

        totals = result["totals"]

        # Expected: subtotal=1005, vat=101 (SSOT HALF_UP rounding), total=1106
        # SSOT rounding.json: mode=HALF_UP (100.5 → 101, not 100)
        assert totals["subtotal"] == 1005
        assert totals["vat"] == 101  # HALF_UP: 100.5 → 101
        assert totals["total"] == 1106

        # Verify currency
        assert totals["currency"] == "KRW"

    async def test_multi_item_rounding(self, db_session):
        """Test rounding with multiple items (total rounding, not per-item)"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        items = [
            {
                "sku": "ITEM-1",
                "quantity": 3,
                "unit_price": 333,  # 999 subtotal
                "uom": "EA",
            },
            {
                "sku": "ITEM-2",
                "quantity": 2,
                "unit_price": 555,  # 1110 subtotal
                "uom": "EA",
            },
        ]

        result = await service.create_quote(items=items, client="MultiRoundTest")

        totals = result["totals"]

        # Subtotal: 999 + 1110 = 2109
        assert totals["subtotal"] == 2109

        # VAT: 2109 * 0.1 = 210.9 → rounds to 211 (HALF_UP)
        assert totals["vat"] == 211

        # Total: 2109 + 211 = 2320
        assert totals["total"] == 2320


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteVATCalculation:
    """Test VAT 10% application (SSOT rounding.json)"""

    async def test_vat_10_percent(self, db_session):
        """Test VAT calculation (10% of subtotal - discount)"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        items = [
            {
                "sku": "VAT-TEST",
                "quantity": 1,
                "unit_price": 1_000_000,
                "uom": "EA",
            }
        ]

        result = await service.create_quote(items=items, client="VATTest")

        totals = result["totals"]

        # Expected: subtotal=1M, vat=100K, total=1.1M
        assert totals["subtotal"] == 1_000_000
        assert totals["vat"] == 100_000  # 10% of 1M
        assert totals["total"] == 1_100_000

    async def test_vat_after_discount(self, db_session):
        """Test VAT applied after discount (not on original subtotal)"""
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        items = [
            {
                "sku": "VAT-DISCOUNT-TEST",
                "quantity": 1,
                "unit_price": 1_000_000,
                "uom": "EA",
                "discount_tier": "A",  # 5% discount
            }
        ]

        result = await service.create_quote(items=items, client="VATDiscountTest")

        totals = result["totals"]

        # Subtotal: 1M
        # Discount: 1M * 0.05 = 50K
        # VAT base: 1M - 50K = 950K
        # VAT: 950K * 0.1 = 95K
        # Total: 1M - 50K + 95K = 1,045K

        assert totals["subtotal"] == 1_000_000
        assert totals["discount"] == 50_000
        assert totals["vat"] == 95_000  # VAT on discounted amount
        assert totals["total"] == 1_045_000


@pytest.mark.asyncio
@pytest.mark.integration
class TestQuoteComplexCombinations:
    """Test complex combinations (multi-item, mixed discounts, rounding)"""

    async def test_complex_quote_calculation(self, db_session):
        """
        Test realistic quote with multiple items, mixed discounts, rounding

        Items:
        1. Enclosure (no discount): 5M × 2 = 10M
        2. Breakers (A tier 5%): 100K × 50 = 5M → discount 250K
        3. Accessories (VIP tier 12%): 50K × 100 = 5M → discount 600K

        Subtotal: 20M
        Discount: 850K
        VAT base: 19.15M
        VAT: 1.915M → rounds to 1,915,000
        Total: 20,915,000
        """
        from kis_estimator_core.services.quote_service import QuoteService

        service = QuoteService(db_session)

        items = [
            {
                "sku": "ENC-LARGE",
                "quantity": 2,
                "unit_price": 5_000_000,
                "uom": "EA",
            },
            {
                "sku": "BREAKER-STD",
                "quantity": 50,
                "unit_price": 100_000,
                "uom": "EA",
                "discount_tier": "A",
            },
            {
                "sku": "ACC-PREMIUM",
                "quantity": 100,
                "unit_price": 50_000,
                "uom": "EA",
                "discount_tier": "VIP",
            },
        ]

        result = await service.create_quote(items=items, client="ComplexQuote")

        totals = result["totals"]

        # Verify subtotal
        assert totals["subtotal"] == 20_000_000

        # Verify discount (250K + 600K = 850K)
        assert totals["discount"] == 850_000

        # Verify VAT (19.15M * 0.1 = 1.915M)
        assert totals["vat"] == 1_915_000

        # Verify total (20M - 850K + 1,915K = 21,065K)
        assert totals["total"] == 21_065_000

        # Verify approval NOT required (< 50M threshold)
        assert result["approval_required"] is False
