"""
KIS ERP - 매출 어댑터 API
프론트엔드 /v1/erp/sales 경로를 백엔드 vouchers 서비스로 위임
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
    VoucherFilter,
    VoucherType,
    VoucherStatus,
)

router = APIRouter(prefix="/sales", tags=["ERP - 매출 (어댑터)"])


# ---------- 매출전표 FE 인터페이스에 맞춘 응답 변환 ----------

def _voucher_to_sale(v: Voucher) -> dict:
    """Voucher → 프론트엔드 ERPSale 형태로 변환"""
    items = []
    for item in (v.items or []):
        items.append({
            "product_id": getattr(item, "product_id", None),
            "product_code": None,
            "product_name": getattr(item, "product_name", ""),
            "spec": getattr(item, "spec", None),
            "unit": getattr(item, "unit", "EA"),
            "quantity": getattr(item, "quantity", 0),
            "unit_price": getattr(item, "unit_price", 0),
            "supply_amount": getattr(item, "supply_price", 0),
            "tax_amount": getattr(item, "tax_amount", 0),
            "total_amount": getattr(item, "total_amount", 0),
            "memo": getattr(item, "memo", None),
        })
    return {
        "id": v.id,
        "sale_number": v.voucher_no,
        "sale_date": str(v.voucher_date),
        "customer_id": v.customer_id or "",
        "status": v.status,
        "supply_amount": v.supply_amount,
        "tax_amount": v.tax_amount,
        "total_amount": v.total_amount,
        "cost_amount": 0,
        "profit_amount": 0,
        "memo": v.memo,
        "items": items,
        "customer": None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }


@router.get("", summary="매출전표 목록 조회")
async def list_sales(
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    status: Optional[str] = Query(None, description="전표 상태"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    search: Optional[str] = Query(None, description="검색어"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """매출전표 목록을 프론트엔드 ERPSale 형태로 반환합니다."""
    try:
        service = VoucherService()
        voucher_status = VoucherStatus(status) if status else None
        filters = VoucherFilter(
            voucher_type=VoucherType.SALES,
            status=voucher_status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        results = await service.list_vouchers(db, filters, skip, limit)
        vouchers = [Voucher(**r) for r in results]
        return {
            "items": [_voucher_to_sale(v) for v in vouchers],
            "total": len(vouchers),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매출전표 조회 실패: {str(e)}")


@router.post("", status_code=201, summary="매출전표 생성")
async def create_sale(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """프론트엔드 ERPSaleCreate 형태를 받아 VoucherCreate로 변환하여 생성합니다."""
    try:
        from kis_erp_core.models.voucher_models import VoucherItemCreate

        items_raw = data.get("items", [])
        voucher_items = []
        for item in items_raw:
            voucher_items.append(VoucherItemCreate(
                product_id=item.get("product_id"),
                product_name=item.get("product_name", ""),
                spec=item.get("spec"),
                unit=item.get("unit", "EA"),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
                memo=item.get("memo"),
            ))

        voucher_data = VoucherCreate(
            voucher_type=VoucherType.SALES,
            voucher_date=date.fromisoformat(data.get("sale_date", str(date.today()))),
            customer_id=data.get("customer_id"),
            memo=data.get("memo"),
            items=voucher_items,
        )

        service = VoucherService()
        result = await service.create_voucher(db, voucher_data)
        await db.commit()

        voucher = Voucher(**result)

        # 확정 상태 요청 시 자동 확정
        if data.get("status") == "confirmed":
            try:
                confirmed = await service.confirm_voucher(db, voucher.id)
                await db.commit()
                voucher = Voucher(**confirmed)
            except ValueError:
                pass  # 확정 실패는 무시 (이미 생성됨)

        return _voucher_to_sale(voucher)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매출전표 생성 실패: {str(e)}")


@router.get("/{sale_id}", summary="매출전표 상세 조회")
async def get_sale(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
):
    """매출전표 상세를 프론트엔드 ERPSale 형태로 반환합니다."""
    try:
        service = VoucherService()
        result = await service.get_voucher(db, sale_id)
        if not result:
            raise HTTPException(status_code=404, detail="매출전표를 찾을 수 없습니다")
        voucher = Voucher(**result)
        return _voucher_to_sale(voucher)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매출전표 조회 실패: {str(e)}")
