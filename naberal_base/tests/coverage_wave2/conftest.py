"""
Wave 2 Test Fixtures - breaker_placer.py + enclosure_solver.py

Coverage Targets:
- breaker_placer.py: 15% → 80%
- enclosure_solver.py: 11% → 80%

Zero-Mock Principle: Real engines, real data, real calculations
"""

import pytest
from kis_estimator_core.models.enclosure import BreakerSpec, EnclosureDimensions


# ============================================================================
# Breaker Fixtures
# ============================================================================


@pytest.fixture
def main_breaker_50af():
    """Main breaker: 2P 30A 50AF"""
    return BreakerSpec(
        model="SBE-52", poles=2, current=30, frame_af=50, width=50, height=130, depth=60
    )


@pytest.fixture
def main_breaker_100af():
    """Main breaker: 4P 75A 100AF"""
    return BreakerSpec(
        model="SBE-104",
        poles=4,
        current=75,
        frame_af=100,
        width=100,
        height=130,
        depth=60,
        n_bus_metadata={
            "n_bus_type": "main",
            "n_bus_side": "center",
            "rule": "main_breaker",
        },
    )


@pytest.fixture
def main_breaker_400af():
    """Main breaker: 3P 300A 400AF (large)"""
    return BreakerSpec(
        model="SBS-403",
        poles=3,
        current=300,
        frame_af=400,
        width=140,
        height=257,
        depth=109,
    )


@pytest.fixture
def branch_breakers_small():
    """5 small branch breakers (2P 20A 50AF)"""
    return [
        BreakerSpec(
            model=f"SBE-52-{i}",
            poles=2,
            current=20,
            frame_af=50,
            width=50,
            height=130,
            depth=60,
        )
        for i in range(5)
    ]


@pytest.fixture
def branch_breakers_mixed():
    """Mixed branch breakers: 2P, 3P, different frames"""
    breakers = []

    # 3x 2P 50AF
    for i in range(3):
        breakers.append(
            BreakerSpec(
                model=f"SBE-52-{i}",
                poles=2,
                current=20,
                frame_af=50,
                width=50,
                height=130,
                depth=60,
            )
        )

    # 2x 3P 100AF
    for i in range(2):
        breakers.append(
            BreakerSpec(
                model=f"SBE-103-{i}",
                poles=3,
                current=50,
                frame_af=100,
                width=75,
                height=130,
                depth=60,
            )
        )

    # 1x 4P 200AF
    breakers.append(
        BreakerSpec(
            model="SBS-204",
            poles=4,
            current=125,
            frame_af=200,
            width=140,
            height=165,
            depth=60,
            n_bus_metadata={
                "n_bus_type": "shared",
                "n_bus_side": "left",
                "rule": "shared_if_pair",
            },
        )
    )

    return breakers


@pytest.fixture
def branch_breakers_large():
    """12 branch breakers for large panel"""
    breakers = []

    # 8x 2P 50AF
    for i in range(8):
        breakers.append(
            BreakerSpec(
                model=f"SBE-52-{i}",
                poles=2,
                current=20,
                frame_af=50,
                width=50,
                height=130,
                depth=60,
            )
        )

    # 4x 3P 100AF
    for i in range(4):
        breakers.append(
            BreakerSpec(
                model=f"SBE-103-{i}",
                poles=3,
                current=30,
                frame_af=100,
                width=75,
                height=130,
                depth=60,
            )
        )

    return breakers


# ============================================================================
# Enclosure Fixtures
# ============================================================================


@pytest.fixture
def panel_dimensions_small():
    """Small panel dimensions (600x400x200)"""
    return EnclosureDimensions(width=600, height=400, depth=200)


@pytest.fixture
def panel_dimensions_medium():
    """Medium panel dimensions (700x600x200)"""
    return EnclosureDimensions(width=700, height=600, depth=200)


@pytest.fixture
def panel_dimensions_large():
    """Large panel dimensions (800x800x250)"""
    return EnclosureDimensions(width=800, height=800, depth=250)


# ============================================================================
# Placement Context Fixtures
# ============================================================================


@pytest.fixture
def placement_context_simple(
    main_breaker_100af, branch_breakers_small, panel_dimensions_medium
):
    """Simple placement context: 1 main + 5 branch"""
    return {
        "main_breaker": main_breaker_100af,
        "branch_breakers": branch_breakers_small,
        "panel_dimensions": panel_dimensions_medium,
        "enclosure_type": "옥내노출",
        "material": "STEEL",
        "thickness": "1.6T",
    }


