"""
KIS ERP - 세금계산서 API
프론트엔드 /v1/erp/tax-invoices 경로 대응
세금계산서 CRUD 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

import uuid
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.db import get_db

router = APIRouter(prefix="/tax-invoices", tags=["ERP - 세금계산서"])


def _row_to_dict(row) -> dict:
    """DB row → dict 변환"""
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if hasattr(row, "_asdict"):
        return row._asdict()
    return dict(row)


@router.get("", summary="세금계산서 목록 조회")
async def list_tax_invoices(
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    invoice_type: Optional[str] = Query(None, description="유형 (sales/purchase)"),
    status: Optional[str] = Query(None, description="상태 (draft/issued/cancelled)"),
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 목록을 조회합니다."""
    try:
        conditions = []
        params: dict = {"skip": skip, "limit": limit}

        if customer_id:
            conditions.append("ti.customer_id = :customer_id")
            params["customer_id"] = customer_id
        if invoice_type:
            conditions.append("ti.invoice_type = :invoice_type")
            params["invoice_type"] = invoice_type
        if status:
            conditions.append("ti.status = :status")
            params["status"] = status
        if start_date:
            conditions.append("ti.issue_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            conditions.append("ti.issue_date <= :end_date")
            params["end_date"] = end_date

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = text(f"""
            SELECT ti.*, c.name as customer_name
            FROM erp_tax_invoices ti
            LEFT JOIN erp_customers c ON ti.customer_id = c.id
            WHERE {where_clause}
            ORDER BY ti.issue_date DESC, ti.created_at DESC
            OFFSET :skip LIMIT :limit
        """)

        result = await db.execute(query, params)
        rows = result.fetchall()

        items = []
        for row in rows:
            d = _row_to_dict(row)
            items.append({
                "id": d.get("id", ""),
                "invoice_number": d.get("invoice_number"),
                "invoice_type": d.get("invoice_type", "sales"),
                "issue_date": str(d.get("issue_date", "")),
                "customer_id": d.get("customer_id", ""),
                "supply_amount": float(d.get("supply_amount", 0)),
                "tax_amount": float(d.get("tax_amount", 0)),
                "total_amount": float(d.get("total_amount", 0)),
                "status": d.get("status", "draft"),
                "reference_type": d.get("reference_type"),
                "reference_id": d.get("reference_id"),
                "memo": d.get("memo"),
                "customer": {"name": d.get("customer_name")} if d.get("customer_name") else None,
                "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
                "updated_at": d.get("updated_at").isoformat() if d.get("updated_at") else None,
            })

        return {"items": items, "total": len(items)}

    except Exception as e:
        # 테이블이 없을 경우 빈 결과 반환
        if "does not exist" in str(e) or "no such table" in str(e).lower():
            return {"items": [], "total": 0}
        raise HTTPException(status_code=500, detail=f"세금계산서 조회 실패: {str(e)}")


@router.post("", status_code=201, summary="세금계산서 생성")
async def create_tax_invoice(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서를 생성합니다."""
    try:
        invoice_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # 세금계산서 번호 생성 (TI-YYYYMMDD-XXX 형식)
        today = date.today()
        count_query = text("""
            SELECT COUNT(*) as cnt FROM erp_tax_invoices
            WHERE issue_date = :today
        """)
        try:
            count_result = await db.execute(count_query, {"today": today})
            count = count_result.scalar() or 0
        except Exception:
            count = 0

        invoice_number = f"TI-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(3)}"

        invoice_type = data.get("invoice_type", "sales")
        issue_date = data.get("issue_date", str(today))
        customer_id = data.get("customer_id", "")
        supply_amount = data.get("supply_amount", 0)
        tax_amount = data.get("tax_amount", 0)
        total_amount = data.get("total_amount", supply_amount + tax_amount)
        status = data.get("status", "draft")
        memo = data.get("memo")
        reference_type = data.get("reference_type")
        reference_id = data.get("reference_id")

        insert_query = text("""
            INSERT INTO erp_tax_invoices
            (id, invoice_number, invoice_type, issue_date, customer_id,
             supply_amount, tax_amount, total_amount, status,
             reference_type, reference_id, memo, created_at, updated_at)
            VALUES
            (:id, :invoice_number, :invoice_type, :issue_date, :customer_id,
             :supply_amount, :tax_amount, :total_amount, :status,
             :reference_type, :reference_id, :memo, :created_at, :updated_at)
        """)

        await db.execute(insert_query, {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "issue_date": issue_date,
            "customer_id": customer_id,
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "status": status,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "memo": memo,
            "created_at": now,
            "updated_at": now,
        })
        await db.commit()

        return {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "issue_date": str(issue_date),
            "customer_id": customer_id,
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "status": status,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "memo": memo,
            "customer": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        # 테이블이 없으면 안내
        if "does not exist" in str(e) or "no such table" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="세금계산서 테이블(erp_tax_invoices)이 아직 생성되지 않았습니다.",
            )
        raise HTTPException(status_code=500, detail=f"세금계산서 생성 실패: {str(e)}")


@router.delete("/{invoice_id}", summary="세금계산서 삭제")
async def delete_tax_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서를 삭제합니다."""
    try:
        # 존재 여부 확인
        check_query = text("SELECT id FROM erp_tax_invoices WHERE id = :id")
        result = await db.execute(check_query, {"id": invoice_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="세금계산서를 찾을 수 없습니다.")

        delete_query = text("DELETE FROM erp_tax_invoices WHERE id = :id")
        await db.execute(delete_query, {"id": invoice_id})
        await db.commit()

        return {"message": "세금계산서가 삭제되었습니다.", "id": invoice_id}

    except HTTPException:
        raise
    except Exception as e:
        if "does not exist" in str(e) or "no such table" in str(e).lower():
            raise HTTPException(status_code=503, detail="세금계산서 테이블이 존재하지 않습니다.")
        raise HTTPException(status_code=500, detail=f"세금계산서 삭제 실패: {str(e)}")


@router.get("/unissued-customers", summary="미발행 거래처 조회")
async def get_unissued_customers(
    start_date: date = Query(..., description="매출 시작일"),
    end_date: date = Query(..., description="매출 종료일"),
    db: AsyncSession = Depends(get_db),
):
    """
    지정 기간에 매출이력이 있지만 세금계산서를 아직 발행하지 않은 거래처 목록을 조회합니다.
    매출이력이 있고, 세금계산서도 발행된 거래처는 제외됩니다.
    """
    try:
        query = text("""
            SELECT
                c.id as customer_id,
                c.name as customer_name,
                c.business_number,
                c.representative,
                COALESCE(SUM(s.total_amount), 0) as total_sales_amount,
                COALESCE(SUM(s.supply_amount), 0) as total_supply_amount,
                COALESCE(SUM(s.tax_amount), 0) as total_tax_amount,
                COUNT(s.id) as sale_count
            FROM erp_customers c
            INNER JOIN erp_sales s ON s.customer_id = c.id
                AND s.sale_date >= :start_date
                AND s.sale_date <= :end_date
            LEFT JOIN erp_tax_invoices ti ON ti.customer_id = c.id
                AND ti.issue_date >= :start_date
                AND ti.issue_date <= :end_date
                AND ti.invoice_type = 'sales'
            WHERE ti.id IS NULL
            GROUP BY c.id, c.name, c.business_number, c.representative
            ORDER BY total_sales_amount DESC
        """)

        result = await db.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
        })
        rows = result.fetchall()

        items = []
        for row in rows:
            d = _row_to_dict(row)
            items.append({
                "customer_id": d["customer_id"],
                "customer_name": d["customer_name"],
                "business_number": d.get("business_number"),
                "representative": d.get("representative"),
                "total_sales_amount": float(d["total_sales_amount"]),
                "total_supply_amount": float(d["total_supply_amount"]),
                "total_tax_amount": float(d["total_tax_amount"]),
                "sale_count": int(d["sale_count"]),
            })

        return {"items": items, "total": len(items)}

    except Exception as e:
        if "does not exist" in str(e) or "no such table" in str(e).lower():
            return {"items": [], "total": 0}
        raise HTTPException(status_code=500, detail=f"미발행 거래처 조회 실패: {str(e)}")
