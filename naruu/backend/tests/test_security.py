"""Unit tests for app.utils.security -- password hashing and JWT tokens.

Every test calls real bcrypt / PyJWT functions. Zero mocks.
"""

import time

import jwt
import pytest

from app.config import get_settings
from app.utils.security import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)

settings = get_settings()


# ── Password hashing ────────────────────────────────


class TestPasswordHashing:
    """hash_password / verify_password round-trip tests."""

    def test_hash_and_verify_correct_password(self):
        plain = "MySecureP@ss123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_produces_different_outputs_for_same_input(self):
        """bcrypt salts should make every hash unique."""
        plain = "same-password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2, "Two hashes of the same password must differ (unique salt)"

    def test_hash_is_bcrypt_format(self):
        hashed = hash_password("anything")
        assert hashed.startswith("$2"), "Hash should be bcrypt ($2a$ or $2b$)"

    def test_empty_password_hashes_and_verifies(self):
        plain = ""
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_unicode_password(self):
        plain = "パスワード密码1234!"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_long_password(self):
        """bcrypt truncates at 72 bytes but should still round-trip."""
        plain = "A" * 100
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True


# ── JWT token creation ──────────────────────────────


class TestAccessToken:
    """create_access_token / verify_access_token round-trip tests."""

    def test_create_and_verify_access_token(self):
        token = create_access_token(user_id=1, username="admin@test.com", role="admin")
        payload = verify_access_token(token)

        assert payload is not None
        assert payload.sub == "1"
        assert payload.username == "admin@test.com"
        assert payload.role == "admin"
        assert payload.type == "access"

    def test_access_token_has_correct_claims(self):
        token = create_access_token(user_id=42, username="u@x.com", role="staff")
        raw = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert raw["sub"] == "42"
        assert raw["username"] == "u@x.com"
        assert raw["role"] == "staff"
        assert raw["type"] == "access"
        assert "exp" in raw
        assert "iat" in raw

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token(user_id=1, username="a@b.com", role="admin")
        assert verify_refresh_token(token) is None

    def test_access_token_with_different_roles(self):
        for role in ("admin", "manager", "staff"):
            token = create_access_token(user_id=1, username="x@y.com", role=role)
            payload = verify_access_token(token)
            assert payload is not None
            assert payload.role == role


class TestRefreshToken:
    """create_refresh_token / verify_refresh_token round-trip tests."""

    def test_create_and_verify_refresh_token(self):
        token = create_refresh_token(user_id=2, username="staff@test.com", role="staff")
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload.sub == "2"
        assert payload.username == "staff@test.com"
        assert payload.role == "staff"
        assert payload.type == "refresh"

    def test_refresh_token_rejected_as_access(self):
        token = create_refresh_token(user_id=1, username="a@b.com", role="admin")
        assert verify_access_token(token) is None


class TestTokenPair:
    """create_token_pair convenience function."""

    def test_pair_contains_both_tokens(self):
        pair = create_token_pair(user_id=5, username="duo@test.com", role="manager")

        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"

        access_payload = verify_access_token(pair.access_token)
        refresh_payload = verify_refresh_token(pair.refresh_token)

        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload.sub == refresh_payload.sub == "5"


# ── Token expiration ────────────────────────────────


class TestTokenExpiration:
    """Expired and tampered token handling."""

    def test_expired_access_token_returns_none(self):
        """Craft a token that expired 10 seconds ago."""
        now = int(time.time())
        payload = {
            "sub": 1,
            "username": "expired@test.com",
            "role": "admin",
            "type": "access",
            "exp": now - 10,
            "iat": now - 70,
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert verify_access_token(token) is None

    def test_expired_refresh_token_returns_none(self):
        now = int(time.time())
        payload = {
            "sub": 1,
            "username": "expired@test.com",
            "role": "admin",
            "type": "refresh",
            "exp": now - 10,
            "iat": now - 70,
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert verify_refresh_token(token) is None


# ── Malformed / tampered tokens ─────────────────────


class TestMalformedTokens:
    """Handling of garbage, tampered, or structurally invalid tokens."""

    def test_random_string_returns_none(self):
        assert decode_token("not-a-jwt-at-all") is None

    def test_empty_string_returns_none(self):
        assert decode_token("") is None

    def test_wrong_secret_returns_none(self):
        payload = {
            "sub": 1,
            "username": "x@y.com",
            "role": "admin",
            "type": "access",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        assert decode_token(token) is None

    def test_missing_claims_returns_none(self):
        """Token with valid signature but missing required claims.

        decode_token catches pydantic.ValidationError when JWT crypto
        succeeds but the payload lacks required TokenPayload fields
        (username, role, type), and returns None gracefully.
        """
        payload = {
            "sub": 1,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            # missing: username, role, type
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert decode_token(token) is None

    def test_wrong_algorithm_returns_none(self):
        """Token signed with HS384 but verified with HS256."""
        payload = {
            "sub": 1,
            "username": "x@y.com",
            "role": "admin",
            "type": "access",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS384")
        assert decode_token(token) is None

    def test_token_with_unknown_type_rejected_by_verify_functions(self):
        """A token with type='unknown' passes decode but fails verify_access/refresh."""
        now = int(time.time())
        payload = {
            "sub": 1,
            "username": "x@y.com",
            "role": "admin",
            "type": "unknown",
            "exp": now + 3600,
            "iat": now,
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.type == "unknown"

        assert verify_access_token(token) is None
        assert verify_refresh_token(token) is None