@pytest.fixture
def placement_context_mixed(
    main_breaker_100af, branch_breakers_mixed, panel_dimensions_large
):
    """Mixed placement context: 1 main + 6 mixed branch"""
    return {
        "main_breaker": main_breaker_100af,
        "branch_breakers": branch_breakers_mixed,
        "panel_dimensions": panel_dimensions_large,
        "enclosure_type": "옥내노출",
        "material": "STEEL",
        "thickness": "1.6T",
    }


@pytest.fixture
def placement_context_large(
    main_breaker_400af, branch_breakers_large, panel_dimensions_large
):
    """Large placement context: 1 large main + 12 branch"""
    return {
        "main_breaker": main_breaker_400af,
        "branch_breakers": branch_breakers_large,
        "panel_dimensions": panel_dimensions_large,
        "enclosure_type": "옥내자립",
        "material": "STEEL",
        "thickness": "1.6T",
    }


# ============================================================================
# Enclosure Solver Input Fixtures
# ============================================================================


@pytest.fixture
def solver_input_minimal():
    """Minimal enclosure solver input"""
    return {
        "main_breaker": {
            "model": "SBE-104",
            "poles": 4,
            "current": 75,
            "frame_a": 100,
            "width": 100,
            "height": 130,
            "depth": 60,
            "n_bus_metadata": {
                "n_bus_type": "main",
                "n_bus_side": "center",
                "rule": "main_breaker",
            },
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame_a": 50,
                "width": 50,
                "height": 130,
                "depth": 60,
            }
        ],
        "enclosure_type": "옥내노출",
        "material": "STEEL",
        "thickness": "1.6T",
        "accessories": [],
    }


@pytest.fixture
def solver_input_with_accessories():
    """Enclosure solver input with accessories (magnets, timers)"""
    return {
        "main_breaker": {
            "model": "SBE-104",
            "poles": 4,
            "current": 75,
            "frame_a": 100,
            "width": 100,
            "height": 130,
            "depth": 60,
            "n_bus_metadata": {
                "n_bus_type": "main",
                "n_bus_side": "center",
                "rule": "main_breaker",
            },
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame_a": 50,
                "width": 50,
                "height": 130,
                "depth": 60,
            }
        ],
        "enclosure_type": "옥내노출",
        "material": "STEEL",
        "thickness": "1.6T",
        "accessories": [
            {
                "type": "MAGNET",
                "model": "MC-22",
                "amperage": 22,
                "width": 45,
                "height": 65,
                "depth": 85,
                "quantity": 2,
            },
            {
                "type": "TIMER",
                "model": "ON-DELAY",
                "width": 22.5,
                "height": 75,
                "depth": 100,
                "quantity": 1,
            },
        ],
    }


@pytest.fixture
def solver_input_400af():
    """Large enclosure solver input (400AF main)"""
    return {
        "main_breaker": {
            "model": "SBS-403",
            "poles": 3,
            "current": 300,
            "frame_a": 400,
            "width": 140,
            "height": 257,
            "depth": 109,
        },
        "branch_breakers": [
            {
                "model": "SBS-204",
                "poles": 4,
                "current": 125,
                "frame_a": 200,
                "width": 140,
                "height": 165,
                "depth": 60,
                "n_bus_metadata": {
                    "n_bus_type": "shared",
                    "n_bus_side": "left",
                    "rule": "shared_if_pair",
                },
            }
            for _ in range(4)
        ],
        "enclosure_type": "옥내자립",
        "material": "STEEL",
        "thickness": "1.6T",
        "accessories": [],
    }


# ============================================================================
# Stage Runner Fixtures (Phase I-3.5)
# ============================================================================


@pytest.fixture
def enclosure_with_model_dump():
    """Enclosure that supports model_dump() method (Pydantic-style)

    Tests: Stage 2 panel_spec extraction via model_dump()
    Target Lines: 338-346
    """
    from kis_estimator_core.models.enclosure import (
        EnclosureResult,
        EnclosureDimensions,
        QualityGateResult,
    )

    dimensions = EnclosureDimensions(width_mm=700, height_mm=900, depth_mm=250)

    quality_gate = QualityGateResult(
        name="fit_score",
        actual=0.93,
        threshold=0.90,
        passed=True,
        operator=">=",
        critical=True,
    )

    enclosure = EnclosureResult(
        dimensions=dimensions,
        quality_gate=quality_gate,
        candidates=[],
        calculation_details={},
    )

    return enclosure


