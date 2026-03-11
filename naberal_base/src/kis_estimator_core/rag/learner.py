"""
RAG Learning Service - 대화 중 학습한 지식/노하우/단가 저장

대표님 요청:
"대화중 분전반의 지식이나 견적에관한 노하우, 지식, 새로운 단가 및 지식들은
RAG시스템으로 저장해서 학습에 활용할수있게해"

카테고리:
- KNOWLEDGE: 분전반/차단기/외함 관련 기술 지식
- KNOWHOW: 견적 작성 노하우, 팁, 경험
- PRICE: 새로운 단가 정보, 가격 업데이트
- RULE: 비즈니스 규칙, 정책

NO MOCKS - Real implementation only
"""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


# 학습 데이터 카테고리
LearningCategory = Literal["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"]


@dataclass
class LearnedItem:
    """학습된 지식 항목"""

    id: str
    category: LearningCategory
    title: str
    content: str
    source: str  # 학습 출처 (대화, 수동 입력 등)
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    hash: str = ""
    verified: bool = False  # 검증 여부

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.hash:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """콘텐츠 해시 계산"""
        content_str = f"{self.category}:{self.title}:{self.content}"
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LearnedItem":
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class PriceUpdate:
    """가격 업데이트 항목"""

    id: str
    item_name: str  # 품목명
    item_code: str  # 품목 코드
    old_price: int | None  # 이전 가격
    new_price: int  # 새 가격
    unit: str = "원"  # 단위
    effective_date: str = ""  # 적용일
    reason: str = ""  # 변경 사유
    source: str = "대화"  # 출처
    verified: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.effective_date:
            self.effective_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PriceUpdate":
        return cls(**data)


