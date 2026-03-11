"""
Audit Service
감사추적 비즈니스 로직
Contract-First + Evidence-Gated + Zero-Mock

Thin wrapper: Repository 위임 패턴
"""

from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.audit_repository import AuditRepository


class AuditService:
    """감사추적 서비스"""

    def __init__(self):
        self.repo = AuditRepository()

    async def log_change(
        self,
        session: AsyncSession,
        table_name: str,
        record_id: str,
        action: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        changed_by: str | None = None,
        ip_address: str | None = None,
        description: str | None = None,
    ) -> dict:
        """변경 이력 기록"""
        return await self.repo.log_change(
            session,
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_by=changed_by,
            ip_address=ip_address,
            description=description,
        )

    async def list_logs(
        self,
        session: AsyncSession,
        table_name: str | None = None,
        record_id: str | None = None,
        action: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """감사 로그 목록 조회"""
        return await self.repo.list_logs(
            session,
            table_name=table_name,
            record_id=record_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

    async def get_record_history(
        self,
        session: AsyncSession,
        table_name: str,
        record_id: str,
    ) -> list[dict]:
        """특정 레코드의 전체 변경 이력 조회"""
        return await self.repo.get_record_history(session, table_name, record_id)
