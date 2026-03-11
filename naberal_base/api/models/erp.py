"""
ERP Pydantic Models
Contract-First + Zero-Mock
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


# ========== Enums ==========

class CustomerType(str, Enum):
    """거래처 유형"""
    BUYER = "매출"
    SUPPLIER = "매입"
    BOTH = "겸용"


class ProductCategory(str, Enum):
    """상품 카테고리"""
    BREAKER = "차단기"
    ENCLOSURE = "외함"
    ACCESSORY = "부속자재"
    OTHER = "기타"


class EmployeeStatus(str, Enum):
    """사원 상태"""
    ACTIVE = "active"
    RESIGNED = "resigned"
    ON_LEAVE = "on_leave"


class VoucherType(str, Enum):
    """전표 유형"""
    SALES = "sales"
    PURCHASE = "purchase"
    RECEIPT = "receipt"
    PAYMENT = "payment"
    EXPENSE = "expense"


class VoucherStatus(str, Enum):
    """전표 상태"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """결제 수단"""
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    NOTE = "note"


class OrderStatus(str, Enum):
    """발주 상태"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class StatementStatus(str, Enum):
    """거래명세서 상태"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"


# ========== Company (자사정보) ==========

class CompanyInfo(BaseModel):
    """자사정보"""
    id: Optional[str] = None
    business_number: str = Field(..., description="사업자등록번호")
    name: str = Field(..., description="상호명")
    ceo: str = Field(..., description="대표자명")
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    bank_info: Optional[dict] = None
    business_type: Optional[str] = None
    business_item: Optional[str] = None
    logo_path: Optional[str] = None
    stamp_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Customer (거래처) ==========

class Customer(BaseModel):
    """거래처"""
    id: Optional[str] = None
    code: Optional[str] = None
    name: str = Field(..., description="거래처명")
    type: CustomerType = Field(..., description="거래처 유형")
    business_number: Optional[str] = None
    ceo: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    balance: Optional[float] = 0.0
    credit_limit: Optional[float] = None
    payment_terms: Optional[str] = None
    bank_info: Optional[dict] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Product (상품) ==========

class Product(BaseModel):
    """상품"""
    id: Optional[str] = None
    code: Optional[str] = None
    name: str = Field(..., description="상품명")
    category: Optional[ProductCategory] = None
    unit: str = Field(default="EA", description="단위")
    unit_cost: Optional[float] = 0.0
    sale_price: Optional[float] = 0.0
    stock_qty: Optional[float] = 0.0
    spec: Optional[str] = None
    manufacturer: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Employee (사원) ==========

class Employee(BaseModel):
    """사원"""
    id: Optional[str] = None
    emp_no: Optional[str] = None
    name: str = Field(..., description="사원명")
    department: Optional[str] = None
    position: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, description="상태")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== BankAccount (은행계좌) ==========

class BankAccount(BaseModel):
    """은행계좌"""
    id: Optional[str] = None
    account_no: str = Field(..., description="계좌번호")
    bank_name: str = Field(..., description="은행명")
    account_name: Optional[str] = Field(None, description="계좌명")
    holder_name: Optional[str] = Field(None, description="예금주")
    balance: float = Field(default=0, description="잔액")
    is_active: bool = Field(default=True, description="활성여부")
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Voucher (전표) ==========

class VoucherItem(BaseModel):
    """전표 상세"""
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    qty: float
    unit_price: float
    amount: float
    memo: Optional[str] = None


class Voucher(BaseModel):
    """전표"""
    id: Optional[str] = None
    voucher_no: Optional[str] = None
    type: VoucherType = Field(..., description="전표 유형")
    date: datetime = Field(..., description="전표 일자")
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float = Field(default=0.0, description="합계금액")
    vat_amount: float = Field(default=0.0, description="부가세")
    status: VoucherStatus = Field(default=VoucherStatus.DRAFT, description="상태")
    items: Optional[List[VoucherItem]] = []
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Order (발주) ==========

class OrderItem(BaseModel):
    """발주 상세"""
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    qty: float
    unit_price: float
    amount: float


class Order(BaseModel):
    """발주"""
    id: Optional[str] = None
    order_no: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    order_date: datetime = Field(..., description="발주일자")
    delivery_date: Optional[datetime] = None
    total_amount: float = Field(default=0.0, description="합계금액")
    status: OrderStatus = Field(default=OrderStatus.DRAFT, description="상태")
    items: Optional[List[OrderItem]] = []
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Statement (거래명세서) ==========

class Statement(BaseModel):
    """거래명세서"""
    id: Optional[str] = None
    statement_no: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    statement_date: datetime = Field(..., description="거래명세서 일자")
    total_amount: float = Field(default=0.0, description="합계금액")
    vat_amount: float = Field(default=0.0, description="부가세")
    status: StatementStatus = Field(default=StatementStatus.DRAFT, description="상태")
    voucher_ids: Optional[List[str]] = []
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Reports (보고서 모델) ==========

class DailySummary(BaseModel):
    """일계표"""
    date: datetime = Field(..., description="일자")
    sales_amount: float = Field(default=0.0, description="매출")
    purchase_amount: float = Field(default=0.0, description="매입")
    receipt_amount: float = Field(default=0.0, description="수금")
    payment_amount: float = Field(default=0.0, description="지급")
    expense_amount: float = Field(default=0.0, description="경비")

    class Config:
        from_attributes = True


class MonthlySummary(BaseModel):
    """월별 현황"""
    year: int = Field(..., description="연도")
    month: int = Field(..., description="월")
    sales_amount: float = Field(default=0.0, description="매출")
    purchase_amount: float = Field(default=0.0, description="매입")
    gross_profit: float = Field(default=0.0, description="매출총이익")
    expense_amount: float = Field(default=0.0, description="경비")
    net_profit: float = Field(default=0.0, description="순이익")

    class Config:
        from_attributes = True


class CustomerBalance(BaseModel):
    """거래처별 잔액 현황"""
    customer_id: str = Field(..., description="거래처 ID")
    customer_name: str = Field(..., description="거래처명")
    customer_type: str = Field(..., description="거래처 유형")
    receivable_amount: float = Field(default=0.0, description="미수금")
    payable_amount: float = Field(default=0.0, description="미지급금")
    balance: float = Field(default=0.0, description="잔액")

    class Config:
        from_attributes = True


# ========== Carryover (기초이월) ==========

class StockCarryover(BaseModel):
    """상품재고 이월"""
    id: Optional[str] = None
    fiscal_year: int = Field(..., description="회계연도")
    product_id: str = Field(..., description="상품 ID")
    product_name: Optional[str] = None
    qty: float = Field(..., description="이월 수량")
    unit_cost: float = Field(..., description="원가")
    total_value: float = Field(..., description="이월 금액")
    carryover_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BalanceCarryover(BaseModel):
    """미수금/미지급금 이월"""
    id: Optional[str] = None
    fiscal_year: int = Field(..., description="회계연도")
    customer_id: str = Field(..., description="거래처 ID")
    customer_name: Optional[str] = None
    balance_type: str = Field(..., description="잔액 유형 (receivable/payable)")
    amount: float = Field(..., description="이월 금액")
    carryover_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CashCarryover(BaseModel):
    """현금/예금 잔고 이월"""
    id: Optional[str] = None
    fiscal_year: int = Field(..., description="회계연도")
    account_id: Optional[str] = Field(None, description="계좌 ID (None=현금)")
    account_name: Optional[str] = None
    amount: float = Field(..., description="이월 금액")
    carryover_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== CreditCard (신용카드) ==========

class CreditCard(BaseModel):
    """신용카드"""
    id: Optional[str] = None
    card_number: str = Field(..., description="카드번호 (마스킹)")
    card_name: Optional[str] = Field(None, description="카드명")
    card_company: Optional[str] = Field(None, description="카드사")
    holder_name: Optional[str] = Field(None, description="명의자")
    expire_date: Optional[str] = Field(None, description="유효기간 (MM/YY)")
    is_active: bool = Field(default=True, description="사용 여부")
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
