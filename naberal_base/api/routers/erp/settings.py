"""
KIS ERP - 환경설정 API (Phase 3-B: Simplified)
일반설정(JSONB) + 사업장 마감 5개 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from kis_erp_core.services.settings_service import SettingsService

# ==================== Pydantic Models ====================

class GeneralSettingsResponse(BaseModel):
    """일반 환경설정 응답"""
    fiscal_year_start_month: int = 1
    tax_rate: float = 10.0
    currency: str = "KRW"
    decimal_places: int = 0
    voucher_number_format: str = "{TYPE}-{YYYYMMDD}-{SEQ:04d}"
    order_number_format: str = "PO-{YYYYMMDD}-{SEQ:04d}"
    statement_number_format: str = "{TYPE}-{YYYYMMDD}-{SEQ:04d}"
    cost_method: str = "moving_average"
    allow_negative_stock: bool = False
    low_stock_alert: bool = True
    updated_at: datetime | None = None


class GeneralSettingsUpdate(BaseModel):
    """일반 환경설정 수정 요청"""
    fiscal_year_start_month: int | None = None
    tax_rate: float | None = None
    currency: str | None = None
    decimal_places: int | None = None
    cost_method: str | None = None
    allow_negative_stock: bool | None = None
    low_stock_alert: bool | None = None


class UserPreferencesResponse(BaseModel):
    """사용자 UI 환경설정 응답 (표시항목 등)"""
    column_preferences: dict[str, list[str]] = {}


class UserPreferencesUpdate(BaseModel):
    """사용자 UI 환경설정 수정 요청"""
    column_preferences: dict[str, list[str]]


class BusinessPeriodResponse(BaseModel):
    """사업장 마감 응답"""
    id: str
    year: int
    month: int
    is_closed: bool = False
    closed_at: datetime | None = None
    notes: str | None = None


# ==================== Router ====================

router = APIRouter(prefix="/settings", tags=["ERP - 환경설정"])


@router.get(
    "/general",
    response_model=GeneralSettingsResponse,
    summary="기본설정 조회",
)
async def get_general_settings(
    db: AsyncSession = Depends(get_db),
) -> GeneralSettingsResponse:
    """
    시스템 기본설정을 조회합니다.
    단일행 JSONB에서 설정값을 읽어 반환합니다.
    """
    service = SettingsService()
    result = await service.get_settings(db)
    return GeneralSettingsResponse(**result)


@router.put(
    "/general",
    response_model=GeneralSettingsResponse,
    summary="기본설정 수정",
)
async def update_general_settings(
    body: GeneralSettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> GeneralSettingsResponse:
    """
    시스템 기본설정을 수정합니다.
    변경된 필드만 JSONB에 병합(merge)됩니다.
    """
    service = SettingsService()
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="변경할 설정이 없습니다")

    result = await service.update_settings(db, update_data)
    await db.commit()
    return GeneralSettingsResponse(**result)


@router.get(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="UI 사용자 환경설정 조회",
)
async def get_user_preferences(
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """
    사용자 UI 환경설정을 조회합니다.
    표시항목(컬럼 가시성) 등의 프론트엔드 설정을 반환합니다.
    """
    service = SettingsService()
    result = await service.get_preferences(db)
    return UserPreferencesResponse(column_preferences=result)


@router.put(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="UI 사용자 환경설정 저장",
)
async def update_user_preferences(
    body: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """
    사용자 UI 환경설정을 저장합니다.
    표시항목(컬럼 가시성) 등을 DB에 영구 저장합니다.
    기존 설정에 병합되므로 변경된 윈도우의 설정만 보내도 됩니다.
    """
    if not body.column_preferences:
        raise HTTPException(status_code=400, detail="변경할 설정이 없습니다")

    service = SettingsService()
    result = await service.update_preferences(db, body.column_preferences)
    await db.commit()
    return UserPreferencesResponse(column_preferences=result)


@router.get(
    "/periods",
    response_model=list[BusinessPeriodResponse],
    summary="사업장 마감현황 조회",
)
async def list_business_periods(
    year: int | None = Query(None, description="연도"),
    db: AsyncSession = Depends(get_db),
) -> list[BusinessPeriodResponse]:
    """
    사업장 월별 마감현황을 조회합니다.
    연도 파라미터로 필터링할 수 있습니다.
    """
    service = SettingsService()
    results = await service.list_periods(db, year)
    return [BusinessPeriodResponse(**r) for r in results]


@router.post(
    "/periods/{year}/{month}/close",
    response_model=BusinessPeriodResponse,
    summary="월 마감",
)
async def close_business_period(
    year: int,
    month: int,
    notes: str | None = Query(None, description="비고"),
    db: AsyncSession = Depends(get_db),
) -> BusinessPeriodResponse:
    """
    해당 월을 마감합니다.
    마감 후에는 해당 월의 전표를 수정/삭제할 수 없습니다.
    이미 마감된 월을 다시 마감하면 마감일시가 갱신됩니다.
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="월은 1~12 사이여야 합니다")

    service = SettingsService()
    result = await service.close_period(db, year, month, notes)
    await db.commit()
    return BusinessPeriodResponse(**result)


@router.post(
    "/periods/{year}/{month}/reopen",
    response_model=BusinessPeriodResponse,
    summary="월 마감해제",
)
async def reopen_business_period(
    year: int,
    month: int,
    reason: str = Query(..., description="마감해제 사유"),
    db: AsyncSession = Depends(get_db),
) -> BusinessPeriodResponse:
    """
    해당 월의 마감을 해제합니다.
    마감해제 사유는 필수입니다.
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="월은 1~12 사이여야 합니다")

    service = SettingsService()
    result = await service.reopen_period(db, year, month, reason)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"{year}년 {month}월 마감 기록을 찾을 수 없습니다",
        )

    await db.commit()
    return BusinessPeriodResponse(**result)
