# 고객 미수금 자동 업데이트 기능 개발계획서

**날짜**: 2025-12-07
**목표**: 매출전표 저장 시 고객 미수금(receivable) 자동 업데이트
**스킬**: writing-plans, root-cause-tracing, test-driven-development
**원칙**: 목업금지, 빈파일금지, SSOT준수, 일관성있는코드작성

---

## 📋 Goal (목표)

매출전표가 저장될 때 **고객의 미수금(receivable)이 자동으로 증가**하도록 백엔드와 프론트엔드를 수정합니다.

### 현재 상태 (AS-IS)
- ❌ 매출전표 저장 시 `data/erp/sales.json`에만 저장됨
- ❌ `data/erp/customers.json`의 receivable 필드가 업데이트되지 않음
- ❌ 매출이 발생해도 고객별 미수금 현황이 반영되지 않음

### 목표 상태 (TO-BE)
- ✅ 매출전표 저장 시 고객 receivable이 자동으로 `total_amount`만큼 증가
- ✅ 트랜잭션 안전성 보장 (sales 저장 실패 시 receivable 변경 롤백)
- ✅ 프론트엔드에서 업데이트된 미수금을 즉시 확인 가능
- ✅ 데이터 정합성 검증 테스트 포함

---

## 🏗️ Architecture (아키텍처)

### 데이터 흐름
```
[Frontend: SalesVoucherWindow]
  ↓ POST /erp/sales (ERPSaleCreate)
[Backend: erp.py::create_sale()]
  ↓ 1. sales.json에 저장
  ↓ 2. customers.json 읽기
  ↓ 3. receivable 업데이트
  ↓ 4. customers.json 저장
  ↓ 5. ERPSale 응답 (updated customer 포함)
[Frontend]
  ↓ selectedCustomer receivable 업데이트
  ↓ UI 즉시 반영
```

### 트랜잭션 처리
```python
try:
    # 1. 매출 저장
    sale = save_sale_to_json(sale_data)

    # 2. 고객 미수금 업데이트
    customer = update_customer_receivable(
        customer_id=sale.customer_id,
        amount=sale.total_amount
    )

    # 3. 성공 응답
    return sale
except Exception as e:
    # 롤백 로직
    rollback_sale(sale.id)
    raise
```

### SSOT 준수
- **금액 단위**: `src/kis_estimator_core/core/ssot/constants.py`
- **상태 정의**: `src/kis_estimator_core/core/ssot/constants.py`
- **오류 코드**: `src/kis_estimator_core/core/ssot/constants.py`

---

## 🛠️ Tech Stack (기술 스택)

### Backend
- **언어**: Python 3.11+
- **프레임워크**: FastAPI
- **데이터 저장**: JSON 파일 (`data/erp/customers.json`, `data/erp/sales.json`)
- **스키마**: Pydantic (ERPCustomer, ERPSale)

### Frontend
- **언어**: TypeScript
- **프레임워크**: Next.js, React
- **API 클라이언트**: `frontend/src/lib/api.ts`
- **상태 관리**: React useState

### Testing
- **백엔드**: pytest
- **프론트엔드**: Jest (필요 시)
- **TDD 워크플로우**: test → fail → implement → pass → commit

---

## ✅ Tasks (작업 목록)

### Task 1: SSOT 상수 정의 (2분)
**목표**: 미수금 업데이트 관련 상수를 SSOT에 정의

**파일**: `src/kis_estimator_core/core/ssot/constants.py`

**코드**:
```python
# 기존 코드 하단에 추가

# ============================================================
# 고객 미수금 관련 상수 (Customer Receivables)
# ============================================================

# 미수금 업데이트 모드
RECEIVABLE_UPDATE_MODE_AUTO = "auto"  # 자동 업데이트
RECEIVABLE_UPDATE_MODE_MANUAL = "manual"  # 수동 업데이트

# 미수금 한도 경고 임계값 (%)
RECEIVABLE_WARNING_THRESHOLD = 80  # 신용한도의 80% 도달 시 경고
RECEIVABLE_CRITICAL_THRESHOLD = 100  # 신용한도 초과 시 치명적 경고

# 미수금 관련 오류 코드
ERROR_CODE_RECEIVABLE_OVERFLOW = "E_RECV_001"  # 신용한도 초과
ERROR_CODE_RECEIVABLE_UPDATE_FAILED = "E_RECV_002"  # 업데이트 실패
```

