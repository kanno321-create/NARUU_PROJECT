"""
KIS ERP - 거래명세서 관리 API
거래명세서 발행/조회/수정/삭제 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from pydantic import BaseModel

from api.db import get_db

from kis_erp_core.services.statement_service import StatementService

router = APIRouter(prefix="/statements", tags=["ERP - 거래명세서"])


# ==================== Pydantic 모델 ====================


class StatementCreate(BaseModel):
    """거래명세서 생성 요청"""
    statement_date: date
    customer_id: str
    voucher_ids: list[str] = []
    memo: Optional[str] = None


class StatementUpdate(BaseModel):
    """거래명세서 수정 요청"""
    statement_date: Optional[date] = None
    customer_id: Optional[str] = None
    voucher_ids: Optional[list[str]] = None
    memo: Optional[str] = None


class StatementResponse(BaseModel):
    """거래명세서 응답"""
    id: str
    statement_no: str
    statement_date: date
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    supply_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "draft"
    voucher_ids: list[str] = []
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== 거래명세서 API ====================


@router.get(
    "",
    response_model=List[StatementResponse],
    summary="거래명세서 목록 조회",
)
async def list_statements(
    statement_type: Optional[str] = Query(
        None, description="유형 (sales/purchase) - 연결된 전표 타입 기준"
    ),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[StatementResponse]:
    """
    거래명세서 목록을 조회합니다.

    statement_type 필터는 테이블 컬럼이 아닌
    연결된 전표의 voucher_type을 기준으로 필터링합니다.
    """
    service = StatementService()
    results = await service.list_statements(
        db,
        statement_type=statement_type,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [StatementResponse(**r) for r in results]


@router.post(
    "",
    response_model=StatementResponse,
    status_code=201,
    summary="거래명세서 생성",
)
async def create_statement(
    body: StatementCreate,
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    새 거래명세서를 생성합니다.

    voucher_ids를 지정하면 해당 전표들의 금액이 자동 합산됩니다.
    거래명세서 번호는 연결된 전표 타입에 따라 SS-/SP- 접두사로 자동 생성됩니다.
    """
    service = StatementService()
    data = body.model_dump()
    result = await service.create_statement(db, data)
    await db.commit()
    return StatementResponse(**result)


@router.post(
    "/from-voucher/{voucher_id}",
    response_model=StatementResponse,
    status_code=201,
    summary="전표에서 거래명세서 생성",
)
async def create_statement_from_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    전표(매출/매입)에서 거래명세서를 자동 생성합니다.

    전표의 거래처, 금액 정보가 자동으로 복사되며
    전표-거래명세서 연결이 생성됩니다.
    """
    service = StatementService()
    result = await service.create_from_voucher(db, voucher_id)
    if result is None:
        raise HTTPException(status_code=404, detail="전표를 찾을 수 없습니다")
    await db.commit()
    return StatementResponse(**result)


@router.get(
    "/{statement_id}",
    response_model=StatementResponse,
    summary="거래명세서 상세 조회",
)
async def get_statement(
    statement_id: str,
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    거래명세서 상세 정보를 조회합니다.
    """
    service = StatementService()
    result = await service.get_statement(db, statement_id)
    if result is None:
        raise HTTPException(status_code=404, detail="거래명세서를 찾을 수 없습니다")
    return StatementResponse(**result)


@router.put(
    "/{statement_id}",
    response_model=StatementResponse,
    summary="거래명세서 수정",
)
async def update_statement(
    statement_id: str,
    body: StatementUpdate,
    db: AsyncSession = Depends(get_db),
) -> StatementResponse:
    """
    거래명세서를 수정합니다.

    draft 상태인 거래명세서만 수정 가능합니다.
    voucher_ids를 변경하면 금액이 자동 재계산됩니다.
    """
    service = StatementService()

    # 존재 여부 확인
    existing = await service.get_statement(db, statement_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="거래명세서를 찾을 수 없습니다")

    if existing["status"] != "draft":
        raise HTTPException(
            status_code=400,
            detail="draft 상태인 거래명세서만 수정할 수 있습니다",
        )

    update_data = body.model_dump(exclude_unset=True)
    result = await service.update_statement(db, statement_id, update_data)

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="거래명세서 수정에 실패했습니다 (draft 상태가 아닐 수 있습니다)",
        )

    await db.commit()
    return StatementResponse(**result)


@router.delete(
    "/{statement_id}",
    status_code=204,
    summary="거래명세서 삭제",
)
async def delete_statement(
    statement_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    거래명세서를 삭제합니다.

    draft 상태인 거래명세서만 삭제 가능합니다.
    연결된 전표-거래명세서 관계도 CASCADE로 함께 삭제됩니다.
    """
    service = StatementService()

    # 존재 여부 확인
    existing = await service.get_statement(db, statement_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="거래명세서를 찾을 수 없습니다")

    if existing["status"] != "draft":
        raise HTTPException(
            status_code=400,
            detail="draft 상태인 거래명세서만 삭제할 수 있습니다",
        )

    deleted = await service.delete_statement(db, statement_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="거래명세서 삭제에 실패했습니다")
    await db.commit()
