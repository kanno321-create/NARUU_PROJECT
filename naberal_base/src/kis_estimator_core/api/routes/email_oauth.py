"""
Email OAuth - LINE WORKS OAuth token management and API sending

OAuth token acquisition/refresh, LINE WORKS Mail API sending,
OAuth API endpoints (authorize, callback, status).
Extracted from email.py for single-responsibility compliance.
"""

import logging
import os
import time
import urllib.parse
from uuid import uuid4

import httpx

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from kis_estimator_core.api.routes.email_lineworks import (
    load_api_config,
    save_api_config,
)

logger = logging.getLogger(__name__)

# ==================== OAuth Constants ====================

OAUTH_AUTH_URL = "https://auth.worksmobile.com/oauth2/v2.0/authorize"
OAUTH_TOKEN_URL = "https://auth.worksmobile.com/oauth2/v2.0/token"
MAIL_API_BASE = "https://www.worksapis.com/v1.0"


def _oauth_html(title: str, heading: str, body_text: str, color: str = "#ef4444", bg: str = "white") -> str:
    """OAuth HTML 응답 생성 헬퍼"""
    return (
        f'<html><head><meta charset="utf-8"><title>{title}</title></head>'
        f'<body style="font-family:sans-serif;text-align:center;padding:50px;background:{bg};">'
        f'<div style="max-width:500px;margin:0 auto;background:white;padding:40px;border-radius:16px;'
        f'box-shadow:0 4px 6px rgba(0,0,0,0.1);">'
        f'<h1 style="color:{color};">{heading}</h1>{body_text}</div></body></html>'
    )


# ==================== OAuth Helpers ====================

def _get_oauth_redirect_uri() -> str:
    """OAuth 리다이렉트 URI 생성"""
    base = os.getenv("BASE_URL", "https://naberalproject-production.up.railway.app")
    return f"{base}/v1/email/oauth/callback"


async def _get_oauth_access_token() -> str:
    """
    OAuth Access Token 획득 (저장된 토큰 -> 자동 갱신)

    Mail API는 User Account OAuth만 지원하므로
    refresh_token을 사용하여 access_token을 자동 갱신합니다.
    """
    api_cfg = load_api_config()

    access_token = api_cfg.get("oauth_access_token")
    expires_at = api_cfg.get("oauth_expires_at", 0)

    # 토큰이 아직 유효하면 그대로 사용
    if access_token and time.time() < expires_at - 60:
        return access_token

    # Refresh Token으로 갱신
    refresh_token = api_cfg.get("oauth_refresh_token")
    if not refresh_token:
        raise RuntimeError(
            "OAuth 인증이 필요합니다. /v1/email/oauth/authorize에서 LINE WORKS 로그인을 진행해주세요."
        )

    client_id = api_cfg.get("client_id")
    client_secret = api_cfg.get("client_secret")
    if not client_id or not client_secret:
        raise RuntimeError("LINE WORKS API 설정(client_id, client_secret)이 필요합니다.")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            logger.error(f"OAuth 토큰 갱신 실패: {resp.status_code} - {resp.text}")
            raise RuntimeError(
                "OAuth 토큰이 만료되었습니다. /v1/email/oauth/authorize에서 재인증해주세요."
            )
        data = resp.json()

    # 갱신된 토큰 저장
    api_cfg["oauth_access_token"] = data["access_token"]
    if "refresh_token" in data:
        api_cfg["oauth_refresh_token"] = data["refresh_token"]
    api_cfg["oauth_expires_at"] = time.time() + int(data.get("expires_in", 3600))
    save_api_config(api_cfg)

    logger.info("OAuth access token 갱신 성공")
    return data["access_token"]


# ==================== LINE WORKS Mail API Sending ====================

