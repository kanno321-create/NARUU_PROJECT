"""
Carryover Service
기초이월 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.carryover_repository import CarryoverRepository


class CarryoverService:
    """기초이월 서비스"""

    def __init__(self):
        self.repo = CarryoverRepository()

    # ==================== 상품재고 이월 ====================

    async def list_stock(
        self,
        session: AsyncSession,
        fiscal_year: int,
        product_id: Optional[str] = None,
    ) -> List[dict]:
        """재고이월 목록 조회"""
        return await self.repo.list_stock(session, fiscal_year, product_id)

    async def create_stock(self, session: AsyncSession, data: dict) -> dict:
        """재고이월 단건 생성"""
        return await self.repo.create_stock(session, data)

    async def create_stock_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """재고이월 일괄 생성"""
        return await self.repo.create_stock_bulk(session, items)

    async def delete_stock(self, session: AsyncSession, carryover_id: str) -> bool:
        """재고이월 삭제"""
        return await self.repo.delete_stock(session, carryover_id)

    # ==================== 미수/미지급금 이월 ====================

    async def list_balance(
        self,
        session: AsyncSession,
        fiscal_year: int,
        balance_type: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> List[dict]:
        """잔액이월 목록 조회"""
        return await self.repo.list_balance(
            session, fiscal_year, balance_type, customer_id
        )

    async def create_balance(self, session: AsyncSession, data: dict) -> dict:
        """잔액이월 단건 생성"""
        return await self.repo.create_balance(session, data)

    async def create_balance_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """잔액이월 일괄 생성"""
        return await self.repo.create_balance_bulk(session, items)

    async def delete_balance(self, session: AsyncSession, carryover_id: str) -> bool:
        """잔액이월 삭제"""
        return await self.repo.delete_balance(session, carryover_id)

    # ==================== 현금잔고 이월 ====================

    async def list_cash(
        self,
        session: AsyncSession,
        fiscal_year: int,
        account_id: Optional[str] = None,
    ) -> List[dict]:
        """현금이월 목록 조회"""
        return await self.repo.list_cash(session, fiscal_year, account_id)

    async def create_cash(self, session: AsyncSession, data: dict) -> dict:
        """현금이월 단건 생성"""
        return await self.repo.create_cash(session, data)

    async def create_cash_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """현금이월 일괄 생성"""
        return await self.repo.create_cash_bulk(session, items)

    async def delete_cash(self, session: AsyncSession, carryover_id: str) -> bool:
        """현금이월 삭제"""
        return await self.repo.delete_cash(session, carryover_id)

    # ==================== 자동 이월 / 요약 ====================

    async def auto_generate(
        self,
        session: AsyncSession,
        fiscal_year: int,
        carryover_date: date,
    ) -> dict:
        """전년도 데이터 기반으로 기초이월 자동 생성"""
        return await self.repo.auto_generate(session, fiscal_year, carryover_date)

    async def summary(self, session: AsyncSession, fiscal_year: int) -> dict:
        """해당 회계연도의 기초이월 현황 요약"""
        return await self.repo.summary(session, fiscal_year)
