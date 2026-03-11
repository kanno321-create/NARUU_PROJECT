"""
Email Service - 이메일 발송 서비스

견적서, 도면 등 문서 이메일 발송 기능:
- SMTP 기반 이메일 발송
- Naver Works 연동 준비
- 첨부파일 지원 (PDF, Excel, SVG)
"""

import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """이메일 설정"""
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    sender_name: str = os.getenv("SMTP_SENDER_NAME", "NABERAL KIS Estimator")
    sender_email: str = os.getenv("SMTP_SENDER_EMAIL", "")


@dataclass
class EmailRequest:
    """이메일 발송 요청"""
    to: str
    subject: str
    body: str
    attachments: list[str] | None = None  # 파일 경로 목록
    cc: str | None = None
    bcc: str | None = None


@dataclass
class EmailResult:
    """이메일 발송 결과"""
    success: bool
    message: str
    sent_at: str | None = None
    recipient: str | None = None
    subject: str | None = None
    error: str | None = None


class EmailService:
    """이메일 발송 서비스"""

    def __init__(self, config: EmailConfig | None = None):
        """초기화"""
        self.config = config or EmailConfig()
        self._validate_config()

    def _validate_config(self):
        """설정 검증"""
        if not self.config.smtp_user or not self.config.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending will fail.")

    async def send_email(self, request: EmailRequest) -> EmailResult:
        """
        이메일 발송

        Args:
            request: 이메일 발송 요청

        Returns:
            EmailResult: 발송 결과
        """
        try:
            # SMTP 자격 증명 확인
            if not self.config.smtp_user or not self.config.smtp_password:
                return EmailResult(
                    success=False,
                    message="SMTP 자격 증명이 설정되지 않았습니다.",
                    error="SMTP_USER, SMTP_PASSWORD 환경변수를 설정해주세요."
                )

            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.sender_name} <{self.config.sender_email or self.config.smtp_user}>"
            msg['To'] = request.to
            msg['Subject'] = request.subject

            if request.cc:
                msg['Cc'] = request.cc
            if request.bcc:
                msg['Bcc'] = request.bcc

            # 본문 추가
            msg.attach(MIMEText(request.body, 'html', 'utf-8'))

            # 첨부파일 추가
            if request.attachments:
                for file_path in request.attachments:
                    self._attach_file(msg, file_path)

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)

                recipients = [request.to]
                if request.cc:
                    recipients.append(request.cc)
                if request.bcc:
                    recipients.append(request.bcc)

                server.sendmail(
                    self.config.smtp_user,
                    recipients,
                    msg.as_string()
                )

            logger.info(f"Email sent successfully to {request.to}")

            return EmailResult(
                success=True,
                message="이메일이 성공적으로 발송되었습니다.",
                sent_at=datetime.now(UTC).isoformat(),
                recipient=request.to,
                subject=request.subject
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return EmailResult(
                success=False,
                message="SMTP 인증에 실패했습니다.",
                error=str(e)
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return EmailResult(
                success=False,
                message="이메일 발송 중 오류가 발생했습니다.",
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return EmailResult(
                success=False,
                message="이메일 발송에 실패했습니다.",
                error=str(e)
            )

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """파일 첨부"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Attachment file not found: {file_path}")
            return

        try:
            with open(path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{path.name}"'
                )
                msg.attach(part)
                logger.info(f"Attached file: {path.name}")
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")

    async def send_estimate_email(
        self,
        to: str,
        estimate_id: str,
        customer_name: str = "",
        estimate_data: dict | None = None,
        attachments: list[str] | None = None
    ) -> EmailResult:
        """
        견적서 이메일 발송

        Args:
            to: 수신자 이메일
            estimate_id: 견적 ID
            customer_name: 고객명
            estimate_data: 견적 데이터
            attachments: 첨부파일 경로 목록

        Returns:
            EmailResult: 발송 결과
        """
        # 이메일 제목
        subject = f"[견적서] {estimate_id}"
        if customer_name:
            subject = f"[견적서] {customer_name}님 - {estimate_id}"

        # 이메일 본문 (HTML)
        body = self._generate_estimate_email_body(
            estimate_id=estimate_id,
            customer_name=customer_name,
            estimate_data=estimate_data
        )

        request = EmailRequest(
            to=to,
            subject=subject,
            body=body,
            attachments=attachments
        )

        return await self.send_email(request)

    def _generate_estimate_email_body(
        self,
        estimate_id: str,
        customer_name: str = "",
        estimate_data: dict | None = None
    ) -> str:
        """견적서 이메일 본문 생성"""
        greeting = f"{customer_name}님," if customer_name else "안녕하세요,"
        data = estimate_data or {}

        body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9fafb; }}
        .estimate-info {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .info-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .label {{ color: #666; }}
        .value {{ font-weight: bold; color: #2563eb; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>견적서 발송</h1>
            <p>NABERAL KIS Estimator</p>
        </div>
        <div class="content">
            <p>{greeting}</p>
            <p>요청하신 견적서를 발송해 드립니다.</p>

            <div class="estimate-info">
                <div class="info-row">
                    <span class="label">견적 ID</span>
                    <span class="value">{estimate_id}</span>
                </div>
                <div class="info-row">
                    <span class="label">발송일</span>
                    <span class="value">{datetime.now().strftime('%Y년 %m월 %d일')}</span>
                </div>
                {self._format_estimate_details(data)}
            </div>

            <p>첨부파일을 확인해 주시기 바랍니다.</p>
            <p>문의사항이 있으시면 언제든지 연락주세요.</p>
        </div>
        <div class="footer">
            <p>NABERAL KIS Estimator</p>
            <p>본 메일은 자동 발송되었습니다.</p>
        </div>
    </div>
</body>
</html>
"""
        return body

    def _format_estimate_details(self, data: dict) -> str:
        """견적 상세 정보 HTML 생성"""
        if not data:
            return ""

        rows = []
        field_labels = {
            "enclosure_type": "외함 종류",
            "brand": "브랜드",
            "main_breaker": "메인 차단기",
            "branch_count": "분기 차단기 수",
            "total_price": "합계",
        }

        for key, label in field_labels.items():
            if key in data:
                value = data[key]
                if key == "total_price":
                    value = f"{value:,}원"
                rows.append(f'''
                <div class="info-row">
                    <span class="label">{label}</span>
                    <span class="value">{value}</span>
                </div>
                ''')

        return "\n".join(rows)


# 싱글톤 인스턴스
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """EmailService 싱글톤"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
