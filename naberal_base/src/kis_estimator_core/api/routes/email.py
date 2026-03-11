"""
KIS Estimator API - Email (이메일 관리)

이메일 관리 API:
- 견적서 이메일 발송
- 이메일 템플릿 관리
- 발송 이력 조회
- 예약 발송
- 다중 수신자 지원

발송 방식:
1. LINE WORKS REST API (HTTPS) - Railway 클라우드 환경 (우선)
2. SMTP 직접 연결 - 로컬 개발 환경 (폴백)

모듈 구조:
- email_schemas.py: Pydantic 모델 (request/response)
- email_lineworks.py: LINE WORKS REST API 클라이언트
- email_smtp.py: SMTP 설정/상수/발송
- email_storage.py: JSON 파일 I/O (템플릿/이력/렌더링)
- email_oauth.py: OAuth 토큰 관리 + OAuth 엔드포인트
- email.py (이 파일): API 라우터 (엔드포인트 정의)
"""

import logging
import smtplib
import socket
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from kis_estimator_core.api.routes.email_schemas import (
    EmailRecipient,
    EmailAttachment,
    SendEmailRequest,
    EmailTemplate,
    EmailTemplateResponse,
    EmailHistory,
    EmailStats,
    SMTPConfig,
    NaverWorksAPIConfig,
)
from kis_estimator_core.api.routes.email_lineworks import (
    load_api_config,
    save_api_config,
    get_naver_works_client,
)
from kis_estimator_core.api.routes.email_smtp import (
    NAVER_WORKS_SMTP,
    GMAIL_SMTP,
    SMTP_PROVIDERS,
    get_provider_defaults,
    load_config,
    save_config,
    send_via_smtp,
)
from kis_estimator_core.api.routes.email_storage import (
    load_templates,
    save_templates,
    load_history,
    save_history,
    render_template,
)
from kis_estimator_core.api.routes.email_oauth import (
    send_via_lineworks_api,
    oauth_router,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["email"])

# OAuth 엔드포인트를 메인 라우터에 포함
router.include_router(oauth_router)


# ==================== Background Send Orchestrator ====================

async def send_email_background(
    history_id: str,
    recipients: list[dict],
    subject: str,
    body: str,
    attachments: list[dict],
    config: dict,
):
    """백그라운드 이메일 발송 (REST API 우선, SMTP 폴백)"""
    history = load_history()
    send_method = "unknown"

    try:
        try:
            api_sent = await send_via_lineworks_api(recipients, subject, body, config)
            if api_sent:
                send_method = "lineworks_api"
                logger.info(f"이메일 발송 성공 (LINE WORKS API): {history_id}")
            else:
                raise RuntimeError("LINE WORKS API 미설정")
        except Exception as api_err:
            logger.warning(f"LINE WORKS API 실패: {api_err}")
            if config.get("host") and config.get("username"):
                logger.info("SMTP 폴백 시도...")
                send_via_smtp(recipients, subject, body, attachments, config)
                send_method = "smtp"
                logger.info(f"이메일 발송 성공 (SMTP): {history_id}")
            else:
                raise RuntimeError(f"LINE WORKS API 실패: {api_err}, SMTP 미설정으로 폴백 불가")

        for h in history:
            if h["id"] == history_id:
                h["status"] = "sent"
                h["sent_at"] = datetime.now().isoformat()
                h["send_method"] = send_method
                break

    except Exception as e:
        for h in history:
            if h["id"] == history_id:
                h["status"] = "failed"
                h["error_message"] = str(e)
                break
        logger.error(f"이메일 발송 실패: {history_id} - {e}")

    save_history(history)


# ==================== Send Endpoints ====================

