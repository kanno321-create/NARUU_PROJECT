"""
BankAccount Service
은행계좌 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.bank_account_repository import BankAccountRepository


class BankAccountService:
    """은행계좌 서비스"""

    def __init__(self):
        self.repo = BankAccountRepository()

    async def create_account(self, session: AsyncSession, data: dict) -> dict:
        """은행계좌 생성"""
        return await self.repo.create(session, data)

    async def get_account(self, session: AsyncSession, account_id: str) -> Optional[dict]:
        """은행계좌 조회"""
        return await self.repo.get(session, account_id)

    async def list_accounts(
        self,
        session: AsyncSession,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """은행계좌 목록"""
        return await self.repo.list(session, is_active, search, skip, limit)

    async def update_account(
        self, session: AsyncSession, account_id: str, data: dict
    ) -> Optional[dict]:
        """은행계좌 수정"""
        return await self.repo.update(session, account_id, data)

    async def delete_account(self, session: AsyncSession, account_id: str) -> bool:
        """은행계좌 비활성화"""
        return await self.repo.delete(session, account_id)
