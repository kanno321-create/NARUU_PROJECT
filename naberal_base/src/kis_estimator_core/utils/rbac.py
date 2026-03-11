"""
RBAC (Role-Based Access Control) - Phase XI

Simple role-based authorization for Quote operations:
- APPROVER: Can approve quotes
- USER: Can create and view quotes (cannot approve)

Role sources (priority order):
1. JWT claims from Authorization header (production + development)
2. X-Actor-Role header (development/test mode ONLY - blocked in production)

Zero-Mock / SSOT / Evidence-Gated
"""

import logging
import os

from fastapi import Request

from kis_estimator_core.core.ssot.errors import Role

logger = logging.getLogger(__name__)

# UserRole (auth_service) -> Role (RBAC) mapping
# UserRole values: "ceo", "manager", "staff"
# Role values: "ADMIN", "APPROVER", "USER"
_USER_ROLE_TO_RBAC_ROLE: dict[str, str] = {
    "ceo": Role.ADMIN.value,
    "manager": Role.APPROVER.value,
    "staff": Role.USER.value,
}


def _is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("APP_ENV", "development").lower() == "production"


def _extract_role_from_jwt(request: Request) -> str | None:
    """
    Extract RBAC role from JWT Authorization header.

    Parses the Bearer token, decodes it, extracts the 'role' claim,
    and maps UserRole -> RBAC Role.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Strip "Bearer "
    if not token:
        return None

    try:
        from kis_estimator_core.services.auth_service import decode_token
        payload = decode_token(token)
        if not payload:
            logger.warning("RBAC: JWT decode failed - invalid or expired token")
            return None

        # payload.role is UserRole enum with .value like "ceo", "manager", "staff"
        user_role_value = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
        rbac_role = _USER_ROLE_TO_RBAC_ROLE.get(user_role_value)

        if rbac_role:
            logger.debug(f"RBAC: JWT role mapped: {user_role_value} -> {rbac_role}")
            return rbac_role

        logger.warning(f"RBAC: Unknown JWT role value: {user_role_value}")
        return None

    except Exception as e:
        logger.warning(f"RBAC: JWT parsing error: {e}")
        return None


class RBACError(Exception):
    """RBAC authorization error"""

    def __init__(self, message: str, required_role: str, actual_role: str | None):
        self.message = message
        self.required_role = required_role
        self.actual_role = actual_role
        super().__init__(self.message)


def get_actor_role(request: Request) -> str | None:
    """
    Extract actor role from request.

    Priority:
    1. JWT Authorization header (always checked first)
    2. X-Actor-Role header (development/test mode ONLY)

    In production: X-Actor-Role header is IGNORED for security.
    In development: X-Actor-Role header is accepted as fallback (for testing convenience).

    Args:
        request: FastAPI Request object

    Returns:
        Role string (APPROVER, USER, ADMIN) or None
    """
    # 1. Always try JWT first (works in all environments)
    jwt_role = _extract_role_from_jwt(request)
    if jwt_role:
        return jwt_role

    # 2. X-Actor-Role header - ONLY in development/test mode
    if not _is_production():
        actor_role_header = request.headers.get("X-Actor-Role")
        if actor_role_header:
            logger.debug(f"RBAC: role from X-Actor-Role header (dev mode): {actor_role_header}")
            return actor_role_header.upper()
    else:
        # In production, log if someone tries to use the header (security audit)
        if request.headers.get("X-Actor-Role"):
            logger.warning("RBAC: X-Actor-Role header ignored in production environment")

    return None


def require_role(request: Request, required_role: Role) -> None:
    """
    Check if actor has required role

    Args:
        request: FastAPI Request object
        required_role: Required role

    Raises:
        RBACError: If actor does not have required role
    """
    actor_role = get_actor_role(request)

    # If no role detected, deny (default-deny policy)
    if not actor_role:
        raise RBACError(
            message=f"Authentication required. Role '{required_role.value}' needed.",
            required_role=required_role.value,
            actual_role=None,
        )

    # Check if actor has required role
    if actor_role != required_role.value:
        # Special case: ADMIN has all permissions
        if actor_role == Role.ADMIN.value:
            logger.debug(f"ADMIN role bypasses {required_role.value} requirement")
            return

        raise RBACError(
            message=f"Insufficient permissions. Role '{required_role.value}' required, but actor has '{actor_role}'.",
            required_role=required_role.value,
            actual_role=actor_role,
        )

    logger.debug(
        f"RBAC check passed: actor={actor_role}, required={required_role.value}"
    )


def check_quote_approval_permission(request: Request) -> None:
    """
    Check if actor can approve quotes

    Args:
        request: FastAPI Request object

    Raises:
        RBACError: If actor cannot approve quotes
    """
    require_role(request, Role.APPROVER)


def check_quote_pdf_permission(request: Request, quote_status: str) -> None:
    """
    Check if actor can generate PDF for quote

    Phase XI policy:
    - Approved quotes: Anyone can generate PDF
    - Unapproved quotes: FORBIDDEN (403)

    Args:
        request: FastAPI Request object
        quote_status: Quote status (DRAFT, APPROVED, etc.)

    Raises:
        RBACError: If PDF generation not allowed for this quote
    """
    if quote_status != "APPROVED":
        raise RBACError(
            message="PDF generation is only allowed for APPROVED quotes. Please approve the quote first.",
            required_role="APPROVED_QUOTE",
            actual_role=quote_status,
        )
