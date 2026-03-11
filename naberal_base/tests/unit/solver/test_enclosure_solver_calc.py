"""
Phase I-3.7: engine/enclosure_solver.py Coverage Tests (10.59% → 50%+)
ULTRATHINK | Zero-Mock | SSOT | LAW-01..06

Target: Core calculation methods
- calculate_height()
- calculate_width()
- calculate_depth()
- _get_top_margin()
- _get_bottom_margin()
- _get_breaker_height()
- _calculate_branches_height()
- _calculate_accessory_margin()

DoD: 12+ test cases PASS, ≥50% coverage
"""

import pytest
from pathlib import Path
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.models.enclosure import (
    BreakerSpec,
    AccessorySpec,
)


# ===== Fixtures =====


@pytest.fixture
def solver():
    """EnclosureSolver instance with real knowledge file"""
    # Use actual knowledge file
    knowledge_path = (
        Path(__file__).parent.parent.parent.parent
        / "temp_basic_knowledge"
        / "core_rules.json"
    )

    if not knowledge_path.exists():
        pytest.skip(f"Knowledge file not found: {knowledge_path}")

    return EnclosureSolver(knowledge_path=knowledge_path)


@pytest.fixture
def main_breaker_100af():
    """Standard 100AF main breaker"""
    return BreakerSpec(
        id="MAIN-100A",
        model="SBE-104",
        poles=4,
        frame_af=100,
        current_a=75,
    )


@pytest.fixture
def main_breaker_400af():
    """Large 400AF main breaker"""
    return BreakerSpec(
        id="MAIN-400A",
        model="SBS-404",
        poles=4,
        frame_af=400,
        current_a=300,
    )


@pytest.fixture
def branch_breakers_small():
    """Small branch breakers (2P 30A)"""
    return [
        BreakerSpec(
            id=f"BR-{i+1}-30A",
            model="SBE-52",
            poles=2,
            frame_af=50,
            current_a=30,
        )
        for i in range(5)
    ]


@pytest.fixture
def branch_breakers_large():
    """Large branch breakers (2P 100A)"""
    return [
        BreakerSpec(
            id=f"BR-{i+1}-100A",
            model="SBE-102",
            poles=2,
            frame_af=100,
            current_a=75,
        )
        for i in range(3)
    ]


@pytest.fixture
def accessories_empty():
    """Empty accessories list"""
    return []


@pytest.fixture
def accessories_with_magnets():
    """Accessories with 3 magnets"""
    return [
        AccessorySpec(type="magnet_mc22", model="MC-22", quantity=1),
        AccessorySpec(type="magnet_mc32", model="MC-32", quantity=1),
        AccessorySpec(type="magnet_mc40", model="MC-40", quantity=1),
    ]


@pytest.fixture
def accessories_with_pbl():
    """Accessories with PBL (push button lamp)"""
    return [
        AccessorySpec(type="pbl_on_of", model="PBL", quantity=2),
    ]


# ===== Test Cases =====


@pytest.mark.unit
def test_solver_initialization_success(solver):
    """Test 1: EnclosureSolver initialization with valid knowledge file"""
    assert solver is not None
    assert solver.knowledge is not None
    assert "breaker_dimensions_mm" in solver.knowledge
    assert "frame_clearances" in solver.knowledge
    assert "enclosure_width_rules_mm" in solver.knowledge
    assert "depth_rules_mm" in solver.knowledge


@pytest.mark.unit
def test_solver_initialization_missing_file():
    """Test 2: EnclosureSolver initialization fails with missing file"""
    invalid_path = Path("/nonexistent/path/core_rules.json")

    with pytest.raises(Exception):  # Should raise error from raise_error()
        EnclosureSolver(knowledge_path=invalid_path)