@pytest.fixture
def context_without_breakers_data():
    """Context with main_breaker/branch_breakers but NO 'breakers' field

    Tests: Stage 2 breakers data preparation from main_breaker/branch_breakers
    Target Lines: 300-323
    """
    return {
        "enclosure_type": "옥내노출",
        "install_location": "1층",
        "main_breaker": {
            "poles": 3,
            "current": 100,
            "width_mm": 75,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        "branch_breakers": [
            {
                "poles": 2,
                "current": 30,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            },
            {
                "poles": 2,
                "current": 20,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "elb",
            },
        ],
    }


@pytest.fixture
def context_with_enclosure_no_dimensions():
    """Context with enclosure but no dimensions attribute (fallback test)

    Tests: Stage 2 fallback to default panel_spec
    Target Lines: 348-355
    """
    from types import SimpleNamespace

    # Use SimpleNamespace to create an enclosure without proper dimensions
    enclosure = SimpleNamespace(
        some_field="value",
        # No dimensions attribute
        # No model_dump method
    )

    return {
        "enclosure": enclosure,
        "enclosure_result": enclosure,
        "enclosure_type": "옥내노출",
        "main_breaker": {
            "poles": 4,
            "current": 50,
            "width_mm": 100,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        "branch_breakers": [
            {
                "poles": 2,
                "current": 20,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            }
        ],
    }


@pytest.fixture
def placements_with_3pole_breakers():
    """Placements with 3-pole breakers (for per-phase distribution test)

    Tests: Stage 3 phase load calculation for 3-pole breakers
    Target Lines: 481-485
    """
    from kis_estimator_core.engine.breaker_placer import PlacementResult

    return [
        PlacementResult(
            breaker_id="MAIN",
            position={"row": 0, "col": 0, "x": 0, "y": 0},
            phase="L1",  # Main breaker at row 0 (excluded from phase calculation)
            current_a=100,
            poles=4,
        ),
        PlacementResult(
            breaker_id="BR1",
            position={"row": 1, "col": 0, "x": 0, "y": 180},
            phase="L1",  # 3-pole breaker
            current_a=30,
            poles=3,
        ),
        PlacementResult(
            breaker_id="BR2",
            position={"row": 1, "col": 1, "x": 75, "y": 180},
            phase="L1",  # Another 3-pole
            current_a=45,
            poles=3,
        ),
    ]


@pytest.fixture
def placements_with_mixed_poles():
    """Placements with mixed 2P/3P breakers (complex phase calculation)

    Tests: Stage 3 phase load calculation for mixed breakers
    Target Lines: 479-488
    """
    from kis_estimator_core.engine.breaker_placer import PlacementResult

    return [
        PlacementResult(
            breaker_id="MAIN",
            position={"row": 0, "col": 0, "x": 0, "y": 0},
            phase="L1",
            current_a=100,
            poles=4,
        ),
        PlacementResult(
            breaker_id="BR1",
            position={"row": 1, "col": 0, "x": 0, "y": 180},
            phase="L1",  # 2-pole on L1
            current_a=20,
            poles=2,
        ),
        PlacementResult(
            breaker_id="BR2",
            position={"row": 1, "col": 1, "x": 50, "y": 180},
            phase="L2",  # 2-pole on L2
            current_a=30,
            poles=2,
        ),
        PlacementResult(
            breaker_id="BR3",
            position={"row": 1, "col": 2, "x": 100, "y": 180},
            phase="L1",  # 3-pole (distributes across all phases)
            current_a=45,
            poles=3,
        ),
        PlacementResult(
            breaker_id="BR4",
            position={"row": 1, "col": 3, "x": 175, "y": 180},
            phase="L3",  # 2-pole on L3
            current_a=25,
            poles=2,
        ),
    ]


@pytest.fixture
def mock_plan_with_place():
    """Plan with PLACE verb (for Stage 2 testing)"""
    return {
        "steps": [
            {
                "PLACE": {
                    "breakers": ["MAIN", "BR1", "BR2"],
                    "panel": "default",
                    "strategy": "symmetric",
                }
            }
        ]
    }


@pytest.fixture
def context_with_enclosure_for_stage2(enclosure_with_model_dump):
    """Full context with enclosure for Stage 2 testing"""
    return {
        "enclosure": enclosure_with_model_dump,
        "enclosure_result": enclosure_with_model_dump,
        "enclosure_type": "옥내노출",
        "main_breaker": {
            "poles": 3,
            "current": 75,
            "width_mm": 75,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        "branch_breakers": [
            {
                "poles": 2,
                "current": 20,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            },
            {
                "poles": 2,
                "current": 30,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            },
        ],
    }