class RAGLearner:
    """
    RAG 학습 서비스

    대화 중 학습된 지식/노하우/단가를 저장하고 관리합니다.
    파일 기반 저장 (JSON) - 추후 DGX SPARK RAG 시스템과 연동 예정
    """

    def __init__(self, storage_path: Path | None = None):
        """
        초기화

        Args:
            storage_path: 저장 경로 (기본: data/ai_memory/learned/)
        """
        if storage_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
            storage_path = base_path / "data" / "ai_memory" / "learned"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 카테고리별 파일
        self.knowledge_file = self.storage_path / "knowledge.json"
        self.knowhow_file = self.storage_path / "knowhow.json"
        self.price_file = self.storage_path / "prices.json"
        self.rule_file = self.storage_path / "rules.json"

        # 인덱스 파일 (검색 최적화)
        self.index_file = self.storage_path / "index.json"

        # 캐시
        self._cache: dict[str, list[dict]] = {}

        # 초기화
        self._ensure_files()

    def _ensure_files(self):
        """파일 존재 확인 및 생성"""
        for filepath in [self.knowledge_file, self.knowhow_file,
                        self.price_file, self.rule_file, self.index_file]:
            if not filepath.exists():
                self._write_json(filepath, {"items": [], "meta": {
                    "version": "1.0.0",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "count": 0
                }})

    def _read_json(self, filepath: Path) -> dict:
        """JSON 파일 읽기"""
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"items": [], "meta": {}}

    def _write_json(self, filepath: Path, data: dict):
        """JSON 파일 쓰기"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_file_for_category(self, category: LearningCategory) -> Path:
        """카테고리별 파일 경로"""
        mapping = {
            "KNOWLEDGE": self.knowledge_file,
            "KNOWHOW": self.knowhow_file,
            "PRICE": self.price_file,
            "RULE": self.rule_file,
        }
        return mapping[category]

    # ========== 지식 저장 ==========

    def save_knowledge(
        self,
        title: str,
        content: str,
        category: LearningCategory = "KNOWLEDGE",
        tags: list[str] | None = None,
        source: str = "대화",
        metadata: dict | None = None,
    ) -> LearnedItem:
        """
        지식 저장

        Args:
            title: 제목
            content: 내용
            category: 카테고리 (KNOWLEDGE, KNOWHOW, PRICE, RULE)
            tags: 태그 목록
            source: 출처
            metadata: 추가 메타데이터

        Returns:
            저장된 LearnedItem
        """
        item = LearnedItem(
            id=str(uuid.uuid4())[:8],
            category=category,
            title=title,
            content=content,
            source=source,
            tags=tags or [],
            metadata=metadata or {},
        )

        # 파일에 저장
        filepath = self._get_file_for_category(category)
        data = self._read_json(filepath)
        data["items"].append(item.to_dict())
        data["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        data["meta"]["count"] = len(data["items"])
        self._write_json(filepath, data)

        # 인덱스 업데이트
        self._update_index(item)

        # 캐시 무효화
        self._cache.pop(category, None)

        return item

    def save_knowhow(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "대화",
    ) -> LearnedItem:
        """
        노하우 저장 (간편 메서드)

        예: "4P 50AF는 경제형이 없어서 표준형 사용해야 해"
        """
        return self.save_knowledge(
            title=title,
            content=content,
            category="KNOWHOW",
            tags=tags or ["견적", "노하우"],
            source=source,
        )

    def save_rule(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "대화",
    ) -> LearnedItem:
        """
        비즈니스 규칙 저장

        예: "소형 2P는 마주보기 40mm로 배치"
        """
        return self.save_knowledge(
            title=title,
            content=content,
            category="RULE",
            tags=tags or ["규칙", "정책"],
            source=source,
        )

    # ========== 가격 저장 ==========

    def save_price(
        self,
        item_name: str,
        new_price: int,
        item_code: str = "",
        old_price: int | None = None,
        reason: str = "",
        source: str = "대화",
    ) -> PriceUpdate | None:
        """
        가격 정보 저장 (중복 체크 포함)

        Args:
            item_name: 품목명 (예: "SBE-104 4P 100AF 75AT")
            new_price: 새 가격
            item_code: 품목 코드
            old_price: 이전 가격
            reason: 변경 사유
            source: 출처

        Returns:
            저장된 PriceUpdate 또는 None (중복 시)
        """
        # 기존 가격 데이터 확인
        data = self._read_json(self.price_file)
        item_name_lower = item_name.lower().strip()

        # 동일 품목명 찾기
        existing_idx = None
        existing_item = None
        for idx, item in enumerate(data["items"]):
            if item.get("item_name", "").lower().strip() == item_name_lower:
                existing_idx = idx
                existing_item = item
                break

        if existing_item:
            # 동일 품목 존재
            if existing_item.get("new_price") == new_price:
                # 가격도 동일 → 저장 안 함
                return None
            else:
                # 가격이 다름 → 업데이트
                price_item = PriceUpdate(
                    id=existing_item.get("id", str(uuid.uuid4())[:8]),
                    item_name=item_name,
                    item_code=item_code or existing_item.get("item_code", ""),
                    old_price=existing_item.get("new_price"),  # 기존 가격을 old_price로
                    new_price=new_price,
                    reason=reason or "가격 업데이트",
                    source=source,
                )
                data["items"][existing_idx] = price_item.to_dict()
        else:
            # 신규 품목
            price_item = PriceUpdate(
                id=str(uuid.uuid4())[:8],
                item_name=item_name,
                item_code=item_code,
                old_price=old_price,
                new_price=new_price,
                reason=reason,
                source=source,
            )
            data["items"].append(price_item.to_dict())

        # 파일 저장
        data["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        data["meta"]["count"] = len(data["items"])
        self._write_json(self.price_file, data)

        # 캐시 무효화
        self._cache.pop("PRICE", None)

        return price_item

    # ========== 조회 ==========

    def get_all(self, category: LearningCategory | None = None) -> list[dict]:
        """
        모든 학습 데이터 조회

        Args:
            category: 카테고리 필터 (None이면 전체)

        Returns:
            학습 데이터 목록
        """
        if category:
            # 캐시 확인
            if category in self._cache:
                return self._cache[category]

            filepath = self._get_file_for_category(category)
            data = self._read_json(filepath)
            items = data.get("items", [])
            self._cache[category] = items
            return items

        # 전체 조회
        all_items = []
        for cat in ["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"]:
            items = self.get_all(cat)  # type: ignore
            all_items.extend(items)

        return all_items

    def search(
        self,
        query: str,
        category: LearningCategory | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        학습 데이터 검색 (키워드 기반, 양방향 매칭)

        Args:
            query: 검색어
            category: 카테고리 필터
            limit: 최대 결과 수

        Returns:
            검색 결과 목록 (매칭 점수 순)
        """
        items = self.get_all(category)
        query_lower = query.lower()

        # 쿼리에서 핵심 키워드 추출 (불용어 제외)
        stopwords = {"이", "가", "은", "는", "을", "를", "의", "에", "에서", "로", "으로",
                     "와", "과", "도", "만", "뿐", "까지", "마저", "조차", "부터",
                     "이다", "하다", "되다", "있다", "없다", "아니다",
                     "얼마", "얼마야", "뭐야", "뭐", "어떻게", "언제", "어디", "누가",
                     "가격", "단가", "how", "what", "is", "the", "a", "an"}

        query_keywords = [w for w in query_lower.split() if w not in stopwords and len(w) >= 2]

        results = []
        for item in items:
            # 제목, 내용, 태그, 아이템명에서 검색
            title = item.get("title", "").lower()
            content = item.get("content", "").lower()
            tags = " ".join(item.get("tags", [])).lower()
            item_name = item.get("item_name", "").lower()

            # 모든 검색 대상 텍스트 결합
            searchable_text = f"{title} {content} {tags} {item_name}"

            # 매칭 점수 계산
            match_score = 0

            # 1. 쿼리 키워드가 아이템에 포함되는지 확인
            for keyword in query_keywords:
                if keyword in searchable_text:
                    match_score += 2

            # 2. 아이템명/제목이 쿼리에 포함되는지 확인 (역방향)
            if item_name and item_name in query_lower:
                match_score += 5
            if title and title in query_lower:
                match_score += 3

            # 3. 태그 매칭
            for tag in item.get("tags", []):
                if tag.lower() in query_lower:
                    match_score += 2

            if match_score > 0:
                results.append((match_score, item))

        # 점수 순으로 정렬
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]

    def get_recent(self, limit: int = 10) -> list[dict]:
        """최근 학습 데이터 조회"""
        all_items = self.get_all()

        # 생성일 기준 정렬
        sorted_items = sorted(
            all_items,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        return sorted_items[:limit]

    def get_stats(self) -> dict:
        """학습 데이터 통계"""
        stats = {
            "total": 0,
            "by_category": {},
            "last_updated": None,
        }

        for category in ["KNOWLEDGE", "KNOWHOW", "PRICE", "RULE"]:
            filepath = self._get_file_for_category(category)  # type: ignore
            data = self._read_json(filepath)
            count = len(data.get("items", []))
            stats["by_category"][category] = count
            stats["total"] += count

            # 최근 업데이트 시간
            updated_at = data.get("meta", {}).get("updated_at")
            if updated_at:
                if stats["last_updated"] is None or updated_at > stats["last_updated"]:
                    stats["last_updated"] = updated_at

        return stats

    # ========== 인덱스 관리 ==========

    def _update_index(self, item: LearnedItem):
        """인덱스 업데이트 (검색 최적화)"""
        data = self._read_json(self.index_file)

        # 간단한 역인덱스 구조
        if "keywords" not in data:
            data["keywords"] = {}

        # 제목과 태그에서 키워드 추출
        keywords = item.title.split() + item.tags

        for keyword in keywords:
            keyword = keyword.lower().strip()
            if len(keyword) < 2:
                continue

            if keyword not in data["keywords"]:
                data["keywords"][keyword] = []

            if item.id not in data["keywords"][keyword]:
                data["keywords"][keyword].append(item.id)

        data["meta"] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_keywords": len(data["keywords"]),
        }

        self._write_json(self.index_file, data)

    # ========== 삭제 ==========

    def delete(self, item_id: str, category: LearningCategory) -> bool:
        """
        학습 데이터 삭제

        Args:
            item_id: 항목 ID
            category: 카테고리

        Returns:
            삭제 성공 여부
        """
        filepath = self._get_file_for_category(category)
        data = self._read_json(filepath)

        original_count = len(data["items"])
        data["items"] = [
            item for item in data["items"]
            if item.get("id") != item_id
        ]

        if len(data["items"]) < original_count:
            data["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["meta"]["count"] = len(data["items"])
            self._write_json(filepath, data)
            self._cache.pop(category, None)
            return True

        return False

    def clear_category(self, category: LearningCategory) -> int:
        """
        카테고리 전체 삭제

        Args:
            category: 카테고리

        Returns:
            삭제된 항목 수
        """
        filepath = self._get_file_for_category(category)
        data = self._read_json(filepath)

        deleted_count = len(data["items"])
        data["items"] = []
        data["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        data["meta"]["count"] = 0

        self._write_json(filepath, data)
        self._cache.pop(category, None)

        return deleted_count


# 싱글톤 인스턴스
_learner: RAGLearner | None = None


def get_learner() -> RAGLearner:
    """RAGLearner 싱글톤 인스턴스"""
    global _learner
    if _learner is None:
        _learner = RAGLearner()
    return _learner
