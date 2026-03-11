#!/usr/bin/env python
"""
RAG Knowledge Indexing Script

사용법:
    python scripts/rag_index.py --index      # 전체 인덱싱
    python scripts/rag_index.py --stats      # 통계 확인
    python scripts/rag_index.py --search "차단기 SBE-104"  # 검색 테스트
    python scripts/rag_index.py --reset      # 인덱스 초기화
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def main():
    parser = argparse.ArgumentParser(description="RAG Knowledge Indexing Tool")
    parser.add_argument("--index", action="store_true", help="전체 지식 인덱싱")
    parser.add_argument("--stats", action="store_true", help="인덱스 통계 확인")
    parser.add_argument("--search", type=str, help="검색 테스트")
    parser.add_argument("--category", type=str, help="검색 카테고리 필터")
    parser.add_argument("--reset", action="store_true", help="인덱스 초기화")
    parser.add_argument("--top-k", type=int, default=5, help="검색 결과 수")
    args = parser.parse_args()

    try:
        from kis_estimator_core.rag.config import RAGConfig
        from kis_estimator_core.rag.indexer import VectorIndexer
        from kis_estimator_core.rag.retriever import HybridRetriever
    except ImportError as e:
        print(f"[ERROR] RAG 모듈 임포트 실패: {e}")
        print("\nRAG 의존성 설치 필요:")
        print("  pip install chromadb sentence-transformers")
        return 1

    config = RAGConfig()

    if args.index:
        return do_index(config)
    elif args.stats:
        return do_stats(config)
    elif args.search:
        return do_search(config, args.search, args.category, args.top_k)
    elif args.reset:
        return do_reset(config)
    else:
        parser.print_help()
        return 0


def do_index(config):
    """전체 지식 인덱싱"""
    print("=" * 60)
    print("RAG Knowledge Indexing")
    print("=" * 60)

    # 설정 검증
    print("\n[1/3] Validating config...")
    has_knowledge, warnings = config.validate()

    for warn in warnings:
        print(f"  {warn}")

    if not has_knowledge:
        print("\n  [ERROR] Knowledge base path not found!")
        print(f"  Expected: {config.knowledge_base_path}")
        print("\n  Set environment variable KIS_KNOWLEDGE_PATH to override.")
        return 1

    print(f"  [OK] Knowledge base: {config.knowledge_base_path}")

    # 인덱싱
    print("\n[2/3] 인덱싱 시작...")
    from kis_estimator_core.rag.indexer import VectorIndexer

    indexer = VectorIndexer(config)
    stats = indexer.index_all()

    # 결과 출력
    print("\n[3/3] 인덱싱 완료")
    print(f"  총 청크: {stats['total_chunks']}")
    print(f"  인덱싱: {stats['indexed']}")
    print(f"  스킵(중복): {stats['skipped']}")
    print(f"  오류: {stats['errors']}")
    print("\n카테고리별:")
    for cat, count in stats.get("by_category", {}).items():
        print(f"  - {cat}: {count}")

    print("\n" + "=" * 60)
    print("인덱싱 완료!")
    print("=" * 60)
    return 0


def do_stats(config):
    """인덱스 통계"""
    print("=" * 60)
    print("RAG Index Statistics")
    print("=" * 60)

    from kis_estimator_core.rag.indexer import VectorIndexer

    indexer = VectorIndexer(config)
    stats = indexer.get_stats()

    print(f"\n컬렉션: {stats['collection_name']}")
    print(f"총 청크: {stats['total_chunks']}")
    print(f"임베딩 모델: {stats['embedding_model']}")
    print("\n카테고리 샘플:")
    for cat, count in stats.get("categories_sample", {}).items():
        print(f"  - {cat}: {count}")

    return 0


def do_search(config, query: str, category: str | None, top_k: int):
    """검색 테스트"""
    print("=" * 60)
    print(f"RAG Search: '{query}'")
    if category:
        print(f"Category Filter: {category}")
    print("=" * 60)

    from kis_estimator_core.rag.retriever import HybridRetriever

    retriever = HybridRetriever(config)
    results = retriever.search(query, top_k=top_k, category=category)

    if not results:
        print("\n검색 결과 없음")
        return 0

    print(f"\n{len(results)} 결과 찾음:\n")
    for i, result in enumerate(results, 1):
        print(f"[{i}] Score: {result.score:.4f} | Source: {result.source}")
        print(f"    Category: {result.metadata.get('category', 'N/A')}")
        print(f"    File: {Path(result.metadata.get('source', 'N/A')).name}")
        # 내용 미리보기 (100자)
        preview = result.content[:150].replace("\n", " ")
        print(f"    Preview: {preview}...")
        print()

    return 0


def do_reset(config):
    """인덱스 초기화"""
    print("=" * 60)
    print("RAG Index Reset")
    print("=" * 60)

    confirm = input("\n[WARNING] Delete all indexes. Continue? (y/N): ")
    if confirm.lower() != "y":
        print("취소됨")
        return 0

    from kis_estimator_core.rag.indexer import VectorIndexer

    indexer = VectorIndexer(config)
    count = indexer.delete_all()

    print(f"\n[OK] {count} chunks deleted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
