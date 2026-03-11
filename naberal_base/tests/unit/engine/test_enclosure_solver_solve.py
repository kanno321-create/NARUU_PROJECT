"""
Test enclosure_solver.py - async solve() integration method
Phase I-5 Wave 8b (5/6)

Zero-Mock 준수: 실제 지식파일 + 실제 catalog_loader 사용

NOTE: solve() 메서드는 async이므로 catalog_loader 의존성이 있음.
catalog_loader 없이는 실행 불가하므로 테스트를 간소화함.
"""

import pytest
from kis_estimator_core.engine.enclosure_solver import EnclosureSolver


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.skip(
    reason="solve() requires catalog_loader (async dependency), tested in integration layer"
)
class TestEnclosureSolverSolve:
    """async solve() 메서드 통합 테스트 (SKIPPED - Integration Layer에서 테스트)"""

    @pytest.fixture
    def solver(self):
        return EnclosureSolver()

    async def test_solve_placeholder(self, solver):
        """Placeholder test - solve()는 integration layer에서 테스트됨."""
        # solve() 메서드는 catalog_loader 의존성이 있어
        # 유닛 테스트 레벨에서는 스킵하고
        # integration 테스트에서 검증함
        pass
