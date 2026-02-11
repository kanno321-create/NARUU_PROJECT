"""비밀번호 해싱 — bcrypt 기반."""

from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """평문 비밀번호와 해시 비교."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
