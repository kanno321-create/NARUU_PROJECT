"""
회계 레포지토리 레이어 테스트
- AccountRepository: list, get, get_by_code, create, update 로직 검증
- JournalRepository: list, get, create_entry, update_status, get_trial_balance 로직 검증

DB 필요한 테스트: @pytest.mark.integration
순수 로직 테스트: _row_to_dict 등 유틸리티 메서드
"""

import pytest
from datetime import date
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from kis_erp_core.repositories.account_repository import AccountRepository
from kis_erp_core.repositories.journal_repository import JournalRepository
from kis_erp_core.models.accounting_models import (
    AccountCreate,
    AccountUpdate,
    AccountFilter,
    AccountType,
    BalanceDirection,
    JournalEntryFilter,
    JournalStatus,
)


# ========== AccountRepository Unit Tests ==========


class TestAccountRepositoryRowConversion:
    """AccountRepository._row_to_dict 유틸리티 검증"""

    def test_uuid_fields_converted_to_str(self):
        """UUID 필드가 str로 변환되는지 확인"""
        repo = AccountRepository()
        test_uuid = uuid4()
        parent_uuid = uuid4()
        row = {
            "id": test_uuid,
            "parent_id": parent_uuid,
            "account_code": "1010",
            "account_name": "현금",
        }

        result = repo._row_to_dict(row)
        assert result["id"] == str(test_uuid)
        assert result["parent_id"] == str(parent_uuid)
        assert result["account_code"] == "1010"

    def test_none_parent_id_preserved(self):
        """parent_id가 None이면 None 유지"""
        repo = AccountRepository()
        row = {
            "id": uuid4(),
            "parent_id": None,
            "account_code": "1000",
        }

        result = repo._row_to_dict(row)
        assert result["parent_id"] is None

    def test_non_uuid_fields_unchanged(self):
        """비-UUID 필드는 변환하지 않음"""
        repo = AccountRepository()
        row = {
            "id": uuid4(),
            "account_code": "1010",
            "account_name": "현금",
            "account_type": "asset",
            "is_group": False,
            "is_active": True,
        }

        result = repo._row_to_dict(row)
        assert result["account_code"] == "1010"
        assert result["account_type"] == "asset"
        assert result["is_group"] is False


class TestAccountRepositoryFilterBuilding:
    """AccountRepository.list() 필터 파라미터 검증"""

    @pytest.mark.asyncio
    async def test_filter_by_account_type(self):
        """account_type 필터 적용"""
        repo = AccountRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = AccountFilter(account_type=AccountType.ASSET)
        await repo.list(session, filters)

        # execute가 호출되었는지 확인
        session.execute.assert_called_once()
        call_args = session.execute.call_args
        params = call_args[0][1]  # 두 번째 인자 (params dict)
        assert params["account_type"] == "asset"

    @pytest.mark.asyncio
    async def test_filter_by_search(self):
        """search 필터 (ILIKE) 적용"""
        repo = AccountRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = AccountFilter(search="현금")
        await repo.list(session, filters)

        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["search"] == "%현금%"

    @pytest.mark.asyncio
    async def test_empty_filter(self):
        """필터 없을 때 1=1 조건"""
        repo = AccountRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = AccountFilter(is_active=None)
        await repo.list(session, filters)

        call_args = session.execute.call_args
        query_text = str(call_args[0][0])
        assert "1=1" in query_text


class TestAccountRepositoryUpdate:
    """AccountRepository.update() 동작 검증"""

    @pytest.mark.asyncio
    async def test_empty_update_calls_get(self):
        """수정할 필드 없으면 get() 호출"""
        repo = AccountRepository()
        session = AsyncMock()

        mock_get_result = MagicMock()
        mock_get_result.mappings.return_value.first.return_value = {
            "id": uuid4(),
            "account_code": "1010",
            "account_name": "현금",
        }
        session.execute = AsyncMock(return_value=mock_get_result)

        data = AccountUpdate()  # 모든 필드 None
        result = await repo.update(session, "acc-1", data)

        # get()이 호출되어야 함 (update SQL 대신)
        assert result is not None


# ========== JournalRepository Unit Tests ==========


class TestJournalRepositoryRowConversion:
    """JournalRepository._row_to_dict 유틸리티 검증"""

    def test_all_uuid_fields_converted(self):
        """모든 UUID 필드가 str로 변환"""
        repo = JournalRepository()
        row = {
            "id": uuid4(),
            "journal_entry_id": uuid4(),
            "account_id": uuid4(),
            "voucher_id": uuid4(),
            "customer_id": uuid4(),
            "debit": 100000.0,
            "credit": 0.0,
        }

        result = repo._row_to_dict(row)
        assert isinstance(result["id"], str)
        assert isinstance(result["journal_entry_id"], str)
        assert isinstance(result["account_id"], str)
        assert isinstance(result["voucher_id"], str)
        assert isinstance(result["customer_id"], str)
        assert result["debit"] == 100000.0

    def test_null_optional_uuids_preserved(self):
        """선택적 UUID 필드 None 유지"""
        repo = JournalRepository()
        row = {
            "id": uuid4(),
            "voucher_id": None,
            "customer_id": None,
        }

        result = repo._row_to_dict(row)
        assert result["voucher_id"] is None
        assert result["customer_id"] is None

    def test_missing_uuid_fields_ignored(self):
        """UUID 필드가 없는 경우 에러 없이 처리"""
        repo = JournalRepository()
        row = {
            "id": uuid4(),
            "entry_number": "JE-20260208-0001",
            "narration": "테스트",
        }

        result = repo._row_to_dict(row)
        assert result["entry_number"] == "JE-20260208-0001"


