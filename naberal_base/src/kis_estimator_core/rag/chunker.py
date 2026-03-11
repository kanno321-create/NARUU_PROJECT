"""
Knowledge Chunker - 지식팩 청킹 파이프라인

CLAUDE.md 권장 청킹 전략:
- 차단기 모델: 모델별 1청크
- 공식/규칙: 의미 단위 분할
- 카탈로그: 프레임별 그룹화
"""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kis_estimator_core.rag.config import RAGConfig


@dataclass
class KnowledgeChunk:
    """지식 청크 단위"""

    content: str
    metadata: dict

    @property
    def id(self) -> str:
        """SHA256 기반 청크 ID"""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


class KnowledgeChunker:
    """지식팩 청킹 파이프라인"""

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()

    def chunk_all(self) -> Iterator[KnowledgeChunk]:
        """모든 지식 소스 청킹"""
        # 1. JSON 지식팩 (59개 파일)
        yield from self._chunk_knowledge_packs()

        # 2. 코어 규칙 파일
        yield from self._chunk_core_rules()

        # 3. 가격 카탈로그 (선택적 - 너무 크면 스킵)
        # yield from self._chunk_price_catalog()

    def _chunk_knowledge_packs(self) -> Iterator[KnowledgeChunk]:
        """JSON 지식팩 청킹 - 모든 지식 경로 순회"""
        # 모든 지식 경로 수집
        all_paths = self.config.get_all_knowledge_paths()

        if not all_paths:
            print("[WARN] No knowledge paths found")
            return

        for knowledge_path in all_paths:
            print(f"[INFO] Scanning: {knowledge_path}")
            for json_file in knowledge_path.glob("*.json"):
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)

                    category = self._detect_category(json_file.name, data)

                    # 파일 유형에 따른 청킹 전략
                    if "breaker" in json_file.name.lower():
                        yield from self._chunk_breaker_data(data, json_file, category)
                    elif "enclosure" in json_file.name.lower():
                        yield from self._chunk_enclosure_data(data, json_file, category)
                    elif "accessor" in json_file.name.lower():
                        yield from self._chunk_accessory_data(data, json_file, category)
                    elif "formula" in json_file.name.lower() or "rule" in json_file.name.lower():
                        yield from self._chunk_formula_data(data, json_file, category)
                    else:
                        yield from self._chunk_generic_json(data, json_file, category)

                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"[WARN] Failed to parse: {json_file} - {e}")
                    continue

    def _chunk_breaker_data(
        self, data: dict | list, source: Path, category: str
    ) -> Iterator[KnowledgeChunk]:
        """차단기 데이터 청킹 - 모델별 1청크"""
        if isinstance(data, dict):
            # 모델별로 분리
            for key, value in data.items():
                content = f"## 차단기: {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, key),
                )
        elif isinstance(data, list):
            for item in data:
                model_name = item.get("model", item.get("name", "unknown"))
                content = f"## 차단기: {model_name}\n{json.dumps(item, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, model_name),
                )

    def _chunk_enclosure_data(
        self, data: dict | list, source: Path, category: str
    ) -> Iterator[KnowledgeChunk]:
        """외함 데이터 청킹"""
        if isinstance(data, dict):
            # 규칙/공식별로 분리
            for key, value in data.items():
                content = f"## 외함 규칙: {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, key),
                )
        elif isinstance(data, list):
            # HDS 카탈로그 등 - 그룹화
            for item in data:
                size = item.get("size", item.get("name", "unknown"))
                content = f"## 외함: {size}\n{json.dumps(item, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, size),
                )

    def _chunk_accessory_data(
        self, data: dict | list, source: Path, category: str
    ) -> Iterator[KnowledgeChunk]:
        """부속자재 데이터 청킹"""
        if isinstance(data, dict):
            for key, value in data.items():
                content = f"## 부속자재: {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, key),
                )
        elif isinstance(data, list):
            for item in data:
                name = item.get("name", item.get("type", "unknown"))
                content = f"## 부속자재: {name}\n{json.dumps(item, ensure_ascii=False, indent=2)}"
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, category, name),
                )

    def _chunk_formula_data(
        self, data: dict | list, source: Path, category: str
    ) -> Iterator[KnowledgeChunk]:
        """공식/규칙 데이터 청킹 - 의미 단위 분할"""
        if isinstance(data, dict):
            for key, value in data.items():
                # 공식은 컨텍스트 포함하여 청킹
                content = f"## 규칙/공식: {key}\n"
                if isinstance(value, dict):
                    content += json.dumps(value, ensure_ascii=False, indent=2)
                else:
                    content += str(value)
                yield KnowledgeChunk(
                    content=content,
                    metadata=self._build_metadata(source, "FORMULA", key),
                )

    def _chunk_generic_json(
        self, data: dict | list, source: Path, category: str
    ) -> Iterator[KnowledgeChunk]:
        """일반 JSON 청킹"""
        content = json.dumps(data, ensure_ascii=False, indent=2)

        # 크기가 크면 분할
        if len(content) > self.config.chunk_size * 4:
            if isinstance(data, dict):
                for key, value in data.items():
                    chunk_content = f"## {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}"
                    yield KnowledgeChunk(
                        content=chunk_content,
                        metadata=self._build_metadata(source, category, key),
                    )
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    chunk_content = f"## Item {i}\n{json.dumps(item, ensure_ascii=False, indent=2)}"
                    yield KnowledgeChunk(
                        content=chunk_content,
                        metadata=self._build_metadata(source, category, f"item_{i}"),
                    )
        else:
            yield KnowledgeChunk(
                content=f"## {source.stem}\n{content}",
                metadata=self._build_metadata(source, category, source.stem),
            )

    def _chunk_core_rules(self) -> Iterator[KnowledgeChunk]:
        """코어 규칙 파일 청킹 (ai_estimation_core.json)"""
        core_path = self.config.core_rules_path

        if not core_path.exists():
            return

        try:
            with open(core_path, encoding="utf-8") as f:
                data = json.load(f)

            # 대형 파일 - 최상위 키별로 분할
            for key, value in data.items():
                category = self._detect_category(key, value)
                content = f"## 코어규칙: {key}\n{json.dumps(value, ensure_ascii=False, indent=2)}"

                # 청크가 너무 크면 추가 분할
                if len(content) > self.config.chunk_size * 8:
                    yield from self._split_large_chunk(content, core_path, category, key)
                else:
                    yield KnowledgeChunk(
                        content=content,
                        metadata=self._build_metadata(core_path, category, key),
                    )

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[WARN] 코어 규칙 파싱 실패: {e}")

    def _split_large_chunk(
        self, content: str, source: Path, category: str, prefix: str
    ) -> Iterator[KnowledgeChunk]:
        """대형 청크 분할"""
        max_size = self.config.chunk_size * 4
        overlap = self.config.chunk_overlap

        lines = content.split("\n")
        current_chunk = []
        current_size = 0

        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_size += len(line)

            if current_size >= max_size:
                chunk_content = "\n".join(current_chunk)
                yield KnowledgeChunk(
                    content=chunk_content,
                    metadata=self._build_metadata(source, category, f"{prefix}_part{i}"),
                )
                # 오버랩 유지
                current_chunk = current_chunk[-overlap:] if overlap > 0 else []
                current_size = sum(len(line) for line in current_chunk)

        # 남은 부분
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            yield KnowledgeChunk(
                content=chunk_content,
                metadata=self._build_metadata(source, category, f"{prefix}_final"),
            )

    def _detect_category(self, name: str, data: dict | list | None = None) -> str:
        """파일명/내용 기반 카테고리 감지"""
        name_lower = name.lower()

        if "breaker" in name_lower or "mccb" in name_lower or "elb" in name_lower:
            return "BREAKER"
        elif "enclosure" in name_lower or "외함" in name_lower or "hds" in name_lower:
            return "ENCLOSURE"
        elif "accessor" in name_lower or "부속" in name_lower:
            return "ACCESSORY"
        elif "formula" in name_lower or "공식" in name_lower:
            return "FORMULA"
        elif "iec" in name_lower or "ks" in name_lower or "standard" in name_lower:
            return "STANDARD"
        elif "price" in name_lower or "단가" in name_lower or "가격" in name_lower:
            return "PRICE"
        else:
            return "RULE"

    def _build_metadata(self, source: Path, category: str, key: str) -> dict:
        """메타데이터 생성"""
        return {
            "category": category,
            "source": str(source),
            "key": key,
            "hash": hashlib.sha256(f"{source}:{key}".encode()).hexdigest()[:16],
            "version": "v1.0.0",
            "created_at": datetime.now(UTC).isoformat(),
        }
