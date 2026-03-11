"""
VerbFactory - Verb 타입 안전 생성 패턴 (I-3.3)

I-3.2: ExecutionCtx 기반 Verb 생성 일원화
I-3.3: SSOT 기반 타입 안전 검증
LAW-02: SSOT 준수
LAW-04: AppError 스키마 일관성
LAW-06: REGISTRY 단일 소스
"""

import logging

from ...core.ssot.errors import ErrorCode, raise_error
from ...core.ssot.generated_verbs import VerbSpecModel, resolve_params_model
from ..context import ExecutionCtx
from .base import BaseVerb

logger = logging.getLogger(__name__)


# I-3.3: Verb REGISTRY (고정, LAW-06 단일 소스)
# 신규 Verb 추가 시 여기만 수정
# Lazy import to avoid circular dependency

_REGISTRY: dict[str, type[BaseVerb]] = {}


def _get_registry() -> dict[str, type[BaseVerb]]:
    """
    REGISTRY lazy initialization (순환 import 방지)

    I-3.3: factory.py → verbs.py → factory.py 순환참조 방지
    첫 호출 시 import 및 초기화
    """
    if not _REGISTRY:
        from ...kpew.dsl.verbs import PickEnclosureVerb, PlaceVerb

        _REGISTRY["PICK_ENCLOSURE"] = PickEnclosureVerb
        _REGISTRY["PLACE"] = PlaceVerb
        # Additional verbs can be registered here

    return _REGISTRY


# Public REGISTRY access (lazy initialization)
def get_registry() -> dict[str, type[BaseVerb]]:
    """REGISTRY 접근자 (lazy initialization)"""
    return _get_registry()


def register_verb(verb_name: str, verb_class: type[BaseVerb]) -> None:
    """
    Verb 클래스를 REGISTRY에 등록

    I-3.3 주의: REGISTRY는 고정되어 있으므로 이 함수는 사용 금지
    대신 factory.py REGISTRY dict를 직접 수정하세요 (LAW-06 단일 소스)

    Args:
        verb_name: Verb 이름 (대문자, 예: "PICK_ENCLOSURE")
        verb_class: BaseVerb 하위 클래스
    """
    logger.warning(
        f"[DEPRECATED] register_verb() is deprecated in I-3.3. "
        f"Modify factory.py REGISTRY directly instead. "
        f"Attempted: {verb_name} → {verb_class.__name__}"
    )
    # I-3.3: 동적 등록 금지 (LAW-06 위반)
    # REGISTRY는 고정 dict로 변경됨


def from_spec(spec: dict, *, ctx: ExecutionCtx) -> BaseVerb:
    """
    VerbSpec dict에서 Verb 인스턴스 생성

    I-3.2 규약:
    1. spec['verb_name'] → REGISTRY 조회
    2. spec['params'] → VerbParams (현재는 SimpleNamespace, I-3.3에서 Pydantic)
    3. ctx 주입 → BaseVerb.__init__(params, ctx=ctx)

    Args:
        spec: VerbSpec dict
            {
                "verb_name": "PICK_ENCLOSURE",
                "params": {"panel": "default", "strategy": "auto"}
            }
        ctx: ExecutionCtx (SSOT, DB, Logger, state)

    Returns:
        Verb 인스턴스 (BaseVerb)

    Raises:
        AppError:
            - ErrorCode.VERB_002: 알 수 없는 verb_name
            - ErrorCode.VERB_001: params 검증 실패 (Pydantic)
    """
    if not isinstance(spec, dict):
        raise_error(
            ErrorCode.VERB_001,
            "VerbSpec must be dict",
            hint="from_spec() expects dict with 'verb_name' and 'params'",
            meta={"spec_type": type(spec).__name__},
        )

    verb_name = spec.get("verb_name")
    if not verb_name:
        raise_error(
            ErrorCode.VERB_001,
            "Missing 'verb_name' in VerbSpec",
            hint="VerbSpec dict must have 'verb_name' key",
            meta={"spec_keys": list(spec.keys())},
        )

    # REGISTRY에서 Verb 클래스 조회 (lazy initialization)
    registry = get_registry()
    verb_class = registry.get(verb_name.upper())
    if not verb_class:
        available = list(registry.keys())
        raise_error(
            ErrorCode.VERB_002,
            f"Unknown verb: {verb_name}",
            hint=f"Available verbs: {available}",
            meta={
                "verb_name": verb_name,
                "available_verbs": available,
                "registry_size": len(registry),
            },
        )

    # I-3.3: SSOT Pydantic 검증
    # 1. VerbSpecModel 검증
    try:
        spec_model = VerbSpecModel(**spec)
    except Exception as e:
        raise_error(
            ErrorCode.VALIDATION_VERB_001,
            "VerbSpec validation failed",
            hint=f"Check VerbSpec structure: {e}",
            meta={"spec": spec, "error": str(e)},
        )

    # 2. Params 모델 조회 및 검증
    params_dict = spec_model.params
    try:
        ParamsModel = resolve_params_model(verb_name)
        params = ParamsModel(**params_dict)
    except KeyError as e:
        # resolve_params_model에서 발생 (미등록 verb_name은 REGISTRY에서 이미 검증됨)
        raise_error(
            ErrorCode.VALIDATION_VERB_001,
            f"No params model for verb: {verb_name}",
            hint="params.json에 Verb 정의 추가 필요",
            meta={"verb_name": verb_name, "error": str(e)},
        )
    except Exception as e:
        # Pydantic 검증 실패
        raise_error(
            ErrorCode.VALIDATION_VERB_001,
            f"Params validation failed for {verb_name}",
            hint=f"Check params structure: {e}",
            meta={"verb_name": verb_name, "params": params_dict, "error": str(e)},
        )

    # 3. Verb 인스턴스 생성 (ctx 주입)
    try:
        verb = verb_class(params, ctx=ctx)
        logger.info(f"Created verb: {verb_name} with params {params_dict}")
        return verb
    except Exception as e:
        logger.error(f"Failed to create verb {verb_name}: {e}")
        raise_error(
            ErrorCode.E_INTERNAL,
            f"Verb creation failed: {verb_name}",
            hint="Check Verb __init__ implementation",
            meta={"verb_name": verb_name, "params": params_dict, "exception": str(e)},
        )


def from_spec_list(specs: list[dict], *, ctx: ExecutionCtx) -> list[BaseVerb]:
    """
    VerbSpec list에서 Verb 인스턴스 list 생성

    Args:
        specs: VerbSpec dict list
        ctx: ExecutionCtx (공유)

    Returns:
        Verb 인스턴스 list
    """
    verbs = []
    for idx, spec in enumerate(specs):
        try:
            verb = from_spec(spec, ctx=ctx)
            verbs.append(verb)
        except Exception as e:
            logger.error(f"Failed to create verb at index {idx}: {e}")
            raise_error(
                ErrorCode.VERB_001,
                f"Verb creation failed at index {idx}",
                hint=f"Check VerbSpec[{idx}]: {spec}",
                meta={"index": idx, "spec": spec, "exception": str(e)},
            )

    return verbs


# I-3.2: 순환참조 방지 - lazy registration
# Verbs는 필요 시 수동 등록 (I-3.3에서 자동화)
def _register_builtin_verbs_lazy():
    """
    Built-in Verb 등록 (Lazy, 순환참조 방지)

    I-3.2: factory.py에서 verbs.py import 금지 → 순환참조
    대신 외부에서 register_verb() 호출하여 등록

    I-3.3: Future improvement - Auto-discovery pattern
    """
    pass  # No-op, external registration required
