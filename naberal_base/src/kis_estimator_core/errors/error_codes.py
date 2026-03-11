"""
KIS Estimator 에러 코드 체계
각 에러는 다음 단계 진행 차단
"""

from dataclasses import dataclass

# Import Enums from SSOT (LAW-02: Single Source of Truth)
from kis_estimator_core.core.ssot.enums import ErrorCategory, ErrorSeverity


@dataclass
class ErrorCode:
    """에러 코드 정의"""

    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    hint: str
    blocking: bool = True


# ═══════════════════════════════════════════════════════════
# INPUT ERRORS (INP-001 ~ INP-099)
# ═══════════════════════════════════════════════════════════

INP_001 = ErrorCode(
    code="INP-001",
    category=ErrorCategory.INPUT,
    severity=ErrorSeverity.BLOCKING,
    message="외함 종류 정보 누락",
    hint="외함 재질을 지정하세요: SUS201 1.2T 또는 STEEL 1.6T",
    blocking=True,
)

INP_002 = ErrorCode(
    code="INP-002",
    category=ErrorCategory.INPUT,
    severity=ErrorSeverity.BLOCKING,
    message="외함 설치 위치 정보 누락",
    hint="설치 위치를 지정하세요: 옥내노출, 옥외노출, 매입함, 옥내자립, 옥외자립",
    blocking=True,
)

INP_003 = ErrorCode(
    code="INP-003",
    category=ErrorCategory.INPUT,
    severity=ErrorSeverity.BLOCKING,
    message="차단기 브랜드 정보 누락",
    hint="차단기 브랜드를 지정하세요: 상도차단기, LS산전, 현대일렉트릭",
    blocking=True,
)

INP_004 = ErrorCode(
    code="INP-004",
    category=ErrorCategory.INPUT,
    severity=ErrorSeverity.BLOCKING,
    message="메인 차단기 정보 누락",
    hint="메인 차단기 사양을 지정하세요: 극수(2P/3P/4P), 전류(A), 프레임(AF)",
    blocking=True,
)

