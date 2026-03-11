"""
Company 모델 (자사정보)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """Company 기본 모델"""
    business_number: str = Field(..., description="사업자등록번호")
    name: str = Field(..., description="상호명")
    ceo: str = Field(..., description="대표자명")
    address: Optional[str] = Field(None, description="주소")
    tel: Optional[str] = Field(None, description="전화번호")
    fax: Optional[str] = Field(None, description="팩스번호")
    email: Optional[str] = Field(None, description="이메일")
    bank_info: Optional[dict] = Field(None, description="은행 정보")
    business_type: Optional[str] = Field(None, description="업태")
    business_item: Optional[str] = Field(None, description="종목")
    logo_path: Optional[str] = Field(None, description="로고 이미지 경로")
    stamp_path: Optional[str] = Field(None, description="직인 이미지 경로")


class CompanyCreate(CompanyBase):
    """Company 생성 요청"""
    pass


class CompanyUpdate(BaseModel):
    """Company 수정 요청"""
    name: Optional[str] = None
    ceo: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    bank_info: Optional[dict] = None
    business_type: Optional[str] = None
    business_item: Optional[str] = None
    logo_path: Optional[str] = None
    stamp_path: Optional[str] = None


class Company(CompanyBase):
    """Company 응답 모델"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Customer(BaseModel):
    """Customer 응답 모델"""
    id: UUID
    code: str
    name: str
    type: str
    business_number: Optional[str] = None
    ceo: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    balance: float
    credit_limit: Optional[float] = None
    payment_terms: Optional[str] = None
    bank_info: Optional[dict] = None
    memo: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    """Customer 생성 요청"""
    name: str
    type: str  # 매출/매입/겸용
    business_number: Optional[str] = None
    ceo: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms: Optional[str] = None
    bank_info: Optional[dict] = None
    memo: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Customer 수정 요청"""
    name: Optional[str] = None
    type: Optional[str] = None
    business_number: Optional[str] = None
    ceo: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms: Optional[str] = None
    bank_info: Optional[str] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerFilter(BaseModel):
    """Customer 필터"""
    type: Optional[str] = None
    is_active: Optional[bool] = True
    search: Optional[str] = None  # 이름/코드 검색
