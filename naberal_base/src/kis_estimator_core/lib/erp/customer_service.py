"""
고객 관련 서비스 로직

고객 미수금 관리, 신용한도 체크 등의 비즈니스 로직을 담당합니다.
"""

import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional

from kis_estimator_core.core.ssot.constants import (
    RECEIVABLE_UPDATE_MODE_AUTO,
    RECEIVABLE_WARNING_THRESHOLD,
    RECEIVABLE_CRITICAL_THRESHOLD,
    ERROR_CODE_RECEIVABLE_OVERFLOW,
    ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
)


def update_customer_receivable(
    customer_id: str,
    amount: Decimal,
    customers_file_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    고객의 미수금을 업데이트합니다.

    Args:
        customer_id: 고객 ID
        amount: 추가할 매출 금액 (양수)
        customers_file_path: customers.json 파일 경로 (None이면 기본 경로 사용)

    Returns:
        Dict[str, Any]: 업데이트 결과
            성공 시:
                {
                    "success": True,
                    "customer_id": str,
                    "new_receivable": Decimal,
                    "warning": Optional[Dict]  # 신용한도 경고 시
                }
            실패 시:
                {
                    "success": False,
                    "error": {
                        "code": str,
                        "message": str,
                        "credit_limit": Optional[Decimal],
                        "attempted_receivable": Optional[Decimal]
                    }
                }
    """
    # 기본 파일 경로 설정
    if customers_file_path is None:
        customers_file_path = Path("data/erp/customers.json")

    print(f"[DEBUG] update_customer_receivable 호출됨")
    print(f"[DEBUG] customer_id: {customer_id}")
    print(f"[DEBUG] amount: {amount}")
    print(f"[DEBUG] customers_file_path: {customers_file_path}")
    print(f"[DEBUG] 파일 존재 여부: {customers_file_path.exists()}")

    try:
        # 1. customers.json 파일 읽기
        if not customers_file_path.exists():
            return {
                "success": False,
                "error": {
                    "code": ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
                    "message": f"Customers file not found: {customers_file_path}",
                },
            }

        with open(customers_file_path, "r", encoding="utf-8") as f:
            customers: List[Dict[str, Any]] = json.load(f)

        # 2. 해당 고객 찾기
        customer_index = None
        customer = None

        for idx, cust in enumerate(customers):
            if cust["id"] == customer_id:
                customer_index = idx
                customer = cust
                break

        if customer is None:
            print(f"[DEBUG] 고객을 찾을 수 없음: {customer_id}")
            return {
                "success": False,
                "error": {
                    "code": ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
                    "message": f"Customer not found: {customer_id}",
                },
            }

        print(f"[DEBUG] 고객 발견: {customer.get('name')}, ID: {customer.get('id')}")

        # 3. 현재 미수금과 신용한도 가져오기
        current_receivable = Decimal(str(customer.get("current_receivable", 0)))
        credit_limit = Decimal(str(customer.get("credit_limit", 0)))

        print(f"[DEBUG] 현재 미수금: {current_receivable}")
        print(f"[DEBUG] 신용한도: {credit_limit}")

        # 4. 새 미수금 계산
        new_receivable = current_receivable + amount

        print(f"[DEBUG] 새 미수금: {new_receivable}")

        # 5. 신용한도 검증
        # 5-1. 신용한도 초과 검사 (100%)
        if new_receivable > credit_limit:
            print(f"[DEBUG] 신용한도 초과! {new_receivable} > {credit_limit}")
            return {
                "success": False,
                "error": {
                    "code": ERROR_CODE_RECEIVABLE_OVERFLOW,
                    "message": (
                        f"Credit limit exceeded for customer {customer_id}. "
                        f"Credit limit: {credit_limit}, "
                        f"Attempted receivable: {new_receivable}"
                    ),
                    "credit_limit": credit_limit,
                    "attempted_receivable": new_receivable,
                },
            }

        # 5-2. 신용한도 경고 검사 (80%)
        warning = None
        if credit_limit > 0:
            usage_percent = float((new_receivable / credit_limit) * 100)
            if usage_percent >= RECEIVABLE_WARNING_THRESHOLD:
                warning = {
                    "type": "credit_limit_warning",
                    "threshold": RECEIVABLE_WARNING_THRESHOLD,
                    "usage_percent": round(usage_percent, 2),
                    "message": (
                        f"Customer {customer_id} has reached "
                        f"{usage_percent:.1f}% of credit limit"
                    ),
                }

        # 6. 미수금 업데이트
        customers[customer_index]["current_receivable"] = float(new_receivable)

        print(f"[DEBUG] 미수금 업데이트: {current_receivable} -> {new_receivable}")

        # 7. 파일 저장
        with open(customers_file_path, "w", encoding="utf-8") as f:
            json.dump(customers, f, ensure_ascii=False, indent=2)

        print(f"[DEBUG] 파일 저장 완료: {customers_file_path}")

        # 8. 결과 반환
        result: Dict[str, Any] = {
            "success": True,
            "customer_id": customer_id,
            "new_receivable": new_receivable,
        }

        if warning is not None:
            result["warning"] = warning

        return result

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
                "message": f"Failed to update customer receivable: {str(e)}",
            },
        }
