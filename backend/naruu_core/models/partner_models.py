"""Partner (Clinic/Shop/Venue) Pydantic models"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ServiceItem(BaseModel):
    name_ja: str
    name_kr: Optional[str] = None
    price_krw: Optional[float] = None
    duration_min: Optional[int] = None


class PartnerCreate(BaseModel):
    name_kr: str = Field(..., min_length=1, max_length=100)
    name_ja: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    category: str = Field(..., pattern="^(medical|beauty|restaurant|shopping|experience|tourism)$")
    sub_category: Optional[str] = None
    business_number: Optional[str] = None
    ceo_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_kr: Optional[str] = None
    address_ja: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commission_rate: float = Field(default=20.0, ge=0, le=100)
    payment_terms: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    operating_hours: Optional[dict] = None
    services: list[ServiceItem] = []
    description_ja: Optional[str] = None
    description_kr: Optional[str] = None
    memo: Optional[str] = None


class PartnerUpdate(BaseModel):
    name_kr: Optional[str] = None
    name_ja: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_kr: Optional[str] = None
    address_ja: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commission_rate: Optional[float] = None
    operating_hours: Optional[dict] = None
    services: Optional[list[ServiceItem]] = None
    description_ja: Optional[str] = None
    description_kr: Optional[str] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class PartnerResponse(BaseModel):
    id: str
    code: Optional[str] = None
    name_kr: str
    name_ja: Optional[str] = None
    name_en: Optional[str] = None
    category: str
    sub_category: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_kr: Optional[str] = None
    address_ja: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commission_rate: float = 20.0
    services: list[dict] = []
    description_ja: Optional[str] = None
    rating: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class PartnerListResponse(BaseModel):
    items: list[PartnerResponse]
    total: int
    page: int
    page_size: int
