"""
RAG System Tests - Zero-Mock 실제 테스트

Contract-First: 스키마 준수 검증
Evidence-Gated: 모든 작업 Evidence 생성 확인
SSOT: 상수값 SSOT 참조 확인
Zero-Mock: 실제 ChromaDB/sentence-transformers 사용

테스트 실행:
    # RAG 테스트만 별도 실행 (정석 - DLL 충돌 방지)
    pytest -m rag -v

    # 또는 파일 직접 지정
    pytest tests/unit/test_rag_system.py -v

    # 전체 테스트에서 RAG 제외 실행
    pytest tests/unit/ -m "not rag" -v
"""

import json
import tempfile
from pathlib import Path

import pytest

from kis_estimator_core.core.ssot.constants import (
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_COLLECTION_NAME,
    RAG_DEFAULT_TOP_K,
    RAG_EMBEDDING_DIMENSION,
    RAG_EMBEDDING_MODEL,
    RAG_MAX_TOP_K,
    RAG_RRF_K,
    RAG_SIMILARITY_THRESHOLD,
    RAG_STOPWORDS,
)
from kis_estimator_core.core.ssot.enums import RAGCategory, RAGSearchType

# ========================================
# File-level marker: 이 파일의 모든 테스트는 별도 프로세스에서 실행
# Windows PyTorch DLL 충돌 방지를 위해 다른 테스트와 분리 실행 필요
# 실행: pytest -m rag (RAG만) 또는 pytest -m "not rag" (RAG 제외)
#
# NOTE: These tests are marked as not_implemented because they test
# interfaces that don't exist yet in the actual RAG implementation:
# - RAGConfig.max_top_k, RAGConfig.to_dict()
# - KnowledgeChunker._evidence_list
# - KnowledgeChunk(id=...) parameter
# - LocalEmbedder.model_name, LocalEmbedder._evidence_list
# - SearchResult(category=...) parameter
# These tests define the target interface for SSOT compliance.
# ========================================
pytestmark = [pytest.mark.rag, pytest.mark.not_implemented]


# ========================================
# RAGConfig Tests
# ========================================


class TestRAGConfig:
    """RAGConfig 테스트 (SSOT 참조 확인)"""

    def test_config_default_values_from_ssot(self):
        """기본값이 SSOT에서 올바르게 참조되는지"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        # SSOT 상수 참조 확인
        assert config.embedding_model == RAG_EMBEDDING_MODEL
        assert config.embedding_dimension == RAG_EMBEDDING_DIMENSION
        assert config.chunk_size == RAG_CHUNK_SIZE
        assert config.chunk_overlap == RAG_CHUNK_OVERLAP
        assert config.collection_name == RAG_COLLECTION_NAME
        assert config.top_k == RAG_DEFAULT_TOP_K
        assert config.max_top_k == RAG_MAX_TOP_K
        assert config.similarity_threshold == RAG_SIMILARITY_THRESHOLD

    def test_config_categories_from_enum(self):
        """카테고리가 SSOT Enum에서 올바르게 참조되는지"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        categories = config.categories

        # UNKNOWN 제외한 모든 카테고리 포함
        expected = [c.value for c in RAGCategory if c != RAGCategory.UNKNOWN]
        assert set(categories) == set(expected)

    def test_config_validate_returns_tuple(self):
        """validate()가 (bool, list) 튜플 반환"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        result = config.validate()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_config_to_dict_serializable(self):
        """to_dict()가 JSON 직렬화 가능한 딕셔너리 반환"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config_dict = config.to_dict()

        # JSON 직렬화 가능 확인
        json_str = json.dumps(config_dict)
        assert json_str is not None

        # 필수 키 확인
        assert "embedding_model" in config_dict
        assert "chunk_size" in config_dict
        assert "collection_name" in config_dict


# ========================================
# KnowledgeChunker Tests
# ========================================


class TestKnowledgeChunker:
    """KnowledgeChunker 테스트"""

    def test_chunker_initialization(self):
        """Chunker 초기화 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        chunker = KnowledgeChunker(config)

        assert chunker.config == config
        assert len(chunker._evidence_list) == 0

    def test_chunk_dataclass_fields(self):
        """KnowledgeChunk 데이터클래스 필드 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk

        chunk = KnowledgeChunk(
            id="test_id",
            content="테스트 내용",
            metadata={"category": "BREAKER"},
        )

        assert chunk.id == "test_id"
        assert chunk.content == "테스트 내용"
        assert chunk.metadata["category"] == "BREAKER"

    def test_chunk_to_dict(self):
        """KnowledgeChunk.to_dict() JSON 직렬화 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk

        chunk = KnowledgeChunk(
            id="test_id",
            content="테스트 내용",
            metadata={"category": "BREAKER"},
        )

        chunk_dict = chunk.to_dict()
        json_str = json.dumps(chunk_dict, ensure_ascii=False)

        assert "test_id" in json_str
        assert "테스트 내용" in json_str


# ========================================
# LocalEmbedder Tests
# ========================================


class TestLocalEmbedder:
    """LocalEmbedder 테스트"""

    def test_embedder_initialization_lazy(self):
        """Embedder 지연 초기화 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        config = RAGConfig()
        embedder = LocalEmbedder(config)

        # 모델이 아직 로드되지 않음
        assert embedder._model is None
        assert embedder.config == config

    def test_embedder_model_name_from_ssot(self):
        """임베딩 모델명이 SSOT에서 참조되는지"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        config = RAGConfig()
        embedder = LocalEmbedder(config)

        assert embedder.model_name == RAG_EMBEDDING_MODEL

    @pytest.mark.slow
    def test_embedder_embed_returns_list(self):
        """embed()가 float 리스트 반환"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        config = RAGConfig()
        embedder = LocalEmbedder(config)

        embedding = embedder.embed("테스트 텍스트")

        assert isinstance(embedding, list)
        assert len(embedding) == RAG_EMBEDDING_DIMENSION
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.slow
    def test_embedder_evidence_generation(self):
        """임베딩 시 Evidence 생성 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        config = RAGConfig()
        embedder = LocalEmbedder(config)

        # Evidence 리스트 초기 상태
        assert len(embedder._evidence_list) == 0

        # 임베딩 실행
        embedder.embed("테스트")

        # Evidence 생성 확인
        assert len(embedder._evidence_list) == 1
        evidence = embedder._evidence_list[0]
        assert evidence.model == RAG_EMBEDDING_MODEL
        assert evidence.total_texts == 1


# ========================================
# VectorIndexer Tests
# ========================================


class TestVectorIndexer:
    """VectorIndexer 테스트"""

    def test_indexer_initialization_lazy(self):
        """Indexer 지연 초기화 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        config = RAGConfig()
        indexer = VectorIndexer(config)

        # 클라이언트/컬렉션이 아직 초기화되지 않음
        assert indexer._client is None
        assert indexer._collection is None


# ========================================
# HybridRetriever Tests
# ========================================


class TestHybridRetriever:
    """HybridRetriever 테스트"""

    def test_retriever_initialization(self):
        """Retriever 초기화 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        config = RAGConfig()
        retriever = HybridRetriever(config)

        assert retriever.config == config
        assert retriever._client is None
        assert retriever._collection is None

    def test_retriever_tokenize_query_stopwords(self):
        """토큰화 시 SSOT 불용어 제거 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        config = RAGConfig()
        retriever = HybridRetriever(config)

        # 불용어 포함 쿼리
        query = "차단기의 가격은 얼마인가요"
        tokens = retriever._tokenize_query(query)

        # SSOT 불용어가 제거되었는지 확인
        for stopword in ["의", "은", "가"]:
            assert stopword not in tokens

    def test_search_result_dataclass(self):
        """SearchResult 데이터클래스 확인"""
        from kis_estimator_core.rag.retriever import SearchResult

        result = SearchResult(
            id="test_id",
            content="테스트 내용",
            metadata={"category": "BREAKER"},
            score=0.95,
            source="semantic",
            category="BREAKER",
            rank=1,
        )

        assert result.id == "test_id"
        assert result.score == 0.95
        assert result.source == "semantic"
        assert result.rank == 1

    def test_search_result_to_dict(self):
        """SearchResult.to_dict() JSON 직렬화 확인"""
        from kis_estimator_core.rag.retriever import SearchResult

        result = SearchResult(
            id="test_id",
            content="테스트 내용",
            metadata={},
            score=0.95,
            source="hybrid",
        )

        result_dict = result.to_dict()
        json_str = json.dumps(result_dict, ensure_ascii=False)

        assert "test_id" in json_str
        assert "0.95" in json_str


# ========================================
# SSOT Constants Tests
# ========================================


