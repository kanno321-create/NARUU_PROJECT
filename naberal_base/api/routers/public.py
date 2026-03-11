"""
Public API Router - 비인증 공개 엔드포인트

hkkor.com 공개 사이트에서 호출하는 API:
1. POST /v1/public/estimates - AI 견적 (rate limit: 10/min per IP)
2. POST /v1/public/inquiries - 문의 접수 (rate limit: 5/min per IP)
3. GET  /v1/public/products  - 제품 카탈로그 (공개)
"""

import logging
import time
import json
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/public", tags=["public"])


# ============================================================================
# Per-Endpoint Rate Limiter (in-memory, IP-based)
# ============================================================================

_rate_buckets: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))


def _check_rate_limit(request: Request, endpoint: str, max_per_minute: int):
    """IP별 엔드포인트 rate limit 체크 (슬라이딩 윈도우)"""
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    now = time.time()
    window = 60  # 1분

    # 만료된 타임스탬프 정리
    bucket = _rate_buckets[endpoint][client_ip]
    _rate_buckets[endpoint][client_ip] = [t for t in bucket if now - t < window]
    bucket = _rate_buckets[endpoint][client_ip]

    if len(bucket) >= max_per_minute:
        retry_after = int(window - (now - bucket[0])) + 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"분당 {max_per_minute}회 제한 초과. {retry_after}초 후 다시 시도해주세요.",
                "retry_after_seconds": retry_after,
            },
        )

    bucket.append(now)


# ============================================================================
# Request/Response Models
# ============================================================================


class PublicBreakerSpec(BaseModel):
    """공개 견적용 차단기 스펙"""
    type: str = Field(default="MCCB", description="차단기 종류 (MCCB/ELB)")
    poles: int = Field(..., ge=2, le=4, description="극수 (2/3/4)")
    current: int = Field(..., gt=0, le=1000, description="전류 (A)")
    frame: int = Field(..., gt=0, le=1000, description="프레임 (AF)")


class PublicAccessory(BaseModel):
    """공개 견적용 부속자재"""
    type: str = Field(..., description="자재 종류")
    quantity: int = Field(default=1, ge=1, description="수량")


class PublicEstimateRequest(BaseModel):
    """공개 AI 견적 요청"""
    panel_usage: str = Field(default="일반", description="분전반 용도")
    install_location: str = Field(..., description="설치 위치 (옥내노출/옥외노출/옥내자립/옥외자립/매입함)")
    enclosure_material: str = Field(default="STEEL 1.6T", description="외함 재질 (STEEL 1.6T, SUS201 1.2T 등)")
    breaker_brand: str = Field(default="상도", description="차단기 브랜드 (상도/LS)")
    breaker_grade: str = Field(default="경제형", description="차단기 등급 (경제형/표준형)")
    main_breaker: PublicBreakerSpec = Field(..., description="메인 차단기")
    branch_breakers: List[PublicBreakerSpec] = Field(
        default_factory=list, description="분기 차단기"
    )
    accessories: List[PublicAccessory] = Field(
        default_factory=list, description="부속자재"
    )
    customer_name: str = Field(default="웹사이트 고객", description="고객명")
    project_name: str = Field(default="온라인 견적", description="프로젝트명")
    contact_phone: str = Field(default="", description="연락처")


class PublicEstimateResponse(BaseModel):
    """공개 AI 견적 응답"""
    estimate_id: str
    success: bool
    total_amount: Optional[int] = None
    line_items: List[Dict[str, Any]] = []
    validation_checks: Dict[str, Any] = {}
    created_at: str
    message: str = ""


class InquiryRequest(BaseModel):
    """문의 접수 요청"""
    name: str = Field(..., min_length=1, max_length=100, description="이름")
    email: str = Field(default="", description="이메일")
    phone: str = Field(default="", description="전화번호")
    company: str = Field(default="", description="회사명")
    inquiry_type: str = Field(
        default="general", description="문의 유형 (estimate/order/technical/general)"
    )
    subject: str = Field(..., min_length=1, max_length=200, description="제목")
    message: str = Field(..., min_length=1, max_length=5000, description="내용")
    estimate_id: Optional[str] = Field(None, description="관련 견적 ID")


class InquiryResponse(BaseModel):
    """문의 접수 응답"""
    inquiry_id: str
    status: str = "received"
    message: str


class PublicProduct(BaseModel):
    """공개 제품 정보"""
    slug: str
    name: str
    category: str
    description: str
    specs: List[str] = []
    features: List[str] = []


# ============================================================================
# POST /v1/public/estimates - 공개 AI 견적
# ============================================================================


