"""
quality_gate.py 실제 호출 테스트 (P4-2 Phase I-4)

목적: 품질 게이트 검증 시스템 coverage 측정 (0% → 80%)
원칙: Zero-Mock, SSOT 정책 사용, 실제 게이트 검증
"""

import pytest

from kis_estimator_core.infra.quality_gate import (
    QualityGate,
    QualityGateValidator,
    QualityGateError,
    ENCLOSURE_GATES,
    BREAKER_PLACEMENT_GATES,
    ESTIMATE_FORMAT_GATES,
    DOC_LINT_GATES,
)


# ============================================================
# Fixture: QualityGateValidator Instance
# ============================================================
@pytest.fixture
def validator():
    """QualityGateValidator 인스턴스"""
    gates = [
        QualityGate(
            name="fit_score",
            threshold=0.90,
            operator=">=",
            critical=True,
            description="Enclosure fit score",
        ),
        QualityGate(
            name="phase_balance",
            threshold=4.0,
            operator="<=",
            critical=True,
            description="Phase balance percentage",
        ),
        QualityGate(
            name="clearance_violations",
            threshold=0.0,
            operator="==",
            critical=True,
            description="Clearance violations count",
        ),
        QualityGate(
            name="formula_preservation",
            threshold=100.0,
            operator="!=",
            critical=False,
            description="Formula preservation rate",
        ),
    ]
    return QualityGateValidator(gates)


# ============================================================
# Test: QualityGate Model Creation
# ============================================================
def test_quality_gate_model_creation():
    """QualityGate 모델 생성"""
    # 실제 호출
    gate = QualityGate(
        name="test_gate",
        threshold=0.90,
        operator=">=",
        critical=True,
        description="Test gate",
    )

    # 검증
    assert gate.name == "test_gate"
    assert gate.threshold == 0.90
    assert gate.operator == ">="
    assert gate.critical is True
    assert gate.description == "Test gate"


def test_quality_gate_optional_description():
    """QualityGate 설명 없이 생성"""
    # 실제 호출
    gate = QualityGate(name="test_gate", threshold=1.0, operator="==", critical=False)

    # 검증
    assert gate.description is None


