"""
Enclosure Solver 모델 정의
SPEC: .specify/specs/phase1-fix4-pipeline.md
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


class BreakerSpec(BaseModel):
    """차단기 사양"""

    id: str = Field(..., description="차단기 ID")
    model: str = Field(..., description="모델명 (예: SBE-102)")
    poles: int = Field(..., ge=2, le=4, description="극수 (2P/3P/4P)")
    current_a: int = Field(..., gt=0, description="정격 전류 (A)")
    frame_af: int = Field(..., gt=0, description="프레임 크기 (AF)")

    @field_validator("poles")
    @classmethod
    def validate_poles(cls, v):
        if v not in [2, 3, 4]:
            raise_error(ErrorCode.E_INTERNAL, "극수는 2, 3, 4만 가능합니다")
        return v


class AccessorySpec(BaseModel):
    """부속자재 사양"""

    type: str = Field(..., description="자재 유형 (magnet, timer 등)")
    model: str = Field(..., description="모델명 (예: MC-22)")
    quantity: int = Field(..., gt=0, description="수량")


class CustomerRequirements(BaseModel):
    """고객 요구사항"""

    enclosure_type: str = Field(..., description="외함 종류 (옥내자립, 옥외자립 등)")
    ip_rating: str | None = Field(None, description="IP 등급")
    material: str | None = Field(None, description="재질")


class EnclosureSpec(BaseModel):
    """외함 계산 입력 사양"""

    breakers: list[BreakerSpec] = Field(..., min_length=1, description="차단기 목록")
    accessories: list[AccessorySpec] = Field(
        default_factory=list, description="부속자재 목록"
    )
    customer_requirements: CustomerRequirements = Field(
        ..., description="고객 요구사항"
    )

    @field_validator("breakers")
    @classmethod
    def validate_breakers(cls, v):
        if not v:
            raise_error(
                ErrorCode.E_INTERNAL, "차단기 목록은 최소 1개 이상이어야 합니다"
            )
        return v


class EnclosureDimensions(BaseModel):
    """계산된 외함 치수"""

    width_mm: int = Field(..., gt=0, description="폭 (mm)")
    height_mm: int = Field(..., gt=0, description="높이 (mm)")
    depth_mm: int = Field(..., gt=0, description="깊이 (mm)")

    # 계산 상세
    top_margin: int | None = Field(None, description="상단 여유 (mm)")
    breaker_heights: int | None = Field(None, description="차단기 총 높이 (mm)")
    bottom_margin: int | None = Field(None, description="하단 여유 (mm)")
    accessory_heights: int | None = Field(None, description="부속자재 여유 (mm)")


class EnclosureCandidate(BaseModel):
    """HDS 카탈로그 후보"""

    model: str = Field(..., description="모델명 (예: HB607020)")
    size_mm: tuple[int, int, int] = Field(..., description="치수 (W, H, D)")
    price: int = Field(..., ge=0, description="단가 (원)")
    match_type: str = Field(..., description="매칭 타입 (exact/nearest)")
    material: str = Field(..., description="재질 (steel, sus)")
    install_location: str = Field(..., description="설치 위치 (indoor/outdoor)")


class QualityGateResult(BaseModel):
    """품질 게이트 검증 결과"""

    name: str = Field(..., description="게이트 이름")
    passed: bool = Field(..., description="통과 여부")
    actual: Any = Field(..., description="실제 값")
    threshold: Any = Field(..., description="기준 값")
    operator: str = Field(..., description="비교 연산자 (>=, <=, ==)")
    critical: bool = Field(..., description="필수 여부")


class EnclosureResult(BaseModel):
    """외함 계산 결과 (Task 7 구현 기준)"""

    # 계산된 치수
    dimensions: EnclosureDimensions = Field(..., description="계산된 요구 치수")

    # HDS 카탈로그 후보 목록
    candidates: list[EnclosureCandidate] = Field(
        default_factory=list, description="매칭된 HDS 카탈로그 후보"
    )

    # 품질 게이트
    quality_gate: QualityGateResult = Field(..., description="품질 게이트 결과")

    # 계산 상세 내역
    calculation_details: dict[str, Any] = Field(
        default_factory=dict, description="계산 과정 상세"
    )

    # 외함 종류 및 재질 (고객 요구사항에서 전달받음) - 필수 필드
    enclosure_type: str = Field(
        ..., description="외함 종류 (옥내노출, 옥외노출, 옥내자립, 옥외자립 등)"
    )
    material: str = Field(
        ..., description="재질 (STEEL 1.0T, STEEL 1.6T, SUS201 1.2T, SUS304 1.2T)"
    )
