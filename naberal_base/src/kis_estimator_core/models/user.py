"""
사용자 인증 모델
Contract-First + JWT + bcrypt 기반 인증 시스템

Phase 1 보안 구현:
- bcrypt 비밀번호 해싱
- JWT 토큰 기반 인증
- 역할 기반 접근 제어 (RBAC)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    """사용자 역할"""
    CEO = "ceo"           # 대표이사 - 전체 권한
    MANAGER = "manager"   # 관리자 - 사용자 관리 제외 전체 권한
    STAFF = "staff"       # 직원 - 기본 권한
    CUSTOMER = "customer" # 고객 - 포털 접근 전용


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# ============================================================================
# 사용자 모델
# ============================================================================

class UserBase(BaseModel):
    """사용자 기본 정보"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    name: str = Field(..., min_length=1, max_length=100, description="실명")
    role: UserRole = Field(default=UserRole.STAFF, description="역할")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """사용자명 검증 (영문, 숫자, 언더스코어만)"""
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다")
        return v.lower()


class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """비밀번호 정책 검증 (보안 강화)"""
        import re

        errors = []

        if len(v) < 8:
            errors.append("최소 8자 이상")
        if len(v) > 100:
            errors.append("최대 100자 이하")
        if not re.search(r'[A-Z]', v):
            errors.append("대문자 1개 이상")
        if not re.search(r'[a-z]', v):
            errors.append("소문자 1개 이상")
        if not re.search(r'\d', v):
            errors.append("숫자 1개 이상")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("특수문자 1개 이상 (!@#$%^&*(),.?\":{}|<>)")

        # 연속 문자/숫자 3개 이상 금지 (예: 123, abc)
        if re.search(r'(012|123|234|345|456|567|678|789|890)', v):
            errors.append("연속 숫자 3개 이상 금지")
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', v.lower()):
            errors.append("연속 알파벳 3개 이상 금지")

        if errors:
            raise ValueError(f"비밀번호 정책 위반: {', '.join(errors)}")

        return v


class CustomerSignupRequest(BaseModel):
    """고객 회원가입 요청 (공개 API)"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    name: str = Field(..., min_length=1, max_length=100, description="이름")
    company: str = Field(default="", max_length=200, description="회사명")
    phone: str = Field(default="", max_length=20, description="연락처")
    email: str = Field(default="", max_length=200, description="이메일")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다")
        return v


class UserUpdate(BaseModel):
    """사용자 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserPasswordChange(BaseModel):
    """비밀번호 변경 요청"""
    current_password: Optional[str] = Field(None, description="현재 비밀번호 (본인 변경 시)")
    new_password: str = Field(..., min_length=8, max_length=100, description="새 비밀번호")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """비밀번호 정책 검증 (보안 강화) - UserCreate와 동일"""
        import re

        errors = []

        if len(v) < 8:
            errors.append("최소 8자 이상")
        if len(v) > 100:
            errors.append("최대 100자 이하")
        if not re.search(r'[A-Z]', v):
            errors.append("대문자 1개 이상")
        if not re.search(r'[a-z]', v):
            errors.append("소문자 1개 이상")
        if not re.search(r'\d', v):
            errors.append("숫자 1개 이상")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("특수문자 1개 이상 (!@#$%^&*(),.?\":{}|<>)")

        # 연속 문자/숫자 3개 이상 금지 (예: 123, abc)
        if re.search(r'(012|123|234|345|456|567|678|789|890)', v):
            errors.append("연속 숫자 3개 이상 금지")
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', v.lower()):
            errors.append("연속 알파벳 3개 이상 금지")

        if errors:
            raise ValueError(f"비밀번호 정책 위반: {', '.join(errors)}")

        return v


class UserInDB(UserBase):
    """DB에 저장되는 사용자 모델"""
    id: str = Field(..., description="사용자 ID (UUID)")
    hashed_password: str = Field(..., description="해싱된 비밀번호")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="상태")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성일시")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정일시")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")


class UserResponse(BaseModel):
    """사용자 응답 (비밀번호 제외)"""
    id: str
    username: str
    name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    users: list[UserResponse]
    total: int


# ============================================================================
# 인증 모델
# ============================================================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호")


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간 (초)")


class TokenPayload(BaseModel):
    """JWT 토큰 페이로드"""
    sub: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    role: UserRole = Field(..., description="역할")
    exp: int = Field(..., description="만료 시간 (Unix timestamp)")
    iat: int = Field(..., description="발급 시간 (Unix timestamp)")
    type: str = Field(..., description="토큰 타입 (access/refresh)")


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class CurrentUser(BaseModel):
    """현재 인증된 사용자"""
    id: str
    username: str
    name: str
    role: UserRole

    def is_ceo(self) -> bool:
        """CEO 권한 확인"""
        return self.role == UserRole.CEO

    def is_manager_or_above(self) -> bool:
        """관리자 이상 권한 확인"""
        return self.role in [UserRole.CEO, UserRole.MANAGER]

    def can_manage_users(self) -> bool:
        """사용자 관리 권한 확인 (CEO만)"""
        return self.role == UserRole.CEO

    def is_customer(self) -> bool:
        """고객 여부 확인"""
        return self.role == UserRole.CUSTOMER

    def is_internal(self) -> bool:
        """내부 사용자 여부 확인"""
        return self.role in [UserRole.CEO, UserRole.MANAGER, UserRole.STAFF]