@router.post("/send", response_model=EmailHistory, status_code=201, summary="이메일 발송")
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
) -> EmailHistory:
    """
    이메일을 발송합니다.

    기능:
    - 다중 수신자 (TO, CC, BCC)
    - HTML 본문 지원
    - 첨부파일 지원
    - 템플릿 사용
    - 예약 발송
    - 발송 추적
    """
    config = load_config()
    api_config = load_api_config()
    oauth_ready = bool(api_config.get("oauth_refresh_token"))
    smtp_ready = bool(config.get("host"))
    if not oauth_ready and not smtp_ready:
        raise HTTPException(
            status_code=400,
            detail="이메일 설정이 필요합니다. /v1/email/oauth/authorize에서 LINE WORKS OAuth 인증을 진행해주세요."
        )

    history = load_history()
    now = datetime.now().isoformat()

    # 템플릿 적용
    subject = request.subject
    body = request.body

    if request.template_id:
        templates = load_templates()
        template = next((t for t in templates if t["id"] == request.template_id), None)
        if template:
            subject = request.subject or template["subject"]
            body = request.body or template["body"]
            template["usage_count"] = template.get("usage_count", 0) + 1
            save_templates(templates)

    # 이력 생성
    history_entry = {
        "id": f"mail-{uuid4()}",
        "recipients": [r.dict() for r in request.recipients],
        "subject": subject,
        "body_preview": body[:200] + "..." if len(body) > 200 else body,
        "template_id": request.template_id,
        "estimate_id": request.estimate_id,
        "customer": request.customer,
        "attachments_count": len(request.attachments),
        "status": "scheduled" if request.scheduled_at else "pending",
        "sent_at": None,
        "scheduled_at": request.scheduled_at,
        "error_message": None,
        "opened_at": None,
        "clicked_at": None,
        "created_at": now,
    }

    history.append(history_entry)
    save_history(history)

    # 백그라운드 발송 (예약이 아닌 경우)
    if not request.scheduled_at:
        background_tasks.add_task(
            send_email_background,
            history_entry["id"],
            [r.dict() for r in request.recipients],
            subject,
            body,
            [a.dict() for a in request.attachments],
            config,
        )

    logger.info(f"이메일 발송 요청: {history_entry['id']}")

    return EmailHistory(**history_entry)


@router.post("/quick-send", response_model=EmailHistory, summary="빠른 이메일 발송")
async def quick_send_email(
    to: str = Query(..., description="수신자 이메일"),
    subject: str = Query(..., description="제목"),
    body: str = Query(..., description="본문"),
    background_tasks: BackgroundTasks = None,
) -> EmailHistory:
    """
    빠른 이메일 발송 (쿼리 파라미터로 간단히 발송)

    예: /email/quick-send?to=customer@example.com&subject=안녕하세요&body=본문입니다
    """
    request = SendEmailRequest(
        recipients=[EmailRecipient(email=to, type="to")],
        subject=subject,
        body=body,
    )
    return await send_email(request, background_tasks)


@router.post("/resend/{email_id}", response_model=EmailHistory, summary="이메일 재발송")
async def resend_email(email_id: str, background_tasks: BackgroundTasks) -> EmailHistory:
    """실패한 이메일을 재발송합니다."""
    config = load_config()
    if not config.get("host"):
        raise HTTPException(status_code=400, detail="SMTP 설정이 필요합니다.")

    history = load_history()

    for h in history:
        if h["id"] == email_id:
            if h["status"] not in ["failed", "cancelled"]:
                raise HTTPException(status_code=400, detail="재발송은 실패/취소된 이메일만 가능합니다.")

            h["status"] = "pending"
            h["error_message"] = None
            h["sent_at"] = None
            save_history(history)

            background_tasks.add_task(
                send_email_background,
                h["id"],
                h["recipients"],
                h["subject"],
                h["body_preview"],
                [],
                config,
            )

            return EmailHistory(**h)

    raise HTTPException(status_code=404, detail=f"이메일을 찾을 수 없습니다: {email_id}")


# ==================== History Endpoints ====================