INP_005 = ErrorCode(
    code="INP-005",
    category=ErrorCategory.INPUT,
    severity=ErrorSeverity.BLOCKING,
    message="분기 차단기 정보 누락",
    hint="최소 1개 이상의 분기 차단기가 필요합니다",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# 7대 치명적 버그 (BUG-001 ~ BUG-007)
# ═══════════════════════════════════════════════════════════

BUG_001 = ErrorCode(
    code="BUG-001",
    category=ErrorCategory.BREAKER,
    severity=ErrorSeverity.BLOCKING,
    message="MCCB/ELB 구분 실패",
    hint="배선용차단기(MCCB)와 누전차단기(ELB)를 명확히 구분하세요. 요구사항에 '누전' 키워드가 있으면 ELB, 없으면 MCCB입니다.",
    blocking=True,
)

BUG_002 = ErrorCode(
    code="BUG-002",
    category=ErrorCategory.CATALOG,
    severity=ErrorSeverity.BLOCKING,
    message="카탈로그에 존재하지 않는 차단기 사양",
    hint="카탈로그(중요ai단가표의_2.0V.csv)에서 해당 사양을 찾을 수 없습니다. 극수, 전류, 차단용량을 확인하세요.",
    blocking=True,
)

BUG_003 = ErrorCode(
    code="BUG-003",
    category=ErrorCategory.BREAKER,
    severity=ErrorSeverity.BLOCKING,
    message="소형 차단기 자동 선택 실패",
    hint="2P 20A/30A는 소형 차단기(SIE-32, SIB-32, SBW-32, 32GRHS, BS-32)를 사용해야 합니다.",
    blocking=True,
)

BUG_004 = ErrorCode(
    code="BUG-004",
    category=ErrorCategory.BREAKER,
    severity=ErrorSeverity.BLOCKING,
    message="컴팩트 타입 선택 실패",
    hint="2P 40~50A는 컴팩트 타입(SEC-52, SBC-52, 52GRHS, BS-52)을 우선 사용해야 합니다.",
    blocking=True,
)

BUG_005 = ErrorCode(
    code="BUG-005",
    category=ErrorCategory.BREAKER,
    severity=ErrorSeverity.BLOCKING,
    message="동일 품목 통합 실패",
    hint="동일한 차단기는 수량으로 통합해야 합니다. 예: ELB 2P 20A 10개 → 1줄로 표기",
    blocking=True,
)

BUG_006 = ErrorCode(
    code="BUG-006",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="분기 BUS-BAR 누락",
    hint="MAIN BUS-BAR 외에 분기용 BUS-BAR(3T×15)도 추가해야 합니다.",
    blocking=True,
)

BUG_007 = ErrorCode(
    code="BUG-007",
    category=ErrorCategory.LAYOUT,
    severity=ErrorSeverity.BLOCKING,
    message="마주보기 배치 계산 오류",
    hint="분기 차단기 마주보기 배치 시 H = Σ(branch_W) + main_H + clearances + gaps 공식을 사용하세요. 4P는 N상 간섭으로 +25mm 추가됩니다.",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# BUSBAR ERRORS (BUS-001 ~ BUS-099)
# ═══════════════════════════════════════════════════════════

BUS_001 = ErrorCode(
    code="BUS-001",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="MAIN BUS-BAR 규격 오류 (50~125AF)",
    hint="메인 차단기가 50~125AF일 때 MAIN BUS-BAR는 3T×15 규격이어야 합니다.",
    blocking=True,
)

BUS_002 = ErrorCode(
    code="BUS-002",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="MAIN BUS-BAR 규격 오류 (200~250AF)",
    hint="메인 차단기가 200~250AF일 때 MAIN BUS-BAR는 5T×20 규격이어야 합니다.",
    blocking=True,
)

BUS_003 = ErrorCode(
    code="BUS-003",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="MAIN BUS-BAR 규격 오류 (400AF)",
    hint="메인 차단기가 400AF일 때 MAIN BUS-BAR는 6T×30 규격이어야 합니다.",
    blocking=True,
)

BUS_004 = ErrorCode(
    code="BUS-004",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="MAIN BUS-BAR 규격 오류 (600~800AF)",
    hint="메인 차단기가 600~800AF일 때 MAIN BUS-BAR는 8T×40 규격이어야 합니다.",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# CATALOG ERRORS (CAT-001 ~ CAT-099)
# ═══════════════════════════════════════════════════════════

CAT_001 = ErrorCode(
    code="CAT-001",
    category=ErrorCategory.CATALOG,
    severity=ErrorSeverity.BLOCKING,
    message="외함 규격 카탈로그 미존재",
    hint="계산된 외함 크기가 카탈로그에 없습니다. 가장 가까운 큰 사이즈를 선택하거나 주문제작이 필요합니다.",
    blocking=True,
)

CAT_002 = ErrorCode(
    code="CAT-002",
    category=ErrorCategory.CATALOG,
    severity=ErrorSeverity.BLOCKING,
    message="차단기 모델명 카탈로그 미존재",
    hint="요청한 차단기 모델이 카탈로그에 없습니다. 브랜드, 극수, 전류, 차단용량을 확인하세요.",
    blocking=True,
)

CAT_003 = ErrorCode(
    code="CAT-003",
    category=ErrorCategory.CATALOG,
    severity=ErrorSeverity.BLOCKING,
    message="경제형 차단기 없음 - 표준형 대체 필요",
    hint="경제형이 없으므로 표준형으로 대체합니다. 가격이 약 20~30% 상승합니다.",
    blocking=False,  # Warning으로 처리, 자동 대체
)


# ═══════════════════════════════════════════════════════════
# ENCLOSURE ERRORS (ENC-001 ~ ENC-099)
# ═══════════════════════════════════════════════════════════

ENC_001 = ErrorCode(
    code="ENC-001",
    category=ErrorCategory.ENCLOSURE,
    severity=ErrorSeverity.BLOCKING,
    message="외함 높이 계산 공식 오류",
    hint="H = A(상단여유) + B(메인-분기간격) + C(분기총높이) + D(하단여유) + E(부속여유) 공식을 사용하세요.",
    blocking=True,
)

ENC_002 = ErrorCode(
    code="ENC-002",
    category=ErrorCategory.ENCLOSURE,
    severity=ErrorSeverity.BLOCKING,
    message="외함 폭 계산 오류",
    hint="메인 차단기 프레임별 기본 폭 규칙을 확인하세요. 50~100AF: 600mm, 125~250AF: 700mm, 400AF: 800mm, 600~800AF: 900mm",
    blocking=True,
)

ENC_003 = ErrorCode(
    code="ENC-003",
    category=ErrorCategory.ENCLOSURE,
    severity=ErrorSeverity.BLOCKING,
    message="마주보기 배치 시 높이 계산 오류",
    hint="마주보기 배치 시 H = Σ(branch_W) + main_H + top_clearance + gap + bottom_clearance 공식을 사용하세요.",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# ACCESSORY ERRORS (ACC-001 ~ ACC-099)
# ═══════════════════════════════════════════════════════════

ACC_001 = ErrorCode(
    code="ACC-001",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="E.T 수량 계산 오류",
    hint="E.T는 전원 극수에 따라 계산됩니다. 3상: 3개, 단상: 2개",
    blocking=True,
)

ACC_002 = ErrorCode(
    code="ACC-002",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="P-COVER 가격 계산 오류",
    hint="P-COVER 가격 = (W × H) / 25000 공식을 사용하세요.",
    blocking=True,
)

ACC_003 = ErrorCode(
    code="ACC-003",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="ASSEMBLY CHARGE 범위 오류",
    hint="50~100AF 기준 70,000~80,000원 범위를 준수하세요.",
    blocking=True,
)

ACC_004 = ErrorCode(
    code="ACC-004",
    category=ErrorCategory.ACCESSORY,
    severity=ErrorSeverity.BLOCKING,
    message="마그네트 동반자재 누락",
    hint="마그네트 1개당 FUSEHOLDER(1), TERMINAL_BLOCK(3), PVC DUCT(2), CABLE_WIRE(2), 인건비(20,000원) 필수 포함",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# LAYOUT ERRORS (LAY-001 ~ LAY-099)
# ═══════════════════════════════════════════════════════════

LAY_001 = ErrorCode(
    code="LAY-001",
    category=ErrorCategory.LAYOUT,
    severity=ErrorSeverity.BLOCKING,
    message="상평형 불균형 초과",
    hint="상평형은 4% 이내로 유지해야 합니다. 현재 불균형이 허용 범위를 초과했습니다.",
    blocking=True,
)

LAY_002 = ErrorCode(
    code="LAY-002",
    category=ErrorCategory.LAYOUT,
    severity=ErrorSeverity.BLOCKING,
    message="차단기 간섭 위반",
    hint="차단기 간 최소 간격을 유지해야 합니다. 간섭이 감지되었습니다.",
    blocking=True,
)

LAY_004 = ErrorCode(
    code="LAY-004",
    category=ErrorCategory.LAYOUT,
    severity=ErrorSeverity.BLOCKING,
    message="4P N상 마주보기 간섭",
    hint="4P 차단기의 N상은 마주볼 수 없습니다. 각 4P 차단기에 +25mm(상 1개 크기) 추가하세요.",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# CALCULATION ERRORS (CAL-001 ~ CAL-099)
# ═══════════════════════════════════════════════════════════

CAL_001 = ErrorCode(
    code="CAL-001",
    category=ErrorCategory.CALCULATION,
    severity=ErrorSeverity.BLOCKING,
    message="수식 보존 실패",
    hint="Excel 수식이 100% 보존되어야 합니다. 수식이 손상되었습니다.",
    blocking=True,
)

CAL_002 = ErrorCode(
    code="CAL-002",
    category=ErrorCategory.CALCULATION,
    severity=ErrorSeverity.BLOCKING,
    message="합계 계산 불일치",
    hint="견적서 합계와 표지 합계가 일치하지 않습니다.",
    blocking=True,
)


# ═══════════════════════════════════════════════════════════
# 에러 코드 매핑
# ═══════════════════════════════════════════════════════════

ERROR_CODE_MAP = {
    # Input Errors
    "INP-001": INP_001,
    "INP-002": INP_002,
    "INP-003": INP_003,
    "INP-004": INP_004,
    "INP-005": INP_005,
    # 7대 치명적 버그
    "BUG-001": BUG_001,
    "BUG-002": BUG_002,
    "BUG-003": BUG_003,
    "BUG-004": BUG_004,
    "BUG-005": BUG_005,
    "BUG-006": BUG_006,
    "BUG-007": BUG_007,
    # BUS-BAR Errors
    "BUS-001": BUS_001,
    "BUS-002": BUS_002,
    "BUS-003": BUS_003,
    "BUS-004": BUS_004,
    # Catalog Errors
    "CAT-001": CAT_001,
    "CAT-002": CAT_002,
    "CAT-003": CAT_003,
    # Enclosure Errors
    "ENC-001": ENC_001,
    "ENC-002": ENC_002,
    "ENC-003": ENC_003,
    # Accessory Errors
    "ACC-001": ACC_001,
    "ACC-002": ACC_002,
    "ACC-003": ACC_003,
    "ACC-004": ACC_004,
    # Layout Errors
    "LAY-001": LAY_001,
    "LAY-002": LAY_002,
    "LAY-004": LAY_004,
    # Calculation Errors
    "CAL-001": CAL_001,
    "CAL-002": CAL_002,
}


def get_error(code: str) -> ErrorCode | None:
    """에러 코드로 ErrorCode 객체 반환"""
    return ERROR_CODE_MAP.get(code)


def is_blocking_error(code: str) -> bool:
    """에러가 다음 단계를 차단하는지 확인"""
    error = get_error(code)
    return error.blocking if error else False
