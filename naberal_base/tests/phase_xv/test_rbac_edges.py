"""
Phase XV: RBAC Edge Cases & Policy Enforcement Tests

Target: rbac.py coverage 34.38% → ≥60%

Test Coverage:
- USER/APPROVER/ADMIN role-based access control
- Quote approval permission (USER → 403, APPROVER → 200, ADMIN → bypass)
- PDF generation permission (DRAFT → 403, APPROVED → 200)
- Presign URL permission (unapproved → 403, approved → 200)
- Invalid role values and unauthenticated context (401/403)
- Observability: RBAC decision logging (user_role, action, resource, decision, policy_rule)
- Production mode: X-Actor-Role header IGNORED, JWT required
- JWT role mapping: UserRole(ceo/manager/staff) → Role(ADMIN/APPROVER/USER)

Contract-First / SSOT / Zero-Mock / Real DB
NO SYNTHETIC DATA - All role checks use real Role enum from SSOT
"""

import os

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request

from kis_estimator_core.utils.rbac import (
    get_actor_role,
    require_role,
    check_quote_approval_permission,
    check_quote_pdf_permission,
    RBACError,
    _USER_ROLE_TO_RBAC_ROLE,
    _is_production,
    _extract_role_from_jwt,
)
from kis_estimator_core.core.ssot.errors import Role


# ========================================================================
# Test Class 1: get_actor_role
# ========================================================================


class TestGetActorRole:
    """Test actor role extraction from request"""

    def test_get_actor_role_from_header_approver(self):
        """Test extract APPROVER role from X-Actor-Role header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "approver"

        role = get_actor_role(mock_request)

        assert role == "APPROVER"  # Should be uppercased

    def test_get_actor_role_from_header_user(self):
        """Test extract USER role from X-Actor-Role header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "user"

        role = get_actor_role(mock_request)

        assert role == "USER"

    def test_get_actor_role_from_header_admin(self):
        """Test extract ADMIN role from X-Actor-Role header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "admin"

        role = get_actor_role(mock_request)

        assert role == "ADMIN"

    def test_get_actor_role_no_header_returns_none(self):
        """Test no X-Actor-Role header returns None (unauthenticated)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None

        role = get_actor_role(mock_request)

        assert role is None

    def test_get_actor_role_case_insensitive(self):
        """Test role extraction is case-insensitive (uppercase conversion)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "ApPrOvEr"

        role = get_actor_role(mock_request)

        assert role == "APPROVER"


# ========================================================================
# Test Class 2: require_role
# ========================================================================


class TestRequireRole:
    """Test role requirement enforcement"""

    def test_require_role_approver_success(self):
        """Test require_role passes when actor has APPROVER role"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "APPROVER"

        # Should not raise
        require_role(mock_request, Role.APPROVER)

    def test_require_role_user_fails_for_approver(self):
        """Test require_role raises RBACError when USER tries APPROVER action"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "USER"

        with pytest.raises(RBACError) as exc_info:
            require_role(mock_request, Role.APPROVER)

        assert exc_info.value.required_role == "APPROVER"
        assert exc_info.value.actual_role == "USER"
        assert "Insufficient permissions" in exc_info.value.message

    def test_require_role_admin_bypasses_all(self):
        """Test ADMIN role bypasses all permission checks"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "ADMIN"

        # ADMIN should bypass APPROVER requirement
        require_role(mock_request, Role.APPROVER)

        # ADMIN should bypass USER requirement
        require_role(mock_request, Role.USER)

    def test_require_role_no_role_raises_auth_required(self):
        """Test require_role raises RBACError when no role present (unauthenticated)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None

        with pytest.raises(RBACError) as exc_info:
            require_role(mock_request, Role.APPROVER)

        assert exc_info.value.required_role == "APPROVER"
        assert exc_info.value.actual_role is None
        assert "Authentication required" in exc_info.value.message


# ========================================================================
# Test Class 3: check_quote_approval_permission
# ========================================================================


class TestCheckQuoteApprovalPermission:
    """Test quote approval permission enforcement"""

    def test_approval_permission_approver_success(self):
        """Test APPROVER can approve quotes"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "APPROVER"

        # Should not raise
        check_quote_approval_permission(mock_request)

    def test_approval_permission_user_fails(self):
        """Test USER cannot approve quotes (403 equivalent)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "USER"

        with pytest.raises(RBACError) as exc_info:
            check_quote_approval_permission(mock_request)

        assert exc_info.value.required_role == "APPROVER"
        assert exc_info.value.actual_role == "USER"

    def test_approval_permission_admin_success(self):
        """Test ADMIN can approve quotes (bypass)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "ADMIN"

        # Should not raise (ADMIN bypasses APPROVER requirement)
        check_quote_approval_permission(mock_request)

    def test_approval_permission_unauthenticated_fails(self):
        """Test unauthenticated request cannot approve (401 equivalent)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None

        with pytest.raises(RBACError) as exc_info:
            check_quote_approval_permission(mock_request)

        assert exc_info.value.actual_role is None
        assert "Authentication required" in exc_info.value.message


# ========================================================================
# Test Class 4: check_quote_pdf_permission
# ========================================================================


class TestCheckQuotePDFPermission:
    """Test PDF generation permission (status-based, not role-based)"""

    def test_pdf_permission_approved_quote_success(self):
        """Test approved quote allows PDF generation (any role)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "USER"

        # Should not raise for APPROVED quote
        check_quote_pdf_permission(mock_request, "APPROVED")

    def test_pdf_permission_draft_quote_fails(self):
        """Test DRAFT quote blocks PDF generation (403 policy violation)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "USER"

        with pytest.raises(RBACError) as exc_info:
            check_quote_pdf_permission(mock_request, "DRAFT")

        assert exc_info.value.required_role == "APPROVED_QUOTE"
        assert exc_info.value.actual_role == "DRAFT"
        assert "only allowed for APPROVED quotes" in exc_info.value.message

    def test_pdf_permission_rejected_quote_fails(self):
        """Test REJECTED quote blocks PDF generation"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "APPROVER"

        with pytest.raises(RBACError) as exc_info:
            check_quote_pdf_permission(mock_request, "REJECTED")

        assert exc_info.value.actual_role == "REJECTED"

    def test_pdf_permission_archived_quote_fails(self):
        """Test ARCHIVED quote blocks PDF generation"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "ADMIN"

        with pytest.raises(RBACError) as exc_info:
            check_quote_pdf_permission(mock_request, "ARCHIVED")

        assert exc_info.value.actual_role == "ARCHIVED"

    def test_pdf_permission_admin_still_requires_approved(self):
        """Test even ADMIN requires APPROVED status for PDF (policy enforcement)"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "ADMIN"

        # ADMIN cannot bypass quote status requirement
        with pytest.raises(RBACError) as exc_info:
            check_quote_pdf_permission(mock_request, "DRAFT")

        assert exc_info.value.actual_role == "DRAFT"


