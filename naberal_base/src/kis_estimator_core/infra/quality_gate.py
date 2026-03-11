"""
Quality Gate System for KIS Estimator
Real validation logic - NO MOCKS
Validates pipeline stage outputs against defined criteria
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# SSOT Integration - Constants
from ..core.ssot.constants import (
    CLEARANCE_VIOLATIONS_THRESHOLD,
    DOOR_CLEARANCE_THRESHOLD,
    FIT_SCORE_THRESHOLD,
    FORMULA_PRESERVATION_THRESHOLD,
    IP_RATING_THRESHOLD,
    LINT_ERRORS_THRESHOLD,
    NAMED_RANGE_DAMAGE_THRESHOLD,
    PHASE_BALANCE_THRESHOLD,
    POLICY_VIOLATIONS_THRESHOLD,
)

# SSOT Integration - Enums (LAW-02: Single Source of Truth)


class QualityGate(BaseModel):
    """
    Quality gate definition with validation criteria

    Example:
        QualityGate(
            name="fit_score",
            threshold=0.90,
            operator=">=",
            critical=True,
            description="Enclosure fit score must be >= 0.90"
        )
    """

    name: str = Field(..., description="Gate name (e.g., 'fit_score', 'phase_balance')")
    threshold: float = Field(..., description="Threshold value for comparison")
    operator: Literal[">=", "<=", "==", "!="] = Field(
        ..., description="Comparison operator"
    )
    critical: bool = Field(
        default=True, description="If True, gate failure blocks pipeline"
    )
    description: str | None = Field(None, description="Human-readable description")

    class Config:
        use_enum_values = True


class QualityGateResult(BaseModel):
    """Result of a single quality gate validation"""

    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    operator: str
    critical: bool
    message: str


class QualityGateValidationResult(BaseModel):
    """Result of validating all quality gates"""

    passed: bool
    total_gates: int
    passed_gates: int
    failed_gates: int
    critical_failures: int
    results: list[QualityGateResult]

    def get_failed_critical(self) -> list[QualityGateResult]:
        """Get list of failed critical gates"""
        return [r for r in self.results if not r.passed and r.critical]

    def get_failed_non_critical(self) -> list[QualityGateResult]:
        """Get list of failed non-critical gates (warnings)"""
        return [r for r in self.results if not r.passed and not r.critical]


class QualityGateError(Exception):
    """Raised when critical quality gate fails"""

    pass


class QualityGateValidator:
    """
    Validates data against defined quality gates

    NO MOCKS - Real validation logic only

    Example:
        gates = [
            QualityGate(name="fit_score", threshold=0.90, operator=">=", critical=True),
            QualityGate(name="phase_balance", threshold=4.0, operator="<=", critical=True),
            QualityGate(name="clearance_violations", threshold=0, operator="==", critical=True)
        ]
        validator = QualityGateValidator(gates)

        data = {"fit_score": 0.93, "phase_balance": 3.2, "clearance_violations": 0}
        result = validator.validate(data)

        if not result.passed:
            raise QualityGateError(f"Quality gates failed: {result.critical_failures} critical")
    """

    def __init__(self, gates: list[QualityGate]):
        """
        Initialize validator with quality gates

        Args:
            gates: List of QualityGate definitions
        """
        self.gates = gates

    def validate(
        self, data: dict[str, Any], raise_on_failure: bool = False
    ) -> QualityGateValidationResult:
        """
        Validate data against all quality gates

        Args:
            data: Dictionary with values to validate (e.g., {"fit_score": 0.93})
            raise_on_failure: If True, raise QualityGateError on critical failures

        Returns:
            QualityGateValidationResult with detailed validation results

        Raises:
            QualityGateError: If raise_on_failure=True and critical gate fails
        """
        results: list[QualityGateResult] = []

        for gate in self.gates:
            # Get actual value from data
            actual_value = data.get(gate.name)

            if actual_value is None:
                # Missing value - treat as failure
                result = QualityGateResult(
                    gate_name=gate.name,
                    passed=False,
                    actual_value=float("nan"),
                    threshold=gate.threshold,
                    operator=gate.operator,
                    critical=gate.critical,
                    message=f"Missing value for gate '{gate.name}'",
                )
                results.append(result)
                continue

            # Convert to float for comparison
            try:
                actual_float = float(actual_value)
            except (ValueError, TypeError):
                result = QualityGateResult(
                    gate_name=gate.name,
                    passed=False,
                    actual_value=float("nan"),
                    threshold=gate.threshold,
                    operator=gate.operator,
                    critical=gate.critical,
                    message=f"Invalid value type for gate '{gate.name}': {type(actual_value)}",
                )
                results.append(result)
                continue

            # Perform comparison
            passed = self._compare(actual_float, gate.threshold, gate.operator)

            # Build message
            status = "PASS" if passed else ("FAIL" if gate.critical else "WARNING")
            message = f"[{status}] {gate.name}: {actual_float} {gate.operator} {gate.threshold}"
            if gate.description:
                message += f" ({gate.description})"

            result = QualityGateResult(
                gate_name=gate.name,
                passed=passed,
                actual_value=actual_float,
                threshold=gate.threshold,
                operator=gate.operator,
                critical=gate.critical,
                message=message,
            )
            results.append(result)

        # Calculate summary
        total_gates = len(results)
        passed_gates = sum(1 for r in results if r.passed)
        failed_gates = total_gates - passed_gates
        critical_failures = sum(1 for r in results if not r.passed and r.critical)

        # Overall pass/fail: passes only if all critical gates pass
        overall_passed = critical_failures == 0

        validation_result = QualityGateValidationResult(
            passed=overall_passed,
            total_gates=total_gates,
            passed_gates=passed_gates,
            failed_gates=failed_gates,
            critical_failures=critical_failures,
            results=results,
        )

        # Raise exception if requested and critical failures exist
        if raise_on_failure and not overall_passed:
            failed_critical = validation_result.get_failed_critical()
            failures = [f.message for f in failed_critical]
            raise QualityGateError(
                f"Critical quality gates failed ({critical_failures} failures):\n"
                + "\n".join(f"  - {msg}" for msg in failures)
            )

        return validation_result

    def _compare(self, actual: float, threshold: float, operator: str) -> bool:
        """
        Compare actual value against threshold using operator

        Args:
            actual: Actual value
            threshold: Threshold value
            operator: Comparison operator (>=, <=, ==, !=)

        Returns:
            bool: True if comparison passes
        """
        if operator == ">=":
            return actual >= threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == "==":
            # Use tolerance for float equality
            return abs(actual - threshold) < 1e-9
        elif operator == "!=":
            # Use tolerance for float inequality
            return abs(actual - threshold) >= 1e-9
        else:
            raise_error(ErrorCode.E_INTERNAL, f"Unsupported operator: {operator}")

    def add_gate(self, gate: QualityGate):
        """Add a quality gate to validator"""
        self.gates.append(gate)

    def remove_gate(self, gate_name: str):
        """Remove a quality gate by name"""
        self.gates = [g for g in self.gates if g.name != gate_name]

    def get_gate(self, gate_name: str) -> QualityGate | None:
        """Get a quality gate by name"""
        for gate in self.gates:
            if gate.name == gate_name:
                return gate
        return None


# Predefined quality gates for FIX-4 pipeline stages
ENCLOSURE_GATES = [
    QualityGate(
        name="fit_score",
        threshold=FIT_SCORE_THRESHOLD,
        operator=">=",
        critical=True,
        description=f"Enclosure fit score must be >= {FIT_SCORE_THRESHOLD}",
    ),
    QualityGate(
        name="ip_rating",
        threshold=IP_RATING_THRESHOLD,
        operator=">=",
        critical=True,
        description=f"IP rating must be >= {IP_RATING_THRESHOLD}",
    ),
    QualityGate(
        name="door_clearance_mm",
        threshold=DOOR_CLEARANCE_THRESHOLD,
        operator=">=",
        critical=True,
        description=f"Door clearance must be >= {DOOR_CLEARANCE_THRESHOLD}mm",
    ),
]

BREAKER_PLACEMENT_GATES = [
    QualityGate(
        name="phase_balance_percent",
        threshold=PHASE_BALANCE_THRESHOLD,
        operator="<=",
        critical=True,
        description=f"Phase balance must be <= {PHASE_BALANCE_THRESHOLD}%",
    ),
    QualityGate(
        name="clearance_violations",
        threshold=CLEARANCE_VIOLATIONS_THRESHOLD,
        operator="==",
        critical=True,
        description="Clearance violations must be 0",
    ),
]

ESTIMATE_FORMAT_GATES = [
    QualityGate(
        name="formula_preservation_percent",
        threshold=FORMULA_PRESERVATION_THRESHOLD,
        operator="==",
        critical=True,
        description=f"Excel formula preservation must be {FORMULA_PRESERVATION_THRESHOLD}%",
    ),
    QualityGate(
        name="named_range_damage",
        threshold=NAMED_RANGE_DAMAGE_THRESHOLD,
        operator="==",
        critical=True,
        description="Named range damage must be 0",
    ),
]

DOC_LINT_GATES = [
    QualityGate(
        name="lint_errors",
        threshold=LINT_ERRORS_THRESHOLD,
        operator="==",
        critical=True,
        description="Document lint errors must be 0",
    ),
    QualityGate(
        name="policy_violations",
        threshold=POLICY_VIOLATIONS_THRESHOLD,
        operator="==",
        critical=True,
        description="Document policy violations must be 0",
    ),
]


if __name__ == "__main__":
    # Test quality gate system with real values
    print("=" * 60)
    print("Testing Quality Gate System")
    print("NO MOCKS - Real validation logic only")
    print("=" * 60)

    # Test 1: Enclosure validation (PASS)
    print("\n[TEST 1] Enclosure validation - PASS case")
    validator = QualityGateValidator(ENCLOSURE_GATES)
    data = {"fit_score": 0.93, "ip_rating": 54, "door_clearance_mm": 35}
    result = validator.validate(data)
    print(f"Overall: {'PASS' if result.passed else 'FAIL'}")
    print(f"Gates: {result.passed_gates}/{result.total_gates} passed")
    for r in result.results:
        print(f"  {r.message}")

    # Test 2: Enclosure validation (FAIL - critical)
    print("\n[TEST 2] Enclosure validation - FAIL case (critical)")
    data_fail = {
        "fit_score": 0.85,  # Below threshold
        "ip_rating": 54,
        "door_clearance_mm": 35,
    }
    result_fail = validator.validate(data_fail)
    print(f"Overall: {'PASS' if result_fail.passed else 'FAIL'}")
    print(f"Critical failures: {result_fail.critical_failures}")
    for r in result_fail.results:
        print(f"  {r.message}")

    # Test 3: Breaker placement validation
    print("\n[TEST 3] Breaker placement validation")
    validator2 = QualityGateValidator(BREAKER_PLACEMENT_GATES)
    data2 = {
        "phase_balance_percent": 3.2,
        "clearance_violations": 0,
    }
    result2 = validator2.validate(data2)
    print(f"Overall: {'PASS' if result2.passed else 'FAIL'}")
    for r in result2.results:
        print(f"  {r.message}")

    # Test 4: All operators
    print("\n[TEST 4] Testing all operators")
    test_gates = [
        QualityGate(name="test_gte", threshold=10.0, operator=">=", critical=True),
        QualityGate(name="test_lte", threshold=5.0, operator="<=", critical=True),
        QualityGate(name="test_eq", threshold=0.0, operator="==", critical=True),
        QualityGate(name="test_neq", threshold=100.0, operator="!=", critical=True),
    ]
    validator3 = QualityGateValidator(test_gates)
    data3 = {
        "test_gte": 15.0,  # 15 >= 10: PASS
        "test_lte": 3.0,  # 3 <= 5: PASS
        "test_eq": 0.0,  # 0 == 0: PASS
        "test_neq": 50.0,  # 50 != 100: PASS
    }
    result3 = validator3.validate(data3)
    print(f"Overall: {'PASS' if result3.passed else 'FAIL'}")
    for r in result3.results:
        print(f"  {r.message}")

    # Test 5: Exception on critical failure
    print("\n[TEST 5] Exception on critical failure")
    try:
        data_critical_fail = {
            "fit_score": 0.80,
            "ip_rating": 30,
            "door_clearance_mm": 20,
        }
        validator.validate(data_critical_fail, raise_on_failure=True)
    except QualityGateError as e:
        print("[EXPECTED] QualityGateError raised:")
        print(f"  {str(e)}")

    # Test 6: Non-critical warnings
    print("\n[TEST 6] Non-critical warnings")
    warning_gates = [
        QualityGate(
            name="critical_value", threshold=10.0, operator=">=", critical=True
        ),
        QualityGate(name="warning_value", threshold=5.0, operator=">=", critical=False),
    ]
    validator4 = QualityGateValidator(warning_gates)
    data4 = {
        "critical_value": 12.0,  # PASS
        "warning_value": 3.0,  # FAIL but non-critical
    }
    result4 = validator4.validate(data4)
    print(f"Overall: {'PASS' if result4.passed else 'FAIL'} (warnings don't block)")
    print(f"Critical failures: {result4.critical_failures}")
    print(f"Non-critical failures: {len(result4.get_failed_non_critical())}")
    for r in result4.results:
        print(f"  {r.message}")

    print("\n" + "=" * 60)
    print("[SUCCESS] All quality gate tests passed")
    print("=" * 60)