@router.get("/history", response_model=list[EmailHistory], summary="발송 이력 조회")
async def get_email_history(
    status: Optional[str] = Query(None, description="상태 필터: pending, sent, failed, scheduled"),
    customer: Optional[str] = Query(None, description="거래처 필터"),
    estimate_id: Optional[str] = Query(None, description="견적 ID 필터"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[EmailHistory]:
    """이메일 발송 이력을 조회합니다."""
    history = load_history()

    filtered = []
    for h in history:
        if status and h.get("status") != status:
            continue
        if customer and customer.lower() not in (h.get("customer") or "").lower():
            continue
        if estimate_id and h.get("estimate_id") != estimate_id:
            continue
        if start_date:
            created = h.get("created_at", "")[:10]
            if created < start_date:
                continue
        if end_date:
            created = h.get("created_at", "")[:10]
            if created > end_date:
                continue
        filtered.append(h)

    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    result = filtered[offset:offset + limit]

    return [EmailHistory(**h) for h in result]


@router.get("/history/{email_id}", response_model=EmailHistory, summary="발송 상세 조회")
async def get_email_detail(email_id: str) -> EmailHistory:
    """특정 이메일의 상세 정보를 조회합니다."""
    history = load_history()

    for h in history:
        if h["id"] == email_id:
            return EmailHistory(**h)

    raise HTTPException(status_code=404, detail=f"이메일을 찾을 수 없습니다: {email_id}")


@router.delete("/history/{email_id}", summary="발송 이력 삭제")
async def delete_email_history(email_id: str) -> dict:
    """발송 이력을 삭제합니다."""
    history = load_history()

    for i, h in enumerate(history):
        if h["id"] == email_id:
            history.pop(i)
            save_history(history)
            return {"success": True, "deleted_id": email_id}

    raise HTTPException(status_code=404, detail=f"이메일을 찾을 수 없습니다: {email_id}")


@router.patch("/cancel/{email_id}", response_model=EmailHistory, summary="예약 발송 취소")
async def cancel_scheduled_email(email_id: str) -> EmailHistory:
    """예약된 이메일을 취소합니다."""
    history = load_history()

    for h in history:
        if h["id"] == email_id:
            if h["status"] != "scheduled":
                raise HTTPException(status_code=400, detail="예약된 이메일만 취소할 수 있습니다.")

            h["status"] = "cancelled"
            save_history(history)

            return EmailHistory(**h)

    raise HTTPException(status_code=404, detail=f"이메일을 찾을 수 없습니다: {email_id}")


# ==================== Template Endpoints ====================

@router.get("/templates", response_model=list[EmailTemplateResponse], summary="템플릿 목록")
async def list_templates(
    category: Optional[str] = Query(None, description="카테고리 필터"),
) -> list[EmailTemplateResponse]:
    """이메일 템플릿 목록을 조회합니다."""
    templates = load_templates()

    if category:
        templates = [t for t in templates if t.get("category") == category]

    return [EmailTemplateResponse(**t) for t in templates]


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse, summary="템플릿 상세")
async def get_template(template_id: str) -> EmailTemplateResponse:
    """특정 템플릿의 상세 정보를 조회합니다."""
    templates = load_templates()

    for t in templates:
        if t["id"] == template_id:
            return EmailTemplateResponse(**t)

    raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")


@router.post("/templates", response_model=EmailTemplateResponse, status_code=201, summary="템플릿 생성")
async def create_template(request: EmailTemplate) -> EmailTemplateResponse:
    """새 이메일 템플릿을 생성합니다."""
    templates = load_templates()

    now = datetime.now().isoformat()
    template = {
        "id": f"tpl-{uuid4()}",
        **request.dict(),
        "created_at": now,
        "updated_at": now,
        "usage_count": 0,
    }

    templates.append(template)
    save_templates(templates)

    logger.info(f"템플릿 생성: {template['id']} - {template['name']}")

    return EmailTemplateResponse(**template)


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse, summary="템플릿 수정")
async def update_template(template_id: str, request: EmailTemplate) -> EmailTemplateResponse:
    """템플릿을 수정합니다."""
    templates = load_templates()

    for i, t in enumerate(templates):
        if t["id"] == template_id:
            t.update(request.dict())
            t["updated_at"] = datetime.now().isoformat()
            templates[i] = t
            save_templates(templates)

            return EmailTemplateResponse(**t)

    raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")


@router.delete("/templates/{template_id}", summary="템플릿 삭제")
async def delete_template(template_id: str) -> dict:
    """템플릿을 삭제합니다."""
    templates = load_templates()

    for i, t in enumerate(templates):
        if t["id"] == template_id:
            if t.get("is_default"):
                raise HTTPException(status_code=400, detail="기본 템플릿은 삭제할 수 없습니다.")

            templates.pop(i)
            save_templates(templates)

            return {"success": True, "deleted_id": template_id}

    raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")


@router.post("/templates/{template_id}/preview", summary="템플릿 미리보기")
async def preview_template(template_id: str, variables: dict) -> dict:
    """템플릿에 변수를 적용한 미리보기를 반환합니다."""
    templates = load_templates()

    for t in templates:
        if t["id"] == template_id:
            subject, body = render_template(t["body"], t["subject"], variables)
            return {
                "subject": subject,
                "body": body,
                "template_id": template_id,
            }

    raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")


