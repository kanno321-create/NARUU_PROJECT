"""
Unit tests for infra/quality_gate.py - Quality Gate Validation System

Target: 80% coverage for quality_gate.py (97 lines)
Principles:
- Zero-Mock: Real validation logic only
- Comprehensive operator testing
- Predefined gates verification

Test Count: 14 tests
"""

import pytest
import math

from kis_estimator_core.infra.quality_gate import (
    QualityGate,
    QualityGateValidator,
    QualityGateError,
    ENCLOSURE_GATES,
    BREAKER_PLACEMENT_GATES,
)


# ============================================================================
# Test 1: QualityGate Model Creation
# ============================================================================


@pytest.mark.unit
def test_quality_gate_model_creation():
    """Test 1: QualityGate model with all fields"""
    gate = QualityGate(
        name="fit_score",
        threshold=0.90,
        operator=">=",
        critical=True,
        description="Fit score must be >= 0.90",
    )

    assert gate.name == "fit_score"
    assert gate.threshold == 0.90
    assert gate.operator == ">="
    assert gate.critical is True
    assert gate.description == "Fit score must be >= 0.90"


# ============================================================================
# Test 2: QualityGateValidator Initialization
# ============================================================================


@pytest.mark.unit
def test_quality_gate_validator_initialization():
    """Test 2: QualityGateValidator initialization with gates"""
    gates = [
        QualityGate(name="metric1", threshold=10.0, operator=">=", critical=True),
        QualityGate(name="metric2", threshold=5.0, operator="<=", critical=False),
    ]

    validator = QualityGateValidator(gates)

    assert len(validator.gates) == 2
    assert validator.gates[0].name == "metric1"
    assert validator.gates[1].name == "metric2"


# ============================================================================
# Test 3-6: Operator Testing
# ============================================================================


@pytest.mark.unit
def test_operator_greater_equal():
    """Test 3: Operator >= validation"""
    gate = QualityGate(name="score", threshold=10.0, operator=">=", critical=True)
    validator = QualityGateValidator([gate])

    # Pass: 15 >= 10
    result_pass = validator.validate({"score": 15.0})
    assert result_pass.passed is True
    assert result_pass.results[0].passed is True

    # Pass: 10 >= 10 (boundary)
    result_boundary = validator.validate({"score": 10.0})
    assert result_boundary.passed is True

    # Fail: 5 >= 10
    result_fail = validator.validate({"score": 5.0})
    assert result_fail.passed is False
    assert result_fail.results[0].passed is False


@pytest.mark.unit
def test_operator_less_equal():
    """Test 4: Operator <= validation"""
    gate = QualityGate(name="error_count", threshold=5.0, operator="<=", critical=True)
    validator = QualityGateValidator([gate])

    # Pass: 3 <= 5
    result_pass = validator.validate({"error_count": 3.0})
    assert result_pass.passed is True

    # Pass: 5 <= 5 (boundary)
    result_boundary = validator.validate({"error_count": 5.0})
    assert result_boundary.passed is True

    # Fail: 10 <= 5
    result_fail = validator.validate({"error_count": 10.0})
    assert result_fail.passed is False


@pytest.mark.unit
def test_operator_equal():
    """Test 5: Operator == validation (with float tolerance)"""
    gate = QualityGate(name="violations", threshold=0.0, operator="==", critical=True)
    validator = QualityGateValidator([gate])

    # Pass: 0 == 0
    result_pass = validator.validate({"violations": 0.0})
    assert result_pass.passed is True

    # Pass: 0.0000000001 == 0 (within tolerance 1e-9)
    result_tolerance = validator.validate({"violations": 1e-10})
    assert result_tolerance.passed is True

    # Fail: 1 == 0
    result_fail = validator.validate({"violations": 1.0})
    assert result_fail.passed is False


@pytest.mark.unit
def test_operator_not_equal():
    """Test 6: Operator != validation"""
    gate = QualityGate(name="diversity", threshold=0.0, operator="!=", critical=True)
    validator = QualityGateValidator([gate])

    # Pass: 5 != 0
    result_pass = validator.validate({"diversity": 5.0})
    assert result_pass.passed is True

    # Fail: 0 != 0
    result_fail = validator.validate({"diversity": 0.0})
    assert result_fail.passed is False


# ============================================================================
# Test 7: Missing Value Handling
# ============================================================================


