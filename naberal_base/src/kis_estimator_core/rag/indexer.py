"""
Vector Indexer - ChromaDB 기반 벡터 인덱싱

로컬 PC에서 영구 저장 지원
"""

from pathlib import Path
from typing import TYPE_CHECKING

from kis_estimator_core.rag.chunker import KnowledgeChunk, KnowledgeChunker
from kis_estimator_core.rag.config import RAGConfig
from kis_estimator_core.rag.embedder import LocalEmbedder

if TYPE_CHECKING:
    import chromadb
    from chromadb.api.models.Collection import Collection


class VectorIndexer:
    """ChromaDB 벡터 인덱서"""

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        self.embedder = LocalEmbedder(self.config)
        self._client: chromadb.ClientAPI | None = None
        self._collection: Collection | None = None

    @property
    def client(self) -> "chromadb.ClientAPI":
        """ChromaDB 클라이언트 (Lazy loading)"""
        if self._client is None:
            self._client = self._init_client()
        return self._client

    @property
    def collection(self) -> "Collection":
        """ChromaDB 컬렉션"""
        if self._collection is None:
            self._collection = self._get_or_create_collection()
        return self._collection

    def _init_client(self) -> "chromadb.ClientAPI":
        """ChromaDB 클라이언트 초기화 (신규 API)"""
        try:
            import chromadb

            # 영구 저장소 디렉토리 생성
            persist_dir = Path(self.config.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)

            print(f"[INFO] ChromaDB 초기화: {persist_dir}")

            # 신규 API: PersistentClient 사용 (자동 persist)
            client = chromadb.PersistentClient(path=str(persist_dir))

            return client

        except ImportError as e:
            raise ImportError(
                "chromadb 패키지가 필요합니다.\n"
                "설치: pip install chromadb"
            ) from e

    def _get_or_create_collection(self) -> "Collection":
        """컬렉션 가져오기 또는 생성"""
        return self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},  # 코사인 유사도
        )

    def index_all(self, batch_size: int = 100) -> dict:
        """모든 지식 인덱싱"""
        chunker = KnowledgeChunker(self.config)
        chunks = list(chunker.chunk_all())

        print(f"[INFO] 총 {len(chunks)} 청크 인덱싱 시작")

        stats = {
            "total_chunks": len(chunks),
            "indexed": 0,
            "skipped": 0,
            "errors": 0,
            "by_category": {},
        }

        # 배치 처리
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            result = self._index_batch(batch)

            stats["indexed"] += result["indexed"]
            stats["skipped"] += result["skipped"]
            stats["errors"] += result["errors"]

            # 카테고리별 통계
            for chunk in batch:
                category = chunk.metadata.get("category", "UNKNOWN")
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            print(f"[INFO] 진행: {min(i + batch_size, len(chunks))}/{len(chunks)}")

        # PersistentClient는 자동 persist - 별도 호출 불필요
        print(f"[INFO] 인덱싱 완료: {stats['indexed']} 청크")

        return stats

    def _index_batch(self, chunks: list[KnowledgeChunk]) -> dict:
        """배치 인덱싱"""
        result = {"indexed": 0, "skipped": 0, "errors": 0}

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for chunk in chunks:
            try:
                # 중복 체크
                existing = self.collection.get(ids=[chunk.id])
                if existing["ids"]:
                    result["skipped"] += 1
                    continue

                # 임베딩 생성
                embedding = self.embedder.embed_document(chunk.content)

                ids.append(chunk.id)
                documents.append(chunk.content)
                metadatas.append(chunk.metadata)
                embeddings.append(embedding)

                result["indexed"] += 1

            except Exception as e:
                print(f"[WARN] 청크 인덱싱 실패: {chunk.id} - {e}")
                result["errors"] += 1

        # 배치 추가
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )

        return result

    def index_chunk(self, chunk: KnowledgeChunk) -> bool:
        """단일 청크 인덱싱"""
        try:
            # 중복 체크
            existing = self.collection.get(ids=[chunk.id])
            if existing["ids"]:
                return False

            # 임베딩 생성 및 추가
            embedding = self.embedder.embed_document(chunk.content)
            self.collection.add(
                ids=[chunk.id],
                documents=[chunk.content],
                metadatas=[chunk.metadata],
                embeddings=[embedding],
            )

            return True

        except Exception as e:
            print(f"[ERROR] 인덱싱 실패: {e}")
            return False

    def delete_all(self) -> int:
        """모든 인덱스 삭제"""
        count = self.collection.count()
        self.client.delete_collection(self.config.collection_name)
        self._collection = None
        print(f"[INFO] {count} 청크 삭제됨")
        return count

    def get_stats(self) -> dict:
        """인덱스 통계"""
        count = self.collection.count()

        # 카테고리별 통계 (샘플링)
        sample = self.collection.get(limit=min(count, 1000), include=["metadatas"])
        categories = {}
        for meta in sample.get("metadatas", []):
            if meta:
                cat = meta.get("category", "UNKNOWN")
                categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_chunks": count,
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
            "categories_sample": categories,
        }