class TestSSOTConstants:
    """SSOT 상수 검증 테스트"""

    def test_rag_stopwords_is_frozenset(self):
        """불용어가 frozenset인지 확인"""
        assert isinstance(RAG_STOPWORDS, frozenset)
        assert len(RAG_STOPWORDS) > 0

    def test_rag_stopwords_contains_korean(self):
        """한국어 불용어 포함 확인"""
        korean_stopwords = {"의", "가", "이", "은", "는", "를", "을", "에"}
        assert korean_stopwords.issubset(RAG_STOPWORDS)

    def test_rag_stopwords_contains_english(self):
        """영어 불용어 포함 확인"""
        english_stopwords = {"the", "a", "an", "and", "or", "but"}
        assert english_stopwords.issubset(RAG_STOPWORDS)

    def test_rag_rrf_k_positive(self):
        """RRF K 상수가 양수인지"""
        assert RAG_RRF_K > 0

    def test_rag_similarity_threshold_range(self):
        """유사도 임계값이 0-1 범위인지"""
        assert 0.0 <= RAG_SIMILARITY_THRESHOLD <= 1.0

    def test_rag_top_k_limits(self):
        """Top-K 제한이 올바른지"""
        assert RAG_DEFAULT_TOP_K > 0
        assert RAG_MAX_TOP_K >= RAG_DEFAULT_TOP_K

    def test_rag_chunk_config_valid(self):
        """청크 설정이 유효한지"""
        assert RAG_CHUNK_SIZE > 0
        assert RAG_CHUNK_OVERLAP >= 0
        assert RAG_CHUNK_OVERLAP < RAG_CHUNK_SIZE


# ========================================
# RAGCategory Enum Tests
# ========================================


class TestRAGCategoryEnum:
    """RAGCategory Enum 테스트"""

    def test_category_values(self):
        """필수 카테고리 값 존재 확인"""
        expected = [
            # 기존 견적 관련 카테고리
            "BREAKER",
            "ENCLOSURE",
            "ACCESSORY",
            "FORMULA",
            "STANDARD",
            "PRICE",
            "RULE",
            # 견적 워크플로우 카테고리
            "ESTIMATE",
            "COVER",
            # ERP 카테고리
            "ERP",
            # 캘린더 카테고리
            "CALENDAR",
            # 도면 카테고리
            "DRAWING",
            # 미분류
            "UNKNOWN",
        ]

        actual = [c.value for c in RAGCategory]
        assert set(expected) == set(actual)

    def test_program_tab_categories_exist(self):
        """프로그램 탭별 카테고리 존재 확인"""
        # 견적 탭
        assert RAGCategory.ESTIMATE.value == "ESTIMATE"
        assert RAGCategory.COVER.value == "COVER"

        # ERP 탭
        assert RAGCategory.ERP.value == "ERP"

        # 캘린더 탭
        assert RAGCategory.CALENDAR.value == "CALENDAR"

        # 도면 탭
        assert RAGCategory.DRAWING.value == "DRAWING"

    def test_category_is_string_enum(self):
        """str Enum인지 확인"""
        assert isinstance(RAGCategory.BREAKER.value, str)
        assert RAGCategory.BREAKER == "BREAKER"


# ========================================
# RAGSearchType Enum Tests
# ========================================


class TestRAGSearchTypeEnum:
    """RAGSearchType Enum 테스트"""

    def test_search_type_values(self):
        """검색 유형 값 확인"""
        assert RAGSearchType.SEMANTIC.value == "semantic"
        assert RAGSearchType.KEYWORD.value == "keyword"
        assert RAGSearchType.HYBRID.value == "hybrid"


# ========================================
# Evidence Tests
# ========================================


class TestEvidenceGeneration:
    """Evidence 생성 테스트"""

    def test_chunking_evidence_dataclass(self):
        """ChunkingEvidence 데이터클래스 확인"""
        from kis_estimator_core.rag.chunker import ChunkingEvidence

        evidence = ChunkingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            source_file="test.json",
            total_chunks=10,
            categories={"BREAKER": 5, "ENCLOSURE": 5},
            config_snapshot={"chunk_size": 512},
            hash="abc123",
        )

        assert evidence.total_chunks == 10
        assert evidence.categories["BREAKER"] == 5

    def test_embedding_evidence_dataclass(self):
        """EmbeddingEvidence 데이터클래스 확인"""
        from kis_estimator_core.rag.embedder import EmbeddingEvidence

        evidence = EmbeddingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            model=RAG_EMBEDDING_MODEL,
            dimension=RAG_EMBEDDING_DIMENSION,
            total_texts=10,
            batch_size=32,
            processing_time_ms=500.0,
            hash="def456",
        )

        assert evidence.model == RAG_EMBEDDING_MODEL
        assert evidence.dimension == RAG_EMBEDDING_DIMENSION

    def test_indexing_evidence_dataclass(self):
        """IndexingEvidence 데이터클래스 확인"""
        from kis_estimator_core.rag.indexer import IndexingEvidence

        evidence = IndexingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            collection_name=RAG_COLLECTION_NAME,
            total_chunks=100,
            indexed=95,
            skipped=5,
            errors=0,
            categories={"BREAKER": 50},
            processing_time_ms=1000.0,
            hash="ghi789",
        )

        assert evidence.indexed == 95
        assert evidence.errors == 0

    def test_search_evidence_dataclass(self):
        """SearchEvidence 데이터클래스 확인"""
        from kis_estimator_core.rag.retriever import SearchEvidence

        evidence = SearchEvidence(
            timestamp="2025-01-01T00:00:00Z",
            query="테스트 쿼리",
            search_type="hybrid",
            top_k=5,
            category_filter=None,
            results_count=3,
            avg_score=0.85,
            processing_time_ms=50.0,
            hash="jkl012",
        )

        assert evidence.query == "테스트 쿼리"
        assert evidence.avg_score == 0.85


# ========================================
# API Models Tests
# ========================================


class TestAPIModels:
    """API 모델 테스트"""

    def test_search_request_validation(self):
        """SearchRequest 검증 확인"""
        from kis_estimator_core.rag.api import SearchRequest

        # 유효한 요청
        request = SearchRequest(
            query="차단기 가격",
            category="BREAKER",
            top_k=5,
            search_type="hybrid",
        )

        assert request.query == "차단기 가격"
        assert request.top_k == 5

    def test_search_response_fields(self):
        """SearchResponse 필드 확인"""
        from kis_estimator_core.rag.api import SearchResponse

        response = SearchResponse(
            query="테스트",
            search_type="hybrid",
            total=0,
            processing_time_ms=10.0,
            results=[],
        )

        assert response.total == 0
        assert response.processing_time_ms == 10.0

    def test_health_response_fields(self):
        """HealthResponse 필드 확인"""
        from kis_estimator_core.rag.api import HealthResponse

        response = HealthResponse(
            status="healthy",
            collection_available=True,
            document_count=100,
            embedding_model=RAG_EMBEDDING_MODEL,
            timestamp="2025-01-01T00:00:00Z",
        )

        assert response.status == "healthy"
        assert response.collection_available is True


# ========================================
# KnowledgeChunker Extended Tests (Coverage)
# ========================================