# ==================== Config Endpoints ====================

@router.get("/config", summary="SMTP 설정 조회")
async def get_email_config() -> dict:
    """현재 SMTP 설정을 조회합니다. (비밀번호는 마스킹)"""
    config = load_config()

    if not config:
        return {
            **NAVER_WORKS_SMTP,
            "username": "",
            "password": "",
            "from_email": "",
            "from_name": "KIS Estimator",
            "configured": False,
            "message": "NAVER WORKS SMTP 설정이 필요합니다. 이메일과 앱 비밀번호를 입력해주세요.",
        }

    if config.get("password"):
        config["password"] = "********"
    config["configured"] = True
    return config


@router.get("/config/naver-works", summary="NAVER WORKS 기본 설정")
async def get_naver_works_defaults() -> dict:
    """NAVER WORKS SMTP 기본 설정 정보를 반환합니다."""
    return {
        "provider": "naver_works",
        "host": NAVER_WORKS_SMTP["host"],
        "port": NAVER_WORKS_SMTP["port"],
        "use_tls": NAVER_WORKS_SMTP["use_tls"],
        "setup_guide": {
            "step_1": "NAVER WORKS 관리자 콘솔 접속",
            "step_2": "보안 > 앱 비밀번호 관리 이동",
            "step_3": "새 앱 비밀번호 생성 (용도: KIS Estimator)",
            "step_4": "생성된 16자리 앱 비밀번호 복사",
            "step_5": "/email/config에서 이메일과 앱 비밀번호 저장",
        },
        "required_fields": {
            "username": "NAVER WORKS 이메일 주소 (예: user@company.com)",
            "password": "앱 비밀번호 (16자리)",
            "from_email": "발신자 이메일 (username과 동일)",
            "from_name": "발신자 이름",
        },
    }


@router.get("/config/providers", summary="지원 이메일 제공자 목록")
async def list_email_providers() -> dict:
    """지원하는 이메일 제공자 목록을 반환합니다."""
    return {
        "providers": [
            {
                "id": "naver_works",
                "name": "NAVER WORKS",
                "host": NAVER_WORKS_SMTP["host"],
                "port": NAVER_WORKS_SMTP["port"],
                "recommended": True,
                "description": "기업용 네이버웍스 메일",
            },
            {
                "id": "gmail",
                "name": "Gmail",
                "host": GMAIL_SMTP["host"],
                "port": GMAIL_SMTP["port"],
                "recommended": False,
                "description": "구글 지메일 (앱 비밀번호 필요)",
            },
            {
                "id": "custom",
                "name": "직접 설정",
                "host": "",
                "port": 587,
                "recommended": False,
                "description": "커스텀 SMTP 서버",
            },
        ],
        "default": "naver_works",
    }


@router.post("/config", summary="SMTP 설정 저장")
async def save_email_config(config: SMTPConfig) -> dict:
    """SMTP 설정을 저장합니다."""
    config_dict = config.dict()

    if config.provider in SMTP_PROVIDERS:
        provider_defaults = get_provider_defaults(config.provider)
        config_dict["host"] = provider_defaults["host"]
        config_dict["port"] = provider_defaults["port"]
        config_dict["use_tls"] = provider_defaults["use_tls"]

    save_config(config_dict)
    logger.info(f"SMTP 설정 저장됨 (제공자: {config.provider})")
    return {
        "success": True,
        "message": f"SMTP 설정이 저장되었습니다. ({config.provider})",
        "provider": config.provider,
        "host": config_dict["host"],
    }


