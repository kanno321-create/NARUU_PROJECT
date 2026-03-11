"""
KIS ERP - 은행계좌 관리 API
은행계좌 등록/조회/수정/삭제 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.erp import BankAccount
from kis_erp_core.services.bank_account_service import BankAccountService

router = APIRouter(prefix="/bank-accounts", tags=["ERP - 은행계좌"])


@router.get("", response_model=List[BankAccount], summary="은행계좌 목록 조회")
async def list_bank_accounts(
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    search: Optional[str] = Query(None, description="은행명/계좌번호/계좌명 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[BankAccount]:
    """은행계좌 목록을 조회합니다."""
    service = BankAccountService()
    results = await service.list_accounts(db, is_active, search, skip, limit)
    return [BankAccount(**r) for r in results]


@router.post("", response_model=BankAccount, status_code=201, summary="은행계좌 등록")
async def create_bank_account(
    account: BankAccount,
    db: AsyncSession = Depends(get_db),
) -> BankAccount:
    """신규 은행계좌를 등록합니다."""
    service = BankAccountService()
    data = account.model_dump(exclude_unset=True, exclude={"id", "created_at", "updated_at"})
    result = await service.create_account(db, data)
    await db.commit()
    return BankAccount(**result)


@router.get("/{account_id}", response_model=BankAccount, summary="은행계좌 상세 조회")
async def get_bank_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> BankAccount:
    """은행계좌 상세 정보를 조회합니다."""
    service = BankAccountService()
    result = await service.get_account(db, account_id)
    if not result:
        raise HTTPException(status_code=404, detail="은행계좌를 찾을 수 없습니다")
    return BankAccount(**result)


@router.put("/{account_id}", response_model=BankAccount, summary="은행계좌 수정")
async def update_bank_account(
    account_id: str,
    account: BankAccount,
    db: AsyncSession = Depends(get_db),
) -> BankAccount:
    """은행계좌 정보를 수정합니다."""
    service = BankAccountService()
    data = account.model_dump(exclude_unset=True, exclude={"id", "created_at", "updated_at"})
    result = await service.update_account(db, account_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="은행계좌를 찾을 수 없습니다")
    await db.commit()
    return BankAccount(**result)


@router.delete("/{account_id}", status_code=204, summary="은행계좌 삭제")
async def delete_bank_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """은행계좌를 비활성화합니다."""
    service = BankAccountService()
    success = await service.delete_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="은행계좌를 찾을 수 없습니다")
    await db.commit()
