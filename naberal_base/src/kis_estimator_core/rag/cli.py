"""
RAG CLI - 지식 학습 및 관리 CLI

사용법:
    python -m kis_estimator_core.rag.cli index       # 지식 인덱싱
    python -m kis_estimator_core.rag.cli search      # 검색
    python -m kis_estimator_core.rag.cli stats       # 통계
    python -m kis_estimator_core.rag.cli validate    # 설정 검증
    python -m kis_estimator_core.rag.cli clear       # 인덱스 삭제

Evidence-Gated: 모든 작업은 Evidence를 생성합니다.
SSOT: 설정은 constants.py에서 참조합니다.
"""

import argparse
import json
import sys
import time

from kis_estimator_core.rag.config import RAGConfig


def cmd_index(args: argparse.Namespace) -> int:
    """지식 인덱싱"""
    from kis_estimator_core.rag.indexer import VectorIndexer

    print("=" * 60)
    print("KIS RAG 지식 인덱싱")
    print("=" * 60)

    config = RAGConfig()

    # 설정 검증
    is_valid, messages = config.validate()
    for msg in messages:
        print(msg)

    if not is_valid:
        print("\n[ERROR] 설정 검증 실패. 인덱싱을 중단합니다.")
        return 1

    print("\n" + "-" * 60)

    # 인덱서 초기화
    indexer = VectorIndexer(config)

    # 기존 인덱스 삭제 (force)
    if args.force:
        print("[INFO] 기존 인덱스 삭제 중...")
        deleted = indexer.delete_all()
        print(f"[INFO] {deleted} 청크 삭제됨")

    # 인덱싱 실행
    print(f"\n[INFO] 인덱싱 시작 (batch_size={args.batch_size})...")
    start_time = time.time()

    stats = indexer.index_all(batch_size=args.batch_size)

    elapsed = time.time() - start_time

    # 결과 출력
    print("\n" + "=" * 60)
    print("인덱싱 결과")
    print("=" * 60)
    print(f"총 청크:    {stats['total_chunks']}")
    print(f"인덱싱됨:   {stats['indexed']}")
    print(f"스킵됨:     {stats['skipped']}")
    print(f"오류:       {stats['errors']}")
    print(f"처리 시간:  {elapsed:.2f}초")

    print("\n카테고리별:")
    for cat, count in stats.get("by_category", {}).items():
        print(f"  {cat}: {count}")

    # Evidence 저장
    evidence_path = indexer.save_evidence()
    print(f"\n[Evidence] 저장됨: {evidence_path}")

    return 0 if stats["errors"] == 0 else 1


