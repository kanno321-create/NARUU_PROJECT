"""
P4-2.1: Quality Gate Validator Tests
Target: validator.py 21.74% → 60% coverage

Tests validation rules from specs/gates/estimation.yaml:
- balance_limit: 0.03 (3%)
- fit_score_min: 0.90
- forbid_violations: true

SB-05 Compliant: Zero-Mock, real policy file
LAW-04: AppError snapshots with error_code verification
"""

import pytest
from kis_estimator_core.kpew.gates.validator import GateValidator
from kis_estimator_core.errors.error_codes import LAY_001, ENC_001, LAY_002

# Import module explicitly for coverage measurement
from kis_estimator_core.kpew.gates import validator as _  # noqa: F401


class TestGateValidator:
    """Quality gate validation tests"""

    @pytest.fixture
    def validator(self):
        """Validator instance with real policy"""
        return GateValidator()

    # ========================================
    # validate_balance tests
    # ========================================

    def test_validate_balance_perfect(self, validator):
        """Perfect balance (0% imbalance) - PASS"""
        phase_loads = {"L1": 100.0, "L2": 100.0, "L3": 100.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_balance_within_limit(self, validator):
        """Imbalance within 3% limit - PASS"""
        # avg = 100, max_diff = 2, imbalance = 2%
        phase_loads = {"L1": 102.0, "L2": 100.0, "L3": 98.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_balance_exceed_limit(self, validator):
        """Imbalance exceeds 3% limit - FAIL (LAY_001)"""
        # avg = 100, max_diff = 10, imbalance = 10% > 3%
        phase_loads = {"L1": 110.0, "L2": 100.0, "L3": 90.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].error_code == LAY_001
        assert errors[0].phase == "Stage 3: Balance"
        assert "imbalance" in errors[0].details
        assert errors[0].details["imbalance"] > 0.03

    def test_validate_balance_normalize_keys_ia_ib_ic(self, validator):
        """Normalize Ia/Ib/Ic → L1/L2/L3 - PASS"""
        phase_loads = {"Ia": 100.0, "Ib": 102.0, "Ic": 98.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_balance_zero_load(self, validator):
        """Zero load (no imbalance) - PASS"""
        phase_loads = {"L1": 0.0, "L2": 0.0, "L3": 0.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_balance_boundary_exact_limit(self, validator):
        """Imbalance exactly 3% (boundary) - PASS"""
        # avg = 100, max_diff = 3, imbalance = 3%
        phase_loads = {"L1": 103.0, "L2": 100.0, "L3": 97.0}
        is_valid, errors = validator.validate_balance(phase_loads)

        # Note: boundary might be inclusive or exclusive, adjust if needed
        # Current implementation uses '>' so 3.0% should PASS
        assert is_valid is True
        assert len(errors) == 0

    # ========================================
    # validate_fit_score tests
    # ========================================

    def test_validate_fit_score_exact_min(self, validator):
        """Fit score exactly 0.90 (min) - PASS"""
        is_valid, errors = validator.validate_fit_score(0.90)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_fit_score_above_min(self, validator):
        """Fit score above 0.90 - PASS"""
        is_valid, errors = validator.validate_fit_score(0.95)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_fit_score_below_min(self, validator):
        """Fit score below 0.90 - FAIL (ENC_001)"""
        is_valid, errors = validator.validate_fit_score(0.85)

        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].error_code == ENC_001
        assert errors[0].phase == "Stage 1: Enclosure"
        assert errors[0].details["fit_score"] == 0.85
        assert errors[0].details["min_required"] == 0.90

    # ========================================
    # validate_violations tests
    # ========================================

    def test_validate_violations_empty(self, validator):
        """No violations - PASS"""
        is_valid, errors = validator.validate_violations([])

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_violations_single(self, validator):
        """Single violation - FAIL (LAY_002)"""
        violations = ["slot_overlap_detected"]
        is_valid, errors = validator.validate_violations(violations)

        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].error_code == LAY_002
        assert errors[0].phase == "Stage 2: Layout"
        assert errors[0].details["violation"] == "slot_overlap_detected"

    def test_validate_violations_multiple(self, validator):
        """Multiple violations - FAIL (multiple LAY_002)"""
        violations = ["slot_overlap", "width_exceeded", "vendor_rule_violated"]
        is_valid, errors = validator.validate_violations(violations)

        assert is_valid is False
        assert len(errors) == 3
        for i, error in enumerate(errors):
            assert error.error_code == LAY_002
            assert error.phase == "Stage 2: Layout"
            assert error.details["violation"] == violations[i]