**Commit**:
```bash
git add src/kis_estimator_core/core/ssot/constants.py
git commit -m "feat: Add SSOT constants for customer receivables"
```

---

### Task 2: 백엔드 테스트 작성 - 미수금 업데이트 함수 (3분)
**목표**: 미수금 업데이트 함수에 대한 단위 테스트 작성 (TDD - 실패하는 테스트 먼저)

**파일**: `tests/unit/test_customer_receivable_update.py` (신규 생성)

**코드**:
```python
"""
고객 미수금 자동 업데이트 기능 단위 테스트

작성일: 2025-12-07
목적: 매출전표 저장 시 고객 미수금 자동 증가 검증
"""

import pytest
from datetime import date
from src.kis_estimator_core.api.routes.erp import update_customer_receivable
from src.kis_estimator_core.core.ssot.constants import (
    RECEIVABLE_UPDATE_MODE_AUTO,
    ERROR_CODE_RECEIVABLE_OVERFLOW,
)


def test_update_customer_receivable_success():
    """정상적인 미수금 업데이트 테스트"""
    # Given: 기존 미수금 100,000원인 고객
    customer_id = "cust_001"
    initial_receivable = 100_000
    additional_amount = 50_000

    # When: 50,000원 매출 발생
    result = update_customer_receivable(customer_id, additional_amount)

    # Then: 미수금이 150,000원으로 증가
    assert result["receivable"] == 150_000
    assert result["customer_id"] == customer_id


def test_update_customer_receivable_zero_amount():
    """0원 추가 시 미수금 변화 없음 테스트"""
    # Given: 기존 미수금 100,000원인 고객
    customer_id = "cust_001"
    initial_receivable = 100_000

    # When: 0원 매출 발생
    result = update_customer_receivable(customer_id, 0)

    # Then: 미수금 변화 없음
    assert result["receivable"] == initial_receivable


def test_update_customer_receivable_exceeds_credit_limit():
    """신용한도 초과 시 경고 발생 테스트"""
    # Given: 신용한도 200,000원, 현재 미수금 180,000원인 고객
    customer_id = "cust_002"
    credit_limit = 200_000
    current_receivable = 180_000
    additional_amount = 50_000  # 총 230,000원 → 한도 초과

    # When: 50,000원 매출 발생
    # Then: 한도 초과 경고 발생 (업데이트는 허용하되 경고)
    result = update_customer_receivable(customer_id, additional_amount)

    assert result["receivable"] == 230_000
    assert result["warning"] == ERROR_CODE_RECEIVABLE_OVERFLOW
    assert result["credit_limit_exceeded"] is True


def test_update_customer_receivable_negative_amount():
    """음수 금액(반품/할인) 처리 테스트"""
    # Given: 기존 미수금 100,000원인 고객
    customer_id = "cust_001"
    initial_receivable = 100_000
    refund_amount = -20_000

    # When: 20,000원 반품 발생
    result = update_customer_receivable(customer_id, refund_amount)

    # Then: 미수금이 80,000원으로 감소
    assert result["receivable"] == 80_000


def test_update_customer_receivable_customer_not_found():
    """존재하지 않는 고객 ID 처리 테스트"""
    # Given: 존재하지 않는 고객 ID
    customer_id = "nonexistent_customer"

    # When/Then: ValueError 발생
    with pytest.raises(ValueError, match="Customer not found"):
        update_customer_receivable(customer_id, 10_000)
```

**실행 (실패 확인)**:
```bash
pytest tests/unit/test_customer_receivable_update.py -v
# 예상: FAILED (함수가 아직 구현되지 않음)
```

**Commit**:
```bash
git add tests/unit/test_customer_receivable_update.py
git commit -m "test: Add unit tests for customer receivable update (TDD - red phase)"
```

---

### Task 3: 백엔드 미수금 업데이트 함수 구현 (5분)
**목표**: 고객 미수금을 업데이트하는 함수 구현 (TDD - 테스트 통과)

**파일**: `src/kis_estimator_core/api/routes/erp.py`

**코드 추가 위치**: `create_sale()` 함수 상단에 헬퍼 함수 추가

