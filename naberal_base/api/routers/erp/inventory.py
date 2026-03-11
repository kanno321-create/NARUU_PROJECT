"""
KIS ERP - 재고 관리 API
재고현황, 재고조정, 재고이동 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock

Phase 3-C: LEAN rebuild - 6 endpoints only
- GET  /inventory/status          재고현황 목록
- GET  /inventory/status/{id}     단일 상품 재고
- GET  /inventory/summary         재고현황 요약
- GET  /inventory/adjustments     재고조정 내역
- POST /inventory/adjustments     재고조정 등록
- GET  /inventory/movements       재고이동 내역
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.db import get_db
from kis_erp_core.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["ERP - 재고관리"])


# ==================== Request/Response Models ====================


class InventoryStatusResponse(BaseModel):
    """재고현황 응답"""
    product_id: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit: str = "EA"
    quantity: float = 0
    unit_cost: float = 0
    total_cost: float = 0
    min_stock: float = 0
    is_low_stock: bool = False


class InventorySummaryResponse(BaseModel):
    """재고현황 요약 응답"""
    total_products: int = 0
    total_value: float = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0


class AdjustmentCreate(BaseModel):
    """재고조정 등록 요청"""
    adjustment_date: date
    adjustment_type: str  # increase/decrease/set
    product_id: str
    adjustment_quantity: float
    reason: str
    memo: Optional[str] = None


class AdjustmentResponse(BaseModel):
    """재고조정 응답"""
    id: str
    adjustment_no: str
    adjustment_date: date
    adjustment_type: str
    product_id: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    before_quantity: float = 0
    adjustment_quantity: float
    after_quantity: float = 0
    reason: str
    memo: Optional[str] = None
    created_at: Optional[datetime] = None


class MovementResponse(BaseModel):
    """재고이동 응답"""
    id: str
    movement_date: date
    movement_type: str
    product_id: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity: float
    unit_cost: float = 0
    reason: Optional[str] = None
    before_qty: float = 0
    after_qty: float = 0
    created_at: Optional[datetime] = None


class MovementListResponse(BaseModel):
    """재고이동 목록 응답 (summary 포함)"""
    movements: List[MovementResponse]
    summary: dict


# ==================== 재고현황 API ====================


@router.get(
    "/status",
    response_model=List[InventoryStatusResponse],
    summary="재고현황 조회",
)
async def get_inventory_status(
    category: Optional[str] = Query(None, description="카테고리"),
    low_stock_only: bool = Query(False, description="재고부족만"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[InventoryStatusResponse]:
    """
    전체 재고현황을 조회합니다.

    - **category**: 카테고리별 필터
    - **low_stock_only**: true면 재고부족 상품만 조회
    """
    service = InventoryService()
    results = await service.list_status(
        db,
        category=category,
        low_stock_only=low_stock_only,
        skip=skip,
        limit=limit,
    )
    return [InventoryStatusResponse(**r) for r in results]


@router.get(
    "/status/{product_id}",
    response_model=InventoryStatusResponse,
    summary="상품별 재고 조회",
)
async def get_product_inventory(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> InventoryStatusResponse:
    """특정 상품의 재고현황을 조회합니다."""
    service = InventoryService()
    result = await service.get_product_status(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return InventoryStatusResponse(**result)


@router.get(
    "/summary",
    response_model=InventorySummaryResponse,
    summary="재고현황 요약",
)
async def get_inventory_summary(
    db: AsyncSession = Depends(get_db),
) -> InventorySummaryResponse:
    """재고현황 요약 정보를 조회합니다. (총 상품수, 총 재고가치, 부족/품절 수)"""
    service = InventoryService()
    result = await service.get_summary(db)
    return InventorySummaryResponse(**result)


# ==================== 재고조정 API ====================


@router.get(
    "/adjustments",
    response_model=List[AdjustmentResponse],
    summary="재고조정 내역 조회",
)
async def list_adjustments(
    product_id: Optional[str] = Query(None, description="상품 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[AdjustmentResponse]:
    """
    재고조정 내역을 조회합니다.

    - **product_id**: 특정 상품의 조정 내역만 필터
    - **start_date/end_date**: 기간 필터
    """
    service = InventoryService()
    results = await service.list_adjustments(
        db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [AdjustmentResponse(**r) for r in results]


@router.post(
    "/adjustments",
    response_model=AdjustmentResponse,
    status_code=201,
    summary="재고조정 등록",
)
async def create_adjustment(
    body: AdjustmentCreate,
    db: AsyncSession = Depends(get_db),
) -> AdjustmentResponse:
    """
    재고를 조정합니다.

    조정유형:
    - **increase**: 수량 증가 (입고, 반품 등)
    - **decrease**: 수량 감소 (출고, 폐기 등)
    - **set**: 수량 직접 설정 (실사 반영)

    자동 처리:
    - 조정번호(ADJ-YYYYMMDD-NNNN) 자동 생성
    - before/after 수량 자동 계산
    - 재고이동(inventory_movements) 자동 기록 → DB trigger가 상품 재고 갱신
    """
    service = InventoryService()
    data = body.model_dump()
    try:
        result = await service.create_adjustment(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return AdjustmentResponse(**result)


# ==================== 재고이동 API ====================


@router.get(
    "/movements",
    response_model=MovementListResponse,
    summary="재고이동 내역 조회",
)
async def get_inventory_movements(
    product_id: Optional[str] = Query(None, description="상품 ID"),
    movement_type: Optional[str] = Query(None, description="이동유형 (in/out/adjust)"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> MovementListResponse:
    """
    재고이동(입출고) 내역을 조회합니다.

    - **movement_type**: in(입고), out(출고), adjust(조정)
    - **product_id**: 특정 상품의 이동 내역만 필터
    - **start_date/end_date**: 기간 필터

    응답에 summary(total_in, total_out, net_change) 포함.
    """
    service = InventoryService()
    result = await service.list_movements(
        db,
        product_id=product_id,
        movement_type=movement_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    movements = [MovementResponse(**m) for m in result["movements"]]
    return MovementListResponse(movements=movements, summary=result["summary"])
