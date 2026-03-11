"""
KIS ERP - 급여 관리 API
급여대장 등록/조회/수정 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
import uuid

from api.db import get_db
from kis_erp_core.services.payroll_service import PayrollService

router = APIRouter(prefix="/payroll", tags=["ERP - 급여관리"])

_service = PayrollService()


# ==================== 급여 모델 ====================

class PayrollItem(BaseModel):
    """급여 항목"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str = Field(..., description="사원 ID")
    employee_name: str = Field(..., description="사원명")
    department: Optional[str] = Field(None, description="부서")
    position: Optional[str] = Field(None, description="직위")

    # 급여 항목
    base_salary: Decimal = Field(Decimal("0"), description="기본급")
    overtime_pay: Decimal = Field(Decimal("0"), description="연장수당")
    bonus: Decimal = Field(Decimal("0"), description="상여금")
    allowances: Decimal = Field(Decimal("0"), description="제수당")
    total_earnings: Decimal = Field(Decimal("0"), description="총 지급액")

    # 공제 항목
    income_tax: Decimal = Field(Decimal("0"), description="소득세")
    local_income_tax: Decimal = Field(Decimal("0"), description="지방소득세")
    national_pension: Decimal = Field(Decimal("0"), description="국민연금")
    health_insurance: Decimal = Field(Decimal("0"), description="건강보험")
    employment_insurance: Decimal = Field(Decimal("0"), description="고용보험")
    long_term_care: Decimal = Field(Decimal("0"), description="장기요양보험")
    other_deductions: Decimal = Field(Decimal("0"), description="기타공제")
    total_deductions: Decimal = Field(Decimal("0"), description="총 공제액")

    net_pay: Decimal = Field(Decimal("0"), description="실지급액")
    notes: Optional[str] = Field(None, description="비고")


class Payroll(BaseModel):
    """급여대장"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    year: int = Field(..., description="연도")
    month: int = Field(..., description="월")
    pay_date: date = Field(..., description="지급일")
    status: str = Field("draft", description="상태 (draft/confirmed/paid)")

    items: List[PayrollItem] = Field(default_factory=list, description="급여 항목")

    total_earnings: Decimal = Field(Decimal("0"), description="총 지급액 합계")
    total_deductions: Decimal = Field(Decimal("0"), description="총 공제액 합계")
    total_net_pay: Decimal = Field(Decimal("0"), description="실지급액 합계")

    insurance_rates: Optional[dict] = Field(None, description="4대보험율 설정")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def _payroll_to_model(data: dict) -> dict:
    """DB dict를 Payroll 응답 형식으로 변환"""
    items_raw = data.get("items", [])
    items = []
    for it in items_raw:
        items.append({
            "id": it.get("id", str(uuid.uuid4())),
            "employee_id": it.get("employee_id", ""),
            "employee_name": it.get("employee_name", ""),
            "department": it.get("department"),
            "position": it.get("position"),
            "base_salary": it.get("base_salary", 0),
            "overtime_pay": it.get("overtime_pay", 0),
            "bonus": it.get("bonus", 0),
            "allowances": it.get("allowances", 0),
            "total_earnings": it.get("total_earnings", 0),
            "income_tax": it.get("income_tax", 0),
            "local_income_tax": it.get("local_income_tax", 0),
            "national_pension": it.get("national_pension", 0),
            "health_insurance": it.get("health_insurance", 0),
            "employment_insurance": it.get("employment_insurance", 0),
            "long_term_care": it.get("long_term_care", 0),
            "other_deductions": it.get("other_deductions", 0),
            "total_deductions": it.get("total_deductions", 0),
            "net_pay": it.get("net_pay", 0),
            "notes": it.get("notes"),
        })

    return {
        "id": data.get("id", str(uuid.uuid4())),
        "year": data.get("year"),
        "month": data.get("month"),
        "pay_date": data.get("pay_date"),
        "status": data.get("status", "draft"),
        "items": items,
        "total_earnings": data.get("total_earnings", 0),
        "total_deductions": data.get("total_deductions", 0),
        "total_net_pay": data.get("total_net_pay", 0),
        "insurance_rates": data.get("insurance_rates"),
        "created_at": data.get("created_at", datetime.utcnow()),
        "updated_at": data.get("updated_at", datetime.utcnow()),
    }


def _model_to_db(payroll: Payroll) -> dict:
    """Payroll 모델을 DB 저장 형식으로 변환"""
    items = []
    for it in payroll.items:
        items.append({
            "employee_id": it.employee_id,
            "employee_name": it.employee_name,
            "department": it.department,
            "position": it.position,
            "base_salary": int(it.base_salary),
            "overtime_pay": int(it.overtime_pay),
            "bonus": int(it.bonus),
            "allowances": int(it.allowances),
            "total_earnings": int(it.total_earnings),
            "income_tax": int(it.income_tax),
            "local_income_tax": int(it.local_income_tax),
            "national_pension": int(it.national_pension),
            "health_insurance": int(it.health_insurance),
            "employment_insurance": int(it.employment_insurance),
            "long_term_care": int(it.long_term_care),
            "other_deductions": int(it.other_deductions),
            "total_deductions": int(it.total_deductions),
            "net_pay": int(it.net_pay),
            "notes": it.notes,
        })

    return {
        "year": payroll.year,
        "month": payroll.month,
        "pay_date": str(payroll.pay_date),
        "status": payroll.status,
        "items": items,
        "total_earnings": int(payroll.total_earnings),
        "total_deductions": int(payroll.total_deductions),
        "total_net_pay": int(payroll.total_net_pay),
        "insurance_rates": payroll.insurance_rates or {},
    }


# ==================== 급여대장 API ====================

@router.get("", response_model=List[Payroll], summary="급여대장 목록 조회")
async def list_payrolls(
    year: Optional[int] = Query(None, description="연도"),
    status: Optional[str] = Query(None, description="상태"),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
) -> List[Payroll]:
    """
    급여대장 목록을 조회합니다.
    """
    results = await _service.list_payrolls(db, year, status, skip, limit)
    return [Payroll(**_payroll_to_model(r)) for r in results]


@router.post("", response_model=Payroll, status_code=201, summary="급여대장 생성")
async def create_payroll(
    payroll: Payroll,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    새 급여대장을 생성합니다.
    """
    payroll = _calculate_payroll_totals(payroll)
    db_data = _model_to_db(payroll)
    result = await _service.create_payroll(db, db_data)
    return Payroll(**_payroll_to_model(result))


