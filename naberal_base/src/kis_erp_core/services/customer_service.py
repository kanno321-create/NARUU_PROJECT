"""
Customer Service
비즈니스 로직 레이어
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.erp_models import Customer, CustomerCreate, CustomerUpdate, CustomerFilter
from kis_erp_core.repositories.customer_repository import CustomerRepository


class CustomerService:
    """
    Customer 서비스
    비즈니스 로직 및 Evidence 생성
    """
    
    def __init__(self):
        self.repo = CustomerRepository()
    
    async def create_customer(
        self, 
        session: AsyncSession, 
        data: CustomerCreate
    ) -> dict:
        """
        거래처 생성
        
        비즈니스 로직:
        - 거래처 코드 자동 생성
        - 중복 체크
        - Evidence 생성
        """
        # TODO[KIS-311]: 중복 체크 (business_number, name)
        # TODO[KIS-312]: 거래처 코드 자동 생성
        # TODO[KIS-313]: Evidence 생성
        
        result = await self.repo.create(session, data)
        return result
    
    async def get_customer(
        self, 
        session: AsyncSession, 
        id: UUID
    ) -> Optional[dict]:
        """거래처 조회"""
        return await self.repo.get(session, id)
    
    async def list_customers(
        self,
        session: AsyncSession,
        filters: CustomerFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """거래처 목록 조회"""
        return await self.repo.list(session, filters, skip, limit)
    
    async def update_customer(
        self,
        session: AsyncSession,
        id: UUID,
        data: CustomerUpdate
    ) -> Optional[dict]:
        """
        거래처 수정
        
        비즈니스 로직:
        - 존재 여부 확인
        - Evidence 생성
        """
        # TODO[KIS-314]: 존재 여부 확인
        # TODO[KIS-315]: Evidence 생성
        
        return await self.repo.update(session, id, data)
    
    async def delete_customer(
        self,
        session: AsyncSession,
        id: UUID
    ) -> bool:
        """
        거래처 삭제 (soft delete)
        
        비즈니스 로직:
        - 참조 데이터 확인 (전표 등)
        - Evidence 생성
        """
        # TODO[KIS-316]: 참조 데이터 확인
        # TODO[KIS-317]: Evidence 생성
        
        return await self.repo.delete(session, id)
    
    async def get_balance(
        self,
        session: AsyncSession,
        id: UUID
    ) -> float:
        """거래처 잔액 조회"""
        balance = await self.repo.get_balance(session, id)
        return float(balance)
