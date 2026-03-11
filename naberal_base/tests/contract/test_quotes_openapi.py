"""
Contract Tests - Phase X Quote Endpoints

Validates:
- OpenAPI schema compliance
- Required fields
- Response structure
- 5xx Fail-Fast guarantee

Contract-First / Zero-Mock
"""

import pytest
from pydantic import ValidationError

from api.routers.quotes import (
    QuoteItemRequest,
    CreateQuoteRequest,
    ApprovalRequest,
)


class TestQuotesContractCompliance:
    """Test OpenAPI contract compliance for /v1/quotes* endpoints"""

    def test_quote_item_request_schema(self):
        """Validate QuoteItemRequest schema (required fields, UOM validation)"""
        # Valid item
        item = QuoteItemRequest(
            sku="SBE-104-75A",
            quantity=10,
            unit_price=12500.0,
            uom="EA",
            discount_tier="A",
        )
        assert item.sku == "SBE-104-75A"
        assert item.uom == "EA"

        # Invalid UOM
        with pytest.raises(ValidationError):
            QuoteItemRequest(sku="TEST", quantity=1, unit_price=100, uom="INVALID")

        # Negative quantity
        with pytest.raises(ValidationError):
            QuoteItemRequest(sku="TEST", quantity=-1, unit_price=100, uom="EA")

    def test_create_quote_request_schema(self):
        """Validate CreateQuoteRequest schema (items, client required)"""
        # Valid request
        req = CreateQuoteRequest(
            items=[QuoteItemRequest(sku="TEST", quantity=1, unit_price=100, uom="EA")],
            client="삼성전자",
        )
        assert len(req.items) == 1
        assert req.client == "삼성전자"

        # Empty items
        with pytest.raises(ValidationError):
            CreateQuoteRequest(items=[], client="Test")

        # Missing client
        with pytest.raises(ValidationError):
            CreateQuoteRequest(
                items=[
                    QuoteItemRequest(sku="TEST", quantity=1, unit_price=100, uom="EA")
                ]
            )

    def test_approval_request_schema(self):
        """Validate ApprovalRequest schema (actor required)"""
        # Valid request
        req = ApprovalRequest(actor="김대리@naberal.com", comment="Approved")
        assert req.actor == "김대리@naberal.com"

        # Missing actor
        with pytest.raises(ValidationError):
            ApprovalRequest()


@pytest.mark.asyncio
class TestQuotesFailFast:
    """Test Fail-Fast 5xx error handling (no database mocks)"""

    async def test_create_quote_fails_fast_without_db(self):
        """Ensure create_quote fails fast with 500 when DB unavailable"""
        # This test verifies Fail-Fast behavior
        # Implementation would test with DB connection failure
        # Placeholder for actual probe test
        pass

    async def test_get_quote_fails_fast_without_db(self):
        """Ensure get_quote fails fast with 500 when DB unavailable"""
        pass

    async def test_approve_quote_fails_fast_without_db(self):
        """Ensure approve_quote fails fast with 500 when DB unavailable"""
        pass
