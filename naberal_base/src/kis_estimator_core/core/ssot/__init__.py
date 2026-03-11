"""
Single Source of Truth (SSOT) - 모든 상수/타입/에러/매퍼 통합

절대 원칙:
- 모든 매직 넘버/문자열은 constants.py에서 정의
- 모든 타입은 types.py에서 정의
- 모든 에러는 errors.py에서 정의
- 모든 정규화는 mappers.py에서 정의
"""

from .constants import (
    ACCESSORY_MARGIN_PER_ROW_MM,
    CLEARANCE_VIOLATIONS_THRESHOLD,
    DEPTH_WITH_PBL_MM,
    DEPTH_WITHOUT_PBL_MM,
    DOOR_CLEARANCE_THRESHOLD,
    # Excel Symbols
    EXCEL_MULTIPLY_SYMBOL,
    EXCEL_SUBTOTAL_TEXT,
    EXCEL_TOTAL_TEXT,
    FACE_TO_FACE_SMALL_2P_MM,
    # Quality Gate Thresholds
    FIT_SCORE_THRESHOLD,
    FORMULA_PRESERVATION_THRESHOLD,
    IP_RATING_THRESHOLD,
    # Enclosure Dimensions
    MAIN_TO_BRANCH_GAP_MM,
    # Phase Names
    PHASE_0_NAME,
    PHASE_1_NAME,
    PHASE_2_NAME,
    PHASE_3_NAME,
    PHASE_BALANCE_THRESHOLD,
)
from .errors import (
    ErrorCode,
    EstimatorError,
    EstimatorErrorPayload,
    convert_builtin_error,
    raise_error,
)
from .mappers import (
    normalize_breaker_key,
    normalize_enclosure_key,
)
from .phase3_patch import (
    SSOT as Phase3SSOT,
)
from .phase3_patch import (
    Phase3AppError,
    assert_phase3_inputs,
    build_items,
    excel_formula_guard,
    normalize_breaker,
    normalize_enclosure,
)
from .types import (
    AccessorySpecDict,
    BreakerSpecDict,
    EnclosureDimensionsDict,
)

__all__ = [
    # Constants
    "PHASE_0_NAME",
    "PHASE_1_NAME",
    "PHASE_2_NAME",
    "PHASE_3_NAME",
    "FIT_SCORE_THRESHOLD",
    "PHASE_BALANCE_THRESHOLD",
    "CLEARANCE_VIOLATIONS_THRESHOLD",
    "FORMULA_PRESERVATION_THRESHOLD",
    "IP_RATING_THRESHOLD",
    "DOOR_CLEARANCE_THRESHOLD",
    "MAIN_TO_BRANCH_GAP_MM",
    "DEPTH_WITHOUT_PBL_MM",
    "DEPTH_WITH_PBL_MM",
    "FACE_TO_FACE_SMALL_2P_MM",
    "ACCESSORY_MARGIN_PER_ROW_MM",
    "EXCEL_MULTIPLY_SYMBOL",
    "EXCEL_TOTAL_TEXT",
    "EXCEL_SUBTOTAL_TEXT",
    # Types
    "BreakerSpecDict",
    "AccessorySpecDict",
    "EnclosureDimensionsDict",
    # Errors
    "EstimatorError",
    "EstimatorErrorPayload",
    "ErrorCode",
    "raise_error",
    "convert_builtin_error",
    # Mappers
    "normalize_breaker_key",
    "normalize_enclosure_key",
    # Phase3 Patch
    "Phase3SSOT",
    "Phase3AppError",
    "normalize_enclosure",
    "normalize_breaker",
    "build_items",
    "excel_formula_guard",
    "assert_phase3_inputs",
]
