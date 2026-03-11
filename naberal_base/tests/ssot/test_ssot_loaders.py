"""
SSOT Loader Tests - Phase VII Task 3

UOM, Discount, Rounding SSOT 로더 검증
"""

import math
from kis_estimator_core.core.ssot.ssot_loader import (
    load_uom,
    load_discounts,
    load_rounding,
)


class TestUOMLoader:
    """UOM (Unit of Measure) 로더 테스트"""

    def test_uom_authorized_list(self):
        """UOM 리스트가 올바르게 로드되는지 확인"""
        uom = load_uom()
        assert isinstance(uom, list)
        assert len(uom) > 0
        assert "EA" in uom
        assert "KG" in uom
        assert "M" in uom

    def test_uom_no_duplicates(self):
        """UOM 리스트에 중복이 없는지 확인"""
        uom = load_uom()
        assert len(uom) == len(set(uom))


class TestDiscountLoader:
    """Discount Rules 로더 테스트"""

    def test_discount_tiers_loaded(self):
        """할인 티어가 올바르게 로드되는지 확인"""
        discounts = load_discounts()
        assert isinstance(discounts, list)
        assert len(discounts) > 0

    def test_discount_tiers_sorted_by_rate(self):
        """할인 티어가 rate 순으로 정렬 가능한지 확인"""
        discounts = load_discounts()
        sorted_discounts = sorted(discounts, key=lambda x: x["rate"])

        # VIP가 가장 높은 할인율
        assert sorted_discounts[-1]["tier"] == "VIP"
        assert sorted_discounts[-1]["rate"] == 0.12

    def test_discount_rate_range(self):
        """할인율이 0~1 범위 내인지 확인"""
        discounts = load_discounts()
        for discount in discounts:
            assert 0 <= discount["rate"] <= 1

    def test_discount_tiers_unique(self):
        """티어 이름이 중복되지 않는지 확인"""
        discounts = load_discounts()
        tiers = [d["tier"] for d in discounts]
        assert len(tiers) == len(set(tiers))


class TestRoundingLoader:
    """Rounding Rules 로더 테스트"""

    def test_rounding_config_loaded(self):
        """라운딩 설정이 올바르게 로드되는지 확인"""
        rounding = load_rounding()
        assert isinstance(rounding, dict)

        # 필수 키 확인
        assert "currency" in rounding
        assert "precision" in rounding
        assert "mode" in rounding
        assert "vat_pct" in rounding

    def test_rounding_krw_config(self):
        """KRW 라운딩 설정이 올바른지 확인"""
        rounding = load_rounding()

        assert rounding["currency"] == "KRW"
        assert rounding["precision"] == 0  # 소수점 0자리
        assert rounding["mode"] == "HALF_UP"

    def test_rounding_vat_total_calculation(self):
        """부가세 포함 총액 계산 검증"""
        rounding = load_rounding()
        vat = rounding["vat_pct"]

        # 예시: 123456원 + 10% VAT
        subtotal = 123456.7
        total = math.floor(subtotal * (1 + vat) + 0.5)  # HALF_UP for KRW(0)

        assert total >= subtotal
        assert total == 135802  # 123456.7 * 1.1 = 135802.37 → 135802

    def test_vat_pct_range(self):
        """VAT 비율이 유효한 범위인지 확인"""
        rounding = load_rounding()
        assert 0 <= rounding["vat_pct"] <= 1