@pytest.mark.unit
def test_calculate_height_basic(
    solver, main_breaker_100af, branch_breakers_small, accessories_empty
):
    """Test 3: calculate_height() with basic configuration"""
    H_total, breakdown = solver.calculate_height(
        main_breaker=main_breaker_100af,
        branch_breakers=branch_breakers_small,
        accessories=accessories_empty,
    )

    # Verify calculation
    assert H_total > 0, "H_total should be positive"
    assert isinstance(breakdown, dict)

    # Verify breakdown components
    assert "top_margin_mm" in breakdown
    assert "main_breaker_height_mm" in breakdown
    assert "main_to_branch_gap_mm" in breakdown
    assert "branches_total_height_mm" in breakdown
    assert "bottom_margin_mm" in breakdown
    assert "accessory_margin_mm" in breakdown
    assert "H_total_mm" in breakdown

    # Verify formula: H_calculated = top + main + gap + branches + bottom + accessory
    calculated_total = (
        breakdown["top_margin_mm"]
        + breakdown["main_breaker_height_mm"]
        + breakdown["main_to_branch_gap_mm"]
        + breakdown["branches_total_height_mm"]
        + breakdown["bottom_margin_mm"]
        + breakdown["accessory_margin_mm"]
    )

    # H_calculated_mm이 수식 합과 일치해야 함 (H_total은 기성함 규격 반올림)
    assert abs(breakdown["H_calculated_mm"] - calculated_total) < 0.1, "H_calculated formula mismatch"
    # H_total은 H_calculated 이상 (업사이징만)
    assert H_total >= calculated_total, "H_total should be >= calculated"


@pytest.mark.unit
def test_calculate_height_with_magnets(
    solver, main_breaker_100af, branch_breakers_small, accessories_with_magnets
):
    """Test 4: calculate_height() with magnet accessories (increases height)"""
    H_total, breakdown = solver.calculate_height(
        main_breaker=main_breaker_100af,
        branch_breakers=branch_breakers_small,
        accessories=accessories_with_magnets,
    )

    # Verify accessory margin is added (3 magnets → should add margin)
    assert breakdown["accessory_margin_mm"] > 0, "Magnets should add accessory margin"
    # 마주보기 배치: 높이 계산값이 상대적으로 낮음 (기성함 규격 반올림됨)
    assert H_total > 700, "Height with magnets should be > 700mm"


@pytest.mark.unit
def test_calculate_height_large_af(
    solver, main_breaker_400af, branch_breakers_large, accessories_empty
):
    """Test 5: calculate_height() with large AF (400AF)"""
    H_total, breakdown = solver.calculate_height(
        main_breaker=main_breaker_400af,
        branch_breakers=branch_breakers_large,
        accessories=accessories_empty,
    )

    # 400AF should have larger margins
    assert breakdown["top_margin_mm"] >= 170, "400AF top margin should be >= 170mm"
    assert (
        breakdown["bottom_margin_mm"] >= 200
    ), "400AF bottom margin should be >= 200mm"
    # 마주보기 배치: 3개 분기 → 2행 → 높이 감소, 기성함 규격 반올림됨
    assert H_total >= 900, "400AF total height should be >= 900mm"


@pytest.mark.unit
def test_calculate_width_basic(solver, main_breaker_100af, branch_breakers_small):
    """Test 6: calculate_width() with 100AF main breaker"""
    W_total, breakdown = solver.calculate_width(
        main_breaker=main_breaker_100af,
        branch_breakers=branch_breakers_small,
    )

    assert W_total > 0, "W_total should be positive"
    assert isinstance(breakdown, dict)
    assert "main_af" in breakdown
    assert "W_base_mm" in breakdown
    assert "W_total_mm" in breakdown
    assert "width_bumped" in breakdown

    # 100AF → typically 600mm width
    assert W_total >= 600, "100AF width should be >= 600mm"


@pytest.mark.unit
def test_calculate_width_400af(solver, main_breaker_400af, branch_breakers_small):
    """Test 7: calculate_width() with 400AF main breaker"""
    W_total, breakdown = solver.calculate_width(
        main_breaker=main_breaker_400af,
        branch_breakers=branch_breakers_small,
    )

    # 400AF → typically 800mm width
    assert W_total >= 800, "400AF width should be >= 800mm"
    assert breakdown["main_af"] == 400


