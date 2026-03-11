"""
KIS Estimator Core Models
Pydantic 모델 정의
"""

from .enclosure import (
    AccessorySpec,
    BreakerSpec,
    CustomerRequirements,
    EnclosureCandidate,
    EnclosureDimensions,
    EnclosureResult,
    EnclosureSpec,
    QualityGateResult,
)

__all__ = [
    "BreakerSpec",
    "AccessorySpec",
    "CustomerRequirements",
    "EnclosureSpec",
    "EnclosureCandidate",
    "EnclosureDimensions",
    "QualityGateResult",
    "EnclosureResult",
]
