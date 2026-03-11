"""
매출전표-미수금 통합 테스트

작성일: 2025-12-07
목적: 매출전표 저장 시 고객 미수금 자동 업데이트 검증 (E2E)

TDD Red Phase: 테스트 먼저 작성하여 실패하는 것을 확인
"""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal

from src.kis_estimator_core.api.main import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def temp_test_data(tmp_path: Path):
    """임시 테스트 데이터 디렉토리 및 파일 생성"""
    # 임시 데이터 디렉토리
    data_dir = tmp_path / "erp"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 테스트용 고객 데이터
    customers_data = [
        {
            "id": "test_cust_001",
            "code": "C001",
            "name": "테스트고객1",
            "customer_type": "법인",
            "grade": "A",
            "credit_limit": "1000000.00",
            "current_receivable": "100000.00",
            "is_active": True,
            "created_at": "2025-12-07T00:00:00",
            "updated_at": None,
        },
        {
            "id": "test_cust_002",
            "code": "C002",
            "name": "테스트고객2",
            "customer_type": "개인",
            "grade": "B",
            "credit_limit": "500000.00",
            "current_receivable": "450000.00",  # 90% 사용
            "is_active": True,
            "created_at": "2025-12-07T00:00:00",
            "updated_at": None,
        },
    ]

    # 빈 매출 데이터
    sales_data = []

    # 파일 생성
    customers_file = data_dir / "customers.json"
    sales_file = data_dir / "sales.json"

    with open(customers_file, "w", encoding="utf-8") as f:
        json.dump(customers_data, f, ensure_ascii=False, indent=2)

    with open(sales_file, "w", encoding="utf-8") as f:
        json.dump(sales_data, f, ensure_ascii=False, indent=2)

    # 환경변수 패칭 (필요시)
    import os
    from unittest.mock import patch

    original_data_dir = os.environ.get("ERP_DATA_DIR")

    with patch.dict(os.environ, {"ERP_DATA_DIR": str(data_dir)}):
        yield {
            "data_dir": data_dir,
            "customers_file": customers_file,
            "sales_file": sales_file,
        }

    # 정리
    if original_data_dir:
        os.environ["ERP_DATA_DIR"] = original_data_dir


def test_create_sale_updates_customer_receivable(client, temp_test_data):
    """매출전표 저장 시 고객 미수금 자동 업데이트 테스트

    시나리오:
    1. 초기 미수금이 100,000원인 고객
    2. 50,000원 매출 발생 (VAT 포함 55,000원)
    3. 미수금이 155,000원으로 증가하는지 확인
    """
    # Arrange - 실제 고객 ID 사용 (credit_limit: 1M, current_receivable: 100K)
    customer_id = "6548c874-f073-442b-869c-7af831d4df90"

    # 실제 customers.json 파일 사용
    from src.kis_estimator_core.api.routes.erp import DATA_DIR
    customers_file = DATA_DIR / "customers.json"

    # 초기 미수금 확인
    with open(customers_file, "r", encoding="utf-8") as f:
        customers_before = json.load(f)

    customer_before = next((c for c in customers_before if c["id"] == customer_id), None)
    assert customer_before is not None
    initial_receivable = Decimal(str(customer_before["current_receivable"]))

    # Act: 매출 생성
    sale_data = {
        "sale_date": str(date.today()),
        "customer_id": customer_id,
        "status": "confirmed",
        "items": [
            {
                "product_name": "테스트상품",
                "spec": "규격A",
                "unit": "EA",
                "quantity": 1,
                "unit_price": "50000",
                "cost_price": "30000",
            }
        ],
    }

    # DATA_DIR 패치가 필요한 경우 임시로 하드코딩된 경로 사용
    # TODO: erp.py의 _load_data, _save_data가 환경변수를 참조하도록 수정 필요

    # 현재 이 테스트는 실제 data/erp/ 디렉토리를 사용하므로
    # 통합 테스트로서 실제 환경에서 실행됩니다
    response = client.post("/erp/sales", json=sale_data)

    # Assert: 응답 성공
    assert response.status_code == 200
    result = response.json()
    assert result["customer_id"] == customer_id
    # Note: API returns Decimal as string without trailing zeros
    assert Decimal(result["total_amount"]) == Decimal("55000")  # 50,000 + 5,000 (VAT)

    # Assert: 고객 미수금이 155,000원으로 증가했는지 확인
    # (현재는 create_sale()에 미수금 업데이트 로직이 없으므로 이 부분에서 실패할 것)
    from src.kis_estimator_core.api.routes.erp import DATA_DIR
    actual_customers_file = DATA_DIR / "customers.json"

    with open(actual_customers_file, "r", encoding="utf-8") as f:
        customers_after = json.load(f)

    customer_after = next((c for c in customers_after if c["id"] == customer_id), None)
    assert customer_after is not None

    # 이 assertion은 현재 실패할 것 (TDD Red Phase)
    expected_receivable = Decimal("155000.00")  # 100,000 + 55,000
    actual_receivable = Decimal(str(customer_after["current_receivable"]))

    assert actual_receivable == expected_receivable, (
        f"Expected current_receivable to be {expected_receivable}, "
        f"but got {actual_receivable}. "
        f"create_sale() should update customer receivable automatically."
    )


