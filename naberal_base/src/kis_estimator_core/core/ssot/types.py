"""
SSOT Types - 공용 타입 정의 (TypedDict, Enum, Protocol, Literal)

절대 원칙:
- 모든 타입은 여기서만 정의
- TypedDict로 명확한 구조 정의
- Enum으로 허용값 제한
"""

from enum import Enum
from typing import Literal, Protocol, TypedDict


# ============================================================
# Breaker Types
# ============================================================
class BreakerSpecDict(TypedDict, total=False):
    """
    차단기 스펙 표준 구조

    필수 필드:
        poles: 극수 (2, 3, 4)
        current_a: 정격전류 (A)
        frame_af: 프레임 (AF)

    선택 필드:
        model: 모델명
        type: MCCB/ELB
        brand: 브랜드명
    """

    poles: int  # 2, 3, 4
    current_a: int  # 20, 30, 40, 50, 60, 75, 100, ...
    frame_af: int  # 32, 50, 60, 100, 125, 200, 250, 400, 600, 800
    model: str  # "SBE-102", "SBS-54", etc.
    type: Literal["MCCB", "ELB"]
    brand: str  # "상도차단기", "LS산전", etc.


class AccessorySpecDict(TypedDict, total=False):
    """
    부속자재 스펙 표준 구조

    필수 필드:
        type: 자재 종류
        quantity: 수량

    선택 필드:
        model: 모델명
        spec: 규격
    """

    type: str  # "magnet", "timer", "pbl", "vameter", etc.
    quantity: int
    model: str | None
    spec: str | None


class EnclosureDimensionsDict(TypedDict):
    """
    외함 치수 표준 구조

    모든 필드 필수:
        width_mm: 폭 (mm)
        height_mm: 높이 (mm)
        depth_mm: 깊이 (mm)
    """

    width_mm: float
    height_mm: float
    depth_mm: float


# ============================================================
# Enums
# ============================================================
class BreakerType(str, Enum):
    """차단기 종류"""

    MCCB = "MCCB"  # 배선용차단기
    ELB = "ELB"  # 누전차단기


class BreakerEconomy(str, Enum):
    """차단기 경제성"""

    ECONOMY = "경제형"  # Economy type
    STANDARD = "표준형"  # Standard type
    SMALL = "소형"  # Small type (SIE-32, SIB-32)


class EnclosureMaterial(str, Enum):
    """외함 재질"""

    STEEL_1_6T = "STEEL 1.6T"
    STEEL_1_0T = "STEEL 1.0T"
    SUS201_1_2T = "SUS201 1.2T"


class EnclosureLocation(str, Enum):
    """외함 설치 위치"""

    INDOOR_EXPOSED = "옥내노출"
    OUTDOOR_EXPOSED = "옥외노출"
    INDOOR_FREESTANDING = "옥내자립"
    OUTDOOR_FREESTANDING = "옥외자립"
    RECESSED = "매입함"
    POLE_MOUNTED = "전주부착형"
    FRP = "FRP함"
    HIBOX = "하이박스"


class PhaseType(str, Enum):
    """상 타입"""

    R = "R"  # R상
    S = "S"  # S상
    T = "T"  # T상
    N = "N"  # 중성선


class QualityGateOperator(str, Enum):
    """품질 게이트 비교 연산자"""

    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


# ============================================================
# Protocols (구조적 타입핑)
# ============================================================
class BreakerSpecProtocol(Protocol):
    """차단기 스펙 프로토콜 (덕 타이핑 지원)"""

    poles: int
    current_a: int
    frame_af: int
    model: str


class EnclosureDimensionsProtocol(Protocol):
    """외함 치수 프로토콜"""

    width_mm: float
    height_mm: float
    depth_mm: float


# ============================================================
# Result Types
# ============================================================
class QualityGateResultDict(TypedDict):
    """품질 게이트 검증 결과"""

    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    operator: str
    critical: bool
    message: str


class ValidationResultDict(TypedDict):
    """검증 결과 표준 구조"""

    passed: bool
    errors: list[str]
    warnings: list[str]
    phase: str


# ============================================================
# Literal Types (허용값 제한)
# ============================================================
BreakerPoles = Literal[2, 3, 4]  # 극수
BreakerTypeStr = Literal["MCCB", "ELB"]  # 차단기 타입
PhaseStr = Literal["R", "S", "T", "N"]  # 상 타입
