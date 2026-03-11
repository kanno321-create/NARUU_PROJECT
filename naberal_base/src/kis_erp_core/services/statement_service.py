"""
Statement Service
거래명세서 비즈니스 로직 (thin wrapper over StatementRepository)
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.statement_repository import StatementRepository


class StatementService:
    """거래명세서 서비스"""

    def __init__(self):
        self.repo = StatementRepository()

    async def list_statements(
        self,
        session: AsyncSession,
        statement_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """거래명세서 목록 조회"""
        return await self.repo.list(
            session,
            statement_type=statement_type,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def get_statement(
        self,
        session: AsyncSession,
        statement_id: str,
    ) -> Optional[dict]:
        """거래명세서 단일 조회"""
        return await self.repo.get(session, statement_id)

    async def create_statement(
        self,
        session: AsyncSession,
        data: dict,
    ) -> dict:
        """거래명세서 생성"""
        return await self.repo.create(session, data)

    async def create_from_voucher(
        self,
        session: AsyncSession,
        voucher_id: str,
    ) -> Optional[dict]:
        """전표에서 거래명세서 자동 생성"""
        return await self.repo.create_from_voucher(session, voucher_id)

    async def update_statement(
        self,
        session: AsyncSession,
        statement_id: str,
        data: dict,
    ) -> Optional[dict]:
        """거래명세서 수정 (draft 상태만)"""
        return await self.repo.update(session, statement_id, data)

    async def delete_statement(
        self,
        session: AsyncSession,
        statement_id: str,
    ) -> bool:
        """거래명세서 삭제 (draft 상태만)"""
        return await self.repo.delete(session, statement_id)
