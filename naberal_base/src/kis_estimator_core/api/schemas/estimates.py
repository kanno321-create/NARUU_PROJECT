"""
Estimate Request/Response Schemas

OpenAPI 3.1 스키마 기반 Pydantic 모델 (견적 생성/검증)
Contract: spec_kit/api/openapi.yaml#EstimateRequest, EstimateResponse, ValidationResponse
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ============================================================
# Input Schemas (견적 요청)
# ============================================================

class BreakerInput(BaseModel):
    """
    차단기 입력 스키마

    Contract: spec_kit/api/openapi.yaml#BreakerInput

    Frontend는 breaker_type/poles/ampere만 전송.
    Backend가 카탈로그에서 model을 조회하여 자동 설정.
    """

    breaker_type: str = Field(
        ...,
        description="차단기 종류 (MCCB: 배선용, ELB: 누전차단기)"
    )

    @field_validator("breaker_type", mode="before")
    @classmethod
    def normalize_breaker_type(cls, v: str) -> str:
        """차단기 타입 정규화: CBR, CB, MCB 등을 MCCB/ELB로 변환"""
        if not isinstance(v, str):
            return v
        v_upper = v.upper().strip()
        # ELB 계열
        if v_upper in ("ELB", "ELCB", "RCD", "누전", "누전차단기"):
            return "ELB"
        # MCCB 계열 (기본값)
        if v_upper in ("MCCB", "MCB", "CB", "CBR", "BREAKER", "배선용", "배선용차단기", "차단기"):
            return "MCCB"
        # 이미 유효한 값이면 그대로
        if v_upper in ("MCCB", "ELB"):
            return v_upper
        # 기본값은 MCCB
        return "MCCB"

    ampere: int = Field(
        ...,
        description="정격 전류 (AT)",
        ge=15,
        le=800,
        examples=[75]
    )

    poles: Literal[2, 3, 4] = Field(
        ...,
        description="극수",
        examples=[4]
    )

    quantity: int = Field(
        1,
        description="수량 (분기차단기만, 메인은 1 고정)",
        ge=1,
        le=50
    )

    model: str | None = Field(
        None,
        description="차단기 모델명 (Backend에서 자동 조회, Frontend는 전송 불필요)",
        examples=["SBE-104", "ABN-54", "SIE-32", "SIB-32"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "breaker_type": "MCCB",
                "ampere": 75,
                "poles": 4,
                "quantity": 1
            }
        }


class AccessoryInput(BaseModel):
    """
    부속자재 입력 스키마

    Contract: spec_kit/api/openapi.yaml#AccessoryInput
    """

    type: Literal["magnet", "timer", "meter", "spd", "switch"] = Field(
        ...,
        description="부속자재 종류"
    )

    model: str = Field(
        ...,
        description="모델명",
        examples=["MC-22"]
    )

    quantity: int = Field(
        ...,
        description="수량",
        ge=1,
        le=20
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "magnet",
                "model": "MC-22",
                "quantity": 2
            }
        }


class CustomSize(BaseModel):
    """
    커스텀 외함 크기

    Contract: spec_kit/api/openapi.yaml#EnclosureInput/custom_size
    """

    width_mm: int = Field(
        ...,
        description="폭 (mm)",
        ge=400,
        le=1200
    )

    height_mm: int = Field(
        ...,
        description="높이 (mm)",
        ge=400,
        le=2000
    )

    depth_mm: int = Field(
        ...,
        description="깊이 (mm)",
        ge=150,
        le=400
    )


class EnclosureInput(BaseModel):
    """
    외함 입력 스키마

    Contract: spec_kit/api/openapi.yaml#EnclosureInput
    """

    type: str = Field(
        ...,
        description="설치 유형"
    )

    material: str = Field(
        ...,
        description="재질 및 두께"
    )

    @field_validator("type", mode="before")
    @classmethod
    def normalize_enclosure_type(cls, v: str) -> str:
        """외함 타입 정규화"""
        if not isinstance(v, str):
            return v
        v_lower = v.lower().strip()
        # 옥내노출
        if "옥내" in v_lower and ("노출" in v_lower or "표면" in v_lower):
            return "옥내노출"
        if "indoor" in v_lower and "exposed" in v_lower:
            return "옥내노출"
        # 옥외노출
        if "옥외" in v_lower and ("노출" in v_lower or "표면" in v_lower):
            return "옥외노출"
        if "outdoor" in v_lower and "exposed" in v_lower:
            return "옥외노출"
        # 옥내자립
        if "옥내" in v_lower and "자립" in v_lower:
            return "옥내자립"
        # 옥외자립
        if "옥외" in v_lower and "자립" in v_lower:
            return "옥외자립"
        # 매입함
        if "매입" in v_lower:
            return "매입함"
        # 전주부착형
        if "전주" in v_lower:
            return "전주부착형"
        # FRP함
        if "frp" in v_lower:
            return "FRP함"
        # 하이박스
        if "하이박스" in v_lower or "hibox" in v_lower:
            return "하이박스"
        # 기본값
        return "옥내노출"

    @field_validator("material", mode="before")
    @classmethod
    def normalize_material(cls, v: str) -> str:
        """외함 재질 정규화: SUS, 스틸 등을 정규 형식으로 변환"""
        if not isinstance(v, str):
            return v
        v_upper = v.upper().strip()
        # SUS304 계열
        if "SUS304" in v_upper or "304" in v_upper:
            return "SUS304 1.2T"
        # SUS201 계열 (SUS만 입력 시 기본값)
        if "SUS201" in v_upper or "SUS" in v_upper or "201" in v_upper:
            return "SUS201 1.2T"
        # STEEL 1.6T 계열 (기본 스틸)
        if "1.6" in v_upper or "1.6T" in v_upper:
            return "STEEL 1.6T"
        # STEEL 1.0T 계열
        if "1.0" in v_upper or "1.0T" in v_upper:
            return "STEEL 1.0T"
        # 스틸/STEEL만 입력 시 기본값 STEEL 1.6T
        if "스틸" in v_upper or "STEEL" in v_upper or "강판" in v_upper:
            return "STEEL 1.6T"
        # 기본값
        return "STEEL 1.6T"

    custom_size: CustomSize | None = Field(
        None,
        description="커스텀 크기 (지정하지 않으면 자동 계산)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "옥내노출",
                "material": "STEEL 1.6T",
                "custom_size": None
            }
        }


class PanelInput(BaseModel):
    """
    분전반 입력 스키마

    Contract: spec_kit/api/openapi.yaml#PanelInput
    """

    panel_name: str | None = Field(
        None,
        description="분전반명 (없으면 '분전반' 또는 '분전반1', '분전반2'...)",
        max_length=50
    )

    main_breaker: BreakerInput = Field(
        ...,
        description="메인차단기"
    )

    branch_breakers: list[BreakerInput] | None = Field(
        None,
        description="분기차단기 목록 (없으면 메인차단기만 있는 견적)",
        max_length=50
    )

    accessories: list[AccessoryInput] | None = Field(
        None,
        description="부속자재 목록"
    )

    enclosure: EnclosureInput = Field(
        ...,
        description="외함 정보"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "panel_name": "분전반1",
                "main_breaker": {
                    "model": "SBE-104",
                    "ampere": 75,
                    "poles": 4,
                    "quantity": 1
                },
                "branch_breakers": [
                    {"model": "SBE-102", "ampere": 30, "poles": 2, "quantity": 5},
                    {"model": "SEE-103", "ampere": 50, "poles": 3, "quantity": 3}
                ],
                "accessories": [
                    {"type": "magnet", "model": "MC-22", "quantity": 2}
                ],
                "enclosure": {
                    "type": "옥내노출",
                    "material": "STEEL 1.6T"
                }
            }
        }


class EstimateOptions(BaseModel):
    """
    견적 옵션

    Contract: spec_kit/api/openapi.yaml#EstimateRequest/options
    """

    breaker_brand_preference: Literal["SANGDO", "LS"] | None = Field(
        None,
        description="차단기 브랜드 선호도"
    )

    use_economy_series: bool = Field(
        True,
        description="경제형 우선 사용 여부"
    )

    include_evidence_pack: bool = Field(
        True,
        description="Evidence 팩 포함 여부"
    )


class EstimateRequest(BaseModel):
    """
    견적 생성 요청

    Contract: spec_kit/api/openapi.yaml#EstimateRequest
    """

    customer_name: str = Field(
        ...,
        description="고객명 (거래처명)",
        min_length=1,
        max_length=100
    )

    project_name: str | None = Field(
        None,
        description="건명 (프로젝트명)",
        max_length=200
    )

    panels: list[PanelInput] = Field(
        ...,
        description="분전반 목록",
        min_items=1,
        max_items=10
    )

    options: EstimateOptions | None = Field(
        None,
        description="견적 옵션"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "ABC건설",
                "project_name": "신축 아파트 전기공사",
                "panels": [
                    {
                        "panel_name": "분전반1",
                        "main_breaker": {"model": "SBE-104", "ampere": 75, "poles": 4, "quantity": 1},
                        "branch_breakers": [
                            {"model": "SBE-102", "ampere": 30, "poles": 2, "quantity": 5}
                        ],
                        "enclosure": {"type": "옥내노출", "material": "STEEL 1.6T"}
                    }
                ],
                "options": {
                    "use_economy_series": True,
                    "include_evidence_pack": True
                }
            }
        }


# ============================================================
# Pipeline Results Schemas (FIX-4 파이프라인 결과)
# ============================================================

class Stage1EnclosureResult(BaseModel):
    """
    Stage 1: Enclosure (외함 계산) 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults/stage_1_enclosure
    """

    status: Literal["passed", "failed"] = Field(
        ...,
        description="단계 상태"
    )

    fit_score: float = Field(
        ...,
        description="외함 적합도 (≥ 0.90 필수)",
        ge=0.0,
        le=1.0
    )

    enclosure_size: list[int] = Field(
        ...,
        description="외함 크기 [W, H, D] (mm)",
        min_items=3,
        max_items=3
    )


class Stage2BreakerResult(BaseModel):
    """
    Stage 2: Breaker (브레이커 배치) 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults/stage_2_breaker
    """

    status: Literal["passed", "failed"] = Field(
        ...,
        description="단계 상태"
    )

    phase_balance: float = Field(
        ...,
        description="상평형 (%) (≤ 4% 필수)"
    )

    clearance_violations: int = Field(
        ...,
        description="간섭 위반 건수 (= 0 필수)"
    )

    thermal_violations: int = Field(
        ...,
        description="열밀도 위반 건수 (= 0 필수)"
    )


class Stage3FormatResult(BaseModel):
    """
    Stage 3: Format (문서 포맷) 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults/stage_3_format
    """

    status: Literal["passed", "failed"] = Field(
        ...,
        description="단계 상태"
    )

    formula_preservation: int = Field(
        ...,
        description="수식 보존율 (%) (= 100% 필수)"
    )


class Stage4CoverResult(BaseModel):
    """
    Stage 4: Cover (표지 생성) 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults/stage_4_cover
    """

    status: Literal["passed", "failed"] = Field(
        ...,
        description="단계 상태"
    )

    cover_compliance: int = Field(
        ...,
        description="표지 규칙 준수율 (%) (= 100% 필수)"
    )


class Stage5DocLintResult(BaseModel):
    """
    Stage 5: Doc Lint (최종 검증) 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults/stage_5_doc_lint
    """

    status: Literal["passed", "failed"] = Field(
        ...,
        description="단계 상태"
    )

    lint_errors: int = Field(
        ...,
        description="린트 오류 건수 (= 0 필수)"
    )


class PipelineResults(BaseModel):
    """
    FIX-4 파이프라인 전체 결과

    Contract: spec_kit/api/openapi.yaml#PipelineResults
    """

    stage_1_enclosure: Stage1EnclosureResult = Field(
        ...,
        description="Stage 1: Enclosure (외함 계산)"
    )

    stage_2_breaker: Stage2BreakerResult = Field(
        ...,
        description="Stage 2: Breaker (브레이커 배치)"
    )

    stage_3_format: Stage3FormatResult = Field(
        ...,
        description="Stage 3: Format (문서 포맷)"
    )

    stage_4_cover: Stage4CoverResult = Field(
        ...,
        description="Stage 4: Cover (표지 생성)"
    )

    stage_5_doc_lint: Stage5DocLintResult = Field(
        ...,
        description="Stage 5: Doc Lint (최종 검증)"
    )


# ============================================================
# Validation Checks Schemas (7가지 필수 검증)
# ============================================================

class ValidationChecks(BaseModel):
    """
    7가지 필수 검증 체크 결과

    Contract: spec_kit/api/openapi.yaml#ValidationChecks
    """

    CHK_BUNDLE_MAGNET: Literal["passed", "failed", "skipped"] = Field(
        ...,
        description="마그네트 동반자재 포함 확인"
    )

    CHK_BUNDLE_TIMER: Literal["passed", "failed", "skipped"] = Field(
        ...,
        description="타이머 동반자재 포함 확인"
    )

    CHK_ENCLOSURE_H_FORMULA: Literal["passed", "failed"] = Field(
        ...,
        description="외함 높이 공식 적용 확인"
    )

    CHK_PHASE_BALANCE: Literal["passed", "failed"] = Field(
        ...,
        description="상평형 ≤ 4% 확인"
    )

    CHK_CLEARANCE_VIOLATIONS: Literal["passed", "failed"] = Field(
        ...,
        description="간섭 = 0 확인"
    )

    CHK_THERMAL_VIOLATIONS: Literal["passed", "failed"] = Field(
        ...,
        description="열밀도 = 0 확인"
    )

    CHK_FORMULA_PRESERVATION: Literal["passed", "failed"] = Field(
        ...,
        description="Excel 수식 보존 = 100% 확인"
    )


# ============================================================
# Response Schemas (견적 응답)
# ============================================================

class DocumentUrls(BaseModel):
    """
    문서 다운로드 URL

    Contract: spec_kit/api/openapi.yaml#EstimateResponse/documents
    """

    excel_url: str | None = Field(
        None,
        description="Excel 문서 다운로드 URL"
    )

    pdf_url: str | None = Field(
        None,
        description="PDF 문서 다운로드 URL"
    )


class EvidencePack(BaseModel):
    """
    Evidence 팩 정보

    Contract: spec_kit/api/openapi.yaml#EstimateResponse/evidence
    """

    evidence_pack_url: str | None = Field(
        None,
        description="Evidence 팩 다운로드 URL"
    )

    sha256: str | None = Field(
        None,
        description="Evidence 팩 SHA256 해시",
        pattern=r"^[a-f0-9]{64}$"
    )


# ... (Previous schemas)

class LineItemResponse(BaseModel):
    """
    견적 품목 (Line Item)
    """
    name: str = Field(..., description="품목명")
    spec: str = Field(..., description="규격")
    quantity: float = Field(..., description="수량 (부스바는 소수점 1자리, KG 단위)")
    unit: str = Field(..., description="단위")
    unit_price: int = Field(..., description="단가")
    supply_price: int = Field(..., description="공급가액")

class PanelResponse(BaseModel):
    """
    분전반 견적 결과
    """
    panel_id: str = Field(..., description="분전반 ID")
    total_price: int = Field(..., description="분전반 합계 금액")
    items: list[LineItemResponse] = Field(..., description="견적 품목 목록")


# ============================================================
# AI Verification Schemas (AI 검증 결과)
# ============================================================

class AIVerificationIssue(BaseModel):
    """
    AI 검증 문제점

    견적 검증 시 발견된 개별 문제점 정보
    """
    check_id: str = Field(..., description="검증 항목 ID (예: INPUT_001, ENCL_002)")
    severity: Literal["error", "warning"] = Field(..., description="심각도 (error: 오류, warning: 경고)")
    message: str = Field(..., description="문제 설명")
    expected: str | None = Field(None, description="예상 값")
    actual: str | None = Field(None, description="실제 값")
    suggestion: str = Field("", description="해결 제안")


class AIVerificationResult(BaseModel):
    """
    AI 검증 결과

    견적 시각화 전 6단계 AI 검증 수행 결과:
    1. 견적 요청 정보 확인
    2. 외함 설정 검증 (재질, 두께, 크기)
    3. 차단기 브랜드/타입 검증 (경제형 vs 표준형)
    4. 차단기 스펙 검증 (MCCB, ELB, 극수, 암페어, kA)
    5. 부스바/인건비/추가자재 검증
    6. 최종 검증
    """
    passed: bool = Field(..., description="검증 통과 여부 (False면 오류 존재)")
    summary: str = Field(..., description="검증 결과 요약")
    checks_performed: int = Field(..., description="수행된 검증 항목 수")
    checks_passed: int = Field(..., description="통과한 검증 항목 수")
    issues: list[AIVerificationIssue] = Field(default_factory=list, description="발견된 문제점 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "passed": True,
                "summary": "✅ AI 검증 통과: 6/6 항목 정상",
                "checks_performed": 6,
                "checks_passed": 6,
                "issues": []
            }
        }


class EstimateResponse(BaseModel):
    """
    견적 생성 응답

    Contract: spec_kit/api/openapi.yaml#EstimateResponse
    """

    estimate_id: str = Field(
        ...,
        description="견적 ID",
        pattern=r"^EST-\d{8}-\d{4}$",
        examples=["EST-20251118-0001"]
    )

    status: Literal["completed", "failed", "processing"] = Field(
        ...,
        description="견적 상태"
    )

    created_at: datetime = Field(
        ...,
        description="생성 일시 (UTC+09:00)"
    )

    pipeline_results: PipelineResults = Field(
        ...,
        description="FIX-4 파이프라인 결과"
    )

    validation_checks: ValidationChecks = Field(
        ...,
        description="7가지 필수 검증 결과"
    )

    documents: DocumentUrls | None = Field(
        None,
        description="문서 다운로드 URL"
    )

    evidence: EvidencePack | None = Field(
        None,
        description="Evidence 팩 정보"
    )

    total_price: int = Field(
        ...,
        description="총 견적가 (부가세 제외)"
    )

    total_price_with_vat: int = Field(
        ...,
        description="총 견적가 (부가세 포함)"
    )

    panels: list[PanelResponse] | None = Field(
        None,
        description="분전반별 상세 견적 (BOM)"
    )

    ai_verification: AIVerificationResult | None = Field(
        None,
        description="AI 검증 결과 (6단계 검증)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "estimate_id": "EST-20251118-0001",
                "status": "completed",
                "created_at": "2025-11-18T14:30:00+09:00",
                "pipeline_results": {
                    "stage_1_enclosure": {"status": "passed", "fit_score": 0.95, "enclosure_size": [600, 800, 200]},
                    "stage_2_breaker": {"status": "passed", "phase_balance": 2.5, "clearance_violations": 0, "thermal_violations": 0},
                    "stage_3_format": {"status": "passed", "formula_preservation": 100},
                    "stage_4_cover": {"status": "passed", "cover_compliance": 100},
                    "stage_5_doc_lint": {"status": "passed", "lint_errors": 0}
                },
                "validation_checks": {
                    "CHK_BUNDLE_MAGNET": "passed",
                    "CHK_BUNDLE_TIMER": "skipped",
                    "CHK_ENCLOSURE_H_FORMULA": "passed",
                    "CHK_PHASE_BALANCE": "passed",
                    "CHK_CLEARANCE_VIOLATIONS": "passed",
                    "CHK_THERMAL_VIOLATIONS": "passed",
                    "CHK_FORMULA_PRESERVATION": "passed"
                },
                "documents": {
                    "excel_url": "https://api.example.com/documents/EST-20251118-0001.xlsx",
                    "pdf_url": "https://api.example.com/documents/EST-20251118-0001.pdf"
                },
                "evidence": {
                    "evidence_pack_url": "https://api.example.com/evidence/EST-20251118-0001.zip",
                    "sha256": "a3b2c1d4e5f6789012345678901234567890123456789012345678901234abcd"
                },
                "total_price": 1250000,
                "total_price_with_vat": 1375000,
                "panels": [
                    {
                        "panel_id": "P1",
                        "total_price": 1250000,
                        "items": [
                            {"name": "Main Breaker", "spec": "100AF/3P/100A", "quantity": 1, "unit": "EA", "unit_price": 50000, "supply_price": 50000}
                        ]
                    }
                ]
            }
        }


# ============================================================
# Validation Response Schemas (검증 응답)
# ============================================================

class ValidationError(BaseModel):
    """
    검증 오류 상세

    Contract: spec_kit/api/openapi.yaml#ValidationResponse/errors
    """

    check_id: str = Field(
        ...,
        description="검증 체크 ID"
    )

    message: str = Field(
        ...,
        description="오류 메시지"
    )

    hint: str | None = Field(
        None,
        description="해결 방법 힌트"
    )


class ValidationResponse(BaseModel):
    """
    견적 검증 응답

    Contract: spec_kit/api/openapi.yaml#ValidationResponse
    """

    validation_id: str = Field(
        ...,
        description="검증 ID",
        pattern=r"^VAL-\d{8}-\d{4}$"
    )

    status: Literal["passed", "failed"] = Field(
        ...,
        description="전체 검증 상태"
    )

    checks: ValidationChecks = Field(
        ...,
        description="7가지 필수 검증 결과"
    )

    errors: list[ValidationError] | None = Field(
        None,
        description="검증 오류 목록"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "validation_id": "VAL-20251118-0001",
                "status": "passed",
                "checks": {
                    "CHK_BUNDLE_MAGNET": "passed",
                    "CHK_BUNDLE_TIMER": "skipped",
                    "CHK_ENCLOSURE_H_FORMULA": "passed",
                    "CHK_PHASE_BALANCE": "passed",
                    "CHK_CLEARANCE_VIOLATIONS": "passed",
                    "CHK_THERMAL_VIOLATIONS": "passed",
                    "CHK_FORMULA_PRESERVATION": "passed"
                },
                "errors": []
            }
        }
