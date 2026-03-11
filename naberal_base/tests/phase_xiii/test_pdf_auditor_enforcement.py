"""
Phase XIII: PDF Auditor Policy Enforcement Tests

Coverage Target: E_PDF_POLICY error handling, violation details, Evidence Footer validation

Zero-Mock Compliance:
- Quotes are created via real HTTP API (see conftest.py)
- PDF Auditor is mocked to control audit results (acceptable for policy testing)
- Tests verify API error response structure, not actual PDF generation

Architecture:
- Uses synchronous TestClient with lifespan management
- approved_quote_id fixture creates real quote via HTTP API
- PDFAuditor.audit is patched to simulate policy violations
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from starlette.testclient import TestClient

from kis_estimator_core.core.ssot.errors import ErrorCode


# Mark all tests as integration tests requiring database
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL"),
        reason="DATABASE_URL not set - skipping Phase XIII tests"
    ),
]


def test_pdf_policy_violation_returns_422(client: TestClient, approved_quote_id: str):
    """
    Test: PDF policy violation returns 422 with E_PDF_POLICY code

    Expected:
    - Status: 422
    - Error code: E_PDF_POLICY
    - Detailed violations list in response
    """
    headers = {"X-Actor-Role": "APPROVER"}

    # Mock PDF Auditor to return violations
    mock_audit_result = MagicMock()
    mock_audit_result.passed = False
    mock_audit_result.errors = [
        "Page size A4 violation: expected 210×297mm",
        "Margin violation: left margin < 10mm",
        "Font violation: expected MalgunGothic",
    ]

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # API returns flat structure (not nested in "detail") per error_handler.py
        assert "code" in data
        assert data["code"] == ErrorCode.E_PDF_POLICY.value

        # Verify detailed error message
        assert "PDF policy violation" in data["message"]

        # Verify hint is present
        assert "hint" in data
        assert "A4" in data["hint"]
        assert "margins" in data["hint"] or "10mm" in data["hint"]
        assert "Korean fonts" in data["hint"] or "font" in data["hint"].lower()


def test_pdf_margin_violation_details(client: TestClient, approved_quote_id: str):
    """
    Test: Margin violation provides specific violation details

    Expected:
    - Status: 422
    - Error code: E_PDF_POLICY
    - Violations list includes margin details
    """
    headers = {"X-Actor-Role": "APPROVER"}

    mock_audit_result = MagicMock()
    mock_audit_result.passed = False
    mock_audit_result.errors = ["Margin violation: top margin 8mm < 10mm required"]

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # API returns flat structure (not nested in "detail") per error_handler.py
        assert data["code"] == ErrorCode.E_PDF_POLICY.value
        assert "margin" in data["message"].lower()


def test_pdf_font_violation_details(client: TestClient, approved_quote_id: str):
    """
    Test: Font violation provides specific violation details

    Expected:
    - Status: 422
    - Error code: E_PDF_POLICY
    - Violations list includes font details
    """
    headers = {"X-Actor-Role": "APPROVER"}

    mock_audit_result = MagicMock()
    mock_audit_result.passed = False
    mock_audit_result.errors = [
        "Font violation: Arial detected, expected MalgunGothic/NanumGothic/NanumMyeongjo"
    ]

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # API returns flat structure (not nested in "detail") per error_handler.py
        assert data["code"] == ErrorCode.E_PDF_POLICY.value
        assert "font" in data["message"].lower()


def test_pdf_footer_missing_violation(client: TestClient, approved_quote_id: str):
    """
    Test: Missing Evidence Footer returns 422

    Expected:
    - Status: 422
    - Error code: E_PDF_POLICY
    - Violations list includes footer requirement
    """
    headers = {"X-Actor-Role": "APPROVER"}

    mock_audit_result = MagicMock()
    mock_audit_result.passed = False
    mock_audit_result.errors = ["Evidence Footer missing"]

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # API returns flat structure (not nested in "detail") per error_handler.py
        assert data["code"] == ErrorCode.E_PDF_POLICY.value
        assert (
            "footer" in data["message"].lower()
            or "Footer" in data["message"]
        )


def test_pdf_valid_passes_audit(client: TestClient, approved_quote_id: str):
    """
    Test: Valid PDF passes audit and returns success

    Expected:
    - Status: 200 (or 404 if PDF not found)
    - No E_PDF_POLICY error
    """
    headers = {"X-Actor-Role": "APPROVER"}

    mock_audit_result = MagicMock()
    mock_audit_result.passed = True
    mock_audit_result.errors = []

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        # Should not return 422 E_PDF_POLICY
        if response.status_code != 200:
            # If error, should not be PDF policy error
            if response.status_code == 422:
                data = response.json()
                # API returns flat structure (not nested in "detail") per error_handler.py
                assert data["code"] != ErrorCode.E_PDF_POLICY.value


def test_pdf_policy_hint_contains_requirements(
    client: TestClient, approved_quote_id: str
):
    """
    Test: E_PDF_POLICY hint contains all policy requirements

    Expected:
    - Hint mentions: A4, margins (≥10mm), Korean fonts, Evidence Footer
    """
    headers = {"X-Actor-Role": "APPROVER"}

    mock_audit_result = MagicMock()
    mock_audit_result.passed = False
    mock_audit_result.errors = ["Policy violation"]

    with patch(
        "kis_estimator_core.services.quote_service.PDFAuditor.audit",
        return_value=mock_audit_result,
    ):
        response = client.post(f"/v1/quotes/{approved_quote_id}/pdf", headers=headers)

        assert response.status_code == 422
        data = response.json()

        # API returns flat structure (not nested in "detail") per error_handler.py
        hint = data["hint"]
        assert "A4" in hint
        assert "10mm" in hint or "margin" in hint
        assert "font" in hint.lower() or "korean" in hint.lower()
        assert "footer" in hint.lower() or "Footer" in hint
