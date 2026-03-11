"""
ERP Write Adapter - 쓰기 경로 가드 (Phase 4: disabled stub)

절대 원칙:
- FeatureFlag("erp.write=false") 기본값
- 모든 write 메서드 → AppError(code="ERP_WRITE_DISABLED")
- 실제 DB/API 쓰기 없음 (더미/목업 금지)
- Phase 5 이후 운영 활성화 시 구현 예정
"""

import os
from typing import Dict, Any


class ERPWriteDisabledError(Exception):
    """ERP 쓰기 비활성화 예외 (Phase 4 scaffold)"""

    def __init__(self, message: str, meta: Dict[str, Any]):
        self.code = "ERP_WRITE_DISABLED"
        self.message = message
        self.meta = meta
        super().__init__(message)


class ERPWriteAdapter:
    """
    ERP 쓰기 경로 어댑터 (Phase 4: disabled stub)

    모든 write 메서드는 FeatureFlag로 차단됨:
    - journal_entry()
    - inventory_adjust()
    - invoice_issue()
    """

    def __init__(self):
        """
        FeatureFlag 확인: ERP_WRITE_ENABLED 환경변수 (기본값: false)
        """
        self.write_enabled = os.getenv("ERP_WRITE_ENABLED", "false").lower() == "true"

    def _check_write_enabled(self) -> None:
        """
        쓰기 가드: FeatureFlag 확인 후 차단

        Raises:
            ERPWriteDisabledError: ERP_WRITE_DISABLED (write_enabled=false)
        """
        if not self.write_enabled:
            raise ERPWriteDisabledError(
                message="ERP 쓰기 경로는 비활성화되어 있습니다 (Phase 4 scaffold)",
                meta={
                    "feature_flag": "ERP_WRITE_ENABLED",
                    "current_value": "false",
                    "required_value": "true",
                    "phase": "4-scaffold",
                },
            )

    def journal_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        분개 쓰기 (Phase 4: disabled stub)

        Args:
            data: 분개 데이터

        Returns:
            Dict: 응답 (실제로는 에러)

        Raises:
            AppError: ERP_WRITE_DISABLED
        """
        self._check_write_enabled()
        # Unreachable: _check_write_enabled() always raises ERPWriteDisabledError in Phase 4
        # Phase 5 implementation: actual ERP write logic here

    def inventory_adjust(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        재고 조정 쓰기 (Phase 4: disabled stub)

        Args:
            data: 재고 조정 데이터

        Returns:
            Dict: 응답 (실제로는 에러)

        Raises:
            AppError: ERP_WRITE_DISABLED
        """
        self._check_write_enabled()
        # Unreachable: _check_write_enabled() always raises ERPWriteDisabledError in Phase 4
        # Phase 5 implementation: actual ERP write logic here

    def invoice_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        세금계산서 발행 (Phase 4: disabled stub)

        Args:
            data: 세금계산서 데이터

        Returns:
            Dict: 응답 (실제로는 에러)

        Raises:
            AppError: ERP_WRITE_DISABLED
        """
        self._check_write_enabled()
        # Unreachable: _check_write_enabled() always raises ERPWriteDisabledError in Phase 4
        # Phase 5 implementation: actual ERP write logic here
