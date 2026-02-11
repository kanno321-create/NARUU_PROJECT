"""파이프라인 단계 핸들러 ABC + 결과 데이터클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from naruu_core.models.content import Content


@dataclass
class StageResult:
    """파이프라인 단계 실행 결과.

    Attributes:
        success: 성공 여부.
        next_stage: 성공 시 다음 단계명, 실패 시 "failed".
        data: 생성된 데이터 (script, image_url 등).
        error: 실패 시 에러 메시지.
        cost_usd: 이 단계의 API 비용 (USD).
    """

    success: bool
    next_stage: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    cost_usd: float = 0.0


class StageHandler(ABC):
    """파이프라인 단계 핸들러 추상 클래스.

    각 파이프라인 단계(script, image, voice 등)는 이 클래스를 상속하여
    execute()를 구현한다.
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """이 핸들러가 처리하는 단계 이름."""

    @abstractmethod
    async def execute(self, content: Content, config: dict[str, Any]) -> StageResult:
        """파이프라인 단계 실행.

        Args:
            content: 처리할 콘텐츠 레코드.
            config: AI 모델, 토큰 수 등 설정.

        Returns:
            StageResult — 성공/실패, 다음 단계, 생성 데이터, 비용.
        """
