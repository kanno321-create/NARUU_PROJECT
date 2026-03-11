"""
KIS Branch/Bus Rules SSOT Adapter

LAW-02: JSON SSOT 단일출처 (Python 지식팩 금지)
이 모듈은 kis_branch_bus_rules.v1.json에서 SSOT 지식을 로드하고
engine/breaker_placer.py에서 사용할 수 있도록 검증된 인터페이스를 제공합니다.

모든 상수/타입/맵퍼는 core/ssot/** 에서만 import합니다 (하드코딩 금지).
"""

import json
from pathlib import Path
from typing import Any

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# SSOT 지식파일 경로 (프로젝트 루트 기준)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_JSON_SSOT_PATH = (
    _PROJECT_ROOT / "KIS" / "Knowledge" / "packs" / "kis_branch_bus_rules.v1.json"
)


def load_branch_bus_rules() -> dict[str, Any]:
    """
    KIS Branch/Bus Rules를 JSON에서 로드하고 스키마 검증 수행

    Returns:
        dict: 검증된 Branch/Bus Rules 딕셔너리

    Raises:
        FileNotFoundError: JSON 파일 로드 실패
        ValueError: 스키마 검증 실패
    """
    if not _JSON_SSOT_PATH.exists():
        raise FileNotFoundError(
            f"JSON SSOT file not found: {_JSON_SSOT_PATH}\n"
            f"LAW-02: Python 지식팩(.py) 사용 금지. JSON만 허용됩니다."
        )

    with open(_JSON_SSOT_PATH, encoding="utf-8") as f:
        rules = json.load(f)

    # 스키마 검증 (필수 필드 확인)
    _validate_schema(rules)

    return rules


def _validate_schema(rules: dict[str, Any]) -> None:
    """
    Branch/Bus Rules 스키마 검증

    필수 필드:
    - meta.version
    - panel.layout
    - phases.order
    - policy.2P/3P/4P
    - validation_guards
    """
    required_fields = [
        ("meta", "version"),
        ("panel", "layout"),
        ("phases", "order"),
        ("policy", "2P"),
        ("policy", "3P"),
        ("policy", "4P"),
        ("validation_guards", "phase_alignment"),
        ("validation_guards", "bolt_integrity"),
        ("validation_guards", "n_no_cross_link"),
        ("validation_guards", "outputs_outer_only"),
        ("validation_guards", "center_feed_direction"),
        ("validation_guards", "row_aware_n_phase"),
    ]

    for *path, field in required_fields:
        current = rules
        for key in path:
            if key not in current:
                raise_error(
                    ErrorCode.E_BRANCH_RULE,
                    f"Missing required field: {'.'.join(path)}.{field}",
                )
            current = current[key]
        if field not in current:
            raise_error(
                ErrorCode.E_BRANCH_RULE,
                f"Missing required field: {'.'.join(path)}.{field}",
            )

    # 값 검증
    if rules["panel"]["layout"] != "center_feed_single_branch_bus":
        raise_error(
            ErrorCode.E_BRANCH_RULE,
            f"Invalid layout: {rules['panel']['layout']} "
            f"(expected 'center_feed_single_branch_bus')",
        )

    if set(rules["phases"]["order"]) != {"R", "S", "T", "N"}:
        raise_error(
            ErrorCode.E_BRANCH_RULE,
            f"Invalid phases.order: {rules['phases']['order']} "
            f"(expected ['R','S','T','N'])",
        )


def get_rule(name: str) -> Any:
    """
    Branch/Bus Rules에서 특정 규칙을 조회

    Args:
        name: 규칙 이름 (점 표기법, 예: "policy.4P.n_phase.row_rules.shared_if_pair")

    Returns:
        Any: 규칙 값

    Raises:
        KeyError: 규칙이 존재하지 않음
        ValueError: 잘못된 규칙 이름 형식
    """
    rules = load_branch_bus_rules()
    keys = name.split(".")

    current = rules
    for key in keys:
        if not isinstance(current, dict):
            raise_error(
                ErrorCode.E_BRANCH_RULE,
                f"Invalid rule path: {name} (not a dict at '{key}')",
            )
        if key not in current:
            raise_error(
                ErrorCode.E_BRANCH_RULE, f"Rule not found: {name} (missing key '{key}')"
            )
        current = current[key]

    return current


def get_pole_policy(poles: int) -> dict[str, Any]:
    """
    극수별 정책 조회

    Args:
        poles: 극수 (2, 3, 4)

    Returns:
        dict: 극수별 정책 (shared_branch_bus, bolt_to_main, io_rules 등)

    Raises:
        ValueError: 지원하지 않는 극수
    """
    if poles not in [2, 3, 4]:
        raise_error(
            ErrorCode.E_BRANCH_RULE, f"Unsupported poles: {poles} (expected 2, 3, or 4)"
        )

    rules = load_branch_bus_rules()
    pole_key = f"{poles}P"

    if pole_key not in rules["policy"]:
        raise_error(ErrorCode.E_BRANCH_RULE, f"Policy not found for {pole_key}")

    return rules["policy"][pole_key]


def get_validation_guards() -> dict[str, Any]:
    """
    모든 검증 가드 조회

    Returns:
        dict: 검증 가드 딕셔너리
    """
    rules = load_branch_bus_rules()
    return rules["validation_guards"]


def is_n_phase_rightmost() -> bool:
    """N상이 최우측에 위치하는지 확인"""
    rules = load_branch_bus_rules()
    return rules["phases"].get("n_phase_rightmost", True)


def get_n_phase_row_rules() -> dict[str, bool]:
    """
    4P N상 row-aware 규칙 조회

    Returns:
        dict: {
            "shared_if_pair": bool,
            "split_if_single": bool,
            "no_cross_link": bool,
            "n_phase_rightmost": bool
        }
    """
    rules = load_branch_bus_rules()
    return rules["policy"]["4P"]["n_phase"]["row_rules"]


__all__ = [
    "load_branch_bus_rules",
    "get_rule",
    "get_pole_policy",
    "get_validation_guards",
    "is_n_phase_rightmost",
    "get_n_phase_row_rules",
]
