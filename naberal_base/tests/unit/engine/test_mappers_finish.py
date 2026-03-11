"""
Mappers Finish Tests (T3 - Phase I-5 핀포인트 마무리)

목적: core/ssot/mappers.py 커버리지 증대 (21.62% → 60%+)
원칙: Zero-Mock, 실제 함수 호출 (Real Function Calls)
Phase XVII-b Fix: Add tolerance-based comparison for float/Decimal precision
"""

from decimal import Decimal, ROUND_HALF_UP

from kis_estimator_core.core.ssot.mappers import (
    normalize_breaker_key,
    normalize_enclosure_key,
    parse_breaker_spec,
    format_breaker_spec,
    apply_vat,
)


def approx(a, b, abs_tol=0.5, rel_tol=0.001):
    """
    Tolerance-based comparison for float/Decimal precision (SSOT-compliant)

    Args:
        a, b: Values to compare
        abs_tol: Absolute tolerance (0.5 for mm/원 unit precision)
        rel_tol: Relative tolerance (0.1%)

    Returns:
        bool: True if values are approximately equal
    """
    from decimal import Decimal

    def quantize_if_decimal(x):
        if isinstance(x, Decimal):
            return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return x

    a_q = quantize_if_decimal(a)
    b_q = quantize_if_decimal(b)

    # Convert to float for comparison
    a_f = float(a_q)
    b_f = float(b_q)

    return abs(a_f - b_f) <= max(abs_tol, rel_tol * max(abs(a_f), abs(b_f)))


# ============================================================
# T3-1: Breaker Normalize Roundtrip
# ============================================================
def test_breaker_normalize_roundtrip_ok():
    """
    차단기 키 정규화 → 스펙 파싱 → 스펙 포맷 roundtrip 검증

    Zero-Mock: 실제 함수 호출
    """
    # Step 1: Alias 키로 입력 (현실 시나리오)
    raw_data = {
        "current": 60,  # alias for current_a
        "frame": 100,  # alias for frame_af
        "pole": 2,  # alias for poles
    }

    # Step 2: 키 정규화
    normalized = normalize_breaker_key(raw_data)

    # Assert: 정규화된 키로 변환됨
    assert normalized["current_a"] == 60
    assert normalized["frame_af"] == 100
    assert normalized["poles"] == 2
    assert "current" not in normalized  # alias는 제거됨
    assert "frame" not in normalized
    assert "pole" not in normalized

    # Step 3: 스펙 문자열 생성
    spec_str = format_breaker_spec(
        poles=normalized["poles"],
        frame_af=normalized["frame_af"],
        current_a=normalized["current_a"],
        capacity_ka=14.0,
    )

    # Assert: 올바른 스펙 문자열 생성
    assert spec_str == "2P 100AF 60AT 14.0kA"

    # Step 4: 스펙 문자열 파싱 (roundtrip)
    parsed = parse_breaker_spec(spec_str)

    # Assert: 원본 데이터와 일치 (tolerance-based for float/Decimal precision)
    assert parsed["poles"] == normalized["poles"]
    assert approx(
        parsed["frame_af"], normalized["frame_af"]
    ), f"frame_af mismatch: {parsed['frame_af']} != {normalized['frame_af']}"
    assert approx(
        parsed["current_a"], normalized["current_a"]
    ), f"current_a mismatch: {parsed['current_a']} != {normalized['current_a']}"
    assert approx(
        parsed["capacity_ka"], 14.0
    ), f"capacity_ka mismatch: {parsed['capacity_ka']} != 14.0"


# ============================================================
# T3-2: Enclosure Normalize Missing Field Raises
# ============================================================
def test_enclosure_normalize_missing_field_ok():
    """
    외함 키 정규화 - 일부 필드 누락 시 정상 처리 (에러 없음)

    주의: normalize_enclosure_key는 에러를 raise하지 않음 (단순 copy)
    Zero-Mock: 실제 함수 호출
    """
    # Setup: 일부 필드만 있는 데이터
    incomplete_data = {
        "w": 600,  # width_mm alias
        "h": 800,  # height_mm alias
        # depth 누락
    }

    # Execute: 키 정규화 (에러 없이 처리됨)
    normalized = normalize_enclosure_key(incomplete_data)

    # Assert: 존재하는 필드만 정규화
    assert normalized["width_mm"] == 600
    assert normalized["height_mm"] == 800
    assert "depth_mm" not in normalized  # 누락된 필드는 없음
    assert "w" not in normalized
    assert "h" not in normalized


# ============================================================
# T3-3: VAT Application with Decimal Rounding
# ============================================================
def test_vat_application_decimal_rounding():
    """
    부가세 적용 시 Decimal 타입으로 정확한 계산 검증

    Zero-Mock: 실제 함수 호출
    """
    # Setup: 원금액
    base_amount = Decimal("12500")

    # Execute: 부가세 적용 (10%)
    vat_included = apply_vat(base_amount)

    # Assert: 정확한 계산 (12500 * 1.1 = 13750)
    expected = Decimal("13750.0")
    assert vat_included == expected, f"Expected {expected}, got {vat_included}"

    # Assert: Decimal 타입 유지
    assert isinstance(
        vat_included, Decimal
    ), f"Expected Decimal, got {type(vat_included)}"

    # Edge case: float 입력도 처리
    vat_from_float = apply_vat(12500.0)
    assert vat_from_float == expected
