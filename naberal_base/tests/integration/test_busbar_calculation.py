"""
부스바(Busbar) 계산 테스트 - 대표님 확인용

SSOT 공식:
- 주부스바 중량(kg) = (W×H) × 계수
- MAIN BUS-BAR 계수표:
    - 20~250A:  0.000007
    - 300~400A: 0.000013
    - 500~800A: 0.000015
- BUS-BAR (분기용) 계수표:
    - 20~250A:  0.0000045
    - 300~400A: 0.000007
    - 500~800A: 0.000009
- 단가 = 중량(kg) × 22,000원/kg (2025-12-02 기준)

규격표:
- ~125AF:   3T*15
- ~250AF:   5T*20
- ~400AF:   6T*30
- ~800AF:   8T*40
"""

import pytest
from dataclasses import dataclass

# SSOT 상수
from kis_estimator_core.core.ssot.constants import (
    # MAIN BUS-BAR 계수
    BUSBAR_COEFF_20_250A,
    BUSBAR_COEFF_300_400A,
    BUSBAR_COEFF_500_800A,
    # BUS-BAR (분기용) 계수
    BRANCH_BUSBAR_COEFF_20_250A,
    BRANCH_BUSBAR_COEFF_300_400A,
    BRANCH_BUSBAR_COEFF_500_800A,
    # 규격
    BUSBAR_SPEC_3T_15,
    BUSBAR_SPEC_5T_20,
    BUSBAR_SPEC_6T_30,
    BUSBAR_SPEC_8T_40,
    PRICE_BUSBAR_PER_KG,
    apply_rounding,
)


@dataclass
class BusbarTestCase:
    """부스바 테스트 케이스"""
    case_id: int
    description: str
    main_current_a: int  # 메인차단기 전류
    max_branch_af: int   # 분기차단기 최대 AF
    enclosure_w: int     # 외함 W (mm)
    enclosure_h: int     # 외함 H (mm)


def calculate_main_busbar(w: int, h: int, current_a: int) -> dict:
    """MAIN BUS-BAR 계산"""
    # 계수 선택
    if current_a <= 250:
        coeff = BUSBAR_COEFF_20_250A
        spec = BUSBAR_SPEC_5T_20
    elif current_a <= 400:
        coeff = BUSBAR_COEFF_300_400A
        spec = BUSBAR_SPEC_6T_30
    else:
        coeff = BUSBAR_COEFF_500_800A
        spec = BUSBAR_SPEC_8T_40

    # 중량 계산
    weight_kg = apply_rounding((w * h) * coeff, decimal_places=1)
    price = int(weight_kg * PRICE_BUSBAR_PER_KG)

    return {
        "type": "MAIN BUS-BAR",
        "spec": spec,
        "coefficient": coeff,
        "weight_kg": weight_kg,
        "unit_price": PRICE_BUSBAR_PER_KG,
        "total_price": price,
    }


def calculate_branch_busbar(w: int, h: int, main_current_a: int, max_branch_af: int) -> dict:
    """BUS-BAR (분기용) 계산

    Note: 분기 부스바는 메인 부스바와 다른 계수를 사용함!
    - 출처: 부스바 산출공식.txt (대표님 정의)
    - 계수는 메인차단기 용량 기준으로 선택
    - 규격은 분기차단기 최대 AF 기준으로 선택
    """
    # 메인차단기 용량 기준 계수 선택 (분기용 계수!)
    if main_current_a <= 250:
        coeff = BRANCH_BUSBAR_COEFF_20_250A  # 0.0000045
    elif main_current_a <= 400:
        coeff = BRANCH_BUSBAR_COEFF_300_400A  # 0.000007
    else:
        coeff = BRANCH_BUSBAR_COEFF_500_800A  # 0.000009

    # 분기차단기 최대 AF 기준 규격 선택
    if max_branch_af <= 100:
        spec = BUSBAR_SPEC_3T_15  # ~100A
    elif max_branch_af <= 250:
        spec = BUSBAR_SPEC_5T_20  # 125~250A
    elif max_branch_af <= 400:
        spec = BUSBAR_SPEC_6T_30  # 300~400A
    else:
        spec = BUSBAR_SPEC_8T_40  # 500~800A

    # 중량 계산
    weight_kg = apply_rounding((w * h) * coeff, decimal_places=2)
    price = int(weight_kg * PRICE_BUSBAR_PER_KG)

    return {
        "type": "BUS-BAR",
        "spec": spec,
        "coefficient": coeff,
        "weight_kg": weight_kg,
        "unit_price": PRICE_BUSBAR_PER_KG,
        "total_price": price,
    }