@router.get("/{payroll_id}", response_model=Payroll, summary="급여대장 상세 조회")
async def get_payroll(
    payroll_id: str,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    급여대장 상세 정보를 조회합니다.
    """
    result = await _service.get_payroll(db, payroll_id)
    if not result:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다")
    return Payroll(**_payroll_to_model(result))


@router.get("/period/{year}/{month}", response_model=Payroll, summary="월별 급여대장 조회")
async def get_payroll_by_period(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    특정 연월의 급여대장을 조회합니다.
    """
    result = await _service.get_payroll_by_period(db, year, month)
    if not result:
        raise HTTPException(status_code=404, detail="해당 월의 급여대장을 찾을 수 없습니다")
    return Payroll(**_payroll_to_model(result))


@router.put("/{payroll_id}", response_model=Payroll, summary="급여대장 수정")
async def update_payroll(
    payroll_id: str,
    payroll: Payroll,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    급여대장을 수정합니다. (확정 전만 가능)
    """
    payroll = _calculate_payroll_totals(payroll)
    db_data = _model_to_db(payroll)

    try:
        result = await _service.update_payroll(db, payroll_id, db_data)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다")
    return Payroll(**_payroll_to_model(result))


@router.post("/{payroll_id}/confirm", response_model=Payroll, summary="급여대장 확정")
async def confirm_payroll(
    payroll_id: str,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    급여대장을 확정합니다.
    확정 후에는 수정이 불가합니다.
    """
    result = await _service.confirm_payroll(db, payroll_id)
    if not result:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다 (이미 확정되었거나 존재하지 않음)")
    return Payroll(**_payroll_to_model(result))


@router.post("/{payroll_id}/pay", response_model=Payroll, summary="급여 지급 처리")
async def pay_payroll(
    payroll_id: str,
    db: AsyncSession = Depends(get_db),
) -> Payroll:
    """
    급여를 지급 처리합니다.
    """
    result = await _service.pay_payroll(db, payroll_id)
    if not result:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다 (확정 상태가 아니거나 존재하지 않음)")
    return Payroll(**_payroll_to_model(result))


@router.delete("/{payroll_id}", status_code=204, summary="급여대장 삭제")
async def delete_payroll(
    payroll_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    급여대장을 삭제합니다. (draft 상태만 가능)
    """
    try:
        deleted = await _service.delete_payroll(db, payroll_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다")


# ==================== 급여명세서 ====================

@router.get("/{payroll_id}/slip/{employee_id}", summary="급여명세서 조회")
async def get_pay_slip(
    payroll_id: str,
    employee_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    개인별 급여명세서를 조회합니다.
    """
    result = await _service.get_payroll(db, payroll_id)
    if not result:
        raise HTTPException(status_code=404, detail="급여대장을 찾을 수 없습니다")

    items = result.get("items", [])
    employee_item = None
    for it in items:
        if it.get("employee_id") == employee_id:
            employee_item = it
            break

    if not employee_item:
        raise HTTPException(status_code=404, detail="해당 사원의 급여 정보를 찾을 수 없습니다")

    return {
        "payroll_id": payroll_id,
        "employee_id": employee_id,
        "year": result.get("year"),
        "month": result.get("month"),
        "pay_date": str(result.get("pay_date")),
        "slip": employee_item,
    }


# ==================== 헬퍼 함수 ====================

def _calculate_payroll_totals(payroll: Payroll) -> Payroll:
    """급여대장 합계 계산"""
    total_earnings = Decimal("0")
    total_deductions = Decimal("0")
    total_net_pay = Decimal("0")

    for item in payroll.items:
        # 개인별 합계 계산
        item.total_earnings = (
            item.base_salary + item.overtime_pay +
            item.bonus + item.allowances
        )
        item.total_deductions = (
            item.income_tax + item.local_income_tax +
            item.national_pension + item.health_insurance +
            item.employment_insurance + item.long_term_care +
            item.other_deductions
        )
        item.net_pay = item.total_earnings - item.total_deductions

        # 전체 합계
        total_earnings += item.total_earnings
        total_deductions += item.total_deductions
        total_net_pay += item.net_pay

    payroll.total_earnings = total_earnings
    payroll.total_deductions = total_deductions
    payroll.total_net_pay = total_net_pay

    return payroll
