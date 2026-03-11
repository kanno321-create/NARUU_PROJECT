"""
Email SMTP - SMTP configuration, constants, and sending logic

SMTP provider constants, config load/save, and synchronous email sending.
Extracted from email.py for single-responsibility compliance.
"""

import json
import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

# 데이터 저장 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "email"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

# ==================== SMTP Provider Constants ====================

NAVER_WORKS_SMTP = {
    "host": "smtp.worksmobile.com",
    "port": 587,
    "use_tls": True,
    "provider": "naver_works",
}

GMAIL_SMTP = {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": True,
    "provider": "gmail",
}

SMTP_PROVIDERS = {
    "naver_works": NAVER_WORKS_SMTP,
    "gmail": GMAIL_SMTP,
}


def get_provider_defaults(provider: str) -> dict:
    """제공자별 SMTP 기본 설정 반환"""
    return SMTP_PROVIDERS.get(provider, NAVER_WORKS_SMTP)


# ==================== SMTP Config I/O ====================

def load_config() -> dict:
    """
    SMTP 설정 로드

    우선순위:
    1. 환경변수 (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL)
    2. 파일 폴백 (data/email/config.json)
    """
    config = {}

    env_host = os.getenv("SMTP_HOST")
    env_port = os.getenv("SMTP_PORT")
    env_username = os.getenv("SMTP_USERNAME")
    env_password = os.getenv("SMTP_PASSWORD")
    env_from_email = os.getenv("SMTP_FROM_EMAIL")
    env_from_name = os.getenv("SMTP_FROM_NAME", "KIS Estimator")

    if env_host and env_username and env_password:
        config = {
            "host": env_host,
            "port": int(env_port) if env_port else 587,
            "username": env_username,
            "password": env_password,
            "from_email": env_from_email or env_username,
            "from_name": env_from_name,
            "use_tls": True,
            "provider": "naver_works",
        }
        logger.debug("SMTP config loaded from environment variables")
        return config

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict) -> None:
    """SMTP 설정 저장"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ==================== SMTP Sending ====================

def send_via_smtp(
    recipients: list[dict],
    subject: str,
    body: str,
    attachments: list[dict],
    config: dict,
):
    """SMTP로 이메일 발송 (동기)"""
    if config.get("use_tls", True):
        server = smtplib.SMTP(config["host"], config["port"], timeout=30)
        server.starttls()
    else:
        server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=30)

    server.login(config["username"], config["password"])

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = f"{config.get('from_name', 'KIS Estimator')} <{config['from_email']}>"

    to_emails = [r["email"] for r in recipients if r.get("type", "to") == "to"]
    cc_emails = [r["email"] for r in recipients if r.get("type") == "cc"]
    bcc_emails = [r["email"] for r in recipients if r.get("type") == "bcc"]

    msg["To"] = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)

    msg.attach(MIMEText(body, "html", "utf-8"))

    for attachment in attachments:
        file_path = Path(attachment["file_path"])
        if file_path.exists():
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment.get("file_name", file_path.name)
                )
                msg.attach(part)

    all_recipients = to_emails + cc_emails + bcc_emails
    server.sendmail(config["from_email"], all_recipients, msg.as_string())
    server.quit()
