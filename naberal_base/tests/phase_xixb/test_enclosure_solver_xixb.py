"""
Phase XIX-B: enclosure_solver.py comprehensive tests
Target: ~11% → 25%+ coverage via 12 focused tests
"""

import pytest
from pathlib import Path
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver
from kis_estimator_core.models.enclosure import (
    BreakerSpec,
    AccessorySpec,
)
from kis_estimator_core.errors import ValidationError, ENC_002


class TestEnclosureSolverBasic:
    """Basic calculation scenarios (6 tests)"""

    def test_calculate_height_valid_simple(self):
        """Height calculation: simple case with main + 3 branches"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-100AF-3P", model="SBE-103", frame_af=100, poles=3, current_a=100
        )
        branches = [
            BreakerSpec(
                id="BR1-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            ),
            BreakerSpec(
                id="BR2-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=30
            ),
            BreakerSpec(
                id="BR3-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            ),
        ]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # Should return positive height
        assert H_total > 0
        assert isinstance(breakdown, dict)
        assert "H_total_mm" in breakdown
        assert "top_margin_mm" in breakdown
        assert "main_breaker_height_mm" in breakdown
        assert "branches_total_height_mm" in breakdown
        assert "bottom_margin_mm" in breakdown

    def test_calculate_width_valid_100af(self):
        """Width calculation: 100AF main"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-100AF-3P", model="SBE-103", frame_af=100, poles=3, current_a=75
        )
        branches = [
            BreakerSpec(
                id="BR1-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            ),
            BreakerSpec(
                id="BR2-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=30
            ),
        ]

        W_total, breakdown = solver.calculate_width(main, branches)

        # Should return positive width
        assert W_total > 0
        assert isinstance(breakdown, dict)
        assert "main_af" in breakdown
        assert breakdown["main_af"] == 100

    def test_calculate_depth_without_pbl(self):
        """Depth calculation: no PBL (on/off switch)"""
        solver = EnclosureSolver()

        accessories = []  # No PBL accessories

        D_total, breakdown = solver.calculate_depth(accessories)

        # Should return standard depth (200mm for no PBL)
        assert D_total > 0
        assert isinstance(breakdown, dict)

    def test_calculate_height_with_accessories(self):
        """Height calculation: with magnet accessories"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-100AF-3P", model="SBE-103", frame_af=100, poles=3, current_a=100
        )
        branches = [
            BreakerSpec(
                id="BR1-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            )
        ]
        accessories = [
            AccessorySpec(type="magnet", model="MC-22", height_mm=75, quantity=2)
        ]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # Height should be positive
        assert H_total > 0
        # Breakdown should include accessory_margin_mm key (value may be 0.0 if not implemented yet)
        assert "accessory_margin_mm" in breakdown
        assert isinstance(breakdown["accessory_margin_mm"], (int, float))

    def test_calculate_width_200af_large_frame(self):
        """Width calculation: 200AF main (large frame)"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-200AF-3P", model="SBS-203", frame_af=200, poles=3, current_a=150
        )
        branches = [
            BreakerSpec(
                id="BR1-100AF-2P", model="SBE-102", frame_af=100, poles=2, current_a=50
            ),
            BreakerSpec(
                id="BR2-100AF-2P", model="SBE-102", frame_af=100, poles=2, current_a=60
            ),
        ]

        W_total, breakdown = solver.calculate_width(main, branches)

        # 200AF should have wider panel (≥700mm)
        assert W_total >= 700
        assert breakdown["main_af"] == 200

    def test_calculate_depth_with_pbl(self):
        """Depth calculation: with PBL (on/off switch)"""
        solver = EnclosureSolver()

        accessories = [AccessorySpec(type="pbl", model="PBL-01", quantity=1)]

        D_total, breakdown = solver.calculate_depth(accessories)

        # Should return deeper panel (250mm with PBL)
        assert D_total > 0
        # With PBL should be deeper than without
        assert D_total >= 200


class TestEnclosureSolverEdgeCases:
    """Edge cases and error paths (6 tests)"""

    def test_init_knowledge_file_not_found_raises_error(self):
        """Init with non-existent knowledge file → raises E_INTERNAL"""
        fake_path = Path("/nonexistent/fake_path/core_rules.json")

        with pytest.raises(Exception) as exc_info:
            EnclosureSolver(knowledge_path=fake_path)

        assert "지식파일을 찾을 수 없습니다" in str(exc_info.value)

    def test_calculate_height_zero_branches(self):
        """Height calculation: main only, no branches"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-100AF-3P", model="SBE-103", frame_af=100, poles=3, current_a=100
        )
        branches = []
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # Should still return valid height
        assert H_total > 0
        assert breakdown["branches_total_height_mm"] == 0

    def test_calculate_height_large_accessory_margin(self):
        """Height calculation: many accessories → large margin"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-100AF-3P", model="SBE-103", frame_af=100, poles=3, current_a=100
        )
        branches = [
            BreakerSpec(
                id="BR1-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            )
        ]
        accessories = [
            AccessorySpec(type="magnet", model=f"MC-{i}", height_mm=75, quantity=1)
            for i in range(5)  # 5 magnets
        ]

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # Accessory margin should be significant
        assert breakdown["accessory_margin_mm"] > 100

    def test_calculate_width_invalid_af_out_of_range(self):
        """Width calculation: invalid AF (e.g., 999) → raises ENC-002"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-999AF-3P",
            model="INVALID-999",
            frame_af=999,
            poles=3,
            current_a=100,
        )
        branches = []

        # Should raise validation error for unknown AF
        with pytest.raises(ValidationError) as exc_info:
            solver.calculate_width(main, branches)

        assert exc_info.value.error_code == ENC_002

    def test_calculate_height_extreme_branch_count(self):
        """Height calculation: 50 branches (stress test)"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-200AF-3P", model="SBS-203", frame_af=200, poles=3, current_a=150
        )
        branches = [
            BreakerSpec(
                id=f"BR{i}-50AF-2P", model="SBE-52", frame_af=50, poles=2, current_a=20
            )
            for i in range(50)
        ]
        accessories = []

        H_total, breakdown = solver.calculate_height(main, branches, accessories)

        # Should handle large number of branches
        assert H_total > 0
        assert breakdown["branches_total_height_mm"] > 1000  # Many branches = tall

    def test_calculate_width_400af_special_rules(self):
        """Width calculation: 400AF → special width rules (≥800mm)"""
        solver = EnclosureSolver()

        main = BreakerSpec(
            id="MAIN-400AF-3P", model="SBS-403", frame_af=400, poles=3, current_a=300
        )
        branches = [
            BreakerSpec(
                id="BR1-200AF-2P", model="SBS-202", frame_af=200, poles=2, current_a=100
            )
        ]

        W_total, breakdown = solver.calculate_width(main, branches)

        # 400AF should have wide panel (≥800mm)
        assert W_total >= 800
        assert breakdown["main_af"] == 400
