"""
KIS ERP - 기초이월 API
회계연도 시작 시 재고/잔액/현금 이월 처리 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from api.db import get_db
from kis_erp_core.services.carryover_service import CarryoverService

router = APIRouter(prefix="/carryover", tags=["ERP - 기초이월"])

svc = CarryoverService()


# ==================== Pydantic Request/Response Models ====================


class StockCarryoverCreate(BaseModel):
    fiscal_year: int
    product_id: str
    quantity: float
    unit_cost: float
    carryover_date: Optional[date] = None


class StockCarryoverResponse(BaseModel):
    id: str
    fiscal_year: int
    product_id: str
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    quantity: float
    unit_cost: float
    total_value: float
    carryover_date: date
    created_at: Optional[datetime] = None


class BalanceCarryoverCreate(BaseModel):
    fiscal_year: int
    customer_id: str
    balance_type: str  # receivable / payable
    amount: float
    carryover_date: Optional[date] = None


class BalanceCarryoverResponse(BaseModel):
    id: str
    fiscal_year: int
    customer_id: str
    customer_name: Optional[str] = None
    balance_type: str
    amount: float
    carryover_date: date
    created_at: Optional[datetime] = None


class CashCarryoverCreate(BaseModel):
    fiscal_year: int
    account_id: Optional[str] = None
    amount: float
    carryover_date: Optional[date] = None


class CashCarryoverResponse(BaseModel):
    id: str
    fiscal_year: int
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    amount: float
    carryover_date: date
    created_at: Optional[datetime] = None


# ==================== 상품재고 이월 ====================


@router.get(
    "/stock",
    response_model=List[StockCarryoverResponse],
    summary="재고이월 목록 조회",
)
async def list_stock_carryovers(
    fiscal_year: int = Query(..., description="회계연도"),
    product_id: Optional[str] = Query(None, description="상품 ID"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """상품재고 이월 내역을 조회합니다."""
    return await svc.list_stock(db, fiscal_year, product_id)


@router.post(
    "/stock",
    response_model=StockCarryoverResponse,
    status_code=201,
    summary="재고이월 등록",
)
async def create_stock_carryover(
    body: StockCarryoverCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    상품재고 이월을 등록합니다.

    회계연도 시작 시 전년도 재고를 이월 처리합니다.
    """
    data = body.model_dump()
    result = await svc.create_stock(db, data)
    await db.commit()
    return result


