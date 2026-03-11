"""
ERP API Schemas (Pydantic)

거래처, 상품, 매출, 매입, 세금계산서, 견적서 등 ERP 관련 스키마
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================
# 공통 스키마
# ============================================

class BaseSchema(BaseModel):
    """기본 스키마"""
    class Config:
        from_attributes = True


class TimestampMixin(BaseModel):
    """타임스탬프 믹스인"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ============================================
# 거래처 (Customer) 스키마
# ============================================

class CustomerBase(BaseModel):
    """거래처 기본 스키마"""
    code: Optional[str] = None
    name: str
    customer_type: str = "매출처"  # 매출처, 매입처, 매출매입
    grade: str = "일반"  # VIP, 우수, 일반
    business_number: Optional[str] = None
    ceo_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Decimal = Decimal("0")
    current_receivable: Decimal = Decimal("0")  # 현재 미수금
    payment_terms: Optional[str] = None
    memo: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    """거래처 생성 스키마"""
    pass


class CustomerUpdate(BaseModel):
    """거래처 수정 스키마"""
    name: Optional[str] = None
    customer_type: Optional[str] = None
    grade: Optional[str] = None
    business_number: Optional[str] = None
    ceo_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class Customer(CustomerBase, TimestampMixin):
    """거래처 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))


# ============================================
# 상품 (Product) 스키마
# ============================================

class ProductBase(BaseModel):
    """상품 기본 스키마"""
    code: Optional[str] = None
    name: str
    spec: Optional[str] = None
    unit: str = "EA"
    category_id: Optional[str] = None
    purchase_price: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")
    safety_stock: int = 0
    memo: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    """상품 생성 스키마"""
    pass


class ProductUpdate(BaseModel):
    """상품 수정 스키마"""
    name: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    category_id: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    safety_stock: Optional[int] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class Product(ProductBase, TimestampMixin):
    """상품 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))


# ============================================
# 매출 (Sale) 스키마
# ============================================

class SaleItemBase(BaseModel):
    """매출 항목 기본 스키마"""
    product_id: Optional[str] = None
    product_code: Optional[str] = None
    product_name: str
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    cost_price: Decimal = Decimal("0")
    memo: Optional[str] = None


class SaleItemCreate(SaleItemBase):
    """매출 항목 생성 스키마"""
    pass


class SaleItem(SaleItemBase):
    """매출 항목 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    sale_id: Optional[str] = None
    sort_order: int = 0


class SaleBase(BaseModel):
    """매출 기본 스키마"""
    sale_number: Optional[str] = None
    sale_date: date
    customer_id: str
    status: str = "draft"  # draft, pending, confirmed, shipped, delivered, cancelled
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    cost_amount: Decimal = Decimal("0")
    profit_amount: Decimal = Decimal("0")
    memo: Optional[str] = None


class SaleCreate(BaseModel):
    """매출 생성 스키마"""
    sale_date: date
    customer_id: str
    status: str = "draft"
    memo: Optional[str] = None
    items: List[SaleItemCreate] = []


class SaleUpdate(BaseModel):
    """매출 수정 스키마"""
    sale_date: Optional[date] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
    memo: Optional[str] = None


class Sale(SaleBase, TimestampMixin):
    """매출 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    items: List[SaleItem] = []
    customer: Optional[Customer] = None


# ============================================
# 매입 (Purchase) 스키마
# ============================================

class PurchaseItemBase(BaseModel):
    """매입 항목 기본 스키마"""
    product_id: Optional[str] = None
    product_code: Optional[str] = None
    product_name: str
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    memo: Optional[str] = None


class PurchaseItemCreate(PurchaseItemBase):
    """매입 항목 생성 스키마"""
    pass


class PurchaseItem(PurchaseItemBase):
    """매입 항목 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    purchase_id: Optional[str] = None
    sort_order: int = 0


class PurchaseBase(BaseModel):
    """매입 기본 스키마"""
    purchase_number: Optional[str] = None
    purchase_date: date
    supplier_id: str
    status: str = "draft"
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    memo: Optional[str] = None


class PurchaseCreate(BaseModel):
    """매입 생성 스키마"""
    purchase_date: date
    supplier_id: str
    status: str = "draft"
    memo: Optional[str] = None
    items: List[PurchaseItemCreate] = []


class PurchaseUpdate(BaseModel):
    """매입 수정 스키마"""
    purchase_date: Optional[date] = None
    supplier_id: Optional[str] = None
    status: Optional[str] = None
    memo: Optional[str] = None


class Purchase(PurchaseBase, TimestampMixin):
    """매입 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    items: List[PurchaseItem] = []
    supplier: Optional[Customer] = None


# ============================================
# 세금계산서 (TaxInvoice) 스키마
# ============================================

