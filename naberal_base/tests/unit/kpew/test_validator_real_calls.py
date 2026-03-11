"""
validator.py 실제 호출 테스트 (P4-2 Real-Call 전환)

목적: coverage 측정을 위한 실제 함수 호출
원칙: Zero-Mock, SSOT 정책 사용, EstimatorError 스키마 준수
"""

import pytest

from kis_estimator_core.kpew.gates.validator import GateValidator
from kis_estimator_core.errors.exceptions import EstimatorError


# ============================================================
# Fixture: GateValidator Instance
# ============================================================
@pytest.fixture
def gate_validator():
    """GateValidator 인스턴스 생성"""
    return GateValidator()


# ============================================================
# Test: validate_balance (상평형 검증)
# ============================================================
def test_validate_balance_success(gate_validator):
    """상평형 검증 성공 (imbalance ≤ limit)"""
    # 정상 상평형 (차이 ≤ 4%)
    phase_loads = {"L1": 100.0, "L2": 98.0, "L3": 102.0}

    # 실제 호출
    is_valid, errors = gate_validator.validate_balance(phase_loads)

    # 검증
    assert is_valid is True
    assert len(errors) == 0


def test_validate_balance_failure(gate_validator):
    """상평형 검증 실패 (imbalance > limit)"""
    # 불균형 상태 (L1=100, L2=50, L3=100 → imbalance > 4%)
    phase_loads = {"L1": 100.0, "L2": 50.0, "L3": 100.0}

    # 실제 호출
    is_valid, errors = gate_validator.validate_balance(phase_loads)

    # 검증: 실패
    assert is_valid is False
    assert len(errors) > 0
    assert isinstance(errors[0], EstimatorError)
    assert errors[0].error_code.code == "LAY-001"


def test_validate_balance_with_ia_ib_ic_keys(gate_validator):
    """상평형 검증 (Ia/Ib/Ic 키 정규화)"""
    # Ia/Ib/Ic 키 사용
    phase_loads = {"Ia": 100.0, "Ib": 98.0, "Ic": 102.0}

    # 실제 호출
    is_valid, errors = gate_validator.validate_balance(phase_loads)

    # 검증: 정규화 성공
    assert is_valid is True
    assert len(errors) == 0


def test_validate_balance_zero_load(gate_validator):
    """상평형 검증 (부하 없음 = 0)"""
    # 부하 없음
    phase_loads = {"L1": 0.0, "L2": 0.0, "L3": 0.0}

    # 실제 호출
    is_valid, errors = gate_validator.validate_balance(phase_loads)

    # 검증: 부하 없음은 성공
    assert is_valid is True
    assert len(errors) == 0


# ============================================================
# Test: validate_fit_score (fit_score 검증)
# ============================================================
def test_validate_fit_score_success(gate_validator):
    """fit_score 검증 성공 (≥ min_required)"""
    # fit_score ≥ 0.90 (정책 기준)
    fit_score = 0.95

    # 실제 호출
    is_valid, errors = gate_validator.validate_fit_score(fit_score)

    # 검증
    assert is_valid is True
    assert len(errors) == 0


def test_validate_fit_score_failure(gate_validator):
    """fit_score 검증 실패 (< min_required)"""
    # fit_score < 0.90 (정책 미달)
    fit_score = 0.85

    # 실제 호출
    is_valid, errors = gate_validator.validate_fit_score(fit_score)

    # 검증: 실패
    assert is_valid is False
    assert len(errors) > 0
    assert isinstance(errors[0], EstimatorError)
    assert errors[0].error_code.code == "ENC-001"


def test_validate_fit_score_exact_min(gate_validator):
    """fit_score 검증 (정확히 min_required)"""
    # fit_score = 0.90 (경계값)
    fit_score = 0.90

    # 실제 호출
    is_valid, errors = gate_validator.validate_fit_score(fit_score)

    # 검증: 성공 (≥ 조건)
    assert is_valid is True
    assert len(errors) == 0


# ============================================================
# Test: validate_violations (위반사항 검증)
# ============================================================
def test_validate_violations_success(gate_validator):
    """위반사항 검증 성공 (violations = 0)"""
    # 위반사항 없음
    violations = []

    # 실제 호출
    is_valid, errors = gate_validator.validate_violations(violations)

    # 검증
    assert is_valid is True
    assert len(errors) == 0


def test_validate_violations_failure(gate_validator):
    """위반사항 검증 실패 (violations > 0)"""
    # 위반사항 존재
    violations = [
        "간섭 위반: 브레이커 간 간격 부족 (10mm < 30mm)",
        "열 밀도 위반: 400AF 브레이커 과밀 배치",
    ]

    # 실제 호출
    is_valid, errors = gate_validator.validate_violations(violations)

    # 검증: 실패
    assert is_valid is False
    assert len(errors) == 2
    assert all(isinstance(err, EstimatorError) for err in errors)
    assert all(err.error_code.code == "LAY-002" for err in errors)


def test_validate_violations_single_violation(gate_validator):
    """위반사항 검증 (단일 위반)"""
    # 위반사항 1개
    violations = ["간섭 위반: 브레이커 A와 B 간 간격 부족"]

    # 실제 호출
    is_valid, errors = gate_validator.validate_violations(violations)

    # 검증: 실패 (1개 위반)
    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].error_code.code == "LAY-002"


# ============================================================
# Test: GateValidator Initialization
# ============================================================
def test_gate_validator_init():
    """GateValidator 초기화 및 정책 로딩"""
    # 실제 호출
    validator = GateValidator()

    # 검증: 정책 로딩 성공
    assert validator.policy is not None
    assert "rules" in validator.policy
    assert "balance_limit" in validator.policy["rules"]
    assert "fit_score_min" in validator.policy["rules"]
    assert "forbid_violations" in validator.policy["rules"]


def test_gate_validator_policy_values(gate_validator):
    """GateValidator 정책 값 검증"""
    # 정책 값 확인
    assert (
        gate_validator.policy["rules"]["balance_limit"] == 0.03
    )  # 3% (estimation.yaml 실제 값)
    assert gate_validator.policy["rules"]["fit_score_min"] == 0.90  # 90%
    assert gate_validator.policy["rules"]["forbid_violations"] is True


def test_validate_violations_with_forbid_false(gate_validator, monkeypatch):
    """위반사항 검증 - forbid_violations=False일 때 (위반 허용)"""
    # Policy를 forbid_violations=False로 변경
    monkeypatch.setitem(gate_validator.policy["rules"], "forbid_violations", False)

    # 위반 사항 있음
    violations = ["clearance_violation_1", "thermal_violation_2"]

    # 실제 호출
    is_valid, errors = gate_validator.validate_violations(violations)

    # 검증: forbid_violations=False → 위반 있어도 성공 (line 86-95 branch)
    assert is_valid is True
    assert len(errors) == 0