```python
# 기존 import 구문 하단에 추가
from src.kis_estimator_core.core.ssot.constants import (
    RECEIVABLE_UPDATE_MODE_AUTO,
    RECEIVABLE_WARNING_THRESHOLD,
    RECEIVABLE_CRITICAL_THRESHOLD,
    ERROR_CODE_RECEIVABLE_OVERFLOW,
    ERROR_CODE_RECEIVABLE_UPDATE_FAILED,
)


def update_customer_receivable(customer_id: str, amount: float) -> dict:
    """
    고객 미수금을 업데이트합니다.

    Args:
        customer_id: 고객 ID
        amount: 추가할 금액 (음수 가능 - 반품/할인 시)

    Returns:
        dict: {
            "customer_id": str,
            "receivable": float,
            "credit_limit_exceeded": bool,
            "warning": str | None
        }

    Raises:
        ValueError: 고객을 찾을 수 없는 경우
    """
    customers_file = DATA_DIR / "customers.json"

    # 1. customers.json 읽기
    if not customers_file.exists():
        raise ValueError("Customers data file not found")

    with open(customers_file, "r", encoding="utf-8") as f:
        customers_data = json.load(f)

    # 2. 고객 찾기
    customer = next(
        (c for c in customers_data if c["id"] == customer_id),
        None
    )

    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    # 3. 미수금 업데이트
    old_receivable = customer.get("receivable", 0.0)
    new_receivable = old_receivable + amount
    customer["receivable"] = new_receivable

    # 4. 신용한도 체크
    credit_limit = customer.get("credit_limit", 0.0)
    credit_limit_exceeded = new_receivable > credit_limit
    warning = ERROR_CODE_RECEIVABLE_OVERFLOW if credit_limit_exceeded else None

    # 5. customers.json 저장
    with open(customers_file, "w", encoding="utf-8") as f:
        json.dump(customers_data, f, ensure_ascii=False, indent=2)

    # 6. 결과 반환
    return {
        "customer_id": customer_id,
        "receivable": new_receivable,
        "credit_limit_exceeded": credit_limit_exceeded,
        "warning": warning,
    }
```

**실행 (성공 확인)**:
```bash
pytest tests/unit/test_customer_receivable_update.py -v
# 예상: PASSED (모든 테스트 통과)
```

**Commit**:
```bash
git add src/kis_estimator_core/api/routes/erp.py
git commit -m "feat: Implement customer receivable auto-update function (TDD - green phase)"
```

---

### Task 4: 백엔드 통합 테스트 작성 - 매출 저장 + 미수금 업데이트 (3분)
**목표**: 매출 저장 시 미수금이 자동으로 업데이트되는지 검증하는 통합 테스트 작성

**파일**: `tests/integration/test_sale_receivable_integration.py` (신규 생성)

**코드**:
```python
"""
매출전표-미수금 통합 테스트

작성일: 2025-12-07
목적: 매출전표 저장 시 고객 미수금 자동 업데이트 검증 (E2E)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date
from src.kis_estimator_core.api.main import app
from src.kis_estimator_core.api.routes.erp import DATA_DIR
import json


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """테스트용 고객 데이터 초기화"""
    customers_file = DATA_DIR / "customers.json"

    # 백업
    if customers_file.exists():
        backup_file = DATA_DIR / "customers_backup.json"
        with open(customers_file, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

    # 테스트 데이터 생성
    test_customers = [
        {
            "id": "test_cust_001",
            "code": "C001",
            "name": "테스트고객1",
            "customer_type": "법인",
            "grade": "A",
            "credit_limit": 1000000.0,
            "receivable": 100000.0,
            "is_active": True,
        }
    ]

    with open(customers_file, "w", encoding="utf-8") as f:
        json.dump(test_customers, f, ensure_ascii=False, indent=2)

    yield

    # 복원
    if backup_file.exists():
        with open(backup_file, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        with open(customers_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        backup_file.unlink()


def test_create_sale_updates_customer_receivable(client, setup_test_data):
    """매출전표 저장 시 고객 미수금 자동 업데이트 테스트"""
    # Given: 초기 미수금 100,000원인 고객
    customer_id = "test_cust_001"

    # When: 50,000원(VAT 포함 55,000원) 매출 발생
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
                "unit_price": 50000,
                "supply_amount": 50000,
                "tax_amount": 5000,
                "total_amount": 55000,
            }
        ]
    }

    response = client.post("/erp/sales", json=sale_data)

    # Then: 응답 성공
    assert response.status_code == 200
    result = response.json()

    # Then: 매출 데이터 정상 저장
    assert result["customer_id"] == customer_id
    assert result["total_amount"] == 55000

    # Then: 고객 미수금이 155,000원으로 증가
    customers_file = DATA_DIR / "customers.json"
    with open(customers_file, "r", encoding="utf-8") as f:
        customers = json.load(f)

    customer = next((c for c in customers if c["id"] == customer_id), None)
    assert customer is not None
    assert customer["receivable"] == 155000.0  # 100,000 + 55,000


def test_create_sale_exceeds_credit_limit_warning(client, setup_test_data):
    """신용한도 초과 시 경고 발생 테스트"""
    # Given: 신용한도 1,000,000원, 현재 미수금 100,000원인 고객
    customer_id = "test_cust_001"

    # When: 950,000원 매출 발생 (총 1,050,000원 → 한도 초과)
    sale_data = {
        "sale_date": str(date.today()),
        "customer_id": customer_id,
        "status": "confirmed",
        "items": [
            {
                "product_name": "고액상품",
                "unit": "EA",
                "quantity": 1,
                "unit_price": 950000,
                "supply_amount": 950000,
                "tax_amount": 95000,
                "total_amount": 1045000,
            }
        ]
    }

    response = client.post("/erp/sales", json=sale_data)

    # Then: 매출은 저장되지만 경고 포함
    assert response.status_code == 200
    result = response.json()

    # Then: 응답에 경고 정보 포함
    assert "warning" in result
    assert result["warning"]["code"] == "E_RECV_001"
    assert result["warning"]["credit_limit_exceeded"] is True
```

