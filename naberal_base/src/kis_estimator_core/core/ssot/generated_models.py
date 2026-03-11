"""
SSOT DTO Models - 정규화된 Pydantic 모델

I-3.2b: BOM 단계에서 dict → DTO 타입 안전 변환

생성 원본: scripts/generate_ssot_wrappers.py
절대 원칙: 수동 수정 금지 (스크립트 재생성으로만 변경)
"""

from typing import Literal

from pydantic import BaseModel, Field, validator


# ============================================================
# Breaker DTO
# ============================================================
class BreakerInput(BaseModel):
    """
    차단기 입력 DTO (SSOT 정규화)

    I-3.2b: dict → BreakerInput 변환으로 타입 안전성 보장
    """

    id: str = Field(..., description="차단기 ID (MAIN, BR1, BR2, ...)")
    model: str | None = Field(None, description="모델명 (SBE-102, SBS-54, ...)")
    frame_af: int = Field(
        ..., alias="frame", description="프레임 (32, 50, 100, 200, 400, 600, 800)"
    )
    current_a: int = Field(..., alias="current", description="정격전류 (A)")
    poles: int = Field(..., description="극수 (2, 3, 4)")
    width_mm: float | None = Field(None, description="폭 (mm)")
    height_mm: float | None = Field(None, description="높이 (mm)")
    depth_mm: float | None = Field(None, description="깊이 (mm)")
    breaker_type: str | None = Field(
        "normal", description="차단기 유형 (normal, elb, ...)"
    )
    type: Literal["MCCB", "ELB"] | None = Field("MCCB", description="차단기 종류")

    class Config:
        allow_population_by_field_name = True  # alias와 실제 필드명 둘 다 허용
        extra = "allow"  # 추가 필드 허용 (하위 호환)

    @validator("poles")
    def validate_poles(cls, v):
        """극수 검증 (2, 3, 4만 허용)"""
        if v not in [2, 3, 4]:
            raise ValueError(f"poles must be 2, 3, or 4, got {v}")
        return v

    @validator("frame_af")
    def validate_frame(cls, v):
        """프레임 검증 (표준 프레임만 허용)"""
        valid_frames = [32, 50, 60, 100, 125, 200, 225, 250, 400, 600, 800]
        if v not in valid_frames:
            raise ValueError(f"frame_af must be in {valid_frames}, got {v}")
        return v


# ============================================================
# Enclosure DTO
# ============================================================
class EnclosureDimensionsInput(BaseModel):
    """
    외함 치수 DTO

    I-3.2b: 외함 치수 정규화
    """

    width_mm: float = Field(..., description="폭 (mm)")
    height_mm: float = Field(..., description="높이 (mm)")
    depth_mm: float = Field(..., description="깊이 (mm)")

    class Config:
        extra = "forbid"  # 치수는 정확히 3개만 허용


class EnclosureInput(BaseModel):
    """
    외함 입력 DTO (SSOT 정규화)

    I-3.2b: dict → EnclosureInput 변환으로 타입 안전성 보장
    """

    id: str | None = Field(None, description="외함 ID")
    code: str | None = Field(None, description="외함 코드 (HDS-600*400*200)")
    size: EnclosureDimensionsInput | None = Field(
        None, description="외함 치수 {w, h, d}"
    )
    dimensions: EnclosureDimensionsInput | None = Field(
        None, description="외함 치수 (대체 필드)"
    )
    enclosure_type: str | None = Field(
        None, description="외함 종류 (옥내노출, 옥외노출, ...)"
    )
    material: str | None = Field(None, description="재질 (STEEL, SUS201, ...)")
    thickness: str | None = Field(None, description="두께 (1.6T, 1.2T, ...)")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"  # 추가 필드 허용 (EnclosureResult 호환)


# ============================================================
# Placement DTO (Optional)
# ============================================================
class PlacementInput(BaseModel):
    """
    배치 결과 DTO

    I-3.2b: 배치 결과 정규화
    """

    breaker_id: str = Field(..., description="차단기 ID")
    x: float = Field(..., description="X 좌표 (mm)")
    y: float = Field(..., description="Y 좌표 (mm)")
    phase: str | None = Field(None, description="상 배정 (R, S, T)")
    row: int | None = Field(None, description="행 번호")
    column: int | None = Field(None, description="열 번호")

    class Config:
        extra = "allow"
