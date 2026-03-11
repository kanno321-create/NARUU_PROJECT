"""
Unit tests for models/catalog.py - AI-optimized catalog models

Target: 85% coverage for catalog.py (101 lines)
Principles:
- Zero-Mock: Real Pydantic models only
- Comprehensive validation testing
- All auto-generation logic verified

Test Count: 15 tests
"""

import pytest
from pydantic import ValidationError

from kis_estimator_core.models.catalog import (
    BreakerCategory,
    BreakerSeries,
    Brand,
    EnclosureType,
    EnclosureMaterial,
    BreakerDimensions,
    CatalogBreakerItem,
    CatalogEnclosureItem,
    AICatalog,
)


# ============================================================================
# Test 1-3: Enum Instantiation
# ============================================================================


@pytest.mark.unit
def test_breaker_category_enum():
    """Test 1: BreakerCategory enum values"""
    assert BreakerCategory.MCCB.value == "MCCB"
    assert BreakerCategory.ELB.value == "ELB"

    # Enum from string
    cat = BreakerCategory("MCCB")
    assert cat == BreakerCategory.MCCB


@pytest.mark.unit
def test_brand_enum():
    """Test 2: Brand enum values"""
    assert Brand.SADOELE.value == "상도차단기"
    assert Brand.LSIS.value == "LS산전"
    assert Brand.HDELECTRIC.value == "현대일렉트릭"
    assert Brand.KISCO.value == "한국산업"

    # All brands instantiable
    for brand in Brand:
        assert isinstance(brand.value, str)


@pytest.mark.unit
def test_enclosure_type_enum():
    """Test 3: EnclosureType enum values"""
    assert EnclosureType.INDOOR_EXPOSED.value == "옥내노출"
    assert EnclosureType.OUTDOOR_EXPOSED.value == "옥외노출"
    assert EnclosureType.INDOOR_STANDALONE.value == "옥내자립"
    assert EnclosureType.OUTDOOR_STANDALONE.value == "옥외자립"
    assert EnclosureType.EMBEDDED.value == "매입함"


# ============================================================================
# Test 4-5: BreakerDimensions Validation
# ============================================================================


@pytest.mark.unit
def test_breaker_dimensions_valid():
    """Test 4: BreakerDimensions with valid values"""
    dims = BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60)

    assert dims.width_mm == 50
    assert dims.height_mm == 130
    assert dims.depth_mm == 60


@pytest.mark.unit
def test_breaker_dimensions_required_fields():
    """Test 5: BreakerDimensions requires all fields"""
    with pytest.raises(ValidationError) as exc_info:
        BreakerDimensions(width_mm=50, height_mm=130)  # Missing depth_mm

    assert "depth_mm" in str(exc_info.value)


# ============================================================================
# Test 6-9: CatalogBreakerItem Creation & Validation
# ============================================================================


@pytest.mark.unit
def test_catalog_breaker_item_creation():
    """Test 6: CatalogBreakerItem creation with all required fields"""
    item = CatalogBreakerItem(
        category=BreakerCategory.MCCB,
        brand=Brand.SADOELE,
        series=BreakerSeries.ECONOMY,
        model="SBE-102",
        poles=2,
        current_a=60,
        frame_af=100,
        breaking_capacity_ka=14.0,
        price=12500,
        dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
    )

    assert item.model == "SBE-102"
    assert item.poles == 2
    assert item.current_a == 60
    assert item.frame_af == 100
    assert item.price == 12500


@pytest.mark.unit
def test_catalog_breaker_item_poles_validation():
    """Test 7: CatalogBreakerItem validates poles (2, 3, 4 only)"""
    # Valid poles
    for poles in [2, 3, 4]:
        item = CatalogBreakerItem(
            category=BreakerCategory.MCCB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model=f"SBE-{poles}02",
            poles=poles,
            current_a=60,
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=12500,
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        )
        assert item.poles == poles

    # Invalid poles
    with pytest.raises(ValidationError) as exc_info:
        CatalogBreakerItem(
            category=BreakerCategory.MCCB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model="SBE-102",
            poles=5,  # Invalid
            current_a=60,
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=12500,
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        )

    assert "poles" in str(exc_info.value)


@pytest.mark.unit
def test_catalog_breaker_item_current_validation():
    """Test 8: CatalogBreakerItem validates current_a > 0"""
    with pytest.raises(ValidationError) as exc_info:
        CatalogBreakerItem(
            category=BreakerCategory.MCCB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model="SBE-102",
            poles=2,
            current_a=0,  # Invalid: must be > 0
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=12500,
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        )

    # Error should mention current_a validation
    assert "current_a" in str(exc_info.value) or "양수" in str(exc_info.value)


@pytest.mark.unit
def test_catalog_breaker_item_price_validation():
    """Test 9: CatalogBreakerItem validates price >= 0"""
    # Valid price (0 or positive)
    item_free = CatalogBreakerItem(
        category=BreakerCategory.MCCB,
        brand=Brand.SADOELE,
        series=BreakerSeries.ECONOMY,
        model="SBE-102",
        poles=2,
        current_a=60,
        frame_af=100,
        breaking_capacity_ka=14.0,
        price=0,  # Valid: free item
        dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
    )
    assert item_free.price == 0

    # Invalid price (negative)
    with pytest.raises(ValidationError) as exc_info:
        CatalogBreakerItem(
            category=BreakerCategory.MCCB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model="SBE-102",
            poles=2,
            current_a=60,
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=-1000,  # Invalid
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        )

    assert "price" in str(exc_info.value)