def cmd_search(args: argparse.Namespace) -> int:
    """지식 검색"""
    from kis_estimator_core.rag.retriever import HybridRetriever

    config = RAGConfig()
    retriever = HybridRetriever(config)

    print("=" * 60)
    print(f"검색: {args.query}")
    print(f"유형: {args.type} | Top-K: {args.top_k}")
    if args.category:
        print(f"카테고리: {args.category}")
    print("=" * 60 + "\n")

    try:
        results = retriever.search(
            query=args.query,
            top_k=args.top_k,
            category=args.category,
            search_type=args.type,
        )

        if not results:
            print("[INFO] 검색 결과가 없습니다.")
            return 0

        for i, r in enumerate(results, 1):
            print(f"[{i}] Score: {r.score:.4f} | Category: {r.category}")
            print(f"    ID: {r.id}")

            # 내용 출력 (최대 200자)
            content = r.content[:200] + "..." if len(r.content) > 200 else r.content
            print(f"    Content: {content}")
            print()

        # 통계
        stats = retriever.get_stats()
        print("-" * 60)
        print(f"총 검색: {stats['total_searches']} | 결과: {len(results)}")

        # Evidence 저장 (옵션)
        if args.save_evidence:
            evidence_path = retriever.save_evidence()
            print(f"[Evidence] 저장됨: {evidence_path}")

        return 0

    except FileNotFoundError:
        print("[ERROR] 인덱스가 존재하지 않습니다.")
        print("먼저 'python -m kis_estimator_core.rag.cli index'를 실행하세요.")
        return 1
    except Exception as e:
        print(f"[ERROR] 검색 실패: {e}")
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """인덱스 통계"""
    from kis_estimator_core.rag.indexer import VectorIndexer

    config = RAGConfig()

    print("=" * 60)
    print("KIS RAG 인덱스 통계")
    print("=" * 60 + "\n")

    try:
        indexer = VectorIndexer(config)
        stats = indexer.get_stats()

        print(f"컬렉션:      {stats.get('collection_name', 'N/A')}")
        print(f"총 문서:     {stats.get('total_chunks', 0)}")
        print(f"임베딩 모델: {stats.get('embedding_model', 'N/A')}")

        print("\n카테고리별 (샘플):")
        for cat, count in stats.get("categories_sample", {}).items():
            print(f"  {cat}: {count}")

        if args.json:
            print("\n" + "-" * 60)
            print(json.dumps(stats, indent=2, ensure_ascii=False))

        return 0

    except FileNotFoundError:
        print("[INFO] 인덱스가 존재하지 않습니다.")
        return 0
    except Exception as e:
        print(f"[ERROR] 통계 조회 실패: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """설정 검증"""
    print("=" * 60)
    print("KIS RAG 설정 검증")
    print("=" * 60 + "\n")

    config = RAGConfig()
    is_valid, messages = config.validate()

    for msg in messages:
        print(msg)

    print("\n" + "-" * 60)

    if args.json:
        print("\n설정 (JSON):")
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    if is_valid:
        print("[OK] 설정 검증 성공")
        return 0
    else:
        print("[FAIL] 설정 검증 실패")
        return 1


def cmd_clear(args: argparse.Namespace) -> int:
    """인덱스 삭제"""
    from kis_estimator_core.rag.indexer import VectorIndexer

    if not args.force:
        confirm = input("정말로 모든 인덱스를 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            print("취소되었습니다.")
            return 0

    config = RAGConfig()
    indexer = VectorIndexer(config)

    print("[INFO] 인덱스 삭제 중...")
    deleted = indexer.delete_all()
    print(f"[INFO] {deleted} 청크 삭제됨")

    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    """지식 학습 (인덱싱 + 검증)"""
    from kis_estimator_core.rag.indexer import VectorIndexer

    print("=" * 60)
    print("KIS RAG 지식 학습")
    print("=" * 60)

    config = RAGConfig()

    # 1. 설정 검증
    print("\n[1/3] 설정 검증...")
    is_valid, messages = config.validate()
    for msg in messages:
        print(f"  {msg}")

    if not is_valid:
        print("\n[ERROR] 설정 검증 실패")
        return 1

    print("  [OK] 설정 검증 완료")

    # 2. 인덱싱
    print("\n[2/3] 지식 인덱싱...")
    indexer = VectorIndexer(config)

    if args.force:
        print("  [INFO] 기존 인덱스 삭제...")
        indexer.delete_all()

    start_time = time.time()
    stats = indexer.index_all(batch_size=args.batch_size)
    elapsed = time.time() - start_time

    print(f"  총 청크: {stats['total_chunks']}")
    print(f"  인덱싱: {stats['indexed']}, 스킵: {stats['skipped']}, 오류: {stats['errors']}")
    print(f"  처리 시간: {elapsed:.2f}초")

    if stats["errors"] > 0:
        print(f"  [WARN] {stats['errors']}개 오류 발생")
    else:
        print("  [OK] 인덱싱 완료")

    # 3. 검증 검색
    print("\n[3/3] 검증 검색...")
    from kis_estimator_core.rag.retriever import HybridRetriever

    retriever = HybridRetriever(config)

    test_queries = [
        ("차단기", "BREAKER"),
        ("외함 크기", "ENCLOSURE"),
        ("마그네트", "ACCESSORY"),
    ]

    all_passed = True
    for query, expected_cat in test_queries:
        results = retriever.search(query, top_k=3)
        if results:
            top_cat = results[0].category
            status = "[OK]" if top_cat == expected_cat else "[WARN]"
            print(f"  {status} '{query}' -> {len(results)} 결과 (Top: {top_cat})")
        else:
            print(f"  [FAIL] '{query}' -> 결과 없음")
            all_passed = False

    # Evidence 저장
    evidence_path = indexer.save_evidence()
    print(f"\n[Evidence] {evidence_path}")

    # 결과
    print("\n" + "=" * 60)
    if all_passed and stats["errors"] == 0:
        print("[OK] 지식 학습 완료")
        return 0
    else:
        print("[WARN] 지식 학습 완료 (일부 경고)")
        return 1


def main():
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(
        prog="kis-rag",
        description="KIS RAG 지식 학습 및 관리 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 지식 인덱싱
  python -m kis_estimator_core.rag.cli index --batch-size 64

  # 강제 재인덱싱
  python -m kis_estimator_core.rag.cli index --force

  # 지식 검색
  python -m kis_estimator_core.rag.cli search "SBE-104 차단기 가격"
  python -m kis_estimator_core.rag.cli search "외함 크기 계산" --category FORMULA

  # 인덱스 통계
  python -m kis_estimator_core.rag.cli stats --json

  # 설정 검증
  python -m kis_estimator_core.rag.cli validate

  # 인덱스 삭제
  python -m kis_estimator_core.rag.cli clear --force

  # 지식 학습 (인덱싱 + 검증)
  python -m kis_estimator_core.rag.cli learn --force
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # index 명령어
    p_index = subparsers.add_parser("index", help="지식 인덱싱")
    p_index.add_argument(
        "--batch-size", type=int, default=32, help="배치 크기 (기본값: 32)"
    )
    p_index.add_argument(
        "--force", "-f", action="store_true", help="기존 인덱스 삭제 후 재인덱싱"
    )

    # search 명령어
    p_search = subparsers.add_parser("search", help="지식 검색")
    p_search.add_argument("query", help="검색 쿼리")
    p_search.add_argument(
        "--top-k", "-k", type=int, default=5, help="반환할 결과 수 (기본값: 5)"
    )
    p_search.add_argument(
        "--category",
        "-c",
        help="카테고리 필터 (BREAKER, ENCLOSURE, ACCESSORY, FORMULA, STANDARD, PRICE, RULE)",
    )
    p_search.add_argument(
        "--type",
        "-t",
        choices=["semantic", "keyword", "hybrid"],
        default="hybrid",
        help="검색 유형 (기본값: hybrid)",
    )
    p_search.add_argument(
        "--save-evidence", "-e", action="store_true", help="Evidence 저장"
    )

    # stats 명령어
    p_stats = subparsers.add_parser("stats", help="인덱스 통계")
    p_stats.add_argument("--json", "-j", action="store_true", help="JSON 형식 출력")

    # validate 명령어
    p_validate = subparsers.add_parser("validate", help="설정 검증")
    p_validate.add_argument("--json", "-j", action="store_true", help="설정 JSON 출력")

    # clear 명령어
    p_clear = subparsers.add_parser("clear", help="인덱스 삭제")
    p_clear.add_argument(
        "--force", "-f", action="store_true", help="확인 없이 삭제"
    )

    # learn 명령어 (통합)
    p_learn = subparsers.add_parser("learn", help="지식 학습 (인덱싱 + 검증)")
    p_learn.add_argument(
        "--batch-size", type=int, default=32, help="배치 크기 (기본값: 32)"
    )
    p_learn.add_argument(
        "--force", "-f", action="store_true", help="기존 인덱스 삭제 후 재인덱싱"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # 명령어 실행
    commands = {
        "index": cmd_index,
        "search": cmd_search,
        "stats": cmd_stats,
        "validate": cmd_validate,
        "clear": cmd_clear,
        "learn": cmd_learn,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