@router.post("/config/test", summary="SMTP 연결 테스트")
async def test_smtp_connection() -> dict:
    """SMTP 연결을 테스트합니다."""
    config = load_config()
    if not config.get("host"):
        raise HTTPException(
            status_code=400,
            detail="SMTP 설정이 필요합니다. NAVER WORKS 이메일과 앱 비밀번호를 설정해주세요."
        )

    host = config["host"]
    port = config["port"]
    diagnostics = {}

    # Step 1: DNS resolution test
    try:
        ip = socket.gethostbyname(host)
        diagnostics["dns_resolved"] = True
        diagnostics["ip_address"] = ip
    except socket.gaierror as e:
        return {
            "success": False,
            "message": f"DNS 해석 실패: {host} -> {str(e)}",
            "diagnostics": diagnostics,
        }

    # Step 2: TCP port connectivity test
    try:
        sock = socket.create_connection((host, port), timeout=15)
        sock.close()
        diagnostics["port_reachable"] = True
    except (socket.timeout, OSError) as e:
        diagnostics["port_reachable"] = False
        return {
            "success": False,
            "message": f"포트 연결 실패: {host}:{port} -> {str(e)}. Railway에서 SMTP 포트가 차단될 수 있습니다.",
            "diagnostics": diagnostics,
            "hint": "클라우드 환경에서 SMTP 포트(587/465)가 방화벽에 의해 차단될 수 있습니다.",
        }

    # Step 3: SMTP handshake + auth test
    try:
        if config.get("use_tls", True):
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=30)

        server.login(config["username"], config["password"])
        server.quit()

        return {
            "success": True,
            "message": "SMTP 연결 성공",
            "provider": config.get("provider", "unknown"),
            "host": host,
            "diagnostics": diagnostics,
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "인증 실패: 이메일 주소 또는 앱 비밀번호를 확인해주세요.",
            "hint": "NAVER WORKS의 경우 앱 비밀번호(16자리)를 사용해야 합니다.",
            "diagnostics": diagnostics,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"SMTP 연결 실패: {str(e)}",
            "diagnostics": diagnostics,
        }


# ==================== LINE WORKS API Config Endpoints ====================

@router.post("/config/api", summary="LINE WORKS API 설정 저장")
async def save_naver_works_api_config(config: NaverWorksAPIConfig) -> dict:
    """LINE WORKS REST API 자격 증명을 저장합니다."""
    config_dict = config.dict()
    save_api_config(config_dict)
    logger.info("LINE WORKS API 설정 저장됨")

    return {
        "success": True,
        "message": "LINE WORKS API 설정이 저장되었습니다. 이제 HTTPS를 통해 이메일을 발송합니다.",
        "client_id": config.client_id[:8] + "...",
        "service_account": config.service_account,
    }


@router.get("/config/api", summary="LINE WORKS API 설정 조회")
async def get_naver_works_api_config() -> dict:
    """LINE WORKS API 설정 상태를 조회합니다. (비밀번호 마스킹)"""
    api_cfg = load_api_config()

    if not api_cfg:
        return {
            "configured": False,
            "message": "LINE WORKS API 설정이 없습니다.",
            "setup_guide": {
                "step_1": "LINE WORKS Developer Console 접속 (https://developers.worksmobile.com)",
                "step_2": "앱 생성 후 Client ID / Client Secret 확인",
                "step_3": "Service Account 생성",
                "step_4": "Private Key 발급 (RSA PEM 형식)",
                "step_5": "OAuth Scopes에 'mail' 권한 추가",
                "step_6": "POST /v1/email/config/api 로 자격 증명 저장",
            },
        }

    return {
        "configured": True,
        "client_id": api_cfg.get("client_id", "")[:8] + "...",
        "service_account": api_cfg.get("service_account", ""),
        "has_private_key": "private_key" in api_cfg,
        "message": "LINE WORKS API 설정 완료. HTTPS로 이메일이 발송됩니다.",
    }


@router.post("/config/api/test", summary="LINE WORKS API 연결 테스트")
async def test_naver_works_api() -> dict:
    """LINE WORKS REST API 연결을 테스트합니다. (Service Account JWT)"""
    import httpx

    nw_client = get_naver_works_client()

    if not nw_client:
        return {
            "success": False,
            "message": "LINE WORKS API 설정이 없습니다. /email/config/api에서 설정해주세요.",
        }

    try:
        token = await nw_client._get_access_token()
        return {
            "success": True,
            "message": "LINE WORKS API 연결 성공! Access Token 획득 완료.",
            "token_preview": token[:20] + "...",
            "note": "메일 발송은 OAuth 인증이 필요합니다. /v1/email/oauth/authorize를 진행해주세요.",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "message": f"인증 실패: {e.response.status_code} - {e.response.text}",
            "hint": "Client ID, Client Secret, Service Account, Private Key를 확인하세요.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"API 연결 실패: {str(e)}",
        }


