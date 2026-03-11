"""
Coverage Wave 1 - Test Fixtures for stage_runner.py
Zero-Mock Principle: Real DB, Real Engines, Real Data
"""

import pytest
from pathlib import Path


@pytest.fixture
def mock_plan_minimal():
    """Minimal plan without verbs (for basic stage testing)"""
    return {"steps": []}


@pytest.fixture
def mock_plan_with_pick_enclosure():
    """Plan with PICK_ENCLOSURE verb

    NOTE: Pydantic validation requires all fields in params
    stage_runner will also copy context data to ctx.state
    """
    return {
        "steps": [
            {
                "PICK_ENCLOSURE": {
                    "main_breaker": {
                        "model": "SBS-404",
                        "poles": 4,
                        "current": 50,
                        "frame_af": 400,
                    },
                    "branch_breakers": [
                        {"model": "SBE-52", "poles": 2, "current": 20, "frame_af": 50}
                    ],
                    "enclosure_type": "옥내노출",
                    "material": "STEEL",
                    "thickness": "1.6T",
                    "accessories": [],
                    "panel": "default",
                    "strategy": "auto",
                }
            }
        ]
    }


@pytest.fixture
def mock_plan_with_place():
    """Plan with PLACE verb

    NOTE: Pydantic validation requires breakers list
    """
    return {
        "steps": [
            {
                "PLACE": {
                    "breakers": ["MAIN", "BR1", "BR2", "BR3"],
                    "panel": "default",
                    "strategy": "symmetric",
                }
            }
        ]
    }


@pytest.fixture
def mock_plan_with_rebalance():
    """Plan with REBALANCE verb"""
    return {"steps": [{"REBALANCE": {"max_imbalance_pct": 4.0}}]}


@pytest.fixture
def mock_plan_full():
    """Full plan with all verbs"""
    return {
        "steps": [
            {
                "PICK_ENCLOSURE": {
                    "main_breaker": {
                        "model": "SBS-404",
                        "poles": 4,
                        "current": 50,
                        "frame_af": 400,
                    },
                    "branch_breakers": [
                        {"model": "SBE-52", "poles": 2, "current": 20, "frame_af": 50}
                    ],
                    "enclosure_type": "옥내노출",
                    "material": "STEEL",
                    "thickness": "1.6T",
                    "accessories": [],
                    "panel": "default",
                    "strategy": "auto",
                }
            },
            {
                "PLACE": {
                    "breakers": ["MAIN", "BR1", "BR2", "BR3"],
                    "panel": "default",
                    "strategy": "symmetric",
                }
            },
            {"REBALANCE": {"max_imbalance_pct": 4.0}},
        ]
    }


@pytest.fixture
def context_minimal():
    """Minimal context (will trigger input validation errors)"""
    return {}


@pytest.fixture
def context_with_inputs():
    """Context with valid inputs for Stage 0 validation"""
    return {
        "enclosure_type": "옥내노출",
        "install_location": "지하1층",
        "main_breaker": {
            "model": "SBS-404",
            "poles": 4,
            "current": 50,
            "frame_a": 400,
            "width_mm": 100,
            "height_mm": 130,
            "depth_mm": 60,
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame_a": 50,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
            }
        ],
        "material": "STEEL",
        "thickness": "1.6T",
    }