@router.post(
    "/stock/bulk",
    response_model=List[StockCarryoverResponse],
    status_code=201,
    summary="재고이월 일괄 등록",
)
async def bulk_create_stock_carryovers(
    items: List[StockCarryoverCreate],
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """상품재고 이월을 일괄 등록합니다."""
    data_list = [item.model_dump() for item in items]
    result = await svc.create_stock_bulk(db, data_list)
    await db.commit()
    return result


@router.delete("/stock/{carryover_id}", status_code=204, summary="재고이월 삭제")
async def delete_stock_carryover(
    carryover_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """재고이월 내역을 삭제합니다."""
    deleted = await svc.delete_stock(db, carryover_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="재고이월 내역을 찾을 수 없습니다")
    await db.commit()


# ==================== 미수/미지급금 이월 ====================


@router.get(
    "/balance",
    response_model=List[BalanceCarryoverResponse],
    summary="잔액이월 목록 조회",
)
async def list_balance_carryovers(
    fiscal_year: int = Query(..., description="회계연도"),
    balance_type: Optional[str] = Query(
        None, description="잔액유형 (receivable/payable)"
    ),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    미수금/미지급금 이월 내역을 조회합니다.

    - **balance_type**: receivable(미수금), payable(미지급금)
    """
    return await svc.list_balance(db, fiscal_year, balance_type, customer_id)


@router.post(
    "/balance",
    response_model=BalanceCarryoverResponse,
    status_code=201,
    summary="잔액이월 등록",
)
async def create_balance_carryover(
    body: BalanceCarryoverCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    미수금/미지급금 이월을 등록합니다.

    회계연도 시작 시 전년도 미수금/미지급금을 이월 처리합니다.
    """
    if body.balance_type not in ("receivable", "payable"):
        raise HTTPException(
            status_code=400,
            detail="balance_type은 'receivable' 또는 'payable'이어야 합니다",
        )
    data = body.model_dump()
    result = await svc.create_balance(db, data)
    await db.commit()
    return result


@router.post(
    "/balance/bulk",
    response_model=List[BalanceCarryoverResponse],
    status_code=201,
    summary="잔액이월 일괄 등록",
)
async def bulk_create_balance_carryovers(
    items: List[BalanceCarryoverCreate],
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """미수금/미지급금 이월을 일괄 등록합니다."""
    for item in items:
        if item.balance_type not in ("receivable", "payable"):
            raise HTTPException(
                status_code=400,
                detail="balance_type은 'receivable' 또는 'payable'이어야 합니다",
            )
    data_list = [item.model_dump() for item in items]
    result = await svc.create_balance_bulk(db, data_list)
    await db.commit()
    return result


@router.delete("/balance/{carryover_id}", status_code=204, summary="잔액이월 삭제")
async def delete_balance_carryover(
    carryover_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """잔액이월 내역을 삭제합니다."""
    deleted = await svc.delete_balance(db, carryover_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="잔액이월 내역을 찾을 수 없습니다")
    await db.commit()


# ==================== 현금잔고 이월 ====================


@router.get(
    "/cash",
    response_model=List[CashCarryoverResponse],
    summary="현금이월 목록 조회",
)
async def list_cash_carryovers(
    fiscal_year: int = Query(..., description="회계연도"),
    account_id: Optional[str] = Query(None, description="계좌 ID"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """현금/예금 잔고 이월 내역을 조회합니다."""
    return await svc.list_cash(db, fiscal_year, account_id)


@router.post(
    "/cash",
    response_model=CashCarryoverResponse,
    status_code=201,
    summary="현금이월 등록",
)
async def create_cash_carryover(
    body: CashCarryoverCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    현금/예금 잔고 이월을 등록합니다.

    - **account_id**: None이면 현금, 값이 있으면 해당 계좌
    """
    data = body.model_dump()
    result = await svc.create_cash(db, data)
    await db.commit()
    return result


@router.post(
    "/cash/bulk",
    response_model=List[CashCarryoverResponse],
    status_code=201,
    summary="현금이월 일괄 등록",
)
async def bulk_create_cash_carryovers(
    items: List[CashCarryoverCreate],
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """현금/예금 잔고 이월을 일괄 등록합니다."""
    data_list = [item.model_dump() for item in items]
    result = await svc.create_cash_bulk(db, data_list)
    await db.commit()
    return result


@router.delete("/cash/{carryover_id}", status_code=204, summary="현금이월 삭제")
async def delete_cash_carryover(
    carryover_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """현금이월 내역을 삭제합니다."""
    deleted = await svc.delete_cash(db, carryover_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="현금이월 내역을 찾을 수 없습니다")
    await db.commit()


# ==================== 자동 이월 처리 ====================


@router.post("/auto-generate", summary="기초이월 자동 생성")
async def auto_generate_carryovers(
    fiscal_year: int = Query(..., description="새 회계연도"),
    carryover_date: Optional[date] = Query(
        None, description="이월일자 (기본: 회계연도 1월 1일)"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    전년도 데이터 기반으로 기초이월을 자동 생성합니다.

    처리 항목:
    1. 상품재고 이월: 현재 재고 수량 x 원가
    2. 미수금 이월: 거래처별 미수금 잔액
    3. 미지급금 이월: 거래처별 미지급금 잔액
    4. 현금/예금 이월: 계좌별 잔액
    """
    actual_date = carryover_date or date(fiscal_year, 1, 1)
    counts = await svc.auto_generate(db, fiscal_year, actual_date)
    await db.commit()

    return {
        "fiscal_year": fiscal_year,
        "carryover_date": str(actual_date),
        "status": "completed",
        "message": "기초이월 자동 생성 완료",
        "created": counts,
    }


@router.get("/summary/{fiscal_year}", summary="기초이월 현황 요약")
async def get_carryover_summary(
    fiscal_year: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """해당 회계연도의 기초이월 현황을 요약 조회합니다."""
    return await svc.summary(db, fiscal_year)