**실행 (실패 확인)**:
```bash
pytest tests/integration/test_sale_receivable_integration.py -v
# 예상: FAILED (create_sale()에 미수금 업데이트 로직이 아직 없음)
```

**Commit**:
```bash
git add tests/integration/test_sale_receivable_integration.py
git commit -m "test: Add integration tests for sale-receivable (TDD - red phase)"
```

---

### Task 5: 백엔드 create_sale() 함수에 미수금 업데이트 통합 (5분)
**목표**: 매출 저장 시 자동으로 미수금을 업데이트하도록 수정

**파일**: `src/kis_estimator_core/api/routes/erp.py`

**수정**: `create_sale()` 함수 내부

**변경 전**:
```python
@router.post("/sales", response_model=Sale, tags=["ERP"])
def create_sale(sale: SaleCreate):
    """매출전표 생성"""
    sales_file = DATA_DIR / "sales.json"

    # ... (기존 코드) ...

    # 저장
    with open(sales_file, "w", encoding="utf-8") as f:
        json.dump(sales_data, f, ensure_ascii=False, indent=2)

    return new_sale
```

**변경 후**:
```python
@router.post("/sales", response_model=Sale, tags=["ERP"])
def create_sale(sale: SaleCreate):
    """매출전표 생성 (고객 미수금 자동 업데이트 포함)"""
    sales_file = DATA_DIR / "sales.json"

    # ... (기존 코드: 매출 데이터 생성) ...

    try:
        # 1. 매출 저장
        with open(sales_file, "w", encoding="utf-8") as f:
            json.dump(sales_data, f, ensure_ascii=False, indent=2)

        # 2. 고객 미수금 자동 업데이트
        receivable_result = update_customer_receivable(
            customer_id=sale.customer_id,
            amount=new_sale["total_amount"]
        )

        # 3. 신용한도 초과 시 경고 추가
        if receivable_result.get("credit_limit_exceeded"):
            new_sale["warning"] = {
                "code": receivable_result["warning"],
                "message": "고객 신용한도를 초과했습니다.",
                "credit_limit_exceeded": True,
                "current_receivable": receivable_result["receivable"],
            }

        return new_sale

    except Exception as e:
        # 롤백: 저장된 매출 제거
        sales_data = [s for s in sales_data if s["id"] != new_sale["id"]]
        with open(sales_file, "w", encoding="utf-8") as f:
            json.dump(sales_data, f, ensure_ascii=False, indent=2)

        raise HTTPException(
            status_code=500,
            detail=f"매출 저장 실패: {str(e)}"
        )
```

**실행 (성공 확인)**:
```bash
pytest tests/integration/test_sale_receivable_integration.py -v
# 예상: PASSED (통합 테스트 통과)
```

**Commit**:
```bash
git add src/kis_estimator_core/api/routes/erp.py
git commit -m "feat: Integrate receivable auto-update into create_sale (TDD - green phase)"
```

---