@pytest.fixture
def context_with_enclosure():
    """Context with enclosure result (for Stage 2 testing)"""
    from kis_estimator_core.models.enclosure import (
        EnclosureResult,
        EnclosureDimensions,
        QualityGateResult,
    )

    dimensions = EnclosureDimensions(width_mm=600, height_mm=800, depth_mm=200)

    quality_gate = QualityGateResult(
        name="fit_score",
        actual=0.95,
        threshold=0.90,
        passed=True,
        operator=">=",
        critical=True,
    )

    enclosure_result = EnclosureResult(
        dimensions=dimensions,
        quality_gate=quality_gate,
        candidates=[],
        calculation_details={},
    )

    return {
        "enclosure_type": "옥내노출",
        "install_location": "지하1층",
        "main_breaker": {
            "model": "SBS-404",
            "poles": 4,
            "current": 50,
            "frame_a": 400,
            "width_mm": 100,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        "branch_breakers": [
            {
                "model": "SBE-52",
                "poles": 2,
                "current": 20,
                "frame_a": 50,
                "width_mm": 50,
                "height_mm": 130,
                "depth_mm": 60,
                "breaker_type": "normal",
            }
            for _ in range(10)
        ],
        "enclosure": enclosure_result,
        "enclosure_result": enclosure_result,
        "dimensions": dimensions,
        "fit_score": 0.95,
    }


@pytest.fixture
def context_with_placements(context_with_enclosure):
    """Context with placements (for Stage 3+ testing)"""
    from kis_estimator_core.engine.breaker_placer import PlacementResult

    context = context_with_enclosure.copy()

    # Add placements (simplified for testing)
    context["placements"] = [
        PlacementResult(
            breaker_id="MAIN",
            position={"row": 0, "col": 0, "x": 0, "y": 0},
            phase="L1",  # Main breaker can be L1 (arbitrary for testing)
            current_a=50,
            poles=4,
        ),
        PlacementResult(
            breaker_id="BR1",
            position={"row": 1, "col": 0, "x": 0, "y": 180},
            phase="L1",
            current_a=20,
            poles=2,
        ),
        PlacementResult(
            breaker_id="BR2",
            position={"row": 1, "col": 1, "x": 50, "y": 180},
            phase="L2",
            current_a=20,
            poles=2,
        ),
        PlacementResult(
            breaker_id="BR3",
            position={"row": 1, "col": 2, "x": 100, "y": 180},
            phase="L3",
            current_a=20,
            poles=2,
        ),
    ]

    # Add breakers data for BOM stage
    context["breakers"] = [
        {
            "breaker_id": "MAIN",
            "poles": 4,
            "current_a": 50,
            "width_mm": 100,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        {
            "breaker_id": "BR1",
            "poles": 2,
            "current_a": 20,
            "width_mm": 50,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        {
            "breaker_id": "BR2",
            "poles": 2,
            "current_a": 20,
            "width_mm": 50,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
        {
            "breaker_id": "BR3",
            "poles": 2,
            "current_a": 20,
            "width_mm": 50,
            "height_mm": 130,
            "depth_mm": 60,
            "breaker_type": "normal",
        },
    ]

    # Add panel_spec for PlaceVerb
    context["panel_spec"] = {
        "width_mm": 600,
        "height_mm": 800,
        "depth_mm": 200,
        "clearance_mm": 50,
    }

    return context


@pytest.fixture
def context_with_estimate_data(context_with_placements):
    """Context with estimate_data (for Stage 5-7 testing)"""
    from types import SimpleNamespace

    context = context_with_placements.copy()

    # Add estimate_data (simplified for testing with SimpleNamespace for flexibility)
    # Using SimpleNamespace to avoid complex model requirements
    item1 = SimpleNamespace(amount=150000)
    item2 = SimpleNamespace(amount=50000)
    item3 = SimpleNamespace(amount=50000)

    panel = SimpleNamespace(
        panel_id="LP-M",
        quantity=1,
        subtotal=250000,
        items=[item1, item2, item3],  # Stage 5 iterates over panel.items
    )

    context["estimate_data"] = SimpleNamespace(
        customer_name="테스트고객",
        project_name="테스트프로젝트",
        panels=[panel],
        total_amount=250000,
        vat_included=275000,
    )

    context["total_cost"] = 250000
    context["total_cost_with_vat"] = 275000

    return context


@pytest.fixture
def real_template_path():
    """Real template path (NO MOCKS!)"""
    project_root = Path(__file__).parent.parent.parent
    template = project_root / "절대코어파일" / "견적서양식.xlsx"

    if not template.exists():
        pytest.skip(f"Real template required: {template} (NO MOCKS!)")

    return template