# ==================== Stats & Health Endpoints ====================

@router.get("/stats", response_model=EmailStats, summary="이메일 통계")
async def get_email_stats() -> EmailStats:
    """이메일 발송 통계를 조회합니다."""
    history = load_history()

    total_sent = sum(1 for h in history if h.get("status") == "sent")
    total_pending = sum(1 for h in history if h.get("status") == "pending")
    total_failed = sum(1 for h in history if h.get("status") == "failed")
    total_scheduled = sum(1 for h in history if h.get("status") == "scheduled")

    opened = sum(1 for h in history if h.get("opened_at"))
    clicked = sum(1 for h in history if h.get("clicked_at"))

    open_rate = (opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (clicked / total_sent * 100) if total_sent > 0 else 0

    by_category = {}
    templates = load_templates()
    template_categories = {t["id"]: t.get("category", "general") for t in templates}

    for h in history:
        cat = template_categories.get(h.get("template_id"), "direct")
        by_category[cat] = by_category.get(cat, 0) + 1

    recent_recipients = []
    for h in sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)[:10]:
        for r in h.get("recipients", []):
            if r["email"] not in recent_recipients:
                recent_recipients.append(r["email"])
                if len(recent_recipients) >= 5:
                    break
        if len(recent_recipients) >= 5:
            break

    return EmailStats(
        total_sent=total_sent,
        total_pending=total_pending,
        total_failed=total_failed,
        total_scheduled=total_scheduled,
        open_rate=round(open_rate, 1),
        click_rate=round(click_rate, 1),
        by_category=by_category,
        recent_recipients=recent_recipients,
    )


@router.get("/health", summary="이메일 서비스 헬스체크")
async def health_check() -> dict:
    """이메일 서비스 상태 확인"""
    config = load_config()
    api_config = load_api_config()
    history = load_history()
    templates = load_templates()

    oauth_configured = bool(api_config.get("oauth_refresh_token"))
    smtp_configured = bool(config.get("host"))

    return {
        "status": "healthy",
        "smtp_configured": smtp_configured,
        "oauth_configured": oauth_configured,
        "oauth_user": api_config.get("oauth_user_id", ""),
        "send_method": "lineworks_oauth" if oauth_configured else ("smtp" if smtp_configured else "none"),
        "data_dir": str(load_config.__module__),
        "total_emails": len(history),
        "total_templates": len(templates),
    }


# ==================== IMAP Receive Endpoints ====================

@router.get("/imap/test", summary="IMAP 연결 테스트")
async def test_imap():
    """IMAP 연결 테스트"""
    from kis_estimator_core.api.routes.email_imap import test_imap_connection

    return test_imap_connection()


