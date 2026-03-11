"""
KIS ERP - Product API Integration Tests
Contract-First + Evidence-Gated + Zero-Mock

Tests:
- GET /v1/erp/products - List products with filters
- GET /v1/erp/products/{id} - Get product detail
- POST /v1/erp/products - Create product
- PUT /v1/erp/products/{id} - Update product
- DELETE /v1/erp/products/{id} - Delete product (soft delete)
- PATCH /v1/erp/products/{id}/stock - Adjust stock
- GET /v1/erp/products/{id}/stock-history - Get stock history
"""

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from api.main import app


@pytest.mark.requires_db
@pytest.mark.asyncio
class TestProductAPI:
    """Product API 통합 테스트"""

    async def test_list_products_empty(self):
        """빈 상품 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                response = await client.get("/v1/erp/products")
                assert response.status_code == 200
                assert isinstance(response.json(), list)

    async def test_create_product_success(self):
        """상품 생성 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                product_data = {
                    "name": "테스트 상품",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 10000,
                    "sale_price": 15000,
                    "spec": "100V 10A",
                    "manufacturer": "테스트 제조사",
                }
                response = await client.post("/v1/erp/products", json=product_data)
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "테스트 상품"
                assert data["unit_cost"] == 10000
                assert data["sale_price"] == 15000
                assert "id" in data
                assert "code" in data
                assert data["code"].startswith("P")

    async def test_get_product_not_found(self):
        """존재하지 않는 상품 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                fake_uuid = "00000000-0000-0000-0000-000000000000"
                response = await client.get(f"/v1/erp/products/{fake_uuid}")
                assert response.status_code == 404
                # HTTPException response format
                json_response = response.json()
                if "detail" in json_response:
                    assert "상품을 찾을 수 없습니다" in json_response["detail"]

    async def test_update_product_success(self):
        """상품 수정 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create product
                product_data = {
                    "name": "수정 테스트 상품",
                    "category": "부속자재",
                    "unit": "M",
                    "unit_cost": 5000,
                    "sale_price": 8000,
                }
                create_response = await client.post(
                    "/v1/erp/products", json=product_data
                )
                assert create_response.status_code == 201
                product_id = create_response.json()["id"]

                # 2. Update product
                update_data = {
                    "name": "수정된 상품",
                    "category": "부속자재",
                    "unit": "M",
                    "unit_cost": 5000,
                    "sale_price": 10000,  # Changed
                    "is_active": True,
                }
                update_response = await client.put(
                    f"/v1/erp/products/{product_id}", json=update_data
                )
                assert update_response.status_code == 200
                updated = update_response.json()
                assert updated["sale_price"] == 10000
                assert updated["name"] == "수정된 상품"

    async def test_delete_product_soft_delete(self):
        """상품 삭제 (소프트 삭제)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create product
                product_data = {
                    "name": "삭제 테스트 상품",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 1000,
                    "sale_price": 2000,
                }
                create_response = await client.post(
                    "/v1/erp/products", json=product_data
                )
                assert create_response.status_code == 201
                product_id = create_response.json()["id"]

                # 2. Delete product
                delete_response = await client.delete(f"/v1/erp/products/{product_id}")
                assert delete_response.status_code == 204

                # 3. Verify product is inactive
                get_response = await client.get(f"/v1/erp/products/{product_id}")
                if get_response.status_code == 200:
                    product = get_response.json()
                    assert product["is_active"] is False

    async def test_list_products_with_filters(self):
        """필터를 사용한 상품 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create test products
                product1 = {
                    "name": "필터 테스트 상품A",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 1000,
                    "sale_price": 1500,
                }
                product2 = {
                    "name": "필터 테스트 상품B",
                    "category": "차단기",
                    "unit": "M",
                    "unit_cost": 2000,
                    "sale_price": 3000,
                }
                await client.post("/v1/erp/products", json=product1)
                await client.post("/v1/erp/products", json=product2)

                # 2. Filter by category
                response = await client.get("/v1/erp/products?category=부속자재")
                assert response.status_code == 200
                products = response.json()
                assert all(p["category"] == "부속자재" for p in products)

                # 3. Search by name
                response = await client.get("/v1/erp/products?search=필터")
                assert response.status_code == 200
                products = response.json()
                assert any("필터" in p["name"] for p in products)

    async def test_adjust_stock_increase(self):
        """재고 수량 증가"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create product
                product_data = {
                    "name": "재고 테스트 상품",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 5000,
                    "sale_price": 8000,
                }
                create_response = await client.post(
                    "/v1/erp/products", json=product_data
                )
                product_id = create_response.json()["id"]
                initial_stock = create_response.json()["stock_qty"]

                # 2. Increase stock
                adjust_response = await client.patch(
                    f"/v1/erp/products/{product_id}/stock?adjustment=100&reason=입고"
                )
                assert adjust_response.status_code == 200
                adjusted = adjust_response.json()
                assert adjusted["stock_qty"] == initial_stock + 100

    async def test_adjust_stock_decrease(self):
        """재고 수량 감소"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create product with stock
                product_data = {
                    "name": "재고 감소 테스트",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 3000,
                    "sale_price": 5000,
                }
                create_response = await client.post(
                    "/v1/erp/products", json=product_data
                )
                product_id = create_response.json()["id"]

                # 2. Increase stock first
                await client.patch(
                    f"/v1/erp/products/{product_id}/stock?adjustment=50&reason=초기재고"
                )

                # 3. Decrease stock
                adjust_response = await client.patch(
                    f"/v1/erp/products/{product_id}/stock?adjustment=-10&reason=출고"
                )
                assert adjust_response.status_code == 200
                adjusted = adjust_response.json()
                assert adjusted["stock_qty"] == 40

    async def test_get_stock_history_not_implemented(self):
        """재고 이력 조회 (현재 미구현)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create product
                product_data = {
                    "name": "이력 테스트 상품",
                    "category": "부속자재",
                    "unit": "EA",
                    "unit_cost": 1000,
                    "sale_price": 1500,
                }
                create_response = await client.post(
                    "/v1/erp/products", json=product_data
                )
                product_id = create_response.json()["id"]

                # 2. Get stock history (currently returns empty list)
                history_response = await client.get(
                    f"/v1/erp/products/{product_id}/stock-history"
                )
                assert history_response.status_code == 200
                history = history_response.json()
                assert isinstance(history, list)
                # 현재는 빈 배열 (재고 이력 테이블 미구현)
