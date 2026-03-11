"""
Catalog Router

카탈로그 조회 엔드포인트 (차단기/외함/부속자재)
Contract: spec_kit/api/openapi.yaml#/catalog

KIS-001: 가격 CSV 연동 완료 (2025-11-28)
- 3_accessories.json 가격 데이터 활용
- 모델/카테고리 기반 가격 lookup
"""

import logging
from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from kis_estimator_core.api.schemas.catalog import (
    BreakerCatalogItem,
    BreakerCatalogResponse,
    EnclosureCatalogResponse,
)
from kis_estimator_core.core.ssot.errors import ErrorCode, EstimatorError, raise_error
from kis_estimator_core.infra.knowledge_loader import get_knowledge_loader

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _build_accessory_price_map() -> dict[str, int]:
    """
    Build accessory price lookup map from 3_accessories.json (KIS-001)

    Returns:
        dict: {model_or_id: price} mapping
    """
    price_map: dict[str, int] = {}

    try:
        loader = get_knowledge_loader()
        accessories_data = loader.get_accessories()

        categories = accessories_data.get("categories", {})

        # Magnet contactors
        magnets = categories.get("magnet_contactors", {}).get("models", [])
        for item in magnets:
            model = item.get("model", "")
            price = item.get("price", 0)
            if model and price:
                price_map[model.upper()] = price
                # Also add with "MG_" prefix for matching
                price_map[f"MG_{model.upper()}"] = price

        # Timers
        timers = categories.get("timers", {}).get("models", [])
        for item in timers:
            model = item.get("model", "")
            price = item.get("price", 0)
            if model and price:
                price_map[model.upper()] = price
                price_map[f"TIMER_{model.upper()}"] = price

        # Timer mandatory bundles
        timer_bundles = categories.get("timers", {}).get("mandatory_bundles", {}).get("items", [])
        for item in timer_bundles:
            item_id = item.get("item_id", "")
            price = item.get("price", 0)
            if item_id and price:
                price_map[item_id.upper()] = price

        # Meters V/A
        va_meter = categories.get("meters", {}).get("v_a_meter", {})
        for comp in va_meter.get("components", []):
            item_id = comp.get("item_id", "")
            price = comp.get("price", 0)
            if item_id and price:
                price_map[item_id.upper()] = price

        # CT meters
        ct_meter = categories.get("meters", {}).get("ct_meter", {})
        for comp in ct_meter.get("components", []):
            item_id = comp.get("item_id", "")
            price = comp.get("price", 0)
            if item_id and price:
                price_map[item_id.upper()] = price

        # SPD
        spd = categories.get("spd", {})
        for comp in spd.get("components", []):
            item_id = comp.get("item_id", "")
            price = comp.get("price", 0)
            if item_id and price:
                price_map[item_id.upper()] = price

        # Standard accessories (bundle items)
        std_acc = categories.get("standard_accessories", {}).get("items", [])
        for item in std_acc:
            item_id = item.get("item_id", "")
            price = item.get("price", 0)
            if item_id and price:
                price_map[item_id.upper()] = price

        logger.info(f"Built accessory price map with {len(price_map)} entries")

    except Exception as e:
        logger.warning(f"Failed to build accessory price map: {e}")

    return price_map


def _lookup_accessory_price(raw_item: dict[str, Any]) -> int:
    """
    Lookup accessory price from 3_accessories.json (KIS-001)

    Args:
        raw_item: Raw accessory item from ai_estimation_core.json

    Returns:
        int: Price (0 if not found)
    """
    # First, try to get price from raw_item itself
    existing_price = raw_item.get("price", 0)
    if existing_price and existing_price > 0:
        return existing_price

    # Lookup from 3_accessories.json
    price_map = _build_accessory_price_map()

    # Try various keys
    lookup_keys = [
        raw_item.get("id", "").upper(),
        raw_item.get("model_range", "").upper() if raw_item.get("model_range") else "",
        raw_item.get("category", "").upper(),
    ]

    for key in lookup_keys:
        if key and key in price_map:
            return price_map[key]

    return 0

router = APIRouter()


