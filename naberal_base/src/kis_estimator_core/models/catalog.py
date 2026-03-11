"""
AI 최적화 카탈로그 모델
Contract-First + Type-Safe + AI-Friendly

목표:
1. 타입 안정성 (Pydantic 검증)
2. 빠른 검색 (인덱싱)
3. AI 친화적 (명확한 필드명)
4. 확장 가능 (버전 관리)
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Import Enums from SSOT (LAW-02: Single Source of Truth)
from kis_estimator_core.core.ssot.enums import (
    Brand,
    BreakerCategory,
    BreakerSeries,
    EnclosureMaterial,
    EnclosureType,
)
from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# ============================================================================
# AI 최적화 모델 (명확한 필드명 + 타입)
# ============================================================================


class BreakerDimensions(BaseModel):
    """차단기 치수 (AI가 직접 접근)"""

    width_mm: int = Field(..., description="폭 (mm)")
    height_mm: int = Field(..., description="높이 (mm)")
    depth_mm: int = Field(..., description="깊이 (mm)")


class CatalogBreakerItem(BaseModel):
    """
    차단기 카탈로그 아이템 (AI 최적화)

    특징:
    - 모든 필드 명확한 이름
    - 타입 강제 (validation)
    - 검색 키워드 자동 생성
    """

    # 기본 정보
    category: BreakerCategory = Field(..., description="MCCB or ELB")
    brand: Brand = Field(..., description="제조사")
    series: BreakerSeries = Field(..., description="경제형 or 표준형")
    model: str = Field(..., description="모델명 (예: SBS-52)")

    # 사양
    poles: Literal[2, 3, 4] = Field(..., description="극수 (2P/3P/4P)")
    current_a: int = Field(..., gt=0, description="정격전류 (A)")
    frame_af: int = Field(..., gt=0, description="프레임 크기 (AF)")
    breaking_capacity_ka: float = Field(..., gt=0, description="차단용량 (kA)")

    # 가격 및 치수
    price: int = Field(..., ge=0, description="견적가 (원)")
    dimensions: BreakerDimensions = Field(..., description="차단기 치수")

    # 메타데이터 (AI 검색용)
    search_keywords: list[str] = Field(
        default_factory=list, description="검색 키워드 (자동 생성)"
    )

    # 원본 정보 (추적용)
    source_line: int | None = Field(None, description="원본 CSV 라인 번호")
    notes: str | None = Field(None, description="주석")

    def __init__(self, **data):
        super().__init__(**data)
        # 검색 키워드 자동 생성
        if not self.search_keywords:
            self.search_keywords = [
                self.model.upper(),
                f"{self.poles}P",
                f"{self.current_a}A",
                f"{self.frame_af}AF",
                self.category.value,
                self.series.value,
                self.brand.value,
            ]

    @field_validator("current_a", "frame_af")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise_error(ErrorCode.E_INTERNAL, "전류와 프레임은 양수여야 합니다")
        return v


class CatalogEnclosureItem(BaseModel):
    """
    외함 카탈로그 아이템 (AI 최적화)
    """

    # 기본 정보
    type: EnclosureType = Field(..., description="외함 종류")
    material: EnclosureMaterial = Field(..., description="재질")
    brand: Brand = Field(..., description="제조사")
    model: str = Field(..., description="모델명 (예: HB304015)")

    # 치수
    width_mm: int = Field(..., gt=0, description="폭 (mm)")
    height_mm: int = Field(..., gt=0, description="높이 (mm)")
    depth_mm: int = Field(..., ge=0, description="깊이 (mm)")  # ge=0: JSON에 depth_mm=0인 항목 허용

    # 가격
    price: int = Field(..., ge=0, description="견적가 (원)")

    # 메타데이터
    search_keywords: list[str] = Field(default_factory=list, description="검색 키워드")
    source_line: int | None = Field(None, description="원본 CSV 라인 번호")
    notes: str | None = Field(None, description="주석")

    def __init__(self, **data):
        super().__init__(**data)
        # 검색 키워드 자동 생성
        if not self.search_keywords:
            self.search_keywords = [
                self.model.upper(),
                f"{self.width_mm}x{self.height_mm}x{self.depth_mm}",
                self.type.value,
                self.material.value,
                self.brand.value,
            ]


class AICatalog(BaseModel):
    """
    AI 최적화 카탈로그 (루트 모델)

    특징:
    - 카테고리별 분리 (빠른 검색)
    - 버전 관리
    - 메타데이터 포함
    """

    version: str = Field(..., description="카탈로그 버전")
    created_at: str = Field(..., description="생성 시각 (ISO 8601)")
    source_file: str = Field(..., description="원본 파일명")

    # 데이터
    breakers: list[CatalogBreakerItem] = Field(
        default_factory=list, description="차단기 목록"
    )
    enclosures: list[CatalogEnclosureItem] = Field(
        default_factory=list, description="외함 목록"
    )

    # 통계
    total_items: int = Field(0, description="총 아이템 수")
    breaker_count: int = Field(0, description="차단기 수")
    enclosure_count: int = Field(0, description="외함 수")

    def __init__(self, **data):
        super().__init__(**data)
        # 통계 자동 계산
        self.breaker_count = len(self.breakers)
        self.enclosure_count = len(self.enclosures)
        self.total_items = self.breaker_count + self.enclosure_count


# ============================================================================
# 검색 헬퍼 (AI가 사용하기 쉬운 인터페이스)
# ============================================================================


class BreakerSearchQuery(BaseModel):
    """차단기 검색 쿼리"""

    category: BreakerCategory | None = None
    brand: Brand | None = None
    series: BreakerSeries | None = None
    poles: Literal[2, 3, 4] | None = None
    current_a: int | None = None
    frame_af: int | None = None
    model: str | None = None


class EnclosureSearchQuery(BaseModel):
    """외함 검색 쿼리"""

    type: EnclosureType | None = None
    material: EnclosureMaterial | None = None
    brand: Brand | None = None
    min_width: int | None = None
    max_width: int | None = None
    min_height: int | None = None
    max_height: int | None = None
    min_depth: int | None = None
    max_depth: int | None = None
