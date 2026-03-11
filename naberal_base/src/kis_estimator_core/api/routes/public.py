"""
Public API Router - 비인증 공개 엔드포인트

hkkor.com 공개 사이트에서 호출하는 API:
1. POST /v1/public/estimates - AI 견적 (rate limit: 10/min per IP)
2. POST /v1/public/inquiries - 문의 접수 (rate limit: 5/min per IP)
3. GET  /v1/public/products  - 제품 카탈로그 (공개)
"""

import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_estimator_core.infra.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Per-Endpoint Rate Limiter (in-memory, IP-based)
# ============================================================================

_rate_buckets: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))


def _check_rate_limit(request: Request, endpoint: str, max_per_minute: int):
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else "unknown"
    )
    now = time.time()
    window = 60

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
    type: str = Field(default="MCCB", description="차단기 종류 (MCCB/ELB)")
    poles: int = Field(..., ge=2, le=4, description="극수 (2/3/4)")
    current: int = Field(..., gt=0, le=1000, description="전류 (A)")
    frame: int = Field(..., gt=0, le=1000, description="프레임 (AF)")


class PublicAccessory(BaseModel):
    type: str = Field(..., description="자재 종류")
    quantity: int = Field(default=1, ge=1, description="수량")


class PublicEstimateRequest(BaseModel):
    panel_usage: str = Field(default="일반", description="분전반 용도")
    install_location: str = Field(
        ..., description="설치 위치 (옥내노출/옥외노출/옥내자립/옥외자립/매입함)"
    )
    enclosure_material: str = Field(
        default="STEEL 1.6T", description="외함 재질 (STEEL 1.6T, SUS201 1.2T 등)"
    )
    breaker_brand: str = Field(default="상도", description="차단기 브랜드 (상도/LS)")
    breaker_grade: str = Field(
        default="경제형", description="차단기 등급 (경제형/표준형)"
    )
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
    estimate_id: str
    success: bool
    total_amount: Optional[int] = None
    line_items: List[Dict[str, Any]] = []
    validation_checks: Dict[str, Any] = {}
    created_at: str
    message: str = ""


class InquiryRequest(BaseModel):
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
    inquiry_id: str
    status: str = "received"
    message: str


class PublicProduct(BaseModel):
    slug: str
    name: str
    category: str
    description: str
    specs: List[str] = []
    features: List[str] = []


# ============================================================================
# POST /estimates - 공개 AI 견적
# ============================================================================


