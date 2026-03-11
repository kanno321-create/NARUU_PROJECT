"""
Integration Tests: /v1/quotes API (Quote Lifecycle)
Phase X: Quote HTTP API 테스트

Category: INTEGRATION TEST
- Requires database connection (kis_beta.quotes table)
- Full Quote lifecycle (Create → Get → Approve → PDF → URL)
- Zero-Mock / Evidence-Gated

API Schema (api/routes/quotes.py):
- POST   /v1/quotes           → create_quote
- GET    /v1/quotes/{id}      → get_quote
- POST   /v1/quotes/{id}/approve → approve_quote
- POST   /v1/quotes/{id}/pdf  → render_pdf
- GET    /v1/quotes/{id}/url  → get_presigned_url
"""

import os
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping quotes API tests in CI - requires real Supabase with quotes table"
    )
]


class TestQuotesAPI:
    """Quote API 통합 테스트 (Phase X)"""

    def test_api_001_create_quote_success(self, client):
        """
        INT-QUOTE-001: 정상 Quote 생성
        - SSOT 기반 UOM/할인/라운딩/VAT 계산
        - Evidence hash 생성
        """
        request_data = {
            "items": [
                {
                    "sku": "SBE-104-75A",
                    "quantity": 10,
                    "unit_price": 12500.0,
                    "uom": "EA",
                    "discount_tier": "A",
                }
            ],
            "client": "테스트건설",
            "terms_ref": "NET30",
        }

        response = client.post("/v1/quotes", json=request_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # 필수 필드 검증
        assert "quote_id" in data
        assert "totals" in data
        assert "approval_required" in data
        assert "evidence_hash" in data
        assert "created_at" in data

        # totals 검증
        totals = data["totals"]
        assert "subtotal" in totals
        assert "discount" in totals
        assert "vat" in totals
        assert "total" in totals
        assert totals["currency"] == "KRW"

        # Evidence hash 형식 검증 (SHA256)
        assert len(data["evidence_hash"]) == 64

        print(f"[OK] Quote created: {data['quote_id']}")
        print(f"   - Total: {totals['total']} KRW")
        print(f"   - Approval required: {data['approval_required']}")

    def test_api_002_create_quote_invalid_uom(self, client):
        """
        INT-QUOTE-002: 잘못된 UOM 시 400 에러
        """
        request_data = {
            "items": [
                {
                    "sku": "SBE-104-75A",
                    "quantity": 1,
                    "unit_price": 10000.0,
                    "uom": "INVALID_UOM",  # 잘못된 UOM
                }
            ],
            "client": "테스트건설",
        }

        response = client.post("/v1/quotes", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "code" in data
        assert "E_VALIDATION" in data["code"]

    def test_api_003_create_quote_missing_fields(self, client):
        """
        INT-QUOTE-003: 필수 필드 누락 시 422 에러
        """
        request_data = {
            "items": [],  # 빈 아이템 리스트
            "client": "테스트건설",
        }

        response = client.post("/v1/quotes", json=request_data)

        # 422 (Pydantic validation) 또는 400 (AppError)
        assert response.status_code in [400, 422]

    def test_api_004_get_quote_success(self, client):
        """
        INT-QUOTE-004: Quote 조회
        - 먼저 생성 후 조회
        """
        # 1. 먼저 Quote 생성
        create_data = {
            "items": [
                {
                    "sku": "TEST-ITEM",
                    "quantity": 5,
                    "unit_price": 5000.0,
                    "uom": "EA",
                }
            ],
            "client": "조회테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        assert create_response.status_code == 201
        quote_id = create_response.json()["quote_id"]

        # 2. 생성한 Quote 조회
        get_response = client.get(f"/v1/quotes/{quote_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["quote_id"] == quote_id
        assert data["client"] == "조회테스트"
        assert data["status"] == "DRAFT"
        assert "items" in data
        assert len(data["items"]) == 1

    def test_api_005_get_quote_not_found(self, client):
        """
        INT-QUOTE-005: 존재하지 않는 Quote 조회 시 404
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/v1/quotes/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "E_NOT_FOUND" in data["code"]

    def test_api_006_approve_quote_success(self, client):
        """
        INT-QUOTE-006: Quote 승인 (DRAFT → APPROVED)
        """
        # 1. Quote 생성
        create_data = {
            "items": [
                {
                    "sku": "APPROVE-TEST",
                    "quantity": 2,
                    "unit_price": 10000.0,
                    "uom": "EA",
                }
            ],
            "client": "승인테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        assert create_response.status_code == 201
        quote_id = create_response.json()["quote_id"]

        # 2. Quote 승인
        approve_data = {
            "actor": "admin@test.com",
            "comment": "테스트 승인",
        }

        approve_response = client.post(f"/v1/quotes/{quote_id}/approve", json=approve_data)

        assert approve_response.status_code == 200
        data = approve_response.json()

        assert data["quote_id"] == quote_id
        assert data["status"] == "APPROVED"
        assert data["approved_by"] == "admin@test.com"
        assert "approved_at" in data
        assert "evidence_entry" in data

    def test_api_007_approve_quote_already_approved(self, client):
        """
        INT-QUOTE-007: 이미 승인된 Quote 재승인 시 409 Conflict
        """
        # 1. Quote 생성 및 승인
        create_data = {
            "items": [{"sku": "CONFLICT-TEST", "quantity": 1, "unit_price": 1000.0, "uom": "EA"}],
            "client": "중복승인테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        quote_id = create_response.json()["quote_id"]

        approve_data = {"actor": "admin@test.com"}
        client.post(f"/v1/quotes/{quote_id}/approve", json=approve_data)

        # 2. 재승인 시도
        second_approve = client.post(f"/v1/quotes/{quote_id}/approve", json=approve_data)

        assert second_approve.status_code == 409
        data = second_approve.json()
        assert "E_CONFLICT" in data["code"]


class TestQuotesAPIPDF:
    """Quote PDF API 테스트"""

    def test_pdf_001_render_success(self, client):
        """
        INT-PDF-001: PDF 생성 성공
        """
        # 1. Quote 생성
        create_data = {
            "items": [{"sku": "PDF-TEST", "quantity": 3, "unit_price": 15000.0, "uom": "EA"}],
            "client": "PDF테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        quote_id = create_response.json()["quote_id"]

        # 2. PDF 생성
        pdf_response = client.post(f"/v1/quotes/{quote_id}/pdf")

        assert pdf_response.status_code == 200
        data = pdf_response.json()

        assert "pdf_path" in data
        assert "evidence_hash" in data
        assert "audit_passed" in data
        assert data["audit_passed"] is True

    def test_pdf_002_url_requires_approval(self, client):
        """
        INT-PDF-002: Pre-signed URL은 승인된 Quote만 가능
        """
        # 1. Quote 생성 (승인하지 않음)
        create_data = {
            "items": [{"sku": "URL-TEST", "quantity": 1, "unit_price": 5000.0, "uom": "EA"}],
            "client": "URL테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        quote_id = create_response.json()["quote_id"]

        # 2. URL 요청 (승인 전)
        url_response = client.get(f"/v1/quotes/{quote_id}/url")

        # 승인 안된 Quote는 400 E_VALIDATION
        assert url_response.status_code == 400
        data = url_response.json()
        assert "E_VALIDATION" in data["code"]

    def test_pdf_003_url_success_after_approval(self, client):
        """
        INT-PDF-003: 승인 후 Pre-signed URL 조회 성공
        """
        # 1. Quote 생성 및 승인
        create_data = {
            "items": [{"sku": "URL-APPROVED-TEST", "quantity": 2, "unit_price": 10000.0, "uom": "EA"}],
            "client": "URL승인테스트",
        }

        create_response = client.post("/v1/quotes", json=create_data)
        quote_id = create_response.json()["quote_id"]

        # 승인
        client.post(f"/v1/quotes/{quote_id}/approve", json={"actor": "admin@test.com"})

        # PDF 먼저 생성 (S3에 업로드되어야 URL 조회 가능)
        client.post(f"/v1/quotes/{quote_id}/pdf")

        # 2. URL 조회
        url_response = client.get(f"/v1/quotes/{quote_id}/url")

        assert url_response.status_code == 200
        data = url_response.json()

        assert "url" in data
        assert "expires_at" in data
        assert "storage_mode" in data
        assert data["approved"] is True


class TestQuotesAPIApprovalThreshold:
    """승인 임계값 테스트 (SSOT: ≥50M KRW)"""

    def test_threshold_001_below_threshold(self, client):
        """
        INT-THRESHOLD-001: 임계값 미만 (approval_required=False)
        """
        request_data = {
            "items": [
                {"sku": "SMALL-ITEM", "quantity": 10, "unit_price": 10000.0, "uom": "EA"}
            ],
            "client": "소규모테스트",
        }

        response = client.post("/v1/quotes", json=request_data)
        data = response.json()

        # 100,000 + VAT = 110,000 KRW < 50M
        assert data["approval_required"] is False

    def test_threshold_002_above_threshold(self, client):
        """
        INT-THRESHOLD-002: 임계값 이상 (approval_required=True)
        """
        request_data = {
            "items": [
                {
                    "sku": "LARGE-ITEM",
                    "quantity": 1000,
                    "unit_price": 55000.0,  # 55M KRW
                    "uom": "EA",
                }
            ],
            "client": "대규모테스트",
        }

        response = client.post("/v1/quotes", json=request_data)
        data = response.json()

        # 55,000,000 + VAT > 50M
        assert data["approval_required"] is True


class TestQuotesAPIPerformance:
    """성능 테스트"""

    def test_perf_001_create_quote_response_time(self, client):
        """
        INT-PERF-001: Quote 생성 응답 시간 < 500ms
        """
        import time

        request_data = {
            "items": [
                {"sku": f"PERF-{i}", "quantity": 1, "unit_price": 1000.0, "uom": "EA"}
                for i in range(10)
            ],
            "client": "성능테스트",
        }

        start = time.time()
        response = client.post("/v1/quotes", json=request_data)
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 201
        assert elapsed_ms < 500, f"성능 목표 초과: {elapsed_ms:.0f}ms > 500ms"

        print(f"[PERF] Quote created in {elapsed_ms:.0f}ms")