def test_create_sale_warns_on_credit_limit_80_percent(client, temp_test_data):
    """신용한도 80% 도달 시 경고 발생 테스트

    시나리오:
    1. 신용한도 500,000원, 현재 미수금 450,000원 (90%)인 고객
    2. 추가로 50,000원 매출 발생하면 100% 초과
    3. 응답에 warning 필드 포함 여부 확인
    """
    # Arrange - 실제 고객 ID 사용 (credit_limit: 500K, current_receivable: 450K = 90%)
    customer_id = "1bf2026b-66c3-46cc-8499-08e2ea156879"

    # Act: 50,000원 매출 생성
    sale_data = {
        "sale_date": str(date.today()),
        "customer_id": customer_id,
        "status": "confirmed",
        "items": [
            {
                "product_name": "테스트상품B",
                "unit": "EA",
                "quantity": 1,
                "unit_price": "50000",
                "cost_price": "30000",
            }
        ],
    }

    response = client.post("/erp/sales", json=sale_data)

    # Assert: 응답 성공 (신용한도 초과해도 매출은 저장됨)
    assert response.status_code == 200
    result = response.json()

    # Assert: 응답에 warning 필드 포함
    # (현재는 create_sale()에 경고 로직이 없으므로 이 부분에서 실패할 것)
    assert "warning" in result, (
        "Expected 'warning' field in response when credit limit is exceeded, "
        "but it was not found. create_sale() should check credit limit and add warning."
    )

    if "warning" in result:
        assert result["warning"]["type"] == "credit_limit_warning"
        assert result["warning"]["threshold"] >= 80


def test_create_sale_errors_on_credit_limit_exceed(client, temp_test_data):
    """신용한도 100% 초과 시 오류 발생 테스트

    시나리오:
    1. 신용한도 500,000원, 현재 미수금 450,000원 (90%)인 고객
    2. 추가로 100,000원 매출 발생하면 110% 초과
    3. 매출 저장 차단 또는 critical warning 발생
    """
    # Arrange - 실제 고객 ID 사용 (credit_limit: 500K, current_receivable: 450K = 90%)
    customer_id = "1bf2026b-66c3-46cc-8499-08e2ea156879"

    # Act: 100,000원 매출 생성 (한도 초과)
    sale_data = {
        "sale_date": str(date.today()),
        "customer_id": customer_id,
        "status": "confirmed",
        "items": [
            {
                "product_name": "고액상품",
                "unit": "EA",
                "quantity": 1,
                "unit_price": "100000",
                "cost_price": "60000",
            }
        ],
    }

    response = client.post("/erp/sales", json=sale_data)

    # Assert: 현재 구현에서는 매출이 저장되지만,
    # 향후 정책에 따라 400 에러를 반환하거나
    # 200 응답에 critical warning을 포함할 수 있음

    # 현재는 경고 없이 저장되므로 이 테스트는 실패할 것 (TDD Red Phase)
    if response.status_code == 200:
        result = response.json()
        assert "warning" in result or "error" in result, (
            "Expected warning or error when credit limit is critically exceeded (>100%), "
            "but response contained neither."
        )
    elif response.status_code == 400:
        # 한도 초과로 매출 저장이 차단된 경우
        result = response.json()
        assert "error" in result
        assert "credit_limit" in result["error"]["message"].lower()
    else:
        pytest.fail(f"Unexpected status code: {response.status_code}")
