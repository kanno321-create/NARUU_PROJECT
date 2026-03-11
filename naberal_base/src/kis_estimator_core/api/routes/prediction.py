"""
Prediction Analytics API Routes (Phase XV)

예측 분석 대시보드 API 엔드포인트
Contract-First 원칙에 따라 정의된 API 계약을 구현합니다.

엔드포인트:
- POST /v1/prediction/sales          - 매출 예측
- POST /v1/prediction/demand         - 자재 수요 예측
- POST /v1/prediction/success-rate   - 견적 성공률 예측
- POST /v1/prediction/trends         - 트렌드 분석
- POST /v1/prediction/anomalies      - 이상 탐지
- GET  /v1/prediction/dashboard      - 대시보드 요약
- GET  /v1/prediction/stats          - 통계 조회
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from kis_estimator_core.api.schemas.prediction import (
    SalesPredictionRequest,
    SalesPredictionResponse,
    SalesPredictionPoint,
    DemandPredictionRequest,
    DemandPredictionResponse,
    MaterialDemandPoint,
    SuccessRatePredictionRequest,
    SuccessRatePredictionResponse,
    SimilarCase,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    TrendItem,
    SeasonalPattern,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyItem,
    DashboardSummaryRequest,
    DashboardSummaryResponse,
    KPIMetric,
)
from kis_estimator_core.services.prediction_service import (
    get_prediction_service,
    PredictionService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prediction", tags=["Prediction Analytics"])


# ============================================================================
# Helper Functions
# ============================================================================

def _convert_sales_predictions(data: dict) -> SalesPredictionResponse:
    """매출 예측 결과 변환"""
    predictions = [
        SalesPredictionPoint(
            prediction_date=p["prediction_date"],
            predicted_amount=p["predicted_amount"],
            lower_bound=p.get("lower_bound"),
            upper_bound=p.get("upper_bound"),
            confidence=p["confidence"],
            factors=p.get("factors", [])
        )
        for p in data.get("predictions", [])
    ]

    return SalesPredictionResponse(
        request_id=data["request_id"],
        predictions=predictions,
        total_predicted=data["total_predicted"],
        trend=data["trend"],
        yoy_growth=data["yoy_growth"],
        mom_growth=data["mom_growth"],
        model_accuracy=data["model_accuracy"]
    )


def _convert_demand_predictions(data: dict) -> DemandPredictionResponse:
    """수요 예측 결과 변환"""
    materials = [
        MaterialDemandPoint(
            material_id=m["material_id"],
            material_name=m["material_name"],
            category=m["category"],
            predicted_quantity=m["predicted_quantity"],
            current_stock=m.get("current_stock"),
            reorder_suggested=m["reorder_suggested"],
            reorder_quantity=m.get("reorder_quantity"),
            confidence=m["confidence"]
        )
        for m in data.get("materials", [])
    ]

    return DemandPredictionResponse(
        request_id=data["request_id"],
        period=data["period"],
        materials=materials,
        top_demand_items=data.get("top_demand_items", []),
        shortage_risk_items=data.get("shortage_risk_items", []),
        total_estimated_cost=data["total_estimated_cost"]
    )


def _convert_success_rate(data: dict) -> SuccessRatePredictionResponse:
    """성공률 예측 결과 변환"""
    similar_cases = [
        SimilarCase(
            estimate_id=c["estimate_id"],
            customer_name=c.get("customer_name"),
            amount=c["amount"],
            success=c["success"],
            similarity_score=c["similarity_score"],
            case_date=c["case_date"]
        )
        for c in data.get("similar_cases", [])
    ]

    return SuccessRatePredictionResponse(
        request_id=data["request_id"],
        predicted_success_rate=data["predicted_success_rate"],
        confidence=data["confidence"],
        key_factors=data["key_factors"],
        improvement_suggestions=data.get("improvement_suggestions", []),
        similar_cases=similar_cases,
        historical_average=data["historical_average"]
    )


def _convert_trend_analysis(data: dict) -> TrendAnalysisResponse:
    """트렌드 분석 결과 변환"""
    items = [
        TrendItem(
            name=i["name"],
            value=i["value"],
            change_rate=i["change_rate"],
            direction=i["direction"],
            forecast=i.get("forecast")
        )
        for i in data.get("items", [])
    ]

    seasonal_patterns = [
        SeasonalPattern(
            season=p["season"],
            average_sales=p["average_sales"],
            peak_month=p["peak_month"],
            typical_projects=p.get("typical_projects", [])
        )
        for p in data.get("seasonal_patterns", [])
    ]

    return TrendAnalysisResponse(
        request_id=data["request_id"],
        analysis_type=data["analysis_type"],
        period=data["period"],
        items=items,
        seasonal_patterns=seasonal_patterns,
        insights=data.get("insights", []),
        recommendations=data.get("recommendations", [])
    )


def _convert_anomaly_detection(data: dict) -> AnomalyDetectionResponse:
    """이상 탐지 결과 변환"""
    anomalies = [
        AnomalyItem(
            anomaly_id=a["anomaly_id"],
            anomaly_type=a["anomaly_type"],
            severity=a["severity"],
            detected_at=a["detected_at"],
            description=a["description"],
            affected_entity=a["affected_entity"],
            expected_value=a.get("expected_value"),
            actual_value=a.get("actual_value"),
            deviation_percent=a.get("deviation_percent"),
            recommended_action=a["recommended_action"]
        )
        for a in data.get("anomalies", [])
    ]

    return AnomalyDetectionResponse(
        request_id=data["request_id"],
        period=data["period"],
        total_anomalies=data["total_anomalies"],
        critical_count=data["critical_count"],
        warning_count=data["warning_count"],
        anomalies=anomalies,
        system_health=data["system_health"],
        next_check_recommended=data["next_check_recommended"]
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/sales",
    response_model=SalesPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="매출 예측",
    description="시계열 분석 기반 매출 예측을 수행합니다."
)
async def predict_sales(request: SalesPredictionRequest):
    """
    매출 예측

    - 이동 평균 기반 예측
    - 계절성 조정 적용
    - 신뢰 구간 제공
    """
    logger.info(f"매출 예측 요청: {request.start_date} ~ {request.end_date}")

    try:
        service = get_prediction_service()

        result = await service.predict_sales(
            start_date=request.start_date,
            end_date=request.end_date,
            granularity=request.granularity,
            customer_id=request.customer_id
        )

        return _convert_sales_predictions(result)

    except Exception as e:
        logger.error(f"매출 예측 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매출 예측 중 오류 발생: {str(e)}"
        )


@router.post(
    "/demand",
    response_model=DemandPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="자재 수요 예측",
    description="과거 사용 패턴 기반 자재 수요를 예측합니다."
)
async def predict_demand(request: DemandPredictionRequest):
    """
    자재 수요 예측

    - 카테고리별 수요 분석
    - 재고 부족 위험 탐지
    - 재주문 권장량 계산
    """
    logger.info(f"자재 수요 예측 요청: {request.material_category}")

    try:
        service = get_prediction_service()

        result = await service.predict_demand(
            start_date=request.start_date,
            end_date=request.end_date,
            category=request.material_category,
            granularity=request.granularity
        )

        return _convert_demand_predictions(result)

    except Exception as e:
        logger.error(f"자재 수요 예측 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"수요 예측 중 오류 발생: {str(e)}"
        )


@router.post(
    "/success-rate",
    response_model=SuccessRatePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="견적 성공률 예측",
    description="견적의 성공 가능성을 예측합니다."
)
async def predict_success_rate(request: SuccessRatePredictionRequest):
    """
    견적 성공률 예측

    - 과거 유사 견적 분석
    - 성공 요인 분석
    - 개선 제안 제공
    """
    logger.info(f"성공률 예측 요청: 고객={request.customer_id}, 금액={request.estimate_amount}")

    try:
        service = get_prediction_service()

        result = await service.predict_success_rate(
            customer_id=request.customer_id,
            estimate_amount=request.estimate_amount,
            panel_count=request.panel_count,
            breaker_count=request.breaker_count,
            include_similar=request.include_similar_cases
        )

        return _convert_success_rate(result)

    except Exception as e:
        logger.error(f"성공률 예측 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"성공률 예측 중 오류 발생: {str(e)}"
        )


@router.post(
    "/trends",
    response_model=TrendAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="트렌드 분석",
    description="계절별/고객별/제품별 트렌드를 분석합니다."
)
async def analyze_trends(request: TrendAnalysisRequest):
    """
    트렌드 분석

    - 계절별 패턴 분석
    - 고객별 매출 트렌드
    - 제품별 수요 변화
    - 인사이트 및 권장사항 제공
    """
    logger.info(f"트렌드 분석 요청: {request.analysis_type}")

    try:
        service = get_prediction_service()

        result = await service.analyze_trends(
            analysis_type=request.analysis_type,
            period_months=request.period_months,
            top_n=request.top_n
        )

        return _convert_trend_analysis(result)

    except Exception as e:
        logger.error(f"트렌드 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"트렌드 분석 중 오류 발생: {str(e)}"
        )


@router.post(
    "/anomalies",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="이상 탐지",
    description="매출, 고객, 가격 등의 이상 패턴을 탐지합니다."
)
async def detect_anomalies(request: AnomalyDetectionRequest):
    """
    이상 탐지

    - 통계적 이상치 탐지
    - 패턴 이탈 감지
    - 심각도별 분류
    - 권장 조치 제공
    """
    logger.info(f"이상 탐지 요청: 범위={request.detection_scope}, 민감도={request.sensitivity}")

    try:
        service = get_prediction_service()

        result = await service.detect_anomalies(
            scope=request.detection_scope,
            sensitivity=request.sensitivity,
            lookback_days=request.lookback_days
        )

        return _convert_anomaly_detection(result)

    except Exception as e:
        logger.error(f"이상 탐지 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이상 탐지 중 오류 발생: {str(e)}"
        )


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="대시보드 요약",
    description="예측 분석 대시보드의 전체 요약을 조회합니다."
)
async def get_dashboard_summary(
    include_predictions: bool = Query(True, description="예측 포함 여부"),
    include_anomalies: bool = Query(True, description="이상 탐지 포함 여부"),
    include_trends: bool = Query(True, description="트렌드 포함 여부"),
    prediction_months: int = Query(3, ge=1, le=12, description="예측 기간 (월)")
):
    """
    대시보드 요약

    - KPI 지표 제공
    - 매출/수요 예측 요약
    - 이상 탐지 요약
    - 트렌드 분석 요약
    - 액션 아이템 및 알림
    """
    logger.info("대시보드 요약 요청")

    try:
        service = get_prediction_service()

        result = await service.get_dashboard_summary(
            include_predictions=include_predictions,
            include_anomalies=include_anomalies,
            include_trends=include_trends,
            prediction_months=prediction_months
        )

        # KPI 변환
        kpis = [
            KPIMetric(
                name=k["name"],
                current_value=k["current_value"],
                previous_value=k["previous_value"],
                change_rate=k["change_rate"],
                target_value=k.get("target_value"),
                status=k["status"]
            )
            for k in result.get("kpis", [])
        ]

        # 하위 분석 결과 변환
        sales_forecast = None
        if result.get("sales_forecast"):
            sales_forecast = _convert_sales_predictions(result["sales_forecast"])

        demand_forecast = None
        if result.get("demand_forecast"):
            demand_forecast = _convert_demand_predictions(result["demand_forecast"])

        anomaly_summary = None
        if result.get("anomaly_summary"):
            anomaly_summary = _convert_anomaly_detection(result["anomaly_summary"])

        trend_summary = None
        if result.get("trend_summary"):
            trend_summary = _convert_trend_analysis(result["trend_summary"])

        return DashboardSummaryResponse(
            request_id=result["request_id"],
            kpis=kpis,
            sales_forecast=sales_forecast,
            demand_forecast=demand_forecast,
            anomaly_summary=anomaly_summary,
            trend_summary=trend_summary,
            action_items=result.get("action_items", []),
            alerts=result.get("alerts", [])
        )

    except Exception as e:
        logger.error(f"대시보드 요약 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 요약 중 오류 발생: {str(e)}"
        )


@router.get(
    "/stats",
    summary="예측 분석 통계",
    description="예측 분석 시스템의 통계를 조회합니다."
)
async def get_prediction_stats():
    """예측 분석 통계 조회"""
    try:
        service = get_prediction_service()
        stats = service.get_stats()

        return {
            "stats": stats,
            "message": "통계 조회 완료"
        }

    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/quick-forecast",
    summary="빠른 매출 예측",
    description="다음 3개월 매출을 빠르게 예측합니다."
)
async def quick_forecast():
    """빠른 매출 예측 (3개월)"""
    try:
        service = get_prediction_service()

        today = date.today()
        # 다음 달 1일부터 3개월
        if today.month == 12:
            start = date(today.year + 1, 1, 1)
        else:
            start = date(today.year, today.month + 1, 1)

        end_month = start.month + 2
        end_year = start.year
        if end_month > 12:
            end_month -= 12
            end_year += 1
        end = date(end_year, end_month, 28)

        result = await service.predict_sales(start, end, "MONTHLY")

        # 간단한 요약
        total = result["total_predicted"]
        trend = result["trend"]

        trend_msg = {
            "UP": "상승 📈",
            "DOWN": "하락 📉",
            "STABLE": "안정 ➡️",
            "VOLATILE": "변동적 📊"
        }.get(trend, trend)

        return {
            "period": f"{start.isoformat()} ~ {end.isoformat()}",
            "total_predicted": total,
            "trend": trend,
            "message": f"향후 3개월 예측 매출: {total:,}원 (추세: {trend_msg})",
            "monthly_breakdown": [
                {
                    "month": p["prediction_date"],
                    "amount": p["predicted_amount"],
                    "confidence": p["confidence"]
                }
                for p in result["predictions"]
            ]
        }

    except Exception as e:
        logger.error(f"빠른 예측 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예측 중 오류 발생: {str(e)}"
        )


@router.get(
    "/alerts",
    summary="현재 알림 조회",
    description="현재 활성화된 이상 탐지 알림을 조회합니다."
)
async def get_current_alerts():
    """현재 알림 조회"""
    try:
        service = get_prediction_service()

        # 빠른 이상 탐지 (최근 7일, 높은 민감도)
        result = await service.detect_anomalies("ALL", "HIGH", 7)

        critical_alerts = [
            a for a in result.get("anomalies", [])
            if a["severity"] == "CRITICAL"
        ]

        warning_alerts = [
            a for a in result.get("anomalies", [])
            if a["severity"] == "WARNING"
        ]

        return {
            "system_health": result["system_health"],
            "critical_count": len(critical_alerts),
            "warning_count": len(warning_alerts),
            "critical_alerts": critical_alerts[:5],
            "warning_alerts": warning_alerts[:5],
            "message": f"시스템 상태: {result['system_health']} (심각: {len(critical_alerts)}건, 경고: {len(warning_alerts)}건)"
        }

    except Exception as e:
        logger.error(f"알림 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 조회 중 오류 발생: {str(e)}"
        )