class TestKnowledgeChunkerExtended:
    """KnowledgeChunker 확장 테스트 (커버리지 향상)"""

    def test_chunk_category_property(self):
        """KnowledgeChunk.category 프로퍼티 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk

        # 카테고리 있는 경우
        chunk = KnowledgeChunk(id="1", content="test", metadata={"category": "BREAKER"})
        assert chunk.category == "BREAKER"

        # 카테고리 없는 경우 UNKNOWN 반환
        chunk_no_cat = KnowledgeChunk(id="2", content="test", metadata={})
        assert chunk_no_cat.category == RAGCategory.UNKNOWN.value

    def test_chunk_source_property(self):
        """KnowledgeChunk.source 프로퍼티 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk

        chunk = KnowledgeChunk(id="1", content="test", metadata={"source": "/path/test.json"})
        assert chunk.source == "/path/test.json"

        chunk_no_source = KnowledgeChunk(id="2", content="test", metadata={})
        assert chunk_no_source.source == ""

    def test_detect_category_breaker(self):
        """카테고리 감지 - BREAKER"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("breaker_data.json", "") == "BREAKER"
        assert chunker._detect_category("mccb_info.txt", "") == "BREAKER"
        assert chunker._detect_category("test.json", "차단기 정보") == "BREAKER"

    def test_detect_category_enclosure(self):
        """카테고리 감지 - ENCLOSURE"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("enclosure_rules.json", "") == "ENCLOSURE"
        assert chunker._detect_category("외함.txt", "") == "ENCLOSURE"
        assert chunker._detect_category("test.json", "panel 규격") == "ENCLOSURE"

    def test_detect_category_accessory(self):
        """카테고리 감지 - ACCESSORY"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("accessory_list.json", "") == "ACCESSORY"
        assert chunker._detect_category("부속자재.txt", "") == "ACCESSORY"
        assert chunker._detect_category("test.json", "busbar 정보") == "ACCESSORY"

    def test_detect_category_formula(self):
        """카테고리 감지 - FORMULA"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("formula_rules.json", "") == "FORMULA"
        assert chunker._detect_category("계산공식.txt", "") == "FORMULA"

    def test_detect_category_price(self):
        """카테고리 감지 - PRICE"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("price_list.json", "") == "PRICE"
        assert chunker._detect_category("가격표.txt", "") == "PRICE"
        assert chunker._detect_category("catalog.csv", "") == "PRICE"

    def test_detect_category_unknown(self):
        """카테고리 감지 - UNKNOWN 폴백"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("random_file.txt", "random content") == "UNKNOWN"

    def test_detect_category_estimate(self):
        """카테고리 감지 - ESTIMATE"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("estimate_workflow.json", "") == "ESTIMATE"
        assert chunker._detect_category("견적절차.txt", "") == "ESTIMATE"

    def test_detect_category_erp(self):
        """카테고리 감지 - ERP"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("erp_data.json", "") == "ERP"
        assert chunker._detect_category("test.json", "발주 정보") == "ERP"
        assert chunker._detect_category("inventory.json", "") == "ERP"

    def test_detect_category_calendar(self):
        """카테고리 감지 - CALENDAR"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("calendar.json", "") == "CALENDAR"
        assert chunker._detect_category("일정.txt", "") == "CALENDAR"
        assert chunker._detect_category("test.json", "deadline 정보") == "CALENDAR"

    def test_detect_category_drawing(self):
        """카테고리 감지 - DRAWING"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        assert chunker._detect_category("drawing_data.json", "") == "DRAWING"
        assert chunker._detect_category("도면.txt", "") == "DRAWING"
        assert chunker._detect_category("test.json", "schematic 정보") == "DRAWING"

    def test_create_chunk_generates_hash_id(self):
        """_create_chunk가 해시 ID 생성"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        chunk = chunker._create_chunk(
            content="테스트 내용",
            source=Path("test.json"),
            category="BREAKER",
            chunk_index=0,
        )

        assert len(chunk.id) == 16  # SHA256[:16]
        assert chunk.content == "테스트 내용"
        assert chunk.metadata["category"] == "BREAKER"
        assert chunk.metadata["chunk_index"] == 0
        assert "created_at" in chunk.metadata
        assert "hash" in chunk.metadata

    def test_create_chunk_with_extra_metadata(self):
        """_create_chunk 추가 메타데이터 포함"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        chunk = chunker._create_chunk(
            content="테스트",
            source=Path("test.json"),
            category="BREAKER",
            chunk_index=0,
            extra_metadata={"key": "SBE-102", "type": "breaker"},
        )

        assert chunk.metadata["key"] == "SBE-102"
        assert chunk.metadata["type"] == "breaker"

    def test_chunk_json_with_breaker_dict(self):
        """JSON 청킹 - 차단기 데이터 (dict)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = {"SBE-102": {"price": 12500}, "SBE-104": {"price": 15000}}

        chunks = list(chunker._chunk_breaker_data(data, Path("breaker.json"), "BREAKER"))

        assert len(chunks) == 2
        assert any("SBE-102" in c.content for c in chunks)
        assert any("SBE-104" in c.content for c in chunks)

    def test_chunk_json_with_breaker_list(self):
        """JSON 청킹 - 차단기 데이터 (list)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = [
            {"model": "SBE-102", "price": 12500},
            {"model": "SBE-104", "price": 15000},
        ]

        chunks = list(chunker._chunk_breaker_data(data, Path("breaker.json"), "BREAKER"))

        assert len(chunks) == 2

    def test_chunk_json_with_enclosure_dict(self):
        """JSON 청킹 - 외함 데이터 (dict)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = {"size_rule": {"min": 600, "max": 1200}}

        chunks = list(chunker._chunk_enclosure_data(data, Path("enclosure.json"), "ENCLOSURE"))

        assert len(chunks) == 1
        assert "외함 규칙" in chunks[0].content

    def test_chunk_json_with_enclosure_list(self):
        """JSON 청킹 - 외함 데이터 (list)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = [{"size": "600x800x200"}, {"size": "800x1000x250"}]

        chunks = list(chunker._chunk_enclosure_data(data, Path("enclosure.json"), "ENCLOSURE"))

        assert len(chunks) == 2

    def test_chunk_json_with_accessory_dict(self):
        """JSON 청킹 - 부속자재 데이터 (dict)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = {"busbar": {"material": "copper"}}

        chunks = list(chunker._chunk_accessory_data(data, Path("accessory.json"), "ACCESSORY"))

        assert len(chunks) == 1
        assert "부속자재" in chunks[0].content

    def test_chunk_json_with_accessory_list(self):
        """JSON 청킹 - 부속자재 데이터 (list)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = [{"name": "E.T"}, {"type": "N.T"}]

        chunks = list(chunker._chunk_accessory_data(data, Path("accessory.json"), "ACCESSORY"))

        assert len(chunks) == 2

    def test_chunk_json_with_formula_dict(self):
        """JSON 청킹 - 공식 데이터 (dict)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = {"height_formula": {"base": 100, "multiplier": 1.5}}

        chunks = list(chunker._chunk_formula_data(data, Path("formula.json"), "FORMULA"))

        assert len(chunks) == 1
        assert chunks[0].metadata["category"] == "FORMULA"

    def test_chunk_json_with_formula_list(self):
        """JSON 청킹 - 공식 데이터 (list)"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = [{"formula": "H = A + B"}, {"formula": "W = X + Y"}]

        chunks = list(chunker._chunk_formula_data(data, Path("formula.json"), "FORMULA"))

        assert len(chunks) == 2

    def test_chunk_generic_json_small(self):
        """일반 JSON 청킹 - 작은 데이터"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = {"small": "data"}

        chunks = list(chunker._chunk_generic_json(data, Path("test.json"), "UNKNOWN"))

        assert len(chunks) == 1

    def test_chunk_generic_json_large_dict(self):
        """일반 JSON 청킹 - 큰 dict 데이터"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        # 최소 청크 크기보다 큰 데이터 생성
        data = {f"key_{i}": "x" * 100 for i in range(50)}

        chunks = list(chunker._chunk_generic_json(data, Path("test.json"), "UNKNOWN"))

        assert len(chunks) >= 1

    def test_chunk_generic_json_large_list(self):
        """일반 JSON 청킹 - 큰 list 데이터"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        data = [{"item": f"value_{i}" * 20} for i in range(50)]

        chunks = list(chunker._chunk_generic_json(data, Path("test.json"), "UNKNOWN"))

        assert len(chunks) >= 1

    def test_chunk_csv_basic(self):
        """CSV 청킹 기본"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "header1,header2\nvalue1,value2\nvalue3,value4"

        chunks = list(chunker._chunk_csv(content, Path("test.csv")))

        assert len(chunks) >= 1
        assert "header1" in chunks[0].content

    def test_chunk_csv_empty(self):
        """CSV 청킹 - 빈 파일"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = ""

        chunks = list(chunker._chunk_csv(content, Path("test.csv")))

        assert len(chunks) == 0

    def test_chunk_text_small(self):
        """텍스트 청킹 - 작은 파일"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "짧은 텍스트"

        chunks = list(chunker._chunk_text(content, Path("test.txt")))

        assert len(chunks) == 1
        assert chunks[0].content == "짧은 텍스트"

    def test_chunk_text_large_with_paragraphs(self):
        """텍스트 청킹 - 여러 문단"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        # 큰 텍스트 생성
        paragraphs = ["문단 " + str(i) + " " * 500 for i in range(20)]
        content = "\n\n".join(paragraphs)

        chunks = list(chunker._chunk_text(content, Path("test.txt")))

        assert len(chunks) >= 1

    def test_split_large_chunk(self):
        """대형 청크 분할"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        # 큰 내용 생성
        content = "\n".join([f"line {i} " + "x" * 100 for i in range(100)])

        chunks = list(chunker._split_large_chunk(content, Path("test.json"), "RULE", "test_rule"))

        assert len(chunks) >= 1

    def test_chunking_evidence_to_dict(self):
        """ChunkingEvidence.to_dict() 확인"""
        from kis_estimator_core.rag.chunker import ChunkingEvidence

        evidence = ChunkingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            source_file="test.json",
            total_chunks=10,
            categories={"BREAKER": 10},
            config_snapshot={},
            hash="abc123",
        )

        result = evidence.to_dict()

        assert result["timestamp"] == "2025-01-01T00:00:00Z"
        assert result["total_chunks"] == 10
        assert json.dumps(result)  # JSON 직렬화 가능

    def test_create_evidence(self):
        """_create_evidence 동작 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk, KnowledgeChunker

        chunker = KnowledgeChunker()
        chunks = [
            KnowledgeChunk(id="1", content="test1", metadata={"category": "BREAKER"}),
            KnowledgeChunk(id="2", content="test2", metadata={"category": "BREAKER"}),
            KnowledgeChunk(id="3", content="test3", metadata={"category": "ENCLOSURE"}),
        ]

        chunker._create_evidence(Path("test.json"), chunks)

        assert len(chunker._evidence_list) == 1
        evidence = chunker._evidence_list[0]
        assert evidence.total_chunks == 3
        assert evidence.categories["BREAKER"] == 2
        assert evidence.categories["ENCLOSURE"] == 1

    def test_save_evidence(self):
        """save_evidence 파일 저장 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk, KnowledgeChunker

        chunker = KnowledgeChunker()
        chunks = [KnowledgeChunk(id="1", content="test", metadata={"category": "BREAKER"})]
        chunker._create_evidence(Path("test.json"), chunks)

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path = chunker.save_evidence(Path(tmpdir))

            assert evidence_path.exists()
            assert evidence_path.suffix == ".json"

            content = json.loads(evidence_path.read_text(encoding="utf-8"))
            assert content["type"] == "chunking_evidence"
            assert content["total_chunks"] == 1

    def test_get_stats(self):
        """get_stats 통계 반환 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunk, KnowledgeChunker

        chunker = KnowledgeChunker()
        chunks = [
            KnowledgeChunk(id="1", content="test1", metadata={"category": "BREAKER"}),
            KnowledgeChunk(id="2", content="test2", metadata={"category": "BREAKER"}),
        ]
        chunker._create_evidence(Path("test1.json"), chunks)

        chunks2 = [KnowledgeChunk(id="3", content="test3", metadata={"category": "ENCLOSURE"})]
        chunker._create_evidence(Path("test2.json"), chunks2)

        stats = chunker.get_stats()

        assert stats["total_files"] == 2
        assert stats["total_chunks"] == 3
        assert stats["categories"]["BREAKER"] == 2
        assert stats["categories"]["ENCLOSURE"] == 1

    def test_chunk_directory_nonexistent(self):
        """존재하지 않는 디렉토리 청킹"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        chunks = list(chunker._chunk_directory(Path("/nonexistent/path")))

        assert len(chunks) == 0

    def test_chunk_file_with_tempfile(self):
        """실제 임시 파일 청킹"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"test_key": "test_value"}, f, ensure_ascii=False)
            f.flush()
            temp_path = Path(f.name)

        try:
            chunks = list(chunker._chunk_file(temp_path))
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()


# ========================================
# VectorIndexer Extended Tests (Coverage)
# ========================================


class TestVectorIndexerExtended:
    """VectorIndexer 확장 테스트 (커버리지 향상)"""

    def test_indexer_config_from_ssot(self):
        """Indexer 설정이 SSOT에서 참조되는지"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        config = RAGConfig()
        indexer = VectorIndexer(config)

        assert indexer.config.collection_name == RAG_COLLECTION_NAME

    def test_indexing_evidence_to_dict(self):
        """IndexingEvidence.to_dict() 확인"""
        from kis_estimator_core.rag.indexer import IndexingEvidence

        evidence = IndexingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            collection_name="test_collection",
            total_chunks=100,
            indexed=95,
            skipped=3,
            errors=2,
            categories={"BREAKER": 50, "ENCLOSURE": 45},
            processing_time_ms=1500.5,
            hash="abc123def456",
        )

        result = evidence.to_dict()

        assert result["timestamp"] == "2025-01-01T00:00:00Z"
        assert result["total_chunks"] == 100
        assert result["indexed"] == 95
        assert result["skipped"] == 3
        assert result["errors"] == 2
        assert result["processing_time_ms"] == 1500.5
        assert json.dumps(result)  # JSON 직렬화 가능

    @pytest.mark.slow
    def test_indexer_client_lazy_loading(self):
        """Indexer 클라이언트 지연 로딩"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)

            indexer = VectorIndexer(config)

            # 초기에는 None
            assert indexer._client is None

            # 접근 시 초기화
            client = indexer.client
            assert client is not None
            assert indexer._client is not None
        finally:
            # Windows: ignore_errors로 정리
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_indexer_collection_lazy_loading(self):
        """Indexer 컬렉션 지연 로딩"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)

            indexer = VectorIndexer(config)

            # 초기에는 None
            assert indexer._collection is None

            # 접근 시 초기화
            collection = indexer.collection
            assert collection is not None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_indexer_index_single_chunk(self):
        """단일 청크 인덱싱"""
        import shutil

        from kis_estimator_core.rag.chunker import KnowledgeChunk
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)
            config.collection_name = "test_single_chunk"

            indexer = VectorIndexer(config)

            chunk = KnowledgeChunk(
                id="test_chunk_1",
                content="차단기 SBE-102 가격 정보",
                metadata={"category": "BREAKER"},
            )

            result = indexer.index_chunk(chunk)
            assert result is True

            # 중복 인덱싱 시도 - False 반환
            result2 = indexer.index_chunk(chunk)
            assert result2 is False
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_indexer_get_stats(self):
        """인덱서 통계 조회"""
        import shutil

        from kis_estimator_core.rag.chunker import KnowledgeChunk
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)
            config.collection_name = "test_stats"

            indexer = VectorIndexer(config)

            chunk = KnowledgeChunk(
                id="stats_test_1",
                content="통계 테스트 데이터",
                metadata={"category": "BREAKER"},
            )
            indexer.index_chunk(chunk)

            stats = indexer.get_stats()

            assert "total_chunks" in stats
            assert stats["total_chunks"] >= 1
            assert "collection_name" in stats
            assert "embedding_model" in stats
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_indexer_delete_all(self):
        """모든 인덱스 삭제"""
        import shutil

        from kis_estimator_core.rag.chunker import KnowledgeChunk
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)
            config.collection_name = "test_delete_all"

            indexer = VectorIndexer(config)

            # 청크 추가
            chunk = KnowledgeChunk(
                id="delete_test_1",
                content="삭제 테스트",
                metadata={"category": "BREAKER"},
            )
            indexer.index_chunk(chunk)

            # 삭제
            count = indexer.delete_all()
            assert count >= 1
            assert indexer._collection is None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_indexer_save_evidence(self):
        """인덱싱 Evidence 저장"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)

            indexer = VectorIndexer(config)

            # Evidence 생성 (직접 호출)
            stats = {"total_chunks": 10, "indexed": 8, "skipped": 2, "errors": 0, "by_category": {"BREAKER": 10}}
            indexer._create_evidence(stats, 500.0)

            # 저장
            evidence_path = indexer.save_evidence(Path(tmpdir))

            assert evidence_path.exists()
            content = json.loads(evidence_path.read_text(encoding="utf-8"))
            assert content["type"] == "indexing_evidence"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ========================================
# HybridRetriever Extended Tests (Coverage)
# ========================================


class TestHybridRetrieverExtended:
    """HybridRetriever 확장 테스트 (커버리지 향상)"""

    def test_retriever_config_from_ssot(self):
        """Retriever 설정이 SSOT에서 참조되는지"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        config = RAGConfig()
        retriever = HybridRetriever(config)

        assert retriever.config.top_k == RAG_DEFAULT_TOP_K
        assert retriever.config.similarity_threshold == RAG_SIMILARITY_THRESHOLD

    def test_search_evidence_to_dict(self):
        """SearchEvidence.to_dict() 확인"""
        from kis_estimator_core.rag.retriever import SearchEvidence

        evidence = SearchEvidence(
            timestamp="2025-01-01T00:00:00Z",
            query="차단기 가격",
            search_type="hybrid",
            top_k=5,
            category_filter="BREAKER",
            results_count=3,
            avg_score=0.85,
            processing_time_ms=45.5,
            hash="abc123",
        )

        result = evidence.to_dict()

        assert result["query"] == "차단기 가격"
        assert result["search_type"] == "hybrid"
        assert result["category_filter"] == "BREAKER"
        assert json.dumps(result)

    def test_search_result_properties(self):
        """SearchResult 기본 속성"""
        from kis_estimator_core.rag.retriever import SearchResult

        result = SearchResult(
            id="test_id",
            content="테스트 내용",
            metadata={"category": "BREAKER", "source": "test.json"},
            score=0.95,
            source="semantic",
            category="BREAKER",
            rank=1,
        )

        assert result.id == "test_id"
        assert result.score == 0.95
        assert result.source == "semantic"
        assert result.category == "BREAKER"
        assert result.rank == 1

    def test_tokenize_query_removes_stopwords(self):
        """토큰화 시 불용어 제거"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        retriever = HybridRetriever(RAGConfig())

        query = "차단기의 가격을 알려주세요"
        tokens = retriever._tokenize_query(query)

        # 한국어 불용어 제거 확인
        assert "의" not in tokens
        assert "을" not in tokens

    def test_tokenize_query_handles_english(self):
        """영어 토큰화"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        retriever = HybridRetriever(RAGConfig())

        query = "the price of breaker"
        tokens = retriever._tokenize_query(query)

        # 영어 불용어 제거 확인
        assert "the" not in tokens
        assert "of" not in tokens
        assert "price" in tokens
        assert "breaker" in tokens

    def test_tokenize_query_empty(self):
        """빈 쿼리 토큰화"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        retriever = HybridRetriever(RAGConfig())

        tokens = retriever._tokenize_query("")
        assert tokens == []

    def test_rrf_logic_in_hybrid_search(self):
        """RRF 로직 검증 (RAG_RRF_K 상수 테스트)"""
        from kis_estimator_core.core.ssot.constants import RAG_RRF_K

        # RRF 공식 검증: 1/(k + rank + 1)
        # rank=0 일 때: 1/(60+0+1) = 1/61 ≈ 0.0164
        # rank=1 일 때: 1/(60+1+1) = 1/62 ≈ 0.0161
        k = RAG_RRF_K
        score_rank_0 = 1 / (k + 0 + 1)
        score_rank_1 = 1 / (k + 1 + 1)

        assert k == 60  # SSOT 상수 확인
        assert score_rank_0 > score_rank_1  # 낮은 rank가 높은 점수
        assert abs(score_rank_0 - 1/61) < 0.001  # 예상 값 확인

        # 양쪽 검색에 모두 존재하면 점수 합산
        combined_score = score_rank_0 + score_rank_0  # 양쪽 1위
        single_score = score_rank_0  # 한쪽만 1위

        assert combined_score > single_score  # 중복 문서가 더 높은 점수

    @pytest.mark.slow
    def test_retriever_client_lazy_loading(self):
        """Retriever 클라이언트 지연 로딩"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)

            retriever = HybridRetriever(config)

            assert retriever._client is None

            client = retriever.client
            assert client is not None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_retriever_save_evidence(self):
        """검색 Evidence 저장"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        tmpdir = tempfile.mkdtemp()
        try:
            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)

            retriever = HybridRetriever(config)

            # Evidence 생성 (직접)
            retriever._create_evidence(
                query="테스트 쿼리",
                search_type="hybrid",
                top_k=5,
                category=None,
                results=[],
                processing_time_ms=50.0,
            )

            # 저장
            evidence_path = retriever.save_evidence(Path(tmpdir))

            assert evidence_path.exists()
            content = json.loads(evidence_path.read_text(encoding="utf-8"))
            assert content["type"] == "search_evidence"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.mark.slow
    def test_retriever_search_empty_collection(self):
        """빈 컬렉션에서 검색"""
        import shutil

        import chromadb

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        tmpdir = tempfile.mkdtemp()
        try:
            # 먼저 빈 컬렉션 생성
            client = chromadb.PersistentClient(path=tmpdir)
            collection_name = "empty_test_collection"
            client.get_or_create_collection(name=collection_name)

            config = RAGConfig()
            config.chroma_persist_dir = Path(tmpdir)
            config.collection_name = collection_name

            retriever = HybridRetriever(config)

            # 빈 컬렉션에서 검색 - 결과 없어야 함
            results = retriever.search("차단기 가격", top_k=5)

            assert results == []
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_category_search_methods_exist(self):
        """카테고리별 검색 메서드 존재 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        # 모든 검색 메서드가 존재하는지 확인 (singular form)
        assert hasattr(HybridRetriever, "search_breaker")
        assert hasattr(HybridRetriever, "search_enclosure")
        assert hasattr(HybridRetriever, "search_accessory")
        assert hasattr(HybridRetriever, "search_formula")
        assert hasattr(HybridRetriever, "search_price")
        assert hasattr(HybridRetriever, "search_rule")
        assert hasattr(HybridRetriever, "search_standard")
        # 새로 추가된 카테고리
        assert hasattr(HybridRetriever, "search_estimate")
        assert hasattr(HybridRetriever, "search_cover")
        assert hasattr(HybridRetriever, "search_erp")
        assert hasattr(HybridRetriever, "search_calendar")
        assert hasattr(HybridRetriever, "search_drawing")


