"""
RAG Vector Service - ChromaDB 기반 벡터 검색 서비스

견적 지식 베이스의 의미론적 검색을 제공합니다.
- 견적서 임베딩 및 저장
- 유사 견적 검색
- 규칙/패턴 검색
- 하이브리드 검색 (semantic + keyword)

Contract-First + Zero-Mock
NO MOCKS - Real vector operations only
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ChromaDB 임포트
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Vector search will be disabled.")


class DocumentCategory(str, Enum):
    """문서 카테고리"""
    ESTIMATE = "estimate"           # 견적서
    BREAKER = "breaker"            # 차단기 규칙
    ENCLOSURE = "enclosure"        # 외함 규칙
    ACCESSORY = "accessory"        # 부속자재 규칙
    FORMULA = "formula"            # 계산 공식
    FEEDBACK = "feedback"          # 사용자 피드백
    ERP_DOCUMENT = "erp_document"  # ERP 문서


@dataclass
class SearchResult:
    """검색 결과"""
    document_id: str
    content: str
    category: DocumentCategory
    score: float
    metadata: dict


class RAGVectorService:
    """
    ChromaDB 기반 RAG 벡터 서비스

    특징:
    - 로컬 영구 저장소 (data/chroma_db)
    - 카테고리별 컬렉션 분리
    - 하이브리드 검색 지원
    - 메타데이터 필터링
    """

    # 저장 경로
    PERSIST_DIR = Path("data/chroma_db")

    # 컬렉션 이름
    COLLECTION_ESTIMATES = "estimates"
    COLLECTION_RULES = "rules"
    COLLECTION_FEEDBACK = "feedback"
    COLLECTION_ERP = "erp_documents"

    _instance: Optional['RAGVectorService'] = None
    _client: Any = None
    _collections: dict = {}

    def __new__(cls) -> 'RAGVectorService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """ChromaDB 클라이언트 초기화"""
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return

        try:
            self.PERSIST_DIR.mkdir(parents=True, exist_ok=True)

            # ChromaDB 클라이언트 생성 (영구 저장소)
            self._client = chromadb.PersistentClient(
                path=str(self.PERSIST_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )

            # 컬렉션 초기화
            self._collections = {
                self.COLLECTION_ESTIMATES: self._client.get_or_create_collection(
                    name=self.COLLECTION_ESTIMATES,
                    metadata={"description": "견적서 문서"}
                ),
                self.COLLECTION_RULES: self._client.get_or_create_collection(
                    name=self.COLLECTION_RULES,
                    metadata={"description": "견적 규칙 및 패턴"}
                ),
                self.COLLECTION_FEEDBACK: self._client.get_or_create_collection(
                    name=self.COLLECTION_FEEDBACK,
                    metadata={"description": "사용자 피드백"}
                ),
                self.COLLECTION_ERP: self._client.get_or_create_collection(
                    name=self.COLLECTION_ERP,
                    metadata={"description": "ERP 문서"}
                ),
            }

            logger.info(f"RAGVectorService initialized with {len(self._collections)} collections")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._client = None

    def _get_collection_name(self, category: DocumentCategory) -> str:
        """카테고리에 따른 컬렉션 이름 반환"""
        category_mapping = {
            DocumentCategory.ESTIMATE: self.COLLECTION_ESTIMATES,
            DocumentCategory.BREAKER: self.COLLECTION_RULES,
            DocumentCategory.ENCLOSURE: self.COLLECTION_RULES,
            DocumentCategory.ACCESSORY: self.COLLECTION_RULES,
            DocumentCategory.FORMULA: self.COLLECTION_RULES,
            DocumentCategory.FEEDBACK: self.COLLECTION_FEEDBACK,
            DocumentCategory.ERP_DOCUMENT: self.COLLECTION_ERP,
        }
        return category_mapping.get(category, self.COLLECTION_RULES)

    def _generate_id(self, content: str, category: str) -> str:
        """고유 ID 생성"""
        hash_input = f"{content}:{category}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def add_document(
        self,
        content: str,
        category: DocumentCategory,
        metadata: Optional[dict] = None,
        document_id: Optional[str] = None,
    ) -> str:
        """
        문서 추가

        Args:
            content: 문서 내용
            category: 문서 카테고리
            metadata: 추가 메타데이터
            document_id: 문서 ID (없으면 자동 생성)

        Returns:
            문서 ID
        """
        if not self._client:
            logger.error("ChromaDB not initialized")
            return ""

        try:
            collection_name = self._get_collection_name(category)
            collection = self._collections.get(collection_name)

            if not collection:
                logger.error(f"Collection not found: {collection_name}")
                return ""

            doc_id = document_id or self._generate_id(content, category.value)

            # 메타데이터 준비
            doc_metadata = {
                "category": category.value,
                "created_at": datetime.now(UTC).isoformat(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            }
            if metadata:
                doc_metadata.update(metadata)

            # 문서 추가 (ChromaDB가 자동으로 임베딩 생성)
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[doc_metadata],
            )

            logger.info(f"Added document {doc_id} to {collection_name}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return ""

    def add_documents_batch(
        self,
        documents: list[dict],
    ) -> list[str]:
        """
        문서 일괄 추가

        Args:
            documents: 문서 목록 [{"content": str, "category": DocumentCategory, "metadata": dict}, ...]

        Returns:
            추가된 문서 ID 목록
        """
        if not self._client:
            return []

        added_ids = []
        for doc in documents:
            doc_id = self.add_document(
                content=doc.get("content", ""),
                category=doc.get("category", DocumentCategory.ESTIMATE),
                metadata=doc.get("metadata"),
            )
            if doc_id:
                added_ids.append(doc_id)

        return added_ids

    def search(
        self,
        query: str,
        category: Optional[DocumentCategory] = None,
        n_results: int = 5,
        min_score: float = 0.0,
        metadata_filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        유사 문서 검색

        Args:
            query: 검색 쿼리
            category: 카테고리 필터 (None이면 전체)
            n_results: 최대 결과 수
            min_score: 최소 유사도 점수
            metadata_filter: 메타데이터 필터

        Returns:
            검색 결과 목록
        """
        if not self._client:
            return []

        try:
            results = []

            # 검색할 컬렉션 결정
            if category:
                collection_names = [self._get_collection_name(category)]
            else:
                collection_names = list(self._collections.keys())

            for collection_name in collection_names:
                collection = self._collections.get(collection_name)
                if not collection:
                    continue

                # where 필터 구성
                where_filter = None
                if category:
                    where_filter = {"category": category.value}
                if metadata_filter:
                    if where_filter:
                        where_filter.update(metadata_filter)
                    else:
                        where_filter = metadata_filter

                # 검색 실행
                search_results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter if where_filter else None,
                )

                # 결과 변환
                if search_results and search_results.get('ids'):
                    ids = search_results['ids'][0]
                    documents = search_results['documents'][0] if search_results.get('documents') else []
                    metadatas = search_results['metadatas'][0] if search_results.get('metadatas') else []
                    distances = search_results['distances'][0] if search_results.get('distances') else []

                    for i, doc_id in enumerate(ids):
                        # 거리를 점수로 변환 (낮을수록 좋음)
                        score = 1.0 / (1.0 + distances[i]) if i < len(distances) else 0.5

                        if score >= min_score:
                            doc_category = DocumentCategory(
                                metadatas[i].get('category', 'estimate')
                            ) if i < len(metadatas) else DocumentCategory.ESTIMATE

                            results.append(SearchResult(
                                document_id=doc_id,
                                content=documents[i] if i < len(documents) else "",
                                category=doc_category,
                                score=score,
                                metadata=metadatas[i] if i < len(metadatas) else {},
                            ))

            # 점수순 정렬
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:n_results]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_hybrid(
        self,
        query: str,
        keywords: list[str],
        category: Optional[DocumentCategory] = None,
        n_results: int = 5,
    ) -> list[SearchResult]:
        """
        하이브리드 검색 (semantic + keyword)

        Args:
            query: 의미론적 검색 쿼리
            keywords: 키워드 목록
            category: 카테고리 필터
            n_results: 최대 결과 수

        Returns:
            검색 결과 목록
        """
        # Semantic 검색
        semantic_results = self.search(
            query=query,
            category=category,
            n_results=n_results * 2,  # 더 많이 가져와서 필터링
        )

        # 키워드 부스팅
        keyword_set = set(kw.lower() for kw in keywords)

        for result in semantic_results:
            content_lower = result.content.lower()
            keyword_matches = sum(1 for kw in keyword_set if kw in content_lower)
            # 키워드 매칭 보너스 (최대 50%)
            keyword_bonus = min(0.5, keyword_matches * 0.1)
            result.score = result.score * (1 + keyword_bonus)

        # 재정렬
        semantic_results.sort(key=lambda x: x.score, reverse=True)
        return semantic_results[:n_results]

    def delete_document(self, document_id: str, category: DocumentCategory) -> bool:
        """
        문서 삭제

        Args:
            document_id: 문서 ID
            category: 문서 카테고리

        Returns:
            성공 여부
        """
        if not self._client:
            return False

        try:
            collection_name = self._get_collection_name(category)
            collection = self._collections.get(collection_name)

            if collection:
                collection.delete(ids=[document_id])
                logger.info(f"Deleted document {document_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def update_document(
        self,
        document_id: str,
        content: str,
        category: DocumentCategory,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        문서 업데이트

        Args:
            document_id: 문서 ID
            content: 새 내용
            category: 카테고리
            metadata: 새 메타데이터

        Returns:
            성공 여부
        """
        if not self._client:
            return False

        try:
            collection_name = self._get_collection_name(category)
            collection = self._collections.get(collection_name)

            if not collection:
                return False

            # 메타데이터 준비
            doc_metadata = {
                "category": category.value,
                "updated_at": datetime.now(UTC).isoformat(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            }
            if metadata:
                doc_metadata.update(metadata)

            # 업데이트
            collection.update(
                ids=[document_id],
                documents=[content],
                metadatas=[doc_metadata],
            )

            logger.info(f"Updated document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False

    def get_stats(self) -> dict:
        """
        통계 정보 조회

        Returns:
            컬렉션별 문서 수 등 통계
        """
        if not self._client:
            return {"error": "ChromaDB not initialized"}

        stats = {
            "collections": {},
            "total_documents": 0,
        }

        try:
            for name, collection in self._collections.items():
                count = collection.count()
                stats["collections"][name] = count
                stats["total_documents"] += count
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            stats["error"] = str(e)

        return stats

    def load_knowledge_pack(self, pack_path: str) -> int:
        """
        지식 팩 로드 (JSON 파일)

        Args:
            pack_path: 지식 팩 파일 경로

        Returns:
            로드된 문서 수
        """
        try:
            with open(pack_path, 'r', encoding='utf-8') as f:
                pack_data = json.load(f)

            documents = []

            # 차단기 규칙
            if 'breakers' in pack_data:
                for item in pack_data['breakers']:
                    documents.append({
                        "content": json.dumps(item, ensure_ascii=False),
                        "category": DocumentCategory.BREAKER,
                        "metadata": {"source": pack_path, "type": "breaker"}
                    })

            # 외함 규칙
            if 'enclosures' in pack_data:
                for item in pack_data['enclosures']:
                    documents.append({
                        "content": json.dumps(item, ensure_ascii=False),
                        "category": DocumentCategory.ENCLOSURE,
                        "metadata": {"source": pack_path, "type": "enclosure"}
                    })

            # 부속자재 규칙
            if 'accessories' in pack_data:
                for item in pack_data['accessories']:
                    documents.append({
                        "content": json.dumps(item, ensure_ascii=False),
                        "category": DocumentCategory.ACCESSORY,
                        "metadata": {"source": pack_path, "type": "accessory"}
                    })

            # 공식
            if 'formulas' in pack_data:
                for item in pack_data['formulas']:
                    documents.append({
                        "content": json.dumps(item, ensure_ascii=False),
                        "category": DocumentCategory.FORMULA,
                        "metadata": {"source": pack_path, "type": "formula"}
                    })

            # 일괄 추가
            added_ids = self.add_documents_batch(documents)
            logger.info(f"Loaded {len(added_ids)} documents from {pack_path}")
            return len(added_ids)

        except Exception as e:
            logger.error(f"Failed to load knowledge pack: {e}")
            return 0


# 싱글톤 인스턴스 접근
_service: Optional[RAGVectorService] = None


def get_rag_vector_service() -> RAGVectorService:
    """RAGVectorService 싱글톤"""
    global _service
    if _service is None:
        _service = RAGVectorService()
    return _service
