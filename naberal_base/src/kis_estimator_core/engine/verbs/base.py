"""
BaseVerb - Verb 추상 클래스

I-3.2: ExecutionCtx 기반 규약 통일
LAW-02: SSOT 준수
LAW-04: AppError 스키마 일관성
LAW-05: 단일 책임 원칙
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from ...core.ssot.errors import ErrorCode, raise_error
from ..context import ExecutionCtx

logger = logging.getLogger(__name__)


class BaseVerb(ABC):
    """
    Verb 추상 클래스

    모든 Verb는 이 클래스를 상속받아 구현.

    규칙:
    1. __init__(params: VerbParamsBase, ctx: ExecutionCtx) 시그니처 준수
    2. params는 필수 (None 불허)
    3. async def run() → None 구현 필수
    4. self.params/self.ctx.state만 사용 (dict 직접 접근 금지)

    에러 처리:
    - params 누락 → ErrorCode.VERB_001
    - 알 수 없는 verb → ErrorCode.VERB_002 (Factory에서 처리)
    - 선행조건 미충족 → ErrorCode.VERB_001 (verb별 validate)
    """

    def __init__(self, params: Any, *, ctx: ExecutionCtx):
        """
        Verb 초기화

        Args:
            params: VerbParams (Pydantic 모델, SSOT 기반)
            ctx: ExecutionCtx (SSOT, DB, Logger, state 포함)

        Raises:
            AppError: params 누락 시 (ErrorCode.VERB_001)
        """
        if params is None:
            raise_error(
                ErrorCode.E_INTERNAL,
                "Verb params required",
                hint="VerbParams missing",
                meta={"verb": self.__class__.__name__},
            )

        self.params = params
        self.ctx = ctx
        self.logger = ctx.logger

    @abstractmethod
    async def run(self) -> None:
        """
        Verb 실행 (추상 메서드)

        구현 규칙:
        1. self.ctx.state에서 입력 데이터 조회
        2. 비즈니스 로직 실행 (REAL engines - NO MOCKS)
        3. self.ctx.state에 결과 저장
        4. 실패 시 raise_error(ErrorCode.XXX, ...) 호출

        Returns:
            None (결과는 ctx.state에 저장)

        Raises:
            AppError: 실행 실패 시
        """
        pass

    def validate_context(self, required_keys: list[str]) -> None:
        """
        선행조건 검증 (필수 state 키 확인)

        Args:
            required_keys: 필수 state 키 목록

        Raises:
            AppError: 필수 키 누락 시 (ErrorCode.VERB_001)
        """
        missing = [key for key in required_keys if not self.ctx.has_state(key)]
        if missing:
            available = list(self.ctx.state.keys())
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Missing required context keys: {missing}",
                hint=f"Verb {self.__class__.__name__} requires {required_keys}",
                meta={
                    "verb": self.__class__.__name__,
                    "missing_keys": missing,
                    "available_keys": available,
                    "requires": required_keys,
                },
            )

    def log_execution_start(self) -> None:
        """Verb 실행 시작 로그"""
        verb_name = self.__class__.__name__
        params_str = (
            str(self.params) if hasattr(self.params, "__dict__") else str(self.params)
        )
        self.logger.info(f"Verb {verb_name} starting: {params_str}")

    def log_execution_end(self, success: bool = True) -> None:
        """Verb 실행 종료 로그"""
        verb_name = self.__class__.__name__
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Verb {verb_name} {status}")


class VerbParamsBase:
    """
    VerbParams 기본 클래스 (Placeholder)

    I-3.3: Future improvement - Replace with SSOT generated_verbs.py Pydantic models
    현재는 SimpleNamespace로 대체 (I-3.1 임시 구현)

    Future:
    - from ...core.ssot.generated_verbs import (
        PickEnclosureParams, PlaceParams, RebalanceParams, TryParams
      )
    """

    pass
