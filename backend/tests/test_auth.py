"""인증 시스템 테스트."""

from __future__ import annotations

import time

import jwt as pyjwt
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from naruu_core.auth.jwt_handler import JWTHandler
from naruu_core.auth.password import hash_password, verify_password
from naruu_core.models.user import User

TEST_SECRET = "test-secret-key-for-naruu-platform"


# ── Unit 테스트: 비밀번호 ──


@pytest.mark.unit
class TestPassword:
    """비밀번호 해싱 유닛 테스트."""

    def test_hash_creates_different_from_plain(self) -> None:
        """해시는 평문과 다르다."""
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 20

    def test_verify_correct_password(self) -> None:
        """올바른 비밀번호 검증 성공."""
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_verify_wrong_password(self) -> None:
        """잘못된 비밀번호 검증 실패."""
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_unique(self) -> None:
        """같은 비밀번호도 다른 해시 생성 (salt)."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ── Unit 테스트: JWT ──


@pytest.mark.unit
class TestJWTHandler:
    """JWT 토큰 유닛 테스트."""

    def test_create_and_decode(self) -> None:
        """토큰 생성 후 디코딩 성공."""
        handler = JWTHandler(secret=TEST_SECRET)
        token = handler.create_token({"sub": "user-1", "email": "test@test.com"})
        payload = handler.decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["email"] == "test@test.com"

    def test_token_has_expiry(self) -> None:
        """토큰에 만료 시간이 있다."""
        handler = JWTHandler(secret=TEST_SECRET, expire_minutes=30)
        token = handler.create_token({"sub": "user-1"})
        payload = handler.decode_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token_raises(self) -> None:
        """만료된 토큰 디코딩 시 예외."""
        handler = JWTHandler(secret=TEST_SECRET, expire_minutes=-1)
        token = handler.create_token({"sub": "user-1"})
        with pytest.raises(pyjwt.ExpiredSignatureError):
            handler.decode_token(token)

    def test_invalid_token_raises(self) -> None:
        """변조된 토큰 디코딩 시 예외."""
        handler = JWTHandler(secret=TEST_SECRET)
        with pytest.raises(pyjwt.InvalidTokenError):
            handler.decode_token("invalid.token.here")

    def test_wrong_secret_raises(self) -> None:
        """다른 시크릿으로 디코딩 시 예외."""
        handler1 = JWTHandler(secret="secret-1")
        handler2 = JWTHandler(secret="secret-2")
        token = handler1.create_token({"sub": "user-1"})
        with pytest.raises(pyjwt.InvalidSignatureError):
            handler2.decode_token(token)

    def test_empty_secret_raises(self) -> None:
        """빈 시크릿은 ValueError."""
        with pytest.raises(ValueError, match="비어있을 수 없습니다"):
            JWTHandler(secret="")

    def test_refresh_token_has_type(self) -> None:
        """리프레시 토큰에 type=refresh 포함."""
        handler = JWTHandler(secret=TEST_SECRET)
        token = handler.create_refresh_token({"sub": "user-1"})
        payload = handler.decode_token(token)
        assert payload["type"] == "refresh"

    def test_refresh_token_longer_expiry(self) -> None:
        """리프레시 토큰은 액세스 토큰보다 만료 시간이 길다."""
        handler = JWTHandler(secret=TEST_SECRET, expire_minutes=60)
        access = handler.create_token({"sub": "user-1"})
        refresh = handler.create_refresh_token({"sub": "user-1"})
        access_exp = handler.decode_token(access)["exp"]
        refresh_exp = handler.decode_token(refresh)["exp"]
        assert refresh_exp > access_exp


# ── Integration 테스트: User 모델 ──


@pytest.mark.integration
class TestUserModel:
    """User 모델 DB 통합 테스트."""

    async def test_create_user(self, db_session: AsyncSession) -> None:
        """User 생성 및 조회."""
        user = User(
            email="test@naruu.jp",
            hashed_password=hash_password("password123"),
            full_name="YAMADA NARUMI",
            role="admin",
        )
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(select(User).where(User.email == "test@naruu.jp"))
        saved = result.scalar_one()
        assert saved.full_name == "YAMADA NARUMI"
        assert saved.role == "admin"
        assert saved.is_active is True
        assert saved.id is not None

    async def test_unique_email_constraint(self, db_session: AsyncSession) -> None:
        """중복 이메일 시 에러."""
        user1 = User(
            email="dup@naruu.jp",
            hashed_password="hash1",
            full_name="User 1",
        )
        user2 = User(
            email="dup@naruu.jp",
            hashed_password="hash2",
            full_name="User 2",
        )
        db_session.add(user1)
        await db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_user_default_role(self, db_session: AsyncSession) -> None:
        """기본 role은 'staff'."""
        user = User(
            email="staff@naruu.jp",
            hashed_password="hash",
            full_name="Staff User",
        )
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(select(User).where(User.email == "staff@naruu.jp"))
        saved = result.scalar_one()
        assert saved.role == "staff"

    async def test_users_table_exists(self, db_engine: AsyncEngine) -> None:
        """users 테이블이 존재한다."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            )
            assert result.scalar() == "users"


# ── Smoke 테스트 ──


@pytest.mark.smoke
class TestAuthSmoke:
    """인증 시스템 스모크 테스트."""

    def test_jwt_roundtrip(self) -> None:
        """JWT 생성 → 디코딩 왕복 성공."""
        handler = JWTHandler(secret=TEST_SECRET)
        data = {"sub": "user-1", "email": "test@test.com", "role": "admin"}
        token = handler.create_token(data)
        decoded = handler.decode_token(token)
        assert decoded["sub"] == data["sub"]
        assert decoded["email"] == data["email"]

    def test_password_roundtrip(self) -> None:
        """비밀번호 해싱 → 검증 왕복 성공."""
        password = "naruu-secure-2024"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False
