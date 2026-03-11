"""
Payroll Service
급여대장 비즈니스 로직
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.payroll_repository import PayrollRepository


class PayrollService:
    """Payroll 서비스"""

    def __init__(self):
        self.repo = PayrollRepository()

    async def create_payroll(self, session: AsyncSession, data: dict) -> dict:
        """급여대장 생성"""
        return await self.repo.save(session, data)

    async def get_payroll(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여대장 상세 조회"""
        return await self.repo.get(session, payroll_id)

    async def get_payroll_by_period(self, session: AsyncSession, year: int, month: int) -> Optional[dict]:
        """특정 연월 급여대장 조회"""
        return await self.repo.get_by_period(session, year, month)

    async def list_payrolls(
        self,
        session: AsyncSession,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 12,
    ) -> List[dict]:
        """급여대장 목록"""
        return await self.repo.list_by_period(session, year, status, skip, limit)

    async def update_payroll(self, session: AsyncSession, payroll_id: str, data: dict) -> Optional[dict]:
        """급여대장 수정"""
        return await self.repo.update(session, payroll_id, data)

    async def delete_payroll(self, session: AsyncSession, payroll_id: str) -> bool:
        """급여대장 삭제"""
        return await self.repo.delete(session, payroll_id)

    async def confirm_payroll(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여대장 확정"""
        return await self.repo.confirm(session, payroll_id)

    async def pay_payroll(self, session: AsyncSession, payroll_id: str) -> Optional[dict]:
        """급여 지급 처리"""
        return await self.repo.pay(session, payroll_id)
