"""
# SPDX-License-Identifier: KIS-Internal
Package initializer (Spec Kit policy).

REBUILD Phase C (T2): Async only
"""

from .health import check_kpew_health_async

__all__ = ["check_kpew_health_async"]
__version__ = "v3.1"

__spec_kit_compliant__ = True  # Phase 3 cleanup R2 + T2 async
