"""
인증 서비스 (PostgreSQL 기반)
bcrypt 해싱 + JWT 토큰 + PostgreSQL 영구 저장

Phase 2 구현:
- PostgreSQL users 테이블 사용 (인메모리 제거)
- Railway 재배포에도 사용자 데이터 유지
- bcrypt 비밀번호 해싱 (솔트 자동 생성)
- JWT Access Token (15분) / Refresh Token (7일)
"""

import os
import time
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text

from kis_estimator_core.models.user import (
    UserRole,
    UserStatus,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    UserPasswordChange,
    TokenPayload,
    TokenResponse,
    CurrentUser,
)
from kis_estimator_core.infra.db import get_db_instance

logger = logging.getLogger(__name__)

# ============================================================================
# 설정
# ============================================================================

def _get_jwt_secret() -> str:
    """JWT 시크릿 키 조회 (환경변수 필수)"""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
    if len(secret) < 32:
        raise ValueError("JWT_SECRET_KEY는 최소 32자 이상이어야 합니다.")
    return secret

SECRET_KEY = _get_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# bcrypt 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB 스키마
SCHEMA = "kis_beta"


# ============================================================================
# 비밀번호 해싱
# ============================================================================

def hash_password(password: str) -> str:
    """비밀번호 bcrypt 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT 토큰
# ============================================================================

def create_access_token(user: UserInDB) -> str:
    """액세스 토큰 생성 (15분)"""
    now = int(time.time())
    expire = now + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: UserInDB) -> str:
    """리프레시 토큰 생성 (7일)"""
    now = int(time.time())
    expire = now + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """토큰 디코딩 및 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            username=payload["username"],
            role=UserRole(payload["role"]),
            exp=payload["exp"],
            iat=payload["iat"],
            type=payload["type"]
        )
    except JWTError as e:
        logger.warning(f"토큰 디코딩 실패: {e}")
        return None


def verify_access_token(token: str) -> Optional[TokenPayload]:
    """액세스 토큰 검증"""
    payload = decode_token(token)
    if payload and payload.type == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[TokenPayload]:
    """리프레시 토큰 검증"""
    payload = decode_token(token)
    if payload and payload.type == "refresh":
        return payload
    return None


# ============================================================================
# 동기 DB 헬퍼 (FastAPI 라우터용)
# ============================================================================

def _run_sync(coro):
    """코루틴을 동기적으로 실행"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 이미 이벤트 루프가 실행 중이면 새 스레드에서 실행
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


# ============================================================================
# 사용자 CRUD (PostgreSQL)
# ============================================================================

async def _get_user_by_id_async(user_id: str) -> Optional[UserInDB]:
    """ID로 사용자 조회 (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text(f"SELECT * FROM {SCHEMA}.users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        if row:
            return _row_to_user(row)
    return None


async def _get_user_by_username_async(username: str) -> Optional[UserInDB]:
    """사용자명으로 조회 (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text(f"SELECT * FROM {SCHEMA}.users WHERE username = :username"),
            {"username": username.lower()}
        )
        row = result.fetchone()
        if row:
            return _row_to_user(row)
    return None


async def _get_all_users_async() -> list[UserResponse]:
    """전체 사용자 목록 (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text(f"SELECT * FROM {SCHEMA}.users ORDER BY created_at DESC")
        )
        rows = result.fetchall()
        return [_row_to_response(row) for row in rows]


async def _create_user_async(data: UserCreate) -> Optional[UserResponse]:
    """사용자 생성 (async)"""
    # 중복 검사
    existing = await _get_user_by_username_async(data.username)
    if existing:
        logger.warning(f"사용자 생성 실패: 중복 사용자명 - {data.username}")
        return None

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(data.password)

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text(f"""
                INSERT INTO {SCHEMA}.users (id, username, name, hashed_password, role, status)
                VALUES (:id, :username, :name, :hashed_password, :role, :status)
            """),
            {
                "id": user_id,
                "username": data.username.lower(),
                "name": data.name,
                "hashed_password": hashed_pw,
                "role": data.role.value,
                "status": UserStatus.ACTIVE.value
            }
        )

    logger.info(f"사용자 생성: {data.username} ({data.role.value})")
    user = await _get_user_by_id_async(user_id)
    if user:
        return _user_to_response(user)
    return None


async def _update_user_async(user_id: str, data: UserUpdate) -> Optional[UserResponse]:
    """사용자 수정 (async)"""
    user = await _get_user_by_id_async(user_id)
    if not user:
        return None

    updates = []
    params = {"user_id": user_id}

    if data.name is not None:
        updates.append("name = :name")
        params["name"] = data.name
    if data.role is not None:
        updates.append("role = :role")
        params["role"] = data.role.value
    if data.status is not None:
        updates.append("status = :status")
        params["status"] = data.status.value

    if not updates:
        return _user_to_response(user)

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text(f"UPDATE {SCHEMA}.users SET {', '.join(updates)} WHERE id = :user_id"),
            params
        )

    logger.info(f"사용자 수정: {user.username}")
    updated_user = await _get_user_by_id_async(user_id)
    if updated_user:
        return _user_to_response(updated_user)
    return None