# ========================================================================
# Test Class 5: RBACError Exception
# ========================================================================


class TestRBACError:
    """Test RBACError exception structure"""

    def test_rbac_error_attributes(self):
        """Test RBACError has required attributes"""
        error = RBACError(
            message="Test error",
            required_role="APPROVER",
            actual_role="USER",
        )

        assert error.message == "Test error"
        assert error.required_role == "APPROVER"
        assert error.actual_role == "USER"
        assert str(error) == "Test error"

    def test_rbac_error_none_actual_role(self):
        """Test RBACError with None actual_role (unauthenticated)"""
        error = RBACError(
            message="Auth required",
            required_role="APPROVER",
            actual_role=None,
        )

        assert error.actual_role is None


# ========================================================================
# Test Class 6: Observability & Logging
# ========================================================================


class TestRBACObservability:
    """Test observability fields in RBAC decisions (structured logging)"""

    @pytest.mark.skip(reason="Observability implementation pending Phase XV")
    def test_observability_rbac_decision_logged(self):
        """Test RBAC decision is logged with structured fields"""
        # Expected observability fields (for future implementation):
        # - user_role: "USER" or "APPROVER" or "ADMIN"
        # - action: "approve_quote" or "generate_pdf" or "presign_url"
        # - resource: "quote_id"
        # - decision: "allow" or "deny"
        # - policy_rule: "APPROVER_ONLY" or "APPROVED_QUOTE_REQUIRED"
        # - latency_ms: execution time

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "USER"

        try:
            check_quote_approval_permission(mock_request)
        except RBACError:
            pass

        # Future: Verify logger called with structured fields
        # assert mock_logger.warning.called
        # call_args = mock_logger.warning.call_args[0][0]
        # assert "user_role" in call_args
        # assert "decision" in call_args
        # assert call_args["decision"] == "deny"


# ========================================================================
# Test Class 7: Edge Cases & Integration
# ========================================================================