@pytest.mark.unit
def test_missing_value_handling():
    """Test 7: Handle missing values in data"""
    gate = QualityGate(
        name="required_metric", threshold=10.0, operator=">=", critical=True
    )
    validator = QualityGateValidator([gate])

    # Missing value should fail
    result = validator.validate({})

    assert result.passed is False
    assert result.results[0].passed is False
    assert math.isnan(result.results[0].actual_value)
    assert "Missing value" in result.results[0].message


# ============================================================================
# Test 8: Invalid Type Handling
# ============================================================================


@pytest.mark.unit
def test_invalid_type_handling():
    """Test 8: Handle invalid value types"""
    gate = QualityGate(name="score", threshold=10.0, operator=">=", critical=True)
    validator = QualityGateValidator([gate])

    # Invalid type (string that can't convert to float)
    result = validator.validate({"score": "INVALID"})

    assert result.passed is False
    assert result.results[0].passed is False
    assert math.isnan(result.results[0].actual_value)
    assert "Invalid value type" in result.results[0].message


# ============================================================================
# Test 9: Critical Failure Exception
# ============================================================================


@pytest.mark.unit
def test_critical_failure_exception():
    """Test 9: raise_on_failure raises QualityGateError"""
    gate = QualityGate(
        name="critical_metric", threshold=10.0, operator=">=", critical=True
    )
    validator = QualityGateValidator([gate])

    # Should raise QualityGateError
    with pytest.raises(QualityGateError) as exc_info:
        validator.validate({"critical_metric": 5.0}, raise_on_failure=True)

    assert "Critical quality gates failed" in str(exc_info.value)
    assert "1 failures" in str(exc_info.value)


# ============================================================================
# Test 10-11: Predefined Gates
# ============================================================================


@pytest.mark.unit
def test_predefined_enclosure_gates():
    """Test 10: ENCLOSURE_GATES predefined configuration"""
    assert len(ENCLOSURE_GATES) == 3

    # Verify gate names
    gate_names = [g.name for g in ENCLOSURE_GATES]
    assert "fit_score" in gate_names
    assert "ip_rating" in gate_names
    assert "door_clearance_mm" in gate_names

    # All gates critical
    assert all(g.critical for g in ENCLOSURE_GATES)


@pytest.mark.unit
def test_predefined_breaker_placement_gates():
    """Test 11: BREAKER_PLACEMENT_GATES predefined configuration"""
    assert len(BREAKER_PLACEMENT_GATES) == 2

    # Verify gate names
    gate_names = [g.name for g in BREAKER_PLACEMENT_GATES]
    assert "phase_balance_percent" in gate_names
    assert "clearance_violations" in gate_names

    # All gates critical
    assert all(g.critical for g in BREAKER_PLACEMENT_GATES)

    # Verify operators
    phase_balance_gate = next(
        g for g in BREAKER_PLACEMENT_GATES if g.name == "phase_balance_percent"
    )
    assert phase_balance_gate.operator == "<="

    clearance_gate = next(
        g for g in BREAKER_PLACEMENT_GATES if g.name == "clearance_violations"
    )
    assert clearance_gate.operator == "=="


# ============================================================================
# Test 12-14: Helper Methods
# ============================================================================


@pytest.mark.unit
def test_add_gate_method():
    """Test 12: add_gate() adds a new gate"""
    validator = QualityGateValidator([])
    assert len(validator.gates) == 0

    new_gate = QualityGate(
        name="new_metric", threshold=100.0, operator=">=", critical=False
    )
    validator.add_gate(new_gate)

    assert len(validator.gates) == 1
    assert validator.gates[0].name == "new_metric"


@pytest.mark.unit
def test_remove_gate_method():
    """Test 13: remove_gate() removes gate by name"""
    gates = [
        QualityGate(name="metric1", threshold=10.0, operator=">=", critical=True),
        QualityGate(name="metric2", threshold=5.0, operator="<=", critical=False),
    ]
    validator = QualityGateValidator(gates)

    assert len(validator.gates) == 2

    validator.remove_gate("metric1")

    assert len(validator.gates) == 1
    assert validator.gates[0].name == "metric2"


@pytest.mark.unit
def test_get_gate_method():
    """Test 14: get_gate() retrieves gate by name"""
    gates = [
        QualityGate(name="metric1", threshold=10.0, operator=">=", critical=True),
        QualityGate(name="metric2", threshold=5.0, operator="<=", critical=False),
    ]
    validator = QualityGateValidator(gates)

    # Get existing gate
    gate = validator.get_gate("metric1")
    assert gate is not None
    assert gate.name == "metric1"
    assert gate.threshold == 10.0

    # Get non-existing gate
    none_gate = validator.get_gate("nonexistent")
    assert none_gate is None