class TaxInvoiceBase(BaseModel):
    """세금계산서 기본 스키마"""
    invoice_number: Optional[str] = None
    invoice_type: str = "매출"  # 매출, 매입
    issue_date: date
    customer_id: str
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    status: str = "draft"  # draft, issued, cancelled
    reference_type: Optional[str] = None  # sale, purchase
    reference_id: Optional[str] = None
    memo: Optional[str] = None


class TaxInvoiceCreate(TaxInvoiceBase):
    """세금계산서 생성 스키마"""
    pass


class TaxInvoiceUpdate(BaseModel):
    """세금계산서 수정 스키마"""
    issue_date: Optional[date] = None
    status: Optional[str] = None
    memo: Optional[str] = None


class TaxInvoice(TaxInvoiceBase, TimestampMixin):
    """세금계산서 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    customer: Optional[Customer] = None


# ============================================
# 견적서 (Quotation) 스키마
# ============================================

class QuotationItemBase(BaseModel):
    """견적 항목 기본 스키마"""
    product_id: Optional[str] = None
    product_code: Optional[str] = None
    product_name: str
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    memo: Optional[str] = None


class QuotationItemCreate(QuotationItemBase):
    """견적 항목 생성 스키마"""
    pass


class QuotationItem(QuotationItemBase):
    """견적 항목 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    quotation_id: Optional[str] = None
    sort_order: int = 0


class QuotationBase(BaseModel):
    """견적서 기본 스키마"""
    quotation_number: Optional[str] = None
    quotation_date: date
    valid_until: Optional[date] = None
    customer_id: str
    status: str = "draft"  # draft, sent, accepted, rejected, expired
    supply_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    memo: Optional[str] = None


class QuotationCreate(BaseModel):
    """견적서 생성 스키마"""
    quotation_date: date
    valid_until: Optional[date] = None
    customer_id: str
    status: str = "draft"
    memo: Optional[str] = None
    items: List[QuotationItemCreate] = []


class QuotationUpdate(BaseModel):
    """견적서 수정 스키마"""
    quotation_date: Optional[date] = None
    valid_until: Optional[date] = None
    status: Optional[str] = None
    memo: Optional[str] = None


class Quotation(QuotationBase, TimestampMixin):
    """견적서 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    items: List[QuotationItem] = []
    customer: Optional[Customer] = None


# ============================================
# 수금/지급 (Payment) 스키마
# ============================================

class PaymentBase(BaseModel):
    """수금/지급 기본 스키마"""
    payment_number: Optional[str] = None
    payment_type: str  # 수금, 지급
    payment_date: date
    customer_id: str
    amount: Decimal = Decimal("0")
    payment_method: str = "현금"  # 현금, 계좌이체, 어음, 카드
    status: str = "scheduled"  # scheduled, pending, completed, cancelled
    completed_date: Optional[date] = None
    reference_type: Optional[str] = None  # sale, purchase
    reference_id: Optional[str] = None
    memo: Optional[str] = None


class PaymentCreate(PaymentBase):
    """수금/지급 생성 스키마"""
    pass


class PaymentUpdate(BaseModel):
    """수금/지급 수정 스키마"""
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    status: Optional[str] = None
    completed_date: Optional[date] = None
    memo: Optional[str] = None


class Payment(PaymentBase, TimestampMixin):
    """수금/지급 응답 스키마"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    customer: Optional[Customer] = None


# ============================================
# 대시보드 (Dashboard) 스키마
# ============================================

class DashboardStats(BaseModel):
    """대시보드 통계 스키마"""
    monthly_sales: Decimal = Decimal("0")
    monthly_purchases: Decimal = Decimal("0")
    total_receivables: Decimal = Decimal("0")
    total_payables: Decimal = Decimal("0")
    sales_count: int = 0
    purchase_count: int = 0
    customer_count: int = 0
    product_count: int = 0


class SalesChartData(BaseModel):
    """매출 차트 데이터 스키마"""
    period: str
    amount: Decimal = Decimal("0")


# ============================================
# 목록 응답 스키마
# ============================================

class CustomerList(BaseModel):
    """거래처 목록 응답"""
    items: List[Customer]
    total: int


class ProductList(BaseModel):
    """상품 목록 응답"""
    items: List[Product]
    total: int


class SaleList(BaseModel):
    """매출 목록 응답"""
    items: List[Sale]
    total: int


class PurchaseList(BaseModel):
    """매입 목록 응답"""
    items: List[Purchase]
    total: int


class TaxInvoiceList(BaseModel):
    """세금계산서 목록 응답"""
    items: List[TaxInvoice]
    total: int


class QuotationList(BaseModel):
    """견적서 목록 응답"""
    items: List[Quotation]
    total: int


class PaymentList(BaseModel):
    """수금/지급 목록 응답"""
    items: List[Payment]
    total: int