async def _delete_user_async(user_id: str) -> bool:
    """사용자 삭제 (async)"""
    user = await _get_user_by_id_async(user_id)
    if not user:
        return False

    if user.role == UserRole.CEO:
        logger.warning(f"사용자 삭제 실패: CEO 계정은 삭제할 수 없습니다 - {user.username}")
        return False

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text(f"DELETE FROM {SCHEMA}.users WHERE id = :user_id"),
            {"user_id": user_id}
        )

    logger.info(f"사용자 삭제: {user.username}")
    return True


async def _change_password_async(user_id: str, data: UserPasswordChange, requester: CurrentUser) -> bool:
    """비밀번호 변경 (async)"""
    user = await _get_user_by_id_async(user_id)
    if not user:
        return False

    # CEO가 아닌 경우 본인만 변경 가능
    if not requester.is_ceo() and requester.id != user_id:
        logger.warning(f"비밀번호 변경 실패: 권한 없음 - {requester.username}")
        return False

    # 본인 변경 시 현재 비밀번호 확인 (CEO는 스킵)
    if requester.id == user_id and not requester.is_ceo():
        if not data.current_password:
            return False
        if not verify_password(data.current_password, user.hashed_password):
            logger.warning(f"비밀번호 변경 실패: 현재 비밀번호 불일치 - {user.username}")
            return False

    new_hashed = hash_password(data.new_password)

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text(f"UPDATE {SCHEMA}.users SET hashed_password = :hashed_password WHERE id = :user_id"),
            {"hashed_password": new_hashed, "user_id": user_id}
        )

    logger.info(f"비밀번호 변경: {user.username}")
    return True


async def _update_last_login_async(user_id: str):
    """마지막 로그인 시간 업데이트 (async)"""
    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text(f"UPDATE {SCHEMA}.users SET last_login = timezone('utc', now()) WHERE id = :user_id"),
            {"user_id": user_id}
        )


# ============================================================================
# 헬퍼 함수
# ============================================================================

def _row_to_user(row) -> UserInDB:
    """DB row를 UserInDB로 변환"""
    return UserInDB(
        id=row.id,
        username=row.username,
        name=row.name,
        hashed_password=row.hashed_password,
        role=UserRole(row.role),
        status=UserStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_login=row.last_login
    )


def _row_to_response(row) -> UserResponse:
    """DB row를 UserResponse로 변환"""
    return UserResponse(
        id=row.id,
        username=row.username,
        name=row.name,
        role=UserRole(row.role),
        status=UserStatus(row.status),
        created_at=row.created_at,
        last_login=row.last_login
    )


def _user_to_response(user: UserInDB) -> UserResponse:
    """UserInDB를 UserResponse로 변환"""
    return UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )


# ============================================================================
# 동기 API (라우터용 - 기존 인터페이스 유지)
# ============================================================================

def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """ID로 사용자 조회"""
    return _run_sync(_get_user_by_id_async(user_id))


def get_user_by_username(username: str) -> Optional[UserInDB]:
    """사용자명으로 조회"""
    return _run_sync(_get_user_by_username_async(username))


def get_all_users() -> list[UserResponse]:
    """전체 사용자 목록"""
    return _run_sync(_get_all_users_async())


def create_user(data: UserCreate) -> Optional[UserResponse]:
    """사용자 생성 (CEO 전용)"""
    return _run_sync(_create_user_async(data))


def update_user(user_id: str, data: UserUpdate) -> Optional[UserResponse]:
    """사용자 수정 (CEO 전용)"""
    return _run_sync(_update_user_async(user_id, data))


