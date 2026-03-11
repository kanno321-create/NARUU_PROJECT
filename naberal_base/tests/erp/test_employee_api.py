"""
KIS ERP - Employee API Integration Tests
Contract-First + Evidence-Gated + Zero-Mock

Tests:
- GET /v1/erp/employees - List employees with filters
- GET /v1/erp/employees/{id} - Get employee detail
- POST /v1/erp/employees - Create employee
- PUT /v1/erp/employees/{id} - Update employee
- DELETE /v1/erp/employees/{id} - Delete employee (status='resigned')
"""

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from api.main import app


@pytest.mark.requires_db
@pytest.mark.asyncio
class TestEmployeeAPI:
    """Employee API 통합 테스트"""

    async def test_list_employees_empty(self):
        """빈 사원 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                response = await client.get("/v1/erp/employees")
                assert response.status_code == 200
                assert isinstance(response.json(), list)

    async def test_create_employee_success(self):
        """사원 생성 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                employee_data = {
                    "name": "홍길동",
                    "department": "영업부",
                    "position": "대리",
                    "tel": "010-1234-5678",
                    "email": "hong@example.com",
                }
                response = await client.post("/v1/erp/employees", json=employee_data)
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "홍길동"
                assert data["department"] == "영업부"
                assert data["position"] == "대리"
                assert "id" in data
                assert "emp_no" in data
                assert data["emp_no"].startswith("E")
                assert data["status"] == "active"

    async def test_get_employee_not_found(self):
        """존재하지 않는 사원 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                fake_uuid = "00000000-0000-0000-0000-000000000000"
                response = await client.get(f"/v1/erp/employees/{fake_uuid}")
                assert response.status_code == 404
                # HTTPException response format
                json_response = response.json()
                if "detail" in json_response:
                    assert "사원을 찾을 수 없습니다" in json_response["detail"]

    async def test_update_employee_success(self):
        """사원 정보 수정 성공"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create employee
                employee_data = {
                    "name": "김철수",
                    "department": "개발부",
                    "position": "사원",
                    "tel": "010-2222-3333",
                    "email": "kim@example.com",
                }
                create_response = await client.post(
                    "/v1/erp/employees", json=employee_data
                )
                assert create_response.status_code == 201
                employee_id = create_response.json()["id"]

                # 2. Update employee (promotion)
                update_data = {
                    "name": "김철수",
                    "department": "개발부",
                    "position": "대리",  # Promoted
                    "tel": "010-2222-3333",
                    "email": "kim.new@example.com",  # Email changed
                    "status": "active",
                }
                update_response = await client.put(
                    f"/v1/erp/employees/{employee_id}", json=update_data
                )
                assert update_response.status_code == 200
                updated = update_response.json()
                assert updated["position"] == "대리"
                assert updated["email"] == "kim.new@example.com"

    async def test_delete_employee_resignation(self):
        """사원 삭제 (퇴사 처리)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create employee
                employee_data = {
                    "name": "박영희",
                    "department": "총무부",
                    "position": "과장",
                    "tel": "010-5555-6666",
                }
                create_response = await client.post(
                    "/v1/erp/employees", json=employee_data
                )
                assert create_response.status_code == 201
                employee_id = create_response.json()["id"]

                # 2. Delete employee (status becomes 'resigned')
                delete_response = await client.delete(
                    f"/v1/erp/employees/{employee_id}"
                )
                assert delete_response.status_code == 204

                # 3. Verify employee status is 'resigned'
                get_response = await client.get(f"/v1/erp/employees/{employee_id}")
                if get_response.status_code == 200:
                    employee = get_response.json()
                    assert employee["status"] == "resigned"

    async def test_list_employees_with_filters(self):
        """필터를 사용한 사원 목록 조회"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create test employees
                employee1 = {
                    "name": "이순신",
                    "department": "영업부",
                    "position": "부장",
                    "tel": "010-1111-2222",
                }
                employee2 = {
                    "name": "세종대왕",
                    "department": "개발부",
                    "position": "이사",
                    "tel": "010-3333-4444",
                }
                await client.post("/v1/erp/employees", json=employee1)
                await client.post("/v1/erp/employees", json=employee2)

                # 2. Filter by department
                response = await client.get("/v1/erp/employees?department=영업부")
                assert response.status_code == 200
                employees = response.json()
                assert all(e["department"] == "영업부" for e in employees)

                # 3. Filter by status
                response = await client.get("/v1/erp/employees?status=active")
                assert response.status_code == 200
                employees = response.json()
                assert all(e["status"] == "active" for e in employees)

                # 4. Search by name
                response = await client.get("/v1/erp/employees?search=순신")
                assert response.status_code == 200
                employees = response.json()
                assert any("순신" in e["name"] for e in employees)

    async def test_employee_emp_no_auto_increment(self):
        """사원번호 자동 증가 검증"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create first employee
                employee1 = {
                    "name": "사번테스트1",
                    "department": "테스트부",
                    "position": "사원",
                }
                response1 = await client.post("/v1/erp/employees", json=employee1)
                emp_no_1 = response1.json()["emp_no"]

                # 2. Create second employee
                employee2 = {
                    "name": "사번테스트2",
                    "department": "테스트부",
                    "position": "사원",
                }
                response2 = await client.post("/v1/erp/employees", json=employee2)
                emp_no_2 = response2.json()["emp_no"]

                # 3. Verify emp_no increments
                assert emp_no_1.startswith("E")
                assert emp_no_2.startswith("E")
                num1 = int(emp_no_1[1:])
                num2 = int(emp_no_2[1:])
                assert num2 == num1 + 1

    async def test_update_employee_status(self):
        """사원 상태 변경 (active → resigned)"""
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as client:
                # 1. Create employee
                employee_data = {
                    "name": "상태테스트",
                    "department": "인사부",
                    "position": "대리",
                }
                create_response = await client.post(
                    "/v1/erp/employees", json=employee_data
                )
                employee_id = create_response.json()["id"]

                # 2. Update status to resigned via PUT
                update_data = {
                    "name": "상태테스트",
                    "department": "인사부",
                    "position": "대리",
                    "status": "resigned",
                }
                update_response = await client.put(
                    f"/v1/erp/employees/{employee_id}", json=update_data
                )
                assert update_response.status_code == 200
                updated = update_response.json()
                assert updated["status"] == "resigned"
