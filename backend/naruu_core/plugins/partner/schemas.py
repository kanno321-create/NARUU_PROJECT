"""거래처 Pydantic 스키마."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

# -- Partner --


class PartnerCreate(BaseModel):
    """거래처 생성 요청."""

    name_ja: str = Field(min_length=1, max_length=200)
    name_ko: str = ""
    category: str = Field(pattern=r"^(medical|beauty|tourism)$")
    address: str = ""
    phone: str = ""
    commission_rate: Decimal = Decimal("20.00")
    notes: str = ""


class PartnerUpdate(BaseModel):
    """거래처 수정 요청 (부분 업데이트)."""

    name_ja: str | None = None
    name_ko: str | None = None
    category: str | None = Field(default=None, pattern=r"^(medical|beauty|tourism)$")
    address: str | None = None
    phone: str | None = None
    commission_rate: Decimal | None = None
    is_active: bool | None = None
    notes: str | None = None


class PartnerResponse(BaseModel):
    """거래처 응답."""

    id: str
    name_ja: str
    name_ko: str
    category: str
    address: str
    phone: str
    commission_rate: Decimal
    is_active: bool
    notes: str
    services: list[ServiceResponse] = []


# -- Service --


class ServiceCreate(BaseModel):
    """서비스 생성 요청."""

    name_ja: str = Field(min_length=1, max_length=200)
    name_ko: str = ""
    price_krw: int = Field(ge=0)
    duration_minutes: int = Field(gt=0, le=1440)
    description: str = ""


class ServiceUpdate(BaseModel):
    """서비스 수정 요청."""

    name_ja: str | None = None
    name_ko: str | None = None
    price_krw: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    description: str | None = None
    is_active: bool | None = None


class ServiceResponse(BaseModel):
    """서비스 응답."""

    id: str
    partner_id: str
    name_ja: str
    name_ko: str
    price_krw: int
    duration_minutes: int
    description: str
    is_active: bool


# Forward ref 해결
PartnerResponse.model_rebuild()
