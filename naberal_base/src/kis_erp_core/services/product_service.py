"""
Product Service
상품/재고 비즈니스 로직
"""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.product_employee_models import ProductCreate, ProductUpdate, ProductFilter
from kis_erp_core.repositories.product_repository import ProductRepository


class ProductService:
    """Product 서비스"""
    
    def __init__(self):
        self.repo = ProductRepository()
    
    async def create_product(self, session: AsyncSession, data: ProductCreate) -> dict:
        """상품 생성"""
        # TODO[KIS-361]: 상품 코드 자동 생성
        # TODO[KIS-362]: 중복 체크
        # TODO[KIS-363]: Evidence 생성
        return await self.repo.create(session, data)
    
    async def get_product(self, session: AsyncSession, id: UUID) -> Optional[dict]:
        """상품 조회"""
        return await self.repo.get(session, id)
    
    async def list_products(self, session: AsyncSession, filters: ProductFilter, skip: int, limit: int) -> List[dict]:
        """상품 목록"""
        return await self.repo.list(session, filters, skip, limit)
    
    async def update_product(self, session: AsyncSession, id: UUID, data: ProductUpdate) -> Optional[dict]:
        """상품 수정"""
        # TODO[KIS-364]: Evidence 생성
        return await self.repo.update(session, id, data)
    
    async def delete_product(self, session: AsyncSession, id: UUID) -> bool:
        """상품 삭제"""
        # TODO[KIS-365]: Evidence 생성
        return await self.repo.delete(session, id)
    
    async def adjust_stock(self, session: AsyncSession, id: UUID, qty: Decimal, reason: str) -> dict:
        """재고 조정"""
        # TODO[KIS-366]: 재고 이력 기록
        # TODO[KIS-367]: Evidence 생성
        return await self.repo.adjust_stock(session, id, qty, reason)
