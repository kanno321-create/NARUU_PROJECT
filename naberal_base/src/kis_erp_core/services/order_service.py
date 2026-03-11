"""
Order Service
발주서 비즈니스 로직 (thin wrapper)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.order_repository import OrderRepository


class OrderService:
    """발주서 서비스 - CRUD + 상태 관리"""

    def __init__(self):
        self.repo = OrderRepository()

    async def list_orders(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """발주서 목록 조회"""
        return await self.repo.list(
            session,
            status=status,
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def get_order(
        self, session: AsyncSession, order_id: str
    ) -> Optional[dict]:
        """발주서 상세 조회 (items 포함)"""
        return await self.repo.get(session, order_id)

    async def create_order(
        self, session: AsyncSession, data: dict
    ) -> dict:
        """발주서 생성 (header + items, 발주번호 자동생성)"""
        return await self.repo.create(session, data)

    async def update_order(
        self, session: AsyncSession, order_id: str, data: dict
    ) -> Optional[dict]:
        """발주서 수정 (draft/sent 상태만)"""
        return await self.repo.update(session, order_id, data)

    async def delete_order(
        self, session: AsyncSession, order_id: str
    ) -> bool:
        """발주서 삭제 (draft 상태만)"""
        existing = await self.repo.get(session, order_id)
        if not existing:
            raise ValueError(f"발주서 ID '{order_id}'을(를) 찾을 수 없습니다")

        if existing["status"] != "draft":
            raise ValueError(
                f"삭제할 수 없는 상태입니다: {existing['status']} "
                f"(draft만 삭제 가능)"
            )

        return await self.repo.delete(session, order_id)

    async def send_order(
        self, session: AsyncSession, order_id: str
    ) -> Optional[dict]:
        """발주서 발송 (draft → sent)"""
        return await self.repo.update_status(session, order_id, "sent")

    async def confirm_order(
        self, session: AsyncSession, order_id: str
    ) -> Optional[dict]:
        """발주 확정 (sent → confirmed)"""
        return await self.repo.update_status(session, order_id, "confirmed")

    async def receive_order(
        self, session: AsyncSession, order_id: str
    ) -> Optional[dict]:
        """입고 처리 (confirmed → received)"""
        return await self.repo.update_status(session, order_id, "received")

    async def cancel_order(
        self, session: AsyncSession, order_id: str, reason: str
    ) -> Optional[dict]:
        """발주 취소 (draft/sent → cancelled, 취소 사유 기록)"""
        memo_append = f"[취소사유] {reason}"
        return await self.repo.update_status(
            session, order_id, "cancelled", memo_append=memo_append
        )
