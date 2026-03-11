"""
Report Models - 보고서 Pydantic 모델
일계표, 월별현황, 거래처잔액, 손익계산서, 대차대조표 등
Contract-First + Evidence-Gated + Zero-Mock
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== 일계표 / 월별현황 ==========


class DailySummary(BaseModel):
    """일계표 (일별 매출/매입/수금/지급/경비)"""
    summary_date: date = Field(..., description="일자")
    sales_amount: float = Field(default=0.0, description="매출")
    purchase_amount: float = Field(default=0.0, description="매입")
    receipt_amount: float = Field(default=0.0, description="수금")
    payment_amount: float = Field(default=0.0, description="지급")
    expense_amount: float = Field(default=0.0, description="경비")
    voucher_count: int = Field(default=0, description="전표 수")


class MonthlySummary(BaseModel):
    """월별 현황"""
    year: int = Field(..., description="연도")
    month: int = Field(..., description="월")
    sales_amount: float = Field(default=0.0, description="매출")
    purchase_amount: float = Field(default=0.0, description="매입")
    receipt_amount: float = Field(default=0.0, description="수금")
    payment_amount: float = Field(default=0.0, description="지급")
    expense_amount: float = Field(default=0.0, description="경비")
    gross_profit: float = Field(default=0.0, description="매출총이익")
    net_profit: float = Field(default=0.0, description="순이익")


# ========== 거래처별 현황 ==========


class CustomerBalance(BaseModel):
    """거래처별 잔액 현황"""
    customer_id: str
    customer_name: str
    total_sales: float = 0.0
    total_purchase: float = 0.0
    total_receipt: float = 0.0
    total_payment: float = 0.0
    receivable: float = 0.0
    payable: float = 0.0


class CustomerTransaction(BaseModel):
    """거래처별 거래 내역 (단건)"""
    voucher_id: str
    voucher_no: str
    voucher_type: str
    voucher_date: date
    total_amount: float
    paid_amount: float
    unpaid_amount: float
    memo: Optional[str] = None


class CustomerTransactionReport(BaseModel):
    """거래처별 거래 내역 보고서"""
    customer_id: str
    customer_name: Optional[str] = None
    transactions: List[CustomerTransaction] = []
    summary: dict = {}


# ========== 미수금 / 미지급금 ==========


class ReceivableDetail(BaseModel):
    """미수금 상세"""
    voucher_id: str
    voucher_no: str
    voucher_date: date
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float
    paid_amount: float
    unpaid_amount: float
    days_overdue: int = 0


class ReceivableReport(BaseModel):
    """미수금 현황 보고서"""
    total_receivable: float = 0.0
    overdue_amount: float = 0.0
    details: List[ReceivableDetail] = []


class PayableDetail(BaseModel):
    """미지급금 상세"""
    voucher_id: str
    voucher_no: str
    voucher_date: date
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float
    paid_amount: float
    unpaid_amount: float
    days_overdue: int = 0


class PayableReport(BaseModel):
    """미지급금 현황 보고서"""
    total_payable: float = 0.0
    overdue_amount: float = 0.0
    details: List[PayableDetail] = []


# ========== 상품별 현황 ==========


class ProductSalesItem(BaseModel):
    """상품별 매출 항목"""
    product_name: str
    total_quantity: float = 0.0
    total_supply: float = 0.0
    total_tax: float = 0.0
    total_amount: float = 0.0


class ProductSalesReport(BaseModel):
    """상품별 매출 보고서"""
    period_start: date
    period_end: date
    products: List[ProductSalesItem] = []
    total_sales: float = 0.0
    total_quantity: float = 0.0


class ProductPurchaseReport(BaseModel):
    """상품별 매입 보고서"""
    period_start: date
    period_end: date
    products: List[ProductSalesItem] = []
    total_purchase: float = 0.0
    total_quantity: float = 0.0


# ========== 매출/매입 명세서 ==========


class VoucherSummaryItem(BaseModel):
    """명세서 전표 요약"""
    voucher_id: str
    voucher_no: str
    voucher_date: date
    customer_name: Optional[str] = None
    supply_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0


class StatementReport(BaseModel):
    """매출/매입 명세서"""
    period_start: date
    period_end: date
    vouchers: List[VoucherSummaryItem] = []
    total_supply: float = 0.0
    total_tax: float = 0.0
    total_amount: float = 0.0


# ========== 손익계산서 ==========


class ProfitLossReport(BaseModel):
    """손익계산서"""
    period_start: date
    period_end: date
    sales: float = 0.0
    cost_of_sales: float = 0.0
    gross_profit: float = 0.0
    expenses: float = 0.0
    net_profit: float = 0.0
    profit_margin: float = 0.0


# ========== 대차대조표 ==========


class BalanceSheetSection(BaseModel):
    """대차대조표 섹션 (자산/부채/자본)"""
    account_code: str
    account_name: str
    balance: float = 0.0


class BalanceSheetReport(BaseModel):
    """대차대조표"""
    as_of_date: date
    assets: List[BalanceSheetSection] = []
    liabilities: List[BalanceSheetSection] = []
    equity: List[BalanceSheetSection] = []
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    is_balanced: bool = False


# ========== 세금 요약 ==========


class TaxSummaryReport(BaseModel):
    """부가세 요약 (분기별 신고용)"""
    period_start: date
    period_end: date
    sales_supply: float = 0.0
    sales_tax: float = 0.0
    purchase_supply: float = 0.0
    purchase_tax: float = 0.0
    tax_payable: float = 0.0
    sales_count: int = 0
    purchase_count: int = 0


# ========== 경비 항목별 ==========


class ExpenseCategory(BaseModel):
    """경비 항목"""
    product_name: str
    total_amount: float = 0.0
    count: int = 0


class ExpenseBreakdownReport(BaseModel):
    """경비 항목별 보고서"""
    period_start: date
    period_end: date
    categories: List[ExpenseCategory] = []
    total: float = 0.0
