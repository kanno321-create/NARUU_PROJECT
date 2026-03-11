"""
Learning System API Schemas (Phase XIII)

AI Self-Learning System의 Request/Response 스키마 정의
Contract-First 원칙에 따라 API 계약을 먼저 정의합니다.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Enums & Types
# ============================================================================

PatternCategory = Literal[
    "PRICE_ADJUSTMENT",   # 가격 조정 패턴
    "BRAND_PREFERENCE",   # 브랜드 선호도
    "LAYOUT_RULE",        # 레이아웃 규칙
    "MATERIAL_SWAP"       # 자재 교체 규칙
]

PreferenceCategory = Literal[
    "BRAND",    # 브랜드 선호도
    "PRICE",    # 가격 임계값
    "LAYOUT",   # 레이아웃 스타일
    "MATERIAL"  # 자재 선호도
]


# ============================================================================
# Estimate Modification Records
# ============================================================================

class EstimateModificationRecord(BaseModel):
    """견적 수정 레코드 스키마"""
    modification_id: str = Field(..., description="수정 ID (UUID)")
    estimate_id: str = Field(..., description="견적 ID")
    user_id: str = Field(..., description="수정자 ID (CEO)")
    modified_fields: list[str] = Field(..., description="수정된 필드 목록")
    diff: dict = Field(..., description="JSON Patch 형식 diff")
    reason: Optional[str] = Field(None, description="수정 사유")
    timestamp: datetime = Field(..., description="수정 시각")
    evidence_hash: str = Field(..., description="SHA256 무결성 해시")


class ModificationListResponse(BaseModel):
    """수정 이력 목록 응답"""
    modifications: list[EstimateModificationRecord]
    total: int
    meta: dict = Field(default_factory=dict)


# ============================================================================
# Pattern Detection
# ============================================================================

class PatternResponse(BaseModel):
    """학습된 패턴 응답 스키마"""
    pattern_id: str = Field(..., description="패턴 ID (UUID)")
    category: PatternCategory = Field(..., description="패턴 카테고리")
    condition: dict = Field(..., description="패턴 조건 (예: {breaker_af: '100AF', pole: '4P'})")
    action: dict = Field(..., description="패턴 액션 (예: {use_brand: 'LS산전', discount: 0.05})")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0 ~ 1.0)")
    occurrences: int = Field(..., ge=1, description="발생 횟수")
    last_seen: datetime = Field(..., description="마지막 발생 시각")

    class Config:
        from_attributes = True


class PatternsResponse(BaseModel):
    """패턴 목록 응답"""
    patterns: list[PatternResponse]
    total: int
    meta: dict = Field(default_factory=dict)


class ManualPatternRequest(BaseModel):
    """수동 패턴 생성 요청"""
    category: PatternCategory = Field(..., description="패턴 카테고리")
    condition: dict = Field(..., description="패턴 조건")
    action: dict = Field(..., description="패턴 액션")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="초기 신뢰도")
    reason: Optional[str] = Field(None, description="생성 사유")


class PatternCreateResponse(BaseModel):
    """패턴 생성 응답"""
    pattern_id: str
    category: PatternCategory
    message: str = "패턴이 생성되었습니다"


# ============================================================================
# CEO Profile
# ============================================================================

class CEOPreferenceItem(BaseModel):
    """CEO 선호도 항목"""
    category: PreferenceCategory
    key: str
    value: str | float | dict
    confidence: float = Field(..., ge=0.0, le=1.0)
    sample_size: int


class CEOProfileResponse(BaseModel):
    """CEO 프로파일 응답"""
    user_id: str = Field(..., description="CEO 사용자 ID")
    brand_preferences: dict[str, str] = Field(
        default_factory=dict,
        description="브랜드 선호도 (예: {'4P_100AF': 'LS산전'})"
    )
    price_thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="가격 임계값 (예: {'discount_max': 0.15})"
    )
    layout_style: dict = Field(
        default_factory=dict,
        description="레이아웃 스타일 (예: {'prefer_compact': true})"
    )
    preferences: list[CEOPreferenceItem] = Field(
        default_factory=list,
        description="전체 선호도 항목 목록"
    )
    sample_size: int = Field(..., description="총 학습 샘플 수")
    last_updated: Optional[datetime] = Field(None, description="마지막 업데이트 시각")


# ============================================================================
# Knowledge Generation
# ============================================================================

class KnowledgeGenRequest(BaseModel):
    """지식 자동 생성 요청"""
    min_occurrences: int = Field(default=3, ge=1, description="최소 발생 횟수")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="최소 신뢰도")
    categories: Optional[list[PatternCategory]] = Field(
        None,
        description="대상 카테고리 (None이면 전체)"
    )
    dry_run: bool = Field(default=False, description="실제 저장 없이 미리보기만")


class GeneratedKnowledge(BaseModel):
    """생성된 지식 항목"""
    knowledge_type: Literal["RULE", "PRICE", "KNOWHOW"]
    title: str
    content: str
    tags: list[str]
    source_pattern_id: str
    confidence: float


class KnowledgeGenResponse(BaseModel):
    """지식 생성 응답"""
    generated: list[GeneratedKnowledge]
    total_generated: int
    skipped_duplicates: int
    skipped_low_confidence: int
    dry_run: bool
    message: str


# ============================================================================
# Estimate Update (Self-Learning Integration)
# ============================================================================

class EstimateUpdateRequest(BaseModel):
    """견적 수정 요청 (Self-Learning 통합)"""
    customer_name: Optional[str] = Field(None, description="고객명")
    panels: list[dict] = Field(..., description="분전반 목록")
    modification_reason: Optional[str] = Field(
        None,
        description="수정 사유 (학습 시스템에서 활용)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "테스트 고객",
                "panels": [
                    {
                        "panel_name": "분전반1",
                        "main_breaker": {"brand": "상도차단기", "pole": "4P", "frame": "100AF", "ampere": 75},
                        "branch_breakers": [
                            {"brand": "상도차단기", "type": "ELB", "pole": "3P", "frame": "30AF", "ampere": 20, "quantity": 5}
                        ]
                    }
                ],
                "modification_reason": "브랜드를 LS산전으로 변경"
            }
        }


# ============================================================================
# Learning Statistics
# ============================================================================

class LearningStatsResponse(BaseModel):
    """학습 시스템 통계"""
    total_modifications: int = Field(..., description="총 수정 이력 수")
    total_patterns: int = Field(..., description="총 학습된 패턴 수")
    patterns_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="카테고리별 패턴 수"
    )
    avg_confidence: float = Field(..., description="평균 신뢰도")
    total_knowledge_generated: int = Field(..., description="생성된 지식 총 수")
    last_pattern_detected: Optional[datetime] = Field(None, description="마지막 패턴 감지 시각")
    last_knowledge_generated: Optional[datetime] = Field(None, description="마지막 지식 생성 시각")
