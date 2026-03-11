"""
Context Normalizer - BOM 진입 전 타입 정규화

I-3.2b: dict → SSOT DTO 일괄 변환 (단일 진입점)

절대 원칙:
- 테스트용 기본값 주입 금지
- 더미 변환 금지
- 실패 시 AppError 발생
"""

import logging
from typing import Any

from kis_estimator_core.core.ssot.errors import raise_error
from kis_estimator_core.core.ssot.generated_models import (
    BreakerInput,
    EnclosureDimensionsInput,
    EnclosureInput,
    PlacementInput,
)
from kis_estimator_core.errors.error_codes import ErrorCode

logger = logging.getLogger(__name__)


def normalize_ctx_state(state: dict[str, Any]) -> None:
    """
    ExecutionCtx.state를 SSOT DTO로 정규화 (in-place)

    I-3.2b: BOM 진입 직전 단일 진입점

    Args:
        state: ExecutionCtx.state (dict)

    Raises:
        AppError: 필수 필드 누락, 타입 불일치

    Side Effects:
        state['breakers']: List[dict | BreakerInput] → List[BreakerInput]
        state['enclosure']: dict | EnclosureInput → EnclosureInput
        state['placements']: List[dict | PlacementInput] → List[PlacementInput]
    """
    logger.info("[I-3.2b] Starting context normalization...")

    # 1. Normalize breakers
    if "breakers" in state:
        breakers = state["breakers"]
        if isinstance(breakers, list):
            normalized_breakers = []
            for idx, b in enumerate(breakers):
                if b is None:
                    continue  # Skip None entries

                # Already DTO? Skip
                if isinstance(b, BreakerInput):
                    normalized_breakers.append(b)
                    continue

                # dict → BreakerInput
                if isinstance(b, dict):
                    try:
                        # I-3.2b: 필수 필드 검증
                        required_fields = ["id", "poles"]
                        missing = [f for f in required_fields if f not in b]
                        if missing:
                            raise_error(
                                ErrorCode.VALIDATION_001,
                                f"Breaker missing required fields: {missing}",
                                hint=f"Breaker at index {idx} requires {required_fields}",
                                meta={"breaker_index": idx, "breaker_data": b},
                            )

                        # 타입 변환
                        breaker_dto = BreakerInput.parse_obj(b)
                        normalized_breakers.append(breaker_dto)
                        logger.debug(
                            f"[I-3.2b] Normalized breaker {idx}: {breaker_dto.id}"
                        )

                    except ValueError as e:
                        raise_error(
                            ErrorCode.VALIDATION_001,
                            f"Invalid breaker data at index {idx}: {str(e)}",
                            hint="Check breaker fields (poles, frame_af, current_a)",
                            meta={
                                "breaker_index": idx,
                                "breaker_data": b,
                                "error": str(e),
                            },
                        )
                else:
                    # 알 수 없는 타입
                    logger.warning(
                        f"[I-3.2b] Unknown breaker type at index {idx}: {type(b)}"
                    )
                    continue

            state["breakers"] = normalized_breakers
            logger.info(f"[I-3.2b] Normalized {len(normalized_breakers)} breakers")

    # 2. Normalize enclosure
    if "enclosure" in state:
        enc = state["enclosure"]
        if enc is None:
            pass  # Allow None
        elif isinstance(enc, EnclosureInput):
            pass  # Already DTO
        elif isinstance(enc, dict):
            try:
                # I-3.2b: dimensions 필드 정규화
                if "dimensions" in enc and isinstance(enc["dimensions"], dict):
                    enc["dimensions"] = EnclosureDimensionsInput.parse_obj(
                        enc["dimensions"]
                    )

                enclosure_dto = EnclosureInput.parse_obj(enc)
                state["enclosure"] = enclosure_dto
                logger.info(
                    f"[I-3.2b] Normalized enclosure: {enclosure_dto.id or 'no-id'}"
                )

            except ValueError as e:
                raise_error(
                    ErrorCode.VALIDATION_001,
                    f"Invalid enclosure data: {str(e)}",
                    hint="Check enclosure fields (dimensions, enclosure_type)",
                    meta={"enclosure_data": enc, "error": str(e)},
                )
        else:
            logger.warning(f"[I-3.2b] Unknown enclosure type: {type(enc)}")

    # 3. Normalize placements (optional)
    if "placements" in state:
        placements = state["placements"]
        if isinstance(placements, list):
            normalized_placements = []
            for idx, p in enumerate(placements):
                if p is None:
                    continue

                # Already DTO? Skip
                if isinstance(p, PlacementInput):
                    normalized_placements.append(p)
                    continue

                # dict → PlacementInput
                if isinstance(p, dict):
                    try:
                        placement_dto = PlacementInput.parse_obj(p)
                        normalized_placements.append(placement_dto)
                        logger.debug(
                            f"[I-3.2b] Normalized placement {idx}: {placement_dto.breaker_id}"
                        )

                    except ValueError as e:
                        logger.warning(
                            f"[I-3.2b] Invalid placement at index {idx}: {str(e)}"
                        )
                        continue
                else:
                    logger.warning(
                        f"[I-3.2b] Unknown placement type at index {idx}: {type(p)}"
                    )
                    continue

            state["placements"] = normalized_placements
            logger.info(f"[I-3.2b] Normalized {len(normalized_placements)} placements")

    logger.info("[I-3.2b] Context normalization complete")


def validate_normalized_state(state: dict[str, Any]) -> None:
    """
    정규화 후 검증 (선택적 사용)

    I-3.2b: 정규화 성공 확인

    Args:
        state: ExecutionCtx.state (dict)

    Raises:
        AppError: 정규화 실패 (dict 타입 잔존)
    """
    # breakers 검증
    if "breakers" in state:
        breakers = state["breakers"]
        if isinstance(breakers, list):
            for idx, b in enumerate(breakers):
                if isinstance(b, dict):
                    raise_error(
                        ErrorCode.VALIDATION_001,
                        f"Breaker at index {idx} still dict after normalization",
                        hint="normalize_ctx_state() failed to convert dict to BreakerInput",
                        meta={"breaker_index": idx},
                    )

    # enclosure 검증
    if "enclosure" in state:
        enc = state["enclosure"]
        if isinstance(enc, dict):
            raise_error(
                ErrorCode.VALIDATION_001,
                "Enclosure still dict after normalization",
                hint="normalize_ctx_state() failed to convert dict to EnclosureInput",
                meta={"enclosure_data": enc},
            )

    logger.info("[I-3.2b] Validation passed: all state is DTO")
