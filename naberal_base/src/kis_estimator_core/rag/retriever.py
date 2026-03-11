"""
Hybrid Retriever - 하이브리드 검색 엔진

Semantic (벡터) + Keyword (BM25) 검색 결합
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from kis_estimator_core.rag.config import RAGConfig
from kis_estimator_core.rag.embedder import LocalEmbedder

if TYPE_CHECKING:
    import chromadb
    from chromadb.api.models.Collection import Collection


@dataclass
class SearchResult:
    """검색 결과"""

    id: str
    content: str
    metadata: dict
    score: float
    source: str  # "semantic" | "keyword" | "hybrid"


class HybridRetriever:
    """하이브리드 검색 엔진"""

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        self.embedder = LocalEmbedder(self.config)
        self._client: chromadb.ClientAPI | None = None
        self._collection: Collection | None = None

    @property
    def client(self) -> "chromadb.ClientAPI":
        """ChromaDB 클라이언트"""
        if self._client is None:
            self._client = self._init_client()
        return self._client

    @property
    def collection(self) -> "Collection":
        """ChromaDB 컬렉션 (없으면 자동 생성)"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"},  # 코사인 유사도
            )
        return self._collection

    def _init_client(self) -> "chromadb.ClientAPI":
        """ChromaDB 클라이언트 초기화 (신규 API)"""
        try:
            from pathlib import Path

            import chromadb

            persist_dir = Path(self.config.chroma_persist_dir)

            # 신규 API: PersistentClient 사용
            return chromadb.PersistentClient(path=str(persist_dir))

        except ImportError as e:
            raise ImportError(
                "chromadb 패키지가 필요합니다.\n"
                "설치: pip install chromadb"
            ) from e

    def search(
        self,
        query: str,
        top_k: int | None = None,
        category: str | None = None,
        search_type: str | None = None,
    ) -> list[SearchResult]:
        """통합 검색"""
        top_k = top_k or self.config.top_k
        search_type = search_type or self.config.search_type

        if search_type == "semantic":
            return self._semantic_search(query, top_k, category)
        elif search_type == "keyword":
            return self._keyword_search(query, top_k, category)
        else:  # hybrid
            return self._hybrid_search(query, top_k, category)

    def _semantic_search(
        self, query: str, top_k: int, category: str | None = None
    ) -> list[SearchResult]:
        """시맨틱 (벡터) 검색"""
        # 쿼리 임베딩
        query_embedding = self.embedder.embed_query(query)

        # 필터 구성
        where_filter = None
        if category:
            where_filter = {"category": category}

        # ChromaDB 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # 결과 변환
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # 거리를 유사도로 변환 (코사인: 1 - distance)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance

                if score >= self.config.similarity_threshold:
                    search_results.append(
                        SearchResult(
                            id=doc_id,
                            content=results["documents"][0][i] if results["documents"] else "",
                            metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                            score=score,
                            source="semantic",
                        )
                    )

        return search_results

    def _keyword_search(
        self, query: str, top_k: int, category: str | None = None
    ) -> list[SearchResult]:
        """키워드 (BM25 유사) 검색"""
        # ChromaDB의 where_document 필터 사용
        where_filter = None
        if category:
            where_filter = {"category": category}

        # 쿼리 토큰화
        keywords = self._tokenize_query(query)

        # 각 키워드로 검색 후 병합
        all_results = {}

        for keyword in keywords:
            try:
                results = self.collection.get(
                    where_document={"$contains": keyword},
                    where=where_filter,
                    limit=top_k * 2,
                    include=["documents", "metadatas"],
                )

                if results["ids"]:
                    for i, doc_id in enumerate(results["ids"]):
                        if doc_id not in all_results:
                            all_results[doc_id] = {
                                "content": results["documents"][i] if results["documents"] else "",
                                "metadata": results["metadatas"][i] if results["metadatas"] else {},
                                "keyword_count": 0,
                            }
                        all_results[doc_id]["keyword_count"] += 1

            except Exception:
                continue

        # 키워드 매칭 수로 점수 계산
        search_results = []
        for doc_id, data in all_results.items():
            score = data["keyword_count"] / len(keywords) if keywords else 0
            search_results.append(
                SearchResult(
                    id=doc_id,
                    content=data["content"],
                    metadata=data["metadata"],
                    score=score,
                    source="keyword",
                )
            )

        # 점수 정렬 및 top_k 반환
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:top_k]

    def _hybrid_search(
        self, query: str, top_k: int, category: str | None = None
    ) -> list[SearchResult]:
        """하이브리드 검색 (Semantic + Keyword)"""
        # 각각 더 많이 가져와서 병합
        semantic_results = self._semantic_search(query, top_k * 2, category)
        keyword_results = self._keyword_search(query, top_k * 2, category)

        # 결과 병합 (RRF - Reciprocal Rank Fusion)
        k = 60  # RRF 상수
        scores = {}

        # 시맨틱 결과 점수
        for rank, result in enumerate(semantic_results):
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "rrf_score": 0,
                }
            scores[result.id]["rrf_score"] += 1 / (k + rank + 1)
            scores[result.id]["result"].source = "hybrid"

        # 키워드 결과 점수
        for rank, result in enumerate(keyword_results):
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "rrf_score": 0,
                }
            scores[result.id]["rrf_score"] += 1 / (k + rank + 1)
            scores[result.id]["result"].source = "hybrid"

        # RRF 점수로 정렬
        merged = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)

        # 결과 반환
        results = []
        for item in merged[:top_k]:
            result = item["result"]
            result.score = item["rrf_score"]
            results.append(result)

        return results

    def _tokenize_query(self, query: str) -> list[str]:
        """쿼리 토큰화 (한국어 + 영어)"""
        # 특수문자 제거
        cleaned = re.sub(r"[^\w\s가-힣]", " ", query)

        # 토큰 분리
        tokens = cleaned.split()

        # 불용어 제거 (간단한 목록)
        stopwords = {"의", "가", "이", "은", "는", "를", "을", "에", "and", "the", "a", "an"}
        tokens = [t for t in tokens if t.lower() not in stopwords and len(t) > 1]

        return tokens

    def search_by_category(
        self, query: str, category: str, top_k: int | None = None
    ) -> list[SearchResult]:
        """카테고리 필터 검색"""
        return self.search(query, top_k, category=category)

    def search_breaker(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """차단기 정보 검색"""
        return self.search_by_category(query, "BREAKER", top_k)

    def search_enclosure(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """외함 정보 검색"""
        return self.search_by_category(query, "ENCLOSURE", top_k)

    def search_accessory(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """부속자재 정보 검색"""
        return self.search_by_category(query, "ACCESSORY", top_k)

    def search_formula(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """공식/규칙 검색"""
        return self.search_by_category(query, "FORMULA", top_k)