async def send_via_lineworks_api(
    recipients: list[dict],
    subject: str,
    body: str,
    config: dict,
) -> bool:
    """
    LINE WORKS REST API로 이메일 발송 (User Account OAuth 사용)

    Mail API는 Service Account(JWT) 인증을 지원하지 않으므로
    User Account OAuth 토큰을 사용합니다.
    """
    api_cfg = load_api_config()

    if not api_cfg.get("oauth_refresh_token"):
        raise RuntimeError(
            "LINE WORKS OAuth 인증이 필요합니다. "
            "/v1/email/oauth/authorize 에서 로그인해주세요."
        )

    token = await _get_oauth_access_token()

    to_emails = [r["email"] for r in recipients if r.get("type", "to") == "to"]
    cc_emails = [r["email"] for r in recipients if r.get("type") == "cc"]
    bcc_emails = [r["email"] for r in recipients if r.get("type") == "bcc"]

    user_id = (
        api_cfg.get("oauth_user_id")
        or config.get("from_email")
        or config.get("username")
        or "master@hkkor.com"
    )

    mail_data: dict = {
        "to": ";".join(to_emails),
        "subject": subject,
        "body": body,
        "contentType": "html",
    }
    if cc_emails:
        mail_data["cc"] = ";".join(cc_emails)
    if bcc_emails:
        mail_data["bcc"] = ";".join(bcc_emails)

    url = f"{MAIL_API_BASE}/users/{user_id}/mail"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json=mail_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code not in (200, 201, 202):
            logger.error(f"LINE WORKS Mail API 에러: {resp.status_code} - {resp.text}")
            resp.raise_for_status()

    logger.info(f"LINE WORKS OAuth Mail API 이메일 발송 성공: {to_emails}")
    return True


# ==================== OAuth API Endpoints ====================

oauth_router = APIRouter()


@oauth_router.get("/oauth/authorize", summary="LINE WORKS OAuth 인증 시작")
async def oauth_authorize() -> dict:
    """
    LINE WORKS OAuth 인증 URL을 생성합니다.

    LINE WORKS Mail API는 User Account OAuth만 지원합니다.
    (Service Account JWT로는 Mail API 호출 불가)

    사용 방법:
    1. 이 엔드포인트 호출 -> authorization_url 확인
    2. 브라우저에서 해당 URL을 열어 LINE WORKS 로그인
    3. 로그인 후 자동으로 콜백 처리됨
    4. 이후 이메일 발송 가능

    사전 준비:
    - Developer Console에서 Redirect URI 등록 필요
    - OAuth Scopes에 'mail' 추가 필요
    """
    api_cfg = load_api_config()
    client_id = api_cfg.get("client_id")

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="LINE WORKS API 설정이 필요합니다. /v1/email/config/api에서 client_id를 먼저 설정해주세요.",
        )

    state = str(uuid4())
    api_cfg["oauth_state"] = state
    save_api_config(api_cfg)

    redirect_uri = _get_oauth_redirect_uri()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "mail",
        "response_type": "code",
        "state": state,
    }
    auth_url = f"{OAUTH_AUTH_URL}?{urllib.parse.urlencode(params)}"

    return {
        "authorization_url": auth_url,
        "redirect_uri": redirect_uri,
        "message": "이 URL을 브라우저에서 열어 LINE WORKS 로그인해주세요.",
        "important": "Developer Console에서 Redirect URI를 반드시 등록해주세요.",
        "register_redirect_uri": redirect_uri,
    }


