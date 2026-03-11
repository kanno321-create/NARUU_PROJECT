"""
TEST-BP-PLACE: BreakerPlacer Placement Algorithm Tests

Coverage Target: place() method - main placement logic
"""

import pytest
from kis_estimator_core.engine.breaker_placer import (
    BreakerPlacer,
    BreakerInput,
    PanelSpec,
)


class TestBreakerPlacerPlacement:
    """BreakerPlacer placement algorithm tests"""

    @pytest.fixture
    def placer(self):
        """BreakerPlacer instance"""
        return BreakerPlacer()

    @pytest.fixture
    def panel_600x800(self):
        """Standard panel 600x800x200"""
        return PanelSpec(width_mm=600, height_mm=800, depth_mm=200, clearance_mm=50)

    @pytest.fixture
    def main_breaker_4p(self):
        """Main breaker: 4P 75A"""
        return BreakerInput(
            id="MAIN",
            poles=4,
            current_a=75,
            width_mm=100,
            height_mm=130,
            depth_mm=60,
            breaker_type="normal",
        )

    @pytest.fixture
    def branch_breakers_2p_6ea(self):
        """6 branch breakers: 2P 20A"""
        return [
            BreakerInput(
                id=f"BR-{i+1}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(6)
        ]

    def test_place_simple_1main_3branch(self, placer, panel_600x800, main_breaker_4p):
        """TEST-BP-PLACE-001: Simple placement (1 main + 3 branch 2P)"""
        branch_breakers = [
            BreakerInput(
                id=f"BR-{i+1}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(3)
        ]

        breakers = [main_breaker_4p] + branch_breakers
        placements = placer.place(breakers, panel_600x800)

        # Should have 4 placements (1 main + 3 branch)
        assert len(placements) == 4

        # Main breaker should be at row=0, center
        main = placements[0]
        assert main.breaker_id == "MAIN"
        assert main.position["row"] == 0
        assert main.position["side"] == "center"
        assert main.poles == 4

    def test_place_perfect_phase_balance_6branch(
        self, placer, panel_600x800, main_breaker_4p, branch_breakers_2p_6ea
    ):
        """TEST-BP-PLACE-002: Perfect phase balance (6 branch = 2R + 2S + 2T)"""
        breakers = [main_breaker_4p] + branch_breakers_2p_6ea
        placements = placer.place(breakers, panel_600x800)

        # Count phases (exclude main, exclude 3P/4P)
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in placements:
            if p.position.get("row") == 0 or p.poles >= 3:
                continue
            phase_counts[p.phase] += 1

        # Should be 2-2-2 (perfect balance)
        assert phase_counts["R"] == 2
        assert phase_counts["S"] == 2
        assert phase_counts["T"] == 2

    def test_place_left_right_symmetry(
        self, placer, panel_600x800, main_breaker_4p, branch_breakers_2p_6ea
    ):
        """TEST-BP-PLACE-003: Left-right symmetry (3 left + 3 right)"""
        breakers = [main_breaker_4p] + branch_breakers_2p_6ea
        placements = placer.place(breakers, panel_600x800)

        # Count left/right (exclude main)
        left_count = sum(1 for p in placements if p.position.get("side") == "left")
        right_count = sum(1 for p in placements if p.position.get("side") == "right")

        # Should be balanced
        assert left_count == right_count or abs(left_count - right_count) == 1

    def test_place_only_main_no_branch(self, placer, panel_600x800, main_breaker_4p):
        """TEST-BP-PLACE-004: Only main breaker (no branch)"""
        breakers = [main_breaker_4p]
        placements = placer.place(breakers, panel_600x800)

        # Should have 1 placement (main only)
        assert len(placements) == 1
        assert placements[0].breaker_id == "MAIN"
        assert placements[0].position["row"] == 0

    def test_place_empty_breakers_error(self, placer, panel_600x800):
        """TEST-BP-PLACE-005: Empty breakers should raise error"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError):
            placer.place([], panel_600x800)

    def test_place_no_panel_error(self, placer, main_breaker_4p):
        """TEST-BP-PLACE-006: No panel spec should raise error"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError):
            placer.place([main_breaker_4p], None)

    def test_place_3p_branch_breakers(self, placer, panel_600x800, main_breaker_4p):
        """TEST-BP-PLACE-007: 3P branch breakers placement"""
        branch_3p = [
            BreakerInput(
                id=f"BR3P-{i+1}",
                poles=3,
                current_a=30,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(2)
        ]

        breakers = [main_breaker_4p] + branch_3p
        placements = placer.place(breakers, panel_600x800)

        # Should have 3 placements (1 main + 2 branch 3P)
        assert len(placements) == 3

        # 3P breakers should have phase="R" (representative)
        three_p_placements = [p for p in placements if p.poles == 3]
        assert len(three_p_placements) == 2
        for p in three_p_placements:
            assert p.phase == "R"

    def test_place_4p_branch_with_n_phase_metadata(
        self, placer, panel_600x800, main_breaker_4p
    ):
        """TEST-BP-PLACE-008: 4P branch breakers with N-phase metadata"""
        branch_4p = [
            BreakerInput(
                id=f"BR4P-{i+1}",
                poles=4,
                current_a=50,
                width_mm=100,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(2)
        ]

        breakers = [main_breaker_4p] + branch_4p
        placements = placer.place(breakers, panel_600x800)

        # Should have 3 placements (1 main + 2 branch 4P)
        assert len(placements) == 3

        # 4P branch breakers should have n_bus_metadata
        four_p_branches = [
            p for p in placements if p.poles == 4 and p.position.get("row") > 0
        ]
        assert len(four_p_branches) == 2

        for p in four_p_branches:
            assert "n_bus_metadata" in p.position
            assert "n_bus_type" in p.position["n_bus_metadata"]

    def test_place_mixed_poles_2p_3p_4p(self, placer, panel_600x800, main_breaker_4p):
        """TEST-BP-PLACE-009: Mixed poles (2P + 3P + 4P branch)"""
        branch_mixed = [
            BreakerInput(
                id="BR2P-1",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="BR3P-1",
                poles=3,
                current_a=30,
                width_mm=75,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="BR4P-1",
                poles=4,
                current_a=50,
                width_mm=100,
                height_mm=130,
                depth_mm=60,
            ),
            BreakerInput(
                id="BR2P-2",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
            ),
        ]

        breakers = [main_breaker_4p] + branch_mixed
        placements = placer.place(breakers, panel_600x800)

        # Should have 5 placements (1 main + 4 branch)
        assert len(placements) == 5

        # Verify pole counts
        pole_counts = {}
        for p in placements:
            pole_counts[p.poles] = pole_counts.get(p.poles, 0) + 1

        assert pole_counts[2] == 2  # 2P breakers
        assert pole_counts[3] == 1  # 3P breaker
        assert pole_counts[4] == 2  # 4P breakers (1 main + 1 branch)

    def test_place_9branch_phase_balance(self, placer, panel_600x800, main_breaker_4p):
        """TEST-BP-PLACE-010: 9 branch breakers (3-3-3 perfect balance)"""
        branch_9ea = [
            BreakerInput(
                id=f"BR-{i+1}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(9)
        ]

        breakers = [main_breaker_4p] + branch_9ea
        placements = placer.place(breakers, panel_600x800)

        # Count phases (exclude main)
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in placements:
            if p.position.get("row") == 0 or p.poles >= 3:
                continue
            phase_counts[p.phase] += 1

        # Should be 3-3-3 (perfect balance)
        assert phase_counts["R"] == 3
        assert phase_counts["S"] == 3
        assert phase_counts["T"] == 3

    def test_place_10branch_uneven_balance(
        self, placer, panel_600x800, main_breaker_4p
    ):
        """TEST-BP-PLACE-011: 10 branch breakers (uneven: 4-3-3 or 3-4-3)"""
        branch_10ea = [
            BreakerInput(
                id=f"BR-{i+1}",
                poles=2,
                current_a=20,
                width_mm=50,
                height_mm=130,
                depth_mm=60,
                breaker_type="normal",
            )
            for i in range(10)
        ]

        breakers = [main_breaker_4p] + branch_10ea
        placements = placer.place(breakers, panel_600x800)

        # Count phases (exclude main)
        phase_counts = {"R": 0, "S": 0, "T": 0}
        for p in placements:
            if p.position.get("row") == 0 or p.poles >= 3:
                continue
            phase_counts[p.phase] += 1

        # Should have diff_max ≤ 1
        counts = list(phase_counts.values())
        diff_max = max(counts) - min(counts)
        assert diff_max <= 1
