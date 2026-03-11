"""
Employee Service
사원 비즈니스 로직
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.product_employee_models import EmployeeCreate, EmployeeUpdate, EmployeeFilter
from kis_erp_core.repositories.employee_repository import EmployeeRepository


class EmployeeService:
    """Employee 서비스"""
    
    def __init__(self):
        self.repo = EmployeeRepository()
    
    async def create_employee(self, session: AsyncSession, data: EmployeeCreate) -> dict:
        """사원 생성"""
        # TODO[KIS-371]: 사원번호 자동 생성
        # TODO[KIS-372]: 중복 체크
        # TODO[KIS-373]: Evidence 생성
        return await self.repo.create(session, data)
    
    async def get_employee(self, session: AsyncSession, id: UUID) -> Optional[dict]:
        """사원 조회"""
        return await self.repo.get(session, id)
    
    async def list_employees(self, session: AsyncSession, filters: EmployeeFilter, skip: int, limit: int) -> List[dict]:
        """사원 목록"""
        return await self.repo.list(session, filters, skip, limit)
    
    async def update_employee(self, session: AsyncSession, id: UUID, data: EmployeeUpdate) -> Optional[dict]:
        """사원 수정"""
        # TODO[KIS-374]: Evidence 생성
        return await self.repo.update(session, id, data)
    
    async def delete_employee(self, session: AsyncSession, id: UUID) -> bool:
        """사원 퇴사 처리"""
        # TODO[KIS-375]: Evidence 생성
        return await self.repo.delete(session, id)
