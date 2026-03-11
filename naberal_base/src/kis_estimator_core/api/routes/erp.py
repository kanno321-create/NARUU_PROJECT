"""
ERP API Routes (FastAPI)

PostgreSQL(asyncpg) 기반 ERP API 라우트
kis_beta 스키마의 테이블을 직접 쿼리하여 데이터 관리
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.api.schemas.erp import (
    Customer, CustomerCreate, CustomerUpdate, CustomerList,
    Product, ProductCreate, ProductUpdate, ProductList,
    Sale, SaleCreate, SaleUpdate, SaleList, SaleItem, SaleItemCreate,
    Purchase, PurchaseCreate, PurchaseUpdate, PurchaseList, PurchaseItem,
    TaxInvoice, TaxInvoiceCreate, TaxInvoiceUpdate, TaxInvoiceList,
    Quotation, QuotationCreate, QuotationUpdate, QuotationList, QuotationItem,
    Payment, PaymentCreate, PaymentUpdate, PaymentList,
    DashboardStats, SalesChartData,
)
from kis_estimator_core.infra.db import get_db
from kis_estimator_core.lib.erp.customer_service import update_customer_receivable

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp", tags=["ERP"])

# ============================================
# 카탈로그 파일 경로 (로컬 JSON - DB 아님)
# ============================================

CATALOG_FILE = Path(__file__).parent.parent.parent.parent.parent / "절대코어파일" / "ai_catalog_v1.json"


# ============================================
# 헬퍼 함수
# ============================================

def _row_to_dict(row, id_to_str: bool = True) -> dict:
    """DB 행 매핑을 dict로 변환. 모든 UUID 필드를 문자열로 캐스팅."""
    d = dict(row)
    if id_to_str:
        for key, value in d.items():
            if isinstance(value, UUID):
                d[key] = str(value)
    return d


# ============================================
# 거래처 (Customer) API
# ============================================

@router.get("/customers", response_model=CustomerList)
async def list_customers(
    search: Optional[str] = None,
    customer_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """거래처 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if search:
        where_clauses.append("(name ILIKE :search OR code ILIKE :search)")
        params["search"] = f"%{search}%"
    if customer_type:
        where_clauses.append("customer_type = :customer_type")
        params["customer_type"] = customer_type
    if is_active is not None:
        where_clauses.append("is_active = :is_active")
        params["is_active"] = is_active

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM customers WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT * FROM customers WHERE {where_sql} "
            f"ORDER BY created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()
    items = [Customer(**_row_to_dict(r)) for r in rows]

    return CustomerList(items=items, total=total)


@router.post("/customers", response_model=Customer)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db),
):
    """거래처 생성"""
    code = customer.code
    if not code:
        last = await db.execute(
            text(
                "SELECT code FROM customers WHERE code LIKE 'C-%' "
                "ORDER BY code DESC LIMIT 1"
            )
        )
        row = last.mappings().first()
        if row and row["code"]:
            try:
                num = int(row["code"].split("-")[1]) + 1
            except (ValueError, IndexError):
                num = 1
            code = f"C-{num:04d}"
        else:
            code = "C-0001"

    data = customer.model_dump()
    data["code"] = code

    result = await db.execute(
        text(
            "INSERT INTO customers "
            "(id, code, name, customer_type, grade, business_number, "
            "ceo_name, contact_person, phone, fax, email, address, "
            "credit_limit, current_receivable, payment_terms, memo, "
            "is_active, created_at) "
            "VALUES (gen_random_uuid(), :code, :name, :customer_type, :grade, "
            ":business_number, :ceo_name, :contact_person, :phone, :fax, "
            ":email, :address, :credit_limit, :current_receivable, "
            ":payment_terms, :memo, :is_active, NOW()) "
            "RETURNING *"
        ),
        data,
    )
    row = result.mappings().first()
    return Customer(**_row_to_dict(row))


@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """거래처 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM customers WHERE id = :id"),
        {"id": customer_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    return Customer(**_row_to_dict(row))


@router.patch("/customers/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """거래처 수정"""
    update_data = customer.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = customer_id

    result = await db.execute(
        text(
            f"UPDATE customers SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    return Customer(**_row_to_dict(row))


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """거래처 삭제"""
    result = await db.execute(
        text("DELETE FROM customers WHERE id = :id RETURNING id"),
        {"id": customer_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    return {"message": "거래처가 삭제되었습니다"}


# ============================================
# 상품 (Product) API
# ============================================

@router.get("/products", response_model=ProductList)
async def list_products(
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """상품 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if search:
        where_clauses.append("(name ILIKE :search OR code ILIKE :search)")
        params["search"] = f"%{search}%"
    if category_id:
        where_clauses.append("category_id = :category_id")
        params["category_id"] = category_id
    if is_active is not None:
        where_clauses.append("is_active = :is_active")
        params["is_active"] = is_active

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM products WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT * FROM products WHERE {where_sql} "
            f"ORDER BY created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()
    items = [Product(**_row_to_dict(r)) for r in rows]

    return ProductList(items=items, total=total)


# ============================================
# 카탈로그 검색 (로컬 JSON - AS-IS 유지)
# ============================================

