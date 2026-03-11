"""
ERP AI Service - AI 기반 ERP 문서 생성 및 분석 서비스

Claude API를 활용한 ERP 업무 자동화:
- 매출/매입 명세서 자동 생성
- 세금계산서 발행 지원
- 기간별/업체별/상품별 분석
- 비교 그래프 데이터 생성
- 정보 요약 및 대화형 업무 지원

Contract-First + Zero-Mock
NO MOCKS - Real AI processing only
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Anthropic 임포트
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available")


class DocumentType(str, Enum):
    """ERP 문서 유형"""
    SALES_STATEMENT = "sales_statement"          # 매출명세서
    PURCHASE_STATEMENT = "purchase_statement"    # 매입명세서
    TAX_INVOICE = "tax_invoice"                  # 세금계산서
    TRANSACTION_STATEMENT = "transaction"        # 거래명세서
    ESTIMATE = "estimate"                        # 견적서


class AnalysisType(str, Enum):
    """분석 유형"""
    PERIOD = "period"           # 기간별
    COMPANY = "company"         # 업체별
    PRODUCT = "product"         # 상품별
    COMPARISON = "comparison"   # 비교 분석
    TREND = "trend"             # 추세 분석
    SUMMARY = "summary"         # 요약


@dataclass
class ERPTransaction:
    """ERP 거래 데이터"""
    id: str
    date: str
    company_name: str
    company_id: str
    product_name: str
    product_code: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    tax_amount: Decimal
    transaction_type: str  # sales, purchase
    metadata: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """분석 결과"""
    analysis_type: AnalysisType
    title: str
    summary: str
    data: dict
    chart_data: Optional[dict] = None
    insights: list[str] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class DocumentResult:
    """문서 생성 결과"""
    document_type: DocumentType
    title: str
    content: dict
    html_content: Optional[str] = None
    generated_at: str = ""


class ERPAIService:
    """
    AI 기반 ERP 서비스

    특징:
    - Claude API로 문서 자동 생성
    - 자연어 쿼리로 데이터 분석
    - 대화형 업무 지원
    - 그래프 데이터 자동 생성
    """

    _instance: Optional['ERPAIService'] = None
    _anthropic_client: Any = None

    # Claude 모델 설정
    CLAUDE_MODEL = "claude-sonnet-4-20250514"

    def __new__(cls) -> 'ERPAIService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """서비스 초기화"""
        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                    logger.info("ERPAIService initialized with Claude API")
                except Exception as e:
                    logger.error(f"Claude 초기화 실패: {e}")
            else:
                logger.warning("ANTHROPIC_API_KEY 환경변수 없음")

    def _call_claude(self, system_prompt: str, user_message: str) -> str:
        """Claude API 호출"""
        if not self._anthropic_client:
            raise RuntimeError("Claude API 초기화되지 않음")

        try:
            response = self._anthropic_client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )
            return response.content[0].text if response.content else ""
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise

    def generate_sales_statement(
        self,
        transactions: list[ERPTransaction],
        company_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> DocumentResult:
        """
        매출명세서 생성

        Args:
            transactions: 거래 데이터 목록
            company_filter: 업체 필터
            date_from: 시작일
            date_to: 종료일

        Returns:
            생성된 문서
        """
        # 필터링
        filtered = [t for t in transactions if t.transaction_type == "sales"]
        if company_filter:
            filtered = [t for t in filtered if company_filter in t.company_name]
        if date_from:
            filtered = [t for t in filtered if t.date >= date_from]
        if date_to:
            filtered = [t for t in filtered if t.date <= date_to]

        # 합계 계산
        total_amount = sum(t.total_amount for t in filtered)
        total_tax = sum(t.tax_amount for t in filtered)
        total_with_tax = total_amount + total_tax

        # 업체별 그룹화
        by_company: dict[str, list[ERPTransaction]] = {}
        for t in filtered:
            if t.company_name not in by_company:
                by_company[t.company_name] = []
            by_company[t.company_name].append(t)

        content = {
            "title": "매출명세서",
            "period": {
                "from": date_from or "전체",
                "to": date_to or "전체",
            },
            "summary": {
                "total_transactions": len(filtered),
                "total_amount": float(total_amount),
                "total_tax": float(total_tax),
                "total_with_tax": float(total_with_tax),
                "companies_count": len(by_company),
            },
            "by_company": {
                name: {
                    "transactions": len(items),
                    "total": float(sum(t.total_amount for t in items)),
                }
                for name, items in by_company.items()
            },
            "transactions": [
                {
                    "date": t.date,
                    "company": t.company_name,
                    "product": t.product_name,
                    "quantity": t.quantity,
                    "unit_price": float(t.unit_price),
                    "amount": float(t.total_amount),
                    "tax": float(t.tax_amount),
                }
                for t in filtered
            ],
        }

        return DocumentResult(
            document_type=DocumentType.SALES_STATEMENT,
            title=f"매출명세서 ({date_from or '전체'} ~ {date_to or '전체'})",
            content=content,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def generate_purchase_statement(
        self,
        transactions: list[ERPTransaction],
        company_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> DocumentResult:
        """
        매입명세서 생성

        Args:
            transactions: 거래 데이터 목록
            company_filter: 업체 필터
            date_from: 시작일
            date_to: 종료일

        Returns:
            생성된 문서
        """
        # 필터링
        filtered = [t for t in transactions if t.transaction_type == "purchase"]
        if company_filter:
            filtered = [t for t in filtered if company_filter in t.company_name]
        if date_from:
            filtered = [t for t in filtered if t.date >= date_from]
        if date_to:
            filtered = [t for t in filtered if t.date <= date_to]

        # 합계 계산
        total_amount = sum(t.total_amount for t in filtered)
        total_tax = sum(t.tax_amount for t in filtered)
        total_with_tax = total_amount + total_tax

        content = {
            "title": "매입명세서",
            "period": {
                "from": date_from or "전체",
                "to": date_to or "전체",
            },
            "summary": {
                "total_transactions": len(filtered),
                "total_amount": float(total_amount),
                "total_tax": float(total_tax),
                "total_with_tax": float(total_with_tax),
            },
            "transactions": [
                {
                    "date": t.date,
                    "company": t.company_name,
                    "product": t.product_name,
                    "quantity": t.quantity,
                    "unit_price": float(t.unit_price),
                    "amount": float(t.total_amount),
                    "tax": float(t.tax_amount),
                }
                for t in filtered
            ],
        }

        return DocumentResult(
            document_type=DocumentType.PURCHASE_STATEMENT,
            title=f"매입명세서 ({date_from or '전체'} ~ {date_to or '전체'})",
            content=content,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def analyze_by_period(
        self,
        transactions: list[ERPTransaction],
        period_type: str = "month",  # day, week, month, quarter, year
        transaction_type: str = "sales",
    ) -> AnalysisResult:
        """
        기간별 분석

        Args:
            transactions: 거래 데이터
            period_type: 기간 유형
            transaction_type: 거래 유형

        Returns:
            분석 결과 (차트 데이터 포함)
        """
        filtered = [t for t in transactions if t.transaction_type == transaction_type]

        # 기간별 그룹화
        by_period: dict[str, Decimal] = {}

        for t in filtered:
            # 날짜 파싱 (YYYY-MM-DD 형식 가정)
            date_parts = t.date.split("-")
            if period_type == "day":
                key = t.date
            elif period_type == "week":
                # 간단히 주차 계산
                key = f"{date_parts[0]}-W{int(date_parts[2])//7 + 1:02d}"
            elif period_type == "month":
                key = f"{date_parts[0]}-{date_parts[1]}"
            elif period_type == "quarter":
                quarter = (int(date_parts[1]) - 1) // 3 + 1
                key = f"{date_parts[0]}-Q{quarter}"
            else:  # year
                key = date_parts[0]

            if key not in by_period:
                by_period[key] = Decimal(0)
            by_period[key] += t.total_amount

        # 정렬
        sorted_data = sorted(by_period.items())

        # 차트 데이터 생성
        chart_data = {
            "type": "line",
            "labels": [item[0] for item in sorted_data],
            "datasets": [
                {
                    "label": "매출" if transaction_type == "sales" else "매입",
                    "data": [float(item[1]) for item in sorted_data],
                }
            ],
        }

        # AI 인사이트 생성
        insights = self._generate_insights(
            f"기간별 {transaction_type} 분석",
            sorted_data,
        )

        total = sum(by_period.values())
        avg = total / len(by_period) if by_period else Decimal(0)

        return AnalysisResult(
            analysis_type=AnalysisType.PERIOD,
            title=f"기간별 {'매출' if transaction_type == 'sales' else '매입'} 분석",
            summary=f"총 {len(by_period)}개 기간, 총액 {total:,.0f}원, 평균 {avg:,.0f}원",
            data={
                "by_period": {k: float(v) for k, v in by_period.items()},
                "total": float(total),
                "average": float(avg),
            },
            chart_data=chart_data,
            insights=insights,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def analyze_by_company(
        self,
        transactions: list[ERPTransaction],
        transaction_type: str = "sales",
        top_n: int = 10,
    ) -> AnalysisResult:
        """
        업체별 분석

        Args:
            transactions: 거래 데이터
            transaction_type: 거래 유형
            top_n: 상위 N개 업체

        Returns:
            분석 결과
        """
        filtered = [t for t in transactions if t.transaction_type == transaction_type]

        # 업체별 그룹화
        by_company: dict[str, dict] = {}

        for t in filtered:
            if t.company_name not in by_company:
                by_company[t.company_name] = {
                    "total_amount": Decimal(0),
                    "transaction_count": 0,
                    "products": set(),
                }
            by_company[t.company_name]["total_amount"] += t.total_amount
            by_company[t.company_name]["transaction_count"] += 1
            by_company[t.company_name]["products"].add(t.product_name)

        # 정렬 (금액 기준)
        sorted_companies = sorted(
            by_company.items(),
            key=lambda x: x[1]["total_amount"],
            reverse=True,
        )[:top_n]

        # 차트 데이터 생성
        chart_data = {
            "type": "bar",
            "labels": [item[0] for item in sorted_companies],
            "datasets": [
                {
                    "label": "거래금액",
                    "data": [float(item[1]["total_amount"]) for item in sorted_companies],
                }
            ],
        }

        total = sum(d["total_amount"] for d in by_company.values())

        return AnalysisResult(
            analysis_type=AnalysisType.COMPANY,
            title=f"업체별 {'매출' if transaction_type == 'sales' else '매입'} 분석",
            summary=f"총 {len(by_company)}개 업체, 상위 {len(sorted_companies)}개 표시",
            data={
                "by_company": {
                    name: {
                        "total_amount": float(data["total_amount"]),
                        "transaction_count": data["transaction_count"],
                        "product_count": len(data["products"]),
                        "percentage": float(data["total_amount"] / total * 100) if total else 0,
                    }
                    for name, data in sorted_companies
                },
                "total": float(total),
                "company_count": len(by_company),
            },
            chart_data=chart_data,
            insights=[
                f"상위 1위 업체: {sorted_companies[0][0]} ({float(sorted_companies[0][1]['total_amount']):,.0f}원)" if sorted_companies else "데이터 없음",
            ],
            generated_at=datetime.now(UTC).isoformat(),
        )

    def analyze_by_product(
        self,
        transactions: list[ERPTransaction],
        transaction_type: str = "sales",
        top_n: int = 10,
    ) -> AnalysisResult:
        """
        상품별 분석

        Args:
            transactions: 거래 데이터
            transaction_type: 거래 유형
            top_n: 상위 N개 상품

        Returns:
            분석 결과
        """
        filtered = [t for t in transactions if t.transaction_type == transaction_type]

        # 상품별 그룹화
        by_product: dict[str, dict] = {}

        for t in filtered:
            if t.product_name not in by_product:
                by_product[t.product_name] = {
                    "total_amount": Decimal(0),
                    "total_quantity": 0,
                    "transaction_count": 0,
                }
            by_product[t.product_name]["total_amount"] += t.total_amount
            by_product[t.product_name]["total_quantity"] += t.quantity
            by_product[t.product_name]["transaction_count"] += 1

        # 정렬
        sorted_products = sorted(
            by_product.items(),
            key=lambda x: x[1]["total_amount"],
            reverse=True,
        )[:top_n]

        # 파이 차트 데이터
        chart_data = {
            "type": "pie",
            "labels": [item[0] for item in sorted_products],
            "datasets": [
                {
                    "data": [float(item[1]["total_amount"]) for item in sorted_products],
                }
            ],
        }

        total = sum(d["total_amount"] for d in by_product.values())

        return AnalysisResult(
            analysis_type=AnalysisType.PRODUCT,
            title=f"상품별 {'매출' if transaction_type == 'sales' else '매입'} 분석",
            summary=f"총 {len(by_product)}개 상품, 상위 {len(sorted_products)}개 표시",
            data={
                "by_product": {
                    name: {
                        "total_amount": float(data["total_amount"]),
                        "total_quantity": data["total_quantity"],
                        "transaction_count": data["transaction_count"],
                        "percentage": float(data["total_amount"] / total * 100) if total else 0,
                    }
                    for name, data in sorted_products
                },
                "total": float(total),
                "product_count": len(by_product),
            },
            chart_data=chart_data,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def generate_comparison_chart(
        self,
        transactions: list[ERPTransaction],
        compare_type: str = "sales_vs_purchase",
        period_type: str = "month",
    ) -> AnalysisResult:
        """
        비교 그래프 생성

        Args:
            transactions: 거래 데이터
            compare_type: 비교 유형
            period_type: 기간 유형

        Returns:
            비교 분석 결과
        """
        # 매출/매입 분리
        sales = [t for t in transactions if t.transaction_type == "sales"]
        purchases = [t for t in transactions if t.transaction_type == "purchase"]

        # 기간별 그룹화
        sales_by_period: dict[str, Decimal] = {}
        purchase_by_period: dict[str, Decimal] = {}

        for t in sales:
            key = t.date[:7] if period_type == "month" else t.date[:4]
            if key not in sales_by_period:
                sales_by_period[key] = Decimal(0)
            sales_by_period[key] += t.total_amount

        for t in purchases:
            key = t.date[:7] if period_type == "month" else t.date[:4]
            if key not in purchase_by_period:
                purchase_by_period[key] = Decimal(0)
            purchase_by_period[key] += t.total_amount

        # 모든 기간 키 수집
        all_periods = sorted(set(sales_by_period.keys()) | set(purchase_by_period.keys()))

        # 차트 데이터
        chart_data = {
            "type": "bar",
            "labels": all_periods,
            "datasets": [
                {
                    "label": "매출",
                    "data": [float(sales_by_period.get(p, 0)) for p in all_periods],
                    "backgroundColor": "rgba(54, 162, 235, 0.7)",
                },
                {
                    "label": "매입",
                    "data": [float(purchase_by_period.get(p, 0)) for p in all_periods],
                    "backgroundColor": "rgba(255, 99, 132, 0.7)",
                },
            ],
        }

        total_sales = sum(sales_by_period.values())
        total_purchase = sum(purchase_by_period.values())
        profit = total_sales - total_purchase

        return AnalysisResult(
            analysis_type=AnalysisType.COMPARISON,
            title="매출/매입 비교 분석",
            summary=f"총매출 {total_sales:,.0f}원, 총매입 {total_purchase:,.0f}원, 차익 {profit:,.0f}원",
            data={
                "total_sales": float(total_sales),
                "total_purchase": float(total_purchase),
                "profit": float(profit),
                "profit_margin": float(profit / total_sales * 100) if total_sales else 0,
                "by_period": {
                    p: {
                        "sales": float(sales_by_period.get(p, 0)),
                        "purchase": float(purchase_by_period.get(p, 0)),
                        "profit": float(sales_by_period.get(p, 0) - purchase_by_period.get(p, 0)),
                    }
                    for p in all_periods
                },
            },
            chart_data=chart_data,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def summarize_data(
        self,
        transactions: list[ERPTransaction],
        query: Optional[str] = None,
    ) -> dict:
        """
        데이터 요약 (AI 활용)

        Args:
            transactions: 거래 데이터
            query: 사용자 질문 (없으면 일반 요약)

        Returns:
            요약 정보
        """
        # 기본 통계
        sales = [t for t in transactions if t.transaction_type == "sales"]
        purchases = [t for t in transactions if t.transaction_type == "purchase"]

        total_sales = sum(t.total_amount for t in sales)
        total_purchase = sum(t.total_amount for t in purchases)

        summary_data = {
            "overview": {
                "total_transactions": len(transactions),
                "sales_count": len(sales),
                "purchase_count": len(purchases),
                "total_sales": float(total_sales),
                "total_purchase": float(total_purchase),
                "profit": float(total_sales - total_purchase),
            },
            "top_customers": self._get_top_items(sales, "company_name", 5),
            "top_products": self._get_top_items(transactions, "product_name", 5),
        }

        # AI 요약 생성 (Claude 사용 가능 시)
        if self._anthropic_client and query:
            try:
                system_prompt = """당신은 ERP 데이터 분석 전문가입니다.
                사용자의 질문에 대해 제공된 데이터를 기반으로 명확하고 간결하게 답변해주세요.
                숫자는 천 단위 구분자를 사용하고, 금액은 원화로 표시해주세요."""

                user_message = f"""다음 데이터를 기반으로 답변해주세요:

