"""
TEST-BP-INIT: BreakerPlacer Initialization Tests

Coverage Target: __init__ method and class setup
"""

from kis_estimator_core.engine.breaker_placer import BreakerPlacer


class TestBreakerPlacerInit:
    """BreakerPlacer initialization and setup tests"""

    def test_init_default(self):
        """TEST-BP-INIT-001: Initialize with default settings"""
        placer = BreakerPlacer()

        assert placer is not None
        assert hasattr(placer, "branch_bus_rules")
        assert hasattr(placer, "validation_guards")
        assert hasattr(placer, "n_phase_row_rules")

    def test_init_branch_bus_rules_loaded(self):
        """TEST-BP-INIT-003: Verify branch bus rules loaded from SSOT"""
        placer = BreakerPlacer()

        # branch_bus_rules should be dict or object
        assert placer.branch_bus_rules is not None

    def test_init_validation_guards_loaded(self):
        """TEST-BP-INIT-004: Verify validation guards loaded"""
        placer = BreakerPlacer()

        # validation_guards should exist
        assert placer.validation_guards is not None

    def test_init_n_phase_rules_loaded(self):
        """TEST-BP-INIT-005: Verify N-phase row rules loaded"""
        placer = BreakerPlacer()

        # n_phase_row_rules should exist
        assert placer.n_phase_row_rules is not None