@router.get(
    "/breakers",
    summary="차단기 카탈로그 조회",
    description="차단기 카탈로그를 조회합니다 (Phase 0 지식 파일 기반)",
    operation_id="getBreakerCatalog"
)
async def get_breaker_catalog(
    category: Literal["MCCB", "ELB"] | None = Query(None, description="차단기 종류 필터"),
    brand: str | None = Query(None, description="브랜드 필터 (SANGDO, LS, 상도)"),
    series: Literal["경제형", "표준형", "소형"] | None = Query(None, description="시리즈 필터"),
    poles: int | None = Query(None, ge=2, le=4, description="극수 필터 (2, 3, 4)"),
    frame_AF: int | None = Query(None, description="프레임 AF 필터")
) -> JSONResponse:
    """
    차단기 카탈로그 조회

    실제 ai_estimation_core.json 데이터 기반
    필터링: category, brand, series, poles, frame_AF (AND 조건)
    """
    try:
        loader = get_knowledge_loader()
        ai_core = loader.get_ai_core()

        # Extract breaker catalog data
        breakers_raw = ai_core.get("catalog", {}).get("breakers", {}).get("items", [])

        # Brand normalization mapping
        brand_map = {
            "Sangdo": "SANGDO",
            "상도": "SANGDO",
            "LS": "LS"
        }

        # Series/Type mapping
        series_map = {
            "Standard": "표준형",
            "Economy": "경제형",
            "소형": "소형"
        }

        # Filter and transform breakers
        filtered_items = []
        for raw_item in breakers_raw:
            # Normalize brand
            raw_brand = raw_item.get("brand", "")
            normalized_brand = brand_map.get(raw_brand, raw_brand)

            # Map series from type (handle "Standard/Economy" format)
            raw_type = raw_item.get("type", "")
            # Split "Standard/Economy" and take first part
            if "/" in raw_type:
                raw_type = raw_type.split("/")[0]
            mapped_series = series_map.get(raw_type, raw_type)

            # Normalize data types
            # Price: list → first value, int → as is
            price = raw_item.get("price", 0)
            if isinstance(price, list):
                price = price[0] if price else 0

            # Capacity: list → first value, float → as is
            capacity_kA = raw_item.get("capacity_kA", 0.0)
            if isinstance(capacity_kA, list):
                capacity_kA = capacity_kA[0] if capacity_kA else 0.0

            # Ampere: int → [int], list → as is
            ampere = raw_item.get("ampere", [])
            if isinstance(ampere, (int, float)):
                ampere = [int(ampere)]

            # Size: None → skip
            size_mm = raw_item.get("size_mm")
            if not size_mm or not isinstance(size_mm, list) or len(size_mm) < 3:
                logger.debug(f"Skipped breaker {raw_item.get('model', 'UNKNOWN')}: invalid size_mm")
                continue

            # Apply filters (AND condition)
            if category is not None and raw_item.get("category") != category:
                continue
            if brand is not None and normalized_brand != brand:
                continue
            if series is not None and mapped_series != series:
                continue
            if poles is not None and raw_item.get("poles") != poles:
                continue
            if frame_AF is not None and raw_item.get("frame_AF") != frame_AF:
                continue

            # Create BreakerCatalogItem
            try:
                item = BreakerCatalogItem(
                    model=raw_item["model"],
                    brand=normalized_brand,
                    category=raw_item["category"],
                    series=mapped_series,
                    poles=raw_item["poles"],
                    frame_AF=raw_item["frame_AF"],
                    ampere=ampere,
                    capacity_kA=capacity_kA,
                    price=price,
                    size_mm=size_mm
                )
                filtered_items.append(item)
            except Exception as item_error:
                logger.warning(f"Skipped invalid breaker item {raw_item.get('model', 'UNKNOWN')}: {item_error}")
                continue

        # Build response
        response = BreakerCatalogResponse(
            total_count=len(filtered_items),
            filters_applied={
                "category": category,
                "brand": brand,
                "series": series,
                "poles": poles,
                "frame_AF": frame_AF
            },
            items=filtered_items
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Breaker catalog error: {e}")
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to load breaker catalog",
            hint="Check knowledge files",
            meta={"error": str(e)}
        )


