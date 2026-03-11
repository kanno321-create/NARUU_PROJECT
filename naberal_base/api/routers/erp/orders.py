"""
KIS ERP - 발주서 관리 API
발주서 CRUD + 상태 관리 (draft→sent→confirmed→received, draft/sent→cancelled)
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.db import get_db
from kis_erp_core.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["ERP - 발주서"])


# ==================== Request/Response Models ====================


class OrderItemCreate(BaseModel):
    """발주서 항목 생성 요청"""
    product_id: Optional[str] = None
    product_name: str
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: float = 1
    unit_price: float = 0
    memo: Optional[str] = None


class OrderCreate(BaseModel):
    """발주서 생성 요청"""
    order_date: date
    supplier_id: str
    delivery_date: Optional[date] = None
    items: list[OrderItemCreate] = []
    memo: Optional[str] = None


class OrderUpdate(BaseModel):
    """발주서 수정 요청"""
    order_date: Optional[date] = None
    supplier_id: Optional[str] = None
    delivery_date: Optional[date] = None
    items: Optional[list[OrderItemCreate]] = None
    memo: Optional[str] = None


class OrderItemResponse(BaseModel):
    """발주서 항목 응답"""
    id: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    spec: Optional[str] = None
    unit: str = "EA"
    quantity: float = 0
    unit_price: float = 0
    amount: float = 0
    memo: Optional[str] = None


class OrderResponse(BaseModel):
    """발주서 응답"""
    id: str
    order_no: str
    order_date: date
    supplier_id: str
    supplier_name: Optional[str] = None
    delivery_date: Optional[date] = None
    total_amount: float = 0.0
    status: str = "draft"
    items: list[OrderItemResponse] = []
    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== 발주서 CRUD ====================


@router.get("", response_model=List[OrderResponse], summary="발주서 목록 조회")
async def list_orders(
    status: Optional[str] = Query(None, description="상태 (draft/sent/confirmed/received/cancelled)"),
    supplier_id: Optional[str] = Query(None, description="공급처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[OrderResponse]:
    """
    발주서 목록을 조회합니다.

    - **status**: draft/sent/confirmed/received/cancelled
    - **supplier_id**: 공급처 ID 필터
    - **start_date/end_date**: 발주일자 기간 필터
    """
    service = OrderService()
    results = await service.list_orders(
        db,
        status=status,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [OrderResponse(**r) for r in results]


@router.post(
    "", response_model=OrderResponse, status_code=201, summary="발주서 생성"
)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    새 발주서를 생성합니다.

    - 발주번호(PO-YYYYMMDD-NNNN) 자동 생성
    - 항목별 금액(quantity x unit_price) 자동 계산
    - 합계(total_amount) 자동 집계
    """
    service = OrderService()
    order_data = {
        "order_date": data.order_date,
        "supplier_id": data.supplier_id,
        "delivery_date": data.delivery_date,
        "memo": data.memo,
        "items": [item.model_dump() for item in data.items],
    }
    result = await service.create_order(db, order_data)
    await db.commit()
    return OrderResponse(**result)


@router.get(
    "/{order_id}", response_model=OrderResponse, summary="발주서 상세 조회"
)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """발주서 상세 정보를 조회합니다. (항목 포함)"""
    service = OrderService()
    result = await service.get_order(db, order_id)
    if not result:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    return OrderResponse(**result)


@router.put(
    "/{order_id}", response_model=OrderResponse, summary="발주서 수정"
)
async def update_order(
    order_id: str,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    발주서를 수정합니다. (draft/sent 상태만 수정 가능)

    items를 제공하면 기존 항목을 전부 교체합니다.
    """
    service = OrderService()
    update_data: dict = {}
    if data.order_date is not None:
        update_data["order_date"] = data.order_date
    if data.supplier_id is not None:
        update_data["supplier_id"] = data.supplier_id
    if data.delivery_date is not None:
        update_data["delivery_date"] = data.delivery_date
    if data.memo is not None:
        update_data["memo"] = data.memo
    if data.items is not None:
        update_data["items"] = [item.model_dump() for item in data.items]

    try:
        result = await service.update_order(db, order_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    await db.commit()
    return OrderResponse(**result)


@router.delete("/{order_id}", status_code=204, summary="발주서 삭제")
async def delete_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """발주서를 삭제합니다. (draft 상태만 삭제 가능)"""
    service = OrderService()
    try:
        deleted = await service.delete_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    await db.commit()


# ==================== 발주서 상태 관리 ====================


@router.post(
    "/{order_id}/confirm", response_model=OrderResponse, summary="발주 확정"
)
async def confirm_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    발주를 확정합니다. (sent → confirmed)

    공급처로부터 발주 확인을 받았을 때 사용합니다.
    """
    service = OrderService()
    try:
        result = await service.confirm_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    await db.commit()
    return OrderResponse(**result)


@router.post(
    "/{order_id}/receive", response_model=OrderResponse, summary="입고 처리"
)
async def receive_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    발주 물품을 입고 처리합니다. (confirmed → received)
    """
    service = OrderService()
    try:
        result = await service.receive_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    await db.commit()
    return OrderResponse(**result)


@router.post(
    "/{order_id}/cancel", response_model=OrderResponse, summary="발주 취소"
)
async def cancel_order(
    order_id: str,
    reason: str = Query(..., description="취소 사유"),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    발주를 취소합니다. (draft/sent → cancelled)

    취소 사유가 메모에 기록됩니다.
    """
    service = OrderService()
    try:
        result = await service.cancel_order(db, order_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="발주서를 찾을 수 없습니다")
    await db.commit()
    return OrderResponse(**result)
