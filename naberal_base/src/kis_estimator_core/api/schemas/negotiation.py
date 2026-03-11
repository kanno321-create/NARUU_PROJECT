"""
AI Negotiation Assistant API Schemas (Phase XVII)

AI 협상 어시스턴트의 Request/Response 스키마 정의
Contract-First 원칙에 따라 API 계약을 먼저 정의합니다.

핵심 기능:
- 최적 가격 제안
- 협상 전략 추천
- 승률 분석 및 예측
- 가격 히스토리 분석
- 경쟁사 대비 포지셔닝
"""

from datetime import datetime, date
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


# ============================================================================
# Enums & Types
# ============================================================================

NegotiationStrategy = Literal[
    "AGGRESSIVE",      # 공격적 (가격 우선)
    "BALANCED",        # 균형 (가격 + 관계)
    "RELATIONSHIP",    # 관계 우선
    "VALUE_BASED",     # 가치 기반
    "COMPETITIVE"      # 경쟁 대응
]

PriceConfidence = Literal[
    "HIGH",           # 높음 (>80% 수주 예상)
    "MEDIUM",         # 중간 (50-80% 수주 예상)
    "LOW",            # 낮음 (<50% 수주 예상)
    "RISKY"           # 위험 (마진 부족 또는 경쟁 열세)
]

NegotiationPhase = Literal[
    "INITIAL",        # 초기 제안
    "COUNTER_OFFER",  # 역제안 대응
    "FINAL",          # 최종 협상
    "CLOSING"         # 마무리
]

CustomerType = Literal[
    "NEW",            # 신규 고객
    "RETURNING",      # 재방문 고객
    "VIP",            # VIP 고객
    "STRATEGIC"       # 전략적 고객
]


# ============================================================================
# Price Analysis (가격 분석)
# ============================================================================

class PriceAnalysisRequest(BaseModel):
    """가격 분석 요청"""
    estimate_id: Optional[str] = Field(None, description="견적 ID")
    base_price: float = Field(..., gt=0, description="기본 가격")
    cost_price: float = Field(..., gt=0, description="원가")
    customer_id: Optional[str] = Field(None, description="고객 ID")
    customer_type: CustomerType = Field(default="NEW", description="고객 유형")
    product_category: str = Field(default="PANEL", description="제품 카테고리")
    quantity: int = Field(default=1, ge=1, description="수량")
    urgency: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = Field(
        default="NORMAL",
        description="긴급도"
    )


class PriceRange(BaseModel):
    """가격 범위"""
    min_price: float = Field(..., description="최소 가격 (마진 한계)")
    recommended_price: float = Field(..., description="권장 가격")
    max_price: float = Field(..., description="최대 가격 (시장 상한)")
    optimal_price: float = Field(..., description="최적 가격 (승률 최적화)")


class MarginAnalysis(BaseModel):
    """마진 분석"""
    cost_price: float = Field(..., description="원가")
    gross_margin: float = Field(..., description="총이익")
    margin_rate: float = Field(..., ge=0, le=100, description="마진율 (%)")
    break_even_price: float = Field(..., description="손익분기점 가격")
    target_margin_rate: float = Field(..., description="목표 마진율")


class CompetitorPosition(BaseModel):
    """경쟁사 포지션"""
    market_average: float = Field(..., description="시장 평균 가격")
    our_position: Literal["BELOW", "AVERAGE", "ABOVE"] = Field(
        ...,
        description="우리 포지션"
    )
    price_difference_pct: float = Field(..., description="가격 차이 (%)")
    competitive_advantage: list[str] = Field(
        default_factory=list,
        description="경쟁 우위 요소"
    )


class PriceAnalysisResponse(BaseModel):
    """가격 분석 응답"""
    request_id: str = Field(..., description="요청 ID")
    base_price: float = Field(..., description="입력 기본 가격")
    price_range: PriceRange = Field(..., description="가격 범위 분석")
    margin_analysis: MarginAnalysis = Field(..., description="마진 분석")
    competitor_position: CompetitorPosition = Field(..., description="경쟁사 포지션")
    confidence: PriceConfidence = Field(..., description="가격 신뢰도")
    win_probability: float = Field(..., ge=0, le=100, description="예상 수주 확률 (%)")
    recommendations: list[str] = Field(default_factory=list, description="권장사항")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Negotiation Strategy (협상 전략)
