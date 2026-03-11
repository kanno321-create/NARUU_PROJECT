"""
KIS ERP - 상품 관리 API
상품정보 CRUD 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.erp import Product

# Import Service (kis_erp_core now in src/)
from kis_erp_core.services.product_service import ProductService
from kis_erp_core.models.product_employee_models import ProductCreate, ProductUpdate, ProductFilter

router = APIRouter(prefix="/products", tags=["ERP - 상품"])


@router.get("", response_model=List[Product], summary="상품 목록 조회")
async def list_products(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    is_active: Optional[bool] = Query(None, description="판매 중 필터"),
    search: Optional[str] = Query(None, description="상품명/코드 검색"),
    low_stock: Optional[bool] = Query(None, description="재고 부족 상품만"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    db: AsyncSession = Depends(get_db),
) -> List[Product]:
    """
    상품 목록을 조회합니다.

    - **category**: 카테고리별 필터
    - **is_active**: 판매 중인 상품만 조회
    - **search**: 상품명 또는 코드로 검색
    - **low_stock**: 최소 재고량 미만 상품만 조회
    """
    service = ProductService()
    filters = ProductFilter(category=category, is_active=is_active, search=search)
    results = await service.list_products(db, filters, skip, limit)
    return [Product(**r) for r in results]


@router.get("/{product_id}", response_model=Product, summary="상품 상세 조회")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> Product:
    """
    상품 상세 정보를 조회합니다.
    """
    service = ProductService()
    result = await service.get_product(db, UUID(product_id))
    if not result:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return Product(**result)


@router.post("", response_model=Product, status_code=201, summary="상품 등록")
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> Product:
    """
    새 상품을 등록합니다.

    필수 항목:
    - **code**: 상품코드 (중복 불가)
    - **name**: 상품명
    - **unit_price**: 판매단가
    """
    service = ProductService()
    result = await service.create_product(db, product)
    await db.commit()
    return Product(**result)


@router.put("/{product_id}", response_model=Product, summary="상품 수정")
async def update_product(
    product_id: str,
    product: Product,
    db: AsyncSession = Depends(get_db),
) -> Product:
    """
    상품 정보를 수정합니다.
    """
    service = ProductService()
    data = ProductUpdate(
        name=product.name,
        category=product.category,
        unit=product.unit,
        unit_cost=product.unit_cost,
        sale_price=product.sale_price,
        spec=product.spec,
        manufacturer=product.manufacturer,
        is_active=product.is_active,
    )
    result = await service.update_product(db, UUID(product_id), data)
    if not result:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    await db.commit()
    return Product(**result)


@router.delete("/{product_id}", status_code=204, summary="상품 삭제")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    상품을 삭제합니다. (소프트 삭제: is_active=False)
    """
    service = ProductService()
    success = await service.delete_product(db, UUID(product_id))
    if not success:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    await db.commit()


@router.patch("/{product_id}/stock", response_model=Product, summary="재고 수량 조정")
async def adjust_stock(
    product_id: str,
    adjustment: int = Query(..., description="조정 수량 (+/-)"),
    reason: Optional[str] = Query(None, description="조정 사유"),
    db: AsyncSession = Depends(get_db),
) -> Product:
    """
    상품 재고 수량을 조정합니다.

    - **adjustment**: 양수면 증가, 음수면 감소
    - **reason**: 재고 조정 사유 기록
    """
    service = ProductService()
    result = await service.adjust_stock(db, UUID(product_id), Decimal(adjustment), reason or "수동 조정")
    if not result:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    await db.commit()
    return Product(**result)


@router.get("/{product_id}/stock-history", summary="재고 변동 이력 조회")
async def get_stock_history(
    product_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    상품의 재고 변동 이력을 조회합니다.

    Note: 재고 이력 테이블 미구현으로 현재 빈 배열 반환
    """
    # 재고 이력 테이블 추가 시 ProductService.get_stock_history() 구현 필요
    return []
