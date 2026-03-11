"""
KIS ERP - 회계 관리 API
계정과목, 분개장, 재무보고서 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

from kis_erp_core.services.account_service import AccountService
from kis_erp_core.services.journal_service import JournalService
from kis_erp_core.models.accounting_models import (
    Account,
    AccountCreate,
    AccountUpdate,
    AccountFilter,
    AccountType,
    JournalEntry,
    JournalEntryCreate,
    JournalEntryFilter,
    JournalStatus,
    TrialBalance,
    BalanceSheet,
    ProfitLoss,
)

router = APIRouter(prefix="/accounting", tags=["ERP - 회계"])


# ========== 계정과목 ==========


@router.get("/accounts", response_model=List[Account], summary="계정과목 목록 조회")
async def list_accounts(
    account_type: Optional[AccountType] = Query(None, description="계정유형 필터"),
    is_group: Optional[bool] = Query(None, description="그룹 계정 필터"),
    is_active: Optional[bool] = Query(True, description="활성 상태 필터"),
    parent_id: Optional[str] = Query(None, description="상위 계정 ID"),
    search: Optional[str] = Query(None, description="계정명/코드 검색"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    db: AsyncSession = Depends(get_db),
) -> List[Account]:
    """
    계정과목 목록을 조회합니다.

    - **account_type**: asset/liability/equity/revenue/expense 필터
    - **is_group**: 그룹 계정만 조회
    - **search**: 계정명 또는 코드로 검색
    """
    service = AccountService()
    filters = AccountFilter(
        account_type=account_type,
        is_group=is_group,
        is_active=is_active,
        parent_id=parent_id,
        search=search,
    )
    results = await service.list_accounts(db, filters, skip, limit)
    return [Account(**r) for r in results]


@router.get(
    "/accounts/{account_id}",
    response_model=Account,
    summary="계정과목 상세 조회",
)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
) -> Account:
    """계정과목 상세 정보를 조회합니다."""
    service = AccountService()
    result = await service.get_account(db, account_id)
    if not result:
        raise HTTPException(status_code=404, detail="계정과목을 찾을 수 없습니다")
    return Account(**result)


@router.post(
    "/accounts",
    response_model=Account,
    status_code=201,
    summary="계정과목 생성",
)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
) -> Account:
    """
    새 계정과목을 등록합니다.

    필수 항목:
    - **account_code**: 계정코드 (예: 1010)
    - **account_name**: 계정명 (예: 현금)
    - **account_type**: 유형 (asset/liability/equity/revenue/expense)
    - **balance_direction**: 잔액 방향 (debit/credit)
    """
    service = AccountService()
    try:
        result = await service.create_account(db, data)
        await db.commit()
        return Account(**result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/accounts/{account_id}",
    response_model=Account,
    summary="계정과목 수정",
)
async def update_account(
    account_id: str,
    data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
) -> Account:
    """계정과목 정보를 수정합니다."""
    service = AccountService()
    try:
        result = await service.update_account(db, account_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="계정과목을 찾을 수 없습니다")
    await db.commit()
    return Account(**result)


# ========== 분개장 ==========


@router.get(
    "/journal-entries",
    response_model=List[JournalEntry],
    summary="분개 목록 조회",
)
async def list_journal_entries(
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    account_id: Optional[str] = Query(None, description="계정과목 ID"),
    status: Optional[JournalStatus] = Query(None, description="상태 필터"),
    voucher_id: Optional[str] = Query(None, description="전표 ID"),
    search: Optional[str] = Query(None, description="적요 검색"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    db: AsyncSession = Depends(get_db),
) -> List[JournalEntry]:
    """
    분개 목록을 조회합니다.

    - **start_date/end_date**: 기간 필터
    - **account_id**: 특정 계정이 포함된 분개만
    - **status**: draft/posted/cancelled 필터
    """
    service = JournalService()
    filters = JournalEntryFilter(
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        status=status,
        voucher_id=voucher_id,
        search=search,
    )
    results = await service.list_entries(db, filters, skip, limit)
    return [JournalEntry(**r) for r in results]


@router.get(
    "/journal-entries/{entry_id}",
    response_model=JournalEntry,
    summary="분개 상세 조회",
)
async def get_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> JournalEntry:
    """분개 상세 정보를 조회합니다 (항목 포함)."""
    service = JournalService()
    result = await service.get_entry(db, entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="분개를 찾을 수 없습니다")
    return JournalEntry(**result)


@router.post(
    "/journal-entries",
    response_model=JournalEntry,
    status_code=201,
    summary="분개 생성",
)
async def create_journal_entry(
    data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> JournalEntry:
    """
    새 분개를 생성합니다 (복식부기).

    규칙:
    - 최소 2개 항목 필수 (차변 + 대변)
    - SUM(차변) == SUM(대변) 필수
    - 생성 시 상태는 draft
    """
    service = JournalService()
    try:
        result = await service.create_journal_entry(db, data)
        await db.commit()
        return JournalEntry(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/journal-entries/{entry_id}/post",
    response_model=JournalEntry,
    summary="분개 전기",
)
async def post_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> JournalEntry:
    """
    분개를 전기합니다 (draft -> posted).

    전기 후에는 수정 불가, 취소만 가능합니다.
    """
    service = JournalService()
    try:
        result = await service.post_entry(db, entry_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="분개를 찾을 수 없습니다")
    await db.commit()
    return JournalEntry(**result)


@router.post(
    "/journal-entries/{entry_id}/cancel",
    response_model=JournalEntry,
    summary="분개 취소",
)
async def cancel_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> JournalEntry:
    """
    분개를 취소합니다 (posted -> cancelled).

    취소 시 역분개가 자동 생성됩니다.
    """
    service = JournalService()
    try:
        result = await service.cancel_entry(db, entry_id)
        await db.commit()
        return JournalEntry(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 재무보고서 ==========


@router.get(
    "/reports/trial-balance",
    response_model=TrialBalance,
    summary="시산표 조회",
)
async def get_trial_balance(
    as_of_date: date = Query(..., description="기준일"),
    db: AsyncSession = Depends(get_db),
) -> TrialBalance:
    """
    시산표를 조회합니다.

    posted 상태의 분개만 반영됩니다.
    """
    service = JournalService()
    result = await service.get_trial_balance(db, as_of_date)
    return TrialBalance(**result)


@router.get(
    "/reports/balance-sheet",
    response_model=BalanceSheet,
    summary="대차대조표 조회",
)
async def get_balance_sheet(
    as_of_date: date = Query(..., description="기준일"),
    db: AsyncSession = Depends(get_db),
) -> BalanceSheet:
    """
    대차대조표를 조회합니다.

    자산 = 부채 + 자본
    """
    service = JournalService()
    result = await service.get_balance_sheet(db, as_of_date)
    return BalanceSheet(**result)


@router.get(
    "/reports/profit-loss",
    response_model=ProfitLoss,
    summary="손익계산서 조회",
)
async def get_profit_loss(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    db: AsyncSession = Depends(get_db),
) -> ProfitLoss:
    """
    손익계산서를 조회합니다.

    순이익 = 수익 - 비용
    """
    service = JournalService()
    result = await service.get_profit_loss(db, start_date, end_date)
    return ProfitLoss(**result)
