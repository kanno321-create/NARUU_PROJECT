"""
TEST-BP-VALID: BreakerPlacer Validation Tests

Coverage Target: validate(), _validate_phase_balance(), _validate_clearance()
"""

import pytest
from kis_estimator_core.engine.breaker_placer import BreakerPlacer, PlacementResult
from kis_estimator_core.errors import PhaseBlockedError


class TestBreakerPlacerValidation:
    """BreakerPlacer validation tests"""

    @pytest.fixture
    def placer(self):
        """BreakerPlacer instance"""
        return BreakerPlacer()

    @pytest.fixture
    def perfect_balance_placements(self):
        """Perfect phase balance: 2R + 2S + 2T"""
        return [
            # Main breaker (row=0, excluded from balance)
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
            # Branch: 2R
            PlacementResult(
                breaker_id="BR-1",
                position={"x": 150, "y": 200, "row": 1, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-2",
                position={"x": 450, "y": 200, "row": 1, "col": 1, "side": "right"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            # Branch: 2S
            PlacementResult(
                breaker_id="BR-3",
                position={"x": 150, "y": 330, "row": 2, "col": 0, "side": "left"},
                phase="S",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-4",
                position={"x": 450, "y": 330, "row": 2, "col": 1, "side": "right"},
                phase="S",
                current_a=20,
                poles=2,
            ),
            # Branch: 2T
            PlacementResult(
                breaker_id="BR-5",
                position={"x": 150, "y": 460, "row": 3, "col": 0, "side": "left"},
                phase="T",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-6",
                position={"x": 450, "y": 460, "row": 3, "col": 1, "side": "right"},
                phase="T",
                current_a=20,
                poles=2,
            ),
        ]

    @pytest.fixture
    def imbalanced_placements(self):
        """Imbalanced phase: 4R + 1S + 1T (diff_max=3, exceeds MAX_COUNT_DIFF=1)"""
        return [
            # Main
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
            # 4R
            PlacementResult(
                breaker_id="BR-R1",
                position={"x": 150, "y": 200, "row": 1, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-R2",
                position={"x": 450, "y": 200, "row": 1, "col": 1, "side": "right"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-R3",
                position={"x": 150, "y": 330, "row": 2, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-R4",
                position={"x": 450, "y": 330, "row": 2, "col": 1, "side": "right"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            # 1S
            PlacementResult(
                breaker_id="BR-S1",
                position={"x": 150, "y": 460, "row": 3, "col": 0, "side": "left"},
                phase="S",
                current_a=20,
                poles=2,
            ),
            # 1T
            PlacementResult(
                breaker_id="BR-T1",
                position={"x": 450, "y": 460, "row": 3, "col": 1, "side": "right"},
                phase="T",
                current_a=20,
                poles=2,
            ),
        ]

    @pytest.fixture
    def clearance_violation_placements(self):
        """Clearance violation: two breakers too close"""
        return [
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
            # Two breakers at same position (0mm clearance)
            PlacementResult(
                breaker_id="BR-1",
                position={"x": 150, "y": 200, "row": 1, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR-2",
                position={
                    "x": 150,
                    "y": 200,
                    "row": 1,
                    "col": 0,
                    "side": "left",
                },  # Same position!
                phase="S",
                current_a=20,
                poles=2,
            ),
        ]

    def test_validate_perfect_balance_pass(self, placer, perfect_balance_placements):
        """TEST-BP-VALID-001: Perfect phase balance (2-2-2) should pass"""
        result = placer.validate(perfect_balance_placements)

        assert result.phase_imbalance_pct == 0.0  # diff_max=0
        assert result.clearance_violations == 0
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_imbalanced_warning(self, placer, imbalanced_placements):
        """TEST-BP-VALID-002: Imbalanced phase (4-1-1) should warn but not block"""
        result = placer.validate(imbalanced_placements)

        # diff_max = 4-1 = 3 > MAX_COUNT_DIFF=1
        assert result.phase_imbalance_pct == 3.0
        assert len(result.errors) >= 1  # Warning message
        # Note: Phase imbalance is WARNING only, not BLOCKING

    def test_validate_clearance_violation_blocks(
        self, placer, clearance_violation_placements
    ):
        """TEST-BP-VALID-003: Clearance violation should block (PhaseBlockedError)"""
        with pytest.raises(PhaseBlockedError) as exc_info:
            placer.validate(clearance_violation_placements)

        # Should have LAY-002 error
        blocked_error = exc_info.value
        assert len(blocked_error.blocking_errors) >= 1
        assert blocked_error.blocking_errors[0].error_code.code == "LAY-002"

    def test_validate_phase_balance_direct(self, placer, perfect_balance_placements):
        """TEST-BP-VALID-004: Direct _validate_phase_balance call"""
        diff_max = placer._validate_phase_balance(perfect_balance_placements)

        # Should be 0.0 (perfect balance)
        assert diff_max == 0.0

    def test_validate_phase_balance_uneven(self, placer, imbalanced_placements):
        """TEST-BP-VALID-005: Uneven phase balance (4-1-1)"""
        diff_max = placer._validate_phase_balance(imbalanced_placements)

        # Should be 3.0 (4-1=3)
        assert diff_max == 3.0

    def test_validate_clearance_direct_pass(self, placer, perfect_balance_placements):
        """TEST-BP-VALID-006: Direct _validate_clearance call (no violations)"""
        violations = placer._validate_clearance(perfect_balance_placements)

        # Should be 0 (no violations)
        assert violations == 0

    def test_validate_clearance_direct_fail(
        self, placer, clearance_violation_placements
    ):
        """TEST-BP-VALID-007: Direct _validate_clearance call (with violations)"""
        violations = placer._validate_clearance(clearance_violation_placements)

        # Should be > 0 (violations detected)
        assert violations > 0

    def test_validate_only_main_no_branch(self, placer):
        """TEST-BP-VALID-008: Only main breaker (no branch) should pass"""
        placements = [
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            )
        ]

        result = placer.validate(placements)

        # No branch breakers → diff_max=0, no violations
        assert result.phase_imbalance_pct == 0.0
        assert result.clearance_violations == 0
        assert result.is_valid is True

    def test_validate_3p_breakers_excluded_from_count(self, placer):
        """TEST-BP-VALID-009: 3P breakers excluded from phase count"""
        placements = [
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
            # 2x 3P branch (excluded from count)
            PlacementResult(
                breaker_id="BR3P-1",
                position={"x": 150, "y": 200, "row": 1, "col": 0, "side": "left"},
                phase="R",
                current_a=30,
                poles=3,
            ),
            PlacementResult(
                breaker_id="BR3P-2",
                position={"x": 450, "y": 200, "row": 1, "col": 1, "side": "right"},
                phase="R",
                current_a=30,
                poles=3,
            ),
            # 3x 2P branch (counted: 1R + 1S + 1T)
            PlacementResult(
                breaker_id="BR2P-1",
                position={"x": 150, "y": 330, "row": 2, "col": 0, "side": "left"},
                phase="R",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR2P-2",
                position={"x": 450, "y": 330, "row": 2, "col": 1, "side": "right"},
                phase="S",
                current_a=20,
                poles=2,
            ),
            PlacementResult(
                breaker_id="BR2P-3",
                position={"x": 150, "y": 460, "row": 3, "col": 0, "side": "left"},
                phase="T",
                current_a=20,
                poles=2,
            ),
        ]

        diff_max = placer._validate_phase_balance(placements)

        # 3P excluded, only 2P counted: 1-1-1 → diff_max=0
        assert diff_max == 0.0

    def test_validate_4p_n_phase_interference(self, placer):
        """TEST-BP-VALID-010: 4P N-phase interference validation"""
        placements = [
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 300,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "center",
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "center",
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
            # Two 4P breakers facing each other with shared N-phase
            PlacementResult(
                breaker_id="BR4P-L",
                position={
                    "x": 150,
                    "y": 200,
                    "row": 1,
                    "col": 0,
                    "side": "left",
                    "n_bus_metadata": {
                        "n_bus_type": "shared",
                        "n_bus_side": "center",
                        "rule": "shared_if_pair",
                    },
                },
                phase="R",
                current_a=50,
                poles=4,
            ),
            PlacementResult(
                breaker_id="BR4P-R",
                position={
                    "x": 450,
                    "y": 200,
                    "row": 1,
                    "col": 1,
                    "side": "right",
                    "n_bus_metadata": {
                        "n_bus_type": "shared",
                        "n_bus_side": "center",
                        "rule": "shared_if_pair",
                    },
                },
                phase="R",
                current_a=50,
                poles=4,
            ),
        ]

        # Should pass (shared N-phase)
        violations = placer._validate_4p_n_phase_interference(placements)
        assert violations == 0

    def test_validate_branch_bus_rules(self, placer, perfect_balance_placements):
        """TEST-BP-VALID-011: Branch bus rules validation"""
        violations = placer._validate_branch_bus_rules(perfect_balance_placements)

        # Should have no violations (well-formed placements)
        assert len(violations) == 0

    def test_validate_branch_bus_main_not_center_violation(self, placer):
        """TEST-BP-VALID-012: Main breaker not at center should violate center_feed_direction"""
        placements = [
            # Main breaker at LEFT (violation!)
            PlacementResult(
                breaker_id="MAIN",
                position={
                    "x": 150,
                    "y": 50,
                    "row": 0,
                    "col": 0,
                    "side": "left",  # Should be "center"
                    "n_bus_metadata": {
                        "n_bus_type": "main",
                        "n_bus_side": "left",  # Wrong side!
                        "rule": "main_breaker",
                    },
                },
                phase="R",
                current_a=75,
                poles=4,
            ),
        ]

        violations = placer._validate_branch_bus_rules(placements)

        # Should have center_feed_direction violation
        assert len(violations) >= 1
        assert any("center_feed_direction" in v for v in violations)
