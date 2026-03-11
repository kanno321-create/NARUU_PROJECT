"""
DrawingFile Service
도면 파일 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.drawing_file_repository import DrawingFileRepository


class DrawingFileService:
    """도면 파일 서비스"""

    def __init__(self):
        self.repo = DrawingFileRepository()

    async def ensure_table(self, session: AsyncSession) -> None:
        """테이블 자동 생성"""
        await self.repo.ensure_table(session)

    async def save_file(
        self,
        session: AsyncSession,
        drawing_name: str,
        file_name: str,
        file_type: str,
        file_data: bytes,
        project_name: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """도면 파일 저장"""
        return await self.repo.save(
            session, drawing_name, file_name, file_type, file_data,
            project_name, customer_name, description, tags,
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
        project_name: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """도면 파일 목록"""
        return await self.repo.list(session, search, project_name, status, skip, limit)

    async def update_file(
        self, session: AsyncSession, file_id: str, data: dict
    ) -> Optional[dict]:
        """도면 메타데이터 수정"""
        return await self.repo.update(session, file_id, data)

    async def delete_file(self, session: AsyncSession, file_id: str) -> bool:
        """도면 파일 삭제"""
        return await self.repo.delete(session, file_id)
