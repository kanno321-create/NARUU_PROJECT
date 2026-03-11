"""
AI Negotiation Assistant Service (Phase XVII)

AI 협상 어시스턴트 서비스 구현
가격 분석, 협상 전략, 승패 분석, 역제안 대응 등 제공

핵심 기능:
- 최적 가격 제안 (마진 + 시장 + 승률 분석)
- 협상 전략 추천 (고객 유형, 상황별)
- 승패 분석 및 예측 (히스토리 기반)
- 역제안 대응 스크립트 생성
- 가격 히스토리 분석
"""

import logging
import uuid
import random
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Optional, Literal

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PriceAnalysisResult:
    """가격 분석 결과"""
    min_price: float
    recommended_price: float
    max_price: float
    optimal_price: float
    margin_rate: float
    win_probability: float
    confidence: str


@dataclass
class NegotiationRecord:
    """협상 기록"""
    estimate_id: str
    customer_id: str
    customer_type: str
    initial_price: float
    final_price: float
    cost_price: float
    outcome: str  # WON, LOST, PENDING
    negotiation_rounds: int
    loss_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Negotiation Service
# ============================================================================

class NegotiationService:
    """AI 협상 어시스턴트 서비스"""

    # 업계 기준 데이터
    INDUSTRY_AVG_WIN_RATE = 35.0
    INDUSTRY_AVG_MARGIN = 18.0
    TARGET_MARGIN_RATES = {
        "NEW": 20.0,
        "RETURNING": 18.0,
        "VIP": 15.0,
        "STRATEGIC": 12.0
    }

    # 손실 원인 패턴
    LOSS_REASONS = [
        ("가격 경쟁력 부족", 35.0),
        ("경쟁사 선택", 25.0),
        ("예산 초과", 20.0),
        ("사양 불일치", 10.0),
        ("납기 문제", 7.0),
        ("기타", 3.0)
    ]

    # 수주 성공 요인
    WIN_FACTORS = [
        ("가격 경쟁력", 30.0),
        ("기술 지원", 25.0),
        ("납기 준수", 20.0),
        ("브랜드 신뢰", 15.0),
        ("관계 영업", 10.0)
    ]

    def __init__(self):
        self._records: list[NegotiationRecord] = []
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """샘플 협상 기록 초기화"""
        customer_types = ["NEW", "RETURNING", "VIP", "STRATEGIC"]
        outcomes = ["WON", "WON", "WON", "LOST", "LOST", "PENDING"]

        for i in range(50):
            customer_type = random.choice(customer_types)
            outcome = random.choice(outcomes)
            initial_price = random.uniform(500000, 5000000)
            discount = random.uniform(0, 20) if outcome == "WON" else random.uniform(0, 10)
            final_price = initial_price * (1 - discount / 100)

            record = NegotiationRecord(
                estimate_id=f"EST-2024-{1000+i}",
                customer_id=f"CUST-{100+i}",
                customer_type=customer_type,
                initial_price=initial_price,
                final_price=final_price,
                cost_price=initial_price * 0.7,
                outcome=outcome,
                negotiation_rounds=random.randint(1, 5),
                loss_reason=random.choice([r[0] for r in self.LOSS_REASONS]) if outcome == "LOST" else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 180))
            )
            self._records.append(record)

    # ========================================================================
    # Price Analysis (가격 분석)
    # ========================================================================

    async def analyze_price(
        self,
        base_price: float,
        cost_price: float,
        customer_type: str = "NEW",
        product_category: str = "PANEL",
        quantity: int = 1,
        urgency: str = "NORMAL"
    ) -> dict:
        """
        가격 분석 수행

        Args:
            base_price: 기본 가격
            cost_price: 원가
            customer_type: 고객 유형
            product_category: 제품 카테고리
            quantity: 수량
            urgency: 긴급도

        Returns:
            가격 분석 결과
        """
        request_id = str(uuid.uuid4())[:8]

        # 마진 분석
        gross_margin = base_price - cost_price
        margin_rate = (gross_margin / base_price) * 100 if base_price > 0 else 0
        target_margin = self.TARGET_MARGIN_RATES.get(customer_type, 18.0)

        # 가격 범위 계산
        min_price = cost_price * 1.08  # 최소 8% 마진
        max_price = base_price * 1.15  # 시장 상한
        recommended_price = cost_price * (1 + target_margin / 100)
        optimal_price = self._calculate_optimal_price(
            base_price, cost_price, customer_type, urgency
        )

        # 승률 예측
        win_probability = self._predict_win_probability(
            base_price, optimal_price, customer_type, urgency
        )

        # 신뢰도 결정
        if win_probability >= 70:
            confidence = "HIGH"
        elif win_probability >= 50:
            confidence = "MEDIUM"
        elif margin_rate < 10:
            confidence = "RISKY"
        else:
            confidence = "LOW"

        # 시장 포지션 분석
        market_average = base_price * 0.95  # 시뮬레이션
        price_diff_pct = ((base_price - market_average) / market_average) * 100

        if price_diff_pct < -5:
            position = "BELOW"
        elif price_diff_pct > 5:
            position = "ABOVE"
        else:
            position = "AVERAGE"

        # 경쟁 우위 요소 (시뮬레이션)
        advantages = []
        if margin_rate > 20:
            advantages.append("가격 조정 여력 충분")
        if quantity > 3:
            advantages.append("대량 구매 할인 가능")
        if customer_type == "VIP":
            advantages.append("장기 관계 기반 신뢰")
        if urgency == "URGENT":
            advantages.append("긴급 대응 능력")

        # 권장사항 생성
        recommendations = self._generate_price_recommendations(
            margin_rate, win_probability, customer_type, position
        )

        return {
            "request_id": request_id,
            "base_price": base_price,
            "price_range": {
                "min_price": round(min_price, 0),
                "recommended_price": round(recommended_price, 0),
                "max_price": round(max_price, 0),
                "optimal_price": round(optimal_price, 0)
            },
            "margin_analysis": {
                "cost_price": cost_price,
                "gross_margin": round(gross_margin, 0),
                "margin_rate": round(margin_rate, 1),
                "break_even_price": cost_price,
                "target_margin_rate": target_margin
            },
            "competitor_position": {
                "market_average": round(market_average, 0),
                "our_position": position,
                "price_difference_pct": round(price_diff_pct, 1),
                "competitive_advantage": advantages
            },
            "confidence": confidence,
            "win_probability": round(win_probability, 1),
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_optimal_price(
        self,
        base_price: float,
        cost_price: float,
        customer_type: str,
        urgency: str
    ) -> float:
        """최적 가격 계산"""
        target_margin = self.TARGET_MARGIN_RATES.get(customer_type, 18.0)

        # 긴급도에 따른 조정
        urgency_factor = {
            "LOW": 1.05,
            "NORMAL": 1.0,
            "HIGH": 0.98,
            "URGENT": 0.95
        }.get(urgency, 1.0)

        optimal = cost_price * (1 + target_margin / 100) * urgency_factor
        return min(max(optimal, cost_price * 1.1), base_price * 1.1)

    def _predict_win_probability(
        self,
        base_price: float,
        optimal_price: float,
        customer_type: str,
        urgency: str
    ) -> float:
        """승률 예측"""
        base_prob = 50.0

        # 가격 요인
        price_ratio = base_price / optimal_price
        if price_ratio > 1.1:
            base_prob -= 15
        elif price_ratio < 0.95:
            base_prob += 10

        # 고객 유형 요인
        customer_factor = {
            "NEW": 0,
            "RETURNING": 10,
            "VIP": 15,
            "STRATEGIC": 20
        }.get(customer_type, 0)
        base_prob += customer_factor

        # 긴급도 요인
        if urgency == "URGENT":
            base_prob += 10

        return max(min(base_prob, 95), 10)

    def _generate_price_recommendations(
        self,
        margin_rate: float,
        win_probability: float,
        customer_type: str,
        position: str
    ) -> list:
        """가격 권장사항 생성"""
        recommendations = []

        if margin_rate < 15:
            recommendations.append("마진율이 낮습니다. 가격 인상 또는 비용 절감을 검토하세요.")
        if margin_rate > 25:
            recommendations.append("마진 여력이 충분합니다. 경쟁력 있는 가격 제안이 가능합니다.")

        if win_probability < 40:
            recommendations.append("수주 확률이 낮습니다. 가격 조정 또는 부가 서비스 제공을 고려하세요.")
        if win_probability > 70:
            recommendations.append("수주 확률이 높습니다. 현재 가격 유지를 권장합니다.")

        if customer_type == "VIP":
            recommendations.append("VIP 고객입니다. 장기 관계를 고려한 유연한 협상을 권장합니다.")
        if customer_type == "NEW":
            recommendations.append("신규 고객입니다. 첫 거래 성공을 위한 경쟁력 있는 가격을 제안하세요.")

        if position == "ABOVE":
            recommendations.append("시장 평균보다 높은 가격입니다. 차별화 포인트를 강조하세요.")
        elif position == "BELOW":
            recommendations.append("시장 평균보다 낮은 가격입니다. 마진 확보에 유의하세요.")

        return recommendations[:5]

    # ========================================================================
    # Negotiation Strategy (협상 전략)
    # ========================================================================

    async def generate_strategy(
        self,
        context: dict,
        min_acceptable_price: Optional[float] = None,
        target_margin_rate: float = 15.0,
        priority: str = "PRICE"
    ) -> dict:
        """
        협상 전략 생성

        Args:
            context: 협상 컨텍스트
            min_acceptable_price: 최저 수용 가격
            target_margin_rate: 목표 마진율
            priority: 협상 우선순위

        Returns:
            협상 전략
        """
        request_id = str(uuid.uuid4())[:8]

        current_price = context.get("current_price", 0)
        customer_target = context.get("customer_target_price")
        customer_type = context.get("customer_type", "NEW")
        phase = context.get("negotiation_phase", "INITIAL")
        competitor_mentioned = context.get("competitor_mentioned", False)

        # 상황 요약
        context_summary = self._summarize_context(context)

        # 전략 선택
        primary_strategy = self._select_primary_strategy(
            context, priority, phase
        )
        alternative_strategies = self._get_alternative_strategies(
            primary_strategy["strategy"], context
        )

        # 가격 전략
        price_move = self._calculate_price_move(
            current_price, customer_target, min_acceptable_price, phase
        )

        # 협상 포인트
        talking_points = self._generate_talking_points(
            context, primary_strategy["strategy"], competitor_mentioned
        )

        # 승률 예측
        win_probability = self._estimate_strategy_success(
            context, price_move, primary_strategy["strategy"]
        )

        # 예상 최종 가격
        expected_final = self._estimate_final_price(
            current_price, customer_target, phase
        )

        return {
            "request_id": request_id,
            "context_summary": context_summary,
            "primary_strategy": primary_strategy,
            "alternative_strategies": alternative_strategies,
            "price_move": price_move,
            "price_floor": min_acceptable_price or current_price * 0.85,
            "talking_points": talking_points,
            "win_probability": round(win_probability, 1),
            "expected_final_price": round(expected_final, 0),
            "generated_at": datetime.utcnow().isoformat()
        }

    def _summarize_context(self, context: dict) -> str:
        """협상 컨텍스트 요약"""
        customer_type = context.get("customer_type", "NEW")
        phase = context.get("negotiation_phase", "INITIAL")
        current_price = context.get("current_price", 0)
        customer_target = context.get("customer_target_price")

        summary = f"{customer_type} 고객과의 {phase} 단계 협상. "
        summary += f"현재 제안가 {current_price:,.0f}원"
        if customer_target:
            gap = ((current_price - customer_target) / current_price) * 100
            summary += f", 고객 목표가와 {gap:.1f}% 차이"
        summary += "."

        return summary

    def _select_primary_strategy(
        self,
        context: dict,
        priority: str,
        phase: str
    ) -> dict:
        """주요 전략 선택"""
        customer_type = context.get("customer_type", "NEW")
        competitor_mentioned = context.get("competitor_mentioned", False)

        if priority == "RELATIONSHIP" or customer_type in ["VIP", "STRATEGIC"]:
            strategy = "RELATIONSHIP"
            rationale = "장기 관계 유지가 중요한 고객입니다."
            outcome = "신뢰 기반의 합의 도출"
        elif competitor_mentioned:
            strategy = "COMPETITIVE"
            rationale = "경쟁사가 언급되었습니다. 차별화 포인트 강조 필요."
            outcome = "가치 기반 차별화 성공"
        elif phase == "FINAL":
            strategy = "VALUE_BASED"
            rationale = "최종 단계입니다. 가치 제안에 집중하세요."
            outcome = "가치 인식 기반 합의"
        elif priority == "PRICE":
            strategy = "BALANCED"
            rationale = "가격과 관계의 균형이 필요합니다."
            outcome = "상호 수용 가능한 합의"
        else:
            strategy = "BALANCED"
            rationale = "표준적인 협상 접근법입니다."
            outcome = "합리적 타협점 도출"

        return {
            "strategy": strategy,
            "confidence": random.uniform(0.7, 0.95),
            "rationale": rationale,
            "expected_outcome": outcome
        }

    def _get_alternative_strategies(
        self,
        primary: str,
        context: dict
    ) -> list:
        """대안 전략 제공"""
        all_strategies = ["AGGRESSIVE", "BALANCED", "RELATIONSHIP", "VALUE_BASED", "COMPETITIVE"]
        alternatives = [s for s in all_strategies if s != primary][:2]

        result = []
        for strategy in alternatives:
            result.append({
                "strategy": strategy,
                "confidence": random.uniform(0.5, 0.75),
                "rationale": f"{strategy} 전략으로 전환 시 다른 결과 가능",
                "expected_outcome": "대안적 합의 가능"
            })
        return result

    def _calculate_price_move(
        self,
        current_price: float,
        customer_target: Optional[float],
        min_price: Optional[float],
        phase: str
    ) -> dict:
        """가격 조정 제안"""
        if not customer_target:
            return {
                "move_type": "HOLD",
                "suggested_price": current_price,
                "discount_rate": 0,
                "justification": "고객 목표가 미제시. 현재 가격 유지 권장.",
                "counter_arguments": ["품질과 서비스 가치 강조", "시장 가격 대비 경쟁력 설명"]
            }

        gap = current_price - customer_target
        gap_pct = (gap / current_price) * 100

        if gap_pct <= 5:
            # 차이가 작음 - 수용 가능
            move_type = "DECREASE"
            suggested_price = customer_target * 1.02
            discount = ((current_price - suggested_price) / current_price) * 100
            justification = "고객 목표가에 근접. 소폭 조정으로 합의 가능."
        elif gap_pct <= 15:
            # 중간 정도 차이 - 협상 여지
            move_type = "DECREASE"
            suggested_price = current_price * 0.93
            discount = 7.0
            justification = "중간 지점 제안으로 협상 진전 유도."
        else:
            # 차이가 큼 - 가치 제안
            move_type = "PACKAGE"
            suggested_price = current_price * 0.95
            discount = 5.0
            justification = "가격 차이가 큽니다. 부가 서비스 포함 패키지 제안 권장."

        if min_price and suggested_price < min_price:
            suggested_price = min_price
            discount = ((current_price - min_price) / current_price) * 100
            justification = "최저 수용가 기준 제안. 추가 할인 불가."

        return {
            "move_type": move_type,
            "suggested_price": round(suggested_price, 0),
            "discount_rate": round(discount, 1),
            "justification": justification,
            "counter_arguments": [
                "원가 상승으로 추가 할인 어려움",
                "이미 경쟁력 있는 가격임",
                "품질 대비 합리적인 가격"
            ]
        }

    def _generate_talking_points(
        self,
        context: dict,
        strategy: str,
        competitor_mentioned: bool
    ) -> list:
        """협상 포인트 생성"""
        points = []

        if strategy == "VALUE_BASED":
            points.append({
                "topic": "가치 제안",
                "key_message": "가격보다 총 소유 비용(TCO)을 고려해 주세요.",
                "supporting_facts": ["10년 보증", "무상 기술 지원", "빠른 A/S 대응"],
                "avoid_topics": ["단순 가격 비교"]
            })

        if competitor_mentioned:
            points.append({
                "topic": "경쟁사 대응",
                "key_message": "저희 제품의 차별화된 특장점을 설명드리겠습니다.",
                "supporting_facts": ["품질 인증", "고객 만족도", "기술력"],
                "avoid_topics": ["경쟁사 직접 비방"]
            })

        if strategy == "RELATIONSHIP":
            points.append({
                "topic": "장기 파트너십",
                "key_message": "단발성 거래가 아닌 장기 파트너로서 최선을 다하겠습니다.",
                "supporting_facts": ["기존 거래 실적", "안정적 공급", "맞춤 서비스"],
                "avoid_topics": ["일회성 할인 요구"]
            })

        # 기본 포인트 추가
        points.append({
            "topic": "품질 보증",
            "key_message": "최고 품질의 제품과 서비스를 보장합니다.",
            "supporting_facts": ["ISO 인증", "국내 생산", "엄격한 품질 관리"],
            "avoid_topics": ["저가 제품과의 직접 비교"]
        })

        return points[:4]

    def _estimate_strategy_success(
        self,
        context: dict,
        price_move: dict,
        strategy: str
    ) -> float:
        """전략 성공 확률 추정"""
        base_prob = 50.0

        # 고객 유형 영향
        customer_type = context.get("customer_type", "NEW")
        customer_factor = {
            "NEW": 0,
            "RETURNING": 10,
            "VIP": 15,
            "STRATEGIC": 20
        }.get(customer_type, 0)
        base_prob += customer_factor

        # 가격 조정 영향
        if price_move["move_type"] == "DECREASE":
            base_prob += 10
        elif price_move["move_type"] == "PACKAGE":
            base_prob += 5

        # 전략 적합성 (시뮬레이션)
        base_prob += random.uniform(-5, 10)

        return max(min(base_prob, 90), 20)

    def _estimate_final_price(
        self,
        current_price: float,
        customer_target: Optional[float],
        phase: str
    ) -> float:
        """예상 최종 가격"""
        if not customer_target:
            return current_price * 0.95

        # 중간점 기반 예측
        midpoint = (current_price + customer_target) / 2

        if phase == "FINAL":
            return midpoint * 0.98
        elif phase == "COUNTER_OFFER":
            return midpoint
        else:
            return current_price * 0.95

    # ========================================================================
    # Win-Loss Analysis (승패 분석)
    # ========================================================================

    async def analyze_win_loss(
        self,
        start_date: date,
        end_date: date,
        customer_type: Optional[str] = None,
        product_category: Optional[str] = None
    ) -> dict:
        """승패 분석 수행"""
        request_id = str(uuid.uuid4())[:8]

        # 기간 필터
        filtered = [
            r for r in self._records
            if start_date <= r.created_at.date() <= end_date
        ]

        if customer_type:
            filtered = [r for r in filtered if r.customer_type == customer_type]

        # 지표 계산
        total = len(filtered)
        wins = len([r for r in filtered if r.outcome == "WON"])
        losses = len([r for r in filtered if r.outcome == "LOST"])
        pending = len([r for r in filtered if r.outcome == "PENDING"])
        win_rate = (wins / total * 100) if total > 0 else 0

        won_records = [r for r in filtered if r.outcome == "WON"]
        avg_deal_size = sum(r.final_price for r in won_records) / len(won_records) if won_records else 0
        avg_margin = sum(
            ((r.final_price - r.cost_price) / r.final_price * 100) for r in won_records
        ) / len(won_records) if won_records else 0

        # 손실 원인 분석
        loss_records = [r for r in filtered if r.outcome == "LOST"]
        loss_reasons = []
        for reason, _ in self.LOSS_REASONS:
            count = len([r for r in loss_records if r.loss_reason == reason])
            if count > 0:
                loss_reasons.append({
                    "reason": reason,
                    "count": count,
                    "percentage": round(count / len(loss_records) * 100, 1) if loss_records else 0,
                    "typical_price_gap": random.uniform(5, 15)
                })

        # 수주 요인
        win_factors = [
            {
                "factor": factor,
                "impact_score": round(impact, 1),
                "occurrence_rate": round(random.uniform(60, 90), 1)
            }
            for factor, impact in self.WIN_FACTORS
        ]

        # 인사이트 생성
        insights = self._generate_win_loss_insights(
            win_rate, avg_margin, loss_reasons, filtered
        )

        # 개선 제안
        suggestions = self._generate_improvement_suggestions(
            win_rate, loss_reasons, avg_margin
        )

        # 벤치마크 비교
        if win_rate > self.INDUSTRY_AVG_WIN_RATE + 10:
            benchmark = "우수 (업계 평균 대비 +{:.1f}%)".format(win_rate - self.INDUSTRY_AVG_WIN_RATE)
        elif win_rate < self.INDUSTRY_AVG_WIN_RATE - 10:
            benchmark = "개선 필요 (업계 평균 대비 {:.1f}%)".format(win_rate - self.INDUSTRY_AVG_WIN_RATE)
        else:
            benchmark = "평균 수준"

        return {
            "request_id": request_id,
            "period": f"{start_date} ~ {end_date}",
            "metrics": {
                "total_opportunities": total,
                "wins": wins,
                "losses": losses,
                "pending": pending,
                "win_rate": round(win_rate, 1),
                "average_deal_size": round(avg_deal_size, 0),
                "average_margin": round(avg_margin, 1)
            },
            "loss_reasons": loss_reasons[:5],
            "win_factors": win_factors,
            "key_insights": insights,
            "improvement_suggestions": suggestions,
            "industry_avg_win_rate": self.INDUSTRY_AVG_WIN_RATE,
            "performance_vs_benchmark": benchmark,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _generate_win_loss_insights(
        self,
        win_rate: float,
        avg_margin: float,
        loss_reasons: list,
        records: list
    ) -> list:
        """승패 인사이트 생성"""
        insights = []

        if win_rate > 50:
            insights.append(f"수주율 {win_rate:.1f}%로 양호한 성과를 보이고 있습니다.")
        else:
            insights.append(f"수주율 {win_rate:.1f}%로 개선이 필요합니다.")

        if avg_margin > self.INDUSTRY_AVG_MARGIN:
            insights.append(f"평균 마진율 {avg_margin:.1f}%로 수익성이 양호합니다.")
        else:
            insights.append(f"평균 마진율 {avg_margin:.1f}%로 수익성 개선이 필요합니다.")

        if loss_reasons:
            top_reason = loss_reasons[0]["reason"]
            insights.append(f"주요 실주 원인은 '{top_reason}'입니다.")

        return insights[:5]

    def _generate_improvement_suggestions(
        self,
        win_rate: float,
        loss_reasons: list,
        avg_margin: float
    ) -> list:
        """개선 제안 생성"""
        suggestions = []

        if win_rate < 40:
            suggestions.append("가격 경쟁력 분석 및 조정을 권장합니다.")
            suggestions.append("경쟁사 분석 강화가 필요합니다.")

        if loss_reasons and loss_reasons[0]["reason"] == "가격 경쟁력 부족":
            suggestions.append("가격 정책 재검토 및 부가 가치 제안 강화를 고려하세요.")

        if avg_margin < 15:
            suggestions.append("원가 절감 방안을 검토하세요.")
            suggestions.append("고부가가치 제품/서비스 비중을 높이세요.")

        suggestions.append("영업 교육 및 협상 스킬 향상 프로그램을 운영하세요.")
        suggestions.append("고객 피드백 수집 및 분석을 강화하세요.")

        return suggestions[:5]

    # ========================================================================
    # Counter Offer (역제안 대응)
    # ========================================================================

    async def respond_to_counter_offer(
        self,
        original_price: float,
        customer_counter_price: float,
        cost_price: float,
        customer_type: str = "NEW",
        reason_given: Optional[str] = None,
        is_final_offer: bool = False
    ) -> dict:
        """역제안 대응 생성"""
        request_id = str(uuid.uuid4())[:8]

        # 가격 차이 분석
        price_gap = original_price - customer_counter_price
        price_gap_pct = (price_gap / original_price) * 100
        min_acceptable = cost_price * 1.1

        is_acceptable = customer_counter_price >= min_acceptable

        # 상황 분석
        if price_gap_pct <= 5:
            analysis = "고객 역제안가가 합리적인 범위입니다. 수용 검토 가능."
        elif price_gap_pct <= 15:
            analysis = "가격 차이가 있지만 협상 여지가 있습니다."
        else:
            analysis = "가격 차이가 큽니다. 신중한 대응이 필요합니다."

        # 추천 옵션 생성
        recommended = self._create_counter_option(
            "추천안", original_price, customer_counter_price, cost_price, is_final_offer
        )

        alternatives = [
            self._create_counter_option(
                "보수적 접근", original_price * 0.97, customer_counter_price, cost_price, False
            ),
            self._create_counter_option(
                "공격적 접근", original_price * 0.92, customer_counter_price, cost_price, False
            )
        ]

        # 응답 스크립트
        response_script = self._generate_response_script(
            price_gap_pct, customer_type, reason_given, recommended
        )

        # 핵심 논점
        key_arguments = [
            "품질과 서비스의 가치를 고려해 주세요.",
            "장기적 파트너십을 위한 합리적인 가격입니다.",
            "원가 상승으로 추가 할인이 어렵습니다.",
            "이미 경쟁력 있는 가격을 제안드렸습니다."
        ]

        # 피해야 할 양보
        concessions_to_avoid = [
            "추가 무료 서비스 무분별한 제공",
            "품질 저하를 동반한 가격 인하",
            "마진 한계 이하로의 가격 인하",
            "선례가 될 수 있는 특별 할인"
        ]

        # 예상 결과
        if price_gap_pct <= 10:
            expected = "합의 가능성 높음"
            walk_away = False
        elif price_gap_pct <= 20:
            expected = "추가 협상 필요"
            walk_away = False
        else:
            expected = "합의 어려움 예상"
            walk_away = not is_acceptable

        return {
            "request_id": request_id,
            "analysis_summary": analysis,
            "price_gap": round(price_gap, 0),
            "price_gap_pct": round(price_gap_pct, 1),
            "is_acceptable": is_acceptable,
            "recommended_option": recommended,
            "alternative_options": alternatives,
            "response_script": response_script,
            "key_arguments": key_arguments,
            "concessions_to_avoid": concessions_to_avoid,
            "expected_outcome": expected,
            "walk_away_recommendation": walk_away,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _create_counter_option(
        self,
        name: str,
        target_price: float,
        customer_price: float,
        cost_price: float,
        is_final: bool
    ) -> dict:
        """역제안 옵션 생성"""
        # 중간점 계산
        if is_final:
            price = customer_price * 1.02
        else:
            price = (target_price + customer_price) / 2

        price = max(price, cost_price * 1.1)
        discount = ((target_price - price) / target_price) * 100
        margin = ((price - cost_price) / price) * 100

        # 수주 확률 추정
        gap_from_customer = (price - customer_price) / customer_price * 100
        if gap_from_customer <= 3:
            win_prob = 80
        elif gap_from_customer <= 7:
            win_prob = 60
        elif gap_from_customer <= 12:
            win_prob = 40
        else:
            win_prob = 25

        return {
            "option_name": name,
            "price": round(price, 0),
            "discount_rate": round(abs(discount), 1),
            "margin_rate": round(margin, 1),
            "win_probability": win_prob,
            "value_adds": ["빠른 납기", "연장 보증", "기술 지원"],
            "conditions": ["현금 결제", "대량 구매 시 적용"]
        }

    def _generate_response_script(
        self,
        price_gap_pct: float,
        customer_type: str,
        reason_given: Optional[str],
        recommended: dict
    ) -> str:
        """응답 스크립트 생성"""
        script = "감사합니다. 제안해 주신 가격을 검토했습니다. "

        if price_gap_pct <= 5:
            script += f"저희도 협력의 의지를 보여드리고자, {recommended['price']:,.0f}원에 공급하도록 하겠습니다."
        elif price_gap_pct <= 15:
            script += f"저희가 제시할 수 있는 최선의 가격은 {recommended['price']:,.0f}원입니다. "
            script += "이 가격에는 연장 보증과 기술 지원이 포함됩니다."
        else:
            script += "말씀하신 가격과는 차이가 있습니다. "
            script += f"품질과 서비스를 고려하면 {recommended['price']:,.0f}원이 합리적인 가격입니다."

        if customer_type == "VIP":
            script += " 오랜 거래를 감사드리며, 최선의 조건을 제안드립니다."

        return script

    # ========================================================================
    # Price History (가격 히스토리)
    # ========================================================================

    async def get_price_history(
        self,
        customer_id: Optional[str] = None,
        product_category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """가격 히스토리 조회"""
        request_id = str(uuid.uuid4())[:8]

        # 필터링
        filtered = self._records.copy()
        if customer_id:
            filtered = [r for r in filtered if r.customer_id == customer_id]
        if start_date:
            filtered = [r for r in filtered if r.created_at.date() >= start_date]
        if end_date:
            filtered = [r for r in filtered if r.created_at.date() <= end_date]

        # 히스토리 변환
        history = []
        for record in filtered[:20]:
            discount = ((record.initial_price - record.final_price) / record.initial_price) * 100
            history.append({
                "estimate_id": record.estimate_id,
                "record_date": record.created_at.date().isoformat(),
                "initial_price": round(record.initial_price, 0),
                "final_price": round(record.final_price, 0),
                "discount_rate": round(discount, 1),
                "outcome": record.outcome,
                "customer_type": record.customer_type,
                "negotiation_rounds": record.negotiation_rounds
            })

        # 통계
        if filtered:
            avg_initial = sum(r.initial_price for r in filtered) / len(filtered)
            avg_final = sum(r.final_price for r in filtered) / len(filtered)
            avg_discount = sum(
                (r.initial_price - r.final_price) / r.initial_price * 100
                for r in filtered
            ) / len(filtered)
        else:
            avg_initial = avg_final = avg_discount = 0

        # 트렌드 (월별)
        trends = [
            {
                "period": "최근 1개월",
                "average_price": round(avg_final * 1.02, 0),
                "average_discount": round(avg_discount * 0.95, 1),
                "price_change_pct": 2.0
            },
            {
                "period": "최근 3개월",
                "average_price": round(avg_final, 0),
                "average_discount": round(avg_discount, 1),
                "price_change_pct": 0.0
            }
        ]

        # 인사이트
        insights = [
            f"평균 할인율 {avg_discount:.1f}%입니다.",
            "VIP 고객의 할인율이 일반 고객보다 높습니다.",
            "최근 가격이 소폭 상승 추세입니다."
        ]

        return {
            "request_id": request_id,
            "history": history,
            "total_records": len(filtered),
            "average_initial_price": round(avg_initial, 0),
            "average_final_price": round(avg_final, 0),
            "average_discount_rate": round(avg_discount, 1),
            "trends": trends,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }

    # ========================================================================
    # Quick Tips (빠른 팁)
    # ========================================================================

    async def get_quick_tip(
        self,
        situation: str,
        customer_statement: Optional[str] = None,
        current_discount: float = 0
    ) -> dict:
        """빠른 협상 팁 제공"""
        request_id = str(uuid.uuid4())[:8]

        # 상황 분류
        situation_lower = situation.lower()
        if "가격" in situation_lower or "비싸" in situation_lower:
            situation_type = "가격 이의"
            immediate = "가격보다 총 가치(TCO)를 강조하세요."
            key_phrase = "가격 이상의 가치를 제공합니다."
            do_list = [
                "가치 제안 강조",
                "경쟁사 대비 장점 설명",
                "패키지 옵션 제안"
            ]
            dont_list = [
                "즉시 할인 제안",
                "가격만 논의",
                "방어적 태도"
            ]
            max_discount = 10.0 - current_discount
        elif "경쟁사" in situation_lower:
            situation_type = "경쟁사 비교"
            immediate = "직접 비교보다 우리만의 강점을 설명하세요."
            key_phrase = "저희만의 차별화된 가치가 있습니다."
            do_list = [
                "차별화 포인트 강조",
                "서비스 품질 설명",
                "사례 소개"
            ]
            dont_list = [
                "경쟁사 비방",
                "가격 경쟁 진입",
                "초조한 반응"
            ]
            max_discount = 8.0 - current_discount
        elif "기다" in situation_lower or "시간" in situation_lower:
            situation_type = "결정 지연"
            immediate = "결정 시급성을 부드럽게 전달하세요."
            key_phrase = "빠른 결정 시 추가 혜택을 드릴 수 있습니다."
            do_list = [
                "한정 혜택 언급",
                "결정 필요성 설명",
                "다음 단계 제안"
            ]
            dont_list = [
                "압박감 조성",
                "최후통첩",
                "조급한 태도"
            ]
            max_discount = 5.0 - current_discount
        else:
            situation_type = "일반 협상"
            immediate = "고객 니즈를 먼저 파악하세요."
            key_phrase = "최적의 솔루션을 제안드리겠습니다."
            do_list = [
                "경청하기",
                "질문하기",
                "니즈 파악"
            ]
            dont_list = [
                "성급한 제안",
                "일방적 설명",
                "가격부터 언급"
            ]
            max_discount = 7.0 - current_discount

        max_discount = max(0, max_discount)

        alternative_concessions = [
            "납기 단축",
            "연장 보증",
            "무상 기술 지원",
            "결제 조건 유연화",
            "무료 설치"
        ]

        return {
            "request_id": request_id,
            "situation_type": situation_type,
            "immediate_response": immediate,
            "key_phrase": key_phrase,
            "do_list": do_list,
            "dont_list": dont_list,
            "max_additional_discount": round(max_discount, 1),
            "alternative_concessions": alternative_concessions,
            "generated_at": datetime.utcnow().isoformat()
        }

    # ========================================================================
    # Dashboard (대시보드)
    # ========================================================================

    async def get_dashboard(self) -> dict:
        """협상 대시보드 조회"""
        # 30일 데이터
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent = [r for r in self._records if r.created_at >= cutoff]

        active = len([r for r in recent if r.outcome == "PENDING"])
        won = len([r for r in recent if r.outcome == "WON"])
        total_decided = len([r for r in recent if r.outcome in ["WON", "LOST"]])
        win_rate = (won / total_decided * 100) if total_decided > 0 else 0

        # 평균 할인율
        won_records = [r for r in recent if r.outcome == "WON"]
        if won_records:
            avg_discount = sum(
                (r.initial_price - r.final_price) / r.initial_price * 100
                for r in won_records
            ) / len(won_records)
        else:
            avg_discount = 0

        # 파이프라인 가치
        pending = [r for r in recent if r.outcome == "PENDING"]
        pipeline_value = sum(r.initial_price for r in pending)

        # 추세 판단
        prev_cutoff = datetime.utcnow() - timedelta(days=60)
        prev_recent = [
            r for r in self._records
            if prev_cutoff <= r.created_at < cutoff
        ]
        prev_won = len([r for r in prev_recent if r.outcome == "WON"])
        prev_total = len([r for r in prev_recent if r.outcome in ["WON", "LOST"]])
        prev_win_rate = (prev_won / prev_total * 100) if prev_total > 0 else 0

        if win_rate > prev_win_rate + 5:
            win_trend = "UP"
        elif win_rate < prev_win_rate - 5:
            win_trend = "DOWN"
        else:
            win_trend = "STABLE"

        # 마진 추세
        margin_trend = "STABLE"

        # 긴급 건
        urgent = [r.estimate_id for r in pending[:3]]

        # 위험 건
        at_risk = [
            r.estimate_id for r in pending
            if r.negotiation_rounds > 3
        ][:3]

        # 일일 팁
        tips = [
            "오늘의 협상에서 가치 제안을 먼저 하세요.",
            "고객의 진정한 니즈를 파악하는 것이 핵심입니다.",
            "첫 제안에서 최종가를 내놓지 마세요.",
            "침묵은 때로 가장 강력한 협상 도구입니다."
        ]

        return {
            "active_negotiations": active,
            "avg_win_rate_30d": round(win_rate, 1),
            "avg_discount_rate": round(avg_discount, 1),
            "total_pipeline_value": round(pipeline_value, 0),
            "win_rate_trend": win_trend,
            "margin_trend": margin_trend,
            "urgent_negotiations": urgent,
            "at_risk_deals": at_risk,
            "daily_tip": random.choice(tips),
            "monthly_performance": {
                "deals_won": won,
                "deals_lost": total_decided - won,
                "total_value": round(sum(r.final_price for r in won_records), 0)
            },
            "generated_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Service Singleton
# ============================================================================

_negotiation_service: Optional[NegotiationService] = None


def get_negotiation_service() -> NegotiationService:
    """Negotiation Service 싱글톤 반환"""
    global _negotiation_service
    if _negotiation_service is None:
        _negotiation_service = NegotiationService()
        logger.info("NegotiationService initialized")
    return _negotiation_service