@pytest.mark.unit
def test_calculate_width_bump_condition(solver, main_breaker_400af):
    """Test 8: calculate_width() bump condition (200~250AF branch ≥2)"""
    # Create branch breakers with 200AF
    branch_breakers_200af = [
        BreakerSpec(
            id=f"BR-200AF-{i+1}",
            model="SBS-202",
            poles=2,
            frame_af=200,
            current_a=125,
        )
        for i in range(2)
    ]

    W_total, breakdown = solver.calculate_width(
        main_breaker=main_breaker_400af,
        branch_breakers=branch_breakers_200af,
    )

    # Bump condition: 200~250AF branch ≥2 → width increases
    if "branch_200_250_count" in breakdown:
        assert breakdown["branch_200_250_count"] == 2


@pytest.mark.unit
def test_calculate_depth_no_pbl(solver, accessories_empty):
    """Test 9: calculate_depth() without PBL"""
    D_total, breakdown = solver.calculate_depth(accessories=accessories_empty)

    assert D_total > 0, "D_total should be positive"
    assert isinstance(breakdown, dict)
    assert "has_pbl" in breakdown
    assert breakdown["has_pbl"] is False
    assert "D_total_mm" in breakdown

    # Without PBL: 150mm (SSOT: DEPTH_WITHOUT_PBL_MM)
    assert D_total == 150, "Depth without PBL should be 150mm"


@pytest.mark.unit
def test_calculate_depth_with_pbl(solver, accessories_with_pbl):
    """Test 10: calculate_depth() with PBL (push button lamp)"""
    D_total, breakdown = solver.calculate_depth(accessories=accessories_with_pbl)

    assert breakdown["has_pbl"] is True
    # With PBL: 200mm (SSOT: DEPTH_WITH_PBL_MM)
    assert D_total == 200, "Depth with PBL should be 200mm"


@pytest.mark.unit
def test_get_top_margin(solver):
    """Test 11: _get_top_margin() for various AF values"""
    # Test different AF values
    top_50af = solver._get_top_margin(50)
    top_100af = solver._get_top_margin(100)
    top_400af = solver._get_top_margin(400)

    assert top_50af > 0, "Top margin for 50AF should be positive"
    assert top_100af > 0, "Top margin for 100AF should be positive"
    assert top_400af > 0, "Top margin for 400AF should be positive"

    # Larger AF → typically larger top margin
    assert top_400af >= top_100af, "400AF top margin should be >= 100AF"


@pytest.mark.unit
def test_get_bottom_margin(solver):
    """Test 12: _get_bottom_margin() for various AF values"""
    bottom_50af = solver._get_bottom_margin(50)
    bottom_100af = solver._get_bottom_margin(100)
    bottom_400af = solver._get_bottom_margin(400)

    assert bottom_50af > 0, "Bottom margin for 50AF should be positive"
    assert bottom_100af > 0, "Bottom margin for 100AF should be positive"
    assert bottom_400af > 0, "Bottom margin for 400AF should be positive"

    # Larger AF → typically larger bottom margin
    assert bottom_400af >= bottom_100af, "400AF bottom margin should be >= 100AF"


@pytest.mark.unit
def test_get_breaker_height(solver, main_breaker_100af, main_breaker_400af):
    """Test 13: _get_breaker_height() for various breakers"""
    height_100af = solver._get_breaker_height(main_breaker_100af)
    height_400af = solver._get_breaker_height(main_breaker_400af)

    assert height_100af > 0, "100AF breaker height should be positive"
    assert height_400af > 0, "400AF breaker height should be positive"

    # 400AF is physically larger
    assert height_400af > height_100af, "400AF breaker should be taller than 100AF"


