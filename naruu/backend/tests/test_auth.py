"""Integration tests for /api/auth endpoints.

Tests exercise the real FastAPI app with real SQLAlchemy sessions against
an in-process SQLite database. Zero mocks.
"""

import time
import uuid

import jwt
import pytest

from app.config import get_settings

settings = get_settings()

# Use .com domain for test emails -- Pydantic's EmailStr rejects .test TLD.
_DOMAIN = "naruutest.com"


# ── Registration ────────────────────────────────────


class TestRegister:
    """POST /api/auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        email = f"reg-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "ValidP@ss1",
                "name_ko": "등록테스트",
                "name_ja": "テスト",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == email
        assert body["name_ko"] == "등록테스트"
        assert body["name_ja"] == "テスト"
        assert body["role"] == "staff"
        assert body["is_active"] is True
        assert "id" in body

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client):
        email = f"dup-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        payload = {
            "email": email,
            "password": "Dup1icateP@ss",
            "name_ko": "중복테스트",
        }
        first = await client.post("/api/auth/register", json=payload)
        assert first.status_code == 201

        second = await client.post("/api/auth/register", json=payload)
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "Pass1234",
                "name_ko": "잘못된이메일",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_required_fields_returns_422(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={"email": f"ok@{_DOMAIN}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_with_custom_role(self, client):
        email = f"admin-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "AdminP@ss1",
                "name_ko": "관리자",
                "role": "admin",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"


# ── Login ───────────────────────────────────────────


class TestLogin:
    """POST /api/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, client):
        email = f"login-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        password = "LoginP@ss1"

        await client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "name_ko": "로그인"},
        )

        resp = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client):
        email = f"wrongpw-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        await client.post(
            "/api/auth/register",
            json={"email": email, "password": "Correct1", "name_ko": "비번오류"},
        )

        resp = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client):
        resp = await client.post(
            "/api/auth/login",
            json={"email": f"nobody@{_DOMAIN}", "password": "Whatever1"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_token_is_valid_jwt(self, client):
        email = f"jwtcheck-{uuid.uuid4().hex[:8]}@{_DOMAIN}"
        password = "JwtCheck1"
        await client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "name_ko": "JWT확인"},
        )
        resp = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        body = resp.json()
        decoded = jwt.decode(
            body["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert decoded["type"] == "access"
        assert decoded["username"] == email


# ── Refresh ─────────────────────────────────────────


class TestRefresh:
    """POST /api/auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_returns_new_token_pair(self, client, auth_headers):
        refresh_token = auth_headers["_refresh_token"]
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_returns_401(self, client):
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "garbage.token.here"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_returns_401(self, client):
        now = int(time.time())
        payload = {
            "sub": 99999,
            "username": f"expired@{_DOMAIN}",
            "role": "staff",
            "type": "refresh",
            "exp": now - 10,
            "iat": now - 70,
        }
        expired = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_returns_401(self, client, auth_headers):
        """Using an access token in the refresh endpoint should fail."""
        access_token = auth_headers["Authorization"].split(" ")[1]
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401


# ── Get Current User (/me) ──────────────────────────


class TestGetMe:
    """GET /api/auth/me"""

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, client, auth_headers):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": auth_headers["Authorization"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == auth_headers["_email"]
        assert body["is_active"] is True
        assert "id" in body

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_expired_token_returns_401(self, client):
        now = int(time.time())
        payload = {
            "sub": 99999,
            "username": f"expired@{_DOMAIN}",
            "role": "staff",
            "type": "access",
            "exp": now - 10,
            "iat": now - 70,
        }
        expired = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_refresh_token_returns_401(self, client, auth_headers):
        """Refresh tokens must not grant access to protected endpoints."""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_headers['_refresh_token']}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_nonexistent_user_id_returns_401(self, client):
        """Token is structurally valid but the user ID does not exist in DB."""
        now = int(time.time())
        payload = {
            "sub": 999999,
            "username": f"ghost@{_DOMAIN}",
            "role": "staff",
            "type": "access",
            "exp": now + 3600,
            "iat": now,
        }
        token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
