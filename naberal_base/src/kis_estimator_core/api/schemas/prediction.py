"""
Prediction Analytics API Schemas (Phase XV)

예측 분석 대시보드의 Request/Response 스키마 정의
Contract-First 원칙에 따라 API 계약을 먼저 정의합니다.

핵심 기능:
- 월별 매출 예측
- 자재 수요 예측
- 계절별/고객별 트렌드 분석
- 견적 성공률 예측
- 이상 탐지 (Anomaly Detection)
"""

from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Enums & Types
# ============================================================================

PredictionType = Literal[
    "SALES",           # 매출 예측
    "DEMAND",          # 자재 수요 예측
    "SUCCESS_RATE",    # 견적 성공률 예측
    "TREND",           # 트렌드 분석
    "ANOMALY"          # 이상 탐지
]

TimeGranularity = Literal[
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "QUARTERLY",
    "YEARLY"
]

ConfidenceLevel = Literal[
    "HIGH",      # 90%+ 신뢰도
    "MEDIUM",    # 70-90% 신뢰도
    "LOW"        # 50-70% 신뢰도
]

TrendDirection = Literal[
    "UP",        # 상승 추세
    "DOWN",      # 하락 추세
    "STABLE",    # 안정적
    "VOLATILE"   # 변동성 높음
]

AnomalyType = Literal[
    "SPIKE",           # 급격한 상승
    "DROP",            # 급격한 하락
    "PATTERN_BREAK",   # 패턴 이탈
    "UNUSUAL_CUSTOMER" # 비정상 고객 행동
]


# ============================================================================
# Sales Prediction (매출 예측)
# ============================================================================

class SalesPredictionRequest(BaseModel):
    """매출 예측 요청"""
    start_date: date = Field(..., description="예측 시작일")
    end_date: date = Field(..., description="예측 종료일")
    granularity: TimeGranularity = Field(
        default="MONTHLY",
        description="예측 단위 (일별/주별/월별)"
    )
    include_confidence_interval: bool = Field(
        default=True,
        description="신뢰 구간 포함 여부"
    )
    customer_id: Optional[str] = Field(
        None,
        description="특정 고객 필터 (없으면 전체)"
    )


class SalesPredictionPoint(BaseModel):
    """매출 예측 데이터 포인트"""
    prediction_date: date = Field(..., description="예측 날짜")
    predicted_amount: int = Field(..., description="예측 매출액")
    lower_bound: Optional[int] = Field(None, description="신뢰 구간 하한")
    upper_bound: Optional[int] = Field(None, description="신뢰 구간 상한")
    confidence: ConfidenceLevel = Field(..., description="예측 신뢰도")
    factors: list[str] = Field(
        default_factory=list,
        description="예측에 영향을 준 요인들"
    )


