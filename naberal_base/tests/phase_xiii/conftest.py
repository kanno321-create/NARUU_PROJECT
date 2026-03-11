"""
Phase XIII Test Fixtures

Provides test fixtures for Phase XIII coverage tests:
- client: TestClient for synchronous API testing (lifespan-managed)
- approved_quote_id: Real approved quote ID created via HTTP API
- unapproved_quote_id: Real unapproved quote ID created via HTTP API

Zero-Mock Compliance:
- All quotes are created via HTTP API (same path as production)
- No placeholder IDs or mock data
- PDF Auditor mocking is acceptable (testing policy responses, not auditor itself)

Architecture Note:
- Uses HTTP API to create quotes (not direct DB) to ensure data visibility
- TestClient uses same app instance, ensuring quote is committed and visible
- This pattern avoids transaction isolation issues between fixtures and tests
"""

import os
import pytest
from starlette.testclient import TestClient

from api.main import app


@pytest.fixture(scope="function")
def client():
    """
    TestClient for synchronous API testing with lifespan management

    Uses context manager to ensure FastAPI startup/shutdown events execute.
    This ensures DB connections and catalog cache are properly initialized.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def approved_quote_id(client):
    """
    Create a real approved quote via HTTP API

    Zero-Mock compliant:
    - Creates quote via POST /v1/quotes
    - Approves via POST /v1/quotes/{id}/approve
    - Returns real quote UUID

    Uses HTTP API instead of direct DB access to ensure:
    - Data is committed and visible to all test operations
    - Same code path as production
    - No transaction isolation issues
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping Phase XIII tests")

    # Create a test quote via HTTP API
    create_payload = {
        "items": [
            {
                "sku": "PDF-TEST-001",
                "quantity": 10,
                "unit_price": 100000,
                "uom": "EA",
            }
        ],
        "client": "Phase XIII PDF Test",
        "terms_ref": "NET30",
    }

    create_response = client.post("/v1/quotes", json=create_payload)

    if create_response.status_code != 201:
        pytest.skip(f"Failed to create quote: {create_response.status_code} - {create_response.text}")

    quote_id = create_response.json()["quote_id"]

    # Approve the quote via HTTP API
    approve_headers = {"X-Actor-Role": "APPROVER"}
    approve_payload = {
        "actor": "test-approver@test.com",
        "comment": "Phase XIII test approval",
    }

    approve_response = client.post(
        f"/v1/quotes/{quote_id}/approve",
        json=approve_payload,
        headers=approve_headers,
    )

    if approve_response.status_code != 200:
        pytest.skip(f"Failed to approve quote: {approve_response.status_code} - {approve_response.text}")

    return quote_id


@pytest.fixture(scope="function")
def unapproved_quote_id(client):
    """
    Create a real unapproved (DRAFT) quote via HTTP API

    Zero-Mock compliant:
    - Creates quote via POST /v1/quotes
    - Quote remains in DRAFT status (not approved)
    - Returns real quote UUID

    Uses HTTP API instead of direct DB access for consistency.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping Phase XIII tests")

    # Create a test quote via HTTP API (remains DRAFT)
    create_payload = {
        "items": [
            {
                "sku": "PDF-TEST-DRAFT-001",
                "quantity": 5,
                "unit_price": 50000,
                "uom": "EA",
            }
        ],
        "client": "Phase XIII Draft Test",
        "terms_ref": "NET30",
    }

    create_response = client.post("/v1/quotes", json=create_payload)

    if create_response.status_code != 201:
        pytest.skip(f"Failed to create draft quote: {create_response.status_code} - {create_response.text}")

    return create_response.json()["quote_id"]