@router.get(
    "/enclosures",
    summary="외함 카탈로그 조회",
    description="외함 카탈로그를 조회합니다 (Phase 0 지식 파일 기반)",
    operation_id="getEnclosureCatalog"
)
async def get_enclosure_catalog(
    installation_type: str | None = Query(None, description="설치 유형 필터"),
    material: str | None = Query(None, description="재질 필터"),
    min_width: int | None = Query(None, ge=400, description="최소 폭 (mm)"),
    max_width: int | None = Query(None, le=1200, description="최대 폭 (mm)")
) -> JSONResponse:
    """
    외함 카탈로그 조회

    실제 ai_estimation_core.json 데이터 기반
    필터링: installation_type, material, min_width, max_width (AND 조건)
    """
    try:
        loader = get_knowledge_loader()
        ai_core = loader.get_ai_core()

        # Extract enclosure catalog data
        enclosures_raw = ai_core.get("catalog", {}).get("enclosures", {}).get("standard", {}).get("items", [])

        # Filter and transform enclosures
        filtered_items = []
        for raw_item in enclosures_raw:
            # Get width from size_mm (W, H, D)
            size_mm = raw_item.get("size_mm")
            if not size_mm or not isinstance(size_mm, list) or len(size_mm) < 3:
                logger.debug(f"Skipped enclosure {raw_item.get('model', 'UNKNOWN')}: invalid size_mm")
                continue
            width = size_mm[0]

            # Apply filters (AND condition)
            if installation_type is not None and raw_item.get("install_location") != installation_type:
                continue
            if material is not None and raw_item.get("material") != material:
                continue
            if min_width is not None and width < min_width:
                continue
            if max_width is not None and width > max_width:
                continue

            # Create EnclosureCatalogItem
            try:
                from kis_estimator_core.api.schemas.catalog import EnclosureCatalogItem
                item = EnclosureCatalogItem(
                    model=raw_item["model"],
                    category=raw_item["category"],
                    material=raw_item["material"],
                    thickness_mm=raw_item["thickness_mm"],
                    install_location=raw_item["install_location"],
                    size_mm=raw_item["size_mm"],
                    price=raw_item["price"],
                    custom_required=raw_item.get("custom_required", False)
                )
                filtered_items.append(item)
            except Exception as item_error:
                logger.warning(f"Skipped invalid enclosure item {raw_item.get('model', 'UNKNOWN')}: {item_error}")
                continue

        # Build response
        response = EnclosureCatalogResponse(
            total_count=len(filtered_items),
            filters_applied={
                "installation_type": installation_type,
                "material": material,
                "min_width": min_width,
                "max_width": max_width
            },
            items=filtered_items
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Enclosure catalog error: {e}")
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to load enclosure catalog",
            hint="Check knowledge files",
            meta={"error": str(e)}
        )


@router.get(
    "/accessories",
    summary="부속자재 카탈로그 조회",
    description="부속자재 카탈로그를 조회합니다 (Phase 0 지식 파일 기반)",
    operation_id="getAccessoryCatalog"
)
async def get_accessory_catalog(
    accessory_type: str | None = Query(None, description="부속자재 종류 필터")
) -> JSONResponse:
    """
    부속자재 카탈로그 조회

    실제 ai_estimation_core.json 데이터 기반
    필터링: accessory_type (category 매칭)
    """
    try:
        loader = get_knowledge_loader()
        ai_core = loader.get_ai_core()

        # Extract accessories catalog data
        accessories_raw = ai_core.get("catalog", {}).get("accessories", {}).get("items", [])

        # Filter and transform accessories
        filtered_items = []
        for raw_item in accessories_raw:
            # Apply filter
            if accessory_type is not None and raw_item.get("category") != accessory_type:
                continue

            # Transform size format: {W_mm, H_mm} -> [W, H, D]
            size_dict = raw_item.get("size", {})
            size_mm = None
            if size_dict:
                w = size_dict.get("W_mm", 0)
                h = size_dict.get("H_mm", 0)
                d = size_dict.get("D_mm", 0)  # D might not exist
                size_mm = [w, h, d]

            # Create AccessoryCatalogItem
            try:
                from kis_estimator_core.api.schemas.catalog import AccessoryCatalogItem
                item = AccessoryCatalogItem(
                    id=raw_item["id"],
                    category=raw_item["category"],
                    model=raw_item.get("model_range"),  # model_range -> model
                    spec=raw_item.get("spec"),  # might not exist
                    unit=raw_item["unit"],
                    price=_lookup_accessory_price(raw_item),  # KIS-001 완료: 3_accessories.json 가격 연동
                    size_mm=size_mm
                )
                filtered_items.append(item)
            except Exception as item_error:
                logger.warning(f"Skipped invalid accessory item {raw_item.get('id', 'UNKNOWN')}: {item_error}")
                continue

        # Build response
        from kis_estimator_core.api.schemas.catalog import AccessoryCatalogResponse
        response = AccessoryCatalogResponse(
            total_count=len(filtered_items),
            filters_applied={
                "accessory_type": accessory_type
            },
            items=filtered_items
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )

    except EstimatorError:
        raise
    except Exception as e:
        logger.error(f"Accessory catalog error: {e}")
        raise_error(
            ErrorCode.E_INTERNAL,
            "Failed to load accessory catalog",
            hint="Check knowledge files",
            meta={"error": str(e)}
        )
