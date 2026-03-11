"""
Inventory Service
재고관리 비즈니스 로직 (thin wrapper)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.inventory_repository import InventoryRepository


class InventoryService:
    """재고관리 서비스 - 현황/조정/이동 조회 및 생성"""

    def __init__(self):
        self.repo = InventoryRepository()

    async def list_status(
        self,
        session: AsyncSession,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        """재고현황 목록 조회"""
        return await self.repo.list_status(
            session,
            category=category,
            low_stock_only=low_stock_only,
            skip=skip,
            limit=limit,
        )

    async def get_product_status(
        self, session: AsyncSession, product_id: str
    ) -> Optional[dict]:
        """단일 상품 재고현황 조회"""
        return await self.repo.get_product_status(session, product_id)

    async def get_summary(self, session: AsyncSession) -> dict:
        """재고현황 요약 집계"""
        return await self.repo.get_summary(session)

    async def list_adjustments(
        self,
        session: AsyncSession,
        product_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """재고조정 내역 조회"""
        return await self.repo.list_adjustments(
            session,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def create_adjustment(
        self, session: AsyncSession, data: dict
    ) -> dict:
        """
        재고조정 등록

        - 조정번호 자동 생성
        - before/after 수량 자동 계산
        - inventory_movements 동시 기록 (DB trigger가 stock_qty 갱신)
        """
        return await self.repo.create_adjustment(session, data)

    async def list_movements(
        self,
        session: AsyncSession,
        product_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """재고이동 내역 조회 (입출고 + 조정, summary 포함)"""
        return await self.repo.list_movements(
            session,
            product_id=product_id,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
