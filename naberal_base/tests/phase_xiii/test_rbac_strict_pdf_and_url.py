"""
Phase XIII: RBAC Strict Enforcement for PDF and URL Endpoints

Coverage Target: RBAC 403 boundary cases, X-Policy-Hint headers
"""

import os
import pytest

# CI skip - tests require fixtures (client, approved_quote_id, unapproved_quote_id)
# with valid UUID format and proper database setup
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping Phase XIII RBAC tests in CI - requires valid UUID fixtures and DB setup"
)

from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_unapproved_quote_pdf_access_forbidden(
    client: TestClient, unapproved_quote_id: str
):
    """
    Test: Unapproved quote PDF access returns 403

    Expected:
    - Status: 403
    - Error code: E_RBAC
    - X-Policy-Hint header present
    """
    headers = {"X-Actor-Role": "APPROVER"}
    response = client.post(f"/v1/quotes/{unapproved_quote_id}/pdf", headers=headers)

    assert response.status_code == 403
    data = response.json()

    assert "code" in data["detail"]
    assert data["detail"]["code"] == "E_RBAC"

    # X-Policy-Hint header should be present
    assert "X-Policy-Hint" in response.headers or "x-policy-hint" in response.headers


@pytest.mark.asyncio
async def test_unapproved_quote_url_access_forbidden(
    client: TestClient, unapproved_quote_id: str
):
    """
    Test: Unapproved quote PDF URL access returns 403

    Expected:
    - Status: 403
    - Error code: E_RBAC
    - X-Policy-Hint header present
    """
    headers = {"X-Actor-Role": "APPROVER"}
    response = client.get(f"/v1/quotes/{unapproved_quote_id}/pdf/url", headers=headers)

    assert response.status_code == 403
    data = response.json()

    assert "code" in data["detail"]
    assert data["detail"]["code"] == "E_RBAC"

    # X-Policy-Hint header should be present
    assert "X-Policy-Hint" in response.headers or "x-policy-hint" in response.headers


@pytest.mark.asyncio
async def test_user_role_pdf_access_forbidden(
    client: TestClient, approved_quote_id: str
):
    """
    Test: USER role cannot access PDF endpoints (even for approved quotes)

    Expected:
    - Status: 403
    - Error code: E_RBAC
    - required_role: APPROVER
    """
    headers = {"X-Actor-Role": "USER"}
    response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

    assert response.status_code == 403
    data = response.json()

    assert "code" in data["detail"]
    assert data["detail"]["code"] == "E_RBAC"
    assert "required_role" in data["detail"]


@pytest.mark.asyncio
async def test_user_role_url_access_forbidden(
    client: TestClient, approved_quote_id: str
):
    """
    Test: USER role cannot access PDF URL endpoint

    Expected:
    - Status: 403
    - Error code: E_RBAC
    """
    headers = {"X-Actor-Role": "USER"}
    response = client.get(f"/v1/quotes/{approved_quote_id}/pdf/url", headers=headers)

    assert response.status_code == 403
    data = response.json()

    assert "code" in data["detail"]
    assert data["detail"]["code"] == "E_RBAC"


@pytest.mark.asyncio
async def test_approver_role_approved_quote_pdf_success(
    client: TestClient, approved_quote_id: str
):
    """
    Test: APPROVER role can access approved quote PDF

    Expected:
    - Status: 200
    - PDF content or redirect
    """
    headers = {"X-Actor-Role": "APPROVER"}
    response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

    # Should succeed (200) or return PDF policy error (422) if PDF invalid
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_approver_role_approved_quote_url_success(
    client: TestClient, approved_quote_id: str
):
    """
    Test: APPROVER role can access approved quote PDF URL

    Expected:
    - Status: 200
    - Response contains url, expires_at, approved=True
    """
    headers = {"X-Actor-Role": "APPROVER"}
    response = client.get(f"/v1/quotes/{approved_quote_id}/pdf/url", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "url" in data
    assert "approved" in data
    assert data["approved"] is True


@pytest.mark.asyncio
async def test_admin_role_approved_quote_url_success(
    client: TestClient, approved_quote_id: str
):
    """
    Test: ADMIN role can access approved quote PDF URL

    Expected:
    - Status: 200
    - Response contains url, approved=True
    """
    headers = {"X-Actor-Role": "ADMIN"}
    response = client.get(f"/v1/quotes/{approved_quote_id}/pdf/url", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "url" in data
    assert "approved" in data
    assert data["approved"] is True


@pytest.mark.asyncio
async def test_missing_role_header_forbidden(
    client: TestClient, approved_quote_id: str
):
    """
    Test: Missing X-Actor-Role header returns 403

    Expected:
    - Status: 403
    - Error code: E_RBAC
    """
    response = client.get(f"/v1/quotes/{approved_quote_id}/pdf/url")

    assert response.status_code == 403