# ============================================================================
# Test 10-11: CatalogBreakerItem Search Keywords Auto-Generation
# ============================================================================


@pytest.mark.unit
def test_catalog_breaker_item_search_keywords_auto_generation():
    """Test 10: Search keywords are auto-generated in __init__"""
    item = CatalogBreakerItem(
        category=BreakerCategory.MCCB,
        brand=Brand.SADOELE,
        series=BreakerSeries.ECONOMY,
        model="SBE-102",
        poles=2,
        current_a=60,
        frame_af=100,
        breaking_capacity_ka=14.0,
        price=12500,
        dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
    )

    # Verify keywords generated
    assert len(item.search_keywords) > 0
    assert "SBE-102" in item.search_keywords
    assert "2P" in item.search_keywords
    assert "60A" in item.search_keywords
    assert "100AF" in item.search_keywords
    assert "MCCB" in item.search_keywords
    assert "경제형" in item.search_keywords
    assert "상도차단기" in item.search_keywords


@pytest.mark.unit
def test_catalog_breaker_item_search_keywords_explicit():
    """Test 11: Explicit search keywords override auto-generation"""
    custom_keywords = ["CUSTOM1", "CUSTOM2"]
    item = CatalogBreakerItem(
        category=BreakerCategory.MCCB,
        brand=Brand.SADOELE,
        series=BreakerSeries.ECONOMY,
        model="SBE-102",
        poles=2,
        current_a=60,
        frame_af=100,
        breaking_capacity_ka=14.0,
        price=12500,
        dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        search_keywords=custom_keywords,
    )

    # Explicit keywords should be preserved (not auto-generated)
    assert item.search_keywords == custom_keywords


# ============================================================================
# Test 12-13: CatalogEnclosureItem Creation & Validation
# ============================================================================


@pytest.mark.unit
def test_catalog_enclosure_item_creation():
    """Test 12: CatalogEnclosureItem creation with all required fields"""
    item = CatalogEnclosureItem(
        type=EnclosureType.INDOOR_EXPOSED,
        material=EnclosureMaterial.STEEL_16T,
        brand=Brand.SADOELE,
        model="HB304015",
        width_mm=300,
        height_mm=400,
        depth_mm=150,
        price=250000,
    )

    assert item.model == "HB304015"
    assert item.width_mm == 300
    assert item.height_mm == 400
    assert item.depth_mm == 150
    assert item.price == 250000


@pytest.mark.unit
def test_catalog_enclosure_item_search_keywords_auto_generation():
    """Test 13: Enclosure search keywords auto-generated"""
    item = CatalogEnclosureItem(
        type=EnclosureType.INDOOR_EXPOSED,
        material=EnclosureMaterial.STEEL_16T,
        brand=Brand.SADOELE,
        model="HB304015",
        width_mm=300,
        height_mm=400,
        depth_mm=150,
        price=250000,
    )

    # Verify keywords generated
    assert len(item.search_keywords) > 0
    assert "HB304015" in item.search_keywords
    assert "300x400x150" in item.search_keywords
    assert "옥내노출" in item.search_keywords
    assert "STEEL 1.6T" in item.search_keywords
    assert "상도차단기" in item.search_keywords


# ============================================================================
# Test 14-15: AICatalog Statistics Auto-Calculation
# ============================================================================


@pytest.mark.unit
def test_ai_catalog_statistics_auto_calculation():
    """Test 14: AICatalog auto-calculates statistics"""
    breakers = [
        CatalogBreakerItem(
            category=BreakerCategory.MCCB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model="SBE-102",
            poles=2,
            current_a=60,
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=12500,
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        ),
        CatalogBreakerItem(
            category=BreakerCategory.ELB,
            brand=Brand.SADOELE,
            series=BreakerSeries.ECONOMY,
            model="SEE-102",
            poles=2,
            current_a=60,
            frame_af=100,
            breaking_capacity_ka=14.0,
            price=18500,
            dimensions=BreakerDimensions(width_mm=50, height_mm=130, depth_mm=60),
        ),
    ]

    enclosures = [
        CatalogEnclosureItem(
            type=EnclosureType.INDOOR_EXPOSED,
            material=EnclosureMaterial.STEEL_16T,
            brand=Brand.SADOELE,
            model="HB304015",
            width_mm=300,
            height_mm=400,
            depth_mm=150,
            price=250000,
        ),
    ]

    catalog = AICatalog(
        version="1.0.0",
        created_at="2025-10-16T10:00:00Z",
        source_file="test.csv",
        breakers=breakers,
        enclosures=enclosures,
    )

    # Statistics auto-calculated
    assert catalog.breaker_count == 2
    assert catalog.enclosure_count == 1
    assert catalog.total_items == 3


@pytest.mark.unit
def test_ai_catalog_empty():
    """Test 15: AICatalog with no items"""
    catalog = AICatalog(
        version="1.0.0",
        created_at="2025-10-16T10:00:00Z",
        source_file="empty.csv",
    )

    # Default empty lists
    assert catalog.breaker_count == 0
    assert catalog.enclosure_count == 0
    assert catalog.total_items == 0
    assert len(catalog.breakers) == 0
    assert len(catalog.enclosures) == 0
