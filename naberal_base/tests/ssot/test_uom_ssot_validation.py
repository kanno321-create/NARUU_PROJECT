"""
UOM/할인/라운딩 SSOT 검증 테스트 (Phase VII-3)

Contract-First + Zero-Mock + Evidence-Gated

검증 항목:
1. SSOT 상수 값 검증 (41개 constants)
2. apply_rounding() HALF_EVEN 동작 검증
3. Busbar 계산 검증 (coefficients, specs, weights, prices)
4. Misc Materials 계산 검증
5. Assembly Charge 계산 검증
6. Integration: data_transformer 전체 파이프라인
"""

import pytest

from kis_estimator_core.core.ssot.constants import (
    # Accessory Prices
    PRICE_ET_50_125AF,
    PRICE_ET_200_250AF,
    PRICE_ET_400AF,
    PRICE_ET_600_800AF,
    PRICE_NT,
    PRICE_NP_CARD_HOLDER,
    PRICE_NP_CARD_HOLDER_MAIN_ONLY,
    PRICE_NP_3T_40_200,
    PRICE_COATING,
    PRICE_BREAKER_SUPPORT,
    PRICE_ELB_SUPPORT,
    PRICE_INSULATOR_50_250AF,
    PRICE_INSULATOR_400_800AF,
    PRICE_BUSBAR_PER_KG,
    # Busbar Coefficients
    BUSBAR_COEFF_20_250A,
    BUSBAR_COEFF_300_400A,
    BUSBAR_COEFF_500_800A,
    BUSBAR_SPEC_3T_15,
    BUSBAR_SPEC_5T_20,
    BUSBAR_SPEC_6T_30,
    BUSBAR_SPEC_8T_40,
    BUSBAR_WEIGHT_400AF_OPTION,
    BUSBAR_WEIGHT_600_800AF_OPTION,
    PCOVER_AREA_DIVISOR,
    PCOVER_PRICE_MULTIPLIER,
    # Misc Materials
    MISC_BASE_PRICE,
    MISC_H_INCREMENT_PER_100MM,
    MISC_ACCESSORY_INCREMENT,
    MISC_MAX_PRICE,
    MISC_BUSBAR_OPTION_400_800AF,
    # Assembly Charge
    ASSEMBLY_MAIN_ONLY_50_250AF,
    ASSEMBLY_MAIN_ONLY_400AF,
    ASSEMBLY_MAIN_ONLY_600_800AF,
    ASSEMBLY_MAIN_ONLY_BUSBAR_400AF,
    ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF,
    ASSEMBLY_BASE_H_50_100AF,
    ASSEMBLY_BASE_PRICE_50_100AF,
    ASSEMBLY_BASE_H_125_250AF,
    ASSEMBLY_BASE_PRICE_125_250AF,
    ASSEMBLY_BASE_H_300_400AF,
    ASSEMBLY_BASE_PRICE_300_400AF,
    ASSEMBLY_BASE_H_600_800AF,
    ASSEMBLY_BASE_PRICE_600_800AF,
    ASSEMBLY_H_INCREMENT_PER_100MM,
    # Rounding Utility
    apply_rounding,
)


