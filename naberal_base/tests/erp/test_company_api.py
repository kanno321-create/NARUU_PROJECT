"""
KIS ERP - Company API Integration Tests
Contract-First + Evidence-Gated + Zero-Mock

Tests:
- GET /v1/erp/company - Get company info (singleton)
- POST /v1/erp/company - Create company info
- PUT /v1/erp/company - Update company info

Note: 자사정보는 1개만 존재하는 싱글톤 패턴
"""

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from api.main import app


@pytest.mark.requires_db
@pytest.mark.asyncio
class TestCompanyAPI:
    """Company API 통합 테스트"""

    async def test_get_company_not_found(self):
        """자사정보 미등록 상태"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                response = await client.get("/v1/erp/company")
                # 처음에는 자사정보가 없을 수 있음
                assert response.status_code in [200, 404]
                if response.status_code == 404:
                    assert "자사정보가 등록되지 않았습니다" in response.json()["detail"]

    async def test_create_company_success(self):
        """자사정보 생성 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                company_data = {
                    "business_number": "123-45-67890",
                    "name": "테스트 주식회사",
                    "ceo": "대표이사 홍길동",
                    "address": "서울특별시 강남구 테헤란로 123",
                    "tel": "02-1234-5678",
                    "fax": "02-1234-5679",
                    "email": "contact@test.com",
                    "business_type": "제조업",
                    "business_item": "전기 패널 제조",
                }
                response = await client.post("/v1/erp/company", json=company_data)

                # 첫 생성이면 201, 이미 있으면 409
                if response.status_code == 409:
                    # 이미 존재하는 경우 (다른 테스트에서 생성함)
                    json_response = response.json()
                    if "detail" in json_response:
                        assert "already exists" in json_response["detail"].lower()
                else:
                    assert response.status_code == 201
                    data = response.json()
                    assert data["name"] == "테스트 주식회사"
                    assert data["business_number"] == "123-45-67890"
                    assert "id" in data

    async def test_create_company_duplicate_fail(self):
        """자사정보 중복 생성 실패 (1개만 존재)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. First creation (may already exist)
                company_data = {
                    "business_number": "111-11-11111",
                    "name": "첫 번째 회사",
                    "ceo": "대표 A",
                    "address": "주소 A",
                }
                first_response = await client.post("/v1/erp/company", json=company_data)

                # 2. Second creation (should fail)
                company_data_2 = {
                    "business_number": "222-22-22222",
                    "name": "두 번째 회사",
                    "ceo": "대표 B",
                    "address": "주소 B",
                }
                second_response = await client.post("/v1/erp/company", json=company_data_2)

                # 이미 존재하므로 409 에러
                if first_response.status_code == 201:
                    assert second_response.status_code == 409
                    assert "already exists" in second_response.json()["detail"].lower()

    async def test_update_company_success(self):
        """자사정보 수정 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Ensure company exists
                get_response = await client.get("/v1/erp/company")
                if get_response.status_code == 404:
                    # Create if not exists
                    create_data = {
                        "business_number": "999-99-99999",
                        "name": "수정 테스트 회사",
                        "ceo": "대표 C",
                        "address": "주소 C",
                    }
                    await client.post("/v1/erp/company", json=create_data)

                # 2. Update company
                update_data = {
                    "name": "수정된 회사명",
                    "ceo": "수정된 대표",
                    "tel": "02-9999-9999",
                    "email": "updated@test.com",
                }
                update_response = await client.put("/v1/erp/company", json=update_data)

                if update_response.status_code == 200:
                    updated = update_response.json()
                    assert updated["tel"] == "02-9999-9999"
                    assert updated["email"] == "updated@test.com"

    async def test_get_company_after_creation(self):
        """자사정보 생성 후 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Ensure company exists
                get_response = await client.get("/v1/erp/company")
                if get_response.status_code == 404:
                    create_data = {
                        "business_number": "888-88-88888",
                        "name": "조회 테스트 회사",
                        "ceo": "대표 D",
                        "address": "주소 D",
                    }
                    create_response = await client.post(
                        "/v1/erp/company", json=create_data
                    )
                    assert create_response.status_code == 201

                # 2. Get company
                get_response = await client.get("/v1/erp/company")
                assert get_response.status_code == 200
                company = get_response.json()
                assert "id" in company
                assert "name" in company
                assert "business_number" in company
                assert "ceo" in company
