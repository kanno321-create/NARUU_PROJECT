"""
Email LINE WORKS Client - LINE WORKS REST API integration

NaverWorksMailClient for HTTPS-based email sending.
API config load/save (env -> DB -> file fallback).
Extracted from email.py for single-responsibility compliance.
"""

import json
import logging
import os
import time
from pathlib import Path

import httpx
import jwt

logger = logging.getLogger(__name__)

# 데이터 저장 경로 (상대경로 - Railway 호환)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "email"
DATA_DIR.mkdir(parents=True, exist_ok=True)
API_CONFIG_FILE = DATA_DIR / "api_config.json"


class NaverWorksMailClient:
    """
    LINE WORKS (네이버웍스) Mail REST API 클라이언트

    SMTP 포트가 차단되는 클라우드 환경(Railway 등)에서
    HTTPS를 통해 이메일을 발송합니다.

    인증 흐름:
    1. JWT 토큰 생성 (Service Account + Private Key)
    2. Access Token 획득 (OAuth2 JWT Bearer)
    3. Mail API 호출 (Bearer Token)
    """

    AUTH_URL = "https://auth.worksmobile.com/oauth2/v2.0/token"
    API_BASE = "https://www.worksapis.com/v1.0"

    def __init__(self, client_id: str, client_secret: str,
                 service_account: str, private_key: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.service_account = service_account
        self.private_key = private_key
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    def _create_jwt(self) -> str:
        """Service Account JWT 토큰 생성"""
        now = int(time.time())
        payload = {
            "iss": self.client_id,
            "sub": self.service_account,
            "iat": now,
            "exp": now + 3600,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def _get_access_token(self) -> str:
        """Access Token 획득 (캐싱 포함)"""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        jwt_token = self._create_jwt()

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "assertion": jwt_token,
                    "scope": "mail",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in", 3600))
        logger.info("LINE WORKS access token 획득 성공")
        return self._access_token

    async def send_mail(
        self,
        user_id: str,
        to: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict:
        """
        LINE WORKS Mail API로 이메일 발송

        Args:
            user_id: 발신자 LINE WORKS 사용자 ID (이메일 주소)
            to: 수신자 이메일 목록
            subject: 제목
            body: 본문 (HTML)
            cc: 참조
            bcc: 숨은참조

        Returns:
            API 응답 dict
        """
        token = await self._get_access_token()

        mail_data: dict = {
            "to": ";".join(to),
            "subject": subject,
            "body": body,
            "contentType": "html",
        }
        if cc:
            mail_data["cc"] = ";".join(cc)
        if bcc:
            mail_data["bcc"] = ";".join(bcc)

        url = f"{self.API_BASE}/users/{user_id}/mail"

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

        logger.info(f"LINE WORKS API 이메일 발송 성공: {to} (status={resp.status_code})")
        return {"success": True, "method": "lineworks_api", "status_code": resp.status_code}


def load_api_config() -> dict:
    """
    LINE WORKS API 설정 로드

    우선순위:
    1. 환경변수 (NW_CLIENT_ID, NW_CLIENT_SECRET, NW_SERVICE_ACCOUNT, NW_PRIVATE_KEY)
    2. Supabase DB (nw_oauth_tokens 테이블)
    3. 파일 폴백 (data/api_config.json) - 레거시 지원
    """
    config = {}

    # 1. 환경변수에서 API 자격증명 읽기 (Railway 환경변수)
    env_client_id = os.getenv("NW_CLIENT_ID")
    env_client_secret = os.getenv("NW_CLIENT_SECRET")
    env_service_account = os.getenv("NW_SERVICE_ACCOUNT")
    env_private_key = os.getenv("NW_PRIVATE_KEY")

    if env_client_id:
        config["client_id"] = env_client_id
    if env_client_secret:
        config["client_secret"] = env_client_secret
    if env_service_account:
        config["service_account"] = env_service_account
    if env_private_key:
        config["private_key"] = env_private_key.replace("\\n", "\n")

    # 2. DB에서 OAuth 토큰 및 추가 설정 읽기 (동기 방식 - psycopg2)
    try:
        db_url = os.getenv("ALEMBIC_DATABASE_URL_SYNC")
        if db_url:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("""
                SELECT client_id, client_secret, service_account, private_key,
                       oauth_access_token, oauth_refresh_token, oauth_expires_at,
                       oauth_user_id, oauth_state
                FROM kis_beta.nw_oauth_tokens
                WHERE id = 1
            """)
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                if row[0] and not config.get("client_id"):
                    config["client_id"] = row[0]
                if row[1] and not config.get("client_secret"):
                    config["client_secret"] = row[1]
                if row[2] and not config.get("service_account"):
                    config["service_account"] = row[2]
                if row[3] and not config.get("private_key"):
                    config["private_key"] = row[3]

                if row[4]:
                    config["oauth_access_token"] = row[4]
                if row[5]:
                    config["oauth_refresh_token"] = row[5]
                if row[6]:
                    config["oauth_expires_at"] = row[6]
                if row[7]:
                    config["oauth_user_id"] = row[7]
                if row[8]:
                    config["oauth_state"] = row[8]

                logger.debug("API config loaded from DB")
                return config
    except Exception as e:
        logger.warning(f"DB에서 API config 로드 실패 (파일 폴백): {e}")

    # 3. 파일 폴백 (레거시 - Railway에서는 ephemeral)
    if API_CONFIG_FILE.exists():
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if key not in config:
                        config[key] = value
                logger.debug("API config loaded from file (fallback)")
        except Exception:
            pass

    return config


def save_api_config(config: dict) -> None:
    """
    LINE WORKS API 설정 저장

    저장 위치:
    1. Supabase DB (nw_oauth_tokens 테이블) - 우선
    2. 파일 폴백 (data/api_config.json) - DB 실패 시
    """
    # 1. DB에 저장 시도 (동기 방식 - psycopg2)
    try:
        db_url = os.getenv("ALEMBIC_DATABASE_URL_SYNC")
        if db_url:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO kis_beta.nw_oauth_tokens (
                    id, client_id, client_secret, service_account, private_key,
                    oauth_access_token, oauth_refresh_token, oauth_expires_at,
                    oauth_user_id, oauth_state
                ) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    client_id = EXCLUDED.client_id,
                    client_secret = EXCLUDED.client_secret,
                    service_account = EXCLUDED.service_account,
                    private_key = EXCLUDED.private_key,
                    oauth_access_token = EXCLUDED.oauth_access_token,
                    oauth_refresh_token = EXCLUDED.oauth_refresh_token,
                    oauth_expires_at = EXCLUDED.oauth_expires_at,
                    oauth_user_id = EXCLUDED.oauth_user_id,
                    oauth_state = EXCLUDED.oauth_state,
                    updated_at = timezone('utc', now())
            """, (
                config.get("client_id"),
                config.get("client_secret"),
                config.get("service_account"),
                config.get("private_key"),
                config.get("oauth_access_token"),
                config.get("oauth_refresh_token"),
                config.get("oauth_expires_at"),
                config.get("oauth_user_id"),
                config.get("oauth_state"),
            ))
            conn.commit()
            cur.close()
            conn.close()
            logger.info("API config saved to DB")
            return
    except Exception as e:
        logger.warning(f"DB에 API config 저장 실패 (파일 폴백): {e}")

    # 2. 파일 폴백
    with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    logger.debug("API config saved to file (fallback)")


def get_naver_works_client() -> NaverWorksMailClient | None:
    """설정된 경우 NaverWorksMailClient 인스턴스 반환"""
    api_cfg = load_api_config()
    if all(k in api_cfg for k in ("client_id", "client_secret", "service_account", "private_key")):
        return NaverWorksMailClient(
            client_id=api_cfg["client_id"],
            client_secret=api_cfg["client_secret"],
            service_account=api_cfg["service_account"],
            private_key=api_cfg["private_key"],
        )
    return None