### Task 6: 프론트엔드 타입 정의 업데이트 (2분)
**목표**: ERPSale 응답 타입에 warning 필드 추가

**파일**: `frontend/src/lib/api.ts`

**수정**: ERPSale 인터페이스

**변경 전** (lines 216-232):
```typescript
export interface ERPSale {
    id: string;
    sale_number: string;
    sale_date: string;
    customer_id: string;
    status: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    cost_amount: number;
    profit_amount: number;
    memo?: string | null;
    items: ERPSaleItem[];
    customer?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
}
```

**변경 후**:
```typescript
export interface ERPSale {
    id: string;
    sale_number: string;
    sale_date: string;
    customer_id: string;
    status: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    cost_amount: number;
    profit_amount: number;
    memo?: string | null;
    items: ERPSaleItem[];
    customer?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
    warning?: {
        code: string;
        message: string;
        credit_limit_exceeded: boolean;
        current_receivable: number;
    } | null;
}
```

**Commit**:
```bash
git add frontend/src/lib/api.ts
git commit -m "feat: Add warning field to ERPSale interface"
```

---

### Task 7: 프론트엔드 매출 저장 후 고객 정보 갱신 (5분)
**목표**: 매출 저장 성공 시 고객의 미수금을 즉시 업데이트

**파일**: `frontend/src/components/erp/windows/SalesVoucherWindow.tsx`

**수정**: handleSave 함수

**변경 전** (lines 225-253):
```typescript
const handleSave = async () => {
  if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
  if (items.length === 0) { alert("상품을 추가하세요."); return; }

  try {
    const saleData: ERPSaleCreate = {
      sale_date: saleDate,
      customer_id: selectedCustomer.id,
      status: "confirmed",
      memo: memo,
      items: items.map(item => ({
        product_name: item.productName,
        spec: item.spec,
        unit: item.unit,
        quantity: item.quantity,
        unit_price: item.unitPrice,
        supply_amount: item.supplyPrice,
        tax_amount: item.vat,
        total_amount: item.supplyPrice + item.vat,
        memo: item.memo,
      }))
    };

    const result = await api.erp.sales.create(saleData);
    alert(`저장되었습니다. 전표번호: ${result.sale_number}`);
  } catch (error) {
    alert(`저장 실패: ${error}`);
  }
};
```

**변경 후**:
```typescript
const handleSave = async () => {
  if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
  if (items.length === 0) { alert("상품을 추가하세요."); return; }

  try {
    const saleData: ERPSaleCreate = {
      sale_date: saleDate,
      customer_id: selectedCustomer.id,
      status: "confirmed",
      memo: memo,
      items: items.map(item => ({
        product_name: item.productName,
        spec: item.spec,
        unit: item.unit,
        quantity: item.quantity,
        unit_price: item.unitPrice,
        supply_amount: item.supplyPrice,
        tax_amount: item.vat,
        total_amount: item.supplyPrice + item.vat,
        memo: item.memo,
      }))
    };

    const result = await api.erp.sales.create(saleData);

    // 고객 미수금 즉시 업데이트
    if (selectedCustomer && result.warning?.current_receivable !== undefined) {
      setSelectedCustomer({
        ...selectedCustomer,
        receivable: result.warning.current_receivable,
      });
    } else if (selectedCustomer) {
      // 경고가 없어도 미수금 업데이트 (total_amount만큼 증가)
      setSelectedCustomer({
        ...selectedCustomer,
        receivable: selectedCustomer.receivable + result.total_amount,
      });
    }

    // 신용한도 초과 경고 표시
    if (result.warning?.credit_limit_exceeded) {
      alert(
        `저장되었습니다. 전표번호: ${result.sale_number}\n\n` +
        `⚠️ 경고: ${result.warning.message}\n` +
        `현재 미수금: ${result.warning.current_receivable.toLocaleString()}원\n` +
        `신용한도: ${selectedCustomer.creditLimit.toLocaleString()}원`
      );
    } else {
      alert(`저장되었습니다. 전표번호: ${result.sale_number}`);
    }

    // 입력 폼 초기화
    setItems([]);
    setMemo("");

  } catch (error) {
    alert(`저장 실패: ${error}`);
  }
};
```

**Commit**:
```bash
git add frontend/src/components/erp/windows/SalesVoucherWindow.tsx
git commit -m "feat: Auto-update customer receivable in UI after sale creation"
```

---

