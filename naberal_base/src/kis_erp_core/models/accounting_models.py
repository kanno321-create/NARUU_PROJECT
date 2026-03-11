"""
Accounting Models - 회계 모델 (계정과목, 분개장)
Contract-First + Zero-Mock + Double-Entry Bookkeeping (복식부기)

ERPNext 참조: General Ledger + Journal Entry 패턴
한국 중소제조업 계정과목 체계 적용
"""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


# ========== Enums ==========

class AccountType(str, Enum):
    """계정과목 유형 (5대 분류)"""
    ASSET = "asset"           # 자산
    LIABILITY = "liability"   # 부채
    EQUITY = "equity"         # 자본
    REVENUE = "revenue"       # 수익
    EXPENSE = "expense"       # 비용


class BalanceDirection(str, Enum):
    """잔액 방향"""
    DEBIT = "debit"    # 차변 (자산, 비용은 차변 증가)
    CREDIT = "credit"  # 대변 (부채, 자본, 수익은 대변 증가)


class JournalStatus(str, Enum):
    """분개 상태"""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


# ========== Account (계정과목) ==========

class AccountBase(BaseModel):
    """계정과목 기본"""
    account_code: str = Field(..., description="계정코드 (예: 1010)")
    account_name: str = Field(..., description="계정명 (예: 현금)")
    account_type: AccountType = Field(..., description="유형 (자산/부채/자본/수익/비용)")
    parent_id: Optional[str] = Field(None, description="상위 계정 ID (트리 구조)")
    is_group: bool = Field(default=False, description="그룹 계정 여부 (True=하위 계정 존재)")
    balance_direction: BalanceDirection = Field(..., description="잔액 방향 (차변/대변)")
    description: Optional[str] = Field(None, description="설명")
    is_active: bool = Field(default=True, description="사용 여부")


class AccountCreate(AccountBase):
    """계정과목 생성"""
    pass


class AccountUpdate(BaseModel):
    """계정과목 수정"""
    account_name: Optional[str] = None
    parent_id: Optional[str] = None
    is_group: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Account(AccountBase):
    """계정과목 응답"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountFilter(BaseModel):
    """계정과목 필터"""
    account_type: Optional[AccountType] = None
    is_group: Optional[bool] = None
    is_active: Optional[bool] = True
    parent_id: Optional[str] = None
    search: Optional[str] = None


# ========== JournalEntry (분개) ==========

class JournalItemCreate(BaseModel):
    """분개항목 생성"""
    account_id: str = Field(..., description="계정과목 ID")
    debit: float = Field(default=0.0, ge=0.0, description="차변 금액")
    credit: float = Field(default=0.0, ge=0.0, description="대변 금액")
    customer_id: Optional[str] = Field(None, description="거래처 ID (선택)")
    description: Optional[str] = Field(None, description="적요")


class JournalItem(BaseModel):
    """분개항목 응답"""
    id: str
    journal_entry_id: str
    account_id: str
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class JournalEntryCreate(BaseModel):
    """분개 생성 요청"""
    entry_date: date = Field(..., description="분개일자")
    narration: str = Field(..., description="적요/설명")
    voucher_id: Optional[str] = Field(None, description="연결 전표 ID")
    items: List[JournalItemCreate] = Field(..., min_length=2, description="분개항목 (최소 2개: 차변+대변)")


class JournalEntry(BaseModel):
    """분개 응답"""
    id: str
    entry_number: str
    entry_date: date
    narration: str
    voucher_id: Optional[str] = None
    status: JournalStatus = JournalStatus.DRAFT
    total_debit: float = 0.0
    total_credit: float = 0.0
    items: List[JournalItem] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JournalEntryFilter(BaseModel):
    """분개 필터"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_id: Optional[str] = None
    status: Optional[JournalStatus] = None
    voucher_id: Optional[str] = None
    search: Optional[str] = None


# ========== Report Models (보고서용) ==========

class AccountBalance(BaseModel):
    """계정과목별 잔액"""
    account_id: str
    account_code: str
    account_name: str
    account_type: AccountType
    debit_total: float = 0.0
    credit_total: float = 0.0
    balance: float = 0.0


class TrialBalance(BaseModel):
    """시산표 (Trial Balance)"""
    as_of_date: date
    accounts: List[AccountBalance] = []
    total_debit: float = 0.0
    total_credit: float = 0.0


class BalanceSheetSection(BaseModel):
    """대차대조표 섹션"""
    section_name: str
    accounts: List[AccountBalance] = []
    total: float = 0.0


class BalanceSheet(BaseModel):
    """대차대조표 (Balance Sheet)"""
    as_of_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: float = 0.0
    total_liabilities_equity: float = 0.0
    is_balanced: bool = True


class ProfitLossSection(BaseModel):
    """손익계산서 섹션"""
    section_name: str
    accounts: List[AccountBalance] = []
    total: float = 0.0


class ProfitLoss(BaseModel):
    """손익계산서 (Profit & Loss)"""
    start_date: date
    end_date: date
    revenue: ProfitLossSection
    expenses: ProfitLossSection
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0


class TaxSummaryItem(BaseModel):
    """세금 요약 항목"""
    voucher_type: str
    count: int = 0
    supply_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0


class TaxSummary(BaseModel):
    """세금 요약 (부가세 신고용)"""
    start_date: date
    end_date: date
    sales: TaxSummaryItem
    purchases: TaxSummaryItem
    net_tax: float = 0.0