@router.post("/estimates", response_model=PublicEstimateResponse, status_code=201)
async def create_public_estimate(
    request: Request,
    body: PublicEstimateRequest,
    db: AsyncSession = Depends(get_db),
):
    """비인증 공개 AI 견적 생성 (rate limit: 10/min per IP)

    실제 견적 프로그램과 동일한 FIX4Pipeline을 사용합니다.
    PublicEstimateRequest → EstimateRequest 변환 → FIX4Pipeline 실행.
    """
    _check_rate_limit(request, "public_estimates", max_per_minute=10)

    try:
        from kis_estimator_core.api.schemas.estimates import (
            BreakerInput as SchemaBreakerInput,
            EnclosureInput as SchemaEnclosureInput,
            EstimateOptions,
            EstimateRequest,
            PanelInput,
        )
        from kis_estimator_core.engine.fix4_pipeline import get_pipeline
        from kis_estimator_core.services.estimate_service import (
            EstimateService,
            generate_estimate_id,
        )

        # 1. 브랜드 매핑 (상도 → SANGDO, LS → LS)
        brand_map = {"상도": "SANGDO", "LS": "LS"}
        brand_pref = brand_map.get(body.breaker_brand, "SANGDO")

        # 2. 등급 → use_economy_series
        use_economy = body.breaker_grade != "표준형"

        # 3. 메인 차단기 → BreakerInput 스키마
        main_breaker = SchemaBreakerInput(
            breaker_type=body.main_breaker.type,
            ampere=body.main_breaker.current,
            poles=body.main_breaker.poles,
            quantity=1,
        )

        # 4. 분기 차단기 → BreakerInput 스키마 목록
        branch_breakers = [
            SchemaBreakerInput(
                breaker_type=b.type,
                ampere=b.current,
                poles=b.poles,
                quantity=1,
            )
            for b in body.branch_breakers
        ]

        # 5. 외함 → EnclosureInput 스키마
        enclosure = SchemaEnclosureInput(
            type=body.install_location,
            material=body.enclosure_material or "STEEL 1.6T",
        )

        # 6. 부속자재는 model이 필요 — 기본 모델 매핑
        accessory_model_map = {
            "magnet": "MC-22",
            "timer": "H3Y-2",
            "meter": "LD-3310",
            "spd": "SPD-T2",
            "switch": "SW-01",
        }
        schema_accessories = None
        if body.accessories:
            from kis_estimator_core.api.schemas.estimates import (
                AccessoryInput as SchemaAccessoryInput,
            )
            schema_accessories = [
                SchemaAccessoryInput(
                    type=a.type,
                    model=accessory_model_map.get(a.type, a.type),
                    quantity=a.quantity,
                )
                for a in body.accessories
            ]

        # 7. PanelInput 구성
        panel = PanelInput(
            panel_name="분전반",
            main_breaker=main_breaker,
            branch_breakers=branch_breakers if branch_breakers else None,
            accessories=schema_accessories,
            enclosure=enclosure,
        )

        # 8. EstimateRequest 구성 (실제 견적 프로그램과 동일한 형식)
        estimate_request = EstimateRequest(
            customer_name=body.customer_name or "웹사이트 고객",
            project_name=body.project_name or "온라인 견적",
            panels=[panel],
            options=EstimateOptions(
                breaker_brand_preference=brand_pref,
                use_economy_series=use_economy,
                include_evidence_pack=False,
            ),
        )

        # 9. Estimate ID 생성
        estimate_id = await generate_estimate_id(db)

        # 10. FIX4Pipeline 실행 (실제 견적 엔진)
        pipeline = get_pipeline()
        response = await pipeline.execute(estimate_request, estimate_id=estimate_id)

        # 11. DB 저장 (선택적 — 실패해도 견적 결과 반환)
        try:
            service = EstimateService(db)
            await service.save_estimate(
                estimate_id=response.estimate_id,
                request=estimate_request,
                response=response,
            )
        except Exception as save_err:
            logger.warning(f"Public estimate DB save failed (non-fatal): {save_err}")

        # 12. EstimateResponse → PublicEstimateResponse 변환
        is_success = response.status == "completed"
        line_items = []
        total_amount = response.total_price

        # panels에서 BOM line_items 추출 (PanelResponse.items)
        if response.panels:
            for panel_resp in response.panels:
                panel_items = getattr(panel_resp, "items", None) or getattr(panel_resp, "bom", None)
                if panel_items:
                    for item in panel_items:
                        line_items.append(
                            item.model_dump() if hasattr(item, "model_dump") else item
                        )

        # validation_checks 추출
        vc = response.validation_checks
        checks_info = {}
        if vc:
            checks_info = vc.model_dump() if hasattr(vc, "model_dump") else {}

        return PublicEstimateResponse(
            estimate_id=response.estimate_id,
            success=is_success,
            total_amount=total_amount,
            line_items=line_items,
            validation_checks={
                "all_passed": is_success,
                **checks_info,
            },
            created_at=response.created_at.isoformat() if response.created_at else datetime.now().isoformat() + "Z",
            message=(
                "견적이 성공적으로 생성되었습니다."
                if is_success
                else "견적 생성 중 일부 오류가 발생했습니다."
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Public estimate error: {e}")
        # EstimatorError의 경우 상세 메시지 포함
        error_msg = str(e)
        if hasattr(e, "payload"):
            error_msg = getattr(e.payload, "message", str(e))
            hint = getattr(e.payload, "hint", "")
            if hint:
                error_msg = f"{error_msg} ({hint})"

        raise HTTPException(
            status_code=500,
            detail={
                "code": "PUBLIC_ESTIMATE_ERROR",
                "message": f"견적 생성 실패: {error_msg}",
                "traceId": str(uuid.uuid4()),
            },
        )


# ============================================================================
# POST /inquiries - 문의 접수
# ============================================================================


@router.post("/inquiries", response_model=InquiryResponse, status_code=201)
async def create_inquiry(
    request: Request,
    body: InquiryRequest,
    db: AsyncSession = Depends(get_db),
):
    """고객 문의 접수 (rate limit: 5/min per IP)"""
    _check_rate_limit(request, "public_inquiries", max_per_minute=5)

    try:
        inquiry_id = f"INQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

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
            pass

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
# GET /products - 공개 제품 카탈로그
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


# ============================================================================
# POST /signup - 고객 회원가입 (공개)
# ============================================================================


class CustomerSignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    name: str = Field(..., min_length=1, max_length=100, description="이름")
    company: str = Field(default="", max_length=200, description="회사명")
    phone: str = Field(default="", max_length=20, description="연락처")
    email: str = Field(default="", max_length=200, description="이메일")


class CustomerSignupResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None


@router.post("/signup", response_model=CustomerSignupResponse, status_code=201)
async def customer_signup(
    request: Request,
    body: CustomerSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """고객 회원가입 (rate limit: 5/min per IP)

    고객 역할(customer)로 계정을 생성합니다.
    생성된 계정은 /v1/auth/login으로 로그인 가능합니다.
    """
    _check_rate_limit(request, "public_signup", max_per_minute=5)

    try:
        from kis_estimator_core.services.auth_service import (
            hash_password,
        )
        from kis_estimator_core.infra.db import get_db_instance

        # 사용자명 중복 검사
        db_inst = get_db_instance()
        async with db_inst.session_scope() as session:
            result = await session.execute(
                text("SELECT id FROM kis_beta.users WHERE username = :username"),
                {"username": body.username.lower()},
            )
            if result.fetchone():
                return CustomerSignupResponse(
                    success=False,
                    message="이미 사용 중인 사용자명입니다.",
                )

            # 사용자 생성
            user_id = str(uuid.uuid4())
            hashed_pw = hash_password(body.password)

            await session.execute(
                text("""
                    INSERT INTO kis_beta.users (id, username, name, hashed_password, role, status)
                    VALUES (:id, :username, :name, :hashed_password, 'customer', 'active')
                """),
                {
                    "id": user_id,
                    "username": body.username.lower(),
                    "name": body.name,
                    "hashed_password": hashed_pw,
                },
            )

        logger.info(f"Customer signup: {body.username} ({body.name})")

        return CustomerSignupResponse(
            success=True,
            message="회원가입이 완료되었습니다. 로그인해 주세요.",
            user_id=user_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Customer signup error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SIGNUP_ERROR",
                "message": f"회원가입 실패: {str(e)}",
            },
        )


# ============================================================================
# GET /products - 공개 제품 카탈로그
# ============================================================================


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
        detail={
            "code": "PRODUCT_NOT_FOUND",
            "message": f"제품 '{slug}'을 찾을 수 없습니다.",
        },
    )