### Task 8: E2E 테스트 작성 - 프론트엔드 미수금 표시 확인 (3분)
**목표**: 매출 저장 후 UI에서 미수금이 즉시 갱신되는지 검증

**파일**: `tests/e2e/test_sales_voucher_receivable_update.spec.ts` (신규 생성)

**코드**:
```typescript
/**
 * E2E 테스트: 매출전표 저장 시 고객 미수금 UI 업데이트
 *
 * 작성일: 2025-12-07
 * 목적: 매출 저장 후 고객 정보 영역에서 미수금이 즉시 갱신되는지 검증
 */

import { test, expect } from '@playwright/test';

test.describe('매출전표 - 고객 미수금 자동 업데이트', () => {
  test.beforeEach(async ({ page }) => {
    // ERP 시스템 로그인 및 매출전표 창 열기
    await page.goto('http://localhost:3000/erp');
    await page.click('text=매출전표');
    await expect(page.locator('text=매출전표 입력')).toBeVisible();
  });

  test('매출 저장 시 고객 미수금이 자동으로 증가한다', async ({ page }) => {
    // Given: 고객 선택
    await page.click('button:has-text("거래처 선택")');
    await page.click('text=테스트고객1');

    // 초기 미수금 확인
    const initialReceivable = await page.locator('[data-testid="customer-receivable"]').textContent();
    const initialAmount = parseFloat(initialReceivable?.replace(/[^0-9]/g, '') || '0');

    // When: 상품 추가 및 저장
    await page.click('button:has-text("+ 추가")');
    await page.click('text=테스트상품');
    await page.fill('input[name="quantity"]', '1');
    await page.click('button:has-text("저장")');

    // Then: 저장 성공 메시지 확인
    await expect(page.locator('text=저장되었습니다')).toBeVisible();

    // Then: 미수금이 증가했는지 확인
    await page.click('button:has-text("확인")'); // alert 닫기
    const updatedReceivable = await page.locator('[data-testid="customer-receivable"]').textContent();
    const updatedAmount = parseFloat(updatedReceivable?.replace(/[^0-9]/g, '') || '0');

    expect(updatedAmount).toBeGreaterThan(initialAmount);
  });

  test('신용한도 초과 시 경고 메시지가 표시된다', async ({ page }) => {
    // Given: 신용한도에 가까운 고객 선택
    await page.click('button:has-text("거래처 선택")');
    await page.click('text=한도근접고객');

    // When: 고액 상품 추가 및 저장
    await page.click('button:has-text("+ 추가")');
    await page.click('text=고액상품');
    await page.click('button:has-text("저장")');

    // Then: 신용한도 초과 경고 표시
    await expect(page.locator('text=⚠️ 경고: 고객 신용한도를 초과했습니다')).toBeVisible();
  });
});
```

**실행 (성공 확인)**:
```bash
npx playwright test tests/e2e/test_sales_voucher_receivable_update.spec.ts
# 예상: PASSED (E2E 테스트 통과)
```

**Commit**:
```bash
git add tests/e2e/test_sales_voucher_receivable_update.spec.ts
git commit -m "test: Add E2E tests for receivable UI update"
```

---

### Task 9: 문서 업데이트 - CHANGELOG 및 README (2분)
**목표**: 신규 기능을 문서에 기록

**파일 1**: `CHANGELOG.md`

**추가 내용** (파일 상단에 추가):
```markdown
## [Unreleased] - 2025-12-07

### Added
- ✨ 매출전표 저장 시 고객 미수금 자동 업데이트 기능
  - POST /erp/sales 호출 시 고객의 receivable 필드 자동 증가
  - 신용한도 초과 시 경고 메시지 반환
  - 프론트엔드에서 미수금 즉시 갱신 및 표시
  - 트랜잭션 안전성 보장 (실패 시 롤백)

### Changed
- 🔧 ERPSale 응답 타입에 warning 필드 추가
- 🔧 SalesVoucherWindow에서 고객 미수금 실시간 업데이트

### Tests
- ✅ 단위 테스트: update_customer_receivable() 함수
- ✅ 통합 테스트: 매출 저장 + 미수금 업데이트
- ✅ E2E 테스트: UI에서 미수금 갱신 확인
```

**파일 2**: `README.md`

