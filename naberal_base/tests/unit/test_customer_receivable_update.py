"""
고객 미수금 자동 업데이트 기능 단위 테스트

TDD Red Phase: 테스트 먼저 작성하여 실패하는 것을 확인
"""

import pytest
import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any

from src.kis_estimator_core.core.ssot.constants import (
    RECEIVABLE_UPDATE_MODE_AUTO,
    RECEIVABLE_WARNING_THRESHOLD,
    RECEIVABLE_CRITICAL_THRESHOLD,
    ERROR_CODE_RECEIVABLE_OVERFLOW,
    ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
)


@pytest.fixture
def temp_customers_file(tmp_path: Path) -> Path:
    """임시 customers.json 파일 생성 픽스처"""
    customers_data = [
        {
            "id": "CUST-001",
            "name": "테스트 고객1",
            "credit_limit": Decimal("1000000"),
            "current_receivable": Decimal("500000"),
        },
        {
            "id": "CUST-002",
            "name": "테스트 고객2",
            "credit_limit": Decimal("2000000"),
            "current_receivable": Decimal("1500000"),  # 75% 사용
        },
        {
            "id": "CUST-003",
            "name": "테스트 고객3",
            "credit_limit": Decimal("1000000"),
            "current_receivable": Decimal("950000"),  # 95% 사용
        },
    ]

    file_path = tmp_path / "customers.json"

    # Decimal을 float로 변환하여 JSON 저장
    json_data = []
    for customer in customers_data:
        customer_dict = customer.copy()
        customer_dict["credit_limit"] = float(customer["credit_limit"])
        customer_dict["current_receivable"] = float(customer["current_receivable"])
        json_data.append(customer_dict)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    return file_path


def test_update_customer_receivable_adds_to_existing(temp_customers_file: Path):
    """기존 미수금에 새 매출액을 더하는지 테스트"""
    # Arrange
    from src.kis_estimator_core.lib.erp.customer_service import update_customer_receivable

    customer_id = "CUST-001"
    sale_amount = Decimal("100000")

    # Act
    result = update_customer_receivable(
        customer_id=customer_id,
        amount=sale_amount,
        customers_file_path=temp_customers_file,
    )

    # Assert
    assert result["success"] is True
    assert result["customer_id"] == customer_id
    assert result["new_receivable"] == Decimal("600000")  # 500000 + 100000
    assert "warning" not in result

    # 파일 업데이트 확인
    with open(temp_customers_file, "r", encoding="utf-8") as f:
        customers = json.load(f)

    updated_customer = next(c for c in customers if c["id"] == customer_id)
    assert updated_customer["current_receivable"] == 600000.0


def test_update_customer_receivable_warns_on_credit_limit_80(temp_customers_file: Path):
    """신용한도 80% 도달 시 경고 발생 테스트"""
    # Arrange
    from src.kis_estimator_core.lib.erp.customer_service import update_customer_receivable

    customer_id = "CUST-002"  # 현재 75% 사용 중
    sale_amount = Decimal("100000")  # → 80% 초과 (1,600,000 / 2,000,000 = 80%)

    # Act
    result = update_customer_receivable(
        customer_id=customer_id,
        amount=sale_amount,
        customers_file_path=temp_customers_file,
    )

    # Assert
    assert result["success"] is True
    assert result["customer_id"] == customer_id
    assert result["new_receivable"] == Decimal("1600000")
    assert "warning" in result
    assert result["warning"]["type"] == "credit_limit_warning"
    assert result["warning"]["threshold"] == RECEIVABLE_WARNING_THRESHOLD
    assert result["warning"]["usage_percent"] == 80.0


def test_update_customer_receivable_errors_on_credit_limit_exceed(temp_customers_file: Path):
    """신용한도 초과 시 오류 발생 테스트"""
    # Arrange
    from src.kis_estimator_core.lib.erp.customer_service import update_customer_receivable

    customer_id = "CUST-003"  # 현재 95% 사용 중
    sale_amount = Decimal("100000")  # → 105% 초과 (1,050,000 / 1,000,000 = 105%)

    # Act
    result = update_customer_receivable(
        customer_id=customer_id,
        amount=sale_amount,
        customers_file_path=temp_customers_file,
    )

    # Assert
    assert result["success"] is False
    assert result["error"]["code"] == ERROR_CODE_RECEIVABLE_OVERFLOW
    assert result["error"]["message"] is not None
    assert "credit_limit" in result["error"]
    assert "attempted_receivable" in result["error"]

    # 파일이 업데이트되지 않았는지 확인
    with open(temp_customers_file, "r", encoding="utf-8") as f:
        customers = json.load(f)

    customer = next(c for c in customers if c["id"] == customer_id)
    assert customer["current_receivable"] == 950000.0  # 변경되지 않음


def test_update_customer_receivable_handles_nonexistent_customer(temp_customers_file: Path):
    """존재하지 않는 고객 처리 테스트"""
    # Arrange
    from src.kis_estimator_core.lib.erp.customer_service import update_customer_receivable

    customer_id = "CUST-999"  # 존재하지 않는 고객
    sale_amount = Decimal("100000")

    # Act
    result = update_customer_receivable(
        customer_id=customer_id,
        amount=sale_amount,
        customers_file_path=temp_customers_file,
    )

    # Assert
    assert result["success"] is False
    assert result["error"]["code"] == ERROR_CODE_RECEIVABLE_UPDATE_FAILED
    assert "not found" in result["error"]["message"].lower()


def test_update_customer_receivable_updates_json_file(temp_customers_file: Path):
    """customers.json 파일 업데이트 확인 테스트"""
    # Arrange
    from src.kis_estimator_core.lib.erp.customer_service import update_customer_receivable

    customer_id = "CUST-001"
    sale_amount = Decimal("200000")

    # 업데이트 전 파일 내용 확인
    with open(temp_customers_file, "r", encoding="utf-8") as f:
        customers_before = json.load(f)

    customer_before = next(c for c in customers_before if c["id"] == customer_id)
    assert customer_before["current_receivable"] == 500000.0

    # Act
    result = update_customer_receivable(
        customer_id=customer_id,
        amount=sale_amount,
        customers_file_path=temp_customers_file,
    )

    # Assert - 함수 결과 확인
    assert result["success"] is True
    assert result["new_receivable"] == Decimal("700000")

    # 업데이트 후 파일 내용 확인
    with open(temp_customers_file, "r", encoding="utf-8") as f:
        customers_after = json.load(f)

    customer_after = next(c for c in customers_after if c["id"] == customer_id)
    assert customer_after["current_receivable"] == 700000.0

    # 다른 고객 데이터는 변경되지 않았는지 확인
    for customer in customers_after:
        if customer["id"] != customer_id:
            original = next(c for c in customers_before if c["id"] == customer["id"])
            assert customer["current_receivable"] == original["current_receivable"]
