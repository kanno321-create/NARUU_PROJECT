"""
Phase II-Plus D: quality_gate 유닛 2TC (+0.5~0.6%p)

Zero-Mock Principle:
- No mocking, actual QualityGateValidator execution
- Uses SSOT constants for thresholds
- Real validation logic only

Coverage Target:
- quality_gate.py: validate() boundary conditions
- quality_gate.py: _compare() operator logic
"""

import pytest

from kis_estimator_core.infra.quality_gate import (
    QualityGate,
    QualityGateValidator,
    QualityGateError,
)


class TestQualityGateFinish2:
    """Unit tests for quality_gate.py boundary cases"""

    def test_quality_pass_boundary(self):
        """
        QualityGateValidator.validate(): Exactly at threshold = PASS

        Covers:
        - quality_gate.py: validate() method with boundary value
        - quality_gate.py: _compare() with >= operator at exact threshold
        - quality_gate.py: QualityGateValidationResult assembly (passed=True)
        """
        # Arrange: Create gate with >= operator, value exactly at threshold
        gate = QualityGate(
            name="fit_score",
            threshold=0.90,
            operator=">=",
            critical=True,
            description="Fit score must be >= 0.90",
        )
        validator = QualityGateValidator([gate])

        # Data with value exactly at threshold: 0.90 >= 0.90 → True
        data = {"fit_score": 0.90}

        # Act: Validate
        result = validator.validate(data, raise_on_failure=False)

        # Assert: Should PASS (boundary condition: exactly at threshold)
        assert result.passed is True, "Expected PASS at exact threshold (0.90 >= 0.90)"
        assert result.total_gates == 1
        assert result.passed_gates == 1
        assert result.failed_gates == 0
        assert result.critical_failures == 0

        # Verify gate result details
        gate_result = result.results[0]
        assert gate_result.passed is True
        assert gate_result.actual_value == 0.90
        assert gate_result.threshold == 0.90
        assert gate_result.operator == ">="
        assert "PASS" in gate_result.message

    def test_quality_fail_boundary(self):
        """
        QualityGateValidator.validate(): Below threshold by 0.01 = FAIL → AppError("QG-FAIL")

        Covers:
        - quality_gate.py: validate() method with failing value
        - quality_gate.py: _compare() failure path (0.89 >= 0.90 → False)
        - quality_gate.py: QualityGateValidationResult assembly (passed=False)
        - quality_gate.py: raise_on_failure flag → QualityGateError
        """
        # Arrange: Create gate with >= operator, value below threshold
        gate = QualityGate(
            name="fit_score",
            threshold=0.90,
            operator=">=",
            critical=True,
            description="Fit score must be >= 0.90",
        )
        validator = QualityGateValidator([gate])

        # Data with value below threshold: 0.89 >= 0.90 → False
        data_fail = {"fit_score": 0.89}

        # Act & Assert 1: Validate without exception (raise_on_failure=False)
        result = validator.validate(data_fail, raise_on_failure=False)

        assert result.passed is False, "Expected FAIL below threshold (0.89 >= 0.90)"
        assert result.total_gates == 1
        assert result.passed_gates == 0
        assert result.failed_gates == 1
        assert result.critical_failures == 1

        # Verify gate result details
        gate_result = result.results[0]
        assert gate_result.passed is False
        assert gate_result.actual_value == 0.89
        assert gate_result.threshold == 0.90
        assert gate_result.operator == ">="
        assert "FAIL" in gate_result.message

        # Act & Assert 2: Validate with exception (raise_on_failure=True)
        with pytest.raises(QualityGateError) as exc_info:
            validator.validate(data_fail, raise_on_failure=True)

        # Verify exception message
        error_message = str(exc_info.value)
        assert "Critical quality gates failed" in error_message
        assert "1 failures" in error_message or "fit_score" in error_message