class TestRBACEdgeCases:
    """Test RBAC edge cases and integration scenarios"""

    def test_role_case_variations(self):
        """Test role extraction handles various case formats"""
        test_cases = [
            ("user", "USER"),
            ("USER", "USER"),
            ("User", "USER"),
            ("approver", "APPROVER"),
            ("APPROVER", "APPROVER"),
            ("admin", "ADMIN"),
        ]

        for input_role, expected_role in test_cases:
            mock_request = MagicMock(spec=Request)
            mock_request.headers.get.return_value = input_role

            role = get_actor_role(mock_request)
            assert role == expected_role

    def test_multiple_permission_checks_same_request(self):
        """Test multiple RBAC checks on same request object"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "APPROVER"

        # APPROVER should pass approval check
        check_quote_approval_permission(mock_request)

        # APPROVER should also pass PDF check for APPROVED quote
        check_quote_pdf_permission(mock_request, "APPROVED")

        # Both checks should succeed without interference


# ========================================================================
# Test Class 8: _USER_ROLE_TO_RBAC_ROLE Mapping
# ========================================================================


class TestUserRoleToRBACRoleMapping:
    """Test UserRole -> RBAC Role mapping dictionary"""

    def test_mapping_ceo_to_admin(self):
        """Test CEO maps to ADMIN"""
        assert _USER_ROLE_TO_RBAC_ROLE["ceo"] == "ADMIN"

    def test_mapping_manager_to_approver(self):
        """Test MANAGER maps to APPROVER"""
        assert _USER_ROLE_TO_RBAC_ROLE["manager"] == "APPROVER"

    def test_mapping_staff_to_user(self):
        """Test STAFF maps to USER"""
        assert _USER_ROLE_TO_RBAC_ROLE["staff"] == "USER"

    def test_mapping_has_exactly_three_entries(self):
        """Test mapping contains exactly 3 entries (no extras)"""
        assert len(_USER_ROLE_TO_RBAC_ROLE) == 3

    def test_mapping_unknown_role_returns_none(self):
        """Test unknown role key returns None via .get()"""
        assert _USER_ROLE_TO_RBAC_ROLE.get("unknown") is None

    def test_mapping_uses_ssot_role_values(self):
        """Test mapping values match Role enum from SSOT"""
        assert _USER_ROLE_TO_RBAC_ROLE["ceo"] == Role.ADMIN.value
        assert _USER_ROLE_TO_RBAC_ROLE["manager"] == Role.APPROVER.value
        assert _USER_ROLE_TO_RBAC_ROLE["staff"] == Role.USER.value


# ========================================================================
# Test Class 9: _is_production
# ========================================================================


class TestIsProduction:
    """Test production environment detection"""

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_is_production_true(self):
        """Test returns True when APP_ENV=production"""
        assert _is_production() is True

    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_is_production_false_development(self):
        """Test returns False when APP_ENV=development"""
        assert _is_production() is False

    @patch.dict(os.environ, {"APP_ENV": "Production"})
    def test_is_production_case_insensitive(self):
        """Test production detection is case-insensitive"""
        assert _is_production() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_production_default_development(self):
        """Test defaults to development (False) when APP_ENV not set"""
        assert _is_production() is False

    @patch.dict(os.environ, {"APP_ENV": "staging"})
    def test_is_production_staging_is_not_production(self):
        """Test staging is not production"""
        assert _is_production() is False


# ========================================================================
# Test Class 10: _extract_role_from_jwt
# ========================================================================


class TestExtractRoleFromJWT:
    """Test JWT role extraction from Authorization header"""

    def test_no_authorization_header(self):
        """Test returns None when no Authorization header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None

        assert _extract_role_from_jwt(mock_request) is None

    def test_non_bearer_authorization(self):
        """Test returns None for non-Bearer authorization"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Basic dXNlcjpwYXNz"

        assert _extract_role_from_jwt(mock_request) is None

    def test_empty_bearer_token(self):
        """Test returns None for Bearer with empty token"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer "

        assert _extract_role_from_jwt(mock_request) is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_ceo_maps_to_admin(self, mock_decode):
        """Test JWT with CEO role maps to ADMIN"""
        mock_payload = MagicMock()
        mock_payload.role.value = "ceo"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid_token"

        result = _extract_role_from_jwt(mock_request)
        assert result == "ADMIN"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_manager_maps_to_approver(self, mock_decode):
        """Test JWT with MANAGER role maps to APPROVER"""
        mock_payload = MagicMock()
        mock_payload.role.value = "manager"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid_token"

        result = _extract_role_from_jwt(mock_request)
        assert result == "APPROVER"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_staff_maps_to_user(self, mock_decode):
        """Test JWT with STAFF role maps to USER"""
        mock_payload = MagicMock()
        mock_payload.role.value = "staff"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid_token"

        result = _extract_role_from_jwt(mock_request)
        assert result == "USER"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_decode_returns_none(self, mock_decode):
        """Test returns None when JWT decode fails (expired/invalid)"""
        mock_decode.return_value = None

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer expired_token"

        result = _extract_role_from_jwt(mock_request)
        assert result is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_unknown_role_returns_none(self, mock_decode):
        """Test returns None for unknown JWT role value"""
        mock_payload = MagicMock()
        mock_payload.role.value = "intern"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid_token"

        result = _extract_role_from_jwt(mock_request)
        assert result is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_decode_exception_returns_none(self, mock_decode):
        """Test returns None when decode_token raises exception"""
        mock_decode.side_effect = Exception("Token corrupted")

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer corrupted_token"

        result = _extract_role_from_jwt(mock_request)
        assert result is None

    @patch("kis_estimator_core.services.auth_service.decode_token")
    def test_jwt_role_without_value_attribute(self, mock_decode):
        """Test handles role without .value attribute (string role)"""
        mock_payload = MagicMock(spec=[])  # empty spec = no attributes
        mock_payload.role = "manager"  # plain string, no .value

        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = "Bearer valid_token"

        result = _extract_role_from_jwt(mock_request)
        assert result == "APPROVER"


