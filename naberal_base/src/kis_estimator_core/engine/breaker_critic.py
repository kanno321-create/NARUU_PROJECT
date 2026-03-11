"""
Stage 2.1: Breaker Critic - FIX-4 Pipeline
배치 결과 검증 및 개선 권장사항 생성

Quality Gates (개수 기반):
- 상평형: R/S/T 개수 균등 (diff_max ≤ 1, MANDATORY)
- 간섭 위반 = 0 (MANDATORY)
- 성능: < 200ms (목표), < 500ms (최대)

⚠️ 열(Thermal) 관련 검증은 우리 업무와 무관하여 제거됨 (대표님 지시 2025-10-05)
⚠️ 전류 기반 상평형 폐기, 개수 기반으로 전환 (대표님 지시 2025-10-05)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

if TYPE_CHECKING:
    from kis_estimator_core.engine.breaker_placer import PlacementResult

# SSOT Integration (Count-Based Phase Balance)
from ..core.ssot.constants import MAX_COUNT_DIFF, TARGET_COUNT_DIFF

logger = logging.getLogger(__name__)


# Critical thresholds - 개수 기반 실무 기준
MAX_LIMITS = {
    "diff_max": MAX_COUNT_DIFF,  # R/S/T 개수 최대 차이 (0=완벽, 1=허용)
    "clearances_violation": 0,  # SPEC: 0 (MANDATORY)
    "min_clearance_mm": 50,  # 최소 간격 (mm)
}


@dataclass
class ViolationDetail:
    """위반 사항 상세"""

    type: str  # "phase_imbalance", "clearance", "position"
    severity: str  # "critical", "error", "warning"
    message: str
    cause: str
    recommendation: str
    value: float | None = None
    limit: float | None = None
    count: int | None = None
    position: str | None = None
    breaker_id: str | None = None


@dataclass
class CriticResult:
    """검증 결과 (Stage 2.1 출력)"""

    passed: bool  # 모든 검증 통과 여부
    score: int  # 점수 (0-100)
    violations: list[str] = field(default_factory=list)  # 위반 메시지 목록
    warnings: list[str] = field(default_factory=list)  # 경고 메시지 목록
    violation_details: list[ViolationDetail] = field(
        default_factory=list
    )  # 상세 위반 사항
    phase_imbalance_pct: float = 0.0
    clearance_violations: int = 0
    thresholds: dict[str, float] = field(default_factory=lambda: MAX_LIMITS.copy())
    metrics: dict[str, any] = field(default_factory=dict)


class BreakerCritic:
    """
    차단기 배치 검증 엔진 (Stage 2.1)

    검증 항목:
    1. 상평형 ≤ 80.0% (고정 RST 순환)
    2. 간섭 위반 = 0
    3. 위치 경계 검증
    """

    def __init__(self):
        self.max_limits = MAX_LIMITS.copy()

    def critique(
        self,
        placements: list["PlacementResult"],
        diff_max: float = 0.0,
        clearance_violations: int = 0,
    ) -> CriticResult:
        """
        배치 결과 검증 (개수 기반)

        Args:
            placements: 배치 결과 목록 (PlacementResult 리스트)
            diff_max: 상평형 개수 차이 (max - min, 0=완벽 균등)
            clearance_violations: 간섭 위반 수

        Returns:
            CriticResult: 검증 결과

        Raises:
            ValueError: 입력이 비어있는 경우 (목업 금지 원칙)
        """
        if not placements:
            raise_error(
                ErrorCode.E_INTERNAL,
                "No placements provided. Mock data generation is FORBIDDEN.",
            )

        violations = []
        warnings = []
        violation_details = []

        # 1. 상평형 검사 (개수 기반: diff_max ≤ 1)
        if diff_max > self.max_limits["diff_max"]:
            violation = ViolationDetail(
                type="phase_count_imbalance",
                severity="critical",
                value=diff_max,
                limit=self.max_limits["diff_max"],
                message=f"Phase count imbalance diff_max={int(diff_max)} exceeds limit={self.max_limits['diff_max']}",
                cause="Uneven distribution of branch breakers across R/S/T phases",
                recommendation="Redistribute breakers using round-robin R→S→T pattern",
            )
            violations.append(violation.message)
            violation_details.append(violation)
        elif diff_max == TARGET_COUNT_DIFF:
            # diff_max == 0: 완벽한 균등
            logger.info(f"Perfect phase balance: diff_max={int(diff_max)} (완전 균등)")

        # 2. 간섭 검증
        if clearance_violations > self.max_limits["clearances_violation"]:
            violation = ViolationDetail(
                type="clearance",
                severity="critical",
                count=clearance_violations,
                message=f"Found {clearance_violations} clearance violations",
                cause="Breakers placed too close together",
                recommendation=f"Ensure minimum {self.max_limits['min_clearance_mm']}mm clearance between breakers",
            )
            violations.append(violation.message)
            violation_details.append(violation)

        # 3. 개별 슬롯 위치 검증
        for placement in placements:
            row = placement.position.get("row", 0)
            col = placement.position.get("col", 0)

            # 위치 경계 검사 (row: 0~20, col: 0~1)
            if row < 0 or row > 20:
                violation = ViolationDetail(
                    type="position",
                    severity="error",
                    breaker_id=placement.breaker_id,
                    position=f"row={row}, col={col}",
                    message=f"Breaker {placement.breaker_id} at invalid row {row}",
                    cause="Position outside panel boundaries",
                    recommendation="Ensure row within 0-20 range",
                )
                violations.append(violation.message)
                violation_details.append(violation)

        # 점수 계산
        score = 100
        score -= len(violations) * 20
        score -= len(warnings) * 5
        score = max(0, score)

        # 결과 생성 (개수 기반)
        result = CriticResult(
            passed=len(violations) == 0,
            score=score,
            violations=violations,
            warnings=warnings,
            violation_details=violation_details,
            phase_imbalance_pct=diff_max,  # 개수 차이 (이전: 전류 기반 %)
            clearance_violations=clearance_violations,
            thresholds=self.max_limits.copy(),
            metrics={
                "diff_max": diff_max,  # 개수 차이
                "clearance_violations": clearance_violations,
                "slot_count": len(placements),
            },
        )

        # 로깅
        if result.passed:
            logger.info(
                f"✅ Placement passed all checks (score={result.score}, slots={len(placements)})"
            )
        else:
            logger.error(
                f"❌ Placement has {len(result.violations)} violations (score={result.score})"
            )
            for v in result.violations:
                logger.error(f"   - {v}")

        return result

    def generate_svg_evidence(
        self, result: CriticResult, output_path: Path | None = None
    ) -> str:
        """
        SVG 시각화 Evidence 생성

        Args:
            result: 검증 결과
            output_path: 출력 파일 경로 (optional)

        Returns:
            SVG 문자열
        """
        svg_parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">',
            '<rect width="100%" height="100%" fill="#f8f8f8" stroke="#333" stroke-width="2"/>',
            '<text x="300" y="30" text-anchor="middle" font-size="20" font-weight="bold">Placement Critique</text>',
        ]

        # 상태 표시
        status_color = "#4caf50" if result.passed else "#f44336"
        status_text = "PASSED" if result.passed else "FAILED"
        svg_parts.append(
            f'<rect x="250" y="50" width="100" height="30" fill="{status_color}" rx="5"/>'
        )
        svg_parts.append(
            f'<text x="300" y="70" text-anchor="middle" font-size="14" fill="white">{status_text}</text>'
        )

        # 점수 표시
        svg_parts.append(
            f'<text x="300" y="110" text-anchor="middle" font-size="16">Score: {result.score}/100</text>'
        )

        # 위반 사항 표시 (최대 5개)
        y_pos = 150
        for _i, detail in enumerate(result.violation_details[:5]):
            svg_parts.append(f'<circle cx="50" cy="{y_pos}" r="8" fill="#f44336"/>')
            msg = detail.message[:50] if detail.message else ""
            svg_parts.append(
                f'<text x="70" y="{y_pos + 5}" font-size="12">{detail.type}: {msg}...</text>'
            )
            y_pos += 30

        # 메트릭스 표시
        svg_parts.append(
            f'<text x="50" y="320" font-size="14">Phase Imbalance: {result.phase_imbalance_pct:.2f}%</text>'
        )
        svg_parts.append(
            f'<text x="50" y="340" font-size="14">Clearance Violations: {result.clearance_violations}</text>'
        )
        svg_parts.append(
            f'<text x="50" y="360" font-size="14">Violations: {len(result.violations)} | Warnings: {len(result.warnings)}</text>'
        )

        svg_parts.append("</svg>")
        svg_content = "\n".join(svg_parts)

        # 파일 저장 (optional)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(svg_content, encoding="utf-8")
            logger.info(f"📊 SVG evidence saved to {output_path}")

        return svg_content
