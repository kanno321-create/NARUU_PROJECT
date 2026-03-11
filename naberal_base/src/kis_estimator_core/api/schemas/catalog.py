"""
Catalog Response Schemas

OpenAPI 3.1 스키마 기반 Pydantic 모델 (카탈로그 조회)
Contract: spec_kit/api/openapi.yaml#BreakerCatalogResponse, EnclosureCatalogResponse, AccessoryCatalogResponse
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================
# Breaker Catalog Schemas
# ============================================================

class BreakerCatalogItem(BaseModel):
    """
    차단기 카탈로그 아이템

    Contract: spec_kit/api/openapi.yaml#BreakerCatalogItem
    """

    model: str = Field(
        ...,
        description="모델명",
        examples=["SBE-104", "ABN-54"]
    )

    brand: Literal["SANGDO", "LS"] = Field(
        ...,
        description="브랜드"
    )

    category: Literal["MCCB", "ELB"] = Field(
        ...,
        description="차단기 종류"
    )

    series: Literal["경제형", "표준형", "소형"] = Field(
        ...,
        description="시리즈"
    )

    poles: Literal[2, 3, 4] = Field(
        ...,
        description="극수"
    )

    frame_AF: int = Field(
        ...,
        description="프레임 (AF)",
        ge=30,
        le=800
    )

    ampere: list[int] = Field(
        ...,
        description="지원 암페어 목록",
        min_items=1
    )

    capacity_kA: float = Field(
        ...,
        description="차단용량 (kA)",
        gt=0
    )

    price: int = Field(
        ...,
        description="견적가 (원)",
        ge=0
    )

    size_mm: list[int] = Field(
        ...,
        description="크기 [W, H, D] (mm)",
        min_items=3,
        max_items=3
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "SBE-104",
                "brand": "SANGDO",
                "category": "MCCB",
                "series": "경제형",
                "poles": 4,
                "frame_AF": 100,
                "ampere": [20, 30, 40, 50, 60, 75],
                "capacity_kA": 14.0,
                "price": 12500,
                "size_mm": [100, 130, 60]
            }
        }


class BreakerCatalogResponse(BaseModel):
    """
    차단기 카탈로그 조회 응답

    Contract: spec_kit/api/openapi.yaml#BreakerCatalogResponse
    """

    total_count: int = Field(
        ...,
        description="총 항목 수",
        ge=0
    )

    filters_applied: dict[str, Any] | None = Field(
        None,
        description="적용된 필터"
    )

    items: list[BreakerCatalogItem] = Field(
        ...,
        description="차단기 카탈로그 항목 리스트"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 2,
                "filters_applied": {
                    "category": "MCCB",
                    "brand": "SANGDO",
                    "poles": 4
                },
                "items": [
                    {
                        "model": "SBE-104",
                        "brand": "SANGDO",
                        "category": "MCCB",
                        "series": "경제형",
                        "poles": 4,
                        "frame_AF": 100,
                        "ampere": [20, 30, 40, 50, 60, 75],
                        "capacity_kA": 14.0,
                        "price": 12500,
                        "size_mm": [100, 130, 60]
                    }
                ]
            }
        }


# ============================================================
# Enclosure Catalog Schemas
# ============================================================

class EnclosureCatalogItem(BaseModel):
    """
    외함 카탈로그 아이템

    Contract: spec_kit/api/openapi.yaml#EnclosureCatalogItem
    """

    model: str = Field(
        ...,
        description="모델명",
        examples=["HDS-600*400*200"]
    )

    category: str = Field(
        ...,
        description="외함 종류"
    )

    material: Literal["steel", "sus201", "sus304"] = Field(
        ...,
        description="재질"
    )

    thickness_mm: float = Field(
        ...,
        description="두께 (mm)",
        gt=0
    )

    install_location: Literal["indoor", "outdoor"] = Field(
        ...,
        description="설치 장소"
    )

    size_mm: list[int] = Field(
        ...,
        description="크기 [W, H, D] (mm)",
        min_items=3,
        max_items=3
    )

    price: int = Field(
        ...,
        description="견적가 (원)",
        ge=0
    )

    custom_required: bool = Field(
        False,
        description="주문제작 필요 여부"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "HDS-600*400*200",
                "category": "옥내노출",
                "material": "steel",
                "thickness_mm": 1.6,
                "install_location": "indoor",
                "size_mm": [600, 400, 200],
                "price": 85000,
                "custom_required": False
            }
        }


class EnclosureCatalogResponse(BaseModel):
    """
    외함 카탈로그 조회 응답

    Contract: spec_kit/api/openapi.yaml#EnclosureCatalogResponse
    """

    total_count: int = Field(
        ...,
        description="총 항목 수",
        ge=0
    )

    filters_applied: dict[str, Any] | None = Field(
        None,
        description="적용된 필터"
    )

    items: list[EnclosureCatalogItem] = Field(
        ...,
        description="외함 카탈로그 항목 리스트"
    )


# ============================================================
# Accessory Catalog Schemas
# ============================================================

class AccessoryCatalogItem(BaseModel):
    """
    부속자재 카탈로그 아이템

    Contract: spec_kit/api/openapi.yaml#AccessoryCatalogItem
    """

    id: str = Field(
        ...,
        description="자재 ID"
    )

    category: str = Field(
        ...,
        description="자재 종류"
    )

    model: str | None = Field(
        None,
        description="모델명"
    )

    spec: str | None = Field(
        None,
        description="규격"
    )

    unit: str = Field(
        ...,
        description="단위",
        examples=["EA", "M", "KG"]
    )

    price: int = Field(
        ...,
        description="견적가 (원)",
        ge=0
    )

    size_mm: list[int] | None = Field(
        None,
        description="크기 [W, H, D] (mm)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "MAG_MC_9_22",
                "category": "magnet_contactor",
                "model": "MC-22",
                "spec": "22A",
                "unit": "EA",
                "price": 12000,
                "size_mm": [45, 75, 85]
            }
        }


class AccessoryCatalogResponse(BaseModel):
    """
    부속자재 카탈로그 조회 응답

    Contract: spec_kit/api/openapi.yaml#AccessoryCatalogResponse
    """

    total_count: int = Field(
        ...,
        description="총 항목 수",
        ge=0
    )

    filters_applied: dict[str, Any] | None = Field(
        None,
        description="적용된 필터"
    )

    items: list[AccessoryCatalogItem] = Field(
        ...,
        description="부속자재 카탈로그 항목 리스트"
    )
