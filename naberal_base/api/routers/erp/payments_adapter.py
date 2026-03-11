"""
KIS ERP - 수금/지급 어댑터 API
프론트엔드 /v1/erp/payments 경로를 백엔드 vouchers 서비스로 위임
payment_type으로 receipt(수금)/payment(지급)/expense(지출) 구분
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

from kis_erp_core.services.voucher_service import VoucherService
from kis_erp_core.models.voucher_models import (
    Voucher,
    VoucherCreate,
    VoucherFilter,
    VoucherType,
    VoucherStatus,
)

router = APIRouter(prefix="/payments", tags=["ERP - 수금/지급 (어댑터)"])

# payment_type → VoucherType 매핑
_PAYMENT_TYPE_MAP = {
    "receipt": VoucherType.RECEIPT,
    "collection": VoucherType.RECEIPT,
    "deposit": VoucherType.RECEIPT,
    "payment": VoucherType.PAYMENT,
    "disbursement": VoucherType.PAYMENT,
    "withdrawal": VoucherType.PAYMENT,
    "expense": VoucherType.EXPENSE,
}


def _voucher_to_payment(v: Voucher) -> dict:
    """Voucher → 프론트엔드 ERPPayment 형태로 변환"""
    # voucher_type → payment_type 역매핑
    type_map = {
        "receipt": "receipt",
        "payment": "payment",
        "expense": "expense",
    }
    payment_type = type_map.get(v.voucher_type, v.voucher_type)

    return {
        "id": v.id,
        "payment_number": v.voucher_no,
        "payment_type": payment_type,
        "payment_date": str(v.voucher_date),
        "customer_id": v.customer_id or "",
        "amount": v.total_amount,
        "payment_method": v.payment_method or "cash",
        "status": v.status,
        "completed_date": None,
        "reference_type": None,
        "reference_id": None,
        "memo": v.memo,
        "customer": None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }


@router.get("", summary="수금/지급전표 목록 조회")
async def list_payments(
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    payment_type: Optional[str] = Query(None, description="유형 (receipt/payment/expense)"),
    status: Optional[str] = Query(None, description="전표 상태"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """수금/지급/지출 전표 목록을 프론트엔드 ERPPayment 형태로 반환합니다."""
    try:
        service = VoucherService()
        voucher_status = VoucherStatus(status) if status else None
        voucher_type = _PAYMENT_TYPE_MAP.get(payment_type) if payment_type else None

        # payment_type 미지정이면 receipt + payment + expense 모두 조회
        total_count = 0
        if voucher_type:
            filters = VoucherFilter(
                voucher_type=voucher_type,
                status=voucher_status,
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                search=search,
            )
            results = await service.list_vouchers(db, filters, skip, limit)
            vouchers = [Voucher(**r) for r in results]
            total_count = len(vouchers)
        else:
            all_vouchers = []
            for vtype in [VoucherType.RECEIPT, VoucherType.PAYMENT, VoucherType.EXPENSE]:
                filters = VoucherFilter(
                    voucher_type=vtype,
                    status=voucher_status,
                    customer_id=customer_id,
                    start_date=start_date,
                    end_date=end_date,
                    search=search,
                )
                results = await service.list_vouchers(db, filters, 0, 1000)
                all_vouchers.extend([Voucher(**r) for r in results])
            total_count = len(all_vouchers)
            vouchers = all_vouchers[skip:skip + limit]

        return {
            "items": [_voucher_to_payment(v) for v in vouchers],
            "total": total_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수금/지급전표 조회 실패: {str(e)}")


@router.post("", status_code=201, summary="수금/지급전표 생성")
async def create_payment(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """프론트엔드 ERPPaymentCreate 형태를 받아 VoucherCreate로 변환하여 생성합니다."""
    try:
        from kis_erp_core.models.voucher_models import VoucherItemCreate

        payment_type_str = data.get("payment_type", "receipt")
        voucher_type = _PAYMENT_TYPE_MAP.get(payment_type_str, VoucherType.RECEIPT)

        amount = data.get("amount", 0)
        payment_method_str = data.get("payment_method")

        # 수금/지급은 단일 항목으로 처리
        voucher_items = [
            VoucherItemCreate(
                product_name=f"{'수금' if voucher_type == VoucherType.RECEIPT else '지급' if voucher_type == VoucherType.PAYMENT else '지출'}",
                unit="건",
                quantity=1,
                unit_price=amount,
                memo=data.get("memo"),
            )
        ]

        # payment_method 매핑 (영문 + 한글 모두 지원)
        from kis_erp_core.models.voucher_models import PaymentMethod
        pm = None
        if payment_method_str:
            pm_map = {
                "cash": PaymentMethod.CASH,
                "현금": PaymentMethod.CASH,
                "card": PaymentMethod.CARD,
                "카드": PaymentMethod.CARD,
                "bank_transfer": PaymentMethod.BANK_TRANSFER,
                "계좌이체": PaymentMethod.BANK_TRANSFER,
                "은행": PaymentMethod.BANK_TRANSFER,
                "check": PaymentMethod.CHECK,
                "수표": PaymentMethod.CHECK,
                "note": PaymentMethod.NOTE,
                "어음": PaymentMethod.NOTE,
            }
            pm = pm_map.get(payment_method_str)

        voucher_data = VoucherCreate(
            voucher_type=voucher_type,
            voucher_date=date.fromisoformat(data.get("payment_date", str(date.today()))),
            customer_id=data.get("customer_id"),
            payment_method=pm,
            memo=data.get("memo"),
            items=voucher_items,
        )

        service = VoucherService()
        result = await service.create_voucher(db, voucher_data)
        await db.commit()

        voucher = Voucher(**result)

        if data.get("status") == "confirmed":
            try:
                confirmed = await service.confirm_voucher(db, voucher.id)
                await db.commit()
                voucher = Voucher(**confirmed)
            except ValueError:
                pass

        return _voucher_to_payment(voucher)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수금/지급전표 생성 실패: {str(e)}")