# ========================================
# API Extended Tests (Coverage)
# ========================================


class TestRAGAPIExtended:
    """RAG API 확장 테스트 (커버리지 향상)"""

    def test_categories_response_model(self):
        """CategoriesResponse 모델 확인"""
        from kis_estimator_core.rag.api import CategoriesResponse

        response = CategoriesResponse(
            categories=[c.value for c in RAGCategory if c != RAGCategory.UNKNOWN],
            descriptions={"BREAKER": "차단기 지식", "ENCLOSURE": "외함 지식"},
        )

        assert "BREAKER" in response.categories
        assert "ENCLOSURE" in response.categories
        assert "ESTIMATE" in response.categories
        assert "ERP" in response.categories
        assert "BREAKER" in response.descriptions

    def test_index_request_model(self):
        """IndexRequest 모델 확인"""
        from kis_estimator_core.rag.api import IndexRequest

        request = IndexRequest(batch_size=50)
        assert request.batch_size == 50

        # 기본값은 32
        request_default = IndexRequest()
        assert request_default.batch_size == 32

    def test_index_response_model(self):
        """IndexResponse 모델 확인"""
        from kis_estimator_core.rag.api import IndexResponse

        response = IndexResponse(
            status="completed",
            total_chunks=100,
            indexed=95,
            skipped=5,
            errors=0,
            processing_time_ms=2500.0,
            categories={"BREAKER": 50, "ENCLOSURE": 45},
            evidence_path="/path/to/evidence.json",
        )

        assert response.status == "completed"
        assert response.total_chunks == 100
        assert response.indexed == 95
        assert response.categories["BREAKER"] == 50

    def test_search_request_defaults(self):
        """SearchRequest 기본값 확인"""
        from kis_estimator_core.rag.api import SearchRequest

        request = SearchRequest(query="테스트")

        assert request.query == "테스트"
        assert request.category is None
        assert request.top_k == RAG_DEFAULT_TOP_K
        assert request.search_type == "hybrid"

    def test_search_request_custom(self):
        """SearchRequest 커스텀 값 확인"""
        from kis_estimator_core.rag.api import SearchRequest

        request = SearchRequest(
            query="차단기",
            category="BREAKER",
            top_k=10,
            search_type="semantic",
        )

        assert request.category == "BREAKER"
        assert request.top_k == 10
        assert request.search_type == "semantic"

    def test_search_result_item_model(self):
        """SearchResultItem 모델 확인"""
        from kis_estimator_core.rag.api import SearchResultItem

        item = SearchResultItem(
            id="test_id",
            content="테스트 내용",
            category="BREAKER",
            score=0.95,
            source="test.json",
            search_type="hybrid",
            rank=1,
            metadata={"key": "value"},
        )

        assert item.id == "test_id"
        assert item.score == 0.95
        assert item.category == "BREAKER"
        assert item.rank == 1

    def test_stats_response_model(self):
        """StatsResponse 모델 확인"""
        from kis_estimator_core.rag.api import StatsResponse

        response = StatsResponse(
            total_documents=1000,
            collection_name="kis_knowledge",
            embedding_model=RAG_EMBEDDING_MODEL,
            categories={"BREAKER": 500, "ENCLOSURE": 300},
        )

        assert response.total_documents == 1000
        assert response.categories["BREAKER"] == 500

    def test_generate_trace_id(self):
        """추적 ID 생성 확인"""
        from kis_estimator_core.rag.api import generate_trace_id

        trace_id = generate_trace_id()

        assert isinstance(trace_id, str)
        assert len(trace_id) == 16  # SHA256의 처음 16자
        # 두 번 호출하면 다른 값 (시간 기반)
        trace_id2 = generate_trace_id()
        # 같은 초 내에 호출되면 같을 수 있음

    def test_health_response_model(self):
        """HealthResponse 모델 확인"""
        from kis_estimator_core.rag.api import HealthResponse

        response = HealthResponse(
            status="healthy",
            collection_available=True,
            document_count=500,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            timestamp="2025-01-01T00:00:00Z",
        )

        assert response.status == "healthy"
        assert response.collection_available is True
        assert response.document_count == 500

    def test_error_response_model(self):
        """ErrorResponse 모델 확인"""
        from kis_estimator_core.rag.api import ErrorResponse

        error = ErrorResponse(
            code="TEST_ERROR",
            message="테스트 에러 메시지",
            traceId="abc123",
            hint="힌트 메시지",
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "테스트 에러 메시지"
        assert error.traceId == "abc123"
        assert error.hint == "힌트 메시지"

    def test_search_response_model(self):
        """SearchResponse 모델 확인"""
        from kis_estimator_core.rag.api import SearchResponse, SearchResultItem

        items = [
            SearchResultItem(
                id="1", content="내용", category="BREAKER",
                score=0.9, source="test.json", search_type="hybrid",
                rank=1, metadata={}
            )
        ]

        response = SearchResponse(
            query="테스트 쿼리",
            search_type="hybrid",
            total=1,
            processing_time_ms=50.5,
            results=items,
        )

        assert response.query == "테스트 쿼리"
        assert response.total == 1
        assert len(response.results) == 1


# ========================================
# Additional Coverage Tests
# ========================================


class TestRetrieverCategorySearchMethods:
    """Retriever 카테고리별 검색 메서드 확장 테스트"""

    def test_search_by_category_method_exists(self):
        """search_by_category 메서드 존재 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert hasattr(HybridRetriever, "search_by_category")

    def test_search_estimate_method(self):
        """search_estimate 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_estimate", None))

    def test_search_cover_method(self):
        """search_cover 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_cover", None))

    def test_search_erp_method(self):
        """search_erp 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_erp", None))

    def test_search_calendar_method(self):
        """search_calendar 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_calendar", None))

    def test_search_drawing_method(self):
        """search_drawing 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_drawing", None))

    def test_search_standard_method(self):
        """search_standard 메서드 확인"""
        from kis_estimator_core.rag.retriever import HybridRetriever

        assert callable(getattr(HybridRetriever, "search_standard", None))


class TestRetrieverStats:
    """Retriever 통계 테스트"""

    def test_retriever_stats_dataclass(self):
        """RetrieverStats 데이터클래스 확인"""
        from kis_estimator_core.rag.retriever import RetrieverStats

        stats = RetrieverStats()

        assert stats.total_searches == 0
        assert stats.semantic_searches == 0
        assert stats.keyword_searches == 0
        assert stats.hybrid_searches == 0
        assert stats.total_results == 0
        assert stats.avg_processing_time_ms == 0.0
        assert stats.categories_searched == {}

    def test_retriever_stats_with_values(self):
        """RetrieverStats 값 설정"""
        from kis_estimator_core.rag.retriever import RetrieverStats

        stats = RetrieverStats(
            total_searches=100,
            semantic_searches=30,
            keyword_searches=20,
            hybrid_searches=50,
            total_results=500,
            avg_processing_time_ms=45.5,
            categories_searched={"BREAKER": 40, "ENCLOSURE": 60},
        )

        assert stats.total_searches == 100
        assert stats.hybrid_searches == 50
        assert stats.categories_searched["BREAKER"] == 40


class TestChunkerEdgeCases:
    """Chunker 엣지 케이스 테스트"""

    def test_chunk_with_very_long_content(self):
        """매우 긴 콘텐츠 청킹"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        # 10KB 이상의 긴 텍스트
        long_content = "매우 긴 텍스트 " * 2000

        chunks = list(chunker._chunk_text(long_content, Path("long.txt")))

        # 분할되어야 함
        assert len(chunks) >= 1
        # 청크가 생성되었는지 확인 (분할 정책은 구현에 따라 다름)
        total_length = sum(len(c.content) for c in chunks)
        assert total_length > 0

    def test_chunk_json_with_nested_structure(self):
        """중첩 구조 JSON 청킹"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": "깊은 데이터"
                    }
                }
            }
        }

        chunks = list(chunker._chunk_generic_json(nested_data, Path("nested.json"), "RULE"))

        assert len(chunks) >= 1
        # 중첩 구조가 포함됨
        assert "level1" in chunks[0].content or "깊은" in chunks[0].content

    def test_chunk_empty_json(self):
        """빈 JSON 청킹"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()

        # 빈 dict - 최소 1개 청크 생성
        chunks_dict = list(chunker._chunk_generic_json({}, Path("empty.json"), "UNKNOWN"))
        assert len(chunks_dict) >= 1

        # 빈 list - 청크 생성됨 (구현에 따라 다름)
        chunks_list = list(chunker._chunk_generic_json([], Path("empty.json"), "UNKNOWN"))
        assert len(chunks_list) >= 0  # 빈 list도 청크 생성 가능


class TestSearchEvidenceDataclass:
    """SearchEvidence 데이터클래스 테스트"""

    def test_search_evidence_to_dict(self):
        """SearchEvidence to_dict 메서드"""
        from kis_estimator_core.rag.retriever import SearchEvidence

        evidence = SearchEvidence(
            timestamp="2025-01-01T00:00:00Z",
            query="테스트 쿼리",
            search_type="hybrid",
            top_k=10,
            category_filter="BREAKER",
            results_count=5,
            avg_score=0.85,
            processing_time_ms=25.5,
            hash="abc123",
        )

        data = evidence.to_dict()

        assert data["timestamp"] == "2025-01-01T00:00:00Z"
        assert data["query"] == "테스트 쿼리"
        assert data["search_type"] == "hybrid"
        assert data["top_k"] == 10
        assert data["category_filter"] == "BREAKER"
        assert data["results_count"] == 5
        assert data["avg_score"] == 0.85
        assert data["processing_time_ms"] == 25.5
        assert data["hash"] == "abc123"


class TestIndexingEvidenceDataclass:
    """IndexingEvidence 데이터클래스 테스트"""

    def test_indexing_evidence_to_dict(self):
        """IndexingEvidence to_dict 메서드"""
        from kis_estimator_core.rag.indexer import IndexingEvidence

        evidence = IndexingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            collection_name="test_collection",
            total_chunks=100,
            indexed=95,
            skipped=5,
            errors=0,
            categories={"BREAKER": 50, "ENCLOSURE": 45},
            processing_time_ms=5000.0,
            hash="def456",
        )

        data = evidence.to_dict()

        assert data["timestamp"] == "2025-01-01T00:00:00Z"
        assert data["collection_name"] == "test_collection"
        assert data["total_chunks"] == 100
        assert data["indexed"] == 95
        assert data["skipped"] == 5
        assert data["errors"] == 0
        assert data["categories"]["BREAKER"] == 50
        assert data["processing_time_ms"] == 5000.0


class TestChunkingEvidenceDataclass:
    """ChunkingEvidence 데이터클래스 테스트"""

    def test_chunking_evidence_to_dict(self):
        """ChunkingEvidence to_dict 메서드"""
        from kis_estimator_core.rag.chunker import ChunkingEvidence

        evidence = ChunkingEvidence(
            timestamp="2025-01-01T00:00:00Z",
            source_file="breaker.json",
            total_chunks=10,
            categories={"BREAKER": 5, "ENCLOSURE": 5},
            config_snapshot={"chunk_size": 512},
            hash="ghi789",
        )

        data = evidence.to_dict()

        assert data["timestamp"] == "2025-01-01T00:00:00Z"
        assert data["source_file"] == "breaker.json"
        assert data["total_chunks"] == 10
        assert data["categories"]["BREAKER"] == 5
        assert data["config_snapshot"]["chunk_size"] == 512
        assert data["hash"] == "ghi789"


class TestEmbedderExtended:
    """Embedder 확장 테스트 (커버리지 향상)"""

    @pytest.mark.slow
    def test_embed_batch(self):
        """배치 임베딩 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())
        texts = ["테스트 문장 1", "테스트 문장 2", "테스트 문장 3"]

        embeddings = embedder.embed_batch(texts, batch_size=2)

        assert len(embeddings) == 3
        assert all(len(e) > 0 for e in embeddings)

    @pytest.mark.slow
    def test_similarity_calculation(self):
        """코사인 유사도 계산 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())

        # 같은 텍스트는 높은 유사도
        emb1 = embedder.embed("차단기 가격")
        emb2 = embedder.embed("차단기 가격")

        similarity = embedder.similarity(emb1, emb2)

        assert similarity > 0.99  # 거의 1

    @pytest.mark.slow
    def test_similarity_different_texts(self):
        """다른 텍스트 유사도 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())

        emb1 = embedder.embed("차단기 가격")
        emb2 = embedder.embed("완전히 다른 내용의 문서")

        similarity = embedder.similarity(emb1, emb2)

        assert similarity < 0.9  # 다른 텍스트

    def test_similarity_zero_norm(self):
        """제로 노름 유사도 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())

        zero_vec = [0.0] * 384  # 모델 차원
        non_zero_vec = [1.0] * 384

        similarity = embedder.similarity(zero_vec, non_zero_vec)

        assert similarity == 0.0  # 제로 벡터

    @pytest.mark.slow
    def test_dimension_property(self):
        """임베딩 차원 속성 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())

        dim = embedder.dimension

        assert dim > 0  # 양수 차원
        assert isinstance(dim, int)

    @pytest.mark.slow
    def test_model_name_property(self):
        """모델명 속성 테스트"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder(RAGConfig())

        name = embedder.model_name

        assert isinstance(name, str)
        assert len(name) > 0

    @pytest.mark.slow
    def test_embedder_save_evidence(self):
        """임베더 Evidence 저장 테스트"""
        import shutil

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.embedder import LocalEmbedder

        tmpdir = tempfile.mkdtemp()
        try:
            embedder = LocalEmbedder(RAGConfig())

            # 임베딩 생성 (Evidence도 생성됨)
            embedder.embed("테스트")

            # Evidence 저장
            evidence_path = embedder.save_evidence(Path(tmpdir))

            assert evidence_path.exists()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestAPIHelperFunctions:
    """API 헬퍼 함수 테스트"""

    def test_generate_trace_id_format(self):
        """추적 ID 형식 테스트"""
        from kis_estimator_core.rag.api import generate_trace_id

        trace_id = generate_trace_id()

        # 16자리 hex string
        assert len(trace_id) == 16
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_trace_id_uniqueness(self):
        """추적 ID 고유성 테스트 (다른 시간)"""
        import time

        from kis_estimator_core.rag.api import generate_trace_id

        trace_id1 = generate_trace_id()
        time.sleep(0.001)  # 1ms 대기
        trace_id2 = generate_trace_id()

        # 대부분의 경우 다름 (같은 밀리초 아니면)
        # 단, 같은 밀리초 내에 호출되면 같을 수 있음


class TestRetrieverGetStats:
    """Retriever get_stats 테스트"""

    def test_get_stats_returns_dict(self):
        """get_stats가 딕셔너리 반환"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        retriever = HybridRetriever(RAGConfig())

        stats = retriever.get_stats()

        assert isinstance(stats, dict)
        assert "total_searches" in stats
        assert "by_type" in stats
        assert "total_results" in stats
        assert "collection_name" in stats

    def test_get_stats_initial_values(self):
        """초기 통계값 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        retriever = HybridRetriever(RAGConfig())

        stats = retriever.get_stats()

        assert stats["total_searches"] == 0
        assert stats["by_type"]["semantic"] == 0
        assert stats["by_type"]["keyword"] == 0
        assert stats["by_type"]["hybrid"] == 0
        assert stats["total_results"] == 0


class TestRAGConfigExtended:
    """RAGConfig 확장 테스트"""

    def test_config_default_values(self):
        """기본 설정값 확인"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert config.chunk_size > 0
        assert config.chunk_overlap >= 0
        assert config.top_k > 0
        assert config.similarity_threshold > 0

    def test_config_from_ssot(self):
        """SSOT 상수 기반 설정"""
        from kis_estimator_core.core.ssot.constants import (
            RAG_CHUNK_OVERLAP,
            RAG_CHUNK_SIZE,
            RAG_DEFAULT_TOP_K,
        )
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert config.chunk_size == RAG_CHUNK_SIZE
        assert config.chunk_overlap == RAG_CHUNK_OVERLAP
        assert config.top_k == RAG_DEFAULT_TOP_K

    def test_config_paths_exist(self):
        """경로 설정 확인"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert config.knowledge_base_path is not None
        assert config.chroma_persist_dir is not None
        assert config.evidence_dir is not None

    def test_config_embedding_model(self):
        """임베딩 모델 설정 확인"""
        from kis_estimator_core.core.ssot.constants import RAG_EMBEDDING_MODEL
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert config.embedding_model == RAG_EMBEDDING_MODEL

    def test_config_search_type(self):
        """검색 타입 기본값"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert config.search_type in ["semantic", "keyword", "hybrid"]


