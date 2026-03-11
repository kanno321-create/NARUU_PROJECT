"""
KIS ERP - 자사정보 관리 API
회사 정보 등록/조회/수정 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.erp import CompanyInfo

# Import Service (kis_erp_core now in src/)
from kis_erp_core.services.company_service import CompanyService
from kis_erp_core.models.erp_models import CompanyCreate, CompanyUpdate

router = APIRouter(prefix="/company", tags=["ERP - 자사정보"])


@router.get("", response_model=CompanyInfo, summary="자사정보 조회")
async def get_company_info(
    db: AsyncSession = Depends(get_db),
) -> CompanyInfo:
    """
    자사 정보를 조회합니다.
    시스템에는 하나의 자사정보만 존재합니다.
    """
    service = CompanyService()
    result = await service.get_company(db)
    if not result:
        raise HTTPException(status_code=404, detail="자사정보가 등록되지 않았습니다")
    return CompanyInfo(**result)


@router.post("", response_model=CompanyInfo, status_code=201, summary="자사정보 등록")
async def create_company_info(
    company: CompanyInfo,
    db: AsyncSession = Depends(get_db),
) -> CompanyInfo:
    """
    자사 정보를 등록합니다.
    시스템에는 하나의 자사정보만 존재할 수 있습니다.
    """
    service = CompanyService()
    data = CompanyCreate(
        business_number=company.business_number,
        name=company.name,
        ceo=company.ceo,
        address=company.address,
        tel=company.tel,
        fax=company.fax,
        email=company.email,
        bank_info=company.bank_info,
        business_type=company.business_type,
        business_item=company.business_item,
        logo_path=company.logo_path,
        stamp_path=company.stamp_path,
    )
    try:
        result = await service.create_company(db, data)
        await db.commit()
        return CompanyInfo(**result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("", response_model=CompanyInfo, summary="자사정보 수정")
async def update_company_info(
    company: CompanyInfo,
    db: AsyncSession = Depends(get_db),
) -> CompanyInfo:
    """
    자사 정보를 수정합니다.
    """
    service = CompanyService()
    data = CompanyUpdate(
        name=company.name,
        ceo=company.ceo,
        address=company.address,
        tel=company.tel,
        fax=company.fax,
        email=company.email,
        bank_info=company.bank_info,
        business_type=company.business_type,
        business_item=company.business_item,
        logo_path=company.logo_path,
        stamp_path=company.stamp_path,
    )
    result = await service.update_company(db, data)
    if not result:
        raise HTTPException(status_code=404, detail="자사정보를 찾을 수 없습니다")
    await db.commit()
    return CompanyInfo(**result)
