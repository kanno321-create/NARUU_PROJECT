"""
SSOT Validation Tests - Phase VII Task 3

UOM/할인/라운딩 SSOT 검증 테스트
- UOM 허용 단위 검증
- 할인 규칙 정확성 검증
- 라운딩 규칙 검증 (HALF_UP, VAT 10%)
- 경계값 테스트

Contract-First, Zero-Mock, Evidence-Gated 원칙 준수
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP

from kis_estimator_core.core.ssot.ssot_loader import (
    load_uom,
    load_discounts,
    load_approval_threshold,
    load_rounding,
)


class TestUOMValidation:
    """UOM (Unit of Measure) 검증 테스트"""

    def test_load_uom_returns_list(self):
        """UOM 로더가 리스트를 반환하는지 확인"""
        uom_list = load_uom()
        assert isinstance(uom_list, list)
        assert len(uom_list) > 0

    def test_uom_contains_authorized_units(self):
        """허용된 7가지 단위 포함 확인"""
        uom_list = load_uom()
        authorized = ["EA", "SET", "M", "KG", "PCS", "BOX", "ROLL"]

        for unit in authorized:
            assert unit in uom_list, f"필수 단위 누락: {unit}"

    def test_uom_exactly_seven_units(self):
        """정확히 7가지 단위만 허용"""
        uom_list = load_uom()
        assert len(uom_list) == 7, f"UOM 개수 불일치: {len(uom_list)} != 7"

    @pytest.mark.parametrize("valid_uom", ["EA", "SET", "M", "KG", "PCS", "BOX", "ROLL"])
    def test_valid_uom_accepted(self, valid_uom: str):
        """유효한 UOM 허용 확인"""
        uom_list = load_uom()
        assert valid_uom in uom_list

    @pytest.mark.parametrize("invalid_uom", ["", "INVALID", "ea", "개", "UNIT", "PC", None])
    def test_invalid_uom_rejected(self, invalid_uom):
        """비허용 UOM 거부 확인"""
        uom_list = load_uom()
        assert invalid_uom not in uom_list


class TestDiscountRulesValidation:
    """할인 규칙 검증 테스트"""

    def test_load_discounts_returns_list(self):
        """할인 규칙 로더가 리스트를 반환"""
        discounts = load_discounts()
        assert isinstance(discounts, list)

    def test_discounts_has_five_tiers(self):
        """정확히 5단계 할인율 존재"""
        discounts = load_discounts()
        assert len(discounts) == 5, f"할인 단계 불일치: {len(discounts)} != 5"

    def test_discount_tier_structure(self):
        """각 할인 단계 구조 검증 (tier, rate)"""
        discounts = load_discounts()
        for tier in discounts:
            assert "tier" in tier, f"tier 키 누락: {tier}"
            assert "rate" in tier, f"rate 키 누락: {tier}"
            assert isinstance(tier["tier"], str)
            assert isinstance(tier["rate"], (int, float))

    @pytest.mark.parametrize(
        "tier_name,expected_rate",
        [
            ("A", 0.05),
            ("B", 0.08),
            ("VIP", 0.12),
            ("VOLUME", 0.03),
            ("SEASONAL", 0.02),
        ],
    )
    def test_discount_rate_accuracy(self, tier_name: str, expected_rate: float):
        """각 단계별 할인율 정확성 검증"""
        discounts = load_discounts()
        tier_dict = {t["tier"]: t["rate"] for t in discounts}

        assert tier_name in tier_dict, f"할인 단계 누락: {tier_name}"
        assert tier_dict[tier_name] == expected_rate, \
            f"할인율 불일치: {tier_name} = {tier_dict[tier_name]} (expected {expected_rate})"

    def test_discount_rates_valid_range(self):
        """할인율이 0~1 범위 내인지 검증"""
        discounts = load_discounts()
        for tier in discounts:
            rate = tier["rate"]
            assert 0 <= rate <= 1, f"할인율 범위 초과: {tier['tier']} = {rate}"


class TestApprovalThresholdValidation:
    """승인 임계값 검증 테스트"""

    def test_load_approval_threshold_returns_dict(self):
        """승인 임계값 로더가 딕셔너리 반환"""
        threshold = load_approval_threshold()
        assert isinstance(threshold, dict)

    def test_approval_threshold_currency(self):
        """통화가 KRW인지 확인"""
        threshold = load_approval_threshold()
        assert threshold.get("currency") == "KRW"

    def test_approval_threshold_amount(self):
        """승인 임계값이 5천만원(50,000,000)인지 확인"""
        threshold = load_approval_threshold()
        assert threshold.get("amount") == 50_000_000

    def test_approval_threshold_boundary_below(self):
        """임계값 미만 견적 - 승인 불필요"""
        threshold = load_approval_threshold()
        test_amount = 49_999_999
        requires_approval = test_amount >= threshold["amount"]
        assert not requires_approval

    def test_approval_threshold_boundary_exact(self):
        """임계값 정확히 일치 - 승인 필요"""
        threshold = load_approval_threshold()
        test_amount = 50_000_000
        requires_approval = test_amount >= threshold["amount"]
        assert requires_approval

    def test_approval_threshold_boundary_above(self):
        """임계값 초과 - 승인 필요"""
        threshold = load_approval_threshold()
        test_amount = 50_000_001
        requires_approval = test_amount >= threshold["amount"]
        assert requires_approval


class TestRoundingValidation:
    """라운딩 규칙 검증 테스트"""

    def test_load_rounding_returns_dict(self):
        """라운딩 규칙 로더가 딕셔너리 반환"""
        rounding = load_rounding()
        assert isinstance(rounding, dict)

    def test_rounding_currency(self):
        """통화가 KRW인지 확인"""
        rounding = load_rounding()
        assert rounding.get("currency") == "KRW"

    def test_rounding_precision(self):
        """정밀도가 0 (정수)인지 확인"""
        rounding = load_rounding()
        assert rounding.get("precision") == 0

    def test_rounding_mode(self):
        """반올림 모드가 HALF_UP인지 확인"""
        rounding = load_rounding()
        assert rounding.get("mode") == "HALF_UP"

    def test_vat_percentage(self):
        """VAT가 10%인지 확인"""
        rounding = load_rounding()
        assert rounding.get("vat_pct") == 0.10

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            (Decimal("100.4"), Decimal("100")),
            (Decimal("100.5"), Decimal("101")),  # HALF_UP: 0.5에서 올림
            (Decimal("100.6"), Decimal("101")),
            (Decimal("1234.567"), Decimal("1235")),
            (Decimal("999.999"), Decimal("1000")),
        ],
    )
    def test_half_up_rounding(self, input_value: Decimal, expected: Decimal):
        """HALF_UP 반올림 정확성 검증"""
        rounding = load_rounding()
        precision = rounding["precision"]

        # Python Decimal HALF_UP 적용
        rounded = input_value.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)
        assert rounded == expected, f"반올림 불일치: {input_value} -> {rounded} (expected {expected})"

    @pytest.mark.parametrize(
        "subtotal,expected_vat,expected_total",
        [
            (Decimal("100000"), Decimal("10000"), Decimal("110000")),
            (Decimal("50000000"), Decimal("5000000"), Decimal("55000000")),
            (Decimal("123456"), Decimal("12346"), Decimal("135802")),  # 12345.6 -> 12346
        ],
    )
    def test_vat_calculation(self, subtotal: Decimal, expected_vat: Decimal, expected_total: Decimal):
        """VAT 10% 계산 정확성 검증"""
        rounding = load_rounding()
        vat_rate = Decimal(str(rounding["vat_pct"]))
        precision = rounding["precision"]

        vat = (subtotal * vat_rate).quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)
        total = subtotal + vat

        assert vat == expected_vat, f"VAT 불일치: {vat} (expected {expected_vat})"
        assert total == expected_total, f"총액 불일치: {total} (expected {expected_total})"


class TestSSOTIntegration:
    """SSOT 통합 테스트"""

    def test_all_ssot_files_loadable(self):
        """모든 SSOT 파일 로드 가능 확인"""
        # 로드 시 예외 없이 통과해야 함
        uom = load_uom()
        discounts = load_discounts()
        threshold = load_approval_threshold()
        rounding = load_rounding()

        # 기본 검증
        assert uom is not None
        assert discounts is not None
        assert threshold is not None
        assert rounding is not None

    def test_ssot_consistency(self):
        """SSOT 데이터 간 일관성 검증"""
        threshold = load_approval_threshold()
        rounding = load_rounding()

        # 통화 일관성
        assert threshold["currency"] == rounding["currency"], \
            "승인 임계값과 라운딩 규칙의 통화가 일치해야 함"