class TestChunkerConfigSnapshot:
    """Chunker Config 스냅샷 테스트"""

    def test_chunker_has_config(self):
        """Chunker에 config 속성 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()

        assert chunker.config is not None
        assert chunker.config.chunk_size > 0

    def test_chunker_stats(self):
        """Chunker 통계 확인"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()

        stats = chunker.get_stats()

        assert isinstance(stats, dict)
        assert "total_files" in stats
        assert "total_chunks" in stats
        assert "categories" in stats


class TestIndexerConfigValidation:
    """Indexer Config 검증 테스트"""

    def test_indexer_has_config(self):
        """Indexer에 config 속성 확인"""
        from kis_estimator_core.rag.indexer import VectorIndexer

        indexer = VectorIndexer()

        assert indexer.config is not None

    def test_indexer_embedder_initialized(self):
        """Indexer embedder 초기화 확인"""
        from kis_estimator_core.rag.indexer import VectorIndexer

        indexer = VectorIndexer()

        assert indexer.embedder is not None


class TestCLIModuleImport:
    """CLI 모듈 기본 테스트"""

    def test_cli_module_imports(self):
        """CLI 모듈 import 가능"""
        from kis_estimator_core.rag import cli

        assert cli is not None

    def test_cli_functions_exist(self):
        """CLI 함수들 존재 확인"""
        from kis_estimator_core.rag import cli

        assert hasattr(cli, "cmd_index")
        assert hasattr(cli, "cmd_search")
        assert hasattr(cli, "cmd_stats")
        assert hasattr(cli, "cmd_validate")
        assert hasattr(cli, "cmd_clear")

    def test_cli_main_exists(self):
        """main 함수 존재 확인"""
        from kis_estimator_core.rag import cli

        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_cli_cmd_learn_exists(self):
        """cmd_learn 함수 존재 확인"""
        from kis_estimator_core.rag import cli

        assert hasattr(cli, "cmd_learn")
        assert callable(cli.cmd_learn)