@router.get("/imap/folders", summary="IMAP 폴더 목록 조회")
async def get_imap_folders():
    """IMAP 폴더 목록 조회"""
    from kis_estimator_core.api.routes.email_imap import list_folders

    try:
        folders = list_folders()
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/imap/emails", summary="IMAP 이메일 수신 목록 조회")
async def get_imap_emails(
    folder: str = Query("INBOX", description="IMAP folder"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search query"),
    since: Optional[str] = Query(None, description="Since date (DD-Mon-YYYY)"),
):
    """IMAP 이메일 수신 목록 조회"""
    from kis_estimator_core.api.routes.email_imap import fetch_emails

    try:
        result = fetch_emails(
            folder=folder,
            limit=limit,
            offset=offset,
            search_query=search,
            since_date=since,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/imap/emails/{email_id}", summary="IMAP 이메일 상세 조회")
async def get_imap_email_detail(
    email_id: str,
    folder: str = Query("INBOX"),
):
    """IMAP 이메일 상세 조회"""
    from kis_estimator_core.api.routes.email_imap import fetch_email_detail

    try:
        result = fetch_email_detail(folder=folder, email_id=email_id)
        if not result:
            raise HTTPException(status_code=404, detail="Email not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/imap/emails/{email_id}/mark", summary="이메일 읽음/별표 처리")
async def mark_imap_email(
    email_id: str,
    action: str = Query(..., description="read/unread/star/unstar"),
    folder: str = Query("INBOX"),
):
    """이메일 읽음/별표 처리"""
    from kis_estimator_core.api.routes.email_imap import mark_email

    success = mark_email(folder=folder, email_id=email_id, action=action)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark email")
    return {"success": True, "action": action}


@router.delete("/imap/emails/{email_id}", summary="이메일 삭제")
async def delete_imap_email(
    email_id: str,
    folder: str = Query("INBOX"),
):
    """이메일 삭제"""
    from kis_estimator_core.api.routes.email_imap import delete_email

    success = delete_email(folder=folder, email_id=email_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete email")
    return {"success": True}


# ==================== Attachment Download ====================

@router.get("/imap/emails/{email_id}/attachments/{filename}", summary="첨부파일 다운로드")
async def download_attachment_endpoint(
    email_id: str,
    filename: str,
    folder: str = Query("INBOX"),
):
    """Download email attachment"""
    from kis_estimator_core.api.routes.email_imap import download_attachment
    from fastapi.responses import Response

    result = download_attachment(folder, email_id, filename)
    if not result or not result.get("content"):
        raise HTTPException(status_code=404, detail="Attachment not found")

    return Response(
        content=result["content"],
        media_type=result["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{result["filename"]}"',
            "Content-Length": str(result["size"]),
        },
    )


# ==================== Reply / Forward ====================

@router.post("/reply", summary="답장 데이터 생성")
async def reply_email(
    email_id: str = Query(..., description="원본 이메일 ID"),
    folder: str = Query("INBOX"),
    body: str = Query("", description="추가 본문"),
    reply_all: bool = Query(False, description="전체 답장 여부"),
):
    """Get reply-ready email data (pre-populated fields)"""
    from kis_estimator_core.api.routes.email_imap import fetch_email_detail

    original = fetch_email_detail(folder, email_id)
    if not original:
        raise HTTPException(status_code=404, detail="Original email not found")

    # Build recipients
    reply_to = original.get("reply_to") or original.get("from", {}).get("email", "")
    recipients = [reply_to] if reply_to else []

    cc_list = []
    if reply_all:
        # Add all original To recipients (except self)
        for to in original.get("to", []):
            addr = to.get("email", "") if isinstance(to, dict) else str(to)
            if addr and addr not in recipients:
                cc_list.append(addr)
        # Add original CC
        for cc in original.get("cc", []):
            addr = cc.get("email", "") if isinstance(cc, dict) else str(cc)
            if addr and addr not in recipients and addr not in cc_list:
                cc_list.append(addr)

    # Build subject
    subject = original.get("subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Build quoted body
    from_name = original.get("from", {}).get("name", "")
    from_email = original.get("from", {}).get("email", "")
    date = original.get("date", "")
    original_body = original.get("body_text") or original.get("body_html") or ""

    quoted = f"\n\n--- 원본 메시지 ---\n보낸사람: {from_name} <{from_email}>\n날짜: {date}\n제목: {original.get('subject', '')}\n\n{original_body}"

    return {
        "to": recipients,
        "cc": cc_list,
        "subject": subject,
        "body": quoted,
        "in_reply_to": original.get("message_id", ""),
        "references": original.get("message_id", ""),
    }


@router.post("/forward", summary="전달 데이터 생성")
async def forward_email(
    email_id: str = Query(..., description="원본 이메일 ID"),
    folder: str = Query("INBOX"),
):
    """Get forward-ready email data"""
    from kis_estimator_core.api.routes.email_imap import fetch_email_detail

    original = fetch_email_detail(folder, email_id)
    if not original:
        raise HTTPException(status_code=404, detail="Original email not found")

    subject = original.get("subject", "")
    if not subject.lower().startswith("fwd:"):
        subject = f"Fwd: {subject}"

    from_name = original.get("from", {}).get("name", "")
    from_email = original.get("from", {}).get("email", "")
    date = original.get("date", "")
    original_body = original.get("body_text") or original.get("body_html") or ""

    forwarded = f"\n\n--- 전달된 메시지 ---\n보낸사람: {from_name} <{from_email}>\n날짜: {date}\n제목: {original.get('subject', '')}\n받는사람: {', '.join(t.get('email', '') if isinstance(t, dict) else str(t) for t in original.get('to', []))}\n\n{original_body}"

    return {
        "to": [],
        "cc": [],
        "subject": subject,
        "body": forwarded,
        "attachments": original.get("attachments", []),
    }
