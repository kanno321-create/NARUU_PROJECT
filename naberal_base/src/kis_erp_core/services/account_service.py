"""
Account Service
계정과목 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.accounting_models import (
    AccountCreate,
    AccountUpdate,
    AccountFilter,
)
from kis_erp_core.repositories.account_repository import AccountRepository


class AccountService:
    """Account 서비스"""

    def __init__(self):
        self.repo = AccountRepository()

    async def list_accounts(
        self,
        session: AsyncSession,
        filters: AccountFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """계정과목 목록 조회"""
        return await self.repo.list(session, filters, skip, limit)

    async def get_account(self, session: AsyncSession, id: str) -> Optional[dict]:
        """계정과목 단일 조회"""
        return await self.repo.get(session, id)

    async def get_account_by_code(
        self, session: AsyncSession, code: str
    ) -> Optional[dict]:
        """계정코드로 조회"""
        return await self.repo.get_by_code(session, code)

    async def create_account(
        self, session: AsyncSession, data: AccountCreate
    ) -> dict:
        """
        계정과목 생성

        - 계정코드 중복 검증
        - parent_id 유효성 검증 (지정 시)
        """
        existing = await self.repo.get_by_code(session, data.account_code)
        if existing:
            raise ValueError(
                f"계정코드 '{data.account_code}'이(가) 이미 존재합니다"
            )

        if data.parent_id:
            parent = await self.repo.get(session, data.parent_id)
            if not parent:
                raise ValueError(
                    f"상위 계정 ID '{data.parent_id}'을(를) 찾을 수 없습니다"
                )

        return await self.repo.create(session, data)

    async def update_account(
        self, session: AsyncSession, id: str, data: AccountUpdate
    ) -> Optional[dict]:
        """계정과목 수정"""
        if data.parent_id is not None:
            parent = await self.repo.get(session, data.parent_id)
            if not parent:
                raise ValueError(
                    f"상위 계정 ID '{data.parent_id}'을(를) 찾을 수 없습니다"
                )

        return await self.repo.update(session, id, data)