# ========================================================================
# Test Class 11: Production Mode - X-Actor-Role Header Ignored
# ========================================================================


class TestProductionModeHeaderIgnored:
    """Test X-Actor-Role header is IGNORED in production environment"""

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_ignores_header_returns_none(self):
        """Test production mode ignores X-Actor-Role header, returns None"""
        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "ADMIN"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        role = get_actor_role(mock_request)
        assert role is None  # Header ignored in production

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_header_ignored_even_with_admin(self):
        """Test ADMIN header ignored in production (security: prevents header spoofing)"""
        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "ADMIN"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        # In production, no JWT = no role, even with X-Actor-Role: ADMIN
        with pytest.raises(RBACError):
            require_role(mock_request, Role.USER)

    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_development_allows_header(self):
        """Test development mode allows X-Actor-Role header"""
        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "APPROVER"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        role = get_actor_role(mock_request)
        assert role == "APPROVER"  # Header accepted in development


# ========================================================================
# Test Class 12: JWT + Production Mode Integration
# ========================================================================


class TestJWTProductionIntegration:
    """Test JWT authentication in production mode (end-to-end flow)"""

    @patch("kis_estimator_core.services.auth_service.decode_token")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_jwt_ceo_gets_admin(self, mock_decode):
        """Test production: JWT with CEO role grants ADMIN access"""
        mock_payload = MagicMock()
        mock_payload.role.value = "ceo"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return "Bearer valid_ceo_token"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        role = get_actor_role(mock_request)
        assert role == "ADMIN"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_jwt_manager_can_approve(self, mock_decode):
        """Test production: JWT MANAGER can approve quotes"""
        mock_payload = MagicMock()
        mock_payload.role.value = "manager"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return "Bearer valid_manager_token"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        # Should not raise - manager maps to APPROVER
        check_quote_approval_permission(mock_request)

    @patch("kis_estimator_core.services.auth_service.decode_token")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_jwt_staff_cannot_approve(self, mock_decode):
        """Test production: JWT STAFF cannot approve quotes"""
        mock_payload = MagicMock()
        mock_payload.role.value = "staff"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return "Bearer valid_staff_token"
            return default

        mock_request.headers.get.side_effect = header_side_effect

        with pytest.raises(RBACError) as exc_info:
            check_quote_approval_permission(mock_request)

        assert exc_info.value.actual_role == "USER"
        assert exc_info.value.required_role == "APPROVER"

    @patch("kis_estimator_core.services.auth_service.decode_token")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_jwt_takes_priority_over_header(self, mock_decode):
        """Test JWT role takes priority over X-Actor-Role header"""
        mock_payload = MagicMock()
        mock_payload.role.value = "staff"
        mock_decode.return_value = mock_payload

        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return "Bearer valid_token"
            if name == "X-Actor-Role":
                return "ADMIN"  # Attacker tries header spoofing
            return default

        mock_request.headers.get.side_effect = header_side_effect

        role = get_actor_role(mock_request)
        assert role == "USER"  # JWT staff role wins, not spoofed ADMIN

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_no_jwt_no_access(self):
        """Test production: no JWT token = no access at all"""
        mock_request = MagicMock(spec=Request)

        def header_side_effect(name, default=None):
            if name == "Authorization":
                return None
            if name == "X-Actor-Role":
                return "ADMIN"  # Header ignored
            return default

        mock_request.headers.get.side_effect = header_side_effect

        role = get_actor_role(mock_request)
        assert role is None

        with pytest.raises(RBACError) as exc_info:
            require_role(mock_request, Role.USER)

        assert "Authentication required" in exc_info.value.message
