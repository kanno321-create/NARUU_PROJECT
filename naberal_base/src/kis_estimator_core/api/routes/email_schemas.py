"""
Email Schemas - Pydantic models for Email API

All Pydantic request/response models for email endpoints.
Extracted from email.py for single-responsibility compliance.
"""

from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class EmailRecipient(BaseModel):
    """이메일 수신자"""
    email: str = Field(..., description="이메일 주소")
    name: Optional[str] = Field(None, description="수신자 이름")
    type: str = Field("to", description="수신 유형: to, cc, bcc")


class EmailAttachment(BaseModel):
    """이메일 첨부파일"""
    file_path: str = Field(..., description="파일 경로")
    file_name: Optional[str] = Field(None, description="표시할 파일명")


class SendEmailRequest(BaseModel):
    """이메일 발송 요청"""
    recipients: list[EmailRecipient] = Field(..., min_length=1, description="수신자 목록")
    subject: str = Field(..., min_length=1, description="제목")
    body: str = Field(..., description="본문 (HTML 지원)")
    template_id: Optional[str] = Field(None, description="템플릿 ID")
    attachments: list[EmailAttachment] = Field(default_factory=list, description="첨부파일")
    estimate_id: Optional[str] = Field(None, description="관련 견적 ID")
    customer: Optional[str] = Field(None, description="관련 거래처")
    scheduled_at: Optional[str] = Field(None, description="예약 발송 시간 (ISO 8601)")
    priority: str = Field("normal", description="우선순위: low, normal, high, urgent")
    track_opens: bool = Field(True, description="열람 추적 여부")
    track_clicks: bool = Field(True, description="클릭 추적 여부")


class EmailTemplate(BaseModel):
    """이메일 템플릿"""
    name: str = Field(..., min_length=1, description="템플릿 이름")
    subject: str = Field(..., description="제목 템플릿")
    body: str = Field(..., description="본문 템플릿 (HTML)")
    category: str = Field("general", description="카테고리: estimate, invoice, reminder, general")
    variables: list[str] = Field(default_factory=list, description="사용 가능한 변수")
    is_default: bool = Field(False, description="기본 템플릿 여부")


class EmailTemplateResponse(EmailTemplate):
    """템플릿 응답"""
    id: str
    created_at: str
    updated_at: str
    usage_count: int = 0


class EmailHistory(BaseModel):
    """이메일 발송 이력"""
    id: str
    recipients: list[EmailRecipient]
    subject: str
    body_preview: str
    template_id: Optional[str]
    estimate_id: Optional[str]
    customer: Optional[str]
    attachments_count: int
    status: str  # pending, sent, failed, scheduled, cancelled
    sent_at: Optional[str]
    scheduled_at: Optional[str]
    error_message: Optional[str]
    opened_at: Optional[str]
    clicked_at: Optional[str]
    created_at: str


class EmailStats(BaseModel):
    """이메일 통계"""
    total_sent: int
    total_pending: int
    total_failed: int
    total_scheduled: int
    open_rate: float
    click_rate: float
    by_category: dict
    recent_recipients: list[str]


class SMTPConfig(BaseModel):
    """
    SMTP 설정 (NAVER WORKS 기본)

    NAVER WORKS SMTP 설정:
    - Host: smtp.worksmobile.com
    - Port: 587 (TLS) 또는 465 (SSL)
    - 인증: 이메일 주소 + 앱 비밀번호
    """
    host: str = Field("smtp.worksmobile.com", description="SMTP 서버 호스트")
    port: int = Field(587, description="SMTP 포트 (TLS: 587, SSL: 465)")
    username: str = Field(..., description="NAVER WORKS 이메일 주소")
    password: str = Field(..., description="NAVER WORKS 앱 비밀번호")
    from_email: str = Field(..., description="발신자 이메일")
    from_name: str = Field("KIS Estimator", description="발신자 이름")
    use_tls: bool = Field(True, description="TLS 사용 여부")
    provider: str = Field("naver_works", description="이메일 제공자: naver_works, gmail, custom")


class NaverWorksAPIConfig(BaseModel):
    """LINE WORKS API 자격 증명"""
    client_id: str = Field(..., description="Developer Console Client ID")
    client_secret: str = Field(..., description="Developer Console Client Secret")
    service_account: str = Field(..., description="Service Account ID (이메일 형식)")
    private_key: str = Field(..., description="RSA Private Key (PEM 형식)")