**추가 내용** (Features 섹션에 추가):
```markdown
### 🆕 신규 기능 (2025-12-07)

#### 고객 미수금 자동 관리
- **자동 업데이트**: 매출전표 저장 시 고객 미수금이 자동으로 증가합니다
- **신용한도 관리**: 신용한도 초과 시 경고 메시지가 표시됩니다
- **실시간 반영**: UI에서 미수금 변동사항을 즉시 확인할 수 있습니다
- **데이터 정합성**: 트랜잭션 안전성을 보장하여 데이터 불일치를 방지합니다
```

**Commit**:
```bash
git add CHANGELOG.md README.md
git commit -m "docs: Update CHANGELOG and README for receivable auto-update feature"
```

---

### Task 10: 최종 통합 테스트 실행 (2분)
**목표**: 모든 테스트가 통과하는지 최종 확인

**실행 명령어**:
```bash
# 1. 단위 테스트
pytest tests/unit/test_customer_receivable_update.py -v

# 2. 통합 테스트
pytest tests/integration/test_sale_receivable_integration.py -v

# 3. E2E 테스트
npx playwright test tests/e2e/test_sales_voucher_receivable_update.spec.ts

# 4. 전체 테스트 스위트
pytest tests/ -v
npm test
```

**예상 결과**:
```
✅ 단위 테스트: 5/5 passed
✅ 통합 테스트: 2/2 passed
✅ E2E 테스트: 2/2 passed
✅ 전체 테스트: ALL PASSED
```

**Commit**:
```bash
git add .
git commit -m "test: Verify all tests pass for receivable auto-update feature"
```

---

## 🎯 완료 체크리스트

- [ ] Task 1: SSOT 상수 정의
- [ ] Task 2: 백엔드 단위 테스트 작성 (TDD - red)
- [ ] Task 3: 백엔드 미수금 업데이트 함수 구현 (TDD - green)
- [ ] Task 4: 백엔드 통합 테스트 작성 (TDD - red)
- [ ] Task 5: create_sale()에 미수금 업데이트 통합 (TDD - green)
- [ ] Task 6: 프론트엔드 타입 정의 업데이트
- [ ] Task 7: 프론트엔드 UI 업데이트 (고객 미수금 갱신)
- [ ] Task 8: E2E 테스트 작성
- [ ] Task 9: 문서 업데이트 (CHANGELOG, README)
- [ ] Task 10: 최종 통합 테스트 실행

---

## 🚨 주의사항

### 목업 금지 (NO MOCKS)
- ❌ 가짜 데이터 생성 금지
- ❌ 시뮬레이션 금지
- ✅ 실제 JSON 파일 사용
- ✅ 실제 API 호출 테스트

### 빈 파일 금지 (NO EMPTY FILES)
- 모든 파일은 완전한 구현을 포함해야 함
- TODO 주석만 있는 파일 생성 금지
- Stub 함수 금지

### SSOT 준수 (Single Source of Truth)
- 모든 상수는 `src/kis_estimator_core/core/ssot/constants.py`에서만 정의
- 하드코딩된 값 금지
- Magic number 사용 금지

### 일관성 있는 코드 작성
- 기존 코드 스타일 준수 (Prettier, ESLint, Black)
- 네이밍 컨벤션 일치 (camelCase for TS, snake_case for Python)
- 파일 구조 유지

---

## 📊 예상 소요 시간

| Task | 예상 시간 | 실제 시간 |
|------|-----------|----------|
| Task 1 | 2분 | |
| Task 2 | 3분 | |
| Task 3 | 5분 | |
| Task 4 | 3분 | |
| Task 5 | 5분 | |
| Task 6 | 2분 | |
| Task 7 | 5분 | |
| Task 8 | 3분 | |
| Task 9 | 2분 | |
| Task 10 | 2분 | |
| **총계** | **32분** | |

---

## 🛠️ 스킬 사용 보고

**사용 스킬**: `writing-plans`
**사용 목적**: 고객 미수금 자동 업데이트 기능의 상세 개발계획 작성
**적용 과정**:
1. writing-plans 스킬 문서 로드
2. 2-5분 단위의 작은 태스크로 분할
3. TDD 워크플로우 적용 (test → fail → implement → pass → commit)
4. 정확한 파일 경로와 완전한 코드 포함
5. 목업 금지, 빈 파일 금지, SSOT 준수 원칙 반영

**결과**: 총 10개 태스크로 구성된 상세 개발계획서 완성 (예상 소요 시간: 32분)

---

*작성: 나베랄 감마*
*작성일: 2025-12-07*
*상태: 계획 완료, 실행 대기*
