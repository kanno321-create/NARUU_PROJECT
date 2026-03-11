"""
Settings Service
환경설정 + 사업장 마감 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock

Thin wrapper: Repository 위임 패턴
"""

from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.settings_repository import SettingsRepository


class SettingsService:
    """환경설정 서비스"""

    def __init__(self):
        self.repo = SettingsRepository()

    async def get_settings(self, session: AsyncSession) -> dict:
        """환경설정 조회"""
        return await self.repo.get_settings(session)

    async def update_settings(self, session: AsyncSession, data: dict) -> dict:
        """환경설정 업데이트 (기존 값에 병합)"""
        return await self.repo.update_settings(session, data)

    async def get_preferences(self, session: AsyncSession) -> dict:
        """UI 사용자 환경설정 조회 (표시항목 등)"""
        return await self.repo.get_preferences(session)

    async def update_preferences(self, session: AsyncSession, data: dict) -> dict:
        """UI 사용자 환경설정 저장 (표시항목 등)"""
        return await self.repo.update_preferences(session, data)

    async def list_periods(
        self, session: AsyncSession, year: int | None = None
    ) -> list[dict]:
        """사업장 마감현황 조회"""
        return await self.repo.list_periods(session, year)

    async def close_period(
        self,
        session: AsyncSession,
        year: int,
        month: int,
        notes: str | None = None,
    ) -> dict:
        """월 마감 처리"""
        return await self.repo.close_period(session, year, month, notes)

    async def reopen_period(
        self,
        session: AsyncSession,
        year: int,
        month: int,
        reason: str,
    ) -> dict | None:
        """월 마감해제"""
        return await self.repo.reopen_period(session, year, month, reason)