def delete_user(user_id: str) -> bool:
    """사용자 삭제 (CEO 전용)"""
    return _run_sync(_delete_user_async(user_id))


def change_password(user_id: str, data: UserPasswordChange, requester: CurrentUser) -> bool:
    """비밀번호 변경"""
    return _run_sync(_change_password_async(user_id, data, requester))


# ============================================================================
# 사용자 인증
# ============================================================================

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """사용자 인증"""
    user = get_user_by_username(username)

    if not user:
        logger.warning(f"로그인 실패: 존재하지 않는 사용자 - {username}")
        return None

    if user.status != UserStatus.ACTIVE:
        logger.warning(f"로그인 실패: 비활성 사용자 - {username}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"로그인 실패: 비밀번호 불일치 - {username}")
        return None

    # 마지막 로그인 시간 업데이트
    _run_sync(_update_last_login_async(user.id))
    logger.info(f"로그인 성공: {username}")

    return user


def login(username: str, password: str) -> Optional[TokenResponse]:
    """로그인 처리"""
    user = authenticate_user(username, password)

    if not user:
        return None

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def refresh_tokens(refresh_token: str) -> Optional[TokenResponse]:
    """토큰 갱신"""
    payload = verify_refresh_token(refresh_token)

    if not payload:
        return None

    user = get_user_by_id(payload.sub)

    if not user or user.status != UserStatus.ACTIVE:
        return None

    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def get_current_user_from_token(token: str) -> Optional[CurrentUser]:
    """토큰에서 현재 사용자 추출"""
    payload = verify_access_token(token)

    if not payload:
        return None

    user = get_user_by_id(payload.sub)

    if not user or user.status != UserStatus.ACTIVE:
        return None

    return CurrentUser(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role
    )


# ============================================================================
# Async API (FastAPI 라우터에서 직접 호출)
# ============================================================================

async def authenticate_user_async(username: str, password: str) -> Optional[UserInDB]:
    """사용자 인증 (async)"""
    user = await _get_user_by_username_async(username)

    if not user:
        logger.warning(f"로그인 실패: 존재하지 않는 사용자 - {username}")
        return None

    if user.status != UserStatus.ACTIVE:
        logger.warning(f"로그인 실패: 비활성 사용자 - {username}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"로그인 실패: 비밀번호 불일치 - {username}")
        return None

    # 마지막 로그인 시간 업데이트
    await _update_last_login_async(user.id)
    logger.info(f"로그인 성공: {username}")

    return user


async def login_async(username: str, password: str) -> Optional[TokenResponse]:
    """로그인 처리 (async)"""
    user = await authenticate_user_async(username, password)

    if not user:
        return None

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


async def refresh_tokens_async(refresh_token: str) -> Optional[TokenResponse]:
    """토큰 갱신 (async)"""
    payload = verify_refresh_token(refresh_token)

    if not payload:
        return None

    user = await _get_user_by_id_async(payload.sub)

    if not user or user.status != UserStatus.ACTIVE:
        return None

    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


async def get_current_user_from_token_async(token: str) -> Optional[CurrentUser]:
    """토큰에서 현재 사용자 추출 (async)"""
    payload = verify_access_token(token)

    if not payload:
        return None

    user = await _get_user_by_id_async(payload.sub)

    if not user or user.status != UserStatus.ACTIVE:
        return None

    return CurrentUser(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role
    )


async def get_user_by_id_async(user_id: str) -> Optional[UserInDB]:
    """ID로 사용자 조회 (async)"""
    return await _get_user_by_id_async(user_id)


async def get_all_users_async() -> list[UserResponse]:
    """전체 사용자 목록 (async)"""
    return await _get_all_users_async()


async def create_user_async(data: UserCreate) -> Optional[UserResponse]:
    """사용자 생성 (async)"""
    return await _create_user_async(data)


async def update_user_async(user_id: str, data: UserUpdate) -> Optional[UserResponse]:
    """사용자 수정 (async)"""
    return await _update_user_async(user_id, data)


async def delete_user_async(user_id: str) -> bool:
    """사용자 삭제 (async)"""
    return await _delete_user_async(user_id)


async def change_password_async(user_id: str, data: UserPasswordChange, requester: CurrentUser) -> bool:
    """비밀번호 변경 (async)"""
    return await _change_password_async(user_id, data, requester)
