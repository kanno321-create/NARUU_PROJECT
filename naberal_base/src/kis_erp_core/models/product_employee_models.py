"""
Product/Employee 추가 모델 정의
"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal


# ========== Product Models ==========

class ProductBase(BaseModel):
    """Product 기본 모델"""
    name: str
    category: Optional[str] = None
    unit: str = "EA"
    unit_cost: Optional[float] = 0.0
    sale_price: Optional[float] = 0.0
    spec: Optional[str] = None
    manufacturer: Optional[str] = None


class ProductCreate(ProductBase):
    """Product 생성 요청"""
    pass


class ProductUpdate(BaseModel):
    """Product 수정 요청"""
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    sale_price: Optional[float] = None
    spec: Optional[str] = None
    manufacturer: Optional[str] = None
    is_active: Optional[bool] = None


class Product(ProductBase):
    """Product 응답 모델"""
    id: UUID
    code: str
    stock_qty: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    """Product 필터"""
    category: Optional[str] = None
    is_active: Optional[bool] = True
    search: Optional[str] = None


# ========== Employee Models ==========

class EmployeeBase(BaseModel):
    """Employee 기본 모델"""
    name: str
    department: Optional[str] = None
    position: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Employee 생성 요청"""
    pass


class EmployeeUpdate(BaseModel):
    """Employee 수정 요청"""
    name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    tel: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None


class Employee(EmployeeBase):
    """Employee 응답 모델"""
    id: UUID
    emp_no: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeFilter(BaseModel):
    """Employee 필터"""
    department: Optional[str] = None
    status: Optional[str] = "active"
    search: Optional[str] = None
