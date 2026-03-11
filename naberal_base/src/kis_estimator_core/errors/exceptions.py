"""
KIS Estimator 예외 클래스
"""

from typing import Any

from .error_codes import ErrorCode


class EstimatorError(Exception):
    """견적 시스템 기본 예외 (LAW-04 AppError 스키마 준수)"""

    def __init__(
        self,
        error_code: ErrorCode,
        details: dict[str, Any] | None = None,
        phase: str | None = None,
    ):
        self.error_code = error_code
        self.details = details or {}
        self.phase = phase

        # LAW-04: AppError 스키마 속성 제공
        self.code = error_code.code
        self.message = error_code.message
        self.hint = error_code.hint
        self.meta = self.details

        message = f"[{error_code.code}] {error_code.message}"
        if phase:
            message = f"[Phase: {phase}] {message}"

        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        return {
            "code": self.error_code.code,
            "category": self.error_code.category.value,
            "severity": self.error_code.severity.value,
            "message": self.error_code.message,
            "hint": self.error_code.hint,
            "blocking": self.error_code.blocking,
            "phase": self.phase,
            "details": self.details,
        }


class ValidationError(EstimatorError):
    """검증 실패 예외"""

    def __init__(
        self,
        error_code: ErrorCode,
        field: str | None = None,
        value: Any | None = None,
        expected: Any | None = None,
        phase: str | None = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if expected is not None:
            details["expected"] = expected

        super().__init__(error_code, details, phase)


class CatalogError(EstimatorError):
    """카탈로그 검색 실패 예외"""

    def __init__(
        self,
        error_code: ErrorCode,
        item_type: str | None = None,
        search_params: dict[str, Any] | None = None,
        phase: str | None = None,
    ):
        details = {}
        if item_type:
            details["item_type"] = item_type
        if search_params:
            details["search_params"] = search_params

        super().__init__(error_code, details, phase)


class PhaseBlockedError(EstimatorError):
    """단계 진행 차단 예외"""

    def __init__(
        self, blocking_errors: list[EstimatorError], current_phase: str, next_phase: str
    ):
        self.blocking_errors = blocking_errors
        self.current_phase = current_phase
        self.next_phase = next_phase

        # 첫 번째 blocking 에러를 대표로 사용
        first_error = blocking_errors[0].error_code

        details = {
            "current_phase": current_phase,
            "next_phase": next_phase,
            "blocking_count": len(blocking_errors),
            "error_codes": [e.error_code.code for e in blocking_errors],
        }

        super().__init__(first_error, details, current_phase)

    def to_dict(self) -> dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        base = super().to_dict()
        base["blocking_errors"] = [e.to_dict() for e in self.blocking_errors]
        return base
