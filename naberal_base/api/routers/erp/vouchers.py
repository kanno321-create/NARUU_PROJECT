"""
KIS ERP - 전표 관리 API
매출/매입/수금/지급/지출 전표 CRUD 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

from kis_erp_core.services.voucher_service import VoucherService
from kis_erp_core.models.voucher_models import (
    Voucher,
    VoucherCreate,
    VoucherUpdate,
    VoucherFilter,
    VoucherType,
    VoucherStatus,
)

router = APIRouter(prefix="/vouchers", tags=["ERP - 전표"])


# ==================== 전표 유형별 조회 (정적 경로 - 먼저 등록) ====================


@router.get("/sales", response_model=List[Voucher], summary="매출전표 목록 조회")
async def list_sales_vouchers(
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """매출전표 목록을 조회합니다."""
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=VoucherType.SALES,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


@router.get("/purchase", response_model=List[Voucher], summary="매입전표 목록 조회")
async def list_purchase_vouchers(
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """매입전표 목록을 조회합니다."""
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=VoucherType.PURCHASE,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


@router.get("/receipt", response_model=List[Voucher], summary="수금전표 목록 조회")
async def list_receipt_vouchers(
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """수금전표 목록을 조회합니다."""
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=VoucherType.RECEIPT,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


@router.get("/payment", response_model=List[Voucher], summary="지급전표 목록 조회")
async def list_payment_vouchers(
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """지급전표 목록을 조회합니다."""
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=VoucherType.PAYMENT,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


@router.get("/expense", response_model=List[Voucher], summary="지출전표 목록 조회")
async def list_expense_vouchers(
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """지출전표 목록을 조회합니다."""
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=VoucherType.EXPENSE,
        status=status,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


# ==================== 전표 유형별 생성 ====================


@router.post(
    "/sales", response_model=Voucher, status_code=201, summary="매출전표 생성"
)
async def create_sales_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """매출전표를 생성합니다. voucher_type이 자동으로 sales로 설정됩니다."""
    data.voucher_type = VoucherType.SALES
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


@router.post(
    "/purchase", response_model=Voucher, status_code=201, summary="매입전표 생성"
)
async def create_purchase_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """매입전표를 생성합니다. voucher_type이 자동으로 purchase로 설정됩니다."""
    data.voucher_type = VoucherType.PURCHASE
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


@router.post(
    "/receipt", response_model=Voucher, status_code=201, summary="수금전표 생성"
)
async def create_receipt_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """수금전표를 생성합니다. voucher_type이 자동으로 receipt로 설정됩니다."""
    data.voucher_type = VoucherType.RECEIPT
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


@router.post(
    "/payment", response_model=Voucher, status_code=201, summary="지급전표 생성"
)
async def create_payment_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """지급전표를 생성합니다. voucher_type이 자동으로 payment로 설정됩니다."""
    data.voucher_type = VoucherType.PAYMENT
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


@router.post(
    "/expense", response_model=Voucher, status_code=201, summary="지출전표 생성"
)
async def create_expense_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """지출(경비) 전표를 생성합니다. voucher_type이 자동으로 expense로 설정됩니다."""
    data.voucher_type = VoucherType.EXPENSE
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


# ==================== 전표 CRUD (범용 엔드포인트) ====================


@router.get("", response_model=List[Voucher], summary="전표 목록 조회")
async def list_vouchers(
    voucher_type: Optional[VoucherType] = Query(None, description="전표 유형"),
    status: Optional[VoucherStatus] = Query(None, description="전표 상태"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어 (전표번호, 메모)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Voucher]:
    """
    전표 목록을 조회합니다.

    - **voucher_type**: sales/purchase/receipt/payment/expense
    - **status**: draft/confirmed/cancelled
    - **start_date/end_date**: 기간 필터
    - **search**: 전표번호 또는 메모 검색
    """
    service = VoucherService()
    filters = VoucherFilter(
        voucher_type=voucher_type,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    results = await service.list_vouchers(db, filters, skip, limit)
    return [Voucher(**r) for r in results]


@router.post(
    "", response_model=Voucher, status_code=201, summary="전표 생성"
)
async def create_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """
    새 전표를 생성합니다.

    필수 항목:
    - **voucher_type**: 전표 유형
    - **voucher_date**: 전표일자
    - **items**: 전표 항목 (1개 이상, 상품명/수량/단가 필수)

    금액 자동 계산:
    - supply_price = quantity x unit_price
    - tax_amount = supply_price x 0.1
    - total_amount = supply_price + tax_amount
    """
    service = VoucherService()
    result = await service.create_voucher(db, data)
    await db.commit()
    return Voucher(**result)


@router.get(
    "/{voucher_id}", response_model=Voucher, summary="전표 상세 조회"
)
async def get_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """전표 상세 정보를 조회합니다. (전표 항목 포함)"""
    service = VoucherService()
    result = await service.get_voucher(db, voucher_id)
    if not result:
        raise HTTPException(status_code=404, detail="전표를 찾을 수 없습니다")
    return Voucher(**result)


@router.put(
    "/{voucher_id}", response_model=Voucher, summary="전표 수정"
)
async def update_voucher(
    voucher_id: str,
    data: VoucherUpdate,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """
    전표를 수정합니다. (draft 상태만 수정 가능)

    items를 제공하면 기존 항목을 전부 교체합니다.
    """
    service = VoucherService()
    try:
        result = await service.update_voucher(db, voucher_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="전표를 찾을 수 없습니다")
    await db.commit()
    return Voucher(**result)


@router.delete("/{voucher_id}", status_code=204, summary="전표 삭제")
async def delete_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """전표를 삭제합니다. (draft 상태만 삭제 가능)"""
    service = VoucherService()
    try:
        deleted = await service.delete_voucher(db, voucher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="전표를 찾을 수 없습니다")
    await db.commit()


# ==================== 전표 상태 관리 ====================


@router.post(
    "/{voucher_id}/confirm", response_model=Voucher, summary="전표 확정"
)
async def confirm_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """
    전표를 확정합니다. (draft → confirmed)

    확정 시:
    - 자동 분개(Journal Entry) 생성 + 즉시 전기
    - 수정 불가 상태로 변경
    """
    service = VoucherService()
    try:
        result = await service.confirm_voucher(db, voucher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return Voucher(**result)


@router.post(
    "/{voucher_id}/cancel", response_model=Voucher, summary="전표 취소"
)
async def cancel_voucher(
    voucher_id: str,
    db: AsyncSession = Depends(get_db),
) -> Voucher:
    """
    확정된 전표를 취소합니다. (confirmed → cancelled)

    취소 시:
    - 연결된 분개를 cancelled 처리
    - 역분개 자동 생성 + 전기
    """
    service = VoucherService()
    try:
        result = await service.cancel_voucher(db, voucher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return Voucher(**result)
