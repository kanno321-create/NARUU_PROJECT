"""
KIS ERP - 사원 관리 API
사원 등록/조회/수정/삭제 엔드포인트
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.erp import Employee

# Import Service (kis_erp_core now in src/)
from kis_erp_core.services.employee_service import EmployeeService
from kis_erp_core.models.product_employee_models import EmployeeCreate, EmployeeUpdate, EmployeeFilter

router = APIRouter(prefix="/employees", tags=["ERP - 사원관리"])


@router.get("", response_model=List[Employee], summary="사원 목록 조회")
async def list_employees(
    department: Optional[str] = Query(None, description="부서"),
    status: Optional[str] = Query(None, description="재직 상태 (active/resigned)"),
    search: Optional[str] = Query(None, description="사원명/사번 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Employee]:
    """
    사원 목록을 조회합니다.
    """
    service = EmployeeService()
    filters = EmployeeFilter(department=department, status=status, search=search)
    results = await service.list_employees(db, filters, skip, limit)
    return [Employee(**r) for r in results]


@router.post("", response_model=Employee, status_code=201, summary="사원 등록")
async def create_employee(
    employee: Employee,
    db: AsyncSession = Depends(get_db),
) -> Employee:
    """
    신규 사원을 등록합니다.
    """
    service = EmployeeService()
    data = EmployeeCreate(
        name=employee.name,
        department=employee.department,
        position=employee.position,
        tel=employee.tel,
        email=employee.email,
    )
    result = await service.create_employee(db, data)
    await db.commit()
    return Employee(**result)


@router.get("/{employee_id}", response_model=Employee, summary="사원 상세 조회")
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
) -> Employee:
    """
    사원 상세 정보를 조회합니다.
    """
    service = EmployeeService()
    result = await service.get_employee(db, UUID(employee_id))
    if not result:
        raise HTTPException(status_code=404, detail="사원을 찾을 수 없습니다")
    return Employee(**result)


@router.put("/{employee_id}", response_model=Employee, summary="사원 정보 수정")
async def update_employee(
    employee_id: str,
    employee: Employee,
    db: AsyncSession = Depends(get_db),
) -> Employee:
    """
    사원 정보를 수정합니다.
    """
    service = EmployeeService()
    data = EmployeeUpdate(
        name=employee.name,
        department=employee.department,
        position=employee.position,
        tel=employee.tel,
        email=employee.email,
        status=employee.status,
    )
    result = await service.update_employee(db, UUID(employee_id), data)
    if not result:
        raise HTTPException(status_code=404, detail="사원을 찾을 수 없습니다")
    await db.commit()
    return Employee(**result)


@router.delete("/{employee_id}", status_code=204, summary="사원 삭제")
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    사원을 삭제합니다. (실제로는 status='resigned' 처리)
    """
    service = EmployeeService()
    success = await service.delete_employee(db, UUID(employee_id))
    if not success:
        raise HTTPException(status_code=404, detail="사원을 찾을 수 없습니다")
    await db.commit()