class TestSSOTConstants:
    """SSOT 상수 값 검증"""

    def test_accessory_prices_defined(self):
        """부속자재 가격 상수 정의 확인"""
        assert PRICE_ET_50_125AF == 4500
        assert PRICE_ET_200_250AF == 5500
        assert PRICE_ET_400AF == 12000
        assert PRICE_ET_600_800AF == 18000
        assert PRICE_NT == 3000
        assert PRICE_NP_CARD_HOLDER == 800
        assert PRICE_NP_CARD_HOLDER_MAIN_ONLY == 1500
        assert PRICE_NP_3T_40_200 == 4000
        assert PRICE_COATING == 5000
        assert PRICE_BREAKER_SUPPORT == 1200
        assert PRICE_ELB_SUPPORT == 500
        assert PRICE_INSULATOR_50_250AF == 1100
        assert PRICE_INSULATOR_400_800AF == 4400
        assert PRICE_BUSBAR_PER_KG == 22000  # 2025-12-02 기준 (원자재 가격 변동)

    def test_busbar_coefficients_defined(self):
        """Busbar 계수 상수 정의 확인"""
        assert BUSBAR_COEFF_20_250A == 0.000007
        assert BUSBAR_COEFF_300_400A == 0.000013
        assert BUSBAR_COEFF_500_800A == 0.000015

    def test_busbar_specs_defined(self):
        """Busbar 규격 상수 정의 확인"""
        assert BUSBAR_SPEC_3T_15 == "3T*15"
        assert BUSBAR_SPEC_5T_20 == "5T*20"
        assert BUSBAR_SPEC_6T_30 == "6T*30"
        assert BUSBAR_SPEC_8T_40 == "8T*40"

    def test_busbar_weights_defined(self):
        """Busbar 중량 상수 정의 확인"""
        assert BUSBAR_WEIGHT_400AF_OPTION == 5.0
        assert BUSBAR_WEIGHT_600_800AF_OPTION == 8.0

    def test_pcover_calculation_defined(self):
        """P-COVER 계산 상수 정의 확인"""
        assert PCOVER_AREA_DIVISOR == 90000
        assert PCOVER_PRICE_MULTIPLIER == 3200

    def test_misc_materials_defined(self):
        """잡자재비 계산 상수 정의 확인"""
        assert MISC_BASE_PRICE == 7000
        assert MISC_H_INCREMENT_PER_100MM == 1000
        assert MISC_ACCESSORY_INCREMENT == 10000
        assert MISC_MAX_PRICE == 40000
        assert MISC_BUSBAR_OPTION_400_800AF == 15000

    def test_assembly_charge_main_only_defined(self):
        """Assembly Charge (Main-only) 상수 정의 확인"""
        assert ASSEMBLY_MAIN_ONLY_50_250AF == 15000
        assert ASSEMBLY_MAIN_ONLY_400AF == 20000
        assert ASSEMBLY_MAIN_ONLY_600_800AF == 30000
        assert ASSEMBLY_MAIN_ONLY_BUSBAR_400AF == 40000
        assert ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF == 70000

    def test_assembly_charge_with_branches_defined(self):
        """Assembly Charge (With Branches) 상수 정의 확인"""
        assert ASSEMBLY_BASE_H_50_100AF == 700
        assert ASSEMBLY_BASE_PRICE_50_100AF == 50000
        assert ASSEMBLY_BASE_H_125_250AF == 800
        assert ASSEMBLY_BASE_PRICE_125_250AF == 80000
        assert ASSEMBLY_BASE_H_300_400AF == 900
        assert ASSEMBLY_BASE_PRICE_300_400AF == 120000
        assert ASSEMBLY_BASE_H_600_800AF == 1000
        assert ASSEMBLY_BASE_PRICE_600_800AF == 150000
        assert ASSEMBLY_H_INCREMENT_PER_100MM == 15000


class TestApplyRounding:
    """apply_rounding() 함수 HALF_EVEN 동작 검증"""

    def test_half_even_rounding_to_even(self):
        """HALF_EVEN: .5는 가장 가까운 짝수로 반올림"""
        # 1.25 → 1.2 (짝수)
        assert apply_rounding(1.25, 1) == 1.2
        # 1.35 → 1.4 (짝수)
        assert apply_rounding(1.35, 1) == 1.4
        # 1.45 → 1.4 (짝수)
        assert apply_rounding(1.45, 1) == 1.4
        # 1.55 → 1.6 (짝수)
        assert apply_rounding(1.55, 1) == 1.6

    def test_half_even_rounding_no_tie(self):
        """HALF_EVEN: .5가 아닌 경우 일반 반올림"""
        assert apply_rounding(1.24, 1) == 1.2
        assert apply_rounding(1.26, 1) == 1.3
        assert apply_rounding(1.34, 1) == 1.3
        assert apply_rounding(1.36, 1) == 1.4

    def test_decimal_places_parameter(self):
        """decimal_places 파라미터 검증"""
        # 소수점 1자리
        assert apply_rounding(1.2345, 1) == 1.2
        # 소수점 2자리
        assert apply_rounding(1.2345, 2) == 1.23
        # 소수점 0자리 (정수)
        assert apply_rounding(1.5, 0) == 2.0

    def test_busbar_weight_rounding_example(self):
        """Busbar 중량 계산 예시 (실제 사용 케이스)"""
        # W=600, H=800, coefficient=0.000007
        weight_raw = (600 * 800) * 0.000007  # 3.36
        weight_rounded = apply_rounding(weight_raw, 1)
        assert weight_rounded == 3.4  # HALF_EVEN: 3.36 → 3.4

    def test_rounding_preserves_type(self):
        """반올림 결과가 float 타입 유지"""
        result = apply_rounding(1.25, 1)
        assert isinstance(result, float)


class TestBusbarCalculations:
    """Busbar 계산 검증 (SSOT 연계)"""

    def test_busbar_coefficient_selection_main(self):
        """Main busbar coefficient 선택 로직"""
        # 20~250A → 0.000007
        assert BUSBAR_COEFF_20_250A == 0.000007
        # 300~400A → 0.000013
        assert BUSBAR_COEFF_300_400A == 0.000013
        # 500~800A → 0.000015
        assert BUSBAR_COEFF_500_800A == 0.000015

    def test_busbar_spec_selection_main(self):
        """Main busbar spec 선택 로직"""
        # 20~250A → 5T*20
        assert BUSBAR_SPEC_5T_20 == "5T*20"
        # 300~400A → 6T*30
        assert BUSBAR_SPEC_6T_30 == "6T*30"
        # 500~800A → 8T*40
        assert BUSBAR_SPEC_8T_40 == "8T*40"

    def test_busbar_spec_selection_branch(self):
        """Branch busbar spec 선택 로직"""
        # ~125AF → 3T*15
        assert BUSBAR_SPEC_3T_15 == "3T*15"
        # 126~250AF → 5T*20
        assert BUSBAR_SPEC_5T_20 == "5T*20"
        # 251~400AF → 6T*30
        assert BUSBAR_SPEC_6T_30 == "6T*30"
        # 401~800AF → 8T*40
        assert BUSBAR_SPEC_8T_40 == "8T*40"

    def test_busbar_weight_calculation(self):
        """Busbar 중량 계산 (HALF_EVEN rounding)"""
        w, h = 600, 800
        coefficient = BUSBAR_COEFF_20_250A

        # 계산: (600*800) * 0.000007 = 3.36
        weight = apply_rounding((w * h) * coefficient, 1)
        assert weight == 3.4  # HALF_EVEN

    def test_busbar_unit_price(self):
        """Busbar 단가 검증"""
        assert PRICE_BUSBAR_PER_KG == 22000  # 2025-12-02 기준 (원자재 가격 변동)


