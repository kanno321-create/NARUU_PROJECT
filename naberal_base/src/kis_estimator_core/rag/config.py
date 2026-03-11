"""
RAG System Configuration - 로컬 PC 환경 최적화

환경변수로 외부 지식팩 경로 지정 가능:
    KIS_KNOWLEDGE_PATH: 지식팩 디렉토리
    KIS_CORE_RULES_PATH: 코어 규칙 JSON 파일
    KIS_PRICE_CATALOG_PATH: 가격 카탈로그 CSV
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


def _get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    # 이 파일 위치: src/kis_estimator_core/rag/config.py
    return Path(__file__).parent.parent.parent.parent


@dataclass
class RAGConfig:
    """RAG 시스템 설정"""

    # 지식 파일 경로 (여러 경로 지원)
    knowledge_base_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "KIS_KNOWLEDGE_PATH",
                str(_get_project_root() / "KIS" / "Knowledge" / "packs")
            )
        )
    )

    # 추가 지식 경로 목록
    additional_knowledge_paths: list[Path] = field(
        default_factory=lambda: [
            _get_project_root() / "spec_kit" / "knowledge",
        ]
    )
    core_rules_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "KIS_CORE_RULES_PATH",
                str(_get_project_root() / "core" / "ssot" / "constants" / "registry.py")
            )
        )
    )
    price_catalog_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "KIS_PRICE_CATALOG_PATH",
                str(_get_project_root() / "data" / "catalog.csv")
            )
        )
    )

    # ChromaDB 설정
    chroma_persist_dir: Path = field(
        default_factory=lambda: Path("./data/chroma_db")
    )
    collection_name: str = "kis_knowledge"

    # 임베딩 모델 설정 (sentence-transformers)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384  # MiniLM 출력 차원

    # 청킹 설정
    chunk_size: int = 512  # 토큰 기준
    chunk_overlap: int = 50
    chunking_strategy: Literal["semantic", "fixed", "hybrid"] = "hybrid"

    # 검색 설정
    search_type: Literal["semantic", "keyword", "hybrid"] = "hybrid"
    top_k: int = 5
    similarity_threshold: float = 0.7

    # 카테고리 정의 (CLAUDE.md 기준)
    categories: list[str] = field(
        default_factory=lambda: [
            "BREAKER",      # 차단기 지식
            "ENCLOSURE",    # 외함 지식
            "ACCESSORY",    # 부속자재 지식
            "FORMULA",      # 계산 공식
            "STANDARD",     # IEC/KS 표준
            "PRICE",        # 가격 정보
            "RULE",         # 비즈니스 규칙
        ]
    )

    # 메타데이터 필드
    metadata_fields: list[str] = field(
        default_factory=lambda: [
            "category",
            "source",
            "hash",
            "version",
            "created_at",
        ]
    )

    def get_all_knowledge_paths(self) -> list[Path]:
        """모든 지식 경로 반환 (존재하는 경로만)"""
        paths = []
        if self.knowledge_base_path.exists():
            paths.append(self.knowledge_base_path)
        for path in self.additional_knowledge_paths:
            if path.exists():
                paths.append(path)
        return paths

    def validate(self, strict: bool = False) -> tuple[bool, list[str]]:
        """
        설정 유효성 검증

        Args:
            strict: True면 에러 발생, False면 경고만 출력

        Returns:
            (valid, warnings) 튜플
        """
        warnings = []
        found_paths = []

        if not self.knowledge_base_path.exists():
            warnings.append(f"[WARN] Primary knowledge path not found: {self.knowledge_base_path}")
        else:
            found_paths.append(self.knowledge_base_path)

        for path in self.additional_knowledge_paths:
            if path.exists():
                found_paths.append(path)
                warnings.append(f"[OK] Additional knowledge path: {path}")
            else:
                warnings.append(f"[WARN] Additional path not found: {path}")

        if not self.core_rules_path.exists():
            warnings.append(f"[WARN] Core rules not found: {self.core_rules_path}")

        if self.chunk_size < 100:
            warnings.append(f"[WARN] Chunk size too small: {self.chunk_size}")

        if self.top_k < 1 or self.top_k > 20:
            warnings.append(f"[ERROR] top_k out of range: {self.top_k}")

        # 하나 이상의 지식 경로가 있으면 valid
        has_knowledge = len(found_paths) > 0

        if strict and not has_knowledge:
            raise ValueError("No knowledge paths found!\n" + "\n".join(warnings))

        return has_knowledge, warnings


# 기본 설정 인스턴스
default_config = RAGConfig()
