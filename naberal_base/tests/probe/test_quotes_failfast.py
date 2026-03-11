"""
Probe Tests - Phase X Quote Endpoints Fail-Fast

Validates 5xx Fail-Fast behavior when DB unavailable

Contract-First / Fail-Fast Guarantee

Note: These tests require actual DB infrastructure to test fail-fast behavior.
      Currently marked as skip until Phase X implementation.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create FastAPI test client for quotes fail-fast tests."""
    from api.main import app
    return TestClient(app)


@pytest.mark.probe
@pytest.mark.skip(reason="Phase X: Requires DB infrastructure for fail-fast testing")
class TestQuotesFailFastProbe:
    """Probe tests for /v1/quotes* endpoints (DB off scenario)"""

    def test_quotes_endpoints_exist(self, client: TestClient):
        """Verify all 4 quote endpoints are registered"""
        # This is a placeholder - actual implementation would test:
        # POST /v1/quotes
        # GET /v1/quotes/{id}
        # POST /v1/quotes/{id}/approve
        # POST /v1/quotes/{id}/pdf
        pass

    def test_create_quote_fails_fast_without_db(self, client: TestClient):
        """POST /v1/quotes returns 500 (not hang) when DB unavailable"""
        # Placeholder - would test with DB connection disabled
        # Expected: 500 Internal Server Error (Fail-Fast)
        # NOT: timeout, hang, or connection error
        pass

    def test_get_quote_fails_fast_without_db(self, client: TestClient):
        """GET /v1/quotes/{id} returns 500 when DB unavailable"""
        pass

    def test_approve_quote_fails_fast_without_db(self, client: TestClient):
        """POST /v1/quotes/{id}/approve returns 500 when DB unavailable"""
        pass
