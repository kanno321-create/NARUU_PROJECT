"""
Unit Tests for utils/rbac.py
Coverage target: >90% for RBAC functions

Includes:
- Role extraction from X-Actor-Role header (dev mode)
- JWT role extraction and UserRole -> Role mapping
- Production mode security (header ignored)
- Permission checks (approval, PDF)
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from kis_estimator_core.core.ssot.errors import Role
from kis_estimator_core.utils.rbac import (
    RBACError,
    _USER_ROLE_TO_RBAC_ROLE,
    _extract_role_from_jwt,
    _is_production,
    check_quote_approval_permission,
    check_quote_pdf_permission,
    get_actor_role,
    require_role,
)


class TestRBACError:
    """Tests for RBACError exception"""

    def test_rbac_error_creation(self):
        """Test RBACError creation with all fields"""
        error = RBACError(
            message="Test error",
            required_role="APPROVER",
            actual_role="USER",
        )
        assert error.message == "Test error"
        assert error.required_role == "APPROVER"
        assert error.actual_role == "USER"
        assert str(error) == "Test error"

    def test_rbac_error_no_actual_role(self):
        """Test RBACError with None actual_role"""
        error = RBACError(
            message="Auth required",
            required_role="ADMIN",
            actual_role=None,
        )
        assert error.actual_role is None


class TestGetActorRole:
    """Tests for get_actor_role function"""

    def test_get_role_from_header(self):
        """Test getting role from X-Actor-Role header"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "approver"

        role = get_actor_role(mock_request)
        assert role == "APPROVER"

    def test_get_role_uppercase_header(self):
        """Test header value is converted to uppercase"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "ApProVeR"

        role = get_actor_role(mock_request)
        assert role == "APPROVER"

    def test_get_role_no_header(self):
        """Test returns None when no X-Actor-Role header"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        role = get_actor_role(mock_request)
        assert role is None


class TestRequireRole:
    """Tests for require_role function"""

    def test_require_role_match(self):
        """Test require_role passes when roles match"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "APPROVER"

        # Should not raise
        require_role(mock_request, Role.APPROVER)

    def test_require_role_no_role(self):
        """Test require_role raises when no role detected"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        with pytest.raises(RBACError) as exc:
            require_role(mock_request, Role.APPROVER)

        assert exc.value.required_role == "APPROVER"
        assert exc.value.actual_role is None
        assert "Authentication required" in exc.value.message

    def test_require_role_mismatch(self):
        """Test require_role raises when roles don't match"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "USER"

        with pytest.raises(RBACError) as exc:
            require_role(mock_request, Role.APPROVER)

        assert exc.value.required_role == "APPROVER"
        assert exc.value.actual_role == "USER"
        assert "Insufficient permissions" in exc.value.message

    def test_require_role_admin_bypass(self):
        """Test ADMIN role bypasses all requirements"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "ADMIN"

        # ADMIN should pass APPROVER check
        require_role(mock_request, Role.APPROVER)

        # ADMIN should pass USER check
        require_role(mock_request, Role.USER)


class TestCheckQuoteApprovalPermission:
    """Tests for check_quote_approval_permission function"""

    def test_approver_can_approve(self):
        """Test APPROVER can approve quotes"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "APPROVER"

        # Should not raise
        check_quote_approval_permission(mock_request)

    def test_user_cannot_approve(self):
        """Test USER cannot approve quotes"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "USER"

        with pytest.raises(RBACError):
            check_quote_approval_permission(mock_request)

    def test_admin_can_approve(self):
        """Test ADMIN can approve quotes"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "ADMIN"

        # Should not raise
        check_quote_approval_permission(mock_request)


class TestCheckQuotePdfPermission:
    """Tests for check_quote_pdf_permission function"""

    def test_approved_quote_allowed(self):
        """Test PDF generation allowed for APPROVED quotes"""
        mock_request = MagicMock()

        # Should not raise
        check_quote_pdf_permission(mock_request, "APPROVED")

    def test_draft_quote_forbidden(self):
        """Test PDF generation forbidden for DRAFT quotes"""
        mock_request = MagicMock()

        with pytest.raises(RBACError) as exc:
            check_quote_pdf_permission(mock_request, "DRAFT")

        assert "APPROVED quotes" in exc.value.message
        assert exc.value.actual_role == "DRAFT"

    def test_pending_quote_forbidden(self):
        """Test PDF generation forbidden for PENDING quotes"""
        mock_request = MagicMock()

        with pytest.raises(RBACError) as exc:
            check_quote_pdf_permission(mock_request, "PENDING")

        assert exc.value.actual_role == "PENDING"


class TestIsProduction:
    """Tests for _is_production helper"""

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_env(self):
        assert _is_production() is True

    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_development_env(self):
        assert _is_production() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_default_is_development(self):
        assert _is_production() is False


class TestUserRoleMapping:
    """Tests for _USER_ROLE_TO_RBAC_ROLE mapping"""

    def test_ceo_to_admin(self):
        assert _USER_ROLE_TO_RBAC_ROLE["ceo"] == Role.ADMIN.value

    def test_manager_to_approver(self):
        assert _USER_ROLE_TO_RBAC_ROLE["manager"] == Role.APPROVER.value

    def test_staff_to_user(self):
        assert _USER_ROLE_TO_RBAC_ROLE["staff"] == Role.USER.value


class TestExtractRoleFromJWT:
    """Tests for _extract_role_from_jwt function"""

    def test_no_auth_header(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        assert _extract_role_from_jwt(mock_request) is None

    def test_non_bearer_header(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Basic abc"
        assert _extract_role_from_jwt(mock_request) is None

    def test_empty_bearer(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer "
        assert _extract_role_from_jwt(mock_request) is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_valid_jwt_manager(self, mock_decode):
        mock_payload = MagicMock()
        mock_payload.role.value = "manager"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer tok"
        assert _extract_role_from_jwt(mock_request) == "APPROVER"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_decode_failure(self, mock_decode):
        mock_decode.return_value = None

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer bad"
        assert _extract_role_from_jwt(mock_request) is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_exception(self, mock_decode):
        mock_decode.side_effect = Exception("corrupt")

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer bad"
        assert _extract_role_from_jwt(mock_request) is None


class TestProductionModeSecurity:
    """Tests for production mode X-Actor-Role header blocking"""

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_header_ignored_in_production(self):
        mock_request = MagicMock()

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "ADMIN"
            return default

        mock_request.headers.get.side_effect = header_side_effect
        assert get_actor_role(mock_request) is None

    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_header_allowed_in_development(self):
        mock_request = MagicMock()

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "APPROVER"
            return default

        mock_request.headers.get.side_effect = header_side_effect
        assert get_actor_role(mock_request) == "APPROVER"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_jwt_works_in_production(self, mock_decode):
        mock_payload = MagicMock()
        mock_payload.role.value = "ceo"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock()

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return "Bearer tok"
            return default

        mock_request.headers.get.side_effect = header_side_effect
        assert get_actor_role(mock_request) == "ADMIN"
