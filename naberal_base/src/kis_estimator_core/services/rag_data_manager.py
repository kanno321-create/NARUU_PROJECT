"""
RAG Data Manager - AI 학습 데이터 관리 시스템

이미지 분석 → 견적 생성 학습 데이터를 체계적으로 관리합니다.
- Gold/Silver/Bronze 계층화 시스템
- 이미지 해시 기반 중복 제거
- 성공률 기반 품질 관리
- 자동 정리 정책

Contract-First + Zero-Mock
NO MOCKS - Real data storage only
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DataTier(str, Enum):
    """RAG 데이터 품질 계층"""
    GOLD = "gold"      # 사용자 승인/수정 없이 성공
    SILVER = "silver"  # 1회 수정 후 성공
    BRONZE = "bronze"  # 2회 이상 수정 또는 미승인


@dataclass
class RAGDataEntry:
    """RAG 학습 데이터 엔트리"""
    entry_id: str                    # 고유 ID
    image_hash: str                  # 이미지 perceptual hash (중복 감지)
    original_request: str            # 원본 견적 요청문 (Vision API 출력)
    final_request: str               # 최종 견적 요청문 (사용자 수정 후)
    estimate_id: str | None          # 생성된 견적 ID
    tier: DataTier                   # 데이터 품질 계층
    revision_count: int              # 수정 횟수
    success_count: int               # 유사 이미지 성공 횟수
    fail_count: int                  # 유사 이미지 실패 횟수
    created_at: str                  # 생성 시각
    last_used_at: str                # 마지막 사용 시각
    metadata: dict = field(default_factory=dict)  # 추가 메타데이터

    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5  # 기본값 50%
        return self.success_count / total

    @property
    def relevance_score(self) -> float:
        """
        종합 관련성 점수 계산
        - 성공률 (40%)
        - 계층 가중치 (30%)
        - 최신성 (20%)
        - 사용 빈도 (10%)
        """
        # 계층 가중치
        tier_weights = {
            DataTier.GOLD: 1.0,
            DataTier.SILVER: 0.7,
            DataTier.BRONZE: 0.4,
        }
        tier_score = tier_weights.get(self.tier, 0.5)

        # 최신성 점수 (30일 이내 = 1.0, 180일 이상 = 0.1)
        try:
            last_used = datetime.fromisoformat(self.last_used_at.replace('Z', '+00:00'))
            days_ago = (datetime.now(UTC) - last_used).days
            recency_score = max(0.1, 1.0 - (days_ago / 180))
        except (ValueError, TypeError):
            recency_score = 0.5

        # 사용 빈도 점수
        total_uses = self.success_count + self.fail_count
        frequency_score = min(1.0, total_uses / 10)  # 10회 사용 시 최대

        # 종합 점수
        return (
            self.success_rate * 0.4 +
            tier_score * 0.3 +
            recency_score * 0.2 +
            frequency_score * 0.1
        )


class RAGDataManager:
    """
    RAG 학습 데이터 관리자

    특징:
    - JSON 파일 기반 영구 저장
    - 이미지 해시 기반 중복 감지
    - 계층화된 데이터 품질 관리
    - 자동 정리 정책
    """

    # 저장 경로
    DATA_DIR = Path("data/rag")
    DATA_FILE = DATA_DIR / "rag_entries.json"
    ARCHIVE_DIR = DATA_DIR / "archive"

    # 정책 상수
    MAX_ENTRIES = 10000              # 최대 엔트리 수
    ARCHIVE_DAYS = 180               # 아카이브 기준 일수
    DELETE_SUCCESS_RATE = 0.3        # 삭제 기준 성공률
    DUPLICATE_THRESHOLD = 0.95       # 중복 판정 임계값

    _instance: Optional['RAGDataManager'] = None
    _entries: dict[str, RAGDataEntry] = {}
    _image_hash_index: dict[str, list[str]] = {}  # hash -> entry_ids

    def __new__(cls) -> 'RAGDataManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._entries = {}
            cls._image_hash_index = {}
            cls._instance._init_storage()
        return cls._instance

    def _init_storage(self) -> None:
        """스토리지 초기화"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_data()
        logger.info(f"RAGDataManager initialized with {len(self._entries)} entries")

    def _load_data(self) -> None:
        """파일에서 데이터 로드"""
        if not self.DATA_FILE.exists():
            return

        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for entry_data in data.get('entries', []):
                entry = RAGDataEntry(
                    entry_id=entry_data['entry_id'],
                    image_hash=entry_data['image_hash'],
                    original_request=entry_data['original_request'],
                    final_request=entry_data['final_request'],
                    estimate_id=entry_data.get('estimate_id'),
                    tier=DataTier(entry_data['tier']),
                    revision_count=entry_data['revision_count'],
                    success_count=entry_data['success_count'],
                    fail_count=entry_data['fail_count'],
                    created_at=entry_data['created_at'],
                    last_used_at=entry_data['last_used_at'],
                    metadata=entry_data.get('metadata', {}),
                )
                self._entries[entry.entry_id] = entry

                # 해시 인덱스 구축
                if entry.image_hash not in self._image_hash_index:
                    self._image_hash_index[entry.image_hash] = []
                self._image_hash_index[entry.image_hash].append(entry.entry_id)

            logger.info(f"Loaded {len(self._entries)} RAG entries from file")
        except Exception as e:
            logger.error(f"Failed to load RAG data: {e}")

    def _save_data(self) -> None:
        """파일에 데이터 저장"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now(UTC).isoformat(),
                'entries': [
                    {
                        'entry_id': e.entry_id,
                        'image_hash': e.image_hash,
                        'original_request': e.original_request,
                        'final_request': e.final_request,
                        'estimate_id': e.estimate_id,
                        'tier': e.tier.value,
                        'revision_count': e.revision_count,
                        'success_count': e.success_count,
                        'fail_count': e.fail_count,
                        'created_at': e.created_at,
                        'last_used_at': e.last_used_at,
                        'metadata': e.metadata,
                    }
                    for e in self._entries.values()
                ]
            }

            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self._entries)} RAG entries to file")
        except Exception as e:
            logger.error(f"Failed to save RAG data: {e}")

    @staticmethod
    def compute_image_hash(image_data: bytes) -> str:
        """
        이미지 해시 계산 (중복 감지용)

        실제 perceptual hash 대신 SHA256 사용 (간소화)
        TODO: imagehash 라이브러리로 perceptual hash 구현
        """
        return hashlib.sha256(image_data).hexdigest()[:16]

    def add_entry(
        self,
        image_hash: str,
        original_request: str,
        final_request: str | None = None,
        estimate_id: str | None = None,
        revision_count: int = 0,
        metadata: dict | None = None,
    ) -> RAGDataEntry:
        """
        새 RAG 엔트리 추가

        Args:
            image_hash: 이미지 해시
            original_request: Vision API 원본 출력
            final_request: 사용자 수정 후 최종 요청 (없으면 원본 사용)
            estimate_id: 생성된 견적 ID
            revision_count: 수정 횟수
            metadata: 추가 메타데이터

        Returns:
            생성된 RAGDataEntry
        """
        # 중복 체크
        existing = self.find_by_hash(image_hash)
        if existing and existing.success_rate > self.DUPLICATE_THRESHOLD:
            # 기존 항목 업데이트
            existing.success_count += 1
            existing.last_used_at = datetime.now(UTC).isoformat()
            self._save_data()
            logger.info(f"Updated existing entry {existing.entry_id} (success +1)")
            return existing

        # 새 엔트리 생성
        now = datetime.now(UTC).isoformat()
        entry_id = f"RAG-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{image_hash[:8]}"

        # 계층 결정
        if revision_count == 0:
            tier = DataTier.GOLD
        elif revision_count == 1:
            tier = DataTier.SILVER
        else:
            tier = DataTier.BRONZE

        entry = RAGDataEntry(
            entry_id=entry_id,
            image_hash=image_hash,
            original_request=original_request,
            final_request=final_request or original_request,
            estimate_id=estimate_id,
            tier=tier,
            revision_count=revision_count,
            success_count=1 if revision_count == 0 else 0,
            fail_count=0 if revision_count == 0 else 1,
            created_at=now,
            last_used_at=now,
            metadata=metadata or {},
        )

        self._entries[entry_id] = entry

        # 해시 인덱스 업데이트
        if image_hash not in self._image_hash_index:
            self._image_hash_index[image_hash] = []
        self._image_hash_index[image_hash].append(entry_id)

        self._save_data()
        logger.info(f"Added new RAG entry {entry_id} (tier: {tier.value})")

        return entry

    def update_entry(
        self,
        entry_id: str,
        success: bool = True,
        final_request: str | None = None,
        estimate_id: str | None = None,
    ) -> RAGDataEntry | None:
        """
        RAG 엔트리 업데이트

        Args:
            entry_id: 엔트리 ID
            success: 성공 여부
            final_request: 수정된 요청 (있으면)
            estimate_id: 생성된 견적 ID

        Returns:
            업데이트된 엔트리 또는 None
        """
        entry = self._entries.get(entry_id)
        if not entry:
            logger.warning(f"Entry not found: {entry_id}")
            return None

        if success:
            entry.success_count += 1
        else:
            entry.fail_count += 1

        if final_request and final_request != entry.final_request:
            entry.final_request = final_request
            entry.revision_count += 1
            # 계층 재조정
            if entry.revision_count == 1:
                entry.tier = DataTier.SILVER
            elif entry.revision_count >= 2:
                entry.tier = DataTier.BRONZE

        if estimate_id:
            entry.estimate_id = estimate_id

        entry.last_used_at = datetime.now(UTC).isoformat()

        self._save_data()
        logger.info(f"Updated entry {entry_id}: success_rate={entry.success_rate:.2f}")

        return entry

    def find_by_hash(self, image_hash: str) -> RAGDataEntry | None:
        """
        이미지 해시로 최적 엔트리 찾기

        Args:
            image_hash: 이미지 해시

        Returns:
            가장 적합한 엔트리 또는 None
        """
        entry_ids = self._image_hash_index.get(image_hash, [])
        if not entry_ids:
            return None

        # 관련성 점수로 정렬하여 최고 반환
        entries = [self._entries[eid] for eid in entry_ids if eid in self._entries]
        if not entries:
            return None

        best_entry = max(entries, key=lambda e: e.relevance_score)
        return best_entry

    def search_similar(
        self,
        query: str,
        limit: int = 5,
        min_tier: DataTier = DataTier.BRONZE,
    ) -> list[RAGDataEntry]:
        """
        유사한 요청 검색 (간단한 키워드 매칭)

        Args:
            query: 검색 쿼리
            limit: 최대 반환 개수
            min_tier: 최소 계층

        Returns:
            관련 엔트리 목록 (관련성 점수 순)
        """
        tier_order = {DataTier.GOLD: 0, DataTier.SILVER: 1, DataTier.BRONZE: 2}
        min_tier_order = tier_order.get(min_tier, 2)

        # 계층 필터링
        candidates = [
            e for e in self._entries.values()
            if tier_order.get(e.tier, 3) <= min_tier_order
        ]

        # 키워드 매칭 점수 계산
        query_words = set(query.lower().split())

        def compute_similarity(entry: RAGDataEntry) -> float:
            entry_words = set(entry.final_request.lower().split())
            common = len(query_words & entry_words)
            total = len(query_words | entry_words)
            keyword_score = common / total if total > 0 else 0
            return keyword_score * 0.5 + entry.relevance_score * 0.5

        # 정렬 및 반환
        scored = [(e, compute_similarity(e)) for e in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [e for e, _ in scored[:limit]]

    def cleanup(self) -> dict:
        """
        자동 정리 수행

        정책:
        - 180일 미사용 → 아카이브
        - 성공률 30% 미만 → 삭제
        - 최대 개수 초과 → 낮은 점수부터 삭제

        Returns:
            정리 결과 통계
        """
        stats = {
            'archived': 0,
            'deleted': 0,
            'before_count': len(self._entries),
        }

        now = datetime.now(UTC)
        archive_threshold = now - timedelta(days=self.ARCHIVE_DAYS)

        to_archive = []
        to_delete = []

        for entry_id, entry in self._entries.items():
            try:
                last_used = datetime.fromisoformat(entry.last_used_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                last_used = now

            # 아카이브 대상
            if last_used < archive_threshold:
                to_archive.append(entry_id)
                continue

            # 삭제 대상 (낮은 성공률)
            if entry.success_rate < self.DELETE_SUCCESS_RATE and (entry.success_count + entry.fail_count) >= 5:
                to_delete.append(entry_id)

        # 아카이브 처리
        if to_archive:
            archive_data = []
            for entry_id in to_archive:
                entry = self._entries.pop(entry_id)
                archive_data.append({
                    'entry_id': entry.entry_id,
                    'image_hash': entry.image_hash,
                    'final_request': entry.final_request,
                    'tier': entry.tier.value,
                    'success_rate': entry.success_rate,
                    'archived_at': now.isoformat(),
                })
                # 해시 인덱스에서 제거
                if entry.image_hash in self._image_hash_index:
                    self._image_hash_index[entry.image_hash] = [
                        eid for eid in self._image_hash_index[entry.image_hash]
                        if eid != entry_id
                    ]

            # 아카이브 파일에 저장
            archive_file = self.ARCHIVE_DIR / f"archive_{now.strftime('%Y%m%d')}.json"
            try:
                existing = []
                if archive_file.exists():
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                existing.extend(archive_data)
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Archive save failed: {e}")

            stats['archived'] = len(to_archive)

        # 삭제 처리
        for entry_id in to_delete:
            entry = self._entries.pop(entry_id, None)
            if entry and entry.image_hash in self._image_hash_index:
                self._image_hash_index[entry.image_hash] = [
                    eid for eid in self._image_hash_index[entry.image_hash]
                    if eid != entry_id
                ]
        stats['deleted'] = len(to_delete)

        # 최대 개수 초과 시 정리
        if len(self._entries) > self.MAX_ENTRIES:
            # 낮은 점수 순 정렬
            sorted_entries = sorted(
                self._entries.items(),
                key=lambda x: x[1].relevance_score
            )
            # 초과분 삭제
            overflow = len(self._entries) - self.MAX_ENTRIES
            for entry_id, _ in sorted_entries[:overflow]:
                entry = self._entries.pop(entry_id)
                if entry.image_hash in self._image_hash_index:
                    self._image_hash_index[entry.image_hash] = [
                        eid for eid in self._image_hash_index[entry.image_hash]
                        if eid != entry_id
                    ]
                stats['deleted'] += 1

        stats['after_count'] = len(self._entries)
        self._save_data()

        logger.info(f"RAG cleanup complete: {stats}")
        return stats

    def get_stats(self) -> dict:
        """
        통계 정보 조회

        Returns:
            RAG 데이터 통계
        """
        if not self._entries:
            return {
                'total_entries': 0,
                'by_tier': {'gold': 0, 'silver': 0, 'bronze': 0},
                'avg_success_rate': 0,
                'unique_hashes': 0,
            }

        by_tier = {
            'gold': sum(1 for e in self._entries.values() if e.tier == DataTier.GOLD),
            'silver': sum(1 for e in self._entries.values() if e.tier == DataTier.SILVER),
            'bronze': sum(1 for e in self._entries.values() if e.tier == DataTier.BRONZE),
        }

        avg_rate = sum(e.success_rate for e in self._entries.values()) / len(self._entries)

        return {
            'total_entries': len(self._entries),
            'by_tier': by_tier,
            'avg_success_rate': round(avg_rate, 3),
            'unique_hashes': len(self._image_hash_index),
        }

    def promote_to_gold(self, entry_id: str) -> bool:
        """
        사용자 승인 시 GOLD로 승격

        Args:
            entry_id: 엔트리 ID

        Returns:
            성공 여부
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return False

        entry.tier = DataTier.GOLD
        entry.success_count += 1
        entry.last_used_at = datetime.now(UTC).isoformat()
        self._save_data()

        logger.info(f"Entry {entry_id} promoted to GOLD")
        return True


# 싱글톤 인스턴스 접근
_manager: RAGDataManager | None = None


def get_rag_data_manager() -> RAGDataManager:
    """RAGDataManager 싱글톤"""
    global _manager
    if _manager is None:
        _manager = RAGDataManager()
    return _manager
