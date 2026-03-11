r"""
SSOT Generated Verb Models (I-3.3)

WARNING: This file is AUTO-GENERATED.
Do NOT edit manually. Run scripts/generate_verb_models.py instead.

Generated: 2025-10-15T13:51:11.450544Z
Source: src\kis_estimator_core\core\ssot\verbs\params.json

LAW-02: SSOT Single Source - No duplication
LAW-03: No Hardcoding - Import from here only
"""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================
# VerbParamsBase - 모든 Verb Params의 Base
# ============================================================


class VerbParamsBase(BaseModel):
    """Base class for all Verb parameters"""

    pass


# ============================================================
# VerbSpecModel - VerbSpec 최상위 모델
# ============================================================


class VerbSpecModel(BaseModel):
    """VerbSpec 최상위 모델 (SSOT)"""

    verb_name: str = Field(..., description="Verb 이름 (대문자)")
    params: dict[str, Any] = Field(..., description="Verb별 파라미터 객체")
    version: str = Field("1.0.0", description="Verb spec 버전")


# ============================================================
# Verb Params Models (Auto-Generated)
# ============================================================


class PickenclosureParams(VerbParamsBase):
    """
    외함 선택 Verb 파라미터
    """

    main_breaker: dict[str, Any] = Field(
        ..., description="메인 차단기 사양 (poles, current, frame)"
    )
    branch_breakers: list[Any] = Field(..., description="분기 차단기 목록")
    enclosure_type: str = Field(..., description="외함 타입 (옥내노출, 옥외노출 등)")
    material: str = Field(..., description="재질 (STEEL, SUS201 등)")
    thickness: str = Field(..., description="두께 (1.6T, 1.2T 등)")
    accessories: list[Any] = Field(default_factory=list, description="부속자재 목록")
    panel: str = Field("default", description="패널 이름")
    strategy: str = Field("auto", description="선택 전략 (auto, manual, optimal)")


class PlaceParams(VerbParamsBase):
    """
    브레이커 배치 Verb 파라미터
    """

    breakers: list[Any] = Field(
        ..., description="배치할 브레이커 ID 목록 (예: ['MAIN', 'BR1', 'BR2'])"
    )
    panel: str = Field("default", description="패널 이름")
    strategy: str = Field(
        "compact", description="배치 전략 (compact, balanced, minimize_heat)"
    )
    algo: str = Field("heuristic", description="알고리즘 선택 (heuristic, ortools)")
    seed: int = Field(42, description="랜덤 시드 (재현성)")


# ============================================================
# resolve_params_model - Verb name → Params Model 매핑
# ============================================================


def resolve_params_model(verb_name: str) -> type[VerbParamsBase]:
    """
    Verb name에서 해당 Params 모델 클래스 반환

    Args:
        verb_name: Verb 이름 (대문자, 예: "PICK_ENCLOSURE")

    Returns:
        VerbParamsBase 서브클래스

    Raises:
        KeyError: 알 수 없는 verb_name
    """
    PARAMS_MODEL_REGISTRY: dict[str, type[VerbParamsBase]] = {
        "PICK_ENCLOSURE": PickenclosureParams,
        "PLACE": PlaceParams,
    }

    if verb_name.upper() not in PARAMS_MODEL_REGISTRY:
        raise KeyError(f"Unknown verb_name: {verb_name}")

    return PARAMS_MODEL_REGISTRY[verb_name.upper()]
