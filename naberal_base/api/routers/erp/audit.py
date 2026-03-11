"""
KIS ERP - 감사추적 API (Phase 5: Audit Trail)
감사 로그 조회 2개 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from kis_erp_core.services.audit_service import AuditService

# ==================== Pydantic Models ====================


class AuditLogResponse(BaseModel):
    """감사 로그 응답"""
    id: str
    table_name: str
    record_id: str
    action: str
    changed_by: Optional[str] = None
    changed_at: Optional[datetime] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    ip_address: Optional[str] = None
    description: Optional[str] = None


# ==================== Router ====================

router = APIRouter(prefix="/audit", tags=["ERP - 감사추적"])


@router.get(
    "",
    response_model=list[AuditLogResponse],
    summary="감사 로그 목록 조회",
)
async def list_audit_logs(
    table_name: str | None = Query(None, description="테이블명 필터"),
    record_id: str | None = Query(None, description="레코드 ID 필터"),
    action: str | None = Query(None, description="액션 필터 (INSERT/UPDATE/DELETE)"),
    start_date: str | None = Query(None, description="시작일 (ISO 8601)"),
    end_date: str | None = Query(None, description="종료일 (ISO 8601)"),
    skip: int = Query(0, ge=0, description="건너뛸 행 수"),
    limit: int = Query(50, ge=1, le=200, description="최대 반환 행 수"),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    """
    감사 로그를 조회합니다.
    테이블명, 레코드 ID, 액션, 날짜 범위로 필터링할 수 있습니다.
    """
    service = AuditService()
    results = await service.list_logs(
        db,
        table_name=table_name,
        record_id=record_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [AuditLogResponse(**r) for r in results]


@router.get(
    "/{table_name}/{record_id}",
    response_model=list[AuditLogResponse],
    summary="레코드 변경 이력 조회",
)
async def get_record_history(
    table_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    """
    특정 테이블의 특정 레코드에 대한 전체 변경 이력을 조회합니다.
    최신 변경 순으로 반환됩니다.
    """
    service = AuditService()
    results = await service.get_record_history(db, table_name, record_id)
    return [AuditLogResponse(**r) for r in results]
