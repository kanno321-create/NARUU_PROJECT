"""
회계 모델 단위 테스트 - Pydantic 모델 검증
DB 불필요, 순수 모델 레이어 검증

테스트 범위:
- Enum 값 검증 (AccountType, BalanceDirection, JournalStatus)
- AccountCreate/Update 모델 필드 검증
- JournalEntryCreate 최소 항목 수 검증
- JournalItemCreate debit/credit 범위 검증
- 보고서 모델 구조 검증
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from kis_erp_core.models.accounting_models import (
    AccountType,
    BalanceDirection,
    JournalStatus,
    AccountCreate,
    AccountUpdate,
    Account,
    AccountFilter,
    JournalItemCreate,
    JournalEntryCreate,
    JournalEntry,
    JournalItem,
    AccountBalance,
    TrialBalance,
    BalanceSheet,
    BalanceSheetSection,
    ProfitLoss,
    ProfitLossSection,
)


# ========== Enum Tests ==========


class TestAccountType:
    """AccountType enum 검증"""

    def test_all_five_types(self):
        """5대 계정유형 존재 확인"""
        assert AccountType.ASSET == "asset"
        assert AccountType.LIABILITY == "liability"
        assert AccountType.EQUITY == "equity"
        assert AccountType.REVENUE == "revenue"
        assert AccountType.EXPENSE == "expense"
        assert len(AccountType) == 5

    def test_invalid_type_rejected(self):
        """유효하지 않은 계정유형 거부"""
        with pytest.raises(ValueError):
            AccountType("invalid")


class TestBalanceDirection:
    """BalanceDirection enum 검증"""

    def test_debit_credit(self):
        """차변/대변 방향 확인"""
        assert BalanceDirection.DEBIT == "debit"
        assert BalanceDirection.CREDIT == "credit"
        assert len(BalanceDirection) == 2


class TestJournalStatus:
    """JournalStatus enum 검증"""

    def test_three_statuses(self):
        """3가지 상태 확인"""
        assert JournalStatus.DRAFT == "draft"
        assert JournalStatus.POSTED == "posted"
        assert JournalStatus.CANCELLED == "cancelled"
        assert len(JournalStatus) == 3


# ========== Account Model Tests ==========


class TestAccountCreate:
    """AccountCreate 모델 검증"""

    def test_valid_account(self):
        """정상 계정과목 생성"""
        account = AccountCreate(
            account_code="1010",
            account_name="현금",
            account_type=AccountType.ASSET,
            balance_direction=BalanceDirection.DEBIT,
        )
        assert account.account_code == "1010"
        assert account.account_name == "현금"
        assert account.account_type == AccountType.ASSET
        assert account.balance_direction == BalanceDirection.DEBIT
        assert account.is_group is False
        assert account.is_active is True
        assert account.parent_id is None

    def test_missing_required_fields(self):
        """필수 필드 누락 시 에러"""
        with pytest.raises(ValidationError):
            AccountCreate(
                account_code="1010",
                # account_name 누락
                account_type=AccountType.ASSET,
                balance_direction=BalanceDirection.DEBIT,
            )

    def test_group_account(self):
        """그룹 계정 생성"""
        account = AccountCreate(
            account_code="1000",
            account_name="자산",
            account_type=AccountType.ASSET,
            balance_direction=BalanceDirection.DEBIT,
            is_group=True,
            description="자산 총계",
        )
        assert account.is_group is True
        assert account.description == "자산 총계"

    def test_with_parent_id(self):
        """상위 계정 지정"""
        account = AccountCreate(
            account_code="1010",
            account_name="현금",
            account_type=AccountType.ASSET,
            balance_direction=BalanceDirection.DEBIT,
            parent_id="some-parent-uuid",
        )
        assert account.parent_id == "some-parent-uuid"


class TestAccountUpdate:
    """AccountUpdate 모델 검증"""

    def test_partial_update(self):
        """부분 업데이트 가능"""
        update = AccountUpdate(account_name="수정된 계정명")
        assert update.account_name == "수정된 계정명"
        assert update.parent_id is None
        assert update.is_group is None
        assert update.description is None
        assert update.is_active is None

    def test_empty_update(self):
        """빈 업데이트 허용"""
        update = AccountUpdate()
        assert update.account_name is None


class TestAccountFilter:
    """AccountFilter 모델 검증"""

    def test_default_filter(self):
        """기본 필터 값"""
        f = AccountFilter()
        assert f.account_type is None
        assert f.is_group is None
        assert f.is_active is True
        assert f.parent_id is None
        assert f.search is None

    def test_asset_filter(self):
        """자산 유형 필터"""
        f = AccountFilter(account_type=AccountType.ASSET, is_group=False)
        assert f.account_type == AccountType.ASSET
        assert f.is_group is False


# ========== Journal Model Tests ==========


class TestJournalItemCreate:
    """JournalItemCreate 모델 검증"""

    def test_valid_debit_item(self):
        """정상 차변 항목"""
        item = JournalItemCreate(
            account_id="acc-uuid-1",
            debit=100000.0,
            credit=0.0,
            description="현금 증가",
        )
        assert item.debit == 100000.0
        assert item.credit == 0.0

    def test_valid_credit_item(self):
        """정상 대변 항목"""
        item = JournalItemCreate(
            account_id="acc-uuid-2",
            debit=0.0,
            credit=100000.0,
            description="매출 증가",
        )
        assert item.debit == 0.0
        assert item.credit == 100000.0

    def test_negative_debit_rejected(self):
        """음수 차변 거부"""
        with pytest.raises(ValidationError):
            JournalItemCreate(
                account_id="acc-uuid-1",
                debit=-100.0,
                credit=0.0,
            )

    def test_negative_credit_rejected(self):
        """음수 대변 거부"""
        with pytest.raises(ValidationError):
            JournalItemCreate(
                account_id="acc-uuid-1",
                debit=0.0,
                credit=-100.0,
            )

    def test_optional_fields(self):
        """선택 필드 기본값"""
        item = JournalItemCreate(
            account_id="acc-uuid-1",
            debit=5000.0,
        )
        assert item.credit == 0.0
        assert item.customer_id is None
        assert item.description is None


class TestJournalEntryCreate:
    """JournalEntryCreate 모델 검증"""

    def test_valid_entry(self):
        """정상 분개 생성"""
        entry = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="상품 매출",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0, credit=0.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=100000.0),
            ],
        )
        assert entry.entry_date == date(2026, 2, 8)
        assert entry.narration == "상품 매출"
        assert len(entry.items) == 2

    def test_minimum_two_items_required(self):
        """최소 2개 항목 검증 (Pydantic min_length=2)"""
        with pytest.raises(ValidationError) as exc_info:
            JournalEntryCreate(
                entry_date=date(2026, 2, 8),
                narration="항목 1개만",
                items=[
                    JournalItemCreate(account_id="acc-1", debit=100.0, credit=0.0),
                ],
            )
        assert "items" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_empty_items_rejected(self):
        """빈 항목 리스트 거부"""
        with pytest.raises(ValidationError):
            JournalEntryCreate(
                entry_date=date(2026, 2, 8),
                narration="항목 없음",
                items=[],
            )

    def test_optional_voucher_id(self):
        """전표 ID 선택적"""
        entry = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="일반 분개",
            voucher_id="voucher-uuid-1",
            items=[
                JournalItemCreate(account_id="acc-1", debit=50000.0),
                JournalItemCreate(account_id="acc-2", credit=50000.0),
            ],
        )
        assert entry.voucher_id == "voucher-uuid-1"

    def test_three_way_entry(self):
        """3항목 분개 (1:2 분배)"""
        entry = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="급여 지급",
            items=[
                JournalItemCreate(account_id="acc-salary", debit=3000000.0),
                JournalItemCreate(account_id="acc-withholding", credit=300000.0),
                JournalItemCreate(account_id="acc-cash", credit=2700000.0),
            ],
        )
        assert len(entry.items) == 3


# ========== Report Model Tests ==========


class TestTrialBalance:
    """시산표 모델 검증"""

    def test_empty_trial_balance(self):
        """빈 시산표"""
        tb = TrialBalance(as_of_date=date(2026, 2, 8))
        assert tb.as_of_date == date(2026, 2, 8)
        assert tb.accounts == []
        assert tb.total_debit == 0.0
        assert tb.total_credit == 0.0

    def test_trial_balance_with_accounts(self):
        """계정 포함 시산표"""
        tb = TrialBalance(
            as_of_date=date(2026, 2, 8),
            accounts=[
                AccountBalance(
                    account_id="1",
                    account_code="1010",
                    account_name="현금",
                    account_type=AccountType.ASSET,
                    debit_total=1000000.0,
                    credit_total=200000.0,
                    balance=800000.0,
                ),
            ],
            total_debit=1000000.0,
            total_credit=200000.0,
        )
        assert len(tb.accounts) == 1
        assert tb.total_debit == 1000000.0


class TestBalanceSheet:
    """대차대조표 모델 검증"""

    def test_balanced_sheet(self):
        """균형 대차대조표"""
        bs = BalanceSheet(
            as_of_date=date(2026, 2, 8),
            assets=BalanceSheetSection(section_name="자산", total=1000000.0),
            liabilities=BalanceSheetSection(section_name="부채", total=400000.0),
            equity=BalanceSheetSection(section_name="자본", total=600000.0),
            total_assets=1000000.0,
            total_liabilities_equity=1000000.0,
            is_balanced=True,
        )
        assert bs.is_balanced is True
        assert bs.total_assets == bs.total_liabilities_equity


class TestProfitLoss:
    """손익계산서 모델 검증"""

    def test_profit_scenario(self):
        """이익 시나리오"""
        pl = ProfitLoss(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 8),
            revenue=ProfitLossSection(section_name="수익", total=5000000.0),
            expenses=ProfitLossSection(section_name="비용", total=3000000.0),
            total_revenue=5000000.0,
            total_expenses=3000000.0,
            net_profit=2000000.0,
        )
        assert pl.net_profit == 2000000.0
        assert pl.net_profit == pl.total_revenue - pl.total_expenses

    def test_loss_scenario(self):
        """손실 시나리오"""
        pl = ProfitLoss(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 8),
            revenue=ProfitLossSection(section_name="수익", total=1000000.0),
            expenses=ProfitLossSection(section_name="비용", total=3000000.0),
            total_revenue=1000000.0,
            total_expenses=3000000.0,
            net_profit=-2000000.0,
        )
        assert pl.net_profit < 0
