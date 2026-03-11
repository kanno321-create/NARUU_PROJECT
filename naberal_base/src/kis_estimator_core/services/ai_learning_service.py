"""
AI Learning Service - AI 학습 파이프라인 통합 서비스

수동 → 반자동 → 자동 학습 파이프라인:
- 피드백 수집 및 저장
- RAG 데이터베이스 업데이트
- 학습 상태 모니터링
- 품질 평가 및 자동 개선

Contract-First + Zero-Mock
NO MOCKS - Real learning pipeline only
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 내부 서비스 임포트
from kis_estimator_core.services.rag_data_manager import (
    DataTier,
    RAGDataEntry,
    get_rag_data_manager,
)
from kis_estimator_core.services.rag_vector_service import (
    DocumentCategory,
    get_rag_vector_service,
)
from kis_estimator_core.services.ocr_service import (
    DocumentType as OCRDocumentType,
    get_ocr_service,
)


class LearningMode(str, Enum):
    """학습 모드"""
    MANUAL = "manual"         # 수동 (Phase 1)
    SEMI_AUTO = "semi_auto"   # 반자동 (Phase 2)
    AUTO = "auto"             # 자동 (Phase 3)


class FeedbackType(str, Enum):
    """피드백 유형"""
    APPROVAL = "approval"         # 승인 (정확함)
    CORRECTION = "correction"     # 수정 필요
    REJECTION = "rejection"       # 거부 (오류)
    HANDWRITTEN = "handwritten"   # 손글씨 피드백


@dataclass
class FeedbackEntry:
    """피드백 엔트리"""
    feedback_id: str
    estimate_id: str
    feedback_type: FeedbackType
    original_data: dict           # 원본 견적 데이터
    corrected_data: Optional[dict] = None  # 수정된 데이터
    feedback_text: str = ""       # 피드백 텍스트
    image_path: Optional[str] = None  # 손글씨 이미지 경로
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    created_at: str = ""
    processed: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class LearningStats:
    """학습 통계"""
    total_feedback: int = 0
    approvals: int = 0
    corrections: int = 0
    rejections: int = 0
    accuracy_rate: float = 0.0
    current_mode: LearningMode = LearningMode.MANUAL
    last_update: str = ""


class AILearningService:
    """
    AI 학습 파이프라인 서비스

    특징:
    - 3단계 학습 모드 (수동 → 반자동 → 자동)
    - 피드백 기반 RAG 업데이트
    - 손글씨 OCR 통합
    - 품질 모니터링 및 자동 전환
    """

    # 저장 경로
    DATA_DIR = Path("data/ai_learning")
    FEEDBACK_FILE = DATA_DIR / "feedback_entries.json"
    STATS_FILE = DATA_DIR / "learning_stats.json"

    # 모드 전환 기준
    MODE_TRANSITION_THRESHOLD = {
        LearningMode.MANUAL: {
            "min_feedback": 50,      # 최소 피드백 수
            "min_accuracy": 0.90,    # 최소 정확도
        },
        LearningMode.SEMI_AUTO: {
            "min_feedback": 200,
            "min_accuracy": 0.95,
        },
    }

    # 신뢰도 임계값
    AUTO_APPROVE_THRESHOLD = 0.95
    REVIEW_REQUIRED_THRESHOLD = 0.80

    _instance: Optional['AILearningService'] = None
    _feedback_entries: dict[str, FeedbackEntry] = {}
    _stats: Optional[LearningStats] = None

    def __new__(cls) -> 'AILearningService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """서비스 초기화"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._feedback_entries = {}
        self._load_data()
        logger.info(f"AILearningService 초기화 완료: {len(self._feedback_entries)} 피드백")

    def _load_data(self) -> None:
        """저장된 데이터 로드"""
        # 피드백 로드
        if self.FEEDBACK_FILE.exists():
            try:
                with open(self.FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for entry_data in data.get('entries', []):
                    entry = FeedbackEntry(
                        feedback_id=entry_data['feedback_id'],
                        estimate_id=entry_data['estimate_id'],
                        feedback_type=FeedbackType(entry_data['feedback_type']),
                        original_data=entry_data['original_data'],
                        corrected_data=entry_data.get('corrected_data'),
                        feedback_text=entry_data.get('feedback_text', ''),
                        image_path=entry_data.get('image_path'),
                        confidence_before=entry_data.get('confidence_before', 0),
                        confidence_after=entry_data.get('confidence_after', 0),
                        created_at=entry_data['created_at'],
                        processed=entry_data.get('processed', False),
                        metadata=entry_data.get('metadata', {}),
                    )
                    self._feedback_entries[entry.feedback_id] = entry
            except Exception as e:
                logger.error(f"피드백 데이터 로드 실패: {e}")

        # 통계 로드
        if self.STATS_FILE.exists():
            try:
                with open(self.STATS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._stats = LearningStats(
                    total_feedback=data.get('total_feedback', 0),
                    approvals=data.get('approvals', 0),
                    corrections=data.get('corrections', 0),
                    rejections=data.get('rejections', 0),
                    accuracy_rate=data.get('accuracy_rate', 0),
                    current_mode=LearningMode(data.get('current_mode', 'manual')),
                    last_update=data.get('last_update', ''),
                )
            except Exception as e:
                logger.error(f"통계 로드 실패: {e}")
                self._stats = LearningStats()
        else:
            self._stats = LearningStats()

    def _save_data(self) -> None:
        """데이터 저장"""
        # 피드백 저장
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now(UTC).isoformat(),
                'entries': [
                    {
                        'feedback_id': e.feedback_id,
                        'estimate_id': e.estimate_id,
                        'feedback_type': e.feedback_type.value,
                        'original_data': e.original_data,
                        'corrected_data': e.corrected_data,
                        'feedback_text': e.feedback_text,
                        'image_path': e.image_path,
                        'confidence_before': e.confidence_before,
                        'confidence_after': e.confidence_after,
                        'created_at': e.created_at,
                        'processed': e.processed,
                        'metadata': e.metadata,
                    }
                    for e in self._feedback_entries.values()
                ]
            }
            with open(self.FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"피드백 저장 실패: {e}")

        # 통계 저장
        if self._stats:
            try:
                stats_data = {
                    'total_feedback': self._stats.total_feedback,
                    'approvals': self._stats.approvals,
                    'corrections': self._stats.corrections,
                    'rejections': self._stats.rejections,
                    'accuracy_rate': self._stats.accuracy_rate,
                    'current_mode': self._stats.current_mode.value,
                    'last_update': datetime.now(UTC).isoformat(),
                }
                with open(self.STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"통계 저장 실패: {e}")

    def submit_feedback(
        self,
        estimate_id: str,
        feedback_type: FeedbackType,
        original_data: dict,
        corrected_data: Optional[dict] = None,
        feedback_text: str = "",
        image_path: Optional[str] = None,
        confidence: float = 0.0,
    ) -> FeedbackEntry:
        """
        피드백 제출

        Args:
            estimate_id: 견적 ID
            feedback_type: 피드백 유형
            original_data: 원본 데이터
            corrected_data: 수정된 데이터
            feedback_text: 피드백 텍스트
            image_path: 손글씨 이미지 경로
            confidence: 원본 신뢰도

        Returns:
            생성된 피드백 엔트리
        """
        now = datetime.now(UTC)
        feedback_id = f"FB-{now.strftime('%Y%m%d%H%M%S')}-{estimate_id[:8]}"

        # 손글씨 이미지가 있으면 OCR 처리
        ocr_text = ""
        if image_path and feedback_type == FeedbackType.HANDWRITTEN:
            try:
                ocr_service = get_ocr_service()
                ocr_result = ocr_service.process_handwritten_feedback(image_path)
                ocr_text = ocr_result.get('raw_text', '')
                feedback_text = f"{feedback_text}\n[OCR 결과]: {ocr_text}"
            except Exception as e:
                logger.error(f"OCR 처리 실패: {e}")

        entry = FeedbackEntry(
            feedback_id=feedback_id,
            estimate_id=estimate_id,
            feedback_type=feedback_type,
            original_data=original_data,
            corrected_data=corrected_data,
            feedback_text=feedback_text,
            image_path=image_path,
            confidence_before=confidence,
            created_at=now.isoformat(),
            metadata={
                'ocr_text': ocr_text if ocr_text else None,
            },
        )

        self._feedback_entries[feedback_id] = entry

        # 통계 업데이트
        self._update_stats(feedback_type)

        # 즉시 학습 처리
        self._process_feedback(entry)

        self._save_data()
        logger.info(f"피드백 제출됨: {feedback_id} ({feedback_type.value})")

        return entry

    def _update_stats(self, feedback_type: FeedbackType) -> None:
        """통계 업데이트"""
        if not self._stats:
            self._stats = LearningStats()

        self._stats.total_feedback += 1

        if feedback_type == FeedbackType.APPROVAL:
            self._stats.approvals += 1
        elif feedback_type == FeedbackType.CORRECTION:
            self._stats.corrections += 1
        elif feedback_type == FeedbackType.REJECTION:
            self._stats.rejections += 1

        # 정확도 계산
        total = self._stats.approvals + self._stats.corrections + self._stats.rejections
        if total > 0:
            self._stats.accuracy_rate = self._stats.approvals / total

        self._stats.last_update = datetime.now(UTC).isoformat()

        # 모드 전환 확인
        self._check_mode_transition()

    def _check_mode_transition(self) -> None:
        """학습 모드 전환 확인"""
        if not self._stats:
            return

        current = self._stats.current_mode

        if current == LearningMode.MANUAL:
            threshold = self.MODE_TRANSITION_THRESHOLD[LearningMode.MANUAL]
            if (self._stats.total_feedback >= threshold['min_feedback'] and
                self._stats.accuracy_rate >= threshold['min_accuracy']):
                self._stats.current_mode = LearningMode.SEMI_AUTO
                logger.info("학습 모드 전환: MANUAL → SEMI_AUTO")

        elif current == LearningMode.SEMI_AUTO:
            threshold = self.MODE_TRANSITION_THRESHOLD[LearningMode.SEMI_AUTO]
            if (self._stats.total_feedback >= threshold['min_feedback'] and
                self._stats.accuracy_rate >= threshold['min_accuracy']):
                self._stats.current_mode = LearningMode.AUTO
                logger.info("학습 모드 전환: SEMI_AUTO → AUTO")

    def _process_feedback(self, entry: FeedbackEntry) -> None:
        """피드백 처리 및 학습"""
        try:
            rag_manager = get_rag_data_manager()
            vector_service = get_rag_vector_service()

            # 데이터 해시 생성
            data_hash = hashlib.sha256(
                json.dumps(entry.original_data, sort_keys=True).encode()
            ).hexdigest()[:16]

            if entry.feedback_type == FeedbackType.APPROVAL:
                # 승인: GOLD 등급으로 RAG 추가
                rag_manager.add_entry(
                    image_hash=data_hash,
                    original_request=json.dumps(entry.original_data, ensure_ascii=False),
                    final_request=json.dumps(entry.original_data, ensure_ascii=False),
                    estimate_id=entry.estimate_id,
                    revision_count=0,
                )

                # 벡터 DB에도 추가
                vector_service.add_document(
                    content=json.dumps(entry.original_data, ensure_ascii=False),
                    category=DocumentCategory.ESTIMATE,
                    metadata={
                        'estimate_id': entry.estimate_id,
                        'tier': 'gold',
                        'feedback_type': 'approval',
                    },
                )

                entry.confidence_after = 1.0

            elif entry.feedback_type == FeedbackType.CORRECTION:
                # 수정: 수정된 데이터로 학습
                if entry.corrected_data:
                    rag_manager.add_entry(
                        image_hash=data_hash,
                        original_request=json.dumps(entry.original_data, ensure_ascii=False),
                        final_request=json.dumps(entry.corrected_data, ensure_ascii=False),
                        estimate_id=entry.estimate_id,
                        revision_count=1,
                    )

                    vector_service.add_document(
                        content=json.dumps(entry.corrected_data, ensure_ascii=False),
                        category=DocumentCategory.ESTIMATE,
                        metadata={
                            'estimate_id': entry.estimate_id,
                            'tier': 'silver',
                            'feedback_type': 'correction',
                            'original_data': json.dumps(entry.original_data, ensure_ascii=False),
                        },
                    )

                entry.confidence_after = 0.7

            elif entry.feedback_type == FeedbackType.REJECTION:
                # 거부: 실패 기록
                existing = rag_manager.find_by_hash(data_hash)
                if existing:
                    rag_manager.update_entry(existing.entry_id, success=False)

                entry.confidence_after = 0.0

            # 피드백 텍스트가 있으면 별도 저장
            if entry.feedback_text:
                vector_service.add_document(
                    content=entry.feedback_text,
                    category=DocumentCategory.FEEDBACK,
                    metadata={
                        'estimate_id': entry.estimate_id,
                        'feedback_type': entry.feedback_type.value,
                    },
                )

            entry.processed = True
            logger.info(f"피드백 처리 완료: {entry.feedback_id}")

        except Exception as e:
            logger.error(f"피드백 처리 실패: {e}")

    def should_auto_approve(self, confidence: float) -> bool:
        """
        자동 승인 여부 확인

        Args:
            confidence: 신뢰도

        Returns:
            자동 승인 가능 여부
        """
        if not self._stats:
            return False

        # 수동 모드에서는 자동 승인 없음
        if self._stats.current_mode == LearningMode.MANUAL:
            return False

        # 반자동: 높은 신뢰도만
        if self._stats.current_mode == LearningMode.SEMI_AUTO:
            return confidence >= self.AUTO_APPROVE_THRESHOLD

        # 자동: 일반 임계값 이상
        return confidence >= self.REVIEW_REQUIRED_THRESHOLD

    def needs_review(self, confidence: float) -> bool:
        """
        검토 필요 여부 확인

        Args:
            confidence: 신뢰도

        Returns:
            검토 필요 여부
        """
        if not self._stats:
            return True

        # 수동 모드: 항상 검토
        if self._stats.current_mode == LearningMode.MANUAL:
            return True

        # 신뢰도 낮으면 검토 필요
        return confidence < self.REVIEW_REQUIRED_THRESHOLD

    def get_stats(self) -> dict:
        """학습 통계 조회"""
        if not self._stats:
            return {}

        return {
            'total_feedback': self._stats.total_feedback,
            'approvals': self._stats.approvals,
            'corrections': self._stats.corrections,
            'rejections': self._stats.rejections,
            'accuracy_rate': round(self._stats.accuracy_rate, 4),
            'current_mode': self._stats.current_mode.value,
            'last_update': self._stats.last_update,
            'mode_thresholds': {
                'manual_to_semi': self.MODE_TRANSITION_THRESHOLD[LearningMode.MANUAL],
                'semi_to_auto': self.MODE_TRANSITION_THRESHOLD[LearningMode.SEMI_AUTO],
            },
            'auto_approve_threshold': self.AUTO_APPROVE_THRESHOLD,
            'review_threshold': self.REVIEW_REQUIRED_THRESHOLD,
        }

    def get_pending_reviews(self, limit: int = 10) -> list[FeedbackEntry]:
        """
        대기 중인 검토 목록

        Args:
            limit: 최대 개수

        Returns:
            검토 대기 피드백 목록
        """
        pending = [
            e for e in self._feedback_entries.values()
            if not e.processed
        ]
        pending.sort(key=lambda x: x.created_at, reverse=True)
        return pending[:limit]

    def get_recent_feedback(self, days: int = 7, limit: int = 50) -> list[FeedbackEntry]:
        """
        최근 피드백 조회

        Args:
            days: 최근 N일
            limit: 최대 개수

        Returns:
            피드백 목록
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        recent = [
            e for e in self._feedback_entries.values()
            if e.created_at >= cutoff
        ]
        recent.sort(key=lambda x: x.created_at, reverse=True)
        return recent[:limit]

    def cleanup_old_data(self, days: int = 180) -> dict:
        """
        오래된 데이터 정리

        Args:
            days: 보관 기간

        Returns:
            정리 결과
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        before_count = len(self._feedback_entries)

        # 오래된 피드백 아카이브
        archived = []
        for feedback_id, entry in list(self._feedback_entries.items()):
            if entry.created_at < cutoff and entry.processed:
                archived.append(entry)
                del self._feedback_entries[feedback_id]

        # 아카이브 저장
        if archived:
            archive_dir = self.DATA_DIR / "archive"
            archive_dir.mkdir(exist_ok=True)
            archive_file = archive_dir / f"feedback_archive_{datetime.now(UTC).strftime('%Y%m%d')}.json"

            try:
                existing = []
                if archive_file.exists():
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)

                existing.extend([
                    {
                        'feedback_id': e.feedback_id,
                        'estimate_id': e.estimate_id,
                        'feedback_type': e.feedback_type.value,
                        'created_at': e.created_at,
                    }
                    for e in archived
                ])

                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"아카이브 저장 실패: {e}")

        self._save_data()

        return {
            'before_count': before_count,
            'after_count': len(self._feedback_entries),
            'archived': len(archived),
        }

    def set_mode(self, mode: LearningMode) -> bool:
        """
        학습 모드 수동 설정 (테스트용)

        Args:
            mode: 학습 모드

        Returns:
            성공 여부
        """
        if not self._stats:
            return False

        self._stats.current_mode = mode
        self._save_data()
        logger.info(f"학습 모드 수동 설정: {mode.value}")
        return True


# 싱글톤 인스턴스 접근
_service: Optional[AILearningService] = None


def get_ai_learning_service() -> AILearningService:
    """AILearningService 싱글톤"""
    global _service
    if _service is None:
        _service = AILearningService()
    return _service