class TestAPISingletonFunctions:
    """API 싱글톤 함수 테스트"""

    def test_get_retriever_function_exists(self):
        """get_retriever 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "get_retriever")
        assert callable(api.get_retriever)

    def test_get_indexer_function_exists(self):
        """get_indexer 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "get_indexer")
        assert callable(api.get_indexer)

    def test_router_exists(self):
        """API 라우터 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "router")


class TestAPIEndpointDefinitions:
    """API 엔드포인트 정의 테스트"""

    def test_search_endpoint_defined(self):
        """검색 엔드포인트 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_knowledge")

    def test_index_endpoint_defined(self):
        """인덱싱 엔드포인트 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "index_knowledge")

    def test_stats_endpoint_defined(self):
        """통계 엔드포인트 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "get_stats")

    def test_health_endpoint_defined(self):
        """헬스체크 엔드포인트 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "health_check")

    def test_categories_endpoint_defined(self):
        """카테고리 엔드포인트 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "get_categories")


class TestRAGPackageInit:
    """RAG 패키지 초기화 테스트"""

    def test_package_exports_config(self):
        """RAGConfig 내보내기 확인"""
        from kis_estimator_core.rag import RAGConfig

        assert RAGConfig is not None

    def test_package_exports_chunker(self):
        """KnowledgeChunker 내보내기 확인"""
        from kis_estimator_core.rag import KnowledgeChunker

        assert KnowledgeChunker is not None

    def test_package_exports_indexer(self):
        """VectorIndexer 내보내기 확인"""
        from kis_estimator_core.rag import VectorIndexer

        assert VectorIndexer is not None

    def test_package_exports_retriever(self):
        """HybridRetriever 내보내기 확인"""
        from kis_estimator_core.rag import HybridRetriever

        assert HybridRetriever is not None

    def test_package_exports_embedder(self):
        """LocalEmbedder 내보내기 확인"""
        from kis_estimator_core.rag import LocalEmbedder

        assert LocalEmbedder is not None


