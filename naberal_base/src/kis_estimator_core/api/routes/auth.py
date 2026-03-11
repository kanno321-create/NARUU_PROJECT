"""
인증 API 라우터
JWT 기반 로그인/로그아웃 + 사용자 관리

엔드포인트:
- POST /v1/auth/login     - 로그인
- POST /v1/auth/logout    - 로그아웃
- POST /v1/auth/refresh   - 토큰 갱신
- GET  /v1/auth/me        - 현재 사용자 정보
- GET  /v1/users          - 사용자 목록 (CEO)
- POST /v1/users          - 사용자 생성 (CEO)
- PUT  /v1/users/{id}     - 사용자 수정 (CEO)
- DELETE /v1/users/{id}   - 사용자 삭제 (CEO)
- PUT  /v1/users/{id}/password - 비밀번호 변경
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from kis_estimator_core.models.user import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    UserListResponse,
    CurrentUser,
)
from kis_estimator_core.services import auth_service

logger = logging.getLogger(__name__)

# ============================================================================
# 라우터 설정
# ============================================================================

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Rate Limiter 초기화 (IP 기반)
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# 의존성
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> CurrentUser:
    """현재 인증된 사용자 추출"""
    token = None

    # Bearer 토큰 추출
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await auth_service.get_current_user_from_token_async(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> Optional[CurrentUser]:
    """현재 사용자 (선택적)"""
    try:
        return await get_current_user(credentials, authorization)
    except HTTPException:
        return None


async def require_ceo(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """CEO 권한 필요"""
    if not current_user.is_ceo():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CEO 권한이 필요합니다"
        )
    return current_user


# ============================================================================
# 인증 엔드포인트
# ============================================================================

@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="로그인",
    description="사용자명과 비밀번호로 로그인하여 JWT 토큰 발급"
)
@limiter.limit("5/minute")
async def login(request: Request, login_request: LoginRequest):
    """로그인"""
    result = await auth_service.login_async(login_request.username, login_request.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다"
        )

    return result


@router.post(
    "/auth/logout",
    summary="로그아웃",
    description="현재 세션 로그아웃 (클라이언트에서 토큰 삭제)"
)
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """로그아웃"""
    # JWT는 stateless이므로 서버에서 할 일 없음
    # 클라이언트에서 토큰 삭제
    logger.info(f"로그아웃: {current_user.username}")
    return {"message": "로그아웃 성공", "username": current_user.username}


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="토큰 갱신",
    description="리프레시 토큰으로 새 액세스 토큰 발급"
)
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest):
    """토큰 갱신"""
    result = await auth_service.refresh_tokens_async(refresh_request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다"
        )

    return result


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="현재 사용자 정보",
    description="현재 로그인한 사용자 정보 조회"
)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """현재 사용자 정보"""
    user = await auth_service.get_user_by_id_async(current_user.id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

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
# 사용자 관리 엔드포인트 (CEO 전용)
# ============================================================================

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="사용자 목록",
    description="전체 사용자 목록 조회 (CEO 전용)"
)
async def list_users(current_user: CurrentUser = Depends(require_ceo)):
    """사용자 목록"""
    users = await auth_service.get_all_users_async()
    return UserListResponse(users=users, total=len(users))


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성",
    description="새 사용자 생성 (CEO 전용)"
)
async def create_user(
    request: UserCreate,
    current_user: CurrentUser = Depends(require_ceo)
):
    """사용자 생성"""
    result = await auth_service.create_user_async(request)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자명입니다"
        )

    return result


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 조회",
    description="특정 사용자 정보 조회 (CEO 전용)"
)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_ceo)
):
    """사용자 조회"""
    user = await auth_service.get_user_by_id_async(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 수정",
    description="사용자 정보 수정 (CEO 전용)"
)
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: CurrentUser = Depends(require_ceo)
):
    """사용자 수정"""
    result = await auth_service.update_user_async(user_id, request)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    return result


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="사용자 삭제",
    description="사용자 삭제 (CEO 전용, CEO 계정은 삭제 불가)"
)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_ceo)
):
    """사용자 삭제"""
    # 자기 자신 삭제 방지
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )

    success = await auth_service.delete_user_async(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자를 삭제할 수 없습니다 (CEO 계정이거나 존재하지 않음)"
        )

    return None


@router.put(
    "/users/{user_id}/password",
    summary="비밀번호 변경",
    description="사용자 비밀번호 변경 (본인 또는 CEO)"
)
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    user_id: str,
    password_request: UserPasswordChange,
    current_user: CurrentUser = Depends(get_current_user)
):
    """비밀번호 변경"""
    # 본인 또는 CEO만 가능
    if user_id != current_user.id and not current_user.is_ceo():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비밀번호 변경 권한이 없습니다"
        )

    success = await auth_service.change_password_async(user_id, password_request, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호 변경에 실패했습니다"
        )

    return {"message": "비밀번호가 변경되었습니다"}
