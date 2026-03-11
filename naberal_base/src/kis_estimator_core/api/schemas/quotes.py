"""
Quote Request/Response Schemas

OpenAPI 3.1 스키마 기반 Pydantic 모델 (견적서 저장/조회/승인)
Contract: spec_kit/api/openapi.yaml#Quotes

BUG-1 재설계: 프론트엔드 도메인 payload ↔ 백엔드 스키마 정렬
- 기존: 제네릭 items (sku, quantity, unit_price, uom) → 422
- 변경: 도메인 특화 (customer, enclosure, breakers, accessories, panels)
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================
# Input Schemas (Quote 요청)
# ============================================================


class QuoteCreateRequest(BaseModel):
    """
    견적 저장 요청 (Domain-specific payload)

    프론트엔드 quote/page.tsx에서 견적 결과를 DB에 저장할 때 사용.
    /v1/estimates에서 계산 완료된 결과를 그대로 저장.
    """

    estimate_id: str | None = Field(
        None,
        description="원본 견적 ID (/v1/estimates에서 생성된 ID)",
        examples=["est-550e8400-e29b-41d4-a716-446655440000"],
    )

    customer: str | dict[str, Any] = Field(
        default_factory=dict,
        description="고객 정보 (이름 문자열 또는 상세 객체)",
        examples=["ABC건설"],
    )

    enclosure: dict[str, Any] = Field(
        default_factory=dict,
        description="외함 사양 (location, type, material 등)",
        examples=[{"location": "옥내", "type": "기성함", "material": "STEEL 1.6T"}],
    )

    main_breakers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="메인차단기 목록",
        examples=[[{"type": "MCCB", "poles": "4P", "capacity": "100A"}]],
    )

    branch_breakers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="분기차단기 목록",
    )

    accessories: list[dict[str, Any]] = Field(
        default_factory=list,
        description="부속자재 목록",
    )

    total_price: float = Field(
        0,
        ge=0,
        description="공급가액 (KRW)",
        examples=[2207960],
    )

    total_price_with_vat: float = Field(
        0,
        ge=0,
        description="부가세 포함 합계 (KRW)",
        examples=[2428756],
    )

    panels: list[dict[str, Any]] = Field(
        default_factory=list,
        description="분전반별 상세 BOM (PanelResponse[])",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "estimate_id": "est-123",
                "customer": "ABC건설",
                "enclosure": {"location": "옥내", "type": "기성함", "material": "STEEL 1.6T"},
                "main_breakers": [{"type": "MCCB", "poles": "4P", "capacity": "100A"}],
                "branch_breakers": [{"type": "ELB", "poles": "2P", "capacity": "30A", "quantity": 4}],
                "accessories": [],
                "total_price": 2207960,
                "total_price_with_vat": 2428756,
                "panels": [],
            }
        }


class QuoteApproveRequest(BaseModel):
    """
    Quote 승인 요청

    Contract: spec_kit/api/openapi.yaml#QuoteApproveRequest
    """

    actor: str = Field(
        ...,
        description="승인자 식별자 (이메일 또는 사용자명)",
        min_length=1,
        max_length=100,
        examples=["admin@example.com"],
    )

    comment: str | None = Field(
        None,
        description="승인 코멘트",
        max_length=500,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "actor": "admin@example.com",
                "comment": "가격 검토 완료, 승인함",
            }
        }


# ============================================================
# Response Schemas (Quote 응답)
# ============================================================


class QuoteTotals(BaseModel):
    """
    Quote 합계 정보

    Contract: spec_kit/api/openapi.yaml#QuoteTotals
    """

    subtotal: float = Field(..., description="소계 (공급가액)")
    discount: float = Field(0, description="할인 금액")
    vat: float = Field(..., description="부가세 (10%)")
    total: float = Field(..., description="총합계 (부가세 포함)")
    currency: str = Field("KRW", description="통화 코드")


class QuoteCreateResponse(BaseModel):
    """
    견적 저장 응답

    프론트엔드 호환: data.id, data.quote_id 모두 사용 가능
    """

    id: str = Field(
        ...,
        description="저장된 견적 ID (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    quote_id: str = Field(
        ...,
        description="견적 ID (UUID, id와 동일값)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    totals: QuoteTotals = Field(..., description="합계 정보")

    approval_required: bool = Field(
        False,
        description="승인 필요 여부 (50M KRW 이상)",
    )

    evidence_hash: str = Field(
        ...,
        description="무결성 해시 (SHA256)",
        pattern=r"^[a-f0-9]{64}$",
    )

    created_at: str = Field(
        ...,
        description="생성 일시 (ISO8601)",
    )


class QuoteDetailResponse(BaseModel):
    """
    견적 상세 조회 응답 (Domain-specific)

    저장된 도메인 데이터를 그대로 반환.
    """

    quote_id: str = Field(..., description="Quote UUID")
    estimate_id: str | None = Field(None, description="원본 견적 ID")
    customer: str | dict[str, Any] = Field(default_factory=dict, description="고객 정보")
    enclosure: dict[str, Any] = Field(default_factory=dict, description="외함 사양")
    main_breakers: list[dict[str, Any]] = Field(default_factory=list, description="메인차단기")
    branch_breakers: list[dict[str, Any]] = Field(default_factory=list, description="분기차단기")
    accessories: list[dict[str, Any]] = Field(default_factory=list, description="부속자재")
    panels: list[dict[str, Any]] = Field(default_factory=list, description="분전반별 BOM")
    totals: QuoteTotals = Field(..., description="합계 정보")
    status: Literal["DRAFT", "APPROVED", "REJECTED", "EXPIRED"] = Field(..., description="상태")
    approval_required: bool = Field(False, description="승인 필요 여부")
    evidence_hash: str = Field(..., description="무결성 해시")
    created_at: str = Field(..., description="생성 일시")
    updated_at: str = Field(..., description="수정 일시")
    approved_at: str | None = Field(None, description="승인 일시")
    approved_by: str | None = Field(None, description="승인자")


class QuoteApproveResponse(BaseModel):
    """
    Quote 승인 응답

    Contract: spec_kit/api/openapi.yaml#QuoteApproveResponse
    """

    quote_id: str = Field(..., description="Quote UUID")
    status: Literal["APPROVED"] = Field(..., description="상태")
    approved_at: str = Field(..., description="승인 일시")
    approved_by: str = Field(..., description="승인자")
    evidence_entry: str = Field(..., description="감사 로그 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "APPROVED",
                "approved_at": "2025-11-29T11:00:00+09:00",
                "approved_by": "admin@example.com",
                "evidence_entry": "audit-123e4567-e89b-12d3-a456-426614174000",
            }
        }


class QuotePDFResponse(BaseModel):
    """
    Quote PDF 생성 응답

    Contract: spec_kit/api/openapi.yaml#QuotePDFResponse
    """

    quote_id: str = Field(..., description="Quote UUID")
    pdf_path: str = Field(..., description="PDF 파일 경로")
    evidence_hash: str = Field(..., description="Quote 무결성 해시")
    approved: bool = Field(..., description="승인 여부")
    audit_passed: bool = Field(..., description="PDF 감사 통과 여부")
    s3_url: str | None = Field(None, description="S3 업로드 URL")
    s3_degraded: bool = Field(False, description="S3 업로드 실패 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "pdf_path": "out/pdf/quote-550e8400-e29b-41d4-a716-446655440000.pdf",
                "evidence_hash": "a3b2c1d4e5f6789012345678901234567890123456789012345678901234abcd",
                "approved": True,
                "audit_passed": True,
                "s3_url": "https://s3.ap-northeast-2.amazonaws.com/bucket/quote.pdf",
                "s3_degraded": False,
            }
        }


class QuoteURLResponse(BaseModel):
    """
    Quote Pre-signed URL 응답

    Contract: spec_kit/api/openapi.yaml#QuoteURLResponse
    """

    quote_id: str = Field(..., description="Quote UUID")
    url: str = Field(..., description="Pre-signed URL 또는 local:// URL")
    expires_at: str = Field(..., description="만료 일시")
    approved: bool = Field(..., description="승인 여부")
    evidence_hash: str = Field(..., description="무결성 해시")
    storage_mode: Literal["s3", "local"] = Field(..., description="스토리지 모드")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://bucket.s3.amazonaws.com/quote.pdf?X-Amz-Signature=...",
                "expires_at": "2025-11-29T12:00:00+09:00",
                "approved": True,
                "evidence_hash": "a3b2c1d4e5f6789012345678901234567890123456789012345678901234abcd",
                "storage_mode": "s3",
            }
        }
