"""
Voucher Models - 전표 Pydantic 모델
DB 스키마 (erp_vouchers / erp_voucher_items) 완전 일치
Contract-First + Evidence-Gated + Zero-Mock
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


# ========== Enums ==========


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


# ========== VoucherItem Models ==========


class VoucherItemCreate(BaseModel):
    """전표 항목 생성 입력"""
    product_id: Optional[str] = Field(None, description="상품 ID")
    product_name: str = Field(..., description="상품명")
    spec: Optional[str] = Field(None, description="규격")
    unit: str = Field(default="EA", description="단위")
    quantity: float = Field(..., gt=0, description="수량")
    unit_price: float = Field(..., ge=0, description="단가")
    memo: Optional[str] = None


class VoucherItem(BaseModel):
    """전표 항목 응답 (DB 컬럼 일치)"""
    id: str
    voucher_id: str
    seq: int
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: float
    unit_price: float
    supply_price: float
    tax_amount: float
    total_amount: float
    memo: Optional[str] = None

    class Config:
        from_attributes = True


# ========== Voucher Models ==========


class VoucherCreate(BaseModel):
    """전표 생성 입력"""
    voucher_type: VoucherType = Field(..., description="전표 유형")
    voucher_date: date = Field(..., description="전표일자")
    customer_id: Optional[str] = Field(None, description="거래처 ID")
    employee_id: Optional[str] = Field(None, description="담당자 ID")
    payment_method: Optional[PaymentMethod] = Field(None, description="결제방법")
    bank_account_id: Optional[str] = Field(None, description="계좌 ID")
    memo: Optional[str] = None
    items: List[VoucherItemCreate] = Field(
        ..., min_length=1, description="전표 항목 (1개 이상)"
    )


class VoucherUpdate(BaseModel):
    """전표 수정 입력 (draft 상태만)"""
    voucher_date: Optional[date] = None
    customer_id: Optional[str] = None
    employee_id: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    bank_account_id: Optional[str] = None
    memo: Optional[str] = None
    items: Optional[List[VoucherItemCreate]] = None


class Voucher(BaseModel):
    """전표 응답 (DB 컬럼 일치)"""
    id: str
    voucher_no: str
    voucher_type: str
    voucher_date: date
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    supply_amount: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    paid_amount: float = 0
    unpaid_amount: float = 0
    payment_method: Optional[str] = None
    bank_account_id: Optional[str] = None
    status: str = "draft"
    memo: Optional[str] = None
    items: List[VoucherItem] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoucherFilter(BaseModel):
    """전표 필터"""
    voucher_type: Optional[VoucherType] = None
    status: Optional[VoucherStatus] = None
    customer_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