@oauth_router.get("/oauth/callback", response_class=HTMLResponse, summary="OAuth 콜백")
async def oauth_callback(
    code: str = Query(None, description="Authorization code"),
    state: str = Query(None, description="CSRF state"),
    error: str = Query(None, description="Error code"),
    error_description: str = Query(None, description="Error description"),
):
    """
    LINE WORKS OAuth 콜백 처리.
    브라우저에서 자동으로 호출되며, 인증 코드를 토큰으로 교환합니다.
    """
    # 에러 처리
    if error:
        return HTMLResponse(content=_oauth_html(
            "인증 실패", "LINE WORKS 인증 실패",
            f"<p>에러: {error}</p><p>{error_description or ''}</p>"
            "<p>Developer Console에서 OAuth Scopes에 'mail'이 추가되어 있는지 확인해주세요.</p>",
        ), status_code=400)

    if not code or not state:
        return HTMLResponse(content=_oauth_html(
            "잘못된 요청", "잘못된 요청", "<p>인증 코드 또는 state 값이 없습니다.</p>",
        ), status_code=400)

    api_cfg = load_api_config()

    # CSRF 검증
    if state != api_cfg.get("oauth_state"):
        return HTMLResponse(content=_oauth_html(
            "보안 오류", "보안 오류", "<p>State 값이 일치하지 않습니다. 다시 시도해주세요.</p>",
        ), status_code=400)

    client_id = api_cfg.get("client_id")
    client_secret = api_cfg.get("client_secret")
    redirect_uri = _get_oauth_redirect_uri()

    # Authorization Code -> Token 교환
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                OAUTH_TOKEN_URL,
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if resp.status_code != 200:
                logger.error(f"OAuth 토큰 교환 실패: {resp.status_code} - {resp.text}")
                return HTMLResponse(content=_oauth_html(
                    "토큰 교환 실패", "토큰 교환 실패",
                    f"<p>HTTP {resp.status_code}: {resp.text}</p>",
                ), status_code=400)

            data = resp.json()

    except Exception as e:
        logger.error(f"OAuth 토큰 교환 에러: {e}")
        return HTMLResponse(content=_oauth_html(
            "오류", "연결 오류", f"<p>{str(e)}</p>",
        ), status_code=500)

    # 토큰 저장
    api_cfg["oauth_access_token"] = data["access_token"]
    api_cfg["oauth_refresh_token"] = data["refresh_token"]
    api_cfg["oauth_expires_at"] = time.time() + int(data.get("expires_in", 3600))
    api_cfg["oauth_configured"] = True
    api_cfg["oauth_user_id"] = "master@hkkor.com"  # 로그인한 사용자
    api_cfg.pop("oauth_state", None)
    save_api_config(api_cfg)

    logger.info("LINE WORKS OAuth 인증 완료! 토큰 저장됨.")

    return HTMLResponse(content=_oauth_html(
        "인증 성공", "LINE WORKS 인증 완료!",
        "<p style='color:#4b5563;font-size:16px;'>OAuth 토큰이 성공적으로 저장되었습니다.</p>"
        "<p style='color:#4b5563;font-size:16px;'>이제 KIS Estimator에서 이메일을 발송할 수 있습니다.</p>"
        "<hr style='margin:30px 0;border:none;border-top:1px solid #e5e7eb;'>"
        "<p style='color:#9ca3af;font-size:13px;'>이 창은 닫아도 됩니다.</p>",
        color="#16a34a", bg="#f0fdf4",
    ))


@oauth_router.get("/oauth/status", summary="OAuth 인증 상태 확인")
async def oauth_status() -> dict:
    """LINE WORKS OAuth 인증 상태를 확인합니다."""
    api_cfg = load_api_config()

    oauth_configured = bool(api_cfg.get("oauth_refresh_token"))
    token_valid = False

    if oauth_configured:
        expires_at = api_cfg.get("oauth_expires_at", 0)
        token_valid = time.time() < expires_at - 60

    return {
        "oauth_configured": oauth_configured,
        "token_valid": token_valid,
        "oauth_user_id": api_cfg.get("oauth_user_id", ""),
        "has_refresh_token": bool(api_cfg.get("oauth_refresh_token")),
        "message": (
            "OAuth 인증 완료. 이메일 발송 가능합니다."
            if oauth_configured
            else "OAuth 인증이 필요합니다. /v1/email/oauth/authorize를 호출해주세요."
        ),
    }