# ============================================================
# Test: QualityGateValidator.validate() - Success Cases
# ============================================================
def test_validate_all_pass(validator):
    """모든 게이트 통과"""
    data = {
        "fit_score": 0.95,
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증
    assert result.passed is True
    assert result.failed_gates == 0
    assert result.critical_failures == 0


def test_validate_partial_pass_non_critical(validator):
    """비critical 게이트만 실패 (WARNING 처리)"""
    data = {
        "fit_score": 0.95,
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 100.0,  # != 100 경고 (비critical)
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증: 비critical 실패는 경고로 처리, passed=True
    assert result.passed is True  # 경고는 통과로 처리
    assert result.failed_gates == 1
    assert result.critical_failures == 0
    # Check results list
    failed_result = [r for r in result.results if not r.passed][0]
    assert failed_result.gate_name == "formula_preservation"


# ============================================================
# Test: QualityGateValidator.validate() - Failure Cases
# ============================================================
def test_validate_critical_failure(validator):
    """Critical 게이트 실패"""
    data = {
        "fit_score": 0.85,  # < 0.90 실패 (critical)
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증
    assert result.passed is False
    assert result.failed_gates == 1
    assert result.critical_failures == 1
    # Check results list
    failed_result = [r for r in result.results if not r.passed][0]
    assert failed_result.gate_name == "fit_score"
    assert failed_result.critical is True


def test_validate_multiple_failures(validator):
    """여러 게이트 실패"""
    data = {
        "fit_score": 0.85,  # 실패
        "phase_balance": 5.0,  # 실패
        "clearance_violations": 2.0,  # 실패
        "formula_preservation": 100.0,  # 실패
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증
    assert result.passed is False
    assert result.failed_gates == 4
    assert result.critical_failures == 3


# ============================================================
# Test: QualityGateValidator.validate() - Missing Fields
# ============================================================
def test_validate_missing_required_field(validator):
    """필수 필드 누락"""
    data = {
        "fit_score": 0.95,
        # phase_balance 누락
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증: 누락 필드는 실패로 처리
    assert result.passed is False
    assert result.failed_gates >= 1
    # phase_balance 누락 실패 확인
    assert any(r.gate_name == "phase_balance" and not r.passed for r in result.results)


def test_validate_invalid_value_type(validator):
    """잘못된 값 타입"""
    data = {
        "fit_score": "not_a_number",  # 문자열
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    result = validator.validate(data)

    # 검증: 파싱 실패는 실패로 처리
    assert result.passed is False
    assert any(r.gate_name == "fit_score" and not r.passed for r in result.results)


# ============================================================
# Test: QualityGateValidator.validate() - raise_on_failure
# ============================================================
def test_validate_raise_on_failure_true(validator):
    """raise_on_failure=True → QualityGateError 발생"""
    data = {
        "fit_score": 0.85,  # Critical 실패
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    with pytest.raises(QualityGateError, match="Critical quality gates failed"):
        validator.validate(data, raise_on_failure=True)


def test_validate_raise_on_failure_false(validator):
    """raise_on_failure=False → 결과 객체 반환"""
    data = {
        "fit_score": 0.85,  # Critical 실패
        "phase_balance": 3.5,
        "clearance_violations": 0.0,
        "formula_preservation": 99.0,
    }

    # 실제 호출
    result = validator.validate(data, raise_on_failure=False)

    # 검증: 예외 없이 결과 반환
    assert result.passed is False


# ============================================================
# Test: QualityGateValidator._compare() - All Operators
# ============================================================
def test_compare_greater_equal(validator):
    """_compare() >= 연산자"""
    # 실제 호출
    assert validator._compare(0.95, 0.90, ">=") is True
    assert validator._compare(0.90, 0.90, ">=") is True
    assert validator._compare(0.85, 0.90, ">=") is False


def test_compare_less_equal(validator):
    """_compare() <= 연산자"""
    # 실제 호출
    assert validator._compare(3.5, 4.0, "<=") is True
    assert validator._compare(4.0, 4.0, "<=") is True
    assert validator._compare(5.0, 4.0, "<=") is False


def test_compare_equal_exact(validator):
    """_compare() == 연산자 (정확히 같음)"""
    # 실제 호출
    assert validator._compare(0.0, 0.0, "==") is True
    assert validator._compare(1.0, 1.0, "==") is True
    assert validator._compare(1.0, 2.0, "==") is False


def test_compare_equal_float_tolerance(validator):
    """_compare() == 연산자 (float 허용 오차)"""
    # 실제 호출: 1e-9 이내는 같다고 판단
    assert validator._compare(1.0, 1.0 + 1e-10, "==") is True
    assert validator._compare(1.0, 1.0 + 1e-8, "==") is False


def test_compare_not_equal(validator):
    """_compare() != 연산자"""
    # 실제 호출
    assert validator._compare(99.0, 100.0, "!=") is True
    assert validator._compare(100.0, 100.0, "!=") is False


def test_compare_not_equal_float_tolerance(validator):
    """_compare() != 연산자 (float 허용 오차)"""
    # 실제 호출: 1e-9 이내는 같다고 판단 → != False
    assert validator._compare(100.0, 100.0 + 1e-10, "!=") is False
    assert validator._compare(100.0, 100.0 + 1e-8, "!=") is True


# ============================================================
# Test: Predefined Quality Gates
# ============================================================
def test_enclosure_gates_constants():
    """ENCLOSURE_GATES 상수 확인"""
    # 실제 호출
    assert isinstance(ENCLOSURE_GATES, list)
    assert len(ENCLOSURE_GATES) >= 3  # fit_score, ip_rating, door_clearance_mm 등

    # fit_score 게이트 존재 확인
    fit_score_gate = next((g for g in ENCLOSURE_GATES if g.name == "fit_score"), None)
    assert fit_score_gate is not None
    assert fit_score_gate.threshold == 0.90
    assert fit_score_gate.operator == ">="


def test_breaker_placement_gates_constants():
    """BREAKER_PLACEMENT_GATES 상수 확인"""
    # 실제 호출
    assert isinstance(BREAKER_PLACEMENT_GATES, list)
    assert (
        len(BREAKER_PLACEMENT_GATES) >= 2
    )  # phase_balance_percent, clearance_violations 등

    # phase_balance_percent 게이트 존재 확인
    phase_gate = next(
        (g for g in BREAKER_PLACEMENT_GATES if g.name == "phase_balance_percent"), None
    )
    assert phase_gate is not None
    assert phase_gate.threshold == 4.0
    assert phase_gate.operator == "<="


def test_estimate_format_gates_constants():
    """ESTIMATE_FORMAT_GATES 상수 확인"""
    # 실제 호출
    assert isinstance(ESTIMATE_FORMAT_GATES, list)
    assert (
        len(ESTIMATE_FORMAT_GATES) >= 2
    )  # formula_preservation_percent, named_range_damage 등

    # formula_preservation_percent 게이트 존재 확인
    formula_gate = next(
        (g for g in ESTIMATE_FORMAT_GATES if g.name == "formula_preservation_percent"),
        None,
    )
    assert formula_gate is not None
    assert formula_gate.threshold == 100.0
    assert formula_gate.operator == "=="


def test_doc_lint_gates_constants():
    """DOC_LINT_GATES 상수 확인"""
    # 실제 호출
    assert isinstance(DOC_LINT_GATES, list)
    assert len(DOC_LINT_GATES) >= 1  # lint_errors 등

    # lint_errors 게이트 존재 확인
    lint_gate = next((g for g in DOC_LINT_GATES if g.name == "lint_errors"), None)
    assert lint_gate is not None
    assert lint_gate.threshold == 0.0
    assert lint_gate.operator == "=="


# ============================================================
# Test: Integration with Real Data
# ============================================================
def test_integration_enclosure_validation():
    """실제 Enclosure 데이터 검증 통합 테스트"""
    validator = QualityGateValidator(ENCLOSURE_GATES)

    # 성공 케이스
    success_data = {
        "fit_score": 0.95,
        "ip_rating": 54,
        "door_clearance_mm": 35.0,
    }

    result = validator.validate(success_data)
    assert result.passed is True

    # 실패 케이스
    failure_data = {
        "fit_score": 0.85,  # < 0.90 실패
        "ip_rating": 40,  # < 44 실패
        "door_clearance_mm": 25.0,  # < 30 실패
    }

    result = validator.validate(failure_data)
    assert result.passed is False
    assert result.critical_failures >= 1


def test_integration_breaker_placement_validation():
    """실제 Breaker Placement 데이터 검증 통합 테스트"""
    validator = QualityGateValidator(BREAKER_PLACEMENT_GATES)

    # 성공 케이스
    success_data = {
        "phase_balance_percent": 3.5,
        "clearance_violations": 0.0,
    }

    result = validator.validate(success_data)
    assert result.passed is True

    # 실패 케이스
    failure_data = {
        "phase_balance_percent": 5.0,  # > 4.0 실패
        "clearance_violations": 2.0,  # != 0 실패
    }

    result = validator.validate(failure_data)
    assert result.passed is False
    assert result.critical_failures >= 1


def test_integration_estimate_format_validation():
    """실제 Estimate Format 데이터 검증 통합 테스트"""
    validator = QualityGateValidator(ESTIMATE_FORMAT_GATES)

    # 성공 케이스
    success_data = {
        "formula_preservation_percent": 100.0,
        "named_range_damage": 0.0,
    }

    result = validator.validate(success_data)
    assert result.passed is True

    # 실패 케이스
    failure_data = {
        "formula_preservation_percent": 95.0,  # != 100 실패
        "named_range_damage": 2.0,  # != 0 실패
    }

    result = validator.validate(failure_data)
    assert result.passed is False
