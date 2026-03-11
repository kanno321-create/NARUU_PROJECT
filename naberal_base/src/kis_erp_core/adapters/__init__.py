"""
# SPDX-License-Identifier: KIS-Internal
Package initializer (Spec Kit policy).
"""

from .write_adapter import ERPWriteAdapter, ERPWriteDisabledError

__all__ = ["ERPWriteAdapter", "ERPWriteDisabledError"]
__version__ = "v3"

__spec_kit_compliant__ = True  # Phase 3 cleanup R2
