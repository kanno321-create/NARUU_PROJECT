"""
Company Service
자사정보 비즈니스 로직
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.erp_models import CompanyCreate, CompanyUpdate
from kis_erp_core.repositories.company_repository import CompanyRepository


class CompanyService:
    """Company 서비스"""
    
    def __init__(self):
        self.repo = CompanyRepository()
    
    async def get_company(self, session: AsyncSession) -> Optional[dict]:
        """자사정보 조회"""
        return await self.repo.get(session)
    
    async def create_company(self, session: AsyncSession, data: CompanyCreate) -> dict:
        """자사정보 생성 (최초 1회만)"""
        # TODO[KIS-351]: 이미 존재하는지 확인
        # TODO[KIS-352]: Evidence 생성
        return await self.repo.create(session, data)
    
    async def update_company(self, session: AsyncSession, data: CompanyUpdate) -> Optional[dict]:
        """자사정보 수정"""
        # TODO[KIS-353]: Evidence 생성
        return await self.repo.update(session, data)
