"""
Journal Service
분개장 비즈니스 로직 (복식부기 핵심)
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.accounting_models import (
    JournalEntryCreate,
    JournalEntryFilter,
    AccountType,
)
from kis_erp_core.repositories.journal_repository import JournalRepository
from kis_erp_core.repositories.account_repository import AccountRepository


class JournalService:
    """Journal 서비스 - 복식부기 핵심 로직"""

    def __init__(self):
        self.journal_repo = JournalRepository()
        self.account_repo = AccountRepository()

    async def list_entries(
        self,
        session: AsyncSession,
        filters: JournalEntryFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """분개 목록 조회"""
        return await self.journal_repo.list(session, filters, skip, limit)

    async def get_entry(self, session: AsyncSession, id: str) -> Optional[dict]:
        """분개 상세 조회 (items 포함)"""
        return await self.journal_repo.get(session, id)

    async def create_journal_entry(
        self, session: AsyncSession, data: JournalEntryCreate
    ) -> dict:
        """
        분개 생성 (복식부기 핵심)

        검증:
        1. 최소 2개 항목 필수
        2. SUM(debit) == SUM(credit) 대차평균 검증
        3. 각 account_id가 실제 존재하는지 검증
        4. 각 항목의 debit/credit 유효성 (DB 제약조건과 동일)
        """
        # 1. 최소 2개 항목 검증
        if len(data.items) < 2:
            raise ValueError("분개항목은 최소 2개 필요합니다 (차변+대변)")

        # 2. 대차평균 검증: SUM(debit) == SUM(credit)
        total_debit = sum(item.debit for item in data.items)
        total_credit = sum(item.credit for item in data.items)

        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(
                f"대차평균 불일치: 차변합계={total_debit:,.2f}, "
                f"대변합계={total_credit:,.2f}"
            )

        # 3. 각 항목 유효성 검증
        for idx, item in enumerate(data.items):
            # debit과 credit 둘 다 0이면 안 됨
            if item.debit == 0 and item.credit == 0:
                raise ValueError(
                    f"항목 {idx + 1}: 차변 또는 대변 중 하나는 0보다 커야 합니다"
                )

            # debit과 credit 둘 다 양수면 안 됨
            if item.debit > 0 and item.credit > 0:
                raise ValueError(
                    f"항목 {idx + 1}: 차변과 대변이 동시에 양수일 수 없습니다"
                )

            # 계정과목 존재 검증
            account = await self.account_repo.get(session, item.account_id)
            if not account:
                raise ValueError(
                    f"항목 {idx + 1}: 계정과목 ID '{item.account_id}'을(를) "
                    f"찾을 수 없습니다"
                )

        # 4. 분개 생성
        entry_data = {
            "entry_date": data.entry_date,
            "narration": data.narration,
            "voucher_id": data.voucher_id,
        }

        items_data = [
            {
                "account_id": item.account_id,
                "debit": item.debit,
                "credit": item.credit,
                "customer_id": item.customer_id,
                "description": item.description,
            }
            for item in data.items
        ]

        return await self.journal_repo.create_entry(session, entry_data, items_data)

    async def post_entry(self, session: AsyncSession, id: str) -> Optional[dict]:
        """
        분개 전기 (draft -> posted)

        전기 후에는 수정 불가, 취소만 가능
        """
        entry = await self.journal_repo.get(session, id)
        if not entry:
            return None

        if entry["status"] != "draft":
            raise ValueError(
                f"전기할 수 없는 상태입니다: {entry['status']} "
                f"(draft만 전기 가능)"
            )

        return await self.journal_repo.update_status(session, id, "posted")

    async def cancel_entry(self, session: AsyncSession, id: str) -> dict:
        """
        분개 취소 (posted -> cancelled + 역분개 생성)

        1. 원래 분개를 cancelled로 변경
        2. 역분개(차변/대변 반전) 자동 생성
        """
        entry = await self.journal_repo.get(session, id)
        if not entry:
            raise ValueError(f"분개 ID '{id}'을(를) 찾을 수 없습니다")

        if entry["status"] != "posted":
            raise ValueError(
                f"취소할 수 없는 상태입니다: {entry['status']} "
                f"(posted만 취소 가능)"
            )

        # 1. 원래 분개 취소
        await self.journal_repo.update_status(session, id, "cancelled")

        # 2. 역분개 생성 (차변/대변 반전)
        reverse_items = []
        for item in entry.get("items", []):
            reverse_items.append({
                "account_id": item["account_id"],
                "debit": float(item["credit"]),
                "credit": float(item["debit"]),
                "customer_id": item.get("customer_id"),
                "description": f"[역분개] {item.get('description') or ''}".strip(),
            })

        reverse_entry_data = {
            "entry_date": entry["entry_date"],
            "narration": f"[역분개] {entry['narration']}",
            "voucher_id": entry.get("voucher_id"),
        }

        reverse_entry = await self.journal_repo.create_entry(
            session, reverse_entry_data, reverse_items
        )

        # 역분개를 즉시 전기
        await self.journal_repo.update_status(
            session, reverse_entry["id"], "posted"
        )

        return reverse_entry

    async def get_trial_balance(
        self, session: AsyncSession, as_of_date: date
    ) -> dict:
        """
        시산표 조회

        Returns:
            {as_of_date, accounts: [...], total_debit, total_credit}
        """
        accounts = await self.journal_repo.get_trial_balance(session, as_of_date)

        total_debit = sum(a["debit_total"] for a in accounts)
        total_credit = sum(a["credit_total"] for a in accounts)

        return {
            "as_of_date": as_of_date,
            "accounts": accounts,
            "total_debit": total_debit,
            "total_credit": total_credit,
        }

    async def get_balance_sheet(
        self, session: AsyncSession, as_of_date: date
    ) -> dict:
        """
        대차대조표

        자산 = 부채 + 자본
        """
        accounts = await self.journal_repo.get_trial_balance(session, as_of_date)

        assets = []
        liabilities = []
        equity = []

        for acc in accounts:
            acc_type = acc["account_type"]
            if acc_type == AccountType.ASSET.value:
                assets.append(acc)
            elif acc_type == AccountType.LIABILITY.value:
                liabilities.append(acc)
            elif acc_type == AccountType.EQUITY.value:
                equity.append(acc)

        total_assets = sum(a["balance"] for a in assets)
        total_liabilities = sum(abs(a["balance"]) for a in liabilities)
        total_equity = sum(abs(a["balance"]) for a in equity)

        return {
            "as_of_date": as_of_date,
            "assets": {
                "section_name": "자산",
                "accounts": assets,
                "total": total_assets,
            },
            "liabilities": {
                "section_name": "부채",
                "accounts": liabilities,
                "total": total_liabilities,
            },
            "equity": {
                "section_name": "자본",
                "accounts": equity,
                "total": total_equity,
            },
            "total_assets": total_assets,
            "total_liabilities_equity": total_liabilities + total_equity,
            "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01,
        }

    async def get_profit_loss(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        손익계산서

        순이익 = 수익 - 비용
        """
        accounts = await self.journal_repo.get_trial_balance(session, end_date)

        revenue = []
        expenses = []

        for acc in accounts:
            acc_type = acc["account_type"]
            if acc_type == AccountType.REVENUE.value:
                revenue.append(acc)
            elif acc_type == AccountType.EXPENSE.value:
                expenses.append(acc)

        total_revenue = sum(abs(a["balance"]) for a in revenue)
        total_expenses = sum(a["balance"] for a in expenses)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "revenue": {
                "section_name": "수익",
                "accounts": revenue,
                "total": total_revenue,
            },
            "expenses": {
                "section_name": "비용",
                "accounts": expenses,
                "total": total_expenses,
            },
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": total_revenue - total_expenses,
        }
