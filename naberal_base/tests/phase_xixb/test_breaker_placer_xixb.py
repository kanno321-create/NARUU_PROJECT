"""
Phase XIX-B: breaker_placer.py comprehensive tests
Target: ~40% → 50%+ coverage via 12 focused tests
"""

import pytest
from kis_estimator_core.engine.breaker_placer import (
    BreakerPlacer,
    BreakerInput,
    PanelSpec,
    PlacementResult,
)
from kis_estimator_core.core.ssot.constants import MAX_COUNT_DIFF


class TestBreakerPlacerBasic:
    """Basic placement scenarios (6 tests)"""

    def test_place_single_3p_main_only(self):
        """Single 3P main breaker placement"""
        placer = BreakerPlacer()

        main = BreakerInput(
            id="MAIN-3P-100A",
            poles=3,
            current_a=100,
            width_mm=90,
            height_mm=155,
            depth_mm=60,
        )

        panel = PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=10)

        result = placer.place([main], panel)

        assert len(result) == 1
        assert result[0].breaker_id == "MAIN-3P-100A"
        assert result[0].poles == 3
        assert result[0].position["row"] == 0
        assert result[0].position["side"] == "center"
        assert result[0].phase == "R"

    def test_place_main_plus_6_branches_perfect_balance(self):
        """Main + 6 branches (2P each) → perfect R/S/T balance (2:2:2)"""
        placer = BreakerPlacer()

        main = BreakerInput(
            id="MAIN-3P",
            poles=3,
            current_a=100,
            width_mm=90,
            height_mm=155,
            depth_mm=60,
        )

        branches = [
            BreakerInput(
                id=f"BR-2P-{i}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(6)
        ]

        panel = PanelSpec(width_mm=700, height_mm=800, depth_mm=200, clearance_mm=10)

        result = placer.place([main] + branches, panel)

        assert len(result) == 7  # 1 main + 6 branches

        # Count phases (exclude main row=0)
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in result:
            if p.position["row"] > 0:
                phase = p.phase
                if phase in phase_counts:
                    phase_counts[phase] += 1

        # Perfect balance: 2:2:2
        assert phase_counts["R"] == 2
        assert phase_counts["S"] == 2
        assert phase_counts["T"] == 2

    def test_place_imbalanced_7_branches(self):
        """7 branches → imbalance 3:2:2 (diff_max=1, acceptable)"""
        placer = BreakerPlacer()

        main = BreakerInput(
            id="MAIN", poles=3, current_a=100, width_mm=90, height_mm=155, depth_mm=60
        )

        branches = [
            BreakerInput(
                id=f"BR-{i}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(7)
        ]

        panel = PanelSpec(width_mm=700, height_mm=800, depth_mm=200, clearance_mm=10)

        result = placer.place([main] + branches, panel)

        # Count phases
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in result:
            if p.position["row"] > 0:
                if p.phase in phase_counts:
                    phase_counts[p.phase] += 1

        # 7 = 3 + 2 + 2 → max diff = 1 ≤ MAX_COUNT_DIFF
        counts = sorted(phase_counts.values())
        diff_max = counts[-1] - counts[0]
        assert diff_max <= MAX_COUNT_DIFF

    def test_validate_perfect_balance_zero_clearance_violations(self):
        """Validation: perfect balance + zero clearance violations"""
        placer = BreakerPlacer()

        # Create balanced placements
        placements = [
            PlacementResult(
                breaker_id="MAIN",
                position={"x": 300, "y": 50, "row": 0, "col": 0, "side": "center"},
                phase="R",
                current_a=100,
                poles=3,
            ),
            PlacementResult(
                breaker_id="BR-R",
                position={"x": 150, "y": 200, "row": 1, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-S",
                position={"x": 450, "y": 200, "row": 1, "col": 1, "side": "right"},
                phase="S",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-T",
                position={"x": 150, "y": 350, "row": 2, "col": 0, "side": "left"},
                phase="T",
                current_a=20,
                poles=2,
            ),
        ]

        result = placer.validate(placements)

        # Perfect balance: 1:1:1 (diff_max=0)
        assert result.phase_imbalance_pct == 0.0
        assert result.clearance_violations == 0
        assert result.is_valid is True

    def test_place_no_breakers_raises_error(self):
        """Empty breaker list → raises E_INTERNAL error"""
        placer = BreakerPlacer()

        panel = PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=10)

        with pytest.raises(Exception) as exc_info:
            placer.place([], panel)

        # Should raise EstimatorError with E_INTERNAL
        assert "No breakers provided" in str(exc_info.value)

    def test_place_no_panel_raises_error(self):
        """No panel spec → raises E_INTERNAL error"""
        placer = BreakerPlacer()

        main = BreakerInput(
            id="MAIN", poles=3, current_a=100, width_mm=90, height_mm=155, depth_mm=60
        )

        with pytest.raises(Exception) as exc_info:
            placer.place([main], None)

        assert "No panel spec provided" in str(exc_info.value)


class TestBreakerPlacerEdgeCases:
    """Edge cases and error paths (6 tests)"""

    def test_place_mixed_pole_count_3p_4p_2p(self):
        """Mixed pole counts: 3P main + 4P branch + 2P branches"""
        placer = BreakerPlacer()

        main_3p = BreakerInput(
            id="MAIN-3P",
            poles=3,
            current_a=100,
            width_mm=90,
            height_mm=155,
            depth_mm=60,
        )

        branch_4p = BreakerInput(
            id="BR-4P", poles=4, current_a=50, width_mm=100, height_mm=130, depth_mm=60
        )

        branches_2p = [
            BreakerInput(
                id=f"BR-2P-{i}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(3)
        ]

        panel = PanelSpec(width_mm=700, height_mm=1000, depth_mm=200, clearance_mm=10)

        result = placer.place([main_3p, branch_4p] + branches_2p, panel)

        # 1 main (3P) + 1 branch (4P) + 3 branches (2P) = 5 total
        assert len(result) == 5

        # Main should be first (row 0)
        assert result[0].poles == 3
        assert result[0].position["row"] == 0

        # 4P branch should have n_bus_metadata
        four_pole_result = next(p for p in result if p.poles == 4)
        assert "n_bus_metadata" in four_pole_result.position

    def test_validate_imbalance_exceeds_max_count_diff_warning(self):
        """Imbalance exceeds MAX_COUNT_DIFF → warning (not blocking)"""
        placer = BreakerPlacer()

        # Create severely imbalanced placements: 10:0:0 (diff_max=10)
        placements = [
            PlacementResult(
                breaker_id="MAIN",
                position={"x": 300, "y": 50, "row": 0, "col": 0, "side": "center"},
                phase="R",
                current_a=100,
                poles=3,
            )
        ] + [
            PlacementResult(
                breaker_id=f"BR-R-{i}",
                position={
                    "x": 150,
                    "y": 200 + i * 150,
                    "row": i + 1,
                    "col": 0,
                    "side": "left",
                },
                phase="R",  # All R phase
                current_a=20,
                poles=2,
            )
            for i in range(10)
        ]

        result = placer.validate(placements)

        # diff_max = 10 > MAX_COUNT_DIFF (1), but not blocking
        # phase_imbalance_pct represents diff_max directly (10.0), not percentage
        assert result.phase_imbalance_pct >= 10.0  # Severely imbalanced
        assert len(result.errors) > 0
        # Note: imbalance is WARNING only, not is_valid=False

    def test_place_4p_only_no_main(self):
        """4P branch without main → should still work"""
        placer = BreakerPlacer()

        branch_4p = BreakerInput(
            id="BR-4P-ONLY",
            poles=4,
            current_a=50,
            width_mm=100,
            height_mm=130,
            depth_mm=60,
        )

        panel = PanelSpec(width_mm=700, height_mm=600, depth_mm=200, clearance_mm=10)

        result = placer.place([branch_4p], panel)

        # Should place successfully
        assert len(result) == 1
        assert result[0].poles == 4
        # First breaker should be considered "main" if 3P or 4P
        assert result[0].position["row"] == 0

    def test_place_only_2p_branches_no_main(self):
        """Only 2P branches, no main → should distribute R/S/T"""
        placer = BreakerPlacer()

        branches = [
            BreakerInput(
                id=f"BR-{i}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            )
            for i in range(9)
        ]

        panel = PanelSpec(width_mm=700, height_mm=1000, depth_mm=200, clearance_mm=10)

        result = placer.place(branches, panel)

        # 9 branches → 3:3:3 perfect balance
        assert len(result) == 9

        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in result:
            if p.phase in phase_counts:
                phase_counts[p.phase] += 1

        # 9 branches → 3:3:3
        assert phase_counts["R"] == 3
        assert phase_counts["S"] == 3
        assert phase_counts["T"] == 3

    def test_place_small_breaker_type(self):
        """Small breaker type (SIE-32, SIB-32)"""
        placer = BreakerPlacer()

        main = BreakerInput(
            id="MAIN", poles=3, current_a=100, width_mm=90, height_mm=155, depth_mm=60
        )

        small_breaker = BreakerInput(
            id="SMALL-2P-20A",
            poles=2,
            current_a=20,
            width_mm=33,
            height_mm=70,
            depth_mm=42,
            breaker_type="small",
        )

        panel = PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=10)

        result = placer.place([main, small_breaker], panel)

        assert len(result) == 2
        # Small breaker should be placed as branch
        small_result = next(p for p in result if p.breaker_id == "SMALL-2P-20A")
        assert small_result.position["row"] > 0  # Branch, not main

    def test_validate_empty_placements(self):
        """Empty placements list → raises ValueError (max on empty sequence)"""
        placer = BreakerPlacer()

        # validate([]) calls max() on empty sequence → ValueError
        with pytest.raises(ValueError) as exc_info:
            placer.validate([])

        assert "empty sequence" in str(exc_info.value).lower()
