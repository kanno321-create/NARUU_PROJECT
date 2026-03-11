"""
Redis Driver - Rate Limit + Idempotency + Health

네임스페이스:
- rl:estimate:<key> (rate limit 토큰버킷)
- idem:estimate:<hash> (idempotency 키)
"""

import hashlib
import json
from typing import Any

import redis


class RedisDriver:
    """Redis 드라이버 (토큰버킷 레이트리밋 + idempotency)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        """
        Args:
            host: Redis 호스트
            port: Redis 포트
            db: Redis DB 번호
            password: Redis 비밀번호
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )

    def ping(self) -> bool:
        """Redis 연결 확인"""
        try:
            return self.client.ping()
        except Exception:
            return False

    def health_check(self) -> dict[str, Any]:
        """Health check (readyz 용)"""
        try:
            is_connected = self.ping()
            info = self.client.info() if is_connected else {}
            return {
                "status": "connected" if is_connected else "disconnected",
                "connected": is_connected,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
            }

    # ========================================
    # Rate Limit (Token Bucket)
    # ========================================
    def check_rate_limit(
        self,
        key: str,
        rate: int = 100,
        burst: int = 300,
        window: int = 60,
    ) -> bool:
        """
        토큰버킷 레이트리밋 확인

        Args:
            key: 레이트리밋 키 (예: "user:123")
            rate: 초당 요청 수
            burst: 버스트 허용 (최대 토큰)
            window: 시간 윈도우 (초)

        Returns:
            bool: 허용 여부 (True=허용, False=차단)
        """
        rl_key = f"rl:estimate:{key}"

        # 현재 토큰 수 가져오기
        tokens_str = self.client.get(rl_key)
        if tokens_str is None:
            # 첫 요청: 버스트 허용 - 1
            tokens = burst - 1
            self.client.setex(rl_key, window, str(tokens))
            return True

        tokens = float(tokens_str)

        # 토큰 재충전 (시간 경과에 따라)

        # 간단 구현: 1초당 rate 토큰 재충전
        tokens = min(tokens + rate / window, burst)

        # 토큰 소비
        if tokens >= 1:
            self.client.setex(rl_key, window, str(tokens - 1))
            return True
        else:
            return False

    # ========================================
    # Idempotency
    # ========================================
    def get_idempotency_key(self, payload: dict[str, Any]) -> str:
        """
        Idempotency 키 생성 (payload SHA256 해시)

        Args:
            payload: 요청 페이로드

        Returns:
            str: 해시 키
        """
        payload_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_json.encode()).hexdigest()

    def check_idempotency(
        self,
        idem_hash: str,
        ttl: int = 86400,
    ) -> str | None:
        """
        Idempotency 확인 (중복 요청 차단)

        Args:
            idem_hash: Idempotency 해시
            ttl: TTL (초, 기본 24시간)

        Returns:
            Optional[str]: 이미 처리된 경우 결과 ID, 아니면 None
        """
        idem_key = f"idem:estimate:{idem_hash}"
        result_id = self.client.get(idem_key)
        return result_id

    def set_idempotency(
        self,
        idem_hash: str,
        result_id: str,
        ttl: int = 86400,
    ):
        """
        Idempotency 저장 (처리 완료 표시)

        Args:
            idem_hash: Idempotency 해시
            result_id: 결과 ID
            ttl: TTL (초, 기본 24시간)
        """
        idem_key = f"idem:estimate:{idem_hash}"
        self.client.setex(idem_key, ttl, result_id)

    # ========================================
    # Namespace Probe (for /readyz)
    # ========================================
    def probe_namespaces(self) -> dict[str, int]:
        """
        네임스페이스별 키 개수 확인 (헬스 체크용)

        Returns:
            Dict[str, int]: 네임스페이스별 키 개수
        """
        try:
            rl_count = len(self.client.keys("rl:estimate:*"))
            idem_count = len(self.client.keys("idem:estimate:*"))
            return {
                "rate_limit_keys": rl_count,
                "idempotency_keys": idem_count,
            }
        except Exception:
            return {
                "rate_limit_keys": 0,
                "idempotency_keys": 0,
            }
