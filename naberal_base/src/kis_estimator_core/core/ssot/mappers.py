"""
SSOT Mappers - 키 정규화/스펙 변환/시간·통화 유틸리티

절대 원칙:
- 모든 키 정규화는 여기서만 수행
- Alias 허용: current_a, current, ampere → current_a
- Alias 허용: frame_af, frame, af → frame_af
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

from .constants import (
    BREAKER_CURRENT_ALIASES,
    BREAKER_FRAME_ALIASES,
    BREAKER_POLES_ALIASES,
    ENCLOSURE_DEPTH_ALIASES,
    ENCLOSURE_HEIGHT_ALIASES,
    ENCLOSURE_WIDTH_ALIASES,
    KRW_CURRENCY_SYMBOL,
    VAT_RATE,
)


# ============================================================
# Breaker Key Normalization
# ============================================================
def normalize_breaker_key(data: dict[str, Any]) -> dict[str, Any]:
    """
    차단기 키 정규화

    Alias 허용:
    - current_a, current, ampere, at → current_a
    - frame_af, frame, af → frame_af
    - poles, pole, p → poles

    Args:
        data: 원본 데이터 (예: {"current": 60, "frame": 100})

    Returns:
        정규화된 데이터 (예: {"current_a": 60, "frame_af": 100})
    """
    normalized = data.copy()

    # current_a 정규화
    for alias in BREAKER_CURRENT_ALIASES:
        if alias in normalized:
            normalized["current_a"] = normalized.pop(alias)
            break

    # frame_af 정규화
    for alias in BREAKER_FRAME_ALIASES:
        if alias in normalized:
            normalized["frame_af"] = normalized.pop(alias)
            break

    # poles 정규화
    for alias in BREAKER_POLES_ALIASES:
        if alias in normalized:
            normalized["poles"] = normalized.pop(alias)
            break

    return normalized


def normalize_enclosure_key(data: dict[str, Any]) -> dict[str, Any]:
    """
    외함 키 정규화

    Alias 허용:
    - width_mm, width, w → width_mm
    - height_mm, height, h → height_mm
    - depth_mm, depth, d → depth_mm

    Args:
        data: 원본 데이터 (예: {"w": 600, "h": 800, "d": 150})

    Returns:
        정규화된 데이터 (예: {"width_mm": 600, "height_mm": 800, "depth_mm": 150})
    """
    normalized = data.copy()

    # width_mm 정규화
    for alias in ENCLOSURE_WIDTH_ALIASES:
        if alias in normalized:
            normalized["width_mm"] = normalized.pop(alias)
            break

    # height_mm 정규화
    for alias in ENCLOSURE_HEIGHT_ALIASES:
        if alias in normalized:
            normalized["height_mm"] = normalized.pop(alias)
            break

    # depth_mm 정규화
    for alias in ENCLOSURE_DEPTH_ALIASES:
        if alias in normalized:
            normalized["depth_mm"] = normalized.pop(alias)
            break

    return normalized


# ============================================================
# Spec String Parsing
# ============================================================
def parse_breaker_spec(spec_str: str) -> dict[str, Any]:
    """
    차단기 스펙 문자열 파싱

    예:
        "4P 100AF 75AT 14kA" → {
            "poles": 4,
            "frame_af": 100,
            "current_a": 75,
            "capacity_ka": 14
        }

    Args:
        spec_str: 스펙 문자열

    Returns:
        파싱된 딕셔너리
    """
    parts = spec_str.upper().split()
    result = {}

    for part in parts:
        if part.endswith("P"):
            # Poles
            result["poles"] = int(part[:-1])
        elif "AF" in part:
            # Frame AF
            result["frame_af"] = int(part.replace("AF", ""))
        elif "AT" in part:
            # Current AT
            result["current_a"] = int(part.replace("AT", ""))
        elif "KA" in part:
            # Capacity kA
            result["capacity_ka"] = float(part.replace("KA", ""))

    return result


def format_breaker_spec(
    poles: int,
    frame_af: int,
    current_a: int,
    capacity_ka: float | None = None,
) -> str:
    """
    차단기 스펙 문자열 생성

    Args:
        poles: 극수
        frame_af: 프레임
        current_a: 정격전류
        capacity_ka: 차단용량 (선택)

    Returns:
        스펙 문자열 (예: "4P 100AF 75AT 14kA")
    """
    parts = [
        f"{poles}P",
        f"{frame_af}AF",
        f"{current_a}AT",
    ]

    if capacity_ka is not None:
        parts.append(f"{capacity_ka}kA")

    return " ".join(parts)


# ============================================================
# Size String Parsing
# ============================================================
def parse_size_string(size_str: str) -> dict[str, float]:
    """
    크기 문자열 파싱

    예:
        "600×800×150" → {"width_mm": 600, "height_mm": 800, "depth_mm": 150}
        "600*800*150" → 동일

    Args:
        size_str: 크기 문자열

    Returns:
        파싱된 딕셔너리
    """
    # × 또는 * 로 분리
    parts = size_str.replace("×", "*").split("*")

    if len(parts) != 3:
        raise_error(ErrorCode.E_INTERNAL, f"Invalid size string: {size_str}")

    return {
        "width_mm": float(parts[0].strip()),
        "height_mm": float(parts[1].strip()),
        "depth_mm": float(parts[2].strip()),
    }


def format_size_string(width: float, height: float, depth: float) -> str:
    """
    크기 문자열 생성

    Args:
        width: 폭 (mm)
        height: 높이 (mm)
        depth: 깊이 (mm)

    Returns:
        크기 문자열 (예: "600×800×150")
    """
    return f"{int(width)}×{int(height)}×{int(depth)}"


# ============================================================
# Currency & Tax Utilities
# ============================================================
def apply_vat(amount: int | float | Decimal) -> Decimal:
    """
    부가세 적용

    Args:
        amount: 원금액

    Returns:
        부가세 포함 금액 (10% 적용)
    """
    base = Decimal(str(amount))
    return base * (Decimal("1") + Decimal(str(VAT_RATE)))


def remove_vat(amount: int | float | Decimal) -> Decimal:
    """
    부가세 제거

    Args:
        amount: 부가세 포함 금액

    Returns:
        원금액
    """
    total = Decimal(str(amount))
    return total / (Decimal("1") + Decimal(str(VAT_RATE)))


def format_krw(amount: int | float | Decimal) -> str:
    """
    KRW 통화 포맷

    Args:
        amount: 금액

    Returns:
        포맷된 문자열 (예: "12,500원")
    """
    return f"{int(amount):,}{KRW_CURRENCY_SYMBOL}"


# ============================================================
# Timestamp Utilities
# ============================================================
def format_timestamp(dt: datetime | None = None) -> str:
    """
    타임스탬프 포맷 (ISO 8601)

    Args:
        dt: datetime 객체 (None이면 현재 시각)

    Returns:
        ISO 8601 문자열 (예: "2025-10-05T14:30:00Z")
    """
    if dt is None:
        dt = datetime.utcnow()

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    타임스탬프 파싱

    Args:
        timestamp_str: ISO 8601 문자열

    Returns:
        datetime 객체
    """
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