class SalesPredictionResponse(BaseModel):
    """매출 예측 응답"""
    request_id: str = Field(..., description="요청 ID")
    predictions: list[SalesPredictionPoint] = Field(..., description="예측 데이터")
    total_predicted: int = Field(..., description="총 예측 매출")
    trend: TrendDirection = Field(..., description="전체 추세")
    yoy_growth: float = Field(..., description="전년 대비 성장률 (%)")
    mom_growth: float = Field(..., description="전월 대비 성장률 (%)")
    model_accuracy: float = Field(..., description="모델 정확도 (MAPE)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Demand Prediction (자재 수요 예측)
# ============================================================================

class DemandPredictionRequest(BaseModel):
    """자재 수요 예측 요청"""
    material_category: Optional[Literal["BREAKER", "ENCLOSURE", "ACCESSORY", "ALL"]] = Field(
        default="ALL",
        description="자재 카테고리"
    )
    start_date: date = Field(..., description="예측 시작일")
    end_date: date = Field(..., description="예측 종료일")
    granularity: TimeGranularity = Field(
        default="MONTHLY",
        description="예측 단위"
    )


class MaterialDemandPoint(BaseModel):
    """자재별 수요 예측"""
    material_id: str = Field(..., description="자재 ID")
    material_name: str = Field(..., description="자재명")
    category: str = Field(..., description="카테고리")
    predicted_quantity: int = Field(..., description="예측 수량")
    current_stock: Optional[int] = Field(None, description="현재 재고")
    reorder_suggested: bool = Field(..., description="재주문 권장 여부")
    reorder_quantity: Optional[int] = Field(None, description="권장 주문량")
    confidence: ConfidenceLevel = Field(..., description="예측 신뢰도")


class DemandPredictionResponse(BaseModel):
    """자재 수요 예측 응답"""
    request_id: str = Field(..., description="요청 ID")
    period: str = Field(..., description="예측 기간")
    materials: list[MaterialDemandPoint] = Field(..., description="자재별 예측")
    top_demand_items: list[str] = Field(..., description="수요 상위 5개 자재")
    shortage_risk_items: list[str] = Field(
        default_factory=list,
        description="재고 부족 위험 자재"
    )
    total_estimated_cost: int = Field(..., description="예상 총 구매비용")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Success Rate Prediction (견적 성공률 예측)
# ============================================================================

class SuccessRatePredictionRequest(BaseModel):
    """견적 성공률 예측 요청"""
    customer_id: Optional[str] = Field(None, description="고객 ID (없으면 전체)")
    estimate_amount: Optional[int] = Field(None, description="견적 금액")
    panel_count: Optional[int] = Field(None, description="분전반 수")
    breaker_count: Optional[int] = Field(None, description="차단기 수")
    include_similar_cases: bool = Field(
        default=True,
        description="유사 사례 포함 여부"
    )


class SimilarCase(BaseModel):
    """유사 견적 사례"""
    estimate_id: str = Field(..., description="견적 ID")
    customer_name: Optional[str] = Field(None, description="고객명")
    amount: int = Field(..., description="견적 금액")
    success: bool = Field(..., description="성공 여부")
    similarity_score: float = Field(..., description="유사도 점수 (0-1)")
    case_date: date = Field(..., description="견적 일자")


class SuccessRatePredictionResponse(BaseModel):
    """견적 성공률 예측 응답"""
    request_id: str = Field(..., description="요청 ID")
    predicted_success_rate: float = Field(..., ge=0, le=100, description="예측 성공률 (%)")
    confidence: ConfidenceLevel = Field(..., description="예측 신뢰도")
    key_factors: list[str] = Field(..., description="성공률에 영향을 주는 주요 요인")
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="성공률 향상을 위한 제안"
    )
    similar_cases: list[SimilarCase] = Field(
        default_factory=list,
        description="유사 사례 목록"
    )
    historical_average: float = Field(..., description="과거 평균 성공률 (%)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Trend Analysis (트렌드 분석)
# ============================================================================

class TrendAnalysisRequest(BaseModel):
    """트렌드 분석 요청"""
    analysis_type: Literal["SEASONAL", "CUSTOMER", "PRODUCT", "REGIONAL"] = Field(
        ...,
        description="분석 유형"
    )
    period_months: int = Field(
        default=12,
        ge=1,
        le=60,
        description="분석 기간 (개월)"
    )
    top_n: int = Field(
        default=10,
        ge=1,
        le=50,
        description="상위 N개 결과"
    )


class TrendItem(BaseModel):
    """트렌드 항목"""
    name: str = Field(..., description="항목명")
    value: int = Field(..., description="값 (매출/건수)")
    change_rate: float = Field(..., description="변화율 (%)")
    direction: TrendDirection = Field(..., description="추세 방향")
    forecast: Optional[int] = Field(None, description="다음 기간 예측값")


class SeasonalPattern(BaseModel):
    """계절별 패턴"""
    season: Literal["SPRING", "SUMMER", "FALL", "WINTER"] = Field(..., description="계절")
    average_sales: int = Field(..., description="평균 매출")
    peak_month: int = Field(..., ge=1, le=12, description="피크 월")
    typical_projects: list[str] = Field(..., description="주요 프로젝트 유형")


class TrendAnalysisResponse(BaseModel):
    """트렌드 분석 응답"""
    request_id: str = Field(..., description="요청 ID")
    analysis_type: str = Field(..., description="분석 유형")
    period: str = Field(..., description="분석 기간")
    items: list[TrendItem] = Field(..., description="트렌드 항목들")
    seasonal_patterns: list[SeasonalPattern] = Field(
        default_factory=list,
        description="계절별 패턴 (SEASONAL 분석 시)"
    )
    insights: list[str] = Field(..., description="주요 인사이트")
    recommendations: list[str] = Field(..., description="권장 사항")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Anomaly Detection (이상 탐지)
# ============================================================================

class AnomalyDetectionRequest(BaseModel):
    """이상 탐지 요청"""
    detection_scope: Literal["SALES", "CUSTOMER", "PRICING", "ALL"] = Field(
        default="ALL",
        description="탐지 범위"
    )
    sensitivity: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        default="MEDIUM",
        description="민감도 (HIGH=더 많은 이상 탐지)"
    )
    lookback_days: int = Field(
        default=90,
        ge=7,
        le=365,
        description="분석 기간 (일)"
    )