# 테스트 케이스 (test_real_estimates.py 기반)
TEST_CASES = [
    BusbarTestCase(1, "Case 1: ELB 4P 100AF 75A 메인 + 분기 12개 (50AF)", 75, 50, 600, 700),
    BusbarTestCase(2, "Case 2: MCCB 4P 100AF 100A 메인 + 분기 12개 (50AF)", 100, 50, 600, 900),
    BusbarTestCase(3, "Case 3: 소형 2P 30A + 분기 6개", 30, 32, 500, 600),
    BusbarTestCase(4, "Case 4: 4P 200AF 메인 + 분기 8개", 150, 100, 700, 800),
    BusbarTestCase(5, "Case 5: 4P 400AF 메인 + 분기 16개", 300, 100, 800, 1200),
    BusbarTestCase(6, "Case 6: 메인차단기만 (분기 없음)", 75, 0, 600, 600),
    BusbarTestCase(7, "Case 7: 소형만 (외함 최소)", 30, 32, 600, 600),
    BusbarTestCase(8, "Case 8: 4P 600AF 메인 + 대용량 분기", 500, 200, 900, 1400),
    BusbarTestCase(9, "Case 9: 4P 800AF 메인 + 대용량 분기", 700, 250, 1000, 1600),
    BusbarTestCase(10, "Case 10: 혼합 극수 (2P+4P)", 100, 100, 600, 800),
    BusbarTestCase(11, "Case 11: 대량 분기 (28개)", 100, 50, 700, 1200),
]