{json.dumps(summary_data, ensure_ascii=False, indent=2)}

질문: {query}"""

                ai_response = self._call_claude(system_prompt, user_message)
                summary_data["ai_response"] = ai_response
            except Exception as e:
                logger.error(f"AI 요약 생성 실패: {e}")
                summary_data["ai_response"] = f"AI 요약 생성 실패: {e}"

        return summary_data

    def _get_top_items(
        self,
        transactions: list[ERPTransaction],
        group_by: str,
        top_n: int,
    ) -> list[dict]:
        """상위 항목 추출"""
        by_item: dict[str, Decimal] = {}

        for t in transactions:
            key = getattr(t, group_by, "unknown")
            if key not in by_item:
                by_item[key] = Decimal(0)
            by_item[key] += t.total_amount

        sorted_items = sorted(by_item.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [
            {"name": name, "amount": float(amount)}
            for name, amount in sorted_items
        ]

    def _generate_insights(self, title: str, data: list) -> list[str]:
        """AI 인사이트 생성"""
        if not data:
            return ["데이터가 부족하여 인사이트를 생성할 수 없습니다."]

        # 기본 인사이트 (AI 없이)
        insights = []

        if len(data) >= 2:
            # 최고/최저 비교
            max_item = max(data, key=lambda x: x[1])
            min_item = min(data, key=lambda x: x[1])
            insights.append(f"최고: {max_item[0]} ({float(max_item[1]):,.0f}원)")
            insights.append(f"최저: {min_item[0]} ({float(min_item[1]):,.0f}원)")

            # 추세 (마지막 3개 비교)
            if len(data) >= 3:
                recent = data[-3:]
                if recent[-1][1] > recent[0][1]:
                    insights.append("최근 상승 추세")
                elif recent[-1][1] < recent[0][1]:
                    insights.append("최근 하락 추세")
                else:
                    insights.append("최근 안정적")

        return insights

    def chat_query(self, query: str, context: dict) -> str:
        """
        대화형 ERP 쿼리

        Args:
            query: 사용자 질문
            context: 컨텍스트 데이터

        Returns:
            AI 응답
        """
        if not self._anthropic_client:
            return "AI 서비스가 초기화되지 않았습니다."

        system_prompt = """당신은 한국산업(KIS) ERP 시스템의 AI 어시스턴트입니다.

