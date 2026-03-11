"""
KIS ERP - Customer API Integration Tests
Contract-First + Evidence-Gated + Zero-Mock

Tests:
- GET /v1/erp/customers - List customers with filters
- GET /v1/erp/customers/{id} - Get customer detail
- POST /v1/erp/customers - Create customer
- PUT /v1/erp/customers/{id} - Update customer
- DELETE /v1/erp/customers/{id} - Delete customer (soft delete)
- GET /v1/erp/customers/{id}/balance - Get customer balance
"""

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from api.main import app


@pytest.mark.requires_db
@pytest.mark.asyncio
class TestCustomerAPI:
    """Customer API 통합 테스트"""

    async def test_list_customers_empty(self):
        """빈 거래처 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                response = await client.get("/v1/erp/customers")
                assert response.status_code == 200
                assert isinstance(response.json(), list)

    async def test_create_customer_success(self):
        """거래처 생성 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                customer_data = {
                    "name": "테스트 거래처",
                    "type": "매출",
                    "business_number": "123-45-67890",
                    "ceo": "홍길동",
                    "tel": "02-1234-5678",
                    "email": "test@example.com",
                }
                response = await client.post("/v1/erp/customers", json=customer_data)
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "테스트 거래처"
                assert data["type"] == "매출"
                assert "id" in data
                assert "code" in data
                assert data["code"].startswith("C")

    async def test_get_customer_not_found(self):
        """존재하지 않는 거래처 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                fake_uuid = "00000000-0000-0000-0000-000000000000"
                response = await client.get(f"/v1/erp/customers/{fake_uuid}")
                assert response.status_code == 404
                # HTTPException response format
                json_response = response.json()
                if "detail" in json_response:
                    assert "거래처를 찾을 수 없습니다" in json_response["detail"]

    async def test_update_customer_success(self):
        """거래처 수정 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create customer
                customer_data = {
                    "name": "수정 테스트 거래처",
                    "type": "매출",
                    "business_number": "999-99-99999",
                    "ceo": "김철수",
                    "tel": "02-9999-9999",
                }
                create_response = await client.post(
                    "/v1/erp/customers", json=customer_data
                )
                assert create_response.status_code == 201
                customer_id = create_response.json()["id"]

                # 2. Update customer
                update_data = {
                    "name": "수정된 거래처",
                    "type": "매출",
                    "ceo": "김철수",
                    "tel": "02-8888-8888",  # Changed
                }
                update_response = await client.put(
                    f"/v1/erp/customers/{customer_id}", json=update_data
                )
                assert update_response.status_code == 200
                updated = update_response.json()
                assert updated["tel"] == "02-8888-8888"
                assert updated["name"] == "수정된 거래처"

    async def test_delete_customer_soft_delete(self):
        """거래처 삭제 (소프트 삭제)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create customer
                customer_data = {
                    "name": "삭제 테스트 거래처",
                    "type": "매입",
                    "ceo": "박영희",
                }
                create_response = await client.post(
                    "/v1/erp/customers", json=customer_data
                )
                assert create_response.status_code == 201
                customer_id = create_response.json()["id"]

                # 2. Delete customer
                delete_response = await client.delete(f"/v1/erp/customers/{customer_id}")
                assert delete_response.status_code == 204

                # 3. Verify customer is inactive
                get_response = await client.get(f"/v1/erp/customers/{customer_id}")
                if get_response.status_code == 200:
                    customer = get_response.json()
                    assert customer["is_active"] is False

    async def test_list_customers_with_filters(self):
        """필터를 사용한 거래처 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create test customers
                customer1 = {
                    "name": "ABC 회사",
                    "type": "매출",
                    "ceo": "홍길동",
                }
                customer2 = {
                    "name": "XYZ 회사",
                    "type": "매입",
                    "ceo": "김철수",
                }
                await client.post("/v1/erp/customers", json=customer1)
                await client.post("/v1/erp/customers", json=customer2)

                # 2. Filter by type
                response = await client.get("/v1/erp/customers?customer_type=매출")
                assert response.status_code == 200
                customers = response.json()
                assert all(c["type"] == "매출" for c in customers)

                # 3. Search by name
                response = await client.get("/v1/erp/customers?search=ABC")
                assert response.status_code == 200
                customers = response.json()
                assert any("ABC" in c["name"] for c in customers)

    async def test_get_customer_balance(self):
        """거래처 잔액 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create customer
                customer_data = {
                    "name": "잔액 테스트 거래처",
                    "type": "매출",
                    "ceo": "이순신",
                }
                create_response = await client.post(
                    "/v1/erp/customers", json=customer_data
                )
                customer_id = create_response.json()["id"]

                # 2. Get balance
                balance_response = await client.get(
                    f"/v1/erp/customers/{customer_id}/balance"
                )
                assert balance_response.status_code == 200
                data = balance_response.json()
                assert "customer_id" in data
                assert "balance" in data
                assert isinstance(data["balance"], (int, float))
