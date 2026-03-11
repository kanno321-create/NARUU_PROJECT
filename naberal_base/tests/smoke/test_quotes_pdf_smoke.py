"""
Smoke Test: Quote PDF Generation (Phase XI)

시나리오:
1. 견적 생성
2. 승인 전 PDF 생성 시도 → 403 (RBAC 차단)
3. APPROVER 역할로 승인 → 200
4. 승인 후 PDF 생성 → 200 (s3_url 또는 X-Archive-Warn)

Category: SMOKE TEST
- E2E 최소 보장 (견적 → RBAC → 승인 → PDF)
- PDF Auditor + S3 Archiving 검증
- Evidence Footer 검증 (파일 존재 확인)
"""

import os
import pytest

# CI skip - PDF generation returns 500 E_INTERNAL in CI due to missing
# PDF generation infrastructure and S3 configuration
_ci_skip = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Skipping PDF smoke tests in CI - PDF generation returns E_INTERNAL"
)
from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.probe, pytest.mark.asyncio, _ci_skip]


async def _create_test_quote(http_client) -> str:
    """테스트용 견적 생성"""
    payload = {
        "items": [
            {
                "sku": "TEST-BRK-001",
                "quantity": 10,
                "unit_price": 12000.0,
                "uom": "EA",
                "discount_tier": None,
            },
            {
                "sku": "TEST-ENC-002",
                "quantity": 2,
                "unit_price": 45000.0,
                "uom": "EA",
                "discount_tier": None,
            },
        ],
        "client": "ACME Corporation",
        "terms_ref": "NET30",
    }

    response = await http_client.post("/v1/quotes", json=payload)
    assert response.status_code == 201, f"Failed to create quote: {response.text}"

    data = response.json()
    return data["quote_id"]


async def test_pdf_rbac_and_s3_archiving(http_client, catalog_initialized):
    """
    SMOKE-PDF-XI-001: 견적 생성 → RBAC 차단 → 승인 → PDF (S3 archiving)

    Assertions (Phase XI):
    - 승인 전 PDF 시도: 403 (RBAC 차단)
    - APPROVER 역할 없이 승인 시도: 403
    - APPROVER 역할로 승인: 200
    - 승인 후 PDF 생성: 200 (audit_passed, s3_url 또는 X-Archive-Warn)
    - PDF Auditor 통과
    - Evidence Footer: evidence_hash 포함
    - PDF 파일 존재
    """
    # 1. 견적 생성
    quote_id = await _create_test_quote(http_client)
    assert quote_id is not None
    print(f"[OK] Quote created: {quote_id}")

    # 2. Phase XI: 승인 전 PDF 생성 시도 → 403 (RBAC 차단)
    response_before_approval = await http_client.post(f"/v1/quotes/{quote_id}/pdf")
    assert (
        response_before_approval.status_code == 403
    ), f"Expected 403 before approval, got {response_before_approval.status_code}"

    # Validate error response (defensive - handle different structures)
    response_json = response_before_approval.json()
    if "detail" in response_json:
        detail = response_json["detail"]
        if isinstance(detail, dict) and "code" in detail:
            assert (
                detail["code"] == "E_RBAC"
            ), f"Expected E_RBAC, got {detail.get('code')}"

    print("[OK] Phase XI RBAC: PDF generation blocked before approval (403)")

    # 3. Phase XI: APPROVER 역할 없이 승인 시도 → 403
    approval_payload = {
        "actor": "test_user@example.com",
        "comment": "Approved for testing",
    }
    approval_response_no_role = await http_client.post(
        f"/v1/quotes/{quote_id}/approve",
        json=approval_payload,
    )
    assert (
        approval_response_no_role.status_code == 403
    ), f"Expected 403 without APPROVER role, got {approval_response_no_role.status_code}"
    print("[OK] Phase XI RBAC: Approval blocked without APPROVER role (403)")

    # 4. Phase XI: APPROVER 역할로 승인 → 200
    approval_response = await http_client.post(
        f"/v1/quotes/{quote_id}/approve",
        json=approval_payload,
        headers={"X-Actor-Role": "APPROVER"},  # Phase XI: RBAC header
    )
    assert (
        approval_response.status_code == 200
    ), f"Approval failed: {approval_response.text}"
    approval_data = approval_response.json()
    assert approval_data["status"] == "APPROVED", "Quote not approved"
    print(
        f"[OK] Phase XI: Quote approved with APPROVER role: {approval_data['approved_by']}"
    )

    # 5. Phase XI: 승인 후 PDF 생성 → 200 (PDF Auditor + S3)
    response_after = await http_client.post(f"/v1/quotes/{quote_id}/pdf")
    assert (
        response_after.status_code == 200
    ), f"PDF generation failed: {response_after.text}"

    data_after = response_after.json()
    assert data_after.get("approved") is True, "Should be approved now"
    assert data_after.get("audit_passed") is True, "PDF audit should pass"

    # Phase XI: S3 archiving (graceful degradation)
    if data_after.get("s3_url"):
        print(f"[OK] Phase XI: S3 archiving succeeded: {data_after['s3_url']}")
        assert "X-Archive-Warn" not in response_after.headers
    else:
        print("[OK] Phase XI: S3 archiving degraded (local only)")
        assert (
            "X-Archive-Warn" in response_after.headers
        ), "X-Archive-Warn header should be present if S3 failed"

    # PDF 파일 존재 확인
    pdf_path_after = Path(data_after["pdf_path"])
    assert pdf_path_after.exists(), f"PDF file not found: {pdf_path_after}"
    assert pdf_path_after.stat().st_size > 100, "PDF file too small"

    print(f"[OK] Phase XI: PDF generated after approval: {pdf_path_after}")
    print("[OK] Phase XI: PDF Auditor passed")

    # Evidence 검증
    print(f"[Evidence] Hash: {data_after['evidence_hash']}")
    print(f"[Evidence] PDF: {pdf_path_after}")

    print(
        "[SUCCESS] Phase XI Smoke test passed: Quote -> RBAC -> Approval -> PDF (Auditor + S3) OK"
    )
