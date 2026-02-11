"""거래처 관리 라우터 — CRUD REST API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_api.deps import get_db_session
from naruu_core.auth.middleware import get_current_user
from naruu_core.plugins.partner.schemas import (
    PartnerCreate,
    PartnerResponse,
    PartnerUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from naruu_core.plugins.partner.service import PartnerCRUD

router = APIRouter(prefix="/partners", tags=["partners"])


def _partner_to_response(partner: object) -> PartnerResponse:
    """Partner ORM → PartnerResponse."""
    services = [
        ServiceResponse(
            id=s.id,
            partner_id=s.partner_id,
            name_ja=s.name_ja,
            name_ko=s.name_ko,
            price_krw=s.price_krw,
            duration_minutes=s.duration_minutes,
            description=s.description,
            is_active=s.is_active,
        )
        for s in getattr(partner, "services", [])
    ]
    return PartnerResponse(
        id=partner.id,  # type: ignore[attr-defined]
        name_ja=partner.name_ja,  # type: ignore[attr-defined]
        name_ko=partner.name_ko,  # type: ignore[attr-defined]
        category=partner.category,  # type: ignore[attr-defined]
        address=partner.address,  # type: ignore[attr-defined]
        phone=partner.phone,  # type: ignore[attr-defined]
        commission_rate=partner.commission_rate,  # type: ignore[attr-defined]
        is_active=partner.is_active,  # type: ignore[attr-defined]
        notes=partner.notes,  # type: ignore[attr-defined]
        services=services,
    )


# -- Partner CRUD --


@router.post("", response_model=PartnerResponse, status_code=201)
async def create_partner(
    req: PartnerCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PartnerResponse:
    """거래처 등록."""
    crud = PartnerCRUD(session)
    partner = await crud.create_partner(req)
    return _partner_to_response(partner)


@router.get("", response_model=list[PartnerResponse])
async def list_partners(
    category: str | None = None,
    active_only: bool = True,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[PartnerResponse]:
    """거래처 목록 조회."""
    crud = PartnerCRUD(session)
    partners = await crud.list_partners(category=category, active_only=active_only)
    return [_partner_to_response(p) for p in partners]


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PartnerResponse:
    """거래처 상세 조회."""
    crud = PartnerCRUD(session)
    partner = await crud.get_partner(partner_id)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="거래처를 찾을 수 없습니다."
        )
    return _partner_to_response(partner)


@router.patch("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: str,
    req: PartnerUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PartnerResponse:
    """거래처 수정."""
    crud = PartnerCRUD(session)
    partner = await crud.update_partner(partner_id, req)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="거래처를 찾을 수 없습니다."
        )
    return _partner_to_response(partner)


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """거래처 삭제."""
    crud = PartnerCRUD(session)
    deleted = await crud.delete_partner(partner_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="거래처를 찾을 수 없습니다."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Service CRUD --


@router.post("/{partner_id}/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    partner_id: str,
    req: ServiceCreate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ServiceResponse:
    """서비스 등록."""
    crud = PartnerCRUD(session)
    service = await crud.create_service(partner_id, req)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="거래처를 찾을 수 없습니다."
        )
    return ServiceResponse(
        id=service.id,
        partner_id=service.partner_id,
        name_ja=service.name_ja,
        name_ko=service.name_ko,
        price_krw=service.price_krw,
        duration_minutes=service.duration_minutes,
        description=service.description,
        is_active=service.is_active,
    )


@router.get("/{partner_id}/services", response_model=list[ServiceResponse])
async def list_services(
    partner_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ServiceResponse]:
    """서비스 목록 조회."""
    crud = PartnerCRUD(session)
    services = await crud.list_services(partner_id)
    return [
        ServiceResponse(
            id=s.id,
            partner_id=s.partner_id,
            name_ja=s.name_ja,
            name_ko=s.name_ko,
            price_krw=s.price_krw,
            duration_minutes=s.duration_minutes,
            description=s.description,
            is_active=s.is_active,
        )
        for s in services
    ]


@router.patch("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    req: ServiceUpdate,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ServiceResponse:
    """서비스 수정."""
    crud = PartnerCRUD(session)
    service = await crud.update_service(service_id, req)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="서비스를 찾을 수 없습니다."
        )
    return ServiceResponse(
        id=service.id,
        partner_id=service.partner_id,
        name_ja=service.name_ja,
        name_ko=service.name_ko,
        price_krw=service.price_krw,
        duration_minutes=service.duration_minutes,
        description=service.description,
        is_active=service.is_active,
    )


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: str,
    _user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """서비스 삭제."""
    crud = PartnerCRUD(session)
    deleted = await crud.delete_service(service_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="서비스를 찾을 수 없습니다."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
