"""
Vision AI API Routes (Phase XIV)

도면/사진 분석 및 자동 견적 생성 API 엔드포인트
Contract-First 원칙에 따라 정의된 API 계약을 구현합니다.

엔드포인트:
- POST /v1/vision/analyze         - 이미지 분석
- POST /v1/vision/estimate        - 분석 결과로 견적 생성
- GET  /v1/vision/history         - 분석 이력 조회
- GET  /v1/vision/estimate/{id}   - 생성된 견적 조회
- GET  /v1/vision/stats           - 통계 조회
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from kis_estimator_core.api.schemas.vision import (
    ImageAttachment,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    VisionEstimateRequest,
    VisionEstimateResponse,
    VisionHistoryResponse,
    VisionAnalysisHistoryItem,
    ImageAnalysisResult,
    ExtractedPanel,
    ExtractedBreaker,
    ExtractedEnclosure,
    ExtractedCustomer,
    VisionEstimatePanel,
    VisionEstimateItem,
)
from kis_estimator_core.services.vision_analysis_service import (
    get_vision_service,
    VisionAnalysisService,
)
from kis_estimator_core.services.vision_estimate_service import (
    get_vision_estimate_service,
    VisionEstimateService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision AI"])


# ============================================================================
# Helper Functions
# ============================================================================

def _convert_analysis_result(result) -> ImageAnalysisResult:
    """내부 분석 결과를 API 응답 스키마로 변환"""
    panels = []
    for panel in result.panels:
        # 외함 변환
        enclosure = None
        if panel.enclosure:
            enclosure = ExtractedEnclosure(
                type=panel.enclosure.enclosure_type,
                material=panel.enclosure.material,
                thickness=panel.enclosure.thickness,
                width=panel.enclosure.width,
                height=panel.enclosure.height,
                depth=panel.enclosure.depth,
                confidence=panel.enclosure.confidence
            )

        # 메인 차단기 변환
        main_breaker = None
        if panel.main_breaker:
            main_breaker = ExtractedBreaker(
                type=panel.main_breaker.breaker_type,
                brand=panel.main_breaker.brand,
                pole=panel.main_breaker.pole,
                frame=panel.main_breaker.frame,
                ampere=panel.main_breaker.ampere,
                quantity=1,
                is_main=True,
                confidence=panel.main_breaker.confidence
            )

        # 분기 차단기 변환
        branch_breakers = [
            ExtractedBreaker(
                type=b.breaker_type,
                brand=b.brand,
                pole=b.pole,
                frame=b.frame,
                ampere=b.ampere,
                quantity=b.quantity,
                is_main=False,
                confidence=b.confidence
            )
            for b in panel.branch_breakers
        ]

        panels.append(ExtractedPanel(
            panel_name=panel.panel_name,
            enclosure=enclosure,
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=panel.accessories,
            notes=panel.notes,
            confidence=panel.confidence
        ))

    customer = None
    if result.customer_name or result.project_name:
        customer = ExtractedCustomer(
            name=result.customer_name,
            project_name=result.project_name,
            confidence="MEDIUM"
        )

    return ImageAnalysisResult(
        image_id=result.image_id,
        image_type=result.image_type,
        panels=panels,
        customer=customer,
        raw_text=result.raw_text,
        warnings=result.warnings,
        processing_time_ms=result.processing_time_ms
    )


def _convert_estimate_panel(panel) -> VisionEstimatePanel:
    """내부 견적 패널을 API 응답 스키마로 변환"""
    items = [
        VisionEstimateItem(
            category=item.category,
            name=item.name,
            specification=item.specification,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            source=item.source,
            confidence=item.confidence
        )
        for item in panel.items
    ]

    return VisionEstimatePanel(
        panel_name=panel.panel_name,
        items=items,
        subtotal=panel.subtotal,
        notes=panel.notes
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/analyze",
    response_model=VisionAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="이미지 분석",
    description="도면/사진을 분석하여 전기 패널 구성요소를 추출합니다."
)
async def analyze_images(request: VisionAnalyzeRequest):
    """
    도면/사진 분석

    - 여러 이미지를 동시에 분석 가능
    - 차단기, 외함, 부속자재 자동 인식
    - 신뢰도 점수 제공
    """
    logger.info(f"Vision 분석 요청: {len(request.images)}개 이미지")

    try:
        service = get_vision_service()

        # 이미지 변환
        images = [
            {
                "id": img.id,
                "name": img.name,
                "type": img.type,
                "url": img.url
            }
            for img in request.images
        ]

        # 분석 수행
        analysis = await service.analyze_multiple_images(
            images=images,
            user_hint=request.user_hint
        )

        # 결과 변환
        results = [
            _convert_analysis_result(r)
            for r in analysis.get("results", [])
        ]

        # 병합된 분전반 변환
        merged_panels = []
        for panel in analysis.get("merged_panels", []):
            # 이미 ExtractedPanel 객체인 경우
            if hasattr(panel, 'panel_name'):
                enclosure = None
                if panel.enclosure:
                    enclosure = ExtractedEnclosure(
                        type=panel.enclosure.enclosure_type,
                        material=panel.enclosure.material,
                        thickness=panel.enclosure.thickness,
                        width=panel.enclosure.width,
                        height=panel.enclosure.height,
                        depth=panel.enclosure.depth,
                        confidence=panel.enclosure.confidence
                    )

                main_breaker = None
                if panel.main_breaker:
                    main_breaker = ExtractedBreaker(
                        type=panel.main_breaker.breaker_type,
                        brand=panel.main_breaker.brand,
                        pole=panel.main_breaker.pole,
                        frame=panel.main_breaker.frame,
                        ampere=panel.main_breaker.ampere,
                        quantity=1,
                        is_main=True,
                        confidence=panel.main_breaker.confidence
                    )

                branch_breakers = [
                    ExtractedBreaker(
                        type=b.breaker_type,
                        brand=b.brand,
                        pole=b.pole,
                        frame=b.frame,
                        ampere=b.ampere,
                        quantity=b.quantity,
                        is_main=False,
                        confidence=b.confidence
                    )
                    for b in panel.branch_breakers
                ]

                merged_panels.append(ExtractedPanel(
                    panel_name=panel.panel_name,
                    enclosure=enclosure,
                    main_breaker=main_breaker,
                    branch_breakers=branch_breakers,
                    accessories=panel.accessories,
                    notes=panel.notes,
                    confidence=panel.confidence
                ))

        return VisionAnalyzeResponse(
            request_id=analysis.get("request_id", ""),
            status=analysis.get("status", "SUCCESS"),
            results=results,
            merged_panels=merged_panels,
            total_breakers=analysis.get("total_breakers", 0),
            total_panels=analysis.get("total_panels", 0),
            overall_confidence=analysis.get("overall_confidence", "MEDIUM"),
            message=analysis.get("message", "분석 완료"),
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Vision 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 분석 중 오류 발생: {str(e)}"
        )


@router.post(
    "/estimate",
    response_model=VisionEstimateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vision 기반 견적 생성",
    description="분석 결과를 바탕으로 자동으로 견적을 생성합니다."
)
async def generate_estimate(request: VisionEstimateRequest):
    """
    Vision 기반 자동 견적 생성

    - 이미지 분석 + 견적 생성 통합
    - CEO 학습된 선호도 자동 적용
    - 부속자재 자동 추가
    """
    logger.info("Vision 견적 생성 요청")

    try:
        vision_service = get_vision_service()
        estimate_service = get_vision_estimate_service()

        # 이미지 분석 (새 분석이 필요한 경우)
        if request.images:
            images = [
                {
                    "id": img.id,
                    "name": img.name,
                    "type": img.type,
                    "url": img.url
                }
                for img in request.images
            ]

            analysis_result = await vision_service.analyze_multiple_images(images=images)
        elif request.analysis_result_id:
            # 기존 분석 결과 사용
            cached_result = await vision_service.get_analysis_result(request.analysis_result_id)
            if not cached_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"분석 결과를 찾을 수 없습니다: {request.analysis_result_id}"
                )
            analysis_result = {"results": [cached_result], "merged_panels": cached_result.panels}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 또는 분석 결과 ID가 필요합니다"
            )

        # 견적 생성
        estimate = await estimate_service.generate_estimate(
            analysis_result=analysis_result,
            customer_name=request.customer_name,
            project_name=request.project_name,
            apply_ceo_preferences=request.apply_ceo_preferences,
            brand_override=request.brand_override
        )

        # 응답 변환
        panels = [_convert_estimate_panel(p) for p in estimate.panels]

        return VisionEstimateResponse(
            estimate_id=estimate.estimate_id,
            request_id=estimate.request_id,
            customer_name=estimate.customer_name,
            project_name=estimate.project_name,
            panels=panels,
            total_amount=estimate.total_amount,
            total_with_vat=estimate.total_with_vat,
            ceo_preferences_applied=estimate.ceo_preferences_applied,
            confidence_summary=estimate.confidence_summary,
            warnings=estimate.warnings,
            generated_at=estimate.generated_at,
            message=f"견적이 성공적으로 생성되었습니다. 합계: {estimate.total_amount:,}원 (VAT 별도)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision 견적 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"견적 생성 중 오류 발생: {str(e)}"
        )


@router.get(
    "/history",
    response_model=VisionHistoryResponse,
    summary="분석 이력 조회",
    description="Vision AI 분석 이력을 조회합니다."
)
async def get_analysis_history(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """분석 이력 조회"""
    try:
        service = get_vision_service()
        stats = service.get_stats()

        # 실제 구현에서는 저장된 이력을 페이징해서 반환
        # 현재는 통계만 반환
        return VisionHistoryResponse(
            history=[],
            total=stats.get("total_analyses", 0),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"분석 이력 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이력 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/estimate/{estimate_id}",
    response_model=VisionEstimateResponse,
    summary="생성된 견적 조회",
    description="Vision AI로 생성된 견적을 조회합니다."
)
async def get_estimate(estimate_id: str):
    """생성된 견적 조회"""
    try:
        service = get_vision_estimate_service()
        estimate = await service.get_estimate(estimate_id)

        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"견적을 찾을 수 없습니다: {estimate_id}"
            )

        panels = [_convert_estimate_panel(p) for p in estimate.panels]

        return VisionEstimateResponse(
            estimate_id=estimate.estimate_id,
            request_id=estimate.request_id,
            customer_name=estimate.customer_name,
            project_name=estimate.project_name,
            panels=panels,
            total_amount=estimate.total_amount,
            total_with_vat=estimate.total_with_vat,
            ceo_preferences_applied=estimate.ceo_preferences_applied,
            confidence_summary=estimate.confidence_summary,
            warnings=estimate.warnings,
            generated_at=estimate.generated_at,
            message="견적 조회 완료"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"견적 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"견적 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Vision AI 통계",
    description="Vision AI 시스템 통계를 조회합니다."
)
async def get_vision_stats():
    """Vision AI 통계 조회"""
    try:
        vision_service = get_vision_service()
        estimate_service = get_vision_estimate_service()

        vision_stats = vision_service.get_stats()
        estimate_stats = estimate_service.get_stats()

        return {
            "vision": vision_stats,
            "estimates": estimate_stats,
            "message": "통계 조회 완료"
        }

    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류 발생: {str(e)}"
        )