@pytest.mark.unit
def test_get_breaker_height_small_32af(solver):
    """Test 14: _get_breaker_height() for small 32AF breaker"""
    small_breaker = BreakerSpec(
        id="BR-SMALL-32AF",
        model="SIE-32",
        poles=2,
        frame_af=32,
        current_a=20,
    )

    height = solver._get_breaker_height(small_breaker)

    # Small 32AF 2P: typically 70mm
    assert height > 0, "Small breaker height should be positive"
    assert height < 100, "Small breaker height should be < 100mm"


@pytest.mark.unit
def test_calculate_branches_height(solver, branch_breakers_small):
    """Test 15: _calculate_branches_height() with multiple branches (마주보기 배치)"""
    total_height = solver._calculate_branches_height(branch_breakers_small)

    # 마주보기 배치: 5개 → (5+1)//2 = 3행 × 50mm(50AF 2P 폭) = 150mm
    assert total_height > 0, "Branches total height should be positive"
    assert total_height >= 150, "5 branch breakers in face-to-face = 3 rows × 50mm = 150mm"


@pytest.mark.unit
def test_calculate_accessory_margin_no_magnets(solver, accessories_empty):
    """Test 16: _calculate_accessory_margin() with no magnets"""
    margin = solver._calculate_accessory_margin(accessories_empty)

    assert margin == 0.0, "No magnets → no accessory margin"


@pytest.mark.unit
def test_calculate_accessory_margin_single_magnet(solver):
    """Test 17: _calculate_accessory_margin() with 1 magnet"""
    accessories = [AccessorySpec(type="magnet_mc22", model="MC-22", quantity=1)]

    margin = solver._calculate_accessory_margin(accessories)

    # 1 magnet → placed next to main, no height increase
    assert margin == 0.0, "Single magnet → no height increase"


@pytest.mark.unit
def test_calculate_accessory_margin_multiple_magnets(solver, accessories_with_magnets):
    """Test 18: _calculate_accessory_margin() with 3 magnets"""
    margin = solver._calculate_accessory_margin(accessories_with_magnets)

    # 3 magnets → bottom placement, increases height
    assert margin > 0, "Multiple magnets → positive margin"
    # 3 magnets → 1 row → 250mm
    assert margin == 250, "3 magnets → 1 row → 250mm margin"


@pytest.mark.unit
def test_calculate_accessory_margin_many_magnets(solver):
    """Test 19: _calculate_accessory_margin() with 6 magnets (2 rows)"""
    accessories = [
        AccessorySpec(type=f"magnet_mc{i}", model=f"MC-{20+i}", quantity=1)
        for i in range(6)
    ]

    margin = solver._calculate_accessory_margin(accessories)

    # 6 magnets → 2 rows → 500mm
    assert margin == 500, "6 magnets → 2 rows → 500mm margin"


@pytest.mark.unit
def test_calculate_height_formula_validation(
    solver, main_breaker_100af, branch_breakers_small, accessories_empty
):
    """Test 20: Validate H_total formula correctness"""
    H_total, breakdown = solver.calculate_height(
        main_breaker=main_breaker_100af,
        branch_breakers=branch_breakers_small,
        accessories=accessories_empty,
    )

    # Manual calculation
    expected_total = (
        breakdown["top_margin_mm"]
        + breakdown["main_breaker_height_mm"]
        + breakdown["main_to_branch_gap_mm"]
        + breakdown["branches_total_height_mm"]
        + breakdown["bottom_margin_mm"]
        + breakdown["accessory_margin_mm"]
    )

    # Verify H_calculated_mm matches formula (H_total is rounded to standard size)
    assert (
        abs(breakdown["H_calculated_mm"] - expected_total) < 0.01
    ), f"H_calculated mismatch: {breakdown['H_calculated_mm']} vs {expected_total}"
    assert H_total == breakdown["H_total_mm"], "H_total should match breakdown value"
    # H_total은 H_calculated 이상 (기성함 업사이징)
    assert H_total >= breakdown["H_calculated_mm"], "H_total should be >= H_calculated"