@router.post("/estimates", response_model=PublicEstimateResponse, status_code=201)
async def create_public_estimate(
    request: Request,
    body: PublicEstimateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    비인증 공개 AI 견적 생성 (rate limit: 10/min per IP)

    프론트엔드 EstimateWizard에서 호출.
    내부적으로 KPEW plan → execute 파이프라인 실행.
    """
    _check_rate_limit(request, "public_estimates", max_per_minute=10)

    try:
        from kis_estimator_core.services.plan_service import PlanService
        from kis_estimator_core.repos.plan_repo import PlanRepo
        from kis_estimator_core.kpew.execution.executor import EPDLExecutor

        # 1. BreakerSpec 변환
        main_breaker = {
            "poles": body.main_breaker.poles,
            "current": body.main_breaker.current,
            "frame": body.main_breaker.frame,
        }
        branch_breakers = [
            {"poles": b.poles, "current": b.current, "frame": b.frame}
            for b in body.branch_breakers
        ]
        accessories = [
            {"type": a.type, "quantity": a.quantity}
            for a in body.accessories
        ]

        # 2. 외함 종류 — 프론트엔드에서 한국어로 직접 전달
        valid_locations = {"옥내노출", "옥외노출", "옥내자립", "옥외자립", "매입함"}
        enclosure_type = body.install_location if body.install_location in valid_locations else "옥내노출"

        # 3. 차단기 브랜드 매핑
        brand_map = {"상도": "상도차단기", "LS": "LS산전"}
        breaker_brand = brand_map.get(body.breaker_brand, "상도차단기")

        # 4. VerbSpec 생성
        verb_specs = PlanService.create_verb_specs(
            customer_name=body.customer_name or "웹사이트 고객",
            project_name=body.project_name or "온라인 견적",
            enclosure_type=enclosure_type,
            enclosure_material=body.enclosure_material or "STEEL 1.6T",
            breaker_brand=breaker_brand,
            breaker_grade=body.breaker_grade or "경제형",
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=accessories,
        )

        # 4. 검증
        is_valid, errors = PlanService.validate_verb_specs(verb_specs)
        if not is_valid:
            return PublicEstimateResponse(
                estimate_id="",
                success=False,
                created_at=datetime.now().isoformat() + "Z",
                message=f"입력 검증 실패: {', '.join(errors[:3])}",
            )

        # 5. Plan ID 생성 + DB 저장
        plan_id = f"PUB-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        repo = PlanRepo(db)
        await repo.save_plan(plan_id, verb_specs)

        # 6. 파이프라인 실행
        executor = EPDLExecutor()
        context = {
            "enclosure_type": enclosure_type,
            "enclosure_material": body.enclosure_material or "STEEL 1.6T",
            "breaker_brand": breaker_brand,
            "breaker_grade": body.breaker_grade or "경제형",
        }
        exec_result = await executor.execute({"steps": verb_specs}, context)

        # 7. 결과에서 line_items, total 추출
        line_items = []
        total_amount = 0
        for stage in exec_result.get("stages", []):
            output = stage.get("output", {})
            if isinstance(output, dict):
                items = output.get("line_items", [])
                if items:
                    line_items.extend(items)
                stage_total = output.get("total_amount", 0)
                if stage_total:
                    total_amount = stage_total

        # 8. 실행 이력 저장
        for stage in exec_result.get("stages", []):
            try:
                await db.execute(
                    text("""
                        INSERT INTO execution_history
                        (estimate_id, stage_number, stage_name, status,
                         started_at, completed_at, duration_ms,
                         stage_output, quality_gate_passed)
                        VALUES (:estimate_id, :stage_number, :stage_name, :status,
                                timezone('utc', now()), timezone('utc', now()), :duration_ms,
                                :stage_output, :quality_gate_passed)
                    """),
                    {
                        "estimate_id": plan_id,
                        "stage_number": stage["stage_number"],
                        "stage_name": stage["stage_name"],
                        "status": stage["status"],
                        "duration_ms": stage.get("duration_ms", 0),
                        "stage_output": json.dumps(
                            stage.get("output", {}), ensure_ascii=False
                        ),
                        "quality_gate_passed": stage.get("quality_gate_passed", False),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to save execution history for stage {stage['stage_number']}: {e}")

        await db.commit()

        return PublicEstimateResponse(
            estimate_id=plan_id,
            success=exec_result.get("success", False),
            total_amount=total_amount or None,
            line_items=line_items,
            validation_checks={
                "all_passed": exec_result.get("success", False),
                "stages_completed": len(exec_result.get("stages", [])),
                "total_stages": 8,
            },
            created_at=datetime.now().isoformat() + "Z",
            message="견적이 성공적으로 생성되었습니다." if exec_result.get("success") else "견적 생성 중 일부 오류가 발생했습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Public estimate error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "PUBLIC_ESTIMATE_ERROR",
                "message": f"견적 생성 실패: {str(e)}",
                "traceId": str(uuid.uuid4()),
            },
        )


# ============================================================================
# POST /v1/public/inquiries - 문의 접수
# ============================================================================


@router.post("/inquiries", response_model=InquiryResponse, status_code=201)
async def create_inquiry(
    request: Request,
    body: InquiryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    고객 문의 접수 (rate limit: 5/min per IP)

    DB에 저장하고 관리자에게 알림.
    """
    _check_rate_limit(request, "public_inquiries", max_per_minute=5)

    try:
        inquiry_id = f"INQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # inquiries 테이블 없으면 에러 방지 - 테이블 존재 확인
        try:
            await db.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS public_inquiries (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT DEFAULT '',
                        phone TEXT DEFAULT '',
                        company TEXT DEFAULT '',
                        inquiry_type TEXT DEFAULT 'general',
                        subject TEXT NOT NULL,
                        message TEXT NOT NULL,
                        estimate_id TEXT,
                        status TEXT DEFAULT 'received',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        resolved_at TIMESTAMPTZ
                    )
                """)
            )
        except Exception:
            pass  # 이미 존재하면 무시

        await db.execute(
            text("""
                INSERT INTO public_inquiries
                (id, name, email, phone, company, inquiry_type, subject, message, estimate_id)
                VALUES (:id, :name, :email, :phone, :company, :inquiry_type, :subject, :message, :estimate_id)
            """),
            {
                "id": inquiry_id,
                "name": body.name,
                "email": body.email,
                "phone": body.phone,
                "company": body.company,
                "inquiry_type": body.inquiry_type,
                "subject": body.subject,
                "message": body.message,
                "estimate_id": body.estimate_id,
            },
        )
        await db.commit()

        logger.info(f"New inquiry received: {inquiry_id} from {body.name}")

        return InquiryResponse(
            inquiry_id=inquiry_id,
            status="received",
            message="문의가 접수되었습니다. 담당자가 확인 후 연락드리겠습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Inquiry creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INQUIRY_ERROR",
                "message": f"문의 접수 실패: {str(e)}",
                "traceId": str(uuid.uuid4()),
            },
        )


# ============================================================================
# GET /v1/public/products - 공개 제품 카탈로그
# ============================================================================

PRODUCT_CATALOG: List[Dict[str, Any]] = [
    {
        "slug": "steel-enclosure",
        "name": "철 기성함",
        "category": "기성함",
        "description": "KS C 4510 표준 준수 철제 외함. 분체도장 처리로 내식성 우수.",
        "specs": ["KS C 4510", "분체도장", "1.6T~2.0T 강판"],
        "features": ["표준 규격 재고 보유", "당일 출하 가능", "맞춤 제작 대응"],
    },
    {
        "slug": "stainless-enclosure",
        "name": "스테인리스 기성함",
        "category": "기성함",
        "description": "SUS 304 재질 외함. 해안가, 화학공장 등 부식 환경에 적합.",
        "specs": ["SUS 304", "헤어라인 마감", "1.5T~2.0T"],
        "features": ["내부식성 우수", "고급 외관", "반영구적 수명"],
    },
    {
        "slug": "meter-box",
        "name": "계량기함",
        "category": "계량기함",
        "description": "한전 규격 계량기함. CT/PT 내장형, 단독/집합형.",
        "specs": ["한전 규격", "IP44 이상", "CT/PT 내장"],
        "features": ["한전 검정 대응", "잠금장치 표준", "다양한 크기"],
    },
    {
        "slug": "distribution-panel",
        "name": "기성 분전반",
        "category": "분전반",
        "description": "IEC 61439 표준 기성 분전반. MCCB/ELB 장착 완제품.",
        "specs": ["IEC 61439", "KS C 4510", "MCCB/ELB 장착"],
        "features": ["즉시 설치 가능", "AI 견적 지원", "전국 배송"],
    },
    {
        "slug": "ev-panel",
        "name": "전기차 충전 분전반",
        "category": "분전반",
        "description": "전기차 충전기 전용 분전반. SPD, 누전차단기 기본 장착.",
        "specs": ["KC 인증", "SPD 내장", "ELB 필수"],
        "features": ["충전기 호환성", "과전류 보호", "접지 강화"],
    },
    {
        "slug": "solar-panel",
        "name": "태양광 분전반",
        "category": "분전반",
        "description": "태양광 발전 시스템용 연계 분전반. 역전력 보호 기능.",
        "specs": ["KS C 8567", "역전력 계전기", "DC 차단기"],
        "features": ["계통 연계", "역전력 보호", "모니터링 대응"],
    },
]


@router.get("/products", response_model=List[PublicProduct])
async def get_products(category: Optional[str] = None):
    """공개 제품 카탈로그 조회"""
    products = PRODUCT_CATALOG
    if category:
        products = [p for p in products if p["category"] == category]

    return [PublicProduct(**p) for p in products]


@router.get("/products/{slug}", response_model=PublicProduct)
async def get_product_detail(slug: str):
    """공개 제품 상세 조회"""
    for p in PRODUCT_CATALOG:
        if p["slug"] == slug:
            return PublicProduct(**p)

    raise HTTPException(
        status_code=404,
        detail={"code": "PRODUCT_NOT_FOUND", "message": f"제품 '{slug}'을 찾을 수 없습니다."},
    )
