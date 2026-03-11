"""
KIS ERP - 거래처 관리 API
거래처(매출처/매입처) CRUD 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.erp import Customer, CustomerType

# Import Service (kis_erp_core now in src/)
from kis_erp_core.services.customer_service import CustomerService
from kis_erp_core.models.erp_models import CustomerCreate, CustomerUpdate, CustomerFilter

router = APIRouter(prefix="/customers", tags=["ERP - 거래처"])


@router.get("", response_model=List[Customer], summary="거래처 목록 조회")
async def list_customers(
    customer_type: Optional[CustomerType] = Query(None, description="거래처 유형 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    search: Optional[str] = Query(None, description="거래처명/코드 검색"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    db: AsyncSession = Depends(get_db),
) -> List[Customer]:
    """
    거래처 목록을 조회합니다.

    - **customer_type**: buyer(매출처), supplier(매입처), both(양쪽) 필터
    - **is_active**: 거래 중인 거래처만 조회
    - **search**: 거래처명 또는 코드로 검색
    """
    service = CustomerService()
    filters = CustomerFilter(type=customer_type, is_active=is_active, search=search)
    results = await service.list_customers(db, filters, skip, limit)
    return [Customer(**r) for r in results]


@router.get("/{customer_id}", response_model=Customer, summary="거래처 상세 조회")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """
    거래처 상세 정보를 조회합니다.
    """
    service = CustomerService()
    result = await service.get_customer(db, UUID(customer_id))
    if not result:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    return Customer(**result)


@router.post("", response_model=Customer, status_code=201, summary="거래처 등록")
async def create_customer(
    customer: Customer,
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """
    새 거래처를 등록합니다.

    필수 항목:
    - **name**: 거래처명
    - **type**: 거래처 유형 (매출/매입/겸용)
    """
    service = CustomerService()
    data = CustomerCreate(
        name=customer.name,
        type=customer.type,
        business_number=customer.business_number,
        ceo=customer.ceo,
        contact=customer.contact,
        address=customer.address,
        tel=customer.tel,
        fax=customer.fax,
        email=customer.email,
        mobile=customer.mobile,
        credit_limit=customer.credit_limit,
        payment_terms=customer.payment_terms,
        bank_info=customer.bank_info,
        memo=customer.memo,
    )
    result = await service.create_customer(db, data)
    await db.commit()
    return Customer(**result)


@router.put("/{customer_id}", response_model=Customer, summary="거래처 수정")
async def update_customer(
    customer_id: str,
    customer: Customer,
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """
    거래처 정보를 수정합니다.
    """
    service = CustomerService()
    data = CustomerUpdate(
        name=customer.name,
        type=customer.type,
        business_number=customer.business_number,
        ceo=customer.ceo,
        contact=customer.contact,
        address=customer.address,
        tel=customer.tel,
        fax=customer.fax,
        email=customer.email,
        mobile=customer.mobile,
        credit_limit=customer.credit_limit,
        payment_terms=customer.payment_terms,
        bank_info=customer.bank_info,
        memo=customer.memo,
        is_active=customer.is_active,
    )
    result = await service.update_customer(db, UUID(customer_id), data)
    if not result:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    await db.commit()
    return Customer(**result)


@router.delete("/{customer_id}", status_code=204, summary="거래처 삭제")
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    거래처를 삭제합니다. (소프트 삭제: is_active=False)
    """
    service = CustomerService()
    success = await service.delete_customer(db, UUID(customer_id))
    if not success:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다")
    await db.commit()


@router.get("/{customer_id}/balance", summary="거래처별 잔액 조회")
async def get_customer_balance(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    거래처의 미수금/미지급금 잔액을 조회합니다.
    """
    service = CustomerService()
    balance = await service.get_balance(db, UUID(customer_id))
    return {
        "customer_id": customer_id,
        "balance": float(balance),
    }