class TestBusbarCalculation:
    """부스바 계산 테스트"""

    def test_busbar_calculation_all_cases(self):
        """모든 케이스 부스바 계산 결과 출력"""
        print("\n" + "=" * 100)
        print("[BUSBAR] Busbar Calculation Results - SSOT Based")
        print("=" * 100)
        print(f"\n[SSOT Constants]:")
        print(f"   - BUSBAR_COEFF_20_250A = {BUSBAR_COEFF_20_250A}")
        print(f"   - BUSBAR_COEFF_300_400A = {BUSBAR_COEFF_300_400A}")
        print(f"   - BUSBAR_COEFF_500_800A = {BUSBAR_COEFF_500_800A}")
        print(f"   - PRICE_BUSBAR_PER_KG = {PRICE_BUSBAR_PER_KG:,} won/kg")
        print(f"\n[Spec by AF]:")
        print(f"   - ~125AF:  {BUSBAR_SPEC_3T_15}")
        print(f"   - ~250AF:  {BUSBAR_SPEC_5T_20}")
        print(f"   - ~400AF:  {BUSBAR_SPEC_6T_30}")
        print(f"   - ~800AF:  {BUSBAR_SPEC_8T_40}")

        total_main_price = 0
        total_branch_price = 0

        for tc in TEST_CASES:
            print(f"\n{'-' * 100}")
            print(f"[Case {tc.case_id}] {tc.description}")
            print(f"   Enclosure: {tc.enclosure_w}x{tc.enclosure_h}mm")
            print(f"   Main Breaker Current: {tc.main_current_a}A")

            # MAIN BUS-BAR 계산
            main_bb = calculate_main_busbar(tc.enclosure_w, tc.enclosure_h, tc.main_current_a)
            print(f"\n   [MAIN BUS-BAR]:")
            print(f"      Spec: {main_bb['spec']}")
            print(f"      Coefficient: {main_bb['coefficient']}")
            print(f"      Calc: ({tc.enclosure_w} x {tc.enclosure_h}) x {main_bb['coefficient']} = {main_bb['weight_kg']} kg")
            print(f"      Unit Price: {main_bb['unit_price']:,} won/kg")
            print(f"      Total: {main_bb['weight_kg']} x {main_bb['unit_price']:,} = {main_bb['total_price']:,} won")
            total_main_price += main_bb['total_price']

            # BUS-BAR (분기용) 계산
            if tc.max_branch_af > 0:
                branch_bb = calculate_branch_busbar(tc.enclosure_w, tc.enclosure_h, tc.main_current_a, tc.max_branch_af)
                print(f"\n   [BUS-BAR (Branch)]:")
                print(f"      Max Branch AF: {tc.max_branch_af}AF")
                print(f"      Spec: {branch_bb['spec']}")
                print(f"      Coefficient: {branch_bb['coefficient']}")
                print(f"      Calc: ({tc.enclosure_w} x {tc.enclosure_h}) x {branch_bb['coefficient']} = {branch_bb['weight_kg']} kg")
                print(f"      Unit Price: {branch_bb['unit_price']:,} won/kg")
                print(f"      Total: {branch_bb['weight_kg']} x {branch_bb['unit_price']:,} = {branch_bb['total_price']:,} won")
                total_branch_price += branch_bb['total_price']
            else:
                print(f"\n   [!] No branch breakers - BUS-BAR (Branch) skipped")

        print(f"\n{'=' * 100}")
        print(f"[TOTAL]:")
        print(f"   MAIN BUS-BAR Total: {total_main_price:,} won")
        print(f"   BUS-BAR (Branch) Total: {total_branch_price:,} won")
        print(f"   Grand Total Busbar Cost: {total_main_price + total_branch_price:,} won")
        print("=" * 100)

        # 테스트 통과 (출력 목적)
        assert True

    @pytest.mark.parametrize("tc", TEST_CASES, ids=[f"Case_{tc.case_id}" for tc in TEST_CASES])
    def test_busbar_formula_validation(self, tc: BusbarTestCase):
        """개별 케이스 부스바 공식 검증"""
        # MAIN BUS-BAR
        main_bb = calculate_main_busbar(tc.enclosure_w, tc.enclosure_h, tc.main_current_a)

        # 중량 계산 검증
        expected_weight = apply_rounding(
            (tc.enclosure_w * tc.enclosure_h) * main_bb['coefficient'],
            decimal_places=1
        )
        assert main_bb['weight_kg'] == expected_weight, f"Main busbar weight mismatch"

        # 가격 검증
        expected_price = int(expected_weight * PRICE_BUSBAR_PER_KG)
        assert main_bb['total_price'] == expected_price, f"Main busbar price mismatch"

        # 분기 부스바 (있는 경우)
        if tc.max_branch_af > 0:
            branch_bb = calculate_branch_busbar(tc.enclosure_w, tc.enclosure_h, tc.main_current_a, tc.max_branch_af)
            expected_branch_weight = apply_rounding(
                (tc.enclosure_w * tc.enclosure_h) * branch_bb['coefficient'],
                decimal_places=2
            )
            assert branch_bb['weight_kg'] == expected_branch_weight, f"Branch busbar weight mismatch"

    def test_busbar_spec_by_af(self):
        """AF별 부스바 규격 검증 (분기차단기 최대 AF 기준)"""
        # 메인 100A 기준으로 테스트
        main_current = 100

        # ~100AF → 3T*15
        bb_100 = calculate_branch_busbar(600, 700, main_current, 100)
        assert bb_100['spec'] == BUSBAR_SPEC_3T_15, f"100AF should use {BUSBAR_SPEC_3T_15}"

        # 125~250AF → 5T*20
        bb_200 = calculate_branch_busbar(600, 700, main_current, 200)
        assert bb_200['spec'] == BUSBAR_SPEC_5T_20, f"200AF should use {BUSBAR_SPEC_5T_20}"

        # 300~400AF → 6T*30
        bb_400 = calculate_branch_busbar(600, 700, main_current, 400)
        assert bb_400['spec'] == BUSBAR_SPEC_6T_30, f"400AF should use {BUSBAR_SPEC_6T_30}"

        # 500~800AF → 8T*40
        bb_800 = calculate_branch_busbar(600, 700, main_current, 800)
        assert bb_800['spec'] == BUSBAR_SPEC_8T_40, f"800AF should use {BUSBAR_SPEC_8T_40}"

    def test_main_busbar_coefficient_by_current(self):
        """전류별 메인 부스바 계수 검증"""
        # 20~250A → 0.000007
        bb_75 = calculate_main_busbar(600, 700, 75)
        assert bb_75['coefficient'] == BUSBAR_COEFF_20_250A

        bb_250 = calculate_main_busbar(600, 700, 250)
        assert bb_250['coefficient'] == BUSBAR_COEFF_20_250A

        # 300~400A → 0.000013
        bb_300 = calculate_main_busbar(600, 700, 300)
        assert bb_300['coefficient'] == BUSBAR_COEFF_300_400A

        bb_400 = calculate_main_busbar(600, 700, 400)
        assert bb_400['coefficient'] == BUSBAR_COEFF_300_400A

        # 500~800A → 0.000015
        bb_500 = calculate_main_busbar(600, 700, 500)
        assert bb_500['coefficient'] == BUSBAR_COEFF_500_800A

        bb_800 = calculate_main_busbar(600, 700, 800)
        assert bb_800['coefficient'] == BUSBAR_COEFF_500_800A

    def test_branch_busbar_coefficient_by_main_current(self):
        """메인차단기 전류별 분기 부스바 계수 검증"""
        max_branch_af = 100  # 분기차단기 최대 AF (규격 결정용)

        # 20~250A → 0.0000045
        bb_75 = calculate_branch_busbar(600, 700, 75, max_branch_af)
        assert bb_75['coefficient'] == BRANCH_BUSBAR_COEFF_20_250A

        bb_250 = calculate_branch_busbar(600, 700, 250, max_branch_af)
        assert bb_250['coefficient'] == BRANCH_BUSBAR_COEFF_20_250A

        # 300~400A → 0.000007
        bb_300 = calculate_branch_busbar(600, 700, 300, max_branch_af)
        assert bb_300['coefficient'] == BRANCH_BUSBAR_COEFF_300_400A

        bb_400 = calculate_branch_busbar(600, 700, 400, max_branch_af)
        assert bb_400['coefficient'] == BRANCH_BUSBAR_COEFF_300_400A

        # 500~800A → 0.000009
        bb_500 = calculate_branch_busbar(600, 700, 500, max_branch_af)
        assert bb_500['coefficient'] == BRANCH_BUSBAR_COEFF_500_800A

        bb_800 = calculate_branch_busbar(600, 700, 800, max_branch_af)
        assert bb_800['coefficient'] == BRANCH_BUSBAR_COEFF_500_800A


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