# ============================================================================

class NegotiationContext(BaseModel):
    """협상 컨텍스트"""
    estimate_id: str = Field(..., description="견적 ID")
    customer_id: str = Field(..., description="고객 ID")
    customer_type: CustomerType = Field(..., description="고객 유형")
    current_price: float = Field(..., gt=0, description="현재 제안 가격")
    customer_target_price: Optional[float] = Field(None, description="고객 목표 가격")
    negotiation_phase: NegotiationPhase = Field(
        default="INITIAL",
        description="협상 단계"
    )
    previous_interactions: int = Field(default=0, ge=0, description="이전 협상 횟수")
    customer_urgency: Literal["LOW", "NORMAL", "HIGH"] = Field(
        default="NORMAL",
        description="고객 긴급도"
    )
    competitor_mentioned: bool = Field(default=False, description="경쟁사 언급 여부")
    budget_constraint: Optional[float] = Field(None, description="고객 예산 제약")


class StrategyRecommendation(BaseModel):
    """전략 추천"""
    strategy: NegotiationStrategy = Field(..., description="추천 전략")
    confidence: float = Field(..., ge=0, le=1, description="전략 신뢰도")
    rationale: str = Field(..., description="추천 근거")
    expected_outcome: str = Field(..., description="예상 결과")


class PriceMove(BaseModel):
    """가격 조정 제안"""
    move_type: Literal["HOLD", "DECREASE", "INCREASE", "PACKAGE"] = Field(
        ...,
        description="조정 유형"
    )
    suggested_price: float = Field(..., description="제안 가격")
    discount_rate: float = Field(default=0, description="할인율 (%)")
    justification: str = Field(..., description="가격 조정 근거")
    counter_arguments: list[str] = Field(
        default_factory=list,
        description="예상 반론 및 대응"
    )


class TalkingPoint(BaseModel):
    """협상 포인트"""
    topic: str = Field(..., description="주제")
    key_message: str = Field(..., description="핵심 메시지")
    supporting_facts: list[str] = Field(default_factory=list, description="근거")
    avoid_topics: list[str] = Field(default_factory=list, description="피해야 할 주제")


class NegotiationStrategyRequest(BaseModel):
    """협상 전략 요청"""
    context: NegotiationContext = Field(..., description="협상 컨텍스트")
    min_acceptable_price: Optional[float] = Field(None, description="최저 수용 가격")
    target_margin_rate: float = Field(default=15.0, description="목표 마진율 (%)")
    priority: Literal["PRICE", "RELATIONSHIP", "SPEED"] = Field(
        default="PRICE",
        description="협상 우선순위"
    )


class NegotiationStrategyResponse(BaseModel):
    """협상 전략 응답"""
    request_id: str = Field(..., description="요청 ID")
    context_summary: str = Field(..., description="상황 요약")

    # 전략 추천
    primary_strategy: StrategyRecommendation = Field(..., description="주요 전략")
    alternative_strategies: list[StrategyRecommendation] = Field(
        default_factory=list,
        description="대안 전략"
    )

    # 가격 전략
    price_move: PriceMove = Field(..., description="가격 조정 제안")
    price_floor: float = Field(..., description="최저 가격선")

    # 협상 가이드
    talking_points: list[TalkingPoint] = Field(
        default_factory=list,
        description="협상 포인트"
    )

    # 예측
    win_probability: float = Field(..., ge=0, le=100, description="수주 확률 (%)")
    expected_final_price: float = Field(..., description="예상 최종 가격")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Win-Loss Analysis (승패 분석)
# ============================================================================

class WinLossFilter(BaseModel):
    """승패 분석 필터"""
    start_date: date = Field(..., description="시작일")
    end_date: date = Field(..., description="종료일")
    customer_type: Optional[CustomerType] = Field(None, description="고객 유형")
    product_category: Optional[str] = Field(None, description="제품 카테고리")
    price_range_min: Optional[float] = Field(None, description="가격 범위 최소")
    price_range_max: Optional[float] = Field(None, description="가격 범위 최대")
    sales_rep: Optional[str] = Field(None, description="담당 영업사원")


