"""
Vision AI API Schemas (Phase XIV)

도면/사진 분석 → 자동 견적 시스템의 Request/Response 스키마 정의
Contract-First 원칙에 따라 API 계약을 먼저 정의합니다.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Enums & Types
# ============================================================================

ImageType = Literal[
    "DRAWING",        # 전기 도면
    "PANEL_PHOTO",    # 분전반 사진
    "SPEC_SHEET",     # 사양서/스펙시트
    "HANDWRITTEN",    # 수기 메모
    "OTHER"           # 기타
]

ExtractionConfidence = Literal[
    "HIGH",    # 90%+ 확신
    "MEDIUM",  # 70-90% 확신
    "LOW",     # 50-70% 확신
    "MANUAL"   # 수동 확인 필요
]


# ============================================================================
# Image Analysis Request/Response
# ============================================================================

class ImageAttachment(BaseModel):
    """이미지 첨부파일"""
    id: str = Field(..., description="첨부파일 ID")
    name: str = Field(..., description="파일명")
    type: str = Field(..., description="MIME 타입 (image/png, image/jpeg 등)")
    size: int = Field(..., description="파일 크기 (bytes)")
    url: str = Field(..., description="이미지 URL 또는 base64 데이터")


class VisionAnalyzeRequest(BaseModel):
    """도면/사진 분석 요청"""
    images: list[ImageAttachment] = Field(..., min_length=1, description="분석할 이미지 목록")
    analysis_type: Literal["FULL", "QUICK", "COMPONENTS_ONLY"] = Field(
        default="FULL",
        description="분석 유형: FULL(전체), QUICK(빠른), COMPONENTS_ONLY(컴포넌트만)"
    )
    extract_estimate: bool = Field(
        default=True,
        description="견적 정보 자동 추출 여부"
    )
    user_hint: Optional[str] = Field(
        None,
        description="사용자가 제공하는 추가 정보/힌트"
    )


# ============================================================================
# Extracted Components
# ============================================================================

class ExtractedBreaker(BaseModel):
    """추출된 차단기 정보"""
    type: Literal["MCCB", "ELB"] = Field(..., description="차단기 타입")
    brand: Optional[str] = Field(None, description="브랜드 (상도, LS 등)")
    pole: str = Field(..., description="극수 (2P, 3P, 4P)")
    frame: str = Field(..., description="프레임 (50AF, 100AF 등)")
    ampere: int = Field(..., description="정격전류 (A)")
    quantity: int = Field(default=1, ge=1, description="수량")
    is_main: bool = Field(default=False, description="메인 차단기 여부")
    confidence: ExtractionConfidence = Field(..., description="추출 신뢰도")
    bounding_box: Optional[dict] = Field(None, description="이미지 내 위치 (x, y, w, h)")


class ExtractedEnclosure(BaseModel):
    """추출된 외함 정보"""
    type: str = Field(..., description="외함 종류 (옥내노출, 옥외노출 등)")
    material: Optional[str] = Field(None, description="재질 (STEEL, SUS 등)")
    thickness: Optional[str] = Field(None, description="두께 (1.6T 등)")
    width: Optional[int] = Field(None, description="폭 (mm)")
    height: Optional[int] = Field(None, description="높이 (mm)")
    depth: Optional[int] = Field(None, description="깊이 (mm)")
    confidence: ExtractionConfidence = Field(..., description="추출 신뢰도")


class ExtractedPanel(BaseModel):
    """추출된 분전반 정보"""
    panel_name: str = Field(..., description="분전반명")
    enclosure: Optional[ExtractedEnclosure] = Field(None, description="외함 정보")
    main_breaker: Optional[ExtractedBreaker] = Field(None, description="메인 차단기")
    branch_breakers: list[ExtractedBreaker] = Field(default_factory=list, description="분기 차단기 목록")
    accessories: list[str] = Field(default_factory=list, description="부속자재 목록")
    notes: list[str] = Field(default_factory=list, description="추가 메모/주석")
    confidence: ExtractionConfidence = Field(..., description="전체 추출 신뢰도")


class ExtractedCustomer(BaseModel):
    """추출된 고객 정보"""
    name: Optional[str] = Field(None, description="고객명/거래처명")
    project_name: Optional[str] = Field(None, description="건명/프로젝트명")
    address: Optional[str] = Field(None, description="주소")
    phone: Optional[str] = Field(None, description="연락처")
    confidence: ExtractionConfidence = Field(..., description="추출 신뢰도")


# ============================================================================
# Analysis Response
# ============================================================================

class ImageAnalysisResult(BaseModel):
    """개별 이미지 분석 결과"""
    image_id: str = Field(..., description="분석된 이미지 ID")
    image_type: ImageType = Field(..., description="감지된 이미지 유형")
    panels: list[ExtractedPanel] = Field(default_factory=list, description="추출된 분전반 목록")
    customer: Optional[ExtractedCustomer] = Field(None, description="추출된 고객 정보")
    raw_text: list[str] = Field(default_factory=list, description="OCR로 추출된 원본 텍스트")
    warnings: list[str] = Field(default_factory=list, description="경고 메시지")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")


class VisionAnalyzeResponse(BaseModel):
    """도면/사진 분석 응답"""
    request_id: str = Field(..., description="요청 ID (UUID)")
    status: Literal["SUCCESS", "PARTIAL", "FAILED"] = Field(..., description="분석 상태")
    results: list[ImageAnalysisResult] = Field(default_factory=list, description="이미지별 분석 결과")
    merged_panels: list[ExtractedPanel] = Field(
        default_factory=list,
        description="모든 이미지에서 병합된 분전반 목록"
    )
    total_breakers: int = Field(default=0, description="총 차단기 수")
    total_panels: int = Field(default=0, description="총 분전반 수")
    overall_confidence: ExtractionConfidence = Field(..., description="전체 분석 신뢰도")
    message: str = Field(..., description="결과 메시지")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="분석 시각")


# ============================================================================
# Auto Estimate Generation
# ============================================================================

class VisionEstimateRequest(BaseModel):
    """Vision 기반 자동 견적 생성 요청"""
    analysis_result_id: Optional[str] = Field(
        None,
        description="이전 분석 결과 ID (재사용 시)"
    )
    images: Optional[list[ImageAttachment]] = Field(
        None,
        description="분석할 이미지 목록 (새 분석 시)"
    )
    customer_name: Optional[str] = Field(None, description="고객명 (오버라이드)")
    project_name: Optional[str] = Field(None, description="건명 (오버라이드)")
    apply_ceo_preferences: bool = Field(
        default=True,
        description="CEO 학습된 선호도 적용 여부"
    )
    brand_override: Optional[str] = Field(
        None,
        description="브랜드 강제 지정 (상도, LS 등)"
    )


class VisionEstimateItem(BaseModel):
    """Vision 기반 견적 항목"""
    category: str = Field(..., description="카테고리 (외함, 차단기, 부속자재 등)")
    name: str = Field(..., description="품명")
    specification: str = Field(..., description="규격")
    unit: str = Field(..., description="단위")
    quantity: int = Field(..., ge=1, description="수량")
    unit_price: int = Field(..., ge=0, description="단가")
    total_price: int = Field(..., ge=0, description="금액")
    source: Literal["VISION", "CALCULATED", "CATALOG", "CEO_PREFERENCE"] = Field(
        ...,
        description="가격/정보 출처"
    )
    confidence: ExtractionConfidence = Field(..., description="신뢰도")


class VisionEstimatePanel(BaseModel):
    """Vision 기반 분전반 견적"""
    panel_name: str = Field(..., description="분전반명")
    items: list[VisionEstimateItem] = Field(..., description="견적 항목 목록")
    subtotal: int = Field(..., description="소계")
    notes: list[str] = Field(default_factory=list, description="비고/주의사항")


class VisionEstimateResponse(BaseModel):
    """Vision 기반 자동 견적 응답"""
    estimate_id: str = Field(..., description="생성된 견적 ID")
    request_id: str = Field(..., description="요청 ID")
    customer_name: Optional[str] = Field(None, description="고객명")
    project_name: Optional[str] = Field(None, description="건명")
    panels: list[VisionEstimatePanel] = Field(..., description="분전반별 견적")
    total_amount: int = Field(..., description="합계 (부가세 별도)")
    total_with_vat: int = Field(..., description="합계 (부가세 포함)")
    ceo_preferences_applied: bool = Field(..., description="CEO 선호도 적용 여부")
    confidence_summary: dict[str, int] = Field(
        default_factory=dict,
        description="신뢰도별 항목 수 (HIGH: 10, MEDIUM: 5, ...)"
    )
    warnings: list[str] = Field(default_factory=list, description="경고/확인 필요 사항")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시각")
    message: str = Field(..., description="결과 메시지")


# ============================================================================
# Analysis History
# ============================================================================

class VisionAnalysisHistoryItem(BaseModel):
    """Vision 분석 이력 항목"""
    analysis_id: str = Field(..., description="분석 ID")
    image_count: int = Field(..., description="분석된 이미지 수")
    panel_count: int = Field(..., description="추출된 분전반 수")
    estimate_generated: bool = Field(..., description="견적 생성 여부")
    estimate_id: Optional[str] = Field(None, description="생성된 견적 ID")
    overall_confidence: ExtractionConfidence = Field(..., description="전체 신뢰도")
    analyzed_at: datetime = Field(..., description="분석 시각")
    user_id: Optional[str] = Field(None, description="분석 요청자")


class VisionHistoryResponse(BaseModel):
    """Vision 분석 이력 응답"""
    history: list[VisionAnalysisHistoryItem]
    total: int
    page: int = 1
    page_size: int = 20
