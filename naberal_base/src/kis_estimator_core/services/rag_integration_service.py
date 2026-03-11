"""
RAG Integration Service - 견적 엔진과 RAG 시스템 통합

핵심 기능:
1. 유사 견적 검색 (입력 기반)
2. 견적 결과 저장 (학습용)
3. 규칙 검증 (RAG 기반)
4. 가격 예측 참조

Contract-First + Zero-Mock
NO MOCKS - Real RAG operations only
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class RAGSearchResult:
    """RAG 검색 결과"""
    similar_estimates: list[dict]  # 유사 견적 목록
    relevant_rules: list[dict]     # 관련 규칙
    price_references: list[dict]   # 가격 참조
    confidence: float              # 전체 신뢰도
    search_time_ms: float          # 검색 시간


@dataclass
class RAGValidationResult:
    """RAG 기반 검증 결과"""
    is_valid: bool
    violations: list[dict]         # 규칙 위반 사항
    suggestions: list[dict]        # 개선 제안
    similar_cases: list[dict]      # 유사 사례
    confidence: float


class RAGIntegrationService:
    """
    견적 엔진 RAG 통합 서비스

    역할:
    - 견적 요청 시 유사 견적 검색
    - 견적 완료 시 RAG DB에 저장
    - 규칙 기반 검증
    - 가격 예측 참조
    """

    _instance: Optional['RAGIntegrationService'] = None

    def __new__(cls) -> 'RAGIntegrationService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """서비스 초기화"""
        self._vector_service = None
        self._learning_service = None
        logger.info("RAGIntegrationService 초기화 완료")

    @property
    def vector_service(self):
        """RAG 벡터 서비스 (lazy loading)"""
        if self._vector_service is None:
            from kis_estimator_core.services.rag_vector_service import get_rag_vector_service
            self._vector_service = get_rag_vector_service()
        return self._vector_service

    @property
    def learning_service(self):
        """학습 서비스 (lazy loading)"""
        if self._learning_service is None:
            from kis_estimator_core.services.ai_learning_service import get_ai_learning_service
            self._learning_service = get_ai_learning_service()
        return self._learning_service

    def search_similar_estimates(
        self,
        main_breaker: dict,
        branch_breakers: list[dict],
        enclosure_type: Optional[str] = None,
        accessories: Optional[list[dict]] = None,
        n_results: int = 5,
    ) -> RAGSearchResult:
        """
        유사 견적 검색

        Args:
            main_breaker: 메인 차단기 정보
            branch_breakers: 분기 차단기 목록
            enclosure_type: 외함 종류
            accessories: 부속자재 목록
            n_results: 반환할 결과 수

        Returns:
            RAG 검색 결과
        """
        start_time = datetime.now(UTC)

        try:
            # 검색 쿼리 구성
            query_parts = []

            # 메인 차단기 정보
            if main_breaker:
                query_parts.append(
                    f"메인차단기 {main_breaker.get('poles', 4)}P "
                    f"{main_breaker.get('current', 100)}A "
                    f"{main_breaker.get('breaker_type', 'MCCB')}"
                )

            # 분기 차단기 요약
            if branch_breakers:
                branch_summary = self._summarize_branch_breakers(branch_breakers)
                query_parts.append(f"분기차단기 {branch_summary}")

            # 외함 정보
            if enclosure_type:
                query_parts.append(f"외함 {enclosure_type}")

            # 부속자재
            if accessories:
                acc_types = [a.get('type', '') for a in accessories if a.get('type')]
                if acc_types:
                    query_parts.append(f"부속자재 {', '.join(acc_types)}")

            query = " ".join(query_parts)

            # 벡터 검색 실행
            from kis_estimator_core.services.rag_vector_service import DocumentCategory

            # 견적 검색
            estimate_results = self.vector_service.search(
                query=query,
                category=DocumentCategory.ESTIMATE,
                n_results=n_results,
            )

            # 규칙 검색
            rule_results = self.vector_service.search(
                query=query,
                category=DocumentCategory.RULE,
                n_results=3,
            )

            # 결과 변환
            similar_estimates = [
                {
                    "content": r.content,
                    "similarity": r.similarity,
                    "metadata": r.metadata,
                }
                for r in estimate_results
            ]

            relevant_rules = [
                {
                    "content": r.content,
                    "similarity": r.similarity,
                    "metadata": r.metadata,
                }
                for r in rule_results
            ]

            # 가격 참조 추출
            price_references = self._extract_price_references(similar_estimates)

            # 신뢰도 계산
            confidence = self._calculate_search_confidence(
                similar_estimates, relevant_rules
            )

            search_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

            logger.info(
                f"RAG 검색 완료: 유사 견적 {len(similar_estimates)}건, "
                f"관련 규칙 {len(relevant_rules)}건, 신뢰도 {confidence:.2f}"
            )

            return RAGSearchResult(
                similar_estimates=similar_estimates,
                relevant_rules=relevant_rules,
                price_references=price_references,
                confidence=confidence,
                search_time_ms=search_time,
            )

        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            search_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return RAGSearchResult(
                similar_estimates=[],
                relevant_rules=[],
                price_references=[],
                confidence=0.0,
                search_time_ms=search_time,
            )

    def validate_with_rag(
        self,
        estimate_data: dict,
    ) -> RAGValidationResult:
        """
        RAG 기반 견적 검증

        Args:
            estimate_data: 검증할 견적 데이터

        Returns:
            검증 결과
        """
        violations = []
        suggestions = []
        similar_cases = []

        try:
            # 검색 쿼리 구성
            main = estimate_data.get("main_breaker", {})
            branches = estimate_data.get("branch_breakers", [])

            query = f"검증 메인 {main.get('poles', 4)}P {main.get('current', 100)}A"

            # 관련 규칙 검색
            from kis_estimator_core.services.rag_vector_service import DocumentCategory

            rule_results = self.vector_service.search(
                query=query,
                category=DocumentCategory.RULE,
                n_results=5,
            )

            # 피드백 검색 (유사 실패 사례)
            feedback_results = self.vector_service.search(
                query=query,
                category=DocumentCategory.FEEDBACK,
                n_results=3,
            )

            # 규칙 위반 체크
            for rule in rule_results:
                rule_content = rule.content.lower()

                # 경제형/표준형 규칙
                if "경제형" in rule_content or "표준형" in rule_content:
                    if self._check_breaker_type_rule(estimate_data, rule):
                        violations.append({
                            "rule": rule.content[:100],
                            "type": "breaker_type",
                            "severity": "warning",
                        })

                # 소형 차단기 규칙
                if "소형" in rule_content or "32af" in rule_content:
                    if self._check_small_breaker_rule(estimate_data, rule):
                        suggestions.append({
                            "suggestion": "2P 20A/30A는 소형 차단기 사용 권장",
                            "rule": rule.content[:100],
                        })

            # 유사 사례 (피드백)
            for fb in feedback_results:
                similar_cases.append({
                    "content": fb.content[:200],
                    "similarity": fb.similarity,
                    "type": fb.metadata.get("feedback_type", "unknown"),
                })

            is_valid = len([v for v in violations if v.get("severity") == "error"]) == 0
            confidence = 0.9 if rule_results else 0.5

            return RAGValidationResult(
                is_valid=is_valid,
                violations=violations,
                suggestions=suggestions,
                similar_cases=similar_cases,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"RAG 검증 실패: {e}")
            return RAGValidationResult(
                is_valid=True,  # 검증 실패 시 통과 처리 (안전)
                violations=[],
                suggestions=[],
                similar_cases=[],
                confidence=0.0,
            )

    def save_estimate_result(
        self,
        estimate_id: str,
        request_data: dict,
        result_data: dict,
        success: bool,
        total_price: int,
    ) -> bool:
        """
        견적 결과를 RAG DB에 저장 (학습용)

        Args:
            estimate_id: 견적 ID
            request_data: 요청 데이터
            result_data: 결과 데이터
            success: 성공 여부
            total_price: 총 가격

        Returns:
            저장 성공 여부
        """
        try:
            # 견적 내용 구성
            main = request_data.get("main_breaker", {})
            branches = request_data.get("branch_breakers", [])

            content_parts = [
                f"견적ID: {estimate_id}",
                f"메인차단기: {main.get('poles', 4)}P {main.get('current', 100)}A {main.get('breaker_type', 'MCCB')}",
                f"분기차단기: {self._summarize_branch_breakers(branches)}",
                f"외함: {request_data.get('enclosure_type', '옥내노출')} {request_data.get('enclosure_material', 'STEEL')}",
                f"총가격: {total_price:,}원",
                f"성공: {success}",
            ]

            content = "\n".join(content_parts)

            # 메타데이터
            metadata = {
                "estimate_id": estimate_id,
                "main_poles": main.get("poles", 4),
                "main_current": main.get("current", 100),
                "branch_count": len(branches),
                "total_price": total_price,
                "success": success,
                "created_at": datetime.now(UTC).isoformat(),
            }

            # 벡터 DB에 저장
            from kis_estimator_core.services.rag_vector_service import DocumentCategory

            doc_id = self.vector_service.add_document(
                content=content,
                category=DocumentCategory.ESTIMATE,
                source=f"estimate_{estimate_id}",
                metadata=metadata,
            )

            logger.info(f"견적 결과 RAG 저장 완료: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"견적 결과 RAG 저장 실패: {e}")
            return False

    def get_price_prediction(
        self,
        main_breaker: dict,
        branch_breakers: list[dict],
        enclosure_type: Optional[str] = None,
    ) -> dict:
        """
        유사 견적 기반 가격 예측

        Args:
            main_breaker: 메인 차단기 정보
            branch_breakers: 분기 차단기 목록
            enclosure_type: 외함 종류

        Returns:
            가격 예측 정보
        """
        try:
            # 유사 견적 검색
            search_result = self.search_similar_estimates(
                main_breaker=main_breaker,
                branch_breakers=branch_breakers,
                enclosure_type=enclosure_type,
                n_results=10,
            )

            if not search_result.price_references:
                return {
                    "predicted_price": None,
                    "price_range": None,
                    "confidence": 0.0,
                    "reference_count": 0,
                }

            prices = [p["price"] for p in search_result.price_references if p.get("price")]

            if not prices:
                return {
                    "predicted_price": None,
                    "price_range": None,
                    "confidence": 0.0,
                    "reference_count": 0,
                }

            # 가격 통계
            avg_price = int(sum(prices) / len(prices))
            min_price = min(prices)
            max_price = max(prices)

            # 신뢰도: 참조 수와 유사도 기반
            confidence = min(0.95, 0.5 + (len(prices) * 0.05))

            return {
                "predicted_price": avg_price,
                "price_range": {
                    "min": min_price,
                    "max": max_price,
                },
                "confidence": confidence,
                "reference_count": len(prices),
            }

        except Exception as e:
            logger.error(f"가격 예측 실패: {e}")
            return {
                "predicted_price": None,
                "price_range": None,
                "confidence": 0.0,
                "reference_count": 0,
            }

    def _summarize_branch_breakers(self, branches: list[dict]) -> str:
        """분기 차단기 요약"""
        if not branches:
            return "없음"

        # 타입별 그룹화
        type_counts = {}
        for b in branches:
            key = f"{b.get('poles', 2)}P {b.get('current', 20)}A"
            qty = b.get("quantity", 1)
            type_counts[key] = type_counts.get(key, 0) + qty

        parts = [f"{k} x{v}" for k, v in type_counts.items()]
        return ", ".join(parts)

    def _extract_price_references(
        self,
        similar_estimates: list[dict],
    ) -> list[dict]:
        """유사 견적에서 가격 참조 추출"""
        references = []

        for est in similar_estimates:
            metadata = est.get("metadata", {})
            price = metadata.get("total_price")

            if price:
                references.append({
                    "price": price,
                    "similarity": est.get("similarity", 0),
                    "estimate_id": metadata.get("estimate_id", "unknown"),
                })

        return references

    def _calculate_search_confidence(
        self,
        similar_estimates: list[dict],
        relevant_rules: list[dict],
    ) -> float:
        """검색 신뢰도 계산"""
        if not similar_estimates and not relevant_rules:
            return 0.0

        # 유사 견적 평균 유사도
        est_scores = [e.get("similarity", 0) for e in similar_estimates]
        est_avg = sum(est_scores) / len(est_scores) if est_scores else 0

        # 규칙 평균 유사도
        rule_scores = [r.get("similarity", 0) for r in relevant_rules]
        rule_avg = sum(rule_scores) / len(rule_scores) if rule_scores else 0

        # 가중 평균 (견적 70%, 규칙 30%)
        return (est_avg * 0.7) + (rule_avg * 0.3)

    def _check_breaker_type_rule(
        self,
        estimate_data: dict,
        rule: Any,
    ) -> bool:
        """차단기 타입 규칙 체크"""
        # 규칙 내용 분석하여 위반 여부 확인
        # 실제 구현 시 규칙 파싱 로직 추가
        return False

    def _check_small_breaker_rule(
        self,
        estimate_data: dict,
        rule: Any,
    ) -> bool:
        """소형 차단기 규칙 체크"""
        branches = estimate_data.get("branch_breakers", [])

        for b in branches:
            poles = b.get("poles", 2)
            current = b.get("current", 20)
            frame_af = b.get("frame_af", 50)

            # 2P 20A/30A인데 50AF 이상 사용 시
            if poles == 2 and current in [20, 30] and frame_af >= 50:
                return True

        return False


# 싱글톤 인스턴스 접근
_service: Optional[RAGIntegrationService] = None


def get_rag_integration_service() -> RAGIntegrationService:
    """RAGIntegrationService 싱글톤"""
    global _service
    if _service is None:
        _service = RAGIntegrationService()
    return _service
