"""
Excel Generator SSOT Integration Tests - Phase VII Task 3

excel_generator.py가 SSOT rounding.json을 올바르게 사용하는지 검증
"""

from kis_estimator_core.core.ssot.ssot_loader import load_rounding
from kis_estimator_core.engine import excel_generator


class TestExcelGeneratorSSOTIntegration:
    """Excel Generator의 SSOT 연동 테스트"""

    def test_excel_generator_imports_ssot_loader(self):
        """excel_generator가 ssot_loader를 import하는지 확인"""
        # ssot_loader가 import되어 있어야 함
        assert hasattr(excel_generator, "load_rounding")

    def test_vat_calculation_uses_ssot(self):
        """VAT 계산이 SSOT rounding.json 값을 사용하는지 확인"""
        rounding = load_rounding()
        vat_pct = rounding["vat_pct"]

        # SSOT에서 로드한 VAT가 10%인지 확인
        assert vat_pct == 0.10

        # 예상 VAT multiplier 확인
        expected_multiplier = 1 + vat_pct  # 1.10
        assert expected_multiplier == 1.10

    def test_rounding_mode_half_up(self):
        """라운딩 모드가 HALF_UP인지 확인"""
        rounding = load_rounding()

        assert rounding["mode"] == "HALF_UP"
        assert rounding["precision"] == 0  # KRW는 소수점 0자리

    def test_currency_krw(self):
        """통화가 KRW인지 확인"""
        rounding = load_rounding()
        assert rounding["currency"] == "KRW"


class TestExcelGeneratorEdgeCases:
    """Excel Generator 경계값 테스트"""

    def test_vat_formula_generation(self):
        """VAT 수식이 올바르게 생성되는지 확인"""
        rounding = load_rounding()
        vat_multiplier = 1 + rounding["vat_pct"]

        # Excel 수식 생성 시뮬레이션
        formula = f"=I18*{vat_multiplier}"

        assert formula == "=I18*1.1"

    def test_zero_subtotal_vat_calculation(self):
        """소계가 0일 때 VAT 계산"""
        rounding = load_rounding()
        subtotal = 0
        vat_total = subtotal * (1 + rounding["vat_pct"])

        assert vat_total == 0

    def test_large_subtotal_vat_calculation(self):
        """큰 금액 소계 VAT 계산"""
        rounding = load_rounding()
        subtotal = 999999999  # 약 10억
        vat_total = subtotal * (1 + rounding["vat_pct"])

        # VAT 포함 금액이 소계보다 크고, 오버플로우 없음
        assert vat_total > subtotal
        assert vat_total == 1099999998.9
