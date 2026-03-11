"""
Local Embedder - sentence-transformers 기반 로컬 임베딩

GPU 없이도 동작하는 경량 모델 사용
"""

from typing import TYPE_CHECKING

import numpy as np

from kis_estimator_core.rag.config import RAGConfig

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class LocalEmbedder:
    """로컬 임베딩 처리기 (sentence-transformers)"""

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> "SentenceTransformer":
        """Lazy loading - 필요할 때만 모델 로드"""
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> "SentenceTransformer":
        """임베딩 모델 로드"""
        try:
            from sentence_transformers import SentenceTransformer

            print(f"[INFO] 임베딩 모델 로딩: {self.config.embedding_model}")
            model = SentenceTransformer(self.config.embedding_model)
            print(f"[INFO] 모델 로드 완료 (차원: {model.get_sentence_embedding_dimension()})")
            return model

        except ImportError as e:
            raise ImportError(
                "sentence-transformers 패키지가 필요합니다.\n"
                "설치: pip install sentence-transformers"
            ) from e

    def embed(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """배치 텍스트 임베딩"""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """쿼리 임베딩 (검색용)"""
        # 쿼리에 특수 프리픽스 추가 가능 (모델에 따라)
        return self.embed(query)

    def embed_document(self, document: str) -> list[float]:
        """문서 임베딩 (인덱싱용)"""
        return self.embed(document)

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """코사인 유사도 계산"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @property
    def dimension(self) -> int:
        """임베딩 차원"""
        return self.model.get_sentence_embedding_dimension()
