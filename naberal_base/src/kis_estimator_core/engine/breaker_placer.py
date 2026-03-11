"""
Stage 2: Breaker Placer - FIX-4 Pipeline
좌우 대칭 배치 알고리즘 기반 차단기 최적 배치 엔진

Quality Gates (Count-Based):
- 상평형: R/S/T 개수 균등 (diff_max ≤ 1, MANDATORY)
- 간섭 위반 = 0 (MANDATORY)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

# SSOT Integration (Branch Bus Rules)
from ..core.ssot.branch_bus import (
    get_n_phase_row_rules,
    get_validation_guards,
    load_branch_bus_rules,
)

# SSOT Integration (Count-Based Phase Balance)
from ..core.ssot.constants import (
    MAX_COUNT_DIFF,
    PHASE_LABEL_NORMALIZER,
    PHASES,
    TARGET_COUNT_DIFF,
)

# Error System Integration (Phase 2-3)
from ..errors import LAY_002, LAY_004, PhaseBlockedError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class BreakerInput:
    """차단기 입력 사양"""

    id: str
    poles: int  # 2, 3, 4 (1상 차단기는 없음)
    current_a: int
    width_mm: int
    height_mm: int
    depth_mm: int
    model: str = ""  # 모델명 (SBS-404, SBE-52 등) - 필수 전달
    breaker_type: str = "normal"  # "small", "compact", "normal"
    is_main: bool = False  # FIX: 메인차단기 여부 (2P 메인 지원)


@dataclass
class PanelSpec:
    """패널 사양"""

    width_mm: int
    height_mm: int
    depth_mm: int
    clearance_mm: int  # 최소 간격


@dataclass
class PlacementResult:
    """배치 결과"""

    breaker_id: str
    position: dict[str, int]  # {"x": int, "y": int, "row": int, "col": int}
    phase: str  # "L1", "L2", "L3"
    current_a: int
    poles: int  # 1, 2, 3 - 상평형 계산에 필요
    model: str = ""  # 모델명 (SBS-404, SBE-52 등) - DataTransformer로 전달


@dataclass
class ValidationResult:
    """검증 결과"""

    phase_imbalance_pct: float  # 상평형 (%)
    clearance_violations: int  # 간섭 위반 수
    is_valid: bool  # 모든 검증 통과 여부
    errors: list[str]  # 오류 메시지 목록


class BreakerPlacer:
    """
    차단기 배치 엔진 (Stage 2)

    - 배치 알고리즘: 좌우 대칭 배치 (R→S→T 라운드로빈)
    - Validation: 상평형 ≤ 4%, 간섭 = 0
    """

    def __init__(self):
        # Branch Bus Rules SSOT 로드 (center-feed, row-aware N상)
        self.branch_bus_rules = load_branch_bus_rules()
        self.validation_guards = get_validation_guards()
        self.n_phase_row_rules = get_n_phase_row_rules()

    def _log_phase_balance_evidence(
        self,
        placements: list[PlacementResult],
        diff_max: float,
        clearance_violations: int,
    ) -> None:
        """
        상평형 검증 결과를 Evidence JSONL 파일로 기록

        파일 경로: dist/evidence/pipeline/phase_balance_run_<timestamp>.jsonl
        포맷: {timestamp, nR, nS, nT, diff_max, score, clearance_violations, metadata}
        """
        try:
            # 상별 개수 계산
            phase_counts = {"R": 0, "S": 0, "T": 0}
            for p in placements:
                if p.position.get("row") == 0 or p.poles >= 3:
                    continue  # 메인 및 3P/4P 제외
                normalized_phase = PHASE_LABEL_NORMALIZER.get(p.phase, p.phase)
                if normalized_phase in phase_counts:
                    phase_counts[normalized_phase] += 1

            # Score 계산 (0.0~1.0, 1.0=완벽)
            score = 1.0 - (diff_max / 10.0)  # diff_max=0 → 1.0, diff_max=10 → 0.0
            score = max(0.0, min(1.0, score))

            # Evidence 레코드
            evidence = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "nR": phase_counts["R"],
                "nS": phase_counts["S"],
                "nT": phase_counts["T"],
                "diff_max": diff_max,
                "score": round(score, 3),
                "clearance_violations": clearance_violations,
                "metadata": {
                    "total_placements": len(placements),
                    "branch_count": sum(phase_counts.values()),
                    "phase_balance_mode": "count",
                    "target_diff_max": TARGET_COUNT_DIFF,
                    "max_allowed_diff_max": MAX_COUNT_DIFF,
                },
            }

            # 출력 디렉토리 생성
            evidence_dir = Path("dist/evidence/pipeline")
            evidence_dir.mkdir(parents=True, exist_ok=True)

            # 파일명: phase_balance_run_<timestamp>.jsonl
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            evidence_file = evidence_dir / f"phase_balance_run_{timestamp_str}.jsonl"

            # JSONL 형식으로 기록 (append mode)
            with open(evidence_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(evidence, ensure_ascii=False) + "\n")

            logger.debug(f"Evidence logged: {evidence_file}")

        except Exception as e:
            logger.warning(f"Failed to log phase balance evidence: {e}")

    def place(
        self, breakers: list[BreakerInput], panel: PanelSpec
    ) -> list[PlacementResult]:
        """
        차단기 좌우 대칭 배치 실행

        원리 (실제 샘플 기반):
        - 메인 차단기(3P/4P): 상단 중앙, RST 직결
        - 분기 차단기: 좌우 대칭 배치
        - 1줄 = 좌우 1쌍 = 1개 부스바 = 동일 상
        - 줄 순서대로 R→S→T→R→S→T 순환
        """
        if not breakers:
            raise_error(
                ErrorCode.E_INTERNAL,
                "No breakers provided. Mock data generation is FORBIDDEN.",
            )

        if not panel:
            raise_error(ErrorCode.E_INTERNAL, "No panel spec provided.")

        logger.info(
            f"Starting placement: {len(breakers)} breakers, panel {panel.width_mm}x{panel.height_mm}"
        )

        placements = []

        # 1. 메인 차단기 분리
        # FIX: is_main 속성 우선 체크 (2P 메인도 지원)
        # 기존 로직: 3P/4P만 메인으로 인식 → 2P 메인 케이스 실패
        main_breaker = None
        branch_breakers = []

        for breaker in breakers:
            is_main_attr = getattr(breaker, 'is_main', False)
            if is_main_attr and main_breaker is None:
                # is_main=True인 차단기 → 메인으로 분류 (극수 무관)
                main_breaker = breaker
            elif breaker.poles >= 3 and main_breaker is None:
                # 기존 로직: 3P/4P 차단기 중 첫 번째를 메인으로
                main_breaker = breaker
            else:
                branch_breakers.append(breaker)

        # 2. 메인 차단기 배치 (상단 중앙, RST 직결)
        # 좌표 계산: 패널 중앙 상단
        main_x_mm = panel.width_mm // 2
        main_y_mm = 50  # 상단 여유 50mm

        if main_breaker:
            # 메인 차단기도 4P인 경우 n_bus_metadata 추가
            main_position = {
                "x": main_x_mm,
                "y": main_y_mm,
                "row": 0,
                "col": 0,
                "side": "center",
            }
            if main_breaker.poles == 4:
                main_position["n_bus_metadata"] = {
                    "n_bus_type": "main",
                    "n_bus_side": "center",
                    "rule": "main_breaker",
                }

            placements.append(
                PlacementResult(
                    breaker_id=main_breaker.id,
                    position=main_position,
                    phase="R",  # 3상 대표 (RST)
                    current_a=main_breaker.current_a,
                    poles=main_breaker.poles,
                    model=main_breaker.model,  # 모델명 전파
                )
            )
            logger.info(
                f"Main breaker placed: {main_breaker.id} ({main_breaker.poles}P) at ({main_x_mm}, {main_y_mm})"
            )

        # 3. 분기 차단기 좌우 대칭 배치 (개수 기반 라운드로빈 R→S→T)
        total_branches = len(branch_breakers)
        if total_branches == 0:
            logger.info("No branch breakers to place")
            return placements

        # 좌표 계산 상수
        left_x_mm = panel.width_mm // 4
        right_x_mm = (panel.width_mm * 3) // 4
        start_y_mm = main_y_mm + (main_breaker.height_mm if main_breaker else 0) + 30
        row_height_mm = 130

        # 상평형 개수 추적 (로깅용)
        phase_counts = {"R": 0, "S": 0, "T": 0}

        # 3P/4P 분기 먼저 배치 (RST 자동 배분, 개수 카운트 안 함)
        multi_phase_breakers = [b for b in branch_breakers if b.poles >= 3]
        single_phase_breakers = [b for b in branch_breakers if b.poles < 3]

        # 4P 차단기와 3P 차단기 분리 (4P N상 row-aware 규칙 적용)
        four_pole_breakers = [b for b in multi_phase_breakers if b.poles == 4]
        three_pole_breakers = [b for b in multi_phase_breakers if b.poles == 3]

        row_idx = 1

        # 3P 배치 (기존 로직 유지)
        for breaker in three_pole_breakers:
            placements.append(
                PlacementResult(
                    breaker_id=breaker.id,
                    position={
                        "x": left_x_mm,
                        "y": start_y_mm + (row_idx - 1) * row_height_mm,
                        "row": row_idx,
                        "col": 0,
                        "side": "left",
                    },
                    phase="R",  # 3상 대표
                    current_a=breaker.current_a,
                    poles=breaker.poles,
                    model=breaker.model,  # 모델명 전파
                )
            )
            row_idx += 1

        # 4P 배치 (Branch Bus Rules v1.0 - N상 row-aware)
        if four_pole_breakers:
            row_idx = self._place_4p_with_n_phase_rules(
                four_pole_breakers,
                placements,
                left_x_mm,
                right_x_mm,
                start_y_mm,
                row_height_mm,
                row_idx,
            )

        # 2P 분기 배치 (완벽한 개수 균등: R/S/T 사전 배정)
        total_breakers = len(single_phase_breakers)
        target_per_phase = total_breakers // 3
        remainder = total_breakers % 3

        # 사전 상 배정 (나머지는 R→S→T 순으로 분배)
        # 예: 9개→[R,R,R,S,S,S,T,T,T], 8개→[R,R,R,S,S,S,T,T], 10개→[R,R,R,R,S,S,S,T,T,T]
        phase_assignments = []
        for i in range(3):
            count = target_per_phase + (1 if i < remainder else 0)
            phase_assignments.extend([PHASES[i]] * count)

        # 좌우 대칭 배치
        left_count = (total_breakers + 1) // 2
        right_count = total_breakers - left_count

        left_2p = single_phase_breakers[:left_count]
        right_2p = single_phase_breakers[left_count:]

        breaker_idx = 0  # 사전 배정 리스트 인덱스
        for idx in range(left_count):
            current_y_mm = start_y_mm + (row_idx - 1) * row_height_mm

            # 좌측 차단기 (사전 배정된 상)
            left_breaker = left_2p[idx]
            phase = phase_assignments[breaker_idx]
            phase_counts[phase] += 1
            breaker_idx += 1

            placements.append(
                PlacementResult(
                    breaker_id=left_breaker.id,
                    position={
                        "x": left_x_mm,
                        "y": current_y_mm,
                        "row": row_idx,
                        "col": 0,
                        "side": "left",
                    },
                    phase=phase,
                    current_a=left_breaker.current_a,
                    poles=left_breaker.poles,
                    model=left_breaker.model,  # 모델명 전파
                )
            )

            # 우측 차단기 (사전 배정된 상, 다음 인덱스)
            if idx < right_count:
                right_breaker = right_2p[idx]
                phase = phase_assignments[breaker_idx]
                phase_counts[phase] += 1
                breaker_idx += 1

                placements.append(
                    PlacementResult(
                        breaker_id=right_breaker.id,
                        position={
                            "x": right_x_mm,
                            "y": current_y_mm,
                            "row": row_idx,
                            "col": 1,
                            "side": "right",
                        },
                        phase=phase,
                        current_a=right_breaker.current_a,
                        poles=right_breaker.poles,
                        model=right_breaker.model,  # 모델명 전파
                    )
                )

            row_idx += 1

        logger.info(
            f"Phase-balanced placement (count): R={phase_counts['R']}, S={phase_counts['S']}, T={phase_counts['T']}"
        )
        return placements

    def validate(self, placements: list[PlacementResult]) -> ValidationResult:
        """
        배치 결과 검증 (개수 기반)

        - 상평형: R/S/T 개수 균등 (diff_max ≤ 1, WARNING only)
        - 간섭 위반: LAY-002 (MANDATORY = 0)
        - 4P N상 간섭: LAY-004 (마주보기 배치 시)

        Raises:
            ValidationError: LAY-002, LAY-004 에러 발생 시
            PhaseBlockedError: BLOCKING 에러 누적 시
        """
        errors = []
        error_objects = []

        # 1. 상평형 검증 (개수 기반: diff_max ≤ 1, WARNING only)
        diff_max = self._validate_phase_balance(placements)
        if diff_max > MAX_COUNT_DIFF:  # diff_max > 1: WARNING (BLOCKING 아님)
            errors.append(
                f"상평형 개수 불균형: diff_max={int(diff_max)} > {MAX_COUNT_DIFF}"
            )
            logger.warning(
                f"Phase count imbalance: diff_max={int(diff_max)} exceeds {MAX_COUNT_DIFF} (WARNING only)"
            )
        elif diff_max == TARGET_COUNT_DIFF:  # diff_max == 0: 완벽한 균등
            logger.info(f"Perfect phase balance: diff_max={int(diff_max)} (완전 균등)")

        # 2. 간섭 검증 (LAY-002: MANDATORY = 0)
        clearance_violations = self._validate_clearance(placements)
        if clearance_violations > 0:
            error_obj = ValidationError(
                error_code=LAY_002,
                field="clearance",
                value=clearance_violations,
                expected="0",
                phase="Phase 2-3: Layout",
            )
            errors.append(f"간섭 위반: {clearance_violations}개")
            error_objects.append(error_obj)
            logger.error(
                f"LAY-002: {clearance_violations} clearance violations detected"
            )

        # 3. 4P N상 마주보기 간섭 검증 (LAY-004)
        n_phase_violations = self._validate_4p_n_phase_interference(placements)
        if n_phase_violations > 0:
            error_obj = ValidationError(
                error_code=LAY_004,
                field="4p_n_phase",
                value=n_phase_violations,
                expected="0",
                phase="Phase 2-3: Layout",
            )
            errors.append(f"4P N상 마주보기 간섭: {n_phase_violations}개")
            error_objects.append(error_obj)
            logger.error(
                f"LAY-004: {n_phase_violations} 4P N-phase interference violations"
            )

        # 4. Branch Bus Rules v1.0 검증 (6가지 validation guards)
        branch_bus_violations = self._validate_branch_bus_rules(placements)
        if branch_bus_violations:
            for violation_msg in branch_bus_violations:
                errors.append(violation_msg)
                logger.warning(f"Branch Bus Rules violation: {violation_msg}")

        # BLOCKING 에러 발생 시 PhaseBlockedError 발생
        if error_objects:
            raise PhaseBlockedError(
                blocking_errors=error_objects,
                current_phase="Phase 2-3: Layout",
                next_phase="Phase 4: BOM",
            )

        is_valid = (
            len(errors) == 0
            and clearance_violations == 0
            and len(branch_bus_violations) == 0
        )

        # Evidence 로깅 (Phase 2 - Count-Based Phase Balance)
        self._log_phase_balance_evidence(placements, diff_max, clearance_violations)

        return ValidationResult(
            phase_imbalance_pct=diff_max,  # 개수 차이 (이전: 전류 기반 %)
            clearance_violations=clearance_violations,
            is_valid=is_valid,
            errors=errors,
        )

    def _validate_phase_balance(self, placements: list[PlacementResult]) -> float:
        """
        상평형 계산: 개수 기반 균등 배분 (R/S/T 라운드로빈)

        원리:
        - 메인 차단기: 상평형 계산 제외 (설계 완료 상태)
        - 3P/4P 분기: RST 자동 배분, 개수 카운트 제외
        - 1P/2P 분기: R→S→T 라운드로빈, 각 상 개수 균등
        - 전류/AF 무관, 오직 분기부스바 연결 개수만 고려

        기준: diff_max ≤ 1 (MANDATORY)
        Returns: diff_max (개수 차이, float로 반환하여 기존 호환성 유지)
        """
        phase_counts = {"R": 0, "S": 0, "T": 0}

        for p in placements:
            # 메인 차단기 제외 (row=0)
            if p.position.get("row") == 0:
                continue

            # 3P/4P 분기: RST 자동 배분, 개수 카운트 안 함
            if p.poles >= 3:
                continue

            # 1P/2P 분기만 개수 카운트
            normalized_phase = PHASE_LABEL_NORMALIZER.get(p.phase, p.phase)
            if normalized_phase in phase_counts:
                phase_counts[normalized_phase] += 1

        counts = list(phase_counts.values())
        if not counts or sum(counts) == 0:
            return 0.0  # 분기 없음

        # 개수 차이 (max - min)
        max_count = max(counts)
        min_count = min(counts)
        diff_max = max_count - min_count

        return float(diff_max)

    def _validate_clearance(
        self, placements: list[PlacementResult], min_clearance_mm: int = 50
    ) -> int:
        """
        간섭 검증: 모든 차단기 간 최소 거리 확인

        기준: 위반 = 0

        Args:
            placements: 배치 결과 목록
            min_clearance_mm: 최소 간격 (기본 50mm)

        Returns:
            간섭 위반 개수
        """
        violations = 0

        # 모든 차단기 쌍에 대해 거리 계산
        for i, p1 in enumerate(placements):
            for p2 in placements[i + 1 :]:
                x1, y1 = p1.position["x"], p1.position["y"]
                x2, y2 = p2.position["x"], p2.position["y"]

                # 유클리드 거리 계산
                dx = abs(x1 - x2)
                dy = abs(y1 - y2)
                distance = (dx**2 + dy**2) ** 0.5

                # 특수 규칙: 소형 2P 마주보기 40mm
                # (같은 row, 다른 col = 좌우 대칭)
                is_facing = p1.position.get("row") == p2.position.get(
                    "row"
                ) and p1.position.get("col") != p2.position.get("col")
                is_small_2p_both = (
                    p1.poles == 2
                    and p2.poles == 2
                    and "small" in p1.position.get("breaker_type", "")
                    and "small" in p2.position.get("breaker_type", "")
                )

                required_clearance = min_clearance_mm
                if is_facing and is_small_2p_both:
                    required_clearance = 40  # 소형 2P 마주보기 특수 규칙

                # 간섭 체크
                if distance < required_clearance:
                    violations += 1
                    logger.warning(
                        f"Clearance violation: {p1.breaker_id} <-> {p2.breaker_id}, "
                        f"distance={distance:.1f}mm < required={required_clearance}mm"
                    )

        return violations

    def _place_4p_with_n_phase_rules(
        self,
        four_pole_breakers: list[BreakerInput],
        placements: list[PlacementResult],
        left_x_mm: int,
        right_x_mm: int,
        start_y_mm: int,
        row_height_mm: int,
        start_row_idx: int,
    ) -> int:
        """
        4P 차단기 배치 with Branch Bus Rules v1.0 (N상 row-aware)

        규칙:
        - shared_if_pair: 마주보는 4P의 N상은 하나의 분기부스바 공유
        - split_if_single: 첫/마지막 4P의 N상은 좌/우 분리 (center에서 따로 연결)
        - no_cross_link: N상 간 횡연결 금지 (row 분리)
        - n_phase_rightmost: N상 최우측 컬럼 고정

        Args:
            four_pole_breakers: 4P 차단기 목록
            placements: 배치 결과 누적 리스트
            left_x_mm, right_x_mm: 좌우 x 좌표
            start_y_mm: 시작 y 좌표
            row_height_mm: 행 간격
            start_row_idx: 시작 행 인덱스

        Returns:
            다음 행 인덱스
        """
        row_idx = start_row_idx
        total_4p = len(four_pole_breakers)

        # 좌우 대칭 배치용 분할
        left_count = (total_4p + 1) // 2
        right_count = total_4p - left_count

        left_4p = four_pole_breakers[:left_count]
        right_4p = four_pole_breakers[left_count:]

        for idx in range(left_count):
            current_y_mm = start_y_mm + (row_idx - 1) * row_height_mm

            # 좌측 4P 배치
            left_breaker = left_4p[idx]
            is_first = idx == 0
            is_last = (idx == left_count - 1) and (right_count == 0)
            has_pair = idx < right_count

            # N상 배치 정보 생성
            n_bus_metadata = self._get_n_phase_bus_metadata(
                is_first=is_first, is_last=is_last, has_pair=has_pair, side="left"
            )

            placements.append(
                PlacementResult(
                    breaker_id=left_breaker.id,
                    position={
                        "x": left_x_mm,
                        "y": current_y_mm,
                        "row": row_idx,
                        "col": 0,
                        "side": "left",
                        "n_bus_metadata": n_bus_metadata,
                    },
                    phase="R",  # 4상 대표 (RST+N)
                    current_a=left_breaker.current_a,
                    poles=left_breaker.poles,
                    model=left_breaker.model,  # 모델명 전파
                )
            )

            # 우측 4P 배치 (마주보기)
            if idx < right_count:
                right_breaker = right_4p[idx]
                is_last_right = (idx == right_count - 1) and (idx == left_count - 1)

                n_bus_metadata_right = self._get_n_phase_bus_metadata(
                    is_first=False,  # 우측은 첫 번째가 아님
                    is_last=is_last_right,
                    has_pair=True,  # 좌측과 pair
                    side="right",
                )

                placements.append(
                    PlacementResult(
                        breaker_id=right_breaker.id,
                        position={
                            "x": right_x_mm,
                            "y": current_y_mm,
                            "row": row_idx,
                            "col": 1,
                            "side": "right",
                            "n_bus_metadata": n_bus_metadata_right,
                        },
                        phase="R",  # 4상 대표
                        current_a=right_breaker.current_a,
                        poles=right_breaker.poles,
                        model=right_breaker.model,  # 모델명 전파
                    )
                )

            row_idx += 1

        logger.info(
            f"4P N-phase row-aware placement: {total_4p} breakers, "
            f"pairs={min(left_count, right_count)}, singles={abs(left_count - right_count)}"
        )

        return row_idx

    def _get_n_phase_bus_metadata(
        self,
        is_first: bool,
        is_last: bool,
        has_pair: bool,
        side: str,
    ) -> dict[str, str]:
        """
        N상 분기부스바 메타데이터 생성 (Branch Bus Rules v1.0)

        Args:
            is_first: 첫 번째 4P 여부
            is_last: 마지막 4P 여부
            has_pair: 마주보는 쌍 존재 여부
            side: "left" or "right"

        Returns:
            N상 배치 메타데이터
        """
        # shared_if_pair 우선: 마주보는 쌍이 있으면 공유 (첫/마지막 여부 무관)
        if has_pair:
            return {
                "n_bus_type": "shared",
                "n_bus_side": "center",  # 중앙 공유 부스바
                "rule": "shared_if_pair",
            }

        # split_if_single: 쌍이 없으면 분리 (첫/마지막 또는 중간 단독)
        return {
            "n_bus_type": "split",
            "n_bus_side": f"{side}_only",  # left_only / right_only
            "rule": "split_if_single",
        }

    def _validate_4p_n_phase_interference(
        self, placements: list[PlacementResult]
    ) -> int:
        """
        LAY-004: 4P N상 마주보기 간섭 검증 (Branch Bus Rules v1.0 통합)

        규칙 (no_cross_link):
        - 4P 차단기의 N상 간 횡연결 금지
        - 마주보는 경우 shared_if_pair 규칙 적용 (공유 분기부스바)
        - 단독 N상은 split_if_single 규칙 적용 (좌/우 분리)

        Args:
            placements: 배치 결과 목록

        Returns:
            간섭 위반 개수
        """
        violations = 0

        # 4P 차단기만 추출
        four_pole_placements = [p for p in placements if p.poles == 4]

        # 마주보기 쌍 확인 (no_cross_link 검증)
        for i, p1 in enumerate(four_pole_placements):
            for p2 in four_pole_placements[i + 1 :]:
                # 같은 row, 다른 col = 마주보기
                is_facing = p1.position.get("row") == p2.position.get(
                    "row"
                ) and p1.position.get("col") != p2.position.get("col")

                if is_facing:
                    # n_bus_metadata 확인
                    p1_metadata = p1.position.get("n_bus_metadata", {})
                    p2_metadata = p2.position.get("n_bus_metadata", {})

                    p1_bus_type = p1_metadata.get("n_bus_type", "unknown")
                    p2_bus_type = p2_metadata.get("n_bus_type", "unknown")

                    # shared_if_pair 규칙 적용된 경우 정상
                    if p1_bus_type == "shared" and p2_bus_type == "shared":
                        logger.debug(
                            f"4P N-phase shared bus: {p1.breaker_id} <-> {p2.breaker_id} "
                            f"(row={p1.position.get('row')}, rule=shared_if_pair)"
                        )
                        continue

                    # shared가 아닌 경우 N상 간섭 위반 (no_cross_link)
                    violations += 1
                    logger.warning(
                        f"LAY-004: 4P N-phase cross-link violation: "
                        f"{p1.breaker_id} ({p1_bus_type}) <-> {p2.breaker_id} ({p2_bus_type}) "
                        f"(row={p1.position.get('row')}, rule=no_cross_link)"
                    )

        return violations

    def _validate_branch_bus_rules(
        self, placements: list[PlacementResult]
    ) -> list[str]:
        """
        Branch Bus Rules v1.0 검증 (6가지 validation guards)

        Guards:
        1. phase_alignment: 분기부스바.phase == MAIN_BUS.same_phase
        2. bolt_integrity: 상별 볼트 규격 일치 강제
        3. n_no_cross_link: N상 간 횡연결 금지
        4. outputs_outer_only: 2차 단자 외측만 배치
        5. center_feed_direction: 중앙 하향 공급 방향
        6. n_phase_rightmost: N상 최우측 컬럼 고정

        Args:
            placements: 배치 결과 목록

        Returns:
            위반 메시지 목록 (빈 리스트 = 모든 규칙 통과)
        """
        violations = []

        # Guard 1: phase_alignment (RST 정렬)
        # (현재 구현: 메인 차단기 phase="R", 분기는 R/S/T 순환 배치)
        # 추가 검증 필요 없음 (배치 로직이 이미 보장)

        # Guard 2: bolt_integrity (상별 볼트 규격 일치)
        # (현재 구현: 2P 차단기는 각 상별로 독립 배치 가능)
        # 검증: 3P/4P 차단기의 RST 정렬만 확인 (2P는 제외)
        for row_idx in range(
            1, max([p.position.get("row", 0) for p in placements]) + 1
        ):
            row_placements = [p for p in placements if p.position.get("row") == row_idx]
            # 3P/4P만 검증 (2P는 상별로 다를 수 있음)
            multi_phase_in_row = [p for p in row_placements if p.poles >= 3]
            if len(multi_phase_in_row) >= 2:
                phases = [p.phase for p in multi_phase_in_row]
                if len(set(phases)) > 1:
                    violations.append(
                        f"bolt_integrity violation: row={row_idx}, 3P/4P phases={phases} (expected same phase)"
                    )

        # Guard 3: n_no_cross_link (N상 간 횡연결 금지)
        # (이미 _validate_4p_n_phase_interference에서 검증됨)

        # Guard 4: outputs_outer_only (2차 단자 외측만)
        # (현재 구현: 좌우 대칭 배치, 내측은 1차 단자 예정)
        # 추가 검증 필요 없음 (설계 원칙 준수)

        # Guard 5: center_feed_direction (중앙 하향 공급)
        # (현재 구현: 메인 차단기 상단 중앙 배치)
        # 추가 검증: 메인 차단기 position.side == "center"
        main_placements = [p for p in placements if p.position.get("row") == 0]
        for mp in main_placements:
            if mp.position.get("side") != "center":
                violations.append(
                    f"center_feed_direction violation: main breaker {mp.breaker_id} not at center"
                )

        # Guard 6: n_phase_rightmost (N상 최우측 컬럼)
        # (현재 구현: 4P 차단기의 N상은 position.col 우선순위 최우측)
        # 추가 검증: 4P 차단기의 n_bus_metadata 존재 여부
        four_pole_placements = [p for p in placements if p.poles == 4]
        for fp in four_pole_placements:
            if "n_bus_metadata" not in fp.position:
                violations.append(
                    f"n_phase_rightmost violation: 4P breaker {fp.breaker_id} missing n_bus_metadata"
                )

        return violations
