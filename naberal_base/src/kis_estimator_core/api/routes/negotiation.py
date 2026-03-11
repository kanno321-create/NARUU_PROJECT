"""
AI Negotiation Assistant API Routes (Phase XVII)

AI 협상 어시스턴트 API 엔드포인트
가격 분석, 협상 전략, 승패 분석, 역제안 대응 등

핵심 기능:
- 최적 가격 제안
- 협상 전략 추천
- 승패 분석 및 예측
- 역제안 대응 스크립트
- 가격 히스토리 분석
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from kis_estimator_core.api.schemas.negotiation import (
    # Price Analysis
    PriceAnalysisRequest,
    PriceAnalysisResponse,
    # Negotiation Strategy
    NegotiationStrategyRequest,
    NegotiationStrategyResponse,
    # Win-Loss Analysis
    WinLossFilter,
    WinLossAnalysisResponse,
    # Counter Offer
    CounterOfferRequest,
    CounterOfferResponse,
    # Price History
    PriceHistoryRequest,
    PriceHistoryResponse,
    # Quick Tips
    QuickTipRequest,
    QuickTipResponse,
    # Dashboard
    NegotiationDashboardResponse,
    # Types
    CustomerType,
)
from kis_estimator_core.services.negotiation_service import get_negotiation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/negotiation", tags=["AI Negotiation Assistant"])


# ============================================================================
# Price Analysis (가격 분석)
# ============================================================================

@router.post(
    "/price-analysis",
    response_model=PriceAnalysisResponse,
    summary="가격 분석",
    description="""
    제안 가격을 분석하고 최적 가격 범위, 마진, 경쟁 포지션을 제공합니다.

    분석 항목:
    - 가격 범위 (최소/권장/최대/최적)
    - 마진 분석 (마진율, 손익분기점)
    - 경쟁사 대비 포지션
    - 수주 확률 예측
    - 권장사항
    """
)
async def analyze_price(request: PriceAnalysisRequest):
    """가격 분석 API"""
    try:
        service = get_negotiation_service()
        result = await service.analyze_price(
            base_price=request.base_price,
            cost_price=request.cost_price,
            customer_type=request.customer_type,
            product_category=request.product_category,
            quantity=request.quantity,
            urgency=request.urgency
        )
        return result
    except Exception as e:
        logger.error(f"Price analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quick-price-check",
    summary="빠른 가격 체크",
    description="간단한 가격 적정성 체크"
)
async def quick_price_check(
    price: float = Query(..., gt=0, description="제안 가격"),
    cost: float = Query(..., gt=0, description="원가"),
    customer_type: CustomerType = Query(default="NEW", description="고객 유형")
):
    """빠른 가격 체크"""
    margin_rate = ((price - cost) / price) * 100 if price > 0 else 0

    if margin_rate < 10:
        status = "RISKY"
        message = "마진이 너무 낮습니다. 가격 인상을 권장합니다."
    elif margin_rate < 15:
        status = "LOW"
        message = "마진이 낮습니다. 추가 할인에 주의하세요."
    elif margin_rate < 25:
        status = "GOOD"
        message = "적정 마진입니다."
    else:
        status = "HIGH"
        message = "마진 여력이 충분합니다. 경쟁력 있는 가격 제안이 가능합니다."

    return {
        "price": price,
        "cost": cost,
        "margin_rate": round(margin_rate, 1),
        "status": status,
        "message": message,
        "recommended_min_price": round(cost * 1.15, 0)
    }


# ============================================================================
# Negotiation Strategy (협상 전략)
# ============================================================================

@router.post(
    "/strategy",
    response_model=NegotiationStrategyResponse,
    summary="협상 전략 생성",
    description="""
    현재 협상 상황을 분석하고 최적의 전략을 추천합니다.

    제공 정보:
    - 주요 전략 및 대안 전략
    - 가격 조정 제안
    - 협상 포인트 (핵심 메시지, 근거, 피해야 할 주제)
    - 수주 확률 및 예상 최종 가격
    """
)
async def generate_strategy(request: NegotiationStrategyRequest):
    """협상 전략 생성 API"""
    try:
        service = get_negotiation_service()
        result = await service.generate_strategy(
            context=request.context.model_dump(),
            min_acceptable_price=request.min_acceptable_price,
            target_margin_rate=request.target_margin_rate,
            priority=request.priority
        )
        return result
    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/strategy/quick",
    summary="빠른 전략 조언",
    description="간단한 상황 설명으로 빠른 전략 조언 제공"
)
async def quick_strategy_advice(
    situation: str = Query(..., min_length=5, description="현재 상황"),
    price_gap_pct: float = Query(default=0, description="가격 차이 (%)"),
    customer_type: CustomerType = Query(default="NEW", description="고객 유형")
):
    """빠른 전략 조언"""
    if price_gap_pct <= 5:
        strategy = "수용 검토"
        advice = "가격 차이가 작습니다. 소폭 조정 후 합의를 시도하세요."
    elif price_gap_pct <= 15:
        strategy = "협상 지속"
        advice = "중간 지점을 제안하고, 부가 가치를 강조하세요."
    else:
        strategy = "가치 기반 재제안"
        advice = "가격보다 가치를 강조하는 방향으로 전환하세요."

    if customer_type in ["VIP", "STRATEGIC"]:
        advice += " 장기 관계를 고려한 유연한 접근을 권장합니다."

    return {
        "situation": situation,
        "recommended_strategy": strategy,
        "advice": advice,
        "key_action": "가치 제안 강화" if price_gap_pct > 10 else "타협점 모색"
    }


# ============================================================================
# Win-Loss Analysis (승패 분석)
# ============================================================================

@router.post(
    "/win-loss",
    response_model=WinLossAnalysisResponse,
    summary="승패 분석",
    description="""
    지정 기간의 영업 성과를 분석합니다.

    분석 항목:
    - 핵심 지표 (수주율, 평균 거래 규모, 마진)
    - 실주 원인 분석
    - 수주 성공 요인
    - 업계 벤치마크 대비 성과
    - 개선 제안
    """
)
async def analyze_win_loss(request: WinLossFilter):
    """승패 분석 API"""
    try:
        service = get_negotiation_service()
        result = await service.analyze_win_loss(
            start_date=request.start_date,
            end_date=request.end_date,
            customer_type=request.customer_type,
            product_category=request.product_category
        )
        return result
    except Exception as e:
        logger.error(f"Win-loss analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/win-loss/summary",
    summary="승패 분석 요약",
    description="최근 30일 승패 분석 요약"
)
async def win_loss_summary():
    """승패 분석 요약"""
    service = get_negotiation_service()
    today = date.today()
    result = await service.analyze_win_loss(
        start_date=today - timedelta(days=30),
        end_date=today
    )

    return {
        "period": "최근 30일",
        "win_rate": result["metrics"]["win_rate"],
        "total_opportunities": result["metrics"]["total_opportunities"],
        "wins": result["metrics"]["wins"],
        "losses": result["metrics"]["losses"],
        "top_loss_reason": result["loss_reasons"][0]["reason"] if result["loss_reasons"] else None,
        "key_insight": result["key_insights"][0] if result["key_insights"] else None
    }


# ============================================================================
# Counter Offer (역제안 대응)
# ============================================================================

@router.post(
    "/counter-offer",
    response_model=CounterOfferResponse,
    summary="역제안 대응",
    description="""
    고객 역제안에 대한 최적 대응 방안을 제공합니다.

    제공 정보:
    - 가격 차이 분석
    - 추천 대응 옵션 (가격, 할인율, 마진, 수주 확률)
    - 응답 스크립트
    - 핵심 논점 및 피해야 할 양보
    - 협상 중단 권고 여부
    """
)
async def respond_to_counter_offer(request: CounterOfferRequest):
    """역제안 대응 API"""
    try:
        service = get_negotiation_service()
        result = await service.respond_to_counter_offer(
            original_price=request.original_price,
            customer_counter_price=request.customer_counter_price,
            cost_price=request.cost_price,
            customer_type=request.customer_type,
            reason_given=request.reason_given,
            is_final_offer=request.is_final_offer
        )
        return result
    except Exception as e:
        logger.error(f"Counter offer response failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/counter-offer/quick",
    summary="빠른 역제안 가이드",
    description="간단한 역제안 대응 가이드"
)
async def quick_counter_offer_guide(
    original: float = Query(..., gt=0, description="원래 가격"),
    counter: float = Query(..., gt=0, description="고객 역제안가"),
    cost: float = Query(..., gt=0, description="원가")
):
    """빠른 역제안 가이드"""
    gap = original - counter
    gap_pct = (gap / original) * 100
    min_acceptable = cost * 1.1
    is_acceptable = counter >= min_acceptable

    if gap_pct <= 5:
        recommendation = "수용 검토"
        action = "소폭 조정 후 합의 가능"
    elif gap_pct <= 15:
        recommendation = "역제안"
        midpoint = (original + counter) / 2
        action = f"{midpoint:,.0f}원 수준으로 역제안 권장"
    else:
        recommendation = "가치 재설명"
        action = "가격보다 가치 강조, 패키지 제안 검토"

    return {
        "price_gap": round(gap, 0),
        "price_gap_pct": round(gap_pct, 1),
        "is_acceptable": is_acceptable,
        "min_acceptable_price": round(min_acceptable, 0),
        "recommendation": recommendation,
        "suggested_action": action
    }


# ============================================================================
# Price History (가격 히스토리)
# ============================================================================

@router.post(
    "/price-history",
    response_model=PriceHistoryResponse,
    summary="가격 히스토리 조회",
    description="""
    과거 가격 협상 기록을 조회합니다.

    제공 정보:
    - 협상 히스토리 (초기가, 최종가, 할인율, 결과)
    - 가격 통계 (평균 초기가, 최종가, 할인율)
    - 가격 트렌드
    - 인사이트
    """
)
async def get_price_history(request: PriceHistoryRequest):
    """가격 히스토리 조회 API"""
    try:
        service = get_negotiation_service()
        result = await service.get_price_history(
            customer_id=request.customer_id,
            product_category=request.product_category,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return result
    except Exception as e:
        logger.error(f"Price history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/price-history/stats",
    summary="가격 통계",
    description="가격 협상 통계 요약"
)
async def price_history_stats(
    days: int = Query(default=90, ge=7, le=365, description="분석 기간 (일)")
):
    """가격 통계 조회"""
    service = get_negotiation_service()
    today = date.today()
    result = await service.get_price_history(
        start_date=today - timedelta(days=days),
        end_date=today
    )

    return {
        "period_days": days,
        "total_negotiations": result["total_records"],
        "average_initial_price": result["average_initial_price"],
        "average_final_price": result["average_final_price"],
        "average_discount_rate": result["average_discount_rate"],
        "price_trend": "상승" if result["trends"] and result["trends"][0]["price_change_pct"] > 0 else "하락"
    }


# ============================================================================
# Quick Tips (빠른 팁)
# ============================================================================

@router.post(
    "/quick-tip",
    response_model=QuickTipResponse,
    summary="빠른 협상 팁",
    description="""
    현재 협상 상황에 대한 즉시 사용 가능한 팁을 제공합니다.

    제공 정보:
    - 즉시 응답 (멘트)
    - 해야 할 것 / 하지 말아야 할 것
    - 추가 할인 한도
    - 가격 외 양보 옵션
    """
)
async def get_quick_tip(request: QuickTipRequest):
    """빠른 협상 팁 API"""
    try:
        service = get_negotiation_service()
        result = await service.get_quick_tip(
            situation=request.situation,
            customer_statement=request.customer_statement,
            current_discount=request.current_discount
        )
        return result
    except Exception as e:
        logger.error(f"Quick tip generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tips/daily",
    summary="오늘의 협상 팁",
    description="오늘의 협상 팁 제공"
)
async def daily_tip():
    """오늘의 협상 팁"""
    import random

    tips = [
        {
            "tip": "첫 제안에서 최종가를 내놓지 마세요.",
            "explanation": "협상 여지를 남겨두면 고객에게 '성취감'을 줄 수 있습니다."
        },
        {
            "tip": "고객의 말을 80% 이상 경청하세요.",
            "explanation": "고객의 진정한 니즈를 파악하는 것이 협상 성공의 열쇠입니다."
        },
        {
            "tip": "가격보다 가치를 먼저 설명하세요.",
            "explanation": "가치 인식이 선행되면 가격 협상이 수월해집니다."
        },
        {
            "tip": "침묵은 강력한 협상 도구입니다.",
            "explanation": "제안 후 침묵하면 상대방이 먼저 양보를 고려합니다."
        },
        {
            "tip": "'아니오' 대신 '예, 그리고...'를 사용하세요.",
            "explanation": "긍정적 프레이밍이 협상 분위기를 좋게 만듭니다."
        },
        {
            "tip": "감정이 아닌 데이터로 설득하세요.",
            "explanation": "객관적 근거는 감정적 반발을 줄입니다."
        },
        {
            "tip": "최종 결정권자를 파악하세요.",
            "explanation": "결정권자와의 직접 대화가 협상 시간을 단축합니다."
        }
    ]

    selected = random.choice(tips)
    return {
        "tip_of_the_day": selected["tip"],
        "explanation": selected["explanation"],
        "category": "협상 스킬"
    }


# ============================================================================
# Dashboard (대시보드)
# ============================================================================

@router.get(
    "/dashboard",
    response_model=NegotiationDashboardResponse,
    summary="협상 대시보드",
    description="""
    협상 현황 대시보드를 제공합니다.

    표시 정보:
    - 진행 중 협상 건수
    - 30일 평균 수주율
    - 평균 할인율
    - 총 파이프라인 가치
    - 추세 (수주율, 마진)
    - 긴급/위험 거래
    - 오늘의 팁
    """
)
async def get_dashboard():
    """협상 대시보드 API"""
    try:
        service = get_negotiation_service()
        result = await service.get_dashboard()
        return result
    except Exception as e:
        logger.error(f"Dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/dashboard/kpi",
    summary="핵심 KPI",
    description="핵심 협상 KPI 조회"
)
async def get_kpi():
    """핵심 KPI 조회"""
    service = get_negotiation_service()
    dashboard = await service.get_dashboard()

    return {
        "win_rate": dashboard["avg_win_rate_30d"],
        "win_rate_trend": dashboard["win_rate_trend"],
        "avg_discount": dashboard["avg_discount_rate"],
        "active_deals": dashboard["active_negotiations"],
        "pipeline_value": dashboard["total_pipeline_value"],
        "at_risk_count": len(dashboard["at_risk_deals"])
    }


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get(
    "/benchmark",
    summary="업계 벤치마크",
    description="업계 평균 협상 지표 조회"
)
async def get_benchmark():
    """업계 벤치마크"""
    service = get_negotiation_service()

    return {
        "industry_avg_win_rate": service.INDUSTRY_AVG_WIN_RATE,
        "industry_avg_margin": service.INDUSTRY_AVG_MARGIN,
        "typical_discount_range": {"min": 5, "max": 15},
        "average_negotiation_rounds": 2.5,
        "source": "Internal Analysis",
        "updated_at": date.today().isoformat()
    }


@router.get(
    "/status",
    summary="협상 어시스턴트 상태",
    description="AI 협상 어시스턴트 서비스 상태 확인"
)
async def negotiation_status():
    """서비스 상태 확인"""
    service = get_negotiation_service()

    return {
        "status": "operational",
        "service": "AI Negotiation Assistant",
        "version": "1.0.0",
        "capabilities": [
            "가격 분석",
            "협상 전략 추천",
            "승패 분석",
            "역제안 대응",
            "가격 히스토리",
            "빠른 협상 팁",
            "대시보드"
        ],
        "total_records": len(service._records),
        "message": "AI 협상 어시스턴트가 정상 운영 중입니다."
    }
