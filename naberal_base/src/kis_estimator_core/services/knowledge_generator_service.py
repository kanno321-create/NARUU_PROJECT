"""
지식 자동 생성 서비스 (Phase XIII)

감지된 패턴을 RAG 지식베이스에 자동으로 추가합니다.
Zero-Mock 원칙: 모든 지식은 실제 패턴에서 생성됩니다.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

KnowledgeType = Literal["RULE", "PRICE", "KNOWHOW"]


@dataclass
class GeneratedKnowledge:
    """생성된 지식 데이터 모델"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    title: str
    content: str
    tags: list[str]
    source_pattern_id: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    synced_to_rag: bool = False
    rag_document_id: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "source_pattern_id": self.source_pattern_id,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "synced_to_rag": self.synced_to_rag,
            "rag_document_id": self.rag_document_id
        }


# ============================================================================
# Knowledge Generator Service
# ============================================================================

class KnowledgeGeneratorService:
    """
    지식 자동 생성 서비스

    Features:
    - 패턴에서 자연어 지식 생성
    - RAG 시스템 연동
    - 중복 지식 필터링
    - 신뢰도 기반 필터링
    """

    # 지식 생성 템플릿
    TEMPLATES = {
        "PRICE_ADJUSTMENT": {
            "title": "{pole} {frame} 가격 조정 규칙",
            "content": "{pole} {frame} 차단기 견적 시, CEO는 평균 {adjustment_rate}% 가격 조정을 적용합니다. 이 패턴은 {occurrences}회 관측되었으며 신뢰도는 {confidence}%입니다.",
            "tags": ["가격", "조정", "CEO패턴"]
        },
        "BRAND_PREFERENCE": {
            "title": "{pole} {frame} 브랜드 선호도",
            "content": "{pole} {frame} 사양의 차단기에서 CEO는 {preferred_brand} 브랜드를 선호합니다 (선호율: {preference_rate}%). 이 패턴은 {occurrences}회 관측되었습니다.",
            "tags": ["브랜드", "선호도", "CEO패턴"]
        },
        "LAYOUT_RULE": {
            "title": "분기 {branch_range} 레이아웃 규칙",
            "content": "분기 차단기가 {branch_range} 범위일 때, CEO는 특정 레이아웃 패턴을 선호합니다. 이 패턴은 {occurrences}회 관측되었으며 신뢰도는 {confidence}%입니다.",
            "tags": ["레이아웃", "배치", "CEO패턴"]
        },
        "MATERIAL_SWAP": {
            "title": "{from_brand} → {to_brand} 자재 교체 패턴",
            "content": "CEO는 {from_brand} 브랜드 자재를 {to_brand}로 교체하는 경향이 있습니다 (교체 횟수: {swap_count}회). 이 패턴을 견적 시 고려하세요.",
            "tags": ["자재", "교체", "CEO패턴"]
        }
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 파일 저장 경로 (None이면 기본 경로 사용)
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "knowledge"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._knowledge: dict[str, GeneratedKnowledge] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        """기존 지식 로드"""
        try:
            index_file = self.storage_path / "knowledge_index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("knowledge", []):
                        knowledge = GeneratedKnowledge(
                            knowledge_id=item["knowledge_id"],
                            knowledge_type=item["knowledge_type"],
                            title=item["title"],
                            content=item["content"],
                            tags=item["tags"],
                            source_pattern_id=item["source_pattern_id"],
                            confidence=item["confidence"],
                            created_at=datetime.fromisoformat(item["created_at"]),
                            synced_to_rag=item.get("synced_to_rag", False),
                            rag_document_id=item.get("rag_document_id")
                        )
                        self._knowledge[knowledge.knowledge_id] = knowledge
                logger.info(f"로드된 지식: {len(self._knowledge)}개")
        except Exception as e:
            logger.warning(f"지식 로드 실패: {e}")

    def _save_index(self) -> None:
        """인덱스 파일 저장"""
        index_file = self.storage_path / "knowledge_index.json"
        data = {
            "knowledge": [k.to_dict() for k in self._knowledge.values()],
            "total": len(self._knowledge),
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _is_duplicate(self, source_pattern_id: str) -> bool:
        """중복 지식 체크"""
        for k in self._knowledge.values():
            if k.source_pattern_id == source_pattern_id:
                return True
        return False

    async def generate_from_pattern(
        self,
        pattern: dict,
        min_confidence: float = 0.7,
        auto_sync_rag: bool = True
    ) -> Optional[GeneratedKnowledge]:
        """
        패턴에서 지식 생성

        Args:
            pattern: 패턴 데이터
            min_confidence: 최소 신뢰도 임계값
            auto_sync_rag: RAG 자동 동기화 여부

        Returns:
            생성된 지식 (신뢰도 미달 시 None)
        """
        category = pattern.get("category")
        confidence = pattern.get("confidence", 0)

        # 신뢰도 체크
        if confidence < min_confidence:
            logger.debug(f"신뢰도 미달: {confidence} < {min_confidence}")
            return None

        # 중복 체크
        pattern_id = pattern.get("pattern_id", "")
        if self._is_duplicate(pattern_id):
            logger.debug(f"중복 패턴: {pattern_id}")
            return None

        # 템플릿 선택
        template = self.TEMPLATES.get(category)
        if not template:
            logger.warning(f"알 수 없는 카테고리: {category}")
            return None

        # 템플릿 변수 준비
        condition = pattern.get("condition", {})
        action = pattern.get("action", {})
        occurrences = pattern.get("occurrences", 1)

        template_vars = {
            **condition,
            **action,
            "occurrences": occurrences,
            "confidence": round(confidence * 100, 1)
        }

        # 지식 생성
        try:
            title = template["title"].format(**template_vars)
            content = template["content"].format(**template_vars)
        except KeyError as e:
            logger.warning(f"템플릿 변수 누락: {e}")
            # 기본값으로 대체
            title = f"{category} 패턴"
            content = f"패턴 조건: {condition}, 액션: {action}"

        knowledge_type: KnowledgeType = self._determine_knowledge_type(category)

        knowledge = GeneratedKnowledge(
            knowledge_id=str(uuid.uuid4()),
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            tags=template.get("tags", []) + [category],
            source_pattern_id=pattern_id,
            confidence=confidence
        )

        self._knowledge[knowledge.knowledge_id] = knowledge

        # RAG 동기화
        if auto_sync_rag:
            await self._sync_to_rag(knowledge)

        self._save_index()
        logger.info(f"지식 생성: {knowledge.title}")

        return knowledge

    def _determine_knowledge_type(self, category: str) -> KnowledgeType:
        """카테고리에서 지식 타입 결정"""
        if category == "PRICE_ADJUSTMENT":
            return "PRICE"
        elif category in ["BRAND_PREFERENCE", "MATERIAL_SWAP"]:
            return "RULE"
        else:
            return "KNOWHOW"

    async def _sync_to_rag(self, knowledge: GeneratedKnowledge) -> bool:
        """RAG 시스템에 동기화"""
        try:
            # RAGLearner 임포트 및 동기화 시도
            from kis_estimator_core.rag.learner import RAGLearner

            learner = RAGLearner()

            # 지식을 RAG 문서로 변환
            document = {
                "title": knowledge.title,
                "content": knowledge.content,
                "metadata": {
                    "type": "ai_learned",
                    "knowledge_id": knowledge.knowledge_id,
                    "knowledge_type": knowledge.knowledge_type,
                    "source_pattern_id": knowledge.source_pattern_id,
                    "confidence": knowledge.confidence,
                    "tags": knowledge.tags,
                    "created_at": knowledge.created_at.isoformat()
                }
            }

            # RAG에 저장
            doc_id = await learner.add_knowledge(
                content=knowledge.content,
                title=knowledge.title,
                tags=knowledge.tags,
                metadata=document["metadata"]
            )

            knowledge.synced_to_rag = True
            knowledge.rag_document_id = doc_id
            self._save_index()

            logger.info(f"RAG 동기화 완료: {knowledge.knowledge_id} → {doc_id}")
            return True

        except ImportError:
            logger.warning("RAGLearner 모듈을 찾을 수 없습니다. RAG 동기화 건너뜀.")
            return False
        except Exception as e:
            logger.error(f"RAG 동기화 실패: {e}")
            return False

    async def generate_batch(
        self,
        patterns: list[dict],
        min_confidence: float = 0.7,
        dry_run: bool = False
    ) -> dict:
        """
        여러 패턴에서 일괄 지식 생성

        Args:
            patterns: 패턴 목록
            min_confidence: 최소 신뢰도
            dry_run: 실제 저장 없이 미리보기만

        Returns:
            생성 결과 통계
        """
        generated = []
        skipped_duplicates = 0
        skipped_low_confidence = 0

        for pattern in patterns:
            if pattern.get("confidence", 0) < min_confidence:
                skipped_low_confidence += 1
                continue

            if self._is_duplicate(pattern.get("pattern_id", "")):
                skipped_duplicates += 1
                continue

            if not dry_run:
                knowledge = await self.generate_from_pattern(
                    pattern,
                    min_confidence=min_confidence,
                    auto_sync_rag=True
                )
                if knowledge:
                    generated.append(knowledge.to_dict())
            else:
                # Dry run: 미리보기만
                category = pattern.get("category")
                template = self.TEMPLATES.get(category, {})
                generated.append({
                    "title": template.get("title", f"{category} 패턴"),
                    "category": category,
                    "confidence": pattern.get("confidence"),
                    "preview": True
                })

        return {
            "generated": generated,
            "total_generated": len(generated),
            "skipped_duplicates": skipped_duplicates,
            "skipped_low_confidence": skipped_low_confidence,
            "dry_run": dry_run,
            "message": f"{'미리보기' if dry_run else '생성'} 완료: {len(generated)}개"
        }

    async def get_knowledge(
        self,
        knowledge_type: Optional[KnowledgeType] = None,
        synced_only: bool = False,
        limit: int = 50
    ) -> list[GeneratedKnowledge]:
        """
        지식 조회

        Args:
            knowledge_type: 지식 타입 필터
            synced_only: RAG 동기화된 것만
            limit: 최대 반환 개수

        Returns:
            지식 목록 (최신순)
        """
        result = list(self._knowledge.values())

        if knowledge_type:
            result = [k for k in result if k.knowledge_type == knowledge_type]

        if synced_only:
            result = [k for k in result if k.synced_to_rag]

        # 최신순 정렬
        result.sort(key=lambda x: x.created_at, reverse=True)

        return result[:limit]

    async def get_knowledge_by_id(self, knowledge_id: str) -> Optional[GeneratedKnowledge]:
        """ID로 지식 조회"""
        return self._knowledge.get(knowledge_id)

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """지식 삭제"""
        if knowledge_id in self._knowledge:
            knowledge = self._knowledge[knowledge_id]

            # RAG에서도 삭제 시도
            if knowledge.synced_to_rag and knowledge.rag_document_id:
                try:
                    from kis_estimator_core.rag.learner import RAGLearner
                    learner = RAGLearner()
                    await learner.delete_knowledge(knowledge.rag_document_id)
                except Exception as e:
                    logger.warning(f"RAG 삭제 실패: {e}")

            del self._knowledge[knowledge_id]
            self._save_index()
            logger.info(f"지식 삭제: {knowledge_id}")
            return True

        return False

    def get_stats(self) -> dict:
        """지식 통계"""
        if not self._knowledge:
            return {
                "total": 0,
                "by_type": {},
                "synced_count": 0,
                "latest": None
            }

        by_type: dict[str, int] = {}
        synced_count = 0

        for k in self._knowledge.values():
            by_type[k.knowledge_type] = by_type.get(k.knowledge_type, 0) + 1
            if k.synced_to_rag:
                synced_count += 1

        latest = max(self._knowledge.values(), key=lambda x: x.created_at)

        return {
            "total": len(self._knowledge),
            "by_type": by_type,
            "synced_count": synced_count,
            "latest": latest.created_at.isoformat()
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_knowledge_generator: Optional[KnowledgeGeneratorService] = None


def get_knowledge_generator() -> KnowledgeGeneratorService:
    """지식 생성 서비스 싱글톤 인스턴스 반환"""
    global _knowledge_generator
    if _knowledge_generator is None:
        _knowledge_generator = KnowledgeGeneratorService()
    return _knowledge_generator