역할:
- 매출/매입 데이터 분석
- 거래처 및 상품 정보 제공
- 재무 현황 요약
- 업무 관련 질문 답변

응답 스타일:
- 간결하고 명확하게
- 숫자는 천 단위 구분자 사용
- 금액은 원화로 표시
- 필요 시 표나 목록 형식 사용"""

        user_message = f"""현재 ERP 데이터 컨텍스트:
{json.dumps(context, ensure_ascii=False, indent=2)}

사용자 질문: {query}"""

        try:
            return self._call_claude(system_prompt, user_message)
        except Exception as e:
            logger.error(f"Chat 쿼리 실패: {e}")
            return f"쿼리 처리 중 오류 발생: {e}"

    def get_status(self) -> dict:
        """서비스 상태 확인"""
        return {
            "claude_available": self._anthropic_client is not None,
            "model": self.CLAUDE_MODEL,
            "features": [
                "매출/매입 명세서 생성",
                "기간별 분석",
                "업체별 분석",
                "상품별 분석",
                "비교 그래프",
                "AI 요약",
                "대화형 쿼리",
            ],
        }


# 싱글톤 인스턴스 접근
_service: Optional[ERPAIService] = None


def get_erp_ai_service() -> ERPAIService:
    """ERPAIService 싱글톤"""
    global _service
    if _service is None:
        _service = ERPAIService()
    return _service
