"""
Enclosure Input Validator

입력 검증 규칙:
1. Breaker AF-Pole 조합 검증 (MANDATORY)
2. UOM 정규화 (mm/cm/inch → mm 기준)
3. 경계값 검증
4. 명확한 오류 코드 및 힌트 제공

절대 원칙:
- NO 목업/더미 데이터
- Contract-First: OpenAPI 스키마와 정확히 일치
- Evidence-Gated: 모든 검증 실패는 명확한 오류 코드 반환
"""

import re
from typing import Any

from ..core.ssot.constants import (
    PHASE_1_NAME,
    UOM_CM_TO_MM,
    UOM_INCH_TO_MM,
    UOM_PATTERN_CM,
    UOM_PATTERN_INCH,
    UOM_PATTERN_MM,
    VALID_AF_POLE_COMBINATIONS,
    VALID_AF_VALUES,
)
from ..errors import ENC_003, ValidationError


def validate_breaker_spec(breaker: dict[str, Any]) -> None:
    """
    차단기 스펙 검증 (AF-Pole 조합 MANDATORY)

    Args:
        breaker: 차단기 스펙 딕셔너리
            - frame_af (int): 프레임 크기
            - poles (int): 극수 (2, 3, 4)
            - model (str): 모델명

    Raises:
        ValidationError: ENC-003 - 불가능한 AF-Pole 조합
    """
    frame_af = breaker.get("frame_af")
    poles = breaker.get("poles")
    model = breaker.get("model", "UNKNOWN")

    # 1. AF 값 검증
    if frame_af not in VALID_AF_VALUES:
        raise ValidationError(
            error_code=ENC_003,
            field="breaker.frame_af",
            value=frame_af,
            expected=f"유효한 AF 값: {VALID_AF_VALUES}",
            phase=PHASE_1_NAME,
        )

    # 2. AF-Pole 조합 검증 (CRITICAL)
    valid_poles = VALID_AF_POLE_COMBINATIONS.get(frame_af, [])
    if poles not in valid_poles:
        raise ValidationError(
            error_code=ENC_003,
            field=f"breaker.poles (model={model})",
            value=f"{poles}P @ {frame_af}AF",
            expected=f"허용 극수: {valid_poles}P",
            phase=PHASE_1_NAME,
        )


def normalize_dimension_uom(value: Any, field_name: str) -> float:
    """
    치수 단위 정규화 (mm/cm/inch → mm 기준)

    Args:
        value: 입력 값 (숫자 또는 문자열)
        field_name: 필드명 (오류 메시지용)

    Returns:
        float: mm 단위로 변환된 값

    Raises:
        ValidationError: ENC-003 - 단위 파싱 실패
    """
    # 숫자 그대로인 경우 (기본: mm)
    if isinstance(value, (int, float)):
        return float(value)

    # 문자열 파싱
    if isinstance(value, str):
        # mm 패턴
        match = re.match(UOM_PATTERN_MM, value)
        if match:
            return float(match.group(1))

        # cm 패턴
        match = re.match(UOM_PATTERN_CM, value)
        if match:
            return float(match.group(1)) * UOM_CM_TO_MM

        # inch 패턴
        match = re.match(UOM_PATTERN_INCH, value)
        if match:
            return float(match.group(1)) * UOM_INCH_TO_MM

    # 파싱 실패
    raise ValidationError(
        error_code=ENC_003,
        field=field_name,
        value=value,
        expected="숫자 또는 '100mm', '10cm', '5inch' 형식",
        phase=PHASE_1_NAME,
    )


def validate_dimension_range(
    value: float, field_name: str, min_val: float, max_val: float
) -> None:
    """
    치수 경계값 검증

    Args:
        value: 검증할 값 (mm 단위)
        field_name: 필드명
        min_val: 최소값
        max_val: 최대값

    Raises:
        ValidationError: ENC-003 - 범위 초과
    """
    if not (min_val <= value <= max_val):
        raise ValidationError(
            error_code=ENC_003,
            field=field_name,
            value=f"{value}mm",
            expected=f"{min_val}~{max_val}mm 범위 내",
            phase=PHASE_1_NAME,
        )


def validate_enclosure_input(
    main_breaker: dict[str, Any],
    branch_breakers: list[dict[str, Any]],
    customer_requirements: dict[str, Any] | None = None,
) -> None:
    """
    외함 입력 전체 검증 (Phase 1 진입 전 전처리)

    Args:
        main_breaker: 메인 차단기 스펙
        branch_breakers: 분기 차단기 리스트
        customer_requirements: 고객 요구사항 (선택)

    Raises:
        ValidationError: ENC-003 - 입력 검증 실패
    """
    # 1. 메인 차단기 검증
    validate_breaker_spec(main_breaker)

    # 2. 분기 차단기 검증
    for i, breaker in enumerate(branch_breakers):
        try:
            validate_breaker_spec(breaker)
        except ValidationError as e:
            # 분기 차단기 번호 추가
            raise ValidationError(
                error_code=e.error_code,
                field=f"branch_breakers[{i}].{e.details.get('field', 'unknown')}",
                value=e.details.get("value"),
                expected=e.details.get("expected"),
                phase=e.phase,
            ) from e

    # 3. 고객 요구사항 검증 (선택적)
    if customer_requirements:
        # 치수 단위 정규화 (향후 확장)
        pass