class WinLossMetrics(BaseModel):
    """승패 지표"""
    total_opportunities: int = Field(..., description="총 기회")
    wins: int = Field(..., description="수주")
    losses: int = Field(..., description="실주")
    pending: int = Field(..., description="진행 중")
    win_rate: float = Field(..., ge=0, le=100, description="수주율 (%)")
    average_deal_size: float = Field(..., description="평균 거래 규모")
    average_margin: float = Field(..., description="평균 마진율 (%)")


class LossReason(BaseModel):
    """실주 원인"""
    reason: str = Field(..., description="원인")
    count: int = Field(..., description="건수")
    percentage: float = Field(..., ge=0, le=100, description="비율 (%)")
    typical_price_gap: Optional[float] = Field(None, description="일반적 가격 차이")


class WinFactor(BaseModel):
    """수주 요인"""
    factor: str = Field(..., description="요인")
    impact_score: float = Field(..., ge=0, le=100, description="영향도")
    occurrence_rate: float = Field(..., ge=0, le=100, description="발생률 (%)")


class WinLossAnalysisResponse(BaseModel):
    """승패 분석 응답"""
    request_id: str = Field(..., description="요청 ID")
    period: str = Field(..., description="분석 기간")

    # 핵심 지표
    metrics: WinLossMetrics = Field(..., description="핵심 지표")

    # 분석 결과
    loss_reasons: list[LossReason] = Field(
        default_factory=list,
        description="실주 원인 분석"
    )
    win_factors: list[WinFactor] = Field(
        default_factory=list,
        description="수주 성공 요인"
    )

    # 인사이트
    key_insights: list[str] = Field(default_factory=list, description="핵심 인사이트")
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="개선 제안"
    )

    # 벤치마크
    industry_avg_win_rate: float = Field(..., description="업계 평균 수주율")
    performance_vs_benchmark: str = Field(..., description="벤치마크 대비 성과")

    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Counter Offer (역제안 대응)
# ============================================================================

class CounterOfferRequest(BaseModel):
    """역제안 대응 요청"""
    estimate_id: str = Field(..., description="견적 ID")
    original_price: float = Field(..., gt=0, description="원래 제안 가격")
    customer_counter_price: float = Field(..., gt=0, description="고객 역제안 가격")
    cost_price: float = Field(..., gt=0, description="원가")
    customer_id: Optional[str] = Field(None, description="고객 ID")
    customer_type: CustomerType = Field(default="NEW", description="고객 유형")
    reason_given: Optional[str] = Field(None, description="고객이 제시한 이유")
    deadline: Optional[date] = Field(None, description="결정 기한")
    is_final_offer: bool = Field(default=False, description="최종 제안 여부")


class CounterOfferOption(BaseModel):
    """역제안 옵션"""
    option_name: str = Field(..., description="옵션명")
    price: float = Field(..., description="제안 가격")
    discount_rate: float = Field(..., description="할인율 (%)")
    margin_rate: float = Field(..., description="마진율 (%)")
    win_probability: float = Field(..., ge=0, le=100, description="수주 확률")
    value_adds: list[str] = Field(default_factory=list, description="추가 가치")
    conditions: list[str] = Field(default_factory=list, description="조건")


class CounterOfferResponse(BaseModel):
    """역제안 대응 응답"""
    request_id: str = Field(..., description="요청 ID")
    analysis_summary: str = Field(..., description="상황 분석")

    # 가격 차이 분석
    price_gap: float = Field(..., description="가격 차이")
    price_gap_pct: float = Field(..., description="가격 차이 (%)")
    is_acceptable: bool = Field(..., description="수용 가능 여부")

    # 옵션들
    recommended_option: CounterOfferOption = Field(..., description="추천 옵션")
    alternative_options: list[CounterOfferOption] = Field(
        default_factory=list,
        description="대안 옵션"
    )

    # 협상 가이드
    response_script: str = Field(..., description="응답 스크립트")
    key_arguments: list[str] = Field(default_factory=list, description="핵심 논점")
    concessions_to_avoid: list[str] = Field(
        default_factory=list,
        description="피해야 할 양보"
    )

    # 예측
    expected_outcome: str = Field(..., description="예상 결과")
    walk_away_recommendation: bool = Field(
        default=False,
        description="협상 중단 권고"
    )

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Price History (가격 히스토리)
# ============================================================================