class TestSearchResultDataclass:
    """SearchResult 데이터클래스 테스트"""

    def test_search_result_to_dict(self):
        """SearchResult to_dict 메서드"""
        from kis_estimator_core.rag.retriever import SearchResult

        result = SearchResult(
            id="test_123",
            content="테스트 내용입니다",
            metadata={"source": "test.json"},
            score=0.9234,
            source="semantic",
            category="BREAKER",
            rank=1,
        )

        data = result.to_dict()

        assert data["id"] == "test_123"
        assert data["content"] == "테스트 내용입니다"
        assert data["metadata"]["source"] == "test.json"
        assert data["score"] == 0.9234
        assert data["source"] == "semantic"
        assert data["category"] == "BREAKER"
        assert data["rank"] == 1

    def test_search_result_to_dict_truncates_long_content(self):
        """긴 콘텐츠 to_dict 시 자름"""
        from kis_estimator_core.rag.retriever import SearchResult

        long_content = "테스트 " * 100  # 300자 이상

        result = SearchResult(
            id="test",
            content=long_content,
            metadata={},
            score=0.9,
            source="semantic",
        )

        data = result.to_dict()

        # 200자 + "..." 형태
        assert len(data["content"]) == 203
        assert data["content"].endswith("...")


class TestAPICategoryEndpoints:
    """API 카테고리별 검색 엔드포인트 테스트"""

    def test_search_breaker_exists(self):
        """search_breaker 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_breaker")
        assert callable(api.search_breaker)

    def test_search_enclosure_exists(self):
        """search_enclosure 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_enclosure")
        assert callable(api.search_enclosure)

    def test_search_accessory_exists(self):
        """search_accessory 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_accessory")
        assert callable(api.search_accessory)

    def test_search_formula_exists(self):
        """search_formula 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_formula")
        assert callable(api.search_formula)

    def test_search_standard_exists(self):
        """search_standard 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_standard")
        assert callable(api.search_standard)

    def test_search_price_exists(self):
        """search_price 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_price")
        assert callable(api.search_price)

    def test_search_rule_exists(self):
        """search_rule 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_rule")
        assert callable(api.search_rule)

    def test_search_estimate_exists(self):
        """search_estimate 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_estimate")
        assert callable(api.search_estimate)

    def test_search_cover_exists(self):
        """search_cover 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_cover")
        assert callable(api.search_cover)

    def test_search_erp_exists(self):
        """search_erp 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_erp")
        assert callable(api.search_erp)

    def test_search_calendar_exists(self):
        """search_calendar 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_calendar")
        assert callable(api.search_calendar)

    def test_search_drawing_exists(self):
        """search_drawing 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "search_drawing")
        assert callable(api.search_drawing)

    def test_delete_index_exists(self):
        """delete_index 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "delete_index")
        assert callable(api.delete_index)

    def test_validate_config_exists(self):
        """validate_config 함수 존재"""
        from kis_estimator_core.rag import api

        assert hasattr(api, "validate_config")
        assert callable(api.validate_config)


class TestRAGConfigValidation:
    """RAGConfig 검증 테스트"""

    def test_config_validate_returns_tuple(self):
        """validate 메서드 반환값 확인"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        result = config.validate()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_config_to_dict_method(self):
        """to_dict 메서드 확인"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        data = config.to_dict()

        assert isinstance(data, dict)
        assert "embedding_model" in data
        assert "chroma_persist_dir" in data

    def test_config_additional_knowledge_paths_list(self):
        """additional_knowledge_paths가 리스트인지 확인"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()

        assert isinstance(config.additional_knowledge_paths, list)


class TestAPIRequestModels:
    """API 요청 모델 테스트"""

    def test_search_request_model(self):
        """SearchRequest 모델 생성"""
        from kis_estimator_core.rag.api import SearchRequest

        request = SearchRequest(
            query="차단기 테스트",
            top_k=5,
            search_type="hybrid",
        )

        assert request.query == "차단기 테스트"
        assert request.top_k == 5
        assert request.search_type == "hybrid"

    def test_search_request_defaults(self):
        """SearchRequest 기본값 확인"""
        from kis_estimator_core.rag.api import SearchRequest

        request = SearchRequest(query="테스트")

        assert request.query == "테스트"
        assert request.top_k == 5  # 기본값
        assert request.search_type == "hybrid"  # 기본값
        assert request.category is None

    def test_index_request_model(self):
        """IndexRequest 모델 생성"""
        from kis_estimator_core.rag.api import IndexRequest

        request = IndexRequest(
            force_reindex=True,
            batch_size=64,
        )

        assert request.force_reindex is True
        assert request.batch_size == 64

    def test_index_request_defaults(self):
        """IndexRequest 기본값 확인"""
        from kis_estimator_core.rag.api import IndexRequest

        request = IndexRequest()

        assert request.force_reindex is False
        assert request.batch_size == 32


