"""
복식부기 핵심 로직 테스트 - JournalService 비즈니스 로직 검증
DB 없이 서비스 레이어 단위 테스트 (repository는 AsyncMock)

테스트 범위:
- 대차평균 검증 (차변합계 == 대변합계)
- 대차불일치 에러 검증
- 최소 항목 수 (2개) 검증
- debit/credit 동시 양수 거부
- debit/credit 동시 0 거부
- 존재하지 않는 계정 ID 거부
- draft -> posted 상태 전이
- posted -> cancelled 상태 전이 + 역분개
- 잘못된 상태 전이 거부
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

from kis_erp_core.services.journal_service import JournalService
from kis_erp_core.models.accounting_models import (
    JournalEntryCreate,
    JournalItemCreate,
)


@pytest.fixture
def journal_service():
    """JournalService with mocked repositories"""
    service = JournalService()
    service.journal_repo = AsyncMock()
    service.account_repo = AsyncMock()
    return service


@pytest.fixture
def mock_session():
    """Mock AsyncSession"""
    return AsyncMock()


# ========== 대차평균 검증 ==========


class TestDoubleEntryBalance:
    """복식부기 대차평균 원리 테스트"""

    @pytest.mark.asyncio
    async def test_balanced_entry_succeeds(self, journal_service, mock_session):
        """차변합계 == 대변합계: 정상 생성"""
        # account_repo.get() returns valid account for every account_id
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1", "account_code": "1010", "account_name": "현금"}
        )
        journal_service.journal_repo.create_entry = AsyncMock(
            return_value={
                "id": "je-1",
                "entry_number": "JE-20260208-0001",
                "entry_date": date(2026, 2, 8),
                "narration": "상품 매출",
                "status": "draft",
                "total_debit": 100000.0,
                "total_credit": 100000.0,
                "items": [],
            }
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="상품 매출",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0, credit=0.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=100000.0),
            ],
        )

        result = await journal_service.create_journal_entry(mock_session, data)
        assert result["status"] == "draft"
        assert result["total_debit"] == 100000.0
        journal_service.journal_repo.create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_unbalanced_entry_rejected(self, journal_service, mock_session):
        """차변합계 != 대변합계: 대차불일치 에러"""
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1", "account_code": "1010"}
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="불균형 분개",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0, credit=0.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=50000.0),
            ],
        )

        with pytest.raises(ValueError, match="대차평균 불일치"):
            await journal_service.create_journal_entry(mock_session, data)

    @pytest.mark.asyncio
    async def test_small_rounding_difference_rejected(self, journal_service, mock_session):
        """미세한 차이(0.02원)도 거부 (허용오차 0.01)"""
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1"}
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="미세 불일치",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.02, credit=0.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=100000.0),
            ],
        )

        with pytest.raises(ValueError, match="대차평균 불일치"):
            await journal_service.create_journal_entry(mock_session, data)

    @pytest.mark.asyncio
    async def test_multi_item_balanced_entry(self, journal_service, mock_session):
        """3개 이상 항목 분개: 합계만 맞으면 통과"""
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1"}
        )
        journal_service.journal_repo.create_entry = AsyncMock(
            return_value={
                "id": "je-2",
                "entry_number": "JE-20260208-0002",
                "entry_date": date(2026, 2, 8),
                "narration": "급여 분배",
                "status": "draft",
                "total_debit": 3000000.0,
                "total_credit": 3000000.0,
                "items": [],
            }
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="급여 분배",
            items=[
                JournalItemCreate(account_id="acc-salary", debit=3000000.0),
                JournalItemCreate(account_id="acc-tax", credit=300000.0),
                JournalItemCreate(account_id="acc-insurance", credit=200000.0),
                JournalItemCreate(account_id="acc-cash", credit=2500000.0),
            ],
        )

        result = await journal_service.create_journal_entry(mock_session, data)
        assert result["total_debit"] == 3000000.0


# ========== 항목 유효성 검증 ==========


class TestItemValidation:
    """분개 항목 유효성 검증"""

    @pytest.mark.asyncio
    async def test_both_debit_credit_positive_rejected(self, journal_service, mock_session):
        """debit과 credit 동시 양수 거부"""
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1"}
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="잘못된 항목",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0, credit=50000.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=50000.0),
            ],
        )

        with pytest.raises(ValueError, match="동시에 양수"):
            await journal_service.create_journal_entry(mock_session, data)

    @pytest.mark.asyncio
    async def test_both_debit_credit_zero_rejected(self, journal_service, mock_session):
        """debit과 credit 동시 0 거부"""
        journal_service.account_repo.get = AsyncMock(
            return_value={"id": "acc-1"}
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="빈 항목",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0, credit=0.0),
                JournalItemCreate(account_id="acc-2", debit=0.0, credit=100000.0),
                JournalItemCreate(account_id="acc-3", debit=0.0, credit=0.0),
            ],
        )

        with pytest.raises(ValueError, match="0보다 커야"):
            await journal_service.create_journal_entry(mock_session, data)

    @pytest.mark.asyncio
    async def test_nonexistent_account_rejected(self, journal_service, mock_session):
        """존재하지 않는 계정 ID 거부"""
        # 첫 번째 계정은 OK, 두 번째는 존재하지 않음
        journal_service.account_repo.get = AsyncMock(
            side_effect=[
                {"id": "acc-1", "account_code": "1010"},
                None,  # account not found
            ]
        )

        data = JournalEntryCreate(
            entry_date=date(2026, 2, 8),
            narration="없는 계정",
            items=[
                JournalItemCreate(account_id="acc-1", debit=100000.0),
                JournalItemCreate(account_id="nonexistent", credit=100000.0),
            ],
        )

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            await journal_service.create_journal_entry(mock_session, data)


# ========== 상태 전이 (State Machine) ==========


class TestStateTransition:
    """분개 상태 전이 테스트"""

    @pytest.mark.asyncio
    async def test_draft_to_posted(self, journal_service, mock_session):
        """draft -> posted 전기 성공"""
        journal_service.journal_repo.get = AsyncMock(
            return_value={
                "id": "je-1",
                "status": "draft",
                "entry_date": date(2026, 2, 8),
                "narration": "테스트",
                "items": [],
            }
        )
        journal_service.journal_repo.update_status = AsyncMock(
            return_value={
                "id": "je-1",
                "status": "posted",
                "entry_date": date(2026, 2, 8),
                "narration": "테스트",
            }
        )

        result = await journal_service.post_entry(mock_session, "je-1")
        assert result["status"] == "posted"
        journal_service.journal_repo.update_status.assert_called_with(
            mock_session, "je-1", "posted"
        )

    @pytest.mark.asyncio
    async def test_posted_cannot_be_posted_again(self, journal_service, mock_session):
        """이미 posted된 분개 재전기 불가"""
        journal_service.journal_repo.get = AsyncMock(
            return_value={"id": "je-1", "status": "posted", "items": []}
        )

        with pytest.raises(ValueError, match="draft만 전기 가능"):
            await journal_service.post_entry(mock_session, "je-1")

    @pytest.mark.asyncio
    async def test_cancelled_cannot_be_posted(self, journal_service, mock_session):
        """cancelled 분개 전기 불가"""
        journal_service.journal_repo.get = AsyncMock(
            return_value={"id": "je-1", "status": "cancelled", "items": []}
        )

        with pytest.raises(ValueError, match="draft만 전기 가능"):
            await journal_service.post_entry(mock_session, "je-1")

    @pytest.mark.asyncio
    async def test_post_nonexistent_entry_returns_none(self, journal_service, mock_session):
        """존재하지 않는 분개 전기 시 None 반환"""
        journal_service.journal_repo.get = AsyncMock(return_value=None)

        result = await journal_service.post_entry(mock_session, "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_draft_cannot_be_cancelled(self, journal_service, mock_session):
        """draft 분개는 취소 불가 (posted만 가능)"""
        journal_service.journal_repo.get = AsyncMock(
            return_value={"id": "je-1", "status": "draft", "items": []}
        )

        with pytest.raises(ValueError, match="posted만 취소 가능"):
            await journal_service.cancel_entry(mock_session, "je-1")


# ========== 역분개 (Reverse Entry) ==========


class TestReverseEntry:
    """분개 취소 + 역분개 생성 테스트"""

    @pytest.mark.asyncio
    async def test_cancel_creates_reverse_entry(self, journal_service, mock_session):
        """posted 분개 취소 시 역분개 생성"""
        original_entry = {
            "id": "je-1",
            "status": "posted",
            "entry_date": date(2026, 2, 8),
            "narration": "상품 매출",
            "voucher_id": None,
            "items": [
                {
                    "account_id": "acc-cash",
                    "debit": 100000.0,
                    "credit": 0.0,
                    "customer_id": None,
                    "description": "현금 수령",
                },
                {
                    "account_id": "acc-revenue",
                    "debit": 0.0,
                    "credit": 100000.0,
                    "customer_id": None,
                    "description": "매출 인식",
                },
            ],
        }

        journal_service.journal_repo.get = AsyncMock(return_value=original_entry)
        journal_service.journal_repo.update_status = AsyncMock(return_value=None)
        journal_service.journal_repo.create_entry = AsyncMock(
            return_value={
                "id": "je-reverse",
                "entry_number": "JE-20260208-0002",
                "entry_date": date(2026, 2, 8),
                "narration": "[역분개] 상품 매출",
                "status": "draft",
                "total_debit": 100000.0,
                "total_credit": 100000.0,
                "items": [],
            }
        )

        result = await journal_service.cancel_entry(mock_session, "je-1")

        # 원래 분개 cancelled로 변경 호출 확인
        journal_service.journal_repo.update_status.assert_any_call(
            mock_session, "je-1", "cancelled"
        )

        # 역분개 생성 호출 확인
        create_call = journal_service.journal_repo.create_entry.call_args
        entry_data = create_call[0][1]
        items_data = create_call[0][2]

        assert "[역분개]" in entry_data["narration"]

        # 역분개 항목: 차변/대변 반전 확인
        assert items_data[0]["debit"] == 0.0  # 원래 debit=100000 -> credit
        assert items_data[0]["credit"] == 100000.0
        assert items_data[1]["debit"] == 100000.0  # 원래 credit=100000 -> debit
        assert items_data[1]["credit"] == 0.0

    @pytest.mark.asyncio
    async def test_reverse_entry_is_auto_posted(self, journal_service, mock_session):
        """역분개가 자동으로 posted 상태로 전환되는지 확인"""
        journal_service.journal_repo.get = AsyncMock(
            return_value={
                "id": "je-1",
                "status": "posted",
                "entry_date": date(2026, 2, 8),
                "narration": "테스트",
                "voucher_id": None,
                "items": [
                    {"account_id": "a1", "debit": 500.0, "credit": 0.0,
                     "customer_id": None, "description": "d1"},
                    {"account_id": "a2", "debit": 0.0, "credit": 500.0,
                     "customer_id": None, "description": "d2"},
                ],
            }
        )
        journal_service.journal_repo.update_status = AsyncMock(return_value=None)
        journal_service.journal_repo.create_entry = AsyncMock(
            return_value={"id": "je-rev", "status": "draft", "items": []}
        )

        await journal_service.cancel_entry(mock_session, "je-1")

        # update_status가 2번 호출: 원래 -> cancelled, 역분개 -> posted
        calls = journal_service.journal_repo.update_status.call_args_list
        assert len(calls) == 2
        assert calls[0][0] == (mock_session, "je-1", "cancelled")
        assert calls[1][0] == (mock_session, "je-rev", "posted")

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_entry_raises_error(self, journal_service, mock_session):
        """존재하지 않는 분개 취소 시 에러"""
        journal_service.journal_repo.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            await journal_service.cancel_entry(mock_session, "nonexistent")


# ========== 계정과목 서비스 ==========


class TestAccountServiceValidation:
    """AccountService 비즈니스 로직 테스트"""

    @pytest.mark.asyncio
    async def test_duplicate_code_rejected(self):
        """중복 계정코드 거부"""
        from kis_erp_core.services.account_service import AccountService

        service = AccountService()
        service.repo = AsyncMock()
        service.repo.get_by_code = AsyncMock(
            return_value={"id": "existing", "account_code": "1010"}
        )
        mock_session = AsyncMock()

        from kis_erp_core.models.accounting_models import AccountCreate, AccountType, BalanceDirection

        data = AccountCreate(
            account_code="1010",
            account_name="현금",
            account_type=AccountType.ASSET,
            balance_direction=BalanceDirection.DEBIT,
        )

        with pytest.raises(ValueError, match="이미 존재"):
            await service.create_account(mock_session, data)

    @pytest.mark.asyncio
    async def test_invalid_parent_id_rejected(self):
        """존재하지 않는 상위 계정 ID 거부"""
        from kis_erp_core.services.account_service import AccountService

        service = AccountService()
        service.repo = AsyncMock()
        service.repo.get_by_code = AsyncMock(return_value=None)
        service.repo.get = AsyncMock(return_value=None)  # parent not found
        mock_session = AsyncMock()

        from kis_erp_core.models.accounting_models import AccountCreate, AccountType, BalanceDirection

        data = AccountCreate(
            account_code="1015",
            account_name="정기예금",
            account_type=AccountType.ASSET,
            balance_direction=BalanceDirection.DEBIT,
            parent_id="nonexistent-parent",
        )

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            await service.create_account(mock_session, data)