class AnomalyItem(BaseModel):
    """이상 탐지 항목"""
    anomaly_id: str = Field(..., description="이상 ID")
    anomaly_type: AnomalyType = Field(..., description="이상 유형")
    severity: Literal["CRITICAL", "WARNING", "INFO"] = Field(..., description="심각도")
    detected_at: datetime = Field(..., description="탐지 시각")
    description: str = Field(..., description="이상 설명")
    affected_entity: str = Field(..., description="영향받는 엔티티 (고객/자재/견적)")
    expected_value: Optional[float] = Field(None, description="예상 값")
    actual_value: Optional[float] = Field(None, description="실제 값")
    deviation_percent: Optional[float] = Field(None, description="편차 (%)")
    recommended_action: str = Field(..., description="권장 조치")


class AnomalyDetectionResponse(BaseModel):
    """이상 탐지 응답"""
    request_id: str = Field(..., description="요청 ID")
    period: str = Field(..., description="분석 기간")
    total_anomalies: int = Field(..., description="총 이상 건수")
    critical_count: int = Field(..., description="심각 이상 건수")
    warning_count: int = Field(..., description="경고 이상 건수")
    anomalies: list[AnomalyItem] = Field(..., description="이상 목록")
    system_health: Literal["HEALTHY", "ATTENTION", "CRITICAL"] = Field(
        ...,
        description="시스템 건강 상태"
    )
    next_check_recommended: datetime = Field(..., description="다음 점검 권장 시각")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Dashboard Summary (대시보드 요약)
# ============================================================================

class DashboardSummaryRequest(BaseModel):
    """대시보드 요약 요청"""
    include_predictions: bool = Field(default=True, description="예측 포함")
    include_anomalies: bool = Field(default=True, description="이상 탐지 포함")
    include_trends: bool = Field(default=True, description="트렌드 포함")
    prediction_months: int = Field(default=3, ge=1, le=12, description="예측 기간 (월)")


class KPIMetric(BaseModel):
    """KPI 지표"""
    name: str = Field(..., description="지표명")
    current_value: float = Field(..., description="현재 값")
    previous_value: float = Field(..., description="이전 값")
    change_rate: float = Field(..., description="변화율 (%)")
    target_value: Optional[float] = Field(None, description="목표 값")
    status: Literal["ON_TRACK", "AT_RISK", "OFF_TRACK"] = Field(..., description="상태")


class DashboardSummaryResponse(BaseModel):
    """대시보드 요약 응답"""
    request_id: str = Field(..., description="요청 ID")

    # KPI 지표
    kpis: list[KPIMetric] = Field(..., description="주요 KPI")

    # 매출 예측 요약
    sales_forecast: Optional[SalesPredictionResponse] = Field(None, description="매출 예측")

    # 수요 예측 요약
    demand_forecast: Optional[DemandPredictionResponse] = Field(None, description="수요 예측")

    # 이상 탐지 요약
    anomaly_summary: Optional[AnomalyDetectionResponse] = Field(None, description="이상 탐지")

    # 트렌드 요약
    trend_summary: Optional[TrendAnalysisResponse] = Field(None, description="트렌드 분석")

    # 액션 아이템
    action_items: list[str] = Field(
        default_factory=list,
        description="권장 조치 사항"
    )

    # 알림
    alerts: list[str] = Field(
        default_factory=list,
        description="주의 알림"
    )

    generated_at: datetime = Field(default_factory=datetime.utcnow)