class PriceHistoryRequest(BaseModel):
    """가격 히스토리 요청"""
    customer_id: Optional[str] = Field(None, description="고객 ID")
    product_category: Optional[str] = Field(None, description="제품 카테고리")
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    include_lost_deals: bool = Field(default=True, description="실주 포함")


class PriceHistoryItem(BaseModel):
    """가격 히스토리 항목"""
    estimate_id: str = Field(..., description="견적 ID")
    record_date: date = Field(..., description="날짜")
    initial_price: float = Field(..., description="초기 가격")
    final_price: float = Field(..., description="최종 가격")
    discount_rate: float = Field(..., description="할인율 (%)")
    outcome: Literal["WON", "LOST", "PENDING"] = Field(..., description="결과")
    customer_type: CustomerType = Field(..., description="고객 유형")
    negotiation_rounds: int = Field(..., description="협상 라운드")


class PriceTrend(BaseModel):
    """가격 트렌드"""
    period: str = Field(..., description="기간")
    average_price: float = Field(..., description="평균 가격")
    average_discount: float = Field(..., description="평균 할인율")
    price_change_pct: float = Field(..., description="가격 변동률 (%)")


class PriceHistoryResponse(BaseModel):
    """가격 히스토리 응답"""
    request_id: str = Field(..., description="요청 ID")
    history: list[PriceHistoryItem] = Field(..., description="히스토리")
    total_records: int = Field(..., description="총 레코드 수")

    # 통계
    average_initial_price: float = Field(..., description="평균 초기 가격")
    average_final_price: float = Field(..., description="평균 최종 가격")
    average_discount_rate: float = Field(..., description="평균 할인율")

    # 트렌드
    trends: list[PriceTrend] = Field(default_factory=list, description="가격 트렌드")

    # 인사이트
    insights: list[str] = Field(default_factory=list, description="인사이트")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Quick Negotiation Tips (빠른 협상 팁)
# ============================================================================

class QuickTipRequest(BaseModel):
    """빠른 팁 요청"""
    situation: str = Field(..., min_length=5, description="현재 상황 설명")
    customer_statement: Optional[str] = Field(None, description="고객 발언")
    current_discount: float = Field(default=0, ge=0, le=50, description="현재 할인율")


class QuickTipResponse(BaseModel):
    """빠른 팁 응답"""
    request_id: str = Field(..., description="요청 ID")
    situation_type: str = Field(..., description="상황 유형")

    # 즉시 사용 가능한 팁
    immediate_response: str = Field(..., description="즉시 응답")
    key_phrase: str = Field(..., description="핵심 멘트")

    # 추가 전략
    do_list: list[str] = Field(default_factory=list, description="해야 할 것")
    dont_list: list[str] = Field(default_factory=list, description="하지 말아야 할 것")

    # 가격 가이드
    max_additional_discount: float = Field(..., description="추가 할인 한도 (%)")
    alternative_concessions: list[str] = Field(
        default_factory=list,
        description="가격 외 양보 옵션"
    )

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Negotiation Dashboard (협상 대시보드)
# ============================================================================

class NegotiationDashboardResponse(BaseModel):
    """협상 대시보드 응답"""
    # 핵심 지표
    active_negotiations: int = Field(..., description="진행 중 협상")
    avg_win_rate_30d: float = Field(..., description="30일 평균 수주율")
    avg_discount_rate: float = Field(..., description="평균 할인율")
    total_pipeline_value: float = Field(..., description="총 파이프라인 가치")

    # 성과 추이
    win_rate_trend: Literal["UP", "DOWN", "STABLE"] = Field(
        ...,
        description="수주율 추세"
    )
    margin_trend: Literal["UP", "DOWN", "STABLE"] = Field(
        ...,
        description="마진 추세"
    )

    # 주요 알림
    urgent_negotiations: list[str] = Field(
        default_factory=list,
        description="긴급 협상 건"
    )
    at_risk_deals: list[str] = Field(
        default_factory=list,
        description="위험 거래"
    )

    # 오늘의 팁
    daily_tip: str = Field(..., description="오늘의 협상 팁")

    # 성과 요약
    monthly_performance: dict = Field(
        default_factory=dict,
        description="월간 성과"
    )

    generated_at: datetime = Field(default_factory=datetime.utcnow)