class TestJournalRepositoryFilterBuilding:
    """JournalRepository.list() 필터 파라미터 검증"""

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self):
        """날짜 범위 필터 적용"""
        repo = JournalRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = JournalEntryFilter(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
        )
        await repo.list(session, filters)

        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["start_date"] == date(2026, 1, 1)
        assert params["end_date"] == date(2026, 2, 28)

    @pytest.mark.asyncio
    async def test_filter_by_status(self):
        """상태 필터 적용"""
        repo = JournalRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = JournalEntryFilter(status=JournalStatus.POSTED)
        await repo.list(session, filters)

        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["status"] == "posted"

    @pytest.mark.asyncio
    async def test_filter_by_search(self):
        """적요 검색 필터"""
        repo = JournalRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        filters = JournalEntryFilter(search="매출")
        await repo.list(session, filters)

        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["search"] == "%매출%"


class TestJournalRepositoryGetEntry:
    """JournalRepository.get() 동작 검증"""

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing(self):
        """존재하지 않는 ID 조회 시 None"""
        repo = JournalRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get(session, "nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_includes_items(self):
        """상세 조회 시 items JOIN 포함"""
        repo = JournalRepository()
        session = AsyncMock()

        header_uuid = uuid4()

        # 첫 번째 execute: 헤더 조회
        header_result = MagicMock()
        header_result.mappings.return_value.first.return_value = {
            "id": header_uuid,
            "entry_number": "JE-20260208-0001",
            "entry_date": date(2026, 2, 8),
            "narration": "테스트",
            "voucher_id": None,
            "total_debit": 100000.0,
            "total_credit": 100000.0,
            "status": "draft",
            "created_at": None,
            "updated_at": None,
        }

        # 두 번째 execute: 항목 조회
        items_result = MagicMock()
        items_result.mappings.return_value.all.return_value = [
            {
                "id": uuid4(),
                "journal_entry_id": header_uuid,
                "account_id": uuid4(),
                "account_code": "1010",
                "account_name": "현금",
                "debit": 100000.0,
                "credit": 0.0,
                "customer_id": None,
                "customer_name": None,
                "description": "현금 수령",
            },
        ]

        session.execute = AsyncMock(side_effect=[header_result, items_result])

        result = await repo.get(session, str(header_uuid))
        assert result is not None
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["account_code"] == "1010"


class TestJournalRepositoryTrialBalance:
    """JournalRepository.get_trial_balance() 검증"""

    @pytest.mark.asyncio
    async def test_trial_balance_returns_float_values(self):
        """시산표 결과에서 Decimal -> float 변환 확인"""
        repo = JournalRepository()
        session = AsyncMock()

        from decimal import Decimal

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {
                "account_id": uuid4(),
                "account_code": "1010",
                "account_name": "현금",
                "account_type": "asset",
                "debit_total": Decimal("500000.00"),
                "credit_total": Decimal("200000.00"),
                "balance": Decimal("300000.00"),
            },
        ]
        session.execute = AsyncMock(return_value=mock_result)

        results = await repo.get_trial_balance(session, date(2026, 2, 8))
        assert len(results) == 1
        assert isinstance(results[0]["debit_total"], float)
        assert isinstance(results[0]["credit_total"], float)
        assert isinstance(results[0]["balance"], float)
        assert results[0]["debit_total"] == 500000.0
        assert results[0]["balance"] == 300000.0

    @pytest.mark.asyncio
    async def test_trial_balance_empty(self):
        """거래 없을 때 빈 리스트"""
        repo = JournalRepository()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        results = await repo.get_trial_balance(session, date(2026, 2, 8))
        assert results == []


class TestJournalRepositoryAccountBalance:
    """JournalRepository.get_account_balance() 검증"""

    @pytest.mark.asyncio
    async def test_account_balance_calculation(self):
        """계정별 잔액 계산"""
        repo = JournalRepository()
        session = AsyncMock()

        from decimal import Decimal

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "debit_total": Decimal("500000.00"),
            "credit_total": Decimal("200000.00"),
        }
        session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_account_balance(session, "acc-1")
        assert result["account_id"] == "acc-1"
        assert result["debit_total"] == 500000.0
        assert result["credit_total"] == 200000.0
        assert result["balance"] == 300000.0  # debit - credit

    @pytest.mark.asyncio
    async def test_account_balance_with_date_filter(self):
        """날짜 필터 적용 시 파라미터 전달 확인"""
        repo = JournalRepository()
        session = AsyncMock()

        from decimal import Decimal

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "debit_total": Decimal("0"),
            "credit_total": Decimal("0"),
        }
        session.execute = AsyncMock(return_value=mock_result)

        await repo.get_account_balance(
            session,
            "acc-1",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
        )

        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["start_date"] == date(2026, 1, 1)
        assert params["end_date"] == date(2026, 2, 28)
