"""
ExecutionCtx - Verb 실행 컨텍스트 표준화

I-3.2: Executor ↔ Verb 컨텍스트 전파 규약 확정
LAW-02: SSOT 단일출처 원칙 준수
LAW-04: AppError 스키마 일관성
"""

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionCtx:
    """
    Verb 실행 컨텍스트

    Verb 간 상태 전파를 위한 표준 컨테이너.
    SSOT, DB, Logger는 주입받고, state는 dict로 Verb 간 데이터 전달.

    Attributes:
        ssot: SSOT 래퍼 (generated.py에서 로드)
        db: AsyncSession 또는 Repository (Async SQLAlchemy)
        logger: 로깅 인스턴스
        state: Verb 간 공유 상태 (key는 SSOT 문서화된 것만 허용)

    Allowed state keys (SSOT documented):
        - "enclosure": 외함 객체 (SSOT 스키마)
        - "dimensions": 외함 치수 {width_mm, height_mm, depth_mm}
        - "placements": 배치 목록 (list)
        - "bom": BOM 중간산출 (선택)
        - "main_breaker": 메인 차단기 정보 (dict or BreakerSpec)
        - "branch_breakers": 분기 차단기 목록 (list)
        - "breakers": 전체 차단기 목록 (BreakerInput list)
        - "panel_spec": 패널 사양 (dict or PanelSpec)
        - "estimate_data": 견적 데이터 (EstimateData)

    금지: 임의 키 신규 도입 (필요 시 SSOT 문서에 추가 후 진행)
    """

    ssot: Any  # SSOT 래퍼 (generated.py SSOT constants)
    logger: logging.Logger
    db: Any | None = None  # AsyncSession/Repo (Supabase/Postgres)
    state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """초기화 후 검증"""
        if self.ssot is None:
            raise ValueError("ExecutionCtx.ssot is required (SSOT 래퍼 주입 필수)")
        if self.logger is None:
            raise ValueError("ExecutionCtx.logger is required")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        안전한 state 조회

        Args:
            key: State key (SSOT 문서화된 키만 허용)
            default: 기본값

        Returns:
            state[key] or default
        """
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """
        State 설정

        Args:
            key: State key (SSOT 문서화된 키만 허용)
            value: 값 (SSOT 스키마 객체 권장)
        """
        self.state[key] = value

    def require_state(self, key: str) -> Any:
        """
        필수 state 조회 (없으면 ValueError)

        Args:
            key: State key

        Returns:
            state[key]

        Raises:
            ValueError: key 없음
        """
        if key not in self.state:
            raise ValueError(
                f"Required state key '{key}' not found. "
                f"Available keys: {list(self.state.keys())}"
            )
        return self.state[key]

    def has_state(self, key: str) -> bool:
        """
        State 존재 여부 확인

        Args:
            key: State key

        Returns:
            bool
        """
        return key in self.state

    def clear_state(self) -> None:
        """State 전체 초기화"""
        self.state.clear()

    def snapshot(self) -> dict[str, Any]:
        """
        현재 state 스냅샷 (Evidence 목적)

        Returns:
            state 복사본 (shallow copy)
        """
        return self.state.copy()

    def merge_state(self, updates: dict[str, Any]) -> None:
        """
        State 병합 (기존 값 덮어쓰기)

        Args:
            updates: 병합할 dict
        """
        self.state.update(updates)
