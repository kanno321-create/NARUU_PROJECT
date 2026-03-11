"""
KIS Estimator 에러 처리 모듈
"""

from .error_codes import (
    # Accessory Errors
    ACC_001,
    ACC_002,
    ACC_003,
    ACC_004,
    # 7대 치명적 버그
    BUG_001,
    BUG_002,
    BUG_003,
    BUG_004,
    BUG_005,
    BUG_006,
    BUG_007,
    # BUS-BAR Errors
    BUS_001,
    BUS_002,
    BUS_003,
    BUS_004,
    # Calculation Errors
    CAL_001,
    CAL_002,
    # Catalog Errors
    CAT_001,
    CAT_002,
    CAT_003,
    # Enclosure Errors
    ENC_001,
    ENC_002,
    ENC_003,
    ERROR_CODE_MAP,
    # Input Errors
    INP_001,
    INP_002,
    INP_003,
    INP_004,
    INP_005,
    # Layout Errors
    LAY_001,
    LAY_002,
    LAY_004,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    get_error,
    is_blocking_error,
)
from .exceptions import CatalogError, EstimatorError, PhaseBlockedError, ValidationError

# Backward compatibility alias
AppError = EstimatorError

__all__ = [
    "ErrorCode",
    "ErrorSeverity",
    "ErrorCategory",
    "ERROR_CODE_MAP",
    "get_error",
    "is_blocking_error",
    "EstimatorError",
    "AppError",  # Backward compatibility
    "ValidationError",
    "CatalogError",
    "PhaseBlockedError",
    # Input Errors
    "INP_001",
    "INP_002",
    "INP_003",
    "INP_004",
    "INP_005",
    # 7대 치명적 버그
    "BUG_001",
    "BUG_002",
    "BUG_003",
    "BUG_004",
    "BUG_005",
    "BUG_006",
    "BUG_007",
    # BUS-BAR Errors
    "BUS_001",
    "BUS_002",
    "BUS_003",
    "BUS_004",
    # Catalog Errors
    "CAT_001",
    "CAT_002",
    "CAT_003",
    # Enclosure Errors
    "ENC_001",
    "ENC_002",
    "ENC_003",
    # Accessory Errors
    "ACC_001",
    "ACC_002",
    "ACC_003",
    "ACC_004",
    # Layout Errors
    "LAY_001",
    "LAY_002",
    "LAY_004",
    # Calculation Errors
    "CAL_001",
    "CAL_002",
]
