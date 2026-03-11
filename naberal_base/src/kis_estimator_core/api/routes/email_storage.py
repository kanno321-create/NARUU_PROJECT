"""
Email Storage - JSON file I/O for templates, history, and rendering

Template/History JSON load/save, default templates, template rendering.
Extracted from email.py for single-responsibility compliance.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 데이터 저장 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "email"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_FILE = DATA_DIR / "templates.json"
HISTORY_FILE = DATA_DIR / "history.json"


# ==================== Template I/O ====================

def load_templates() -> list[dict]:
    """템플릿 로드"""
    if TEMPLATES_FILE.exists():
        try:
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return get_default_templates()


def save_templates(templates: list[dict]) -> None:
    """템플릿 저장"""
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


# ==================== History I/O ====================

def load_history() -> list[dict]:
    """발송 이력 로드"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_history(history: list[dict]) -> None:
    """발송 이력 저장"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ==================== Template Rendering ====================

def render_template(template_body: str, template_subject: str, variables: dict) -> tuple[str, str]:
    """템플릿 렌더링"""
    rendered_body = template_body
    rendered_subject = template_subject

    for key, value in variables.items():
        placeholder = "{" + key + "}"
        rendered_body = rendered_body.replace(placeholder, str(value))
        rendered_subject = rendered_subject.replace(placeholder, str(value))

    return rendered_subject, rendered_body


# ==================== Default Templates ====================

def get_default_templates() -> list[dict]:
    """기본 템플릿 생성"""
    now = datetime.now().isoformat()
    return [
        {
            "id": "tpl-estimate-standard",
            "name": "견적서 발송 (표준)",
            "subject": "[{company_name}] {customer}님 견적서 발송드립니다",
            "body": _TEMPLATE_ESTIMATE_STANDARD,
            "category": "estimate",
            "variables": ["customer", "panel_name", "total_price", "estimate_date",
                          "company_name", "company_phone", "company_email"],
            "is_default": True,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        },
        {
            "id": "tpl-estimate-formal",
            "name": "견적서 발송 (공식)",
            "subject": "[견적서] {customer} - {panel_name}",
            "body": _TEMPLATE_ESTIMATE_FORMAL,
            "category": "estimate",
            "variables": ["customer", "panel_name", "total_price",
                          "company_name", "company_phone", "company_fax", "company_email"],
            "is_default": False,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        },
        {
            "id": "tpl-reminder",
            "name": "납품일정 알림",
            "subject": "[알림] {customer}님 납품 예정 안내",
            "body": _TEMPLATE_REMINDER,
            "category": "reminder",
            "variables": ["customer", "panel_name", "delivery_date", "delivery_location"],
            "is_default": False,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        },
        {
            "id": "tpl-invoice",
            "name": "청구서 발송",
            "subject": "[청구서] {customer}님 - {invoice_month}월분",
            "body": _TEMPLATE_INVOICE,
            "category": "invoice",
            "variables": ["customer", "invoice_month", "total_amount", "due_date", "bank_account"],
            "is_default": False,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0,
        },
    ]


# ==================== HTML Template Strings ====================

_TEMPLATE_ESTIMATE_STANDARD = """
<div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2563eb;">견적서 발송</h2>
    <p>안녕하세요, {customer}님.</p>
    <p>요청하신 견적서를 첨부하여 발송드립니다.</p>

    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin: 0 0 10px 0; color: #374151;">견적 정보</h3>
        <table style="width: 100%;">
            <tr><td style="padding: 5px 0; color: #6b7280;">분전반:</td><td>{panel_name}</td></tr>
            <tr><td style="padding: 5px 0; color: #6b7280;">견적금액:</td><td style="font-weight: bold; color: #2563eb;">{total_price}</td></tr>
            <tr><td style="padding: 5px 0; color: #6b7280;">견적일자:</td><td>{estimate_date}</td></tr>
        </table>
    </div>

    <p>문의사항이 있으시면 언제든 연락 주시기 바랍니다.</p>
    <p>감사합니다.</p>

    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
    <p style="color: #6b7280; font-size: 12px;">
        {company_name}<br>
        Tel: {company_phone} | Email: {company_email}
    </p>
</div>
"""

_TEMPLATE_ESTIMATE_FORMAL = """
<div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="text-align: center; padding: 20px; background: #1e40af; color: white;">
        <h1 style="margin: 0;">{company_name}</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.8;">견적서 송부</p>
    </div>

    <div style="padding: 30px;">
        <p><strong>{customer}</strong> 귀하</p>
        <p>귀사의 무궁한 발전을 기원합니다.</p>
        <p>요청하신 <strong>{panel_name}</strong>에 대한 견적서를 첨부하여 송부드리오니 검토 부탁드립니다.</p>

        <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0;">
            <p style="margin: 0;"><strong>견적금액:</strong> {total_price} (VAT 별도)</p>
            <p style="margin: 5px 0 0 0;"><strong>유효기간:</strong> 견적일로부터 30일</p>
        </div>

        <p>기타 문의사항이 있으시면 아래 연락처로 연락 주시기 바랍니다.</p>

        <p style="margin-top: 30px;">감사합니다.</p>
    </div>

    <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 13px; color: #64748b;">
        <p style="margin: 0;">{company_name}</p>
        <p style="margin: 5px 0;">Tel: {company_phone} | Fax: {company_fax}</p>
        <p style="margin: 0;">Email: {company_email}</p>
    </div>
</div>
"""

_TEMPLATE_REMINDER = """
<div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #f59e0b;">납품 예정 안내</h2>
    <p>안녕하세요, {customer}님.</p>
    <p>아래와 같이 납품이 예정되어 있어 안내드립니다.</p>

    <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin: 0 0 10px 0; color: #92400e;">납품 정보</h3>
        <table style="width: 100%;">
            <tr><td style="padding: 5px 0; color: #78350f;">제품:</td><td>{panel_name}</td></tr>
            <tr><td style="padding: 5px 0; color: #78350f;">납품일:</td><td style="font-weight: bold;">{delivery_date}</td></tr>
            <tr><td style="padding: 5px 0; color: #78350f;">납품장소:</td><td>{delivery_location}</td></tr>
        </table>
    </div>

    <p>변경사항이 있으시면 미리 연락 주시기 바랍니다.</p>
    <p>감사합니다.</p>
</div>
"""

_TEMPLATE_INVOICE = """
<div style="font-family: 'Malgun Gothic', sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #10b981;">청구서 발송</h2>
    <p>안녕하세요, {customer}님.</p>
    <p>{invoice_month}월분 청구서를 첨부하여 발송드립니다.</p>

    <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin: 0 0 10px 0; color: #065f46;">청구 내역</h3>
        <table style="width: 100%;">
            <tr><td style="padding: 5px 0; color: #047857;">청구금액:</td><td style="font-weight: bold; font-size: 18px; color: #059669;">{total_amount}</td></tr>
            <tr><td style="padding: 5px 0; color: #047857;">납부기한:</td><td>{due_date}</td></tr>
        </table>
    </div>

    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px;">
        <p style="margin: 0; font-size: 14px;"><strong>입금계좌:</strong> {bank_account}</p>
    </div>

    <p style="margin-top: 20px;">문의사항이 있으시면 언제든 연락 주시기 바랍니다.</p>
    <p>감사합니다.</p>
</div>
"""
