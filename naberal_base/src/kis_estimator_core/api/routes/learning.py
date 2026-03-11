"""
AI Self-Learning System API Routes (Phase XIII)

CEO 견적 수정 이력 학습 및 패턴 분석 API 엔드포인트
Contract-First 원칙에 따라 정의된 API 계약을 구현합니다.

엔드포인트:
- GET  /v1/learning/modifications     - 수정 이력 조회
- POST /v1/learning/modifications     - 수정 이력 캡처
- GET  /v1/learning/patterns          - 학습된 패턴 조회
- POST /v1/learning/patterns          - 수동 패턴 생성
- POST /v1/learning/patterns/detect   - 패턴 감지 실행
- GET  /v1/learning/profile/{user_id} - CEO 프로파일 조회
- POST /v1/learning/profile/{user_id}/learn - CEO 프로파일 학습
- GET  /v1/learning/recommendations   - 추천 조회
- POST /v1/learning/knowledge/generate - 지식 자동 생성
- GET  /v1/learning/stats             - 학습 시스템 통계
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from kis_estimator_core.api.schemas.learning import (
    CEOProfileResponse,
    EstimateModificationRecord,
    KnowledgeGenRequest,
    KnowledgeGenResponse,
    GeneratedKnowledge,
    LearningStatsResponse,
    ManualPatternRequest,
    ModificationListResponse,
    PatternCreateResponse,
    PatternResponse,
    PatternsResponse,
)
from kis_estimator_core.services.modification_audit_service import (
    get_audit_service,
    ModificationAuditService,
)
from kis_estimator_core.services.pattern_detector_service import (
    get_pattern_detector,
    PatternDetectorService,
)
from kis_estimator_core.services.knowledge_generator_service import (
    get_knowledge_generator,
    KnowledgeGeneratorService,
)
from kis_estimator_core.services.ceo_profile_service import (
    get_ceo_profile_service,
    CEOProfileService,
)

# 인증 의존성 (옵션: CEO 전용 기능에서 사용)
try:
    from kis_estimator_core.api.routes.auth import get_current_user, require_ceo
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["AI Self-Learning"])


# ============================================================================
# 의존성
# ============================================================================

def get_audit() -> ModificationAuditService:
    """수정 감사 서비스 의존성"""
    return get_audit_service()


def get_detector() -> PatternDetectorService:
    """패턴 감지 서비스 의존성"""
    return get_pattern_detector()


def get_generator() -> KnowledgeGeneratorService:
    """지식 생성 서비스 의존성"""
    return get_knowledge_generator()


def get_profile_service() -> CEOProfileService:
    """CEO 프로파일 서비스 의존성"""
    return get_ceo_profile_service()


# ============================================================================
# 수정 이력 API
# ============================================================================

@router.get(
    "/modifications",
    response_model=ModificationListResponse,
    summary="수정 이력 조회",
    description="CEO의 견적 수정 이력을 조회합니다."
)
async def get_modifications(
    estimate_id: Optional[str] = Query(None, description="견적 ID 필터"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    limit: int = Query(50, ge=1, le=200, description="최대 반환 개수"),
    audit: ModificationAuditService = Depends(get_audit)
):
    """수정 이력 조회"""
    modifications = await audit.get_modifications(
        estimate_id=estimate_id,
        user_id=user_id,
        limit=limit
    )

    records = [
        EstimateModificationRecord(
            modification_id=m.modification_id,
            estimate_id=m.estimate_id,
            user_id=m.user_id,
            modified_fields=m.modified_fields,
            diff=m.diff,
            reason=m.reason,
            timestamp=m.timestamp,
            evidence_hash=m.evidence_hash
        )
        for m in modifications
    ]

    return ModificationListResponse(
        modifications=records,
        total=len(records),
        meta=audit.get_stats()
    )


@router.post(
    "/modifications",
    response_model=EstimateModificationRecord,
    status_code=status.HTTP_201_CREATED,
    summary="수정 이력 캡처",
    description="견적 수정 내역을 캡처하고 저장합니다."
)
async def capture_modification(
    estimate_id: str,
    user_id: str,
    before: dict,
    after: dict,
    reason: Optional[str] = None,
    audit: ModificationAuditService = Depends(get_audit)
):
    """수정 이력 캡처"""
    modification = await audit.capture_modification(
        estimate_id=estimate_id,
        before=before,
        after=after,
        user_id=user_id,
        reason=reason
    )

    return EstimateModificationRecord(
        modification_id=modification.modification_id,
        estimate_id=modification.estimate_id,
        user_id=modification.user_id,
        modified_fields=modification.modified_fields,
        diff=modification.diff,
        reason=modification.reason,
        timestamp=modification.timestamp,
        evidence_hash=modification.evidence_hash
    )


# ============================================================================
# 패턴 API
# ============================================================================

@router.get(
    "/patterns",
    response_model=PatternsResponse,
    summary="학습된 패턴 조회",
    description="감지된 패턴 목록을 조회합니다."
)
async def get_patterns(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="최소 신뢰도"),
    limit: int = Query(50, ge=1, le=200, description="최대 반환 개수"),
    detector: PatternDetectorService = Depends(get_detector)
):
    """패턴 조회"""
    patterns = await detector.get_patterns(
        category=category,
        min_confidence=min_confidence,
        limit=limit
    )

    pattern_responses = [
        PatternResponse(
            pattern_id=p.pattern_id,
            category=p.category,
            condition=p.condition,
            action=p.action,
            confidence=p.confidence,
            occurrences=p.occurrences,
            last_seen=p.last_seen
        )
        for p in patterns
    ]

    return PatternsResponse(
        patterns=pattern_responses,
        total=len(pattern_responses),
        meta=detector.get_stats()
    )


@router.post(
    "/patterns",
    response_model=PatternCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="수동 패턴 생성",
    description="수동으로 패턴을 생성합니다."
)
async def create_pattern(
    request: ManualPatternRequest,
    detector: PatternDetectorService = Depends(get_detector)
):
    """수동 패턴 생성"""
    pattern = await detector._create_or_update_pattern(
        category=request.category,
        condition=request.condition,
        action=request.action,
        evidence_hashes=[]
    )

    return PatternCreateResponse(
        pattern_id=pattern.pattern_id,
        category=pattern.category,
        message=f"패턴이 생성되었습니다. 신뢰도: {pattern.confidence}"
    )


@router.post(
    "/patterns/detect",
    response_model=PatternsResponse,
    summary="패턴 감지 실행",
    description="저장된 수정 이력에서 패턴을 감지합니다."
)
async def detect_patterns(
    limit: int = Query(100, ge=1, le=500, description="분석할 수정 이력 수"),
    audit: ModificationAuditService = Depends(get_audit),
    detector: PatternDetectorService = Depends(get_detector)
):
    """패턴 감지 실행"""
    # 수정 이력 조회
    modifications = await audit.get_modifications(limit=limit)

    # 딕셔너리 변환
    mod_dicts = [
        {
            "modification_id": m.modification_id,
            "estimate_id": m.estimate_id,
            "user_id": m.user_id,
            "before_snapshot": m.before_snapshot,
            "after_snapshot": m.after_snapshot,
            "diff": m.diff,
            "modified_fields": m.modified_fields,
            "evidence_hash": m.evidence_hash
        }
        for m in modifications
    ]

    # 패턴 감지
    detected = await detector.detect_patterns_from_modifications(mod_dicts)

    pattern_responses = [
        PatternResponse(
            pattern_id=p.pattern_id,
            category=p.category,
            condition=p.condition,
            action=p.action,
            confidence=p.confidence,
            occurrences=p.occurrences,
            last_seen=p.last_seen
        )
        for p in detected
    ]

    return PatternsResponse(
        patterns=pattern_responses,
        total=len(pattern_responses),
        meta={"analyzed_modifications": len(mod_dicts)}
    )


# ============================================================================
# CEO 프로파일 API
# ============================================================================

@router.get(
    "/profile/{user_id}",
    response_model=CEOProfileResponse,
    summary="CEO 프로파일 조회",
    description="CEO의 학습된 선호도 프로파일을 조회합니다."
)
async def get_ceo_profile(
    user_id: str,
    profile_service: CEOProfileService = Depends(get_profile_service)
):
    """CEO 프로파일 조회"""
    profile = await profile_service.get_profile(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"프로파일을 찾을 수 없습니다: {user_id}"
        )

    preferences = [
        {
            "category": p.category,
            "key": p.key,
            "value": p.value,
            "confidence": p.confidence,
            "sample_size": p.sample_size
        }
        for p in profile.preferences
    ]

    return CEOProfileResponse(
        user_id=profile.user_id,
        brand_preferences=profile.brand_preferences,
        price_thresholds=profile.price_thresholds,
        layout_style=profile.layout_style,
        preferences=preferences,
        sample_size=profile.sample_size,
        last_updated=profile.last_updated
    )


@router.post(
    "/profile/{user_id}/learn",
    response_model=CEOProfileResponse,
    summary="CEO 프로파일 학습",
    description="수정 이력에서 CEO 선호도를 학습합니다."
)
async def learn_ceo_profile(
    user_id: str,
    limit: int = Query(100, ge=1, le=500, description="학습할 수정 이력 수"),
    audit: ModificationAuditService = Depends(get_audit),
    profile_service: CEOProfileService = Depends(get_profile_service)
):
    """CEO 프로파일 학습"""
    # 해당 사용자의 수정 이력 조회
    modifications = await audit.get_modifications(user_id=user_id, limit=limit)

    # 딕셔너리 변환
    mod_dicts = [
        {
            "before_snapshot": m.before_snapshot,
            "after_snapshot": m.after_snapshot,
            "diff": m.diff,
            "modified_fields": m.modified_fields
        }
        for m in modifications
    ]

    # 학습 실행
    profile = await profile_service.learn_from_modifications(user_id, mod_dicts)

    preferences = [
        {
            "category": p.category,
            "key": p.key,
            "value": p.value,
            "confidence": p.confidence,
            "sample_size": p.sample_size
        }
        for p in profile.preferences
    ]

    return CEOProfileResponse(
        user_id=profile.user_id,
        brand_preferences=profile.brand_preferences,
        price_thresholds=profile.price_thresholds,
        layout_style=profile.layout_style,
        preferences=preferences,
        sample_size=profile.sample_size,
        last_updated=profile.last_updated
    )


@router.get(
    "/recommendations",
    summary="추천 조회",
    description="CEO 프로파일 기반 견적 추천을 조회합니다."
)
async def get_recommendations(
    user_id: str = Query(..., description="CEO 사용자 ID"),
    pole: Optional[str] = Query(None, description="극수 (예: 4P)"),
    frame: Optional[str] = Query(None, description="프레임 (예: 100AF)"),
    profile_service: CEOProfileService = Depends(get_profile_service)
):
    """추천 조회"""
    breaker_spec = {}
    if pole:
        breaker_spec["pole"] = pole
    if frame:
        breaker_spec["frame"] = frame

    recommendation = await profile_service.get_recommendation(user_id, breaker_spec)

    return recommendation


# ============================================================================
# 지식 생성 API
# ============================================================================

@router.post(
    "/knowledge/generate",
    response_model=KnowledgeGenResponse,
    summary="지식 자동 생성",
    description="감지된 패턴에서 RAG 지식을 자동으로 생성합니다."
)
async def generate_knowledge(
    request: KnowledgeGenRequest,
    detector: PatternDetectorService = Depends(get_detector),
    generator: KnowledgeGeneratorService = Depends(get_generator)
):
    """지식 자동 생성"""
    # 패턴 조회
    patterns = await detector.get_patterns(
        min_confidence=request.min_confidence,
        limit=100
    )

    # 카테고리 필터
    if request.categories:
        patterns = [p for p in patterns if p.category in request.categories]

    # 최소 발생 횟수 필터
    patterns = [p for p in patterns if p.occurrences >= request.min_occurrences]

    # 패턴 딕셔너리 변환
    pattern_dicts = [p.to_dict() for p in patterns]

    # 일괄 생성
    result = await generator.generate_batch(
        patterns=pattern_dicts,
        min_confidence=request.min_confidence,
        dry_run=request.dry_run
    )

    generated_items = [
        GeneratedKnowledge(
            knowledge_type=g.get("knowledge_type", "KNOWHOW"),
            title=g.get("title", ""),
            content=g.get("content", ""),
            tags=g.get("tags", []),
            source_pattern_id=g.get("source_pattern_id", ""),
            confidence=g.get("confidence", 0.0)
        )
        for g in result.get("generated", [])
        if not g.get("preview")  # 미리보기 제외
    ]

    return KnowledgeGenResponse(
        generated=generated_items,
        total_generated=result["total_generated"],
        skipped_duplicates=result["skipped_duplicates"],
        skipped_low_confidence=result["skipped_low_confidence"],
        dry_run=result["dry_run"],
        message=result["message"]
    )


# ============================================================================
# 통계 API
# ============================================================================

@router.get(
    "/stats",
    response_model=LearningStatsResponse,
    summary="학습 시스템 통계",
    description="전체 학습 시스템의 통계를 조회합니다."
)
async def get_learning_stats(
    audit: ModificationAuditService = Depends(get_audit),
    detector: PatternDetectorService = Depends(get_detector),
    generator: KnowledgeGeneratorService = Depends(get_generator)
):
    """학습 시스템 통계"""
    audit_stats = audit.get_stats()
    pattern_stats = detector.get_stats()
    knowledge_stats = generator.get_stats()

    return LearningStatsResponse(
        total_modifications=audit_stats.get("total", 0),
        total_patterns=pattern_stats.get("total", 0),
        patterns_by_category=pattern_stats.get("by_category", {}),
        avg_confidence=pattern_stats.get("avg_confidence", 0.0),
        total_knowledge_generated=knowledge_stats.get("total", 0),
        last_pattern_detected=pattern_stats.get("latest"),
        last_knowledge_generated=knowledge_stats.get("latest")
    )
