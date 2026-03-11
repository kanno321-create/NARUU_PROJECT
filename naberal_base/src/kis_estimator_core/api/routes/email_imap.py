"""
Email IMAP - IMAP client for receiving emails

IMAP connection, folder listing, email fetching, and caching.
"""

import imaplib
import email
import email.utils
import re
from email.header import decode_header
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "email"
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAP_CACHE_FILE = DATA_DIR / "imap_cache.json"

# IMAP Provider Constants
IMAP_PROVIDERS = {
    "naver_works": {"host": "imap.worksmobile.com", "port": 993, "use_ssl": True},
    "gmail": {"host": "imap.gmail.com", "port": 993, "use_ssl": True},
}


def get_imap_config() -> dict:
    """Get IMAP config from existing SMTP config (same credentials)"""
    config_file = DATA_DIR / "config.json"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            smtp_config = json.load(f)
        provider = smtp_config.get("provider", "naver_works")
        imap_defaults = IMAP_PROVIDERS.get(provider, IMAP_PROVIDERS["naver_works"])

        return {
            "host": smtp_config.get("imap_host", imap_defaults["host"]),
            "port": smtp_config.get("imap_port", imap_defaults["port"]),
            "use_ssl": smtp_config.get("imap_use_ssl", imap_defaults["use_ssl"]),
            "username": smtp_config.get("username", ""),
            "password": smtp_config.get("password", ""),
            "provider": provider,
        }

    # Fallback to env vars
    return {
        "host": os.getenv("IMAP_HOST", "imap.worksmobile.com"),
        "port": int(os.getenv("IMAP_PORT", "993")),
        "use_ssl": True,
        "username": os.getenv("SMTP_USERNAME", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "provider": "naver_works",
    }


def _decode_header_value(value: str) -> str:
    """Decode email header (handles encoded-word syntax)"""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _parse_email_address(addr_str: str) -> dict:
    """Parse 'Name <email@example.com>' into {name, email}"""
    if not addr_str:
        return {"name": "", "email": ""}
    addr_str = _decode_header_value(addr_str)
    if "<" in addr_str:
        name = addr_str.split("<")[0].strip().strip('"')
        email_addr = addr_str.split("<")[1].split(">")[0].strip()
        return {"name": name, "email": email_addr}
    return {"name": "", "email": addr_str.strip()}


def _get_email_body(msg) -> tuple[str, str]:
    """Extract plain text and HTML body from email message"""
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text_body = payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html_body = payload.decode(charset, errors="replace")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                html_body = decoded
            else:
                text_body = decoded

    return text_body, html_body


def _get_attachments_info(msg) -> list[dict]:
    """Extract attachment metadata from email"""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = _decode_header_value(filename)
                    size = len(part.get_payload(decode=True) or b"")
                    attachments.append(
                        {
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": size,
                        }
                    )
    return attachments


def connect_imap() -> imaplib.IMAP4_SSL:
    """Create and authenticate IMAP connection"""
    config = get_imap_config()
    if not config["username"] or not config["password"]:
        raise ValueError(
            "IMAP credentials not configured. Set up email in Settings."
        )

    try:
        if config["use_ssl"]:
            conn = imaplib.IMAP4_SSL(config["host"], config["port"])
        else:
            conn = imaplib.IMAP4(config["host"], config["port"])

        conn.login(config["username"], config["password"])
        return conn
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP login failed: {e}")
        raise ValueError(f"IMAP login failed: {str(e)}")
    except Exception as e:
        logger.error(f"IMAP connection failed: {e}")
        raise ConnectionError(f"Cannot connect to IMAP server: {str(e)}")


def list_folders() -> list[dict]:
    """List all IMAP folders"""
    conn = connect_imap()
    try:
        status, folder_data = conn.list()
        folders = []
        if status == "OK":
            for item in folder_data:
                if isinstance(item, bytes):
                    decoded = item.decode("utf-8", errors="replace")
                    # Parse: (\\flags) "/" "folder_name"
                    parts = decoded.split(' "/" ')
                    if len(parts) >= 2:
                        flags = parts[0]
                        name = parts[1].strip('"')
                        folders.append(
                            {
                                "name": name,
                                "flags": flags,
                                "has_children": "\\HasChildren" in flags,
                                "no_select": "\\Noselect" in flags,
                            }
                        )
        return folders
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def fetch_emails(
    folder: str = "INBOX",
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None,
    since_date: Optional[str] = None,
) -> dict:
    """Fetch emails from IMAP folder

    Returns: {emails: [...], total: int, folder: str}
    """
    conn = connect_imap()
    try:
        # Select folder
        status, data = conn.select(folder, readonly=True)
        if status != "OK":
            raise ValueError(f"Cannot open folder: {folder}")

        total_messages = int(data[0])

        # Build search criteria
        criteria = []
        if search_query:
            criteria.append(
                f'(OR SUBJECT "{search_query}" FROM "{search_query}")'
            )
        if since_date:
            criteria.append(f"SINCE {since_date}")

        if criteria:
            search_str = " ".join(criteria)
        else:
            search_str = "ALL"

        status, msg_ids = conn.search(None, search_str)
        if status != "OK":
            return {"emails": [], "total": 0, "folder": folder}

        id_list = msg_ids[0].split()
        total = len(id_list)

        # Apply pagination (newest first)
        id_list = list(reversed(id_list))
        paginated_ids = id_list[offset : offset + limit]

        emails = []
        for msg_id in paginated_ids:
            try:
                # Fetch HEADER only (skip body/attachments for speed)
                status, msg_data = conn.fetch(msg_id, "(BODY.PEEK[HEADER] FLAGS)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                # Parse flags
                flags_data = (
                    msg_data[0][0].decode("utf-8", errors="replace")
                    if isinstance(msg_data[0][0], bytes)
                    else str(msg_data[0][0])
                )
                is_seen = "\\Seen" in flags_data
                is_flagged = "\\Flagged" in flags_data

                raw_header = msg_data[0][1]
                msg = email.message_from_bytes(raw_header)

                # Parse sender
                from_info = _parse_email_address(msg.get("From", ""))

                # Parse recipients
                to_list = []
                to_str = msg.get("To", "")
                if to_str:
                    for addr in to_str.split(","):
                        to_list.append(_parse_email_address(addr.strip()))

                # Parse date
                date_str = msg.get("Date", "")
                try:
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                    date_iso = parsed_date.isoformat()
                except Exception:
                    date_iso = date_str

                email_data = {
                    "id": (
                        msg_id.decode()
                        if isinstance(msg_id, bytes)
                        else str(msg_id)
                    ),
                    "message_id": msg.get("Message-ID", ""),
                    "subject": _decode_header_value(
                        msg.get("Subject", "(제목 없음)")
                    ),
                    "from": from_info,
                    "to": to_list,
                    "date": date_iso,
                    "body_preview": "",
                    "body_text": "",
                    "body_html": "",
                    "attachments": [],
                    "attachments_count": 0,
                    "is_read": is_seen,
                    "is_starred": is_flagged,
                    "folder": folder,
                }
                emails.append(email_data)

            except Exception as e:
                logger.warning(f"Failed to parse email {msg_id}: {e}")
                continue

        return {
            "emails": emails,
            "total": total,
            "folder": folder,
            "has_more": offset + limit < total,
        }
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def fetch_email_detail(folder: str, email_id: str) -> Optional[dict]:
    """Fetch single email with full body"""
    conn = connect_imap()
    try:
        status, data = conn.select(folder, readonly=True)
        if status != "OK":
            return None

        eid = (
            email_id.encode() if isinstance(email_id, str) else email_id
        )
        status, msg_data = conn.fetch(eid, "(RFC822 FLAGS)")
        if status != "OK" or not msg_data or not msg_data[0]:
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        flags_data = (
            msg_data[0][0].decode("utf-8", errors="replace")
            if isinstance(msg_data[0][0], bytes)
            else str(msg_data[0][0])
        )

        from_info = _parse_email_address(msg.get("From", ""))
        to_list = [
            _parse_email_address(a.strip())
            for a in (msg.get("To", "")).split(",")
            if a.strip()
        ]
        cc_list = [
            _parse_email_address(a.strip())
            for a in (msg.get("Cc", "")).split(",")
            if a.strip()
        ]

        date_str = msg.get("Date", "")
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            date_iso = parsed_date.isoformat()
        except Exception:
            date_iso = date_str

        text_body, html_body = _get_email_body(msg)
        attachments = _get_attachments_info(msg)

        return {
            "id": email_id,
            "message_id": msg.get("Message-ID", ""),
            "subject": _decode_header_value(
                msg.get("Subject", "(제목 없음)")
            ),
            "from": from_info,
            "to": to_list,
            "cc": cc_list,
            "date": date_iso,
            "body_text": text_body,
            "body_html": html_body,
            "attachments": attachments,
            "attachments_count": len(attachments),
            "is_read": "\\Seen" in flags_data,
            "is_starred": "\\Flagged" in flags_data,
            "folder": folder,
            "reply_to": msg.get("Reply-To", ""),
            "in_reply_to": msg.get("In-Reply-To", ""),
        }
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def mark_email(folder: str, email_id: str, action: str) -> bool:
    """Mark email as read/unread/starred/unstarred

    action: 'read', 'unread', 'star', 'unstar'
    """
    conn = connect_imap()
    try:
        status, data = conn.select(folder)
        if status != "OK":
            return False

        eid = (
            email_id.encode() if isinstance(email_id, str) else email_id
        )

        if action == "read":
            conn.store(eid, "+FLAGS", "\\Seen")
        elif action == "unread":
            conn.store(eid, "-FLAGS", "\\Seen")
        elif action == "star":
            conn.store(eid, "+FLAGS", "\\Flagged")
        elif action == "unstar":
            conn.store(eid, "-FLAGS", "\\Flagged")
        else:
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to mark email {email_id}: {e}")
        return False
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def delete_email(folder: str, email_id: str) -> bool:
    """Move email to trash"""
    conn = connect_imap()
    try:
        status, data = conn.select(folder)
        if status != "OK":
            return False

        eid = (
            email_id.encode() if isinstance(email_id, str) else email_id
        )
        conn.store(eid, "+FLAGS", "\\Deleted")
        conn.expunge()
        return True
    except Exception as e:
        logger.error(f"Failed to delete email {email_id}: {e}")
        return False
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def download_attachment(folder: str, email_id: str, filename: str) -> Optional[dict]:
    """Download attachment content from email"""
    conn = connect_imap()
    try:
        status, data = conn.select(folder, readonly=True)
        if status != "OK":
            return None

        status, msg_data = conn.fetch(email_id.encode(), "(RFC822)")
        if status != "OK" or not msg_data or not msg_data[0]:
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    att_filename = part.get_filename()
                    if att_filename:
                        att_filename = _decode_header_value(att_filename)
                        if att_filename == filename:
                            content = part.get_payload(decode=True)
                            return {
                                "filename": att_filename,
                                "content_type": part.get_content_type(),
                                "content": content,
                                "size": len(content) if content else 0,
                            }
        return None
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def test_imap_connection() -> dict:
    """Test IMAP connection and return status"""
    config = get_imap_config()
    try:
        conn = connect_imap()
        # Get inbox count
        status, data = conn.select("INBOX", readonly=True)
        inbox_count = int(data[0]) if status == "OK" else 0

        # Get folders
        folders = list_folders()

        conn.logout()
        return {
            "success": True,
            "host": config["host"],
            "username": config["username"],
            "inbox_count": inbox_count,
            "folders": len(folders),
            "message": f"IMAP 연결 성공 -- 받은편지함 {inbox_count}통",
        }
    except Exception as e:
        return {
            "success": False,
            "host": config.get("host", ""),
            "username": config.get("username", ""),
            "error": str(e),
            "message": f"IMAP 연결 실패: {str(e)}",
        }
