"""
EstimateFile Service
견적 파일 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.estimate_file_repository import EstimateFileRepository


class EstimateFileService:
    """견적 파일 서비스"""

    def __init__(self):
        self.repo = EstimateFileRepository()

    async def ensure_table(self, session: AsyncSession) -> None:
        """테이블 자동 생성"""
        await self.repo.ensure_table(session)

    async def save_file(
        self,
        session: AsyncSession,
        estimate_id: str,
        file_name: str,
        file_type: str,
        file_data: bytes,
        customer_name: Optional[str] = None,
        total_price: Optional[float] = None,
    ) -> dict:
        """견적 파일 저장"""
        return await self.repo.save(
            session, estimate_id, file_name, file_type, file_data,
            customer_name, total_price,
        )

    async def get_file(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 메타데이터 조회"""
        return await self.repo.get(session, file_id)

    async def get_file_data(self, session: AsyncSession, file_id: str) -> Optional[dict]:
        """파일 데이터 포함 조회 (다운로드용)"""
        return await self.repo.get_file_data(session, file_id)

    async def list_files(
        self,
        session: AsyncSession,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """견적 파일 목록"""
        return await self.repo.list(session, search, skip, limit)

    async def delete_file(self, session: AsyncSession, file_id: str) -> bool:
        """견적 파일 삭제"""
        return await self.repo.delete(session, file_id)