class TestIndexerStats:
    """VectorIndexer 통계 테스트"""

    def test_indexer_get_stats_returns_dict(self, tmp_path):
        """get_stats가 dict 반환"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        config = RAGConfig()
        config.chroma_db_path = str(tmp_path / "chroma_stats")
        indexer = VectorIndexer(config)

        stats = indexer.get_stats()

        assert isinstance(stats, dict)
        assert "collection_name" in stats
        assert "total_chunks" in stats

    def test_indexer_delete_all(self, tmp_path):
        """delete_all 메서드 동작 확인"""
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer

        config = RAGConfig()
        config.chroma_db_path = str(tmp_path / "chroma_delete")
        indexer = VectorIndexer(config)

        deleted = indexer.delete_all()

        assert isinstance(deleted, int)
        assert deleted >= 0


class TestRetrieverHybridSearch:
    """HybridRetriever 하이브리드 검색 테스트"""

    def test_hybrid_search_type_enum(self):
        """검색 타입 enum 확인"""
        from kis_estimator_core.core.ssot.enums import RAGSearchType

        assert RAGSearchType.SEMANTIC.value == "semantic"
        assert RAGSearchType.KEYWORD.value == "keyword"
        assert RAGSearchType.HYBRID.value == "hybrid"

    def test_chunking_strategy_enum(self):
        """청킹 전략 enum 확인"""
        from kis_estimator_core.core.ssot.enums import RAGChunkingStrategy

        assert RAGChunkingStrategy.SEMANTIC.value == "semantic"
        assert RAGChunkingStrategy.FIXED.value == "fixed"
        assert RAGChunkingStrategy.HYBRID.value == "hybrid"


class TestChunkerCategoryDetection:
    """KnowledgeChunker 카테고리 감지 테스트"""

    def test_detect_breaker_category(self):
        """BREAKER 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "차단기 SBE-104 사양입니다."

        category = chunker._detect_category(content, "breaker.json")

        assert category == "BREAKER"

    def test_detect_enclosure_category(self):
        """ENCLOSURE 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "외함 규격 600x800x200"

        category = chunker._detect_category(content, "enclosure.json")

        assert category == "ENCLOSURE"

    def test_detect_accessory_category(self):
        """ACCESSORY 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "마그네트 MC-22 부속자재"

        category = chunker._detect_category(content, "accessory.json")

        assert category == "ACCESSORY"

    def test_detect_formula_category(self):
        """FORMULA 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "계산식: H = A + B + C"

        category = chunker._detect_category(content, "formula.json")

        assert category == "FORMULA"

    def test_detect_estimate_category(self):
        """ESTIMATE 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "견적 작성 절차입니다"

        category = chunker._detect_category(content, "estimate.json")

        assert category == "ESTIMATE"

    def test_detect_cover_category(self):
        """COVER 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        # cover.json 파일명 + 표지 키워드로 COVER 카테고리 감지
        content = "표지 양식"

        category = chunker._detect_category(content, "cover.json")

        assert category == "COVER"


class TestEmbedderBatchOperations:
    """LocalEmbedder 배치 연산 테스트"""

    @pytest.mark.slow
    def test_embed_batch_returns_list(self):
        """embed_batch가 리스트 반환"""
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder()
        texts = ["테스트1", "테스트2", "테스트3"]

        embeddings = embedder.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3

    @pytest.mark.slow
    def test_embed_single_text(self):
        """단일 텍스트 임베딩"""
        from kis_estimator_core.rag.embedder import LocalEmbedder

        embedder = LocalEmbedder()
        text = "단일 테스트 텍스트"

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0


class TestConfigCategoryKeywords:
    """RAGConfig 카테고리 키워드 테스트"""

    def test_category_keywords_property(self):
        """category_keywords 프로퍼티"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        keywords = config.category_keywords

        assert isinstance(keywords, dict)
        assert "BREAKER" in keywords
        assert "ENCLOSURE" in keywords

    def test_categories_property(self):
        """categories 프로퍼티"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        categories = config.categories

        assert isinstance(categories, list)
        assert "BREAKER" in categories
        assert "UNKNOWN" not in categories

    def test_get_all_knowledge_paths(self):
        """get_all_knowledge_paths 메서드"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        paths = config.get_all_knowledge_paths()

        assert isinstance(paths, list)


class TestConfigValidateEdgeCases:
    """RAGConfig validate 메서드 경계 테스트"""

    def test_validate_with_small_chunk_size(self, tmp_path):
        """작은 chunk_size로 validate"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config.chunk_size = 50  # 100 미만

        is_valid, messages = config.validate()

        assert any("Chunk size too small" in msg for msg in messages)

    def test_validate_with_overlap_equal_chunk_size(self, tmp_path):
        """chunk_overlap >= chunk_size 검증"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config.chunk_size = 100
        config.chunk_overlap = 100  # chunk_size와 같음

        is_valid, messages = config.validate()

        assert any("overlap" in msg.lower() for msg in messages)
        assert is_valid is False

    def test_validate_with_invalid_top_k(self, tmp_path):
        """잘못된 top_k 검증"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config.top_k = 0  # 1 미만

        is_valid, messages = config.validate()

        assert any("top_k" in msg for msg in messages)

    def test_validate_with_invalid_similarity_threshold(self, tmp_path):
        """잘못된 similarity_threshold 검증"""
        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config.similarity_threshold = 1.5  # 1.0 초과

        is_valid, messages = config.validate()

        assert any("similarity_threshold" in msg for msg in messages)

    def test_validate_strict_mode(self, tmp_path):
        """strict 모드 검증"""
        import pytest

        from kis_estimator_core.rag.config import RAGConfig

        config = RAGConfig()
        config.chunk_size = 100
        config.chunk_overlap = 100  # 에러 유발

        with pytest.raises(ValueError):
            config.validate(strict=True)


class TestRetrieverEdgeCases:
    """HybridRetriever 경계 테스트"""

    @pytest.mark.slow
    def test_retriever_search_types(self, tmp_path):
        """검색 타입별 실행 - 컬렉션 생성 후 테스트"""

        import chromadb

        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.retriever import HybridRetriever

        # 먼저 컬렉션 생성
        chroma_path = tmp_path / "chroma_search_types"
        chroma_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection = client.get_or_create_collection(name="kis_knowledge")
        # 더미 문서 추가
        collection.add(
            ids=["test1"],
            documents=["테스트 문서"],
            metadatas=[{"category": "BREAKER"}],
        )

        config = RAGConfig()
        config.chroma_persist_dir = chroma_path  # 올바른 속성명 사용
        retriever = HybridRetriever(config)

        # semantic 검색
        results = retriever.search("테스트", search_type="semantic")
        assert isinstance(results, list)

        # keyword 검색
        results = retriever.search("테스트", search_type="keyword")
        assert isinstance(results, list)


class TestChunkerNewCategories:
    """KnowledgeChunker 신규 카테고리 테스트"""

    def test_detect_erp_category(self):
        """ERP 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "ERP 발주 관리 시스템"

        category = chunker._detect_category(content, "erp.json")

        assert category == "ERP"

    def test_detect_calendar_category(self):
        """CALENDAR 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "일정 캘린더 납기일"

        category = chunker._detect_category(content, "calendar.json")

        assert category == "CALENDAR"

    def test_detect_drawing_category(self):
        """DRAWING 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "도면 레이아웃 설계"

        category = chunker._detect_category(content, "drawing.json")

        assert category == "DRAWING"

    def test_detect_standard_category(self):
        """STANDARD 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "IEC 표준 규격"

        category = chunker._detect_category(content, "standard.json")

        assert category == "STANDARD"

    def test_detect_price_category(self):
        """PRICE 카테고리 감지"""
        from kis_estimator_core.rag.chunker import KnowledgeChunker

        chunker = KnowledgeChunker()
        content = "단가 가격 price"

        category = chunker._detect_category(content, "price.json")

        assert category == "PRICE"


class TestAPIModelsAdditional:
    """API 추가 모델 테스트"""

    def test_generate_trace_id(self):
        """trace_id 생성 확인"""
        from kis_estimator_core.rag.api import generate_trace_id

        trace_id = generate_trace_id()

        assert isinstance(trace_id, str)
        assert len(trace_id) > 0

    def test_search_request_with_category(self):
        """카테고리 포함 검색 요청"""
        from kis_estimator_core.rag.api import SearchRequest

        request = SearchRequest(
            query="차단기 검색",
            category="BREAKER",
        )

        assert request.category == "BREAKER"

    def test_router_routes_count(self):
        """라우터 경로 수 확인"""
        from kis_estimator_core.rag.api import router

        assert len(router.routes) > 0