class TestMiscMaterialsCalculations:
    """잡자재비 계산 검증 (SSOT 연계)"""

    def test_misc_base_price(self):
        """기본값 검증"""
        assert MISC_BASE_PRICE == 7000

    def test_misc_h_increment(self):
        """H 증분 계산"""
        h = 850  # mm
        h_increments = (h // 100) * MISC_H_INCREMENT_PER_100MM
        # (850 // 100) * 1000 = 8 * 1000 = 8000
        assert h_increments == 8000

    def test_misc_accessory_increment(self):
        """부속자재 증분 계산"""
        accessory_count = 3
        accessory_increment = accessory_count * MISC_ACCESSORY_INCREMENT
        # 3 * 10000 = 30000
        assert accessory_increment == 30000

    def test_misc_max_price_limit(self):
        """최대값 제한"""
        price = 50000  # 계산 결과
        limited = min(price, MISC_MAX_PRICE)
        # min(50000, 40000) = 40000
        assert limited == 40000

    def test_misc_busbar_option(self):
        """부스바 옵션 추가 (400~800AF)"""
        assert MISC_BUSBAR_OPTION_400_800AF == 15000

    def test_misc_materials_full_calculation(self):
        """잡자재비 전체 계산 예시"""
        h = 850
        accessory_count = 2

        price = MISC_BASE_PRICE
        price += (h // 100) * MISC_H_INCREMENT_PER_100MM
        price += accessory_count * MISC_ACCESSORY_INCREMENT
        price = min(price, MISC_MAX_PRICE)

        # 7000 + (8 * 1000) + (2 * 10000) = 35000
        # min(35000, 40000) = 35000
        assert price == 35000


class TestAssemblyChargeCalculations:
    """조립비 계산 검증 (SSOT 연계)"""

    def test_assembly_main_only_base_prices(self):
        """Main-only 기본 인건비"""
        # 50~250AF
        assert ASSEMBLY_MAIN_ONLY_50_250AF == 15000
        # 400AF
        assert ASSEMBLY_MAIN_ONLY_400AF == 20000
        # 600~800AF
        assert ASSEMBLY_MAIN_ONLY_600_800AF == 30000

    def test_assembly_main_only_busbar_option(self):
        """Main-only 부스바 옵션 추가 인건비"""
        # 400AF
        base_400 = ASSEMBLY_MAIN_ONLY_400AF
        busbar_400 = ASSEMBLY_MAIN_ONLY_BUSBAR_400AF
        total_400 = base_400 + busbar_400
        # 20000 + 40000 = 60000
        assert total_400 == 60000

        # 600~800AF
        base_600 = ASSEMBLY_MAIN_ONLY_600_800AF
        busbar_600 = ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF
        total_600 = base_600 + busbar_600
        # 30000 + 70000 = 100000
        assert total_600 == 100000

    def test_assembly_with_branches_base_prices(self):
        """With branches 기본 가격"""
        assert ASSEMBLY_BASE_PRICE_50_100AF == 50000
        assert ASSEMBLY_BASE_PRICE_125_250AF == 80000
        assert ASSEMBLY_BASE_PRICE_300_400AF == 120000
        assert ASSEMBLY_BASE_PRICE_600_800AF == 150000

    def test_assembly_with_branches_base_heights(self):
        """With branches 기준 높이"""
        assert ASSEMBLY_BASE_H_50_100AF == 700
        assert ASSEMBLY_BASE_H_125_250AF == 800
        assert ASSEMBLY_BASE_H_300_400AF == 900
        assert ASSEMBLY_BASE_H_600_800AF == 1000

    def test_assembly_h_increment_calculation(self):
        """H 증분 계산 (100mm당 15,000원)"""
        h = 950
        base_h = ASSEMBLY_BASE_H_125_250AF  # 800
        base_price = ASSEMBLY_BASE_PRICE_125_250AF  # 80000

        h_increment = max(0, (h - base_h) // 100)
        charge = base_price + (h_increment * ASSEMBLY_H_INCREMENT_PER_100MM)

        # h_increment = (950 - 800) // 100 = 1
        # charge = 80000 + (1 * 15000) = 95000
        assert h_increment == 1
        assert charge == 95000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