def _load_catalog() -> dict:
    """카탈로그 JSON 파일 로드"""
    if not CATALOG_FILE.exists():
        return {"breakers": [], "enclosures": []}
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/products/search-all")
async def search_all_products(
    search: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    전체 상품 검색 (ERP 상품 + 카탈로그)

    ERP 등록 상품과 카탈로그를 동시에 검색하여 결과 반환
    ERP 상품이 우선, 카탈로그 상품이 뒤에 추가
    """
    # ERP 상품 검색 (DB)
    result = await db.execute(
        text(
            "SELECT * FROM products "
            "WHERE name ILIKE :search OR code ILIKE :search "
            "OR spec ILIKE :search "
            "ORDER BY created_at DESC LIMIT :limit"
        ),
        {"search": f"%{search}%", "limit": limit},
    )
    rows = result.mappings().all()
    erp_results = []
    for r in rows:
        d = _row_to_dict(r)
        d["is_catalog"] = False
        erp_results.append(d)

    # 카탈로그 검색 (로컬 JSON)
    catalog = _load_catalog()
    breakers = catalog.get("breakers", [])
    search_lower = search.lower()

    catalog_results = []
    for b in breakers:
        model = str(b.get("model", "")).lower()
        keywords = [str(k).lower() for k in b.get("search_keywords", [])]
        cat = str(b.get("category", "")).lower()
        brand = str(b.get("brand", "")).lower()

        if (search_lower in model or
            search_lower in cat or
            search_lower in brand or
            any(search_lower in kw for kw in keywords)):

            catalog_results.append({
                "id": f"catalog_{b.get('model')}_{b.get('poles')}P_{b.get('current_a')}A",
                "code": f"CTG-{b.get('model')}",
                "name": f"{b.get('category')} {b.get('model')}",
                "spec": f"{b.get('poles')}P {b.get('frame_af')}AF {b.get('current_a')}A {b.get('breaking_capacity_ka')}kA",
                "unit": "EA",
                "category_id": "breaker",
                "purchase_price": int(b.get("price", 0) * 0.8),
                "selling_price": b.get("price", 0),
                "safety_stock": 0,
                "memo": f"{b.get('brand')} {b.get('series')}",
                "is_active": True,
                "is_catalog": True,
                "dimensions": b.get("dimensions"),
            })

    # ERP 상품 우선, 카탈로그 상품 뒤에 추가
    all_results = erp_results + catalog_results
    all_results = all_results[:limit]

    return {
        "items": all_results,
        "total": len(all_results),
        "erp_count": len(erp_results),
        "catalog_count": len(catalog_results),
    }


@router.get("/catalog/search")
async def search_catalog(
    search: str = Query(..., min_length=1, description="검색어 (모델명, 카테고리 등)"),
    category: Optional[str] = Query(None, description="카테고리 필터 (MCCB, ELB)"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    카탈로그 검색 (차단기 모델 검색)

    ai_catalog_v1.json에서 차단기 검색
    검색어로 모델명, 키워드, 카테고리 검색
    """
    catalog = _load_catalog()
    breakers = catalog.get("breakers", [])

    search_lower = search.lower()
    results = []

    for b in breakers:
        # 카테고리 필터
        if category and b.get("category") != category:
            continue

        # 검색어 매칭 (모델명, 키워드, 카테고리, 브랜드)
        model = str(b.get("model", "")).lower()
        keywords = [str(k).lower() for k in b.get("search_keywords", [])]
        cat = str(b.get("category", "")).lower()
        brand = str(b.get("brand", "")).lower()
        notes = str(b.get("notes", "")).lower()

        if (search_lower in model or
            search_lower in cat or
            search_lower in brand or
            search_lower in notes or
            any(search_lower in kw for kw in keywords)):

            # ERP 상품 형태로 변환
            results.append({
                "id": f"catalog_{b.get('model')}_{b.get('poles')}P_{b.get('current_a')}A",
                "code": f"CTG-{b.get('model')}",
                "name": f"{b.get('category')} {b.get('model')}",
                "spec": f"{b.get('poles')}P {b.get('frame_af')}AF {b.get('current_a')}A {b.get('breaking_capacity_ka')}kA",
                "unit": "EA",
                "category_id": "breaker",
                "purchase_price": int(b.get("price", 0) * 0.8),  # 매입가 (80%)
                "selling_price": b.get("price", 0),  # 판매가
                "safety_stock": 0,
                "memo": f"{b.get('brand')} {b.get('series')} - {b.get('notes', '')}",
                "is_active": True,
                "is_catalog": True,  # 카탈로그 상품 표시
                "dimensions": b.get("dimensions"),
            })

    # 결과 제한
    results = results[:limit]

    return {
        "items": results,
        "total": len(results),
        "source": "catalog"
    }


@router.post("/products", response_model=Product)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """상품 생성"""
    code = product.code
    if not code:
        last = await db.execute(
            text(
                "SELECT code FROM products WHERE code LIKE 'P-%' "
                "ORDER BY code DESC LIMIT 1"
            )
        )
        row = last.mappings().first()
        if row and row["code"]:
            try:
                num = int(row["code"].split("-")[1]) + 1
            except (ValueError, IndexError):
                num = 1
            code = f"P-{num:04d}"
        else:
            code = "P-0001"

    data = product.model_dump()
    data["code"] = code

    result = await db.execute(
        text(
            "INSERT INTO products "
            "(id, code, name, spec, unit, category_id, purchase_price, "
            "selling_price, safety_stock, memo, is_active, created_at) "
            "VALUES (gen_random_uuid(), :code, :name, :spec, :unit, "
            ":category_id, :purchase_price, :selling_price, :safety_stock, "
            ":memo, :is_active, NOW()) "
            "RETURNING *"
        ),
        data,
    )
    row = result.mappings().first()
    return Product(**_row_to_dict(row))


@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """상품 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM products WHERE id = :id"),
        {"id": product_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return Product(**_row_to_dict(row))


@router.patch("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """상품 수정"""
    update_data = product.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = product_id

    result = await db.execute(
        text(
            f"UPDATE products SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return Product(**_row_to_dict(row))


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """상품 삭제"""
    result = await db.execute(
        text("DELETE FROM products WHERE id = :id RETURNING id"),
        {"id": product_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return {"message": "상품이 삭제되었습니다"}


# ============================================
# 매출 (Sale) API
# ============================================

async def _attach_sale_items(db: AsyncSession, sale_dict: dict) -> dict:
    """매출 레코드에 sale_items를 조인하여 items 필드에 할당"""
    items_result = await db.execute(
        text(
            "SELECT * FROM sale_items WHERE sale_id = :sale_id "
            "ORDER BY sort_order"
        ),
        {"sale_id": sale_dict["id"]},
    )
    items_rows = items_result.mappings().all()
    sale_dict["items"] = [
        SaleItem(**_row_to_dict(ir)) for ir in items_rows
    ]
    return sale_dict


async def _attach_customer_to_sale(db: AsyncSession, sale_dict: dict) -> dict:
    """매출 레코드에 customer 정보를 조인"""
    if sale_dict.get("customer_id"):
        cust_result = await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": sale_dict["customer_id"]},
        )
        cust_row = cust_result.mappings().first()
        if cust_row:
            sale_dict["customer"] = Customer(**_row_to_dict(cust_row))
    return sale_dict


@router.get("/sales", response_model=SaleList)
async def list_sales(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """매출 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if customer_id:
        where_clauses.append("s.customer_id = :customer_id")
        params["customer_id"] = customer_id
    if status:
        where_clauses.append("s.status = :status")
        params["status"] = status
    if start_date:
        where_clauses.append("s.sale_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("s.sale_date <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM sales s WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT s.* FROM sales s WHERE {where_sql} "
            f"ORDER BY s.created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for r in rows:
        sale_dict = _row_to_dict(r)
        await _attach_sale_items(db, sale_dict)
        await _attach_customer_to_sale(db, sale_dict)
        items.append(Sale(**sale_dict))

    return SaleList(items=items, total=total)


@router.post("/sales")
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
):
    """매출 생성"""
    # 매출번호 자동 생성
    last = await db.execute(
        text(
            "SELECT sale_number FROM sales WHERE sale_number LIKE 'S-%' "
            "ORDER BY sale_number DESC LIMIT 1"
        )
    )
    row = last.mappings().first()
    if row and row["sale_number"]:
        try:
            num = int(row["sale_number"].split("-")[1]) + 1
        except (ValueError, IndexError):
            num = 1
        sale_number = f"S-{num:04d}"
    else:
        sale_number = "S-0001"

    # 항목 금액 계산
    supply_amount = Decimal("0")
    tax_amount = Decimal("0")
    cost_amount = Decimal("0")

    computed_items = []
    for idx, item in enumerate(sale.items):
        item_data = item.model_dump()
        item_data["sort_order"] = idx

        qty = Decimal(str(item_data["quantity"]))
        price = Decimal(str(item_data["unit_price"]))
        item_supply = qty * price
        item_tax = item_supply * Decimal("0.1")

        item_data["supply_amount"] = item_supply
        item_data["tax_amount"] = item_tax
        item_data["total_amount"] = item_supply + item_tax

        supply_amount += item_supply
        tax_amount += item_tax
        cost_amount += Decimal(str(item_data.get("cost_price", 0))) * qty

        computed_items.append(item_data)

    total_amount = supply_amount + tax_amount
    profit_amount = supply_amount - cost_amount

    # 매출 레코드 삽입
    sale_result = await db.execute(
        text(
            "INSERT INTO sales "
            "(id, sale_number, sale_date, customer_id, status, "
            "supply_amount, tax_amount, total_amount, cost_amount, "
            "profit_amount, memo, created_at) "
            "VALUES (gen_random_uuid(), :sale_number, :sale_date, "
            ":customer_id, :status, :supply_amount, :tax_amount, "
            ":total_amount, :cost_amount, :profit_amount, :memo, NOW()) "
            "RETURNING *"
        ),
        {
            "sale_number": sale_number,
            "sale_date": sale.sale_date,
            "customer_id": sale.customer_id,
            "status": sale.status,
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "cost_amount": cost_amount,
            "profit_amount": profit_amount,
            "memo": sale.memo,
        },
    )
    sale_row = sale_result.mappings().first()
    sale_id = str(sale_row["id"])

    # 매출 항목 삽입
    inserted_items = []
    for item_data in computed_items:
        item_result = await db.execute(
            text(
                "INSERT INTO sale_items "
                "(id, sale_id, product_id, product_code, product_name, "
                "spec, unit, quantity, unit_price, supply_amount, "
                "tax_amount, total_amount, cost_price, memo, sort_order) "
                "VALUES (gen_random_uuid(), :sale_id, :product_id, "
                ":product_code, :product_name, :spec, :unit, :quantity, "
                ":unit_price, :supply_amount, :tax_amount, :total_amount, "
                ":cost_price, :memo, :sort_order) "
                "RETURNING *"
            ),
            {"sale_id": sale_id, **item_data},
        )
        item_row = item_result.mappings().first()
        inserted_items.append(SaleItem(**_row_to_dict(item_row)))

    # 고객 미수금 업데이트 (JSON 기반 - 실패 시 로그만 남김)
    receivable_warning = None
    receivable_error = None
    try:
        receivable_result = update_customer_receivable(
            customer_id=sale.customer_id,
            amount=total_amount,
        )
        if receivable_result.get("success"):
            if receivable_result.get("warning"):
                receivable_warning = receivable_result["warning"]
        else:
            receivable_error = receivable_result.get("error", {})
            logger.warning(
                "Failed to update customer receivable (JSON-based): %s",
                receivable_error.get("message"),
            )
    except Exception as exc:
        logger.warning(
            "update_customer_receivable raised an exception: %s", exc,
        )

    # 응답 구성
    sale_dict = _row_to_dict(sale_row)
    sale_dict["items"] = inserted_items
    sale_response = Sale(**sale_dict)
    response_dict = sale_response.model_dump()

    if receivable_warning:
        response_dict["warning"] = receivable_warning
    if receivable_error:
        response_dict["error"] = receivable_error

    return response_dict


@router.get("/sales/{sale_id}", response_model=Sale)
async def get_sale(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
):
    """매출 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM sales WHERE id = :id"),
        {"id": sale_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="매출을 찾을 수 없습니다")

    sale_dict = _row_to_dict(row)
    await _attach_sale_items(db, sale_dict)
    await _attach_customer_to_sale(db, sale_dict)
    return Sale(**sale_dict)


@router.patch("/sales/{sale_id}", response_model=Sale)
async def update_sale(
    sale_id: str,
    sale: SaleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """매출 수정"""
    update_data = sale.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = sale_id

    result = await db.execute(
        text(
            f"UPDATE sales SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="매출을 찾을 수 없습니다")

    sale_dict = _row_to_dict(row)
    await _attach_sale_items(db, sale_dict)
    return Sale(**sale_dict)


@router.delete("/sales/{sale_id}")
async def delete_sale(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
):
    """매출 삭제"""
    # 하위 항목 먼저 삭제
    await db.execute(
        text("DELETE FROM sale_items WHERE sale_id = :sale_id"),
        {"sale_id": sale_id},
    )
    result = await db.execute(
        text("DELETE FROM sales WHERE id = :id RETURNING id"),
        {"id": sale_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="매출을 찾을 수 없습니다")
    return {"message": "매출이 삭제되었습니다"}


# ============================================
# 매입 (Purchase) API
# ============================================

async def _attach_purchase_items(db: AsyncSession, purchase_dict: dict) -> dict:
    """매입 레코드에 purchase_items를 조인하여 items 필드에 할당"""
    items_result = await db.execute(
        text(
            "SELECT * FROM purchase_items WHERE purchase_id = :purchase_id "
            "ORDER BY sort_order"
        ),
        {"purchase_id": purchase_dict["id"]},
    )
    items_rows = items_result.mappings().all()
    purchase_dict["items"] = [
        PurchaseItem(**_row_to_dict(ir)) for ir in items_rows
    ]
    return purchase_dict


async def _attach_supplier_to_purchase(db: AsyncSession, purchase_dict: dict) -> dict:
    """매입 레코드에 supplier(customer) 정보를 조인"""
    if purchase_dict.get("supplier_id"):
        cust_result = await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": purchase_dict["supplier_id"]},
        )
        cust_row = cust_result.mappings().first()
        if cust_row:
            purchase_dict["supplier"] = Customer(**_row_to_dict(cust_row))
    return purchase_dict


@router.get("/purchases", response_model=PurchaseList)
async def list_purchases(
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """매입 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if supplier_id:
        where_clauses.append("p.supplier_id = :supplier_id")
        params["supplier_id"] = supplier_id
    if status:
        where_clauses.append("p.status = :status")
        params["status"] = status
    if start_date:
        where_clauses.append("p.purchase_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("p.purchase_date <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM purchases p WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT p.* FROM purchases p WHERE {where_sql} "
            f"ORDER BY p.created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for r in rows:
        purchase_dict = _row_to_dict(r)
        await _attach_purchase_items(db, purchase_dict)
        await _attach_supplier_to_purchase(db, purchase_dict)
        items.append(Purchase(**purchase_dict))

    return PurchaseList(items=items, total=total)


@router.post("/purchases", response_model=Purchase)
async def create_purchase(
    purchase: PurchaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """매입 생성"""
    # 매입번호 자동 생성
    last = await db.execute(
        text(
            "SELECT purchase_number FROM purchases "
            "WHERE purchase_number LIKE 'PO-%' "
            "ORDER BY purchase_number DESC LIMIT 1"
        )
    )
    row = last.mappings().first()
    if row and row["purchase_number"]:
        try:
            num = int(row["purchase_number"].split("-")[1]) + 1
        except (ValueError, IndexError):
            num = 1
        purchase_number = f"PO-{num:04d}"
    else:
        purchase_number = "PO-0001"

    # 항목 금액 계산
    supply_amount = Decimal("0")
    tax_amount = Decimal("0")

    computed_items = []
    for idx, item in enumerate(purchase.items):
        item_data = item.model_dump()
        item_data["sort_order"] = idx

        qty = Decimal(str(item_data["quantity"]))
        price = Decimal(str(item_data["unit_price"]))
        item_supply = qty * price
        item_tax = item_supply * Decimal("0.1")

        item_data["supply_amount"] = item_supply
        item_data["tax_amount"] = item_tax
        item_data["total_amount"] = item_supply + item_tax

        supply_amount += item_supply
        tax_amount += item_tax

        computed_items.append(item_data)

    total_amount = supply_amount + tax_amount

    # 매입 레코드 삽입
    purchase_result = await db.execute(
        text(
            "INSERT INTO purchases "
            "(id, purchase_number, purchase_date, supplier_id, status, "
            "supply_amount, tax_amount, total_amount, memo, created_at) "
            "VALUES (gen_random_uuid(), :purchase_number, :purchase_date, "
            ":supplier_id, :status, :supply_amount, :tax_amount, "
            ":total_amount, :memo, NOW()) "
            "RETURNING *"
        ),
        {
            "purchase_number": purchase_number,
            "purchase_date": purchase.purchase_date,
            "supplier_id": purchase.supplier_id,
            "status": purchase.status,
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "memo": purchase.memo,
        },
    )
    purchase_row = purchase_result.mappings().first()
    purchase_id = str(purchase_row["id"])

    # 매입 항목 삽입
    inserted_items = []
    for item_data in computed_items:
        item_result = await db.execute(
            text(
                "INSERT INTO purchase_items "
                "(id, purchase_id, product_id, product_code, product_name, "
                "spec, unit, quantity, unit_price, supply_amount, "
                "tax_amount, total_amount, memo, sort_order) "
                "VALUES (gen_random_uuid(), :purchase_id, :product_id, "
                ":product_code, :product_name, :spec, :unit, :quantity, "
                ":unit_price, :supply_amount, :tax_amount, :total_amount, "
                ":memo, :sort_order) "
                "RETURNING *"
            ),
            {"purchase_id": purchase_id, **item_data},
        )
        item_row = item_result.mappings().first()
        inserted_items.append(PurchaseItem(**_row_to_dict(item_row)))

    purchase_dict = _row_to_dict(purchase_row)
    purchase_dict["items"] = inserted_items
    return Purchase(**purchase_dict)


@router.get("/purchases/{purchase_id}", response_model=Purchase)
async def get_purchase(
    purchase_id: str,
    db: AsyncSession = Depends(get_db),
):
    """매입 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM purchases WHERE id = :id"),
        {"id": purchase_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="매입을 찾을 수 없습니다")

    purchase_dict = _row_to_dict(row)
    await _attach_purchase_items(db, purchase_dict)
    await _attach_supplier_to_purchase(db, purchase_dict)
    return Purchase(**purchase_dict)


@router.patch("/purchases/{purchase_id}", response_model=Purchase)
async def update_purchase(
    purchase_id: str,
    purchase: PurchaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """매입 수정"""
    update_data = purchase.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = purchase_id

    result = await db.execute(
        text(
            f"UPDATE purchases SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="매입을 찾을 수 없습니다")

    purchase_dict = _row_to_dict(row)
    await _attach_purchase_items(db, purchase_dict)
    return Purchase(**purchase_dict)


@router.delete("/purchases/{purchase_id}")
async def delete_purchase(
    purchase_id: str,
    db: AsyncSession = Depends(get_db),
):
    """매입 삭제"""
    # 하위 항목 먼저 삭제
    await db.execute(
        text("DELETE FROM purchase_items WHERE purchase_id = :purchase_id"),
        {"purchase_id": purchase_id},
    )
    result = await db.execute(
        text("DELETE FROM purchases WHERE id = :id RETURNING id"),
        {"id": purchase_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="매입을 찾을 수 없습니다")
    return {"message": "매입이 삭제되었습니다"}


# ============================================
# 세금계산서 (TaxInvoice) API
# ============================================

@router.get("/tax-invoices", response_model=TaxInvoiceList)
async def list_tax_invoices(
    customer_id: Optional[str] = None,
    invoice_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if customer_id:
        where_clauses.append("t.customer_id = :customer_id")
        params["customer_id"] = customer_id
    if invoice_type:
        where_clauses.append("t.invoice_type = :invoice_type")
        params["invoice_type"] = invoice_type
    if status:
        where_clauses.append("t.status = :status")
        params["status"] = status
    if start_date:
        where_clauses.append("t.issue_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("t.issue_date <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM tax_invoices t WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT t.* FROM tax_invoices t WHERE {where_sql} "
            f"ORDER BY t.created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for r in rows:
        inv_dict = _row_to_dict(r)
        # customer 조인
        if inv_dict.get("customer_id"):
            cust_result = await db.execute(
                text("SELECT * FROM customers WHERE id = :id"),
                {"id": inv_dict["customer_id"]},
            )
            cust_row = cust_result.mappings().first()
            if cust_row:
                inv_dict["customer"] = Customer(**_row_to_dict(cust_row))
        items.append(TaxInvoice(**inv_dict))

    return TaxInvoiceList(items=items, total=total)


@router.post("/tax-invoices", response_model=TaxInvoice)
async def create_tax_invoice(
    invoice: TaxInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 생성"""
    invoice_number = invoice.invoice_number
    if not invoice_number:
        last = await db.execute(
            text(
                "SELECT invoice_number FROM tax_invoices "
                "WHERE invoice_number LIKE 'TI-%' "
                "ORDER BY invoice_number DESC LIMIT 1"
            )
        )
        row = last.mappings().first()
        if row and row["invoice_number"]:
            try:
                num = int(row["invoice_number"].split("-")[1]) + 1
            except (ValueError, IndexError):
                num = 1
            invoice_number = f"TI-{num:04d}"
        else:
            invoice_number = "TI-0001"

    data = invoice.model_dump()
    data["invoice_number"] = invoice_number

    result = await db.execute(
        text(
            "INSERT INTO tax_invoices "
            "(id, invoice_number, invoice_type, issue_date, customer_id, "
            "supply_amount, tax_amount, total_amount, status, "
            "reference_type, reference_id, memo, created_at) "
            "VALUES (gen_random_uuid(), :invoice_number, :invoice_type, "
            ":issue_date, :customer_id, :supply_amount, :tax_amount, "
            ":total_amount, :status, :reference_type, :reference_id, "
            ":memo, NOW()) "
            "RETURNING *"
        ),
        data,
    )
    row = result.mappings().first()
    return TaxInvoice(**_row_to_dict(row))


@router.get("/tax-invoices/{invoice_id}", response_model=TaxInvoice)
async def get_tax_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM tax_invoices WHERE id = :id"),
        {"id": invoice_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="세금계산서를 찾을 수 없습니다")

    inv_dict = _row_to_dict(row)
    if inv_dict.get("customer_id"):
        cust_result = await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": inv_dict["customer_id"]},
        )
        cust_row = cust_result.mappings().first()
        if cust_row:
            inv_dict["customer"] = Customer(**_row_to_dict(cust_row))

    return TaxInvoice(**inv_dict)


@router.patch("/tax-invoices/{invoice_id}", response_model=TaxInvoice)
async def update_tax_invoice(
    invoice_id: str,
    invoice: TaxInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 수정"""
    update_data = invoice.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = invoice_id

    result = await db.execute(
        text(
            f"UPDATE tax_invoices SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="세금계산서를 찾을 수 없습니다")
    return TaxInvoice(**_row_to_dict(row))


@router.delete("/tax-invoices/{invoice_id}")
async def delete_tax_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
):
    """세금계산서 삭제"""
    result = await db.execute(
        text("DELETE FROM tax_invoices WHERE id = :id RETURNING id"),
        {"id": invoice_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="세금계산서를 찾을 수 없습니다")
    return {"message": "세금계산서가 삭제되었습니다"}


# ============================================
# 견적서 (Quotation) API
# ============================================

async def _attach_quotation_items(db: AsyncSession, quotation_dict: dict) -> dict:
    """견적서 레코드에 quotation_items를 조인하여 items 필드에 할당"""
    items_result = await db.execute(
        text(
            "SELECT * FROM quotation_items "
            "WHERE quotation_id = :quotation_id ORDER BY sort_order"
        ),
        {"quotation_id": quotation_dict["id"]},
    )
    items_rows = items_result.mappings().all()
    quotation_dict["items"] = [
        QuotationItem(**_row_to_dict(ir)) for ir in items_rows
    ]
    return quotation_dict


async def _attach_customer_to_quotation(db: AsyncSession, quotation_dict: dict) -> dict:
    """견적서 레코드에 customer 정보를 조인"""
    if quotation_dict.get("customer_id"):
        cust_result = await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": quotation_dict["customer_id"]},
        )
        cust_row = cust_result.mappings().first()
        if cust_row:
            quotation_dict["customer"] = Customer(**_row_to_dict(cust_row))
    return quotation_dict


@router.get("/quotations", response_model=QuotationList)
async def list_quotations(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """견적서 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if customer_id:
        where_clauses.append("q.customer_id = :customer_id")
        params["customer_id"] = customer_id
    if status:
        where_clauses.append("q.status = :status")
        params["status"] = status
    if start_date:
        where_clauses.append("q.quotation_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("q.quotation_date <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM quotations q WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT q.* FROM quotations q WHERE {where_sql} "
            f"ORDER BY q.created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for r in rows:
        q_dict = _row_to_dict(r)
        await _attach_quotation_items(db, q_dict)
        await _attach_customer_to_quotation(db, q_dict)
        items.append(Quotation(**q_dict))

    return QuotationList(items=items, total=total)


@router.post("/quotations", response_model=Quotation)
async def create_quotation(
    quotation: QuotationCreate,
    db: AsyncSession = Depends(get_db),
):
    """견적서 생성"""
    # 견적번호 자동 생성
    last = await db.execute(
        text(
            "SELECT quotation_number FROM quotations "
            "WHERE quotation_number LIKE 'Q-%' "
            "ORDER BY quotation_number DESC LIMIT 1"
        )
    )
    row = last.mappings().first()
    if row and row["quotation_number"]:
        try:
            num = int(row["quotation_number"].split("-")[1]) + 1
        except (ValueError, IndexError):
            num = 1
        quotation_number = f"Q-{num:04d}"
    else:
        quotation_number = "Q-0001"

    # 항목 금액 계산
    supply_amount = Decimal("0")
    tax_amount = Decimal("0")

    computed_items = []
    for idx, item in enumerate(quotation.items):
        item_data = item.model_dump()
        item_data["sort_order"] = idx

        qty = Decimal(str(item_data["quantity"]))
        price = Decimal(str(item_data["unit_price"]))
        item_supply = qty * price
        item_tax = item_supply * Decimal("0.1")

        item_data["supply_amount"] = item_supply
        item_data["tax_amount"] = item_tax
        item_data["total_amount"] = item_supply + item_tax

        supply_amount += item_supply
        tax_amount += item_tax

        computed_items.append(item_data)

    total_amount = supply_amount + tax_amount

    # 견적서 레코드 삽입
    quotation_result = await db.execute(
        text(
            "INSERT INTO quotations "
            "(id, quotation_number, quotation_date, valid_until, "
            "customer_id, status, supply_amount, tax_amount, "
            "total_amount, memo, created_at) "
            "VALUES (gen_random_uuid(), :quotation_number, :quotation_date, "
            ":valid_until, :customer_id, :status, :supply_amount, "
            ":tax_amount, :total_amount, :memo, NOW()) "
            "RETURNING *"
        ),
        {
            "quotation_number": quotation_number,
            "quotation_date": quotation.quotation_date,
            "valid_until": quotation.valid_until,
            "customer_id": quotation.customer_id,
            "status": quotation.status,
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "memo": quotation.memo,
        },
    )
    quotation_row = quotation_result.mappings().first()
    quotation_id = str(quotation_row["id"])

    # 견적 항목 삽입
    inserted_items = []
    for item_data in computed_items:
        item_result = await db.execute(
            text(
                "INSERT INTO quotation_items "
                "(id, quotation_id, product_id, product_code, product_name, "
                "spec, unit, quantity, unit_price, supply_amount, "
                "tax_amount, total_amount, memo, sort_order) "
                "VALUES (gen_random_uuid(), :quotation_id, :product_id, "
                ":product_code, :product_name, :spec, :unit, :quantity, "
                ":unit_price, :supply_amount, :tax_amount, :total_amount, "
                ":memo, :sort_order) "
                "RETURNING *"
            ),
            {"quotation_id": quotation_id, **item_data},
        )
        item_row = item_result.mappings().first()
        inserted_items.append(QuotationItem(**_row_to_dict(item_row)))

    q_dict = _row_to_dict(quotation_row)
    q_dict["items"] = inserted_items
    return Quotation(**q_dict)


@router.get("/quotations/{quotation_id}", response_model=Quotation)
async def get_quotation(
    quotation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """견적서 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM quotations WHERE id = :id"),
        {"id": quotation_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다")

    q_dict = _row_to_dict(row)
    await _attach_quotation_items(db, q_dict)
    await _attach_customer_to_quotation(db, q_dict)
    return Quotation(**q_dict)


@router.patch("/quotations/{quotation_id}", response_model=Quotation)
async def update_quotation(
    quotation_id: str,
    quotation: QuotationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """견적서 수정"""
    update_data = quotation.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = quotation_id

    result = await db.execute(
        text(
            f"UPDATE quotations SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다")

    q_dict = _row_to_dict(row)
    await _attach_quotation_items(db, q_dict)
    return Quotation(**q_dict)


@router.delete("/quotations/{quotation_id}")
async def delete_quotation(
    quotation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """견적서 삭제"""
    # 하위 항목 먼저 삭제
    await db.execute(
        text("DELETE FROM quotation_items WHERE quotation_id = :quotation_id"),
        {"quotation_id": quotation_id},
    )
    result = await db.execute(
        text("DELETE FROM quotations WHERE id = :id RETURNING id"),
        {"id": quotation_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다")
    return {"message": "견적서가 삭제되었습니다"}


# ============================================
# 수금/지급 (Payment) API
# ============================================

@router.get("/payments", response_model=PaymentList)
async def list_payments(
    customer_id: Optional[str] = None,
    payment_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """수금/지급 목록 조회"""
    where_clauses = ["1=1"]
    params: dict = {"skip": skip, "limit": limit}

    if customer_id:
        where_clauses.append("pm.customer_id = :customer_id")
        params["customer_id"] = customer_id
    if payment_type:
        where_clauses.append("pm.payment_type = :payment_type")
        params["payment_type"] = payment_type
    if status:
        where_clauses.append("pm.status = :status")
        params["status"] = status
    if start_date:
        where_clauses.append("pm.payment_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("pm.payment_date <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM payments pm WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    result = await db.execute(
        text(
            f"SELECT pm.* FROM payments pm WHERE {where_sql} "
            f"ORDER BY pm.created_at DESC OFFSET :skip LIMIT :limit"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for r in rows:
        pm_dict = _row_to_dict(r)
        if pm_dict.get("customer_id"):
            cust_result = await db.execute(
                text("SELECT * FROM customers WHERE id = :id"),
                {"id": pm_dict["customer_id"]},
            )
            cust_row = cust_result.mappings().first()
            if cust_row:
                pm_dict["customer"] = Customer(**_row_to_dict(cust_row))
        items.append(Payment(**pm_dict))

    return PaymentList(items=items, total=total)


@router.post("/payments", response_model=Payment)
async def create_payment(
    payment: PaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    """수금/지급 생성"""
    # 수금/지급 번호 자동 생성
    last = await db.execute(
        text(
            "SELECT payment_number FROM payments "
            "WHERE payment_number LIKE 'PM-%' "
            "ORDER BY payment_number DESC LIMIT 1"
        )
    )
    row = last.mappings().first()
    if row and row["payment_number"]:
        try:
            num = int(row["payment_number"].split("-")[1]) + 1
        except (ValueError, IndexError):
            num = 1
        payment_number = f"PM-{num:04d}"
    else:
        payment_number = "PM-0001"

    data = payment.model_dump()
    data["payment_number"] = payment_number

    result = await db.execute(
        text(
            "INSERT INTO payments "
            "(id, payment_number, payment_type, payment_date, customer_id, "
            "amount, payment_method, status, completed_date, "
            "reference_type, reference_id, memo, created_at) "
            "VALUES (gen_random_uuid(), :payment_number, :payment_type, "
            ":payment_date, :customer_id, :amount, :payment_method, "
            ":status, :completed_date, :reference_type, :reference_id, "
            ":memo, NOW()) "
            "RETURNING *"
        ),
        data,
    )
    row = result.mappings().first()
    return Payment(**_row_to_dict(row))


@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """수금/지급 상세 조회"""
    result = await db.execute(
        text("SELECT * FROM payments WHERE id = :id"),
        {"id": payment_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="수금/지급을 찾을 수 없습니다")

    pm_dict = _row_to_dict(row)
    if pm_dict.get("customer_id"):
        cust_result = await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": pm_dict["customer_id"]},
        )
        cust_row = cust_result.mappings().first()
        if cust_row:
            pm_dict["customer"] = Customer(**_row_to_dict(cust_row))

    return Payment(**pm_dict)


@router.patch("/payments/{payment_id}", response_model=Payment)
async def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """수금/지급 수정"""
    update_data = payment.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

    sets = [f"{k} = :{k}" for k in update_data]
    sets.append("updated_at = NOW()")
    update_data["id"] = payment_id

    result = await db.execute(
        text(
            f"UPDATE payments SET {', '.join(sets)} "
            f"WHERE id = :id RETURNING *"
        ),
        update_data,
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="수금/지급을 찾을 수 없습니다")
    return Payment(**_row_to_dict(row))


@router.delete("/payments/{payment_id}")
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """수금/지급 삭제"""
    result = await db.execute(
        text("DELETE FROM payments WHERE id = :id RETURNING id"),
        {"id": payment_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="수금/지급을 찾을 수 없습니다")
    return {"message": "수금/지급이 삭제되었습니다"}


# ============================================
# 대시보드 (Dashboard) API
# ============================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """대시보드 통합 조회 (stats 포워딩)"""
    return await get_dashboard_stats(db=db)


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """대시보드 통계 조회"""
    # 월별 매출 합계
    monthly_sales_result = await db.execute(
        text(
            "SELECT COALESCE(SUM(total_amount), 0) "
            "FROM sales "
            "WHERE sale_date >= date_trunc('month', CURRENT_DATE) "
            "AND sale_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
        )
    )
    monthly_sales = monthly_sales_result.scalar() or Decimal("0")

    # 월별 매입 합계
    monthly_purchases_result = await db.execute(
        text(
            "SELECT COALESCE(SUM(total_amount), 0) "
            "FROM purchases "
            "WHERE purchase_date >= date_trunc('month', CURRENT_DATE) "
            "AND purchase_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
        )
    )
    monthly_purchases = monthly_purchases_result.scalar() or Decimal("0")

    # 미수금 (수금 예정 - 완료되지 않은 것)
    total_receivables_result = await db.execute(
        text(
            "SELECT COALESCE(SUM(amount), 0) "
            "FROM payments "
            "WHERE payment_type = '수금' AND status != 'completed'"
        )
    )
    total_receivables = total_receivables_result.scalar() or Decimal("0")

    # 미지급 (지급 예정 - 완료되지 않은 것)
    total_payables_result = await db.execute(
        text(
            "SELECT COALESCE(SUM(amount), 0) "
            "FROM payments "
            "WHERE payment_type = '지급' AND status != 'completed'"
        )
    )
    total_payables = total_payables_result.scalar() or Decimal("0")

    # 이번 달 매출 건수
    sales_count_result = await db.execute(
        text(
            "SELECT COUNT(*) FROM sales "
            "WHERE sale_date >= date_trunc('month', CURRENT_DATE) "
            "AND sale_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
        )
    )
    sales_count = sales_count_result.scalar() or 0

    # 이번 달 매입 건수
    purchase_count_result = await db.execute(
        text(
            "SELECT COUNT(*) FROM purchases "
            "WHERE purchase_date >= date_trunc('month', CURRENT_DATE) "
            "AND purchase_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
        )
    )
    purchase_count = purchase_count_result.scalar() or 0

    # 활성 거래처 수
    customer_count_result = await db.execute(
        text("SELECT COUNT(*) FROM customers WHERE is_active = true")
    )
    customer_count = customer_count_result.scalar() or 0

    # 활성 상품 수
    product_count_result = await db.execute(
        text("SELECT COUNT(*) FROM products WHERE is_active = true")
    )
    product_count = product_count_result.scalar() or 0

    return DashboardStats(
        monthly_sales=monthly_sales,
        monthly_purchases=monthly_purchases,
        total_receivables=total_receivables,
        total_payables=total_payables,
        sales_count=sales_count,
        purchase_count=purchase_count,
        customer_count=customer_count,
        product_count=product_count,
    )


# ============================================
# 원장 (Ledger) API
# ============================================

@router.get("/ledger/customer")
async def get_customer_ledger(
    customer_id: str = Query(default=None, description="거래처 ID (없으면 전체)"),
    start_date: str = Query(default=None, description="시작일 YYYY-MM-DD"),
    end_date: str = Query(default=None, description="종료일 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """매출처원장 - 거래처별 매출/수금 내역과 누적잔액 조회"""

    # 1) 거래처 목록 조회 (요약)
    cust_where = ["1=1"]
    cust_params: dict = {}
    if customer_id:
        cust_where.append("c.id = :customer_id")
        cust_params["customer_id"] = customer_id

    cust_result = await db.execute(
        text(
            f"SELECT c.id, c.code, c.name, c.business_number, c.ceo_name, c.phone "
            f"FROM customers c WHERE {' AND '.join(cust_where)} "
            f"ORDER BY c.name"
        ),
        cust_params,
    )
    customers = cust_result.mappings().all()

    result_items = []
    for cust in customers:
        cid = str(cust["id"])

        # 2) 해당 거래처의 매출 내역 조회
        sale_where = ["s.customer_id = :cid"]
        sale_params: dict = {"cid": cid}
        if start_date:
            sale_where.append("s.sale_date >= :start_date")
            sale_params["start_date"] = start_date
        if end_date:
            sale_where.append("s.sale_date <= :end_date")
            sale_params["end_date"] = end_date

        sale_sql = " AND ".join(sale_where)
        sales_result = await db.execute(
            text(
                f"SELECT s.id, s.sale_number AS doc_no, s.sale_date AS trans_date, "
                f"'매출' AS trans_type, "
                f"COALESCE(s.memo, '상품판매') AS description, "
                f"s.total_amount AS debit_amount, "
                f"0 AS credit_amount "
                f"FROM sales s WHERE {sale_sql} "
                f"ORDER BY s.sale_date, s.created_at"
            ),
            sale_params,
        )
        sale_rows = sales_result.mappings().all()

        # 3) 해당 거래처의 수금 내역 조회
        pay_where = ["pm.customer_id = :cid", "pm.payment_type = '수금'"]
        pay_params: dict = {"cid": cid}
        if start_date:
            pay_where.append("pm.payment_date >= :start_date")
            pay_params["start_date"] = start_date
        if end_date:
            pay_where.append("pm.payment_date <= :end_date")
            pay_params["end_date"] = end_date

        pay_sql = " AND ".join(pay_where)
        pay_result = await db.execute(
            text(
                f"SELECT pm.id, pm.payment_number AS doc_no, pm.payment_date AS trans_date, "
                f"'수금' AS trans_type, "
                f"COALESCE(pm.memo, '외상수금') AS description, "
                f"0 AS debit_amount, "
                f"pm.amount AS credit_amount "
                f"FROM payments pm WHERE {pay_sql} "
                f"ORDER BY pm.payment_date, pm.created_at"
            ),
            pay_params,
        )
        pay_rows = pay_result.mappings().all()

        # 4) 전기이월 계산 (기간 이전 매출 합계 - 수금 합계)
        previous_balance = Decimal("0")
        if start_date:
            prev_sale_result = await db.execute(
                text(
                    "SELECT COALESCE(SUM(total_amount), 0) AS total "
                    "FROM sales WHERE customer_id = :cid AND sale_date < :start_date"
                ),
                {"cid": cid, "start_date": start_date},
            )
            prev_sales = prev_sale_result.scalar() or Decimal("0")

            prev_pay_result = await db.execute(
                text(
                    "SELECT COALESCE(SUM(amount), 0) AS total "
                    "FROM payments WHERE customer_id = :cid AND payment_type = '수금' "
                    "AND payment_date < :start_date"
                ),
                {"cid": cid, "start_date": start_date},
            )
            prev_payments = prev_pay_result.scalar() or Decimal("0")
            previous_balance = prev_sales - prev_payments

        # 5) 거래 내역 합산 및 잔액 계산
        transactions = []
        all_rows = []
        for row in sale_rows:
            all_rows.append(dict(row))
        for row in pay_rows:
            all_rows.append(dict(row))
        all_rows.sort(key=lambda x: (str(x["trans_date"]), x["trans_type"]))

        running_balance = previous_balance
        current_debit = Decimal("0")
        current_credit = Decimal("0")

        for row in all_rows:
            debit = Decimal(str(row["debit_amount"]))
            credit = Decimal(str(row["credit_amount"]))
            running_balance = running_balance + debit - credit
            current_debit += debit
            current_credit += credit

            transactions.append({
                "id": str(row["id"]),
                "transDate": str(row["trans_date"]),
                "transType": row["trans_type"],
                "docNo": row["doc_no"] or "",
                "description": row["description"] or "",
                "debitAmount": float(debit),
                "creditAmount": float(credit),
                "balance": float(running_balance),
                "memo": "",
            })

        result_items.append({
            "customerCode": cust["code"] or "",
            "customerName": cust["name"] or "",
            "businessNo": cust["business_number"] or "",
            "representative": cust["ceo_name"] or "",
            "phone": cust["phone"] or "",
            "previousBalance": float(previous_balance),
            "currentDebit": float(current_debit),
            "currentCredit": float(current_credit),
            "currentBalance": float(running_balance),
            "transactions": transactions,
        })

    return {"items": result_items, "total": len(result_items)}


@router.get("/ledger/purchase-vendor")
async def get_purchase_vendor_ledger(
    supplier_id: str = Query(default=None, description="공급처 ID (없으면 전체)"),
    start_date: str = Query(default=None, description="시작일 YYYY-MM-DD"),
    end_date: str = Query(default=None, description="종료일 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """매입처원장 - 공급처별 매입/지급 내역과 누적잔액 조회"""

    # 매입 내역 조회
    purchase_where = ["1=1"]
    purchase_params: dict = {}
    if supplier_id:
        purchase_where.append("p.supplier_id = :supplier_id")
        purchase_params["supplier_id"] = supplier_id
    if start_date:
        purchase_where.append("p.purchase_date >= :start_date")
        purchase_params["start_date"] = start_date
    if end_date:
        purchase_where.append("p.purchase_date <= :end_date")
        purchase_params["end_date"] = end_date

    purchase_sql = " AND ".join(purchase_where)

    # 매입 내역 (상품 정보 포함)
    purchases_result = await db.execute(
        text(
            f"SELECT p.id, p.purchase_number AS slip_no, p.purchase_date AS date, "
            f"'매입' AS trans_type, "
            f"COALESCE(c.name, '알수없음') AS vendor_name, "
            f"p.supplier_id, "
            f"p.supply_amount, p.tax_amount, p.total_amount, "
            f"COALESCE(p.memo, '') AS memo "
            f"FROM purchases p "
            f"LEFT JOIN customers c ON c.id = p.supplier_id "
            f"WHERE {purchase_sql} "
            f"ORDER BY p.purchase_date, p.created_at"
        ),
        purchase_params,
    )
    purchase_rows = purchases_result.mappings().all()

    # 지급 내역 조회
    pay_where = ["pm.payment_type = '지급'"]
    pay_params: dict = {}
    if supplier_id:
        pay_where.append("pm.customer_id = :supplier_id")
        pay_params["supplier_id"] = supplier_id
    if start_date:
        pay_where.append("pm.payment_date >= :start_date")
        pay_params["start_date"] = start_date
    if end_date:
        pay_where.append("pm.payment_date <= :end_date")
        pay_params["end_date"] = end_date

    pay_sql = " AND ".join(pay_where)
    payments_result = await db.execute(
        text(
            f"SELECT pm.id, pm.payment_number AS slip_no, pm.payment_date AS date, "
            f"'지급' AS trans_type, "
            f"COALESCE(c.name, '알수없음') AS vendor_name, "
            f"pm.customer_id AS supplier_id, "
            f"0 AS supply_amount, 0 AS tax_amount, "
            f"-pm.amount AS total_amount, "
            f"COALESCE(pm.memo, '') AS memo "
            f"FROM payments pm "
            f"LEFT JOIN customers c ON c.id = pm.customer_id "
            f"WHERE {pay_sql} "
            f"ORDER BY pm.payment_date, pm.created_at"
        ),
        pay_params,
    )
    pay_rows = payments_result.mappings().all()

    # 모든 행을 합치고 날짜순 정렬
    all_rows = []
    for row in purchase_rows:
        all_rows.append(dict(row))
    for row in pay_rows:
        all_rows.append(dict(row))
    all_rows.sort(key=lambda x: (str(x["date"]), x["trans_type"]))

    # 전기이월 계산 (기간 이전)
    prev_balance = Decimal("0")
    if start_date:
        prev_purchase_result = await db.execute(
            text(
                "SELECT COALESCE(SUM(p.total_amount), 0) "
                "FROM purchases p WHERE p.purchase_date < :start_date"
                + (" AND p.supplier_id = :supplier_id" if supplier_id else "")
            ),
            {"start_date": start_date, **({"supplier_id": supplier_id} if supplier_id else {})},
        )
        prev_purchases = prev_purchase_result.scalar() or Decimal("0")

        prev_pay_result = await db.execute(
            text(
                "SELECT COALESCE(SUM(pm.amount), 0) "
                "FROM payments pm WHERE pm.payment_type = '지급' "
                "AND pm.payment_date < :start_date"
                + (" AND pm.customer_id = :supplier_id" if supplier_id else "")
            ),
            {"start_date": start_date, **({"supplier_id": supplier_id} if supplier_id else {})},
        )
        prev_payments = prev_pay_result.scalar() or Decimal("0")
        prev_balance = prev_purchases - prev_payments

    # 잔액 누적 계산
    running_balance = prev_balance
    items = []
    for idx, row in enumerate(all_rows):
        total = Decimal(str(row["total_amount"]))
        running_balance += total

        # 매입 항목의 첫 번째 상품명 조회
        product_name = ""
        spec = ""
        qty = 0
        unit_price = 0
        if row["trans_type"] == "매입":
            pi_result = await db.execute(
                text(
                    "SELECT product_name, spec, quantity, unit_price "
                    "FROM purchase_items WHERE purchase_id = :pid "
                    "ORDER BY sort_order LIMIT 1"
                ),
                {"pid": str(row["id"])},
            )
            pi_row = pi_result.mappings().first()
            if pi_row:
                product_name = pi_row["product_name"] or ""
                spec = pi_row["spec"] or ""
                qty = int(pi_row["quantity"] or 0)
                unit_price = float(pi_row["unit_price"] or 0)

        items.append({
            "id": str(idx + 1),
            "date": str(row["date"]),
            "slipNo": row["slip_no"] or "",
            "transType": row["trans_type"],
            "productName": product_name,
            "spec": spec,
            "qty": qty,
            "unitPrice": unit_price,
            "supplyAmount": float(row["supply_amount"] or 0),
            "tax": float(row["tax_amount"] or 0),
            "totalAmount": float(total),
            "balance": float(running_balance),
            "memo": row["memo"] or "",
        })

    return {
        "items": items,
        "total": len(items),
        "previousBalance": float(prev_balance),
    }


# ============================================
# 보고서 (Reports) API
# ============================================

@router.get("/reports/monthly-sales")
async def get_monthly_sales_report(
    year: int = Query(..., description="년도"),
    month: int = Query(default=None, description="월 (없으면 연간)"),
    db: AsyncSession = Depends(get_db),
):
    """월간 매출현황 - 거래처별/월별 매출 집계"""

    where_clauses = [
        "EXTRACT(YEAR FROM s.sale_date) = :year"
    ]
    params: dict = {"year": year}

    if month:
        where_clauses.append("EXTRACT(MONTH FROM s.sale_date) = :month")
        params["month"] = month

    where_sql = " AND ".join(where_clauses)

    result = await db.execute(
        text(
            f"SELECT "
            f"  c.id AS customer_id, "
            f"  c.code AS customer_code, "
            f"  c.name AS customer_name, "
            f"  EXTRACT(MONTH FROM s.sale_date)::int AS sale_month, "
            f"  COUNT(s.id) AS sale_count, "
            f"  COALESCE(SUM(s.supply_amount), 0) AS supply_amount, "
            f"  COALESCE(SUM(s.tax_amount), 0) AS tax_amount, "
            f"  COALESCE(SUM(s.total_amount), 0) AS total_amount, "
            f"  COALESCE(SUM(s.cost_amount), 0) AS cost_amount, "
            f"  COALESCE(SUM(s.profit_amount), 0) AS profit_amount "
            f"FROM sales s "
            f"LEFT JOIN customers c ON c.id = s.customer_id "
            f"WHERE {where_sql} "
            f"GROUP BY c.id, c.code, c.name, EXTRACT(MONTH FROM s.sale_date) "
            f"ORDER BY c.name, sale_month"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for row in rows:
        supply = float(row["supply_amount"] or 0)
        total = float(row["total_amount"] or 0)
        cost = float(row["cost_amount"] or 0)
        profit = float(row["profit_amount"] or 0)
        profit_rate = (profit / supply * 100) if supply > 0 else 0

        items.append({
            "customerId": str(row["customer_id"]) if row["customer_id"] else None,
            "customerCode": row["customer_code"] or "",
            "customerName": row["customer_name"] or "기타",
            "month": int(row["sale_month"]),
            "saleCount": int(row["sale_count"]),
            "supplyAmount": supply,
            "taxAmount": float(row["tax_amount"] or 0),
            "totalAmount": total,
            "costAmount": cost,
            "profitAmount": profit,
            "profitRate": round(profit_rate, 1),
        })

    # 월별 소계
    monthly_totals = {}
    for item in items:
        m = item["month"]
        if m not in monthly_totals:
            monthly_totals[m] = {
                "month": m,
                "saleCount": 0,
                "supplyAmount": 0,
                "taxAmount": 0,
                "totalAmount": 0,
                "costAmount": 0,
                "profitAmount": 0,
            }
        monthly_totals[m]["saleCount"] += item["saleCount"]
        monthly_totals[m]["supplyAmount"] += item["supplyAmount"]
        monthly_totals[m]["taxAmount"] += item["taxAmount"]
        monthly_totals[m]["totalAmount"] += item["totalAmount"]
        monthly_totals[m]["costAmount"] += item["costAmount"]
        monthly_totals[m]["profitAmount"] += item["profitAmount"]

    for mt in monthly_totals.values():
        mt["profitRate"] = round(
            (mt["profitAmount"] / mt["supplyAmount"] * 100) if mt["supplyAmount"] > 0 else 0, 1
        )

    return {
        "year": year,
        "month": month,
        "items": items,
        "monthlyTotals": list(monthly_totals.values()),
        "total": len(items),
    }


@router.get("/reports/monthly-purchases")
async def get_monthly_purchases_report(
    year: int = Query(..., description="년도"),
    month: int = Query(default=None, description="월 (없으면 연간)"),
    db: AsyncSession = Depends(get_db),
):
    """월간 매입현황 - 공급처별/월별 매입 집계"""

    where_clauses = [
        "EXTRACT(YEAR FROM p.purchase_date) = :year"
    ]
    params: dict = {"year": year}

    if month:
        where_clauses.append("EXTRACT(MONTH FROM p.purchase_date) = :month")
        params["month"] = month

    where_sql = " AND ".join(where_clauses)

    result = await db.execute(
        text(
            f"SELECT "
            f"  c.id AS supplier_id, "
            f"  c.code AS supplier_code, "
            f"  c.name AS supplier_name, "
            f"  EXTRACT(MONTH FROM p.purchase_date)::int AS purchase_month, "
            f"  COUNT(p.id) AS purchase_count, "
            f"  COALESCE(SUM(p.supply_amount), 0) AS supply_amount, "
            f"  COALESCE(SUM(p.tax_amount), 0) AS tax_amount, "
            f"  COALESCE(SUM(p.total_amount), 0) AS total_amount "
            f"FROM purchases p "
            f"LEFT JOIN customers c ON c.id = p.supplier_id "
            f"WHERE {where_sql} "
            f"GROUP BY c.id, c.code, c.name, EXTRACT(MONTH FROM p.purchase_date) "
            f"ORDER BY c.name, purchase_month"
        ),
        params,
    )
    rows = result.mappings().all()

    items = []
    for row in rows:
        items.append({
            "supplierId": str(row["supplier_id"]) if row["supplier_id"] else None,
            "supplierCode": row["supplier_code"] or "",
            "supplierName": row["supplier_name"] or "기타",
            "month": int(row["purchase_month"]),
            "purchaseCount": int(row["purchase_count"]),
            "supplyAmount": float(row["supply_amount"] or 0),
            "taxAmount": float(row["tax_amount"] or 0),
            "totalAmount": float(row["total_amount"] or 0),
        })

    # 월별 소계
    monthly_totals = {}
    for item in items:
        m = item["month"]
        if m not in monthly_totals:
            monthly_totals[m] = {
                "month": m,
                "purchaseCount": 0,
                "supplyAmount": 0,
                "taxAmount": 0,
                "totalAmount": 0,
            }
        monthly_totals[m]["purchaseCount"] += item["purchaseCount"]
        monthly_totals[m]["supplyAmount"] += item["supplyAmount"]
        monthly_totals[m]["taxAmount"] += item["taxAmount"]
        monthly_totals[m]["totalAmount"] += item["totalAmount"]

    return {
        "year": year,
        "month": month,
        "items": items,
        "monthlyTotals": list(monthly_totals.values()),
        "total": len(items),
    }


@router.get("/reports/summary")
async def get_sales_purchase_summary(
    year: int = Query(..., description="년도"),
    db: AsyncSession = Depends(get_db),
):
    """매출매입 종합 - 월별 매출/매입/순이익 집계"""

    # 월별 매출 집계
    sales_result = await db.execute(
        text(
            "SELECT "
            "  EXTRACT(MONTH FROM s.sale_date)::int AS month, "
            "  COUNT(s.id) AS sales_qty, "
            "  COALESCE(SUM(s.supply_amount), 0) AS sales_supply, "
            "  COALESCE(SUM(s.total_amount), 0) AS sales_amount, "
            "  COALESCE(SUM(s.cost_amount), 0) AS sales_cost, "
            "  COALESCE(SUM(s.profit_amount), 0) AS sales_profit "
            "FROM sales s "
            "WHERE EXTRACT(YEAR FROM s.sale_date) = :year "
            "GROUP BY EXTRACT(MONTH FROM s.sale_date) "
            "ORDER BY month"
        ),
        {"year": year},
    )
    sales_rows = {int(r["month"]): dict(r) for r in sales_result.mappings().all()}

    # 월별 매입 집계
    purchase_result = await db.execute(
        text(
            "SELECT "
            "  EXTRACT(MONTH FROM p.purchase_date)::int AS month, "
            "  COUNT(p.id) AS purchase_qty, "
            "  COALESCE(SUM(p.total_amount), 0) AS purchase_amount "
            "FROM purchases p "
            "WHERE EXTRACT(YEAR FROM p.purchase_date) = :year "
            "GROUP BY EXTRACT(MONTH FROM p.purchase_date) "
            "ORDER BY month"
        ),
        {"year": year},
    )
    purchase_rows = {int(r["month"]): dict(r) for r in purchase_result.mappings().all()}

    # 12개월 데이터 조합
    monthly_data = []
    for m in range(1, 13):
        s = sales_rows.get(m, {})
        p = purchase_rows.get(m, {})

        sales_amount = float(s.get("sales_amount", 0) or 0)
        sales_cost = float(s.get("sales_cost", 0) or 0)
        sales_profit = float(s.get("sales_profit", 0) or 0)
        sales_supply = float(s.get("sales_supply", 0) or 0)
        purchase_amount = float(p.get("purchase_amount", 0) or 0)
        net_profit = sales_profit

        profit_rate = (sales_profit / sales_supply * 100) if sales_supply > 0 else 0

        monthly_data.append({
            "month": f"{year}-{m:02d}",
            "salesQty": int(s.get("sales_qty", 0) or 0),
            "salesAmount": sales_amount,
            "salesCost": sales_cost,
            "salesProfit": sales_profit,
            "salesProfitRate": round(profit_rate, 1),
            "purchaseQty": int(p.get("purchase_qty", 0) or 0),
            "purchaseAmount": purchase_amount,
            "netProfit": net_profit,
        })

    # 연간 합계
    totals = {
        "salesQty": sum(d["salesQty"] for d in monthly_data),
        "salesAmount": sum(d["salesAmount"] for d in monthly_data),
        "salesCost": sum(d["salesCost"] for d in monthly_data),
        "salesProfit": sum(d["salesProfit"] for d in monthly_data),
        "purchaseQty": sum(d["purchaseQty"] for d in monthly_data),
        "purchaseAmount": sum(d["purchaseAmount"] for d in monthly_data),
        "netProfit": sum(d["netProfit"] for d in monthly_data),
    }
    totals["salesProfitRate"] = round(
        (totals["salesProfit"] / totals["salesAmount"] * 100) if totals["salesAmount"] > 0 else 0, 1
    )

    return {
        "year": year,
        "monthlyData": monthly_data,
        "totals": totals,
    }


# ============================================
# 대시보드 (Dashboard) API
# ============================================

@router.get("/dashboard/sales-chart", response_model=List[SalesChartData])
async def get_sales_chart(
    period: str = Query("monthly", enum=["daily", "weekly", "monthly"]),
    months: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """매출 차트 데이터 조회"""
    from datetime import timedelta

    now = datetime.utcnow()
    result_data: list[SalesChartData] = []

    if period == "monthly":
        # 월별 집계 - SQL GROUP BY
        chart_result = await db.execute(
            text(
                "SELECT TO_CHAR(sale_date, 'YYYY-MM') AS period, "
                "COALESCE(SUM(total_amount), 0) AS amount "
                "FROM sales "
                "WHERE sale_date >= (CURRENT_DATE - :interval_days * INTERVAL '1 day') "
                "GROUP BY TO_CHAR(sale_date, 'YYYY-MM') "
                "ORDER BY period"
            ),
            {"interval_days": months * 31},
        )
        rows = chart_result.mappings().all()
        db_data = {r["period"]: r["amount"] for r in rows}

        for i in range(months - 1, -1, -1):
            target_date = now - timedelta(days=30 * i)
            month_key = target_date.strftime("%Y-%m")
            result_data.append(SalesChartData(
                period=month_key,
                amount=db_data.get(month_key, Decimal("0")),
            ))

    elif period == "weekly":
        # 주별 집계
        chart_result = await db.execute(
            text(
                "SELECT TO_CHAR(sale_date, 'IYYY-\"W\"IW') AS period, "
                "COALESCE(SUM(total_amount), 0) AS amount "
                "FROM sales "
                "WHERE sale_date >= (CURRENT_DATE - :interval_days * INTERVAL '1 day') "
                "GROUP BY TO_CHAR(sale_date, 'IYYY-\"W\"IW') "
                "ORDER BY period"
            ),
            {"interval_days": months * 31},
        )
        rows = chart_result.mappings().all()
        db_data = {r["period"]: r["amount"] for r in rows}

        for i in range(months * 4 - 1, -1, -1):
            target_date = now - timedelta(weeks=i)
            week_key = target_date.strftime("%Y-W%W")
            result_data.append(SalesChartData(
                period=week_key,
                amount=db_data.get(week_key, Decimal("0")),
            ))

    elif period == "daily":
        # 일별 집계
        chart_result = await db.execute(
            text(
                "SELECT TO_CHAR(sale_date, 'YYYY-MM-DD') AS period, "
                "COALESCE(SUM(total_amount), 0) AS amount "
                "FROM sales "
                "WHERE sale_date >= (CURRENT_DATE - 30 * INTERVAL '1 day') "
                "GROUP BY TO_CHAR(sale_date, 'YYYY-MM-DD') "
                "ORDER BY period"
            )
        )
        rows = chart_result.mappings().all()
        db_data = {r["period"]: r["amount"] for r in rows}

        for i in range(29, -1, -1):
            target_date = now - timedelta(days=i)
            day_key = target_date.strftime("%Y-%m-%d")
            result_data.append(SalesChartData(
                period=day_key,
                amount=db_data.get(day_key, Decimal("0")),
            ))

    return result_data


# ============================================
# 직원 (Employee) API
# ============================================

from pydantic import BaseModel as _BaseModel


class EmployeeResponse(_BaseModel):
    id: str
    code: str
    name: str
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class EmployeeCreate(_BaseModel):
    code: str
    name: str
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[str] = None
    is_active: bool = True


class EmployeeUpdate(_BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(db: AsyncSession = Depends(get_db)):
    """직원 목록 조회"""
    # employees 테이블 존재 확인 및 자동 생성
    try:
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS employees (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                department VARCHAR(50),
                position VARCHAR(50),
                phone VARCHAR(20),
                email VARCHAR(200),
                hire_date VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await db.commit()
    except Exception:
        await db.rollback()

    result = await db.execute(
        text("SELECT id, code, name, department, position, phone, email, hire_date, is_active FROM employees ORDER BY code")
    )
    rows = result.mappings().all()
    return [EmployeeResponse(**{**dict(r), "id": str(r["id"])}) for r in rows]


@router.post("/employees", response_model=EmployeeResponse, status_code=201)
async def create_employee(body: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    """직원 등록"""
    import uuid as _uuid

    emp_id = str(_uuid.uuid4())
    try:
        await db.execute(
            text("""
                INSERT INTO employees (id, code, name, department, position, phone, email, hire_date, is_active)
                VALUES (:id, :code, :name, :department, :position, :phone, :email, :hire_date, :is_active)
            """),
            {
                "id": emp_id,
                "code": body.code,
                "name": body.name,
                "department": body.department,
                "position": body.position,
                "phone": body.phone,
                "email": body.email,
                "hire_date": body.hire_date,
                "is_active": body.is_active,
            },
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"직원 등록 실패: {str(e)}")

    return EmployeeResponse(
        id=emp_id, code=body.code, name=body.name,
        department=body.department, position=body.position,
        phone=body.phone, email=body.email,
        hire_date=body.hire_date, is_active=body.is_active,
    )


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, body: EmployeeUpdate, db: AsyncSession = Depends(get_db)):
    """직원 수정"""
    updates = []
    params = {"emp_id": employee_id}

    for field in ["code", "name", "department", "position", "phone", "email", "hire_date", "is_active"]:
        val = getattr(body, field, None)
        if val is not None:
            updates.append(f"{field} = :{field}")
            params[field] = val

    if not updates:
        raise HTTPException(status_code=400, detail="수정할 항목이 없습니다.")

    updates.append("updated_at = NOW()")
    await db.execute(
        text(f"UPDATE employees SET {', '.join(updates)} WHERE id = :emp_id::uuid"),
        params,
    )
    await db.commit()

    result = await db.execute(
        text("SELECT id, code, name, department, position, phone, email, hire_date, is_active FROM employees WHERE id = :emp_id::uuid"),
        {"emp_id": employee_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
    return EmployeeResponse(**{**dict(row), "id": str(row["id"])})


@router.delete("/employees/{employee_id}", status_code=204)
async def delete_employee(employee_id: str, db: AsyncSession = Depends(get_db)):
    """직원 삭제"""
    result = await db.execute(
        text("DELETE FROM employees WHERE id = :emp_id::uuid"),
        {"emp_id": employee_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
