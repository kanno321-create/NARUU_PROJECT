"""
SSOT Constants - 모든 매직 넘버/문자열 중앙 정의

절대 원칙:
- 코드에서 직접 숫자/문자열 사용 금지
- 모든 상수는 여기서만 정의
- 변경 시 이 파일만 수정

LAW-02: SSOT 위반 금지 - 단일 출처만 참조
LAW-03: 하드코딩 금지 - generated.py에서 import
"""

from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

# ============================================================
# Import from Generated SSOT (Phase B)
# ============================================================
# 주요 지식 데이터는 generated.py에서 import
# generated.py는 scripts/generate_ssot_wrappers.py로 자동 생성됨
try:
    from .generated import (
        ACCESSORIES,
        BREAKERS,
        ENCLOSURES,
        ESTIMATES,
        FORMULAS,
        SSOT_STRUCT_HASHES,
        STANDARDS,
    )
except ImportError:
    # generated.py가 없으면 경고 (빌드 시 자동 생성됨)
    ACCESSORIES = {}
    BREAKERS = {}
    ENCLOSURES = {}
    ESTIMATES = {}
    FORMULAS = {}
    STANDARDS = {}
    SSOT_STRUCT_HASHES = {}
    import warnings

    warnings.warn(
        "generated.py not found. Run: python scripts/generate_ssot_wrappers.py",
        ImportWarning, stacklevel=2,
    )

# ============================================================
# Phase Names (FIX-4 Pipeline)
# ============================================================
PHASE_0_NAME = "Phase 0"  # Input Validation
PHASE_1_NAME = "Phase 1"  # Enclosure Solver
PHASE_2_NAME = "Phase 2"  # Breaker Placement
PHASE_3_NAME = "Phase 3"  # Excel Generation

# ============================================================
# Quality Gate Thresholds
# ============================================================
# Enclosure (Phase 1)
FIT_SCORE_THRESHOLD = 0.90  # 외함 적합도 ≥ 0.90
IP_RATING_THRESHOLD = 44  # IP 등급 ≥ 44
DOOR_CLEARANCE_THRESHOLD = 30  # 도어 여유 ≥ 30mm

# Breaker Placement (Phase 2)
PHASE_BALANCE_THRESHOLD = 4.0  # 상평형 ≤ 4%
CLEARANCE_VIOLATIONS_THRESHOLD = 0  # 간섭 위반 = 0

# Excel Format (Phase 3)
FORMULA_PRESERVATION_THRESHOLD = 100.0  # 수식 보존 = 100%
NAMED_RANGE_DAMAGE_THRESHOLD = 0  # 네임드 범위 손상 = 0

# Doc Lint (Phase 4)
LINT_ERRORS_THRESHOLD = 0  # 린트 오류 = 0
POLICY_VIOLATIONS_THRESHOLD = 0  # 정책 위반 = 0

# ============================================================
# Enclosure Dimension Constants (mm)
# ============================================================
MAIN_TO_BRANCH_GAP_MM = 15  # 메인-분기 간격 (고정값)
DEPTH_WITHOUT_PBL_MM = 150  # PBL 없을 때 깊이
DEPTH_WITH_PBL_MM = 200  # PBL 있을 때 깊이
FACE_TO_FACE_SMALL_2P_MM = 40  # 2P 소형 마주보기 간격
ACCESSORY_MARGIN_PER_ROW_MM = 250.0  # 부속자재 1줄당 여유

# ============================================================
# Standard Enclosure Sizes (기성함 규격) - 가격경쟁력 핵심!
# ============================================================
# 대표님 지식: 기성함 우선 사용, 업사이징만 허용, 다운사이징 절대 금지
# HDS 옥내노출 카탈로그 기준 - 실제 존재하는 W×H 조합만 허용
# W=600 기준 최소 H=600부터 시작 (500은 없음)
# W=700 기준 1100은 없음 (1000 다음 1200)
STANDARD_ENCLOSURE_WIDTHS_MM = [500, 600, 700, 800, 900, 1000]
STANDARD_ENCLOSURE_HEIGHTS_MM = [600, 700, 800, 900, 1000, 1200, 1300, 1400, 1500, 1600, 1800, 2000]
STANDARD_ENCLOSURE_DEPTHS_MM = [150, 200, 250, 300]
# 단위: W=100mm, H=100mm, D=50mm
ENCLOSURE_WIDTH_STEP_MM = 100
ENCLOSURE_HEIGHT_STEP_MM = 100
ENCLOSURE_DEPTH_STEP_MM = 50

# ============================================================
# Custom Enclosure Pricing (주문제작함 STEEL 1.6T 단가표)
# ============================================================
# 평수 = (W × H) / 90000 → 소수점 1자리 반올림
# 최종 소비자가격 = 원가(평수 × 평당단가) × 1.3
# D값 구간별 평당 단가 (원)
CUSTOM_ENCLOSURE_PRICE_PER_PYEONG: dict[str, dict[str, int]] = {
    # 1. 옥내노출 STEEL (HDS 타입 형상)
    "옥내노출": {
        "D80-200": 25000, "D200-250": 26000, "D250-300": 27000,
        "D300-350": 28000, "D350-400": 29000, "D400-450": 30000,
        "D450-500": 31000,
    },
    # 2. 옥내노출 양문형 STEEL (좌우 또는 상하 양문)
    "옥내노출_양문형": {
        "D80-200": 25500, "D200-250": 26500, "D250-300": 27500,
        "D300-350": 28500, "D350-400": 29500, "D400-450": 30500,
        "D450-500": 31500,
    },
    # 3. 매입함 (HS 타입 형상)
    "매입": {
        "D80-200": 14000, "D200-250": 15000,
    },
    # 4. 옥외방수 STEEL
    "옥외방수": {
        "D80-200": 27000, "D200-250": 28000, "D250-300": 29000,
        "D300-350": 30000, "D350-400": 31000, "D400-450": 32000,
        "D450-500": 33000,
    },
}
# 5. STEEL P-COVER: 평당 5,000원 (사이즈: W-100 × H-100)
# 실측 보정: 5,500→5,000 (CLAUDE_KNOWLEDGE 14.5, ×12,500→×10,000 역산)
CUSTOM_PCOVER_STEEL_PRICE_PER_PYEONG = 5000
# 6. 속판: 아연도금 4,600원/평, 분체도장 5,700원/평 (사이즈: W-100 × H-100)
CUSTOM_INNER_PLATE_PRICE_PER_PYEONG = {"아연도금": 4600, "분체도장": 5700}
# 원가 → 소비자가 마크업 배율
CUSTOM_ENCLOSURE_MARKUP = 1.3

# ============================================================
# 고AF 단품 분전반 (400~800AF 차단기 1개, 분기 없음, 동관단자 직결)
# ============================================================
# 대표님 지식 (2026-03-09): 400AF 이상 차단기 1개만 설치되는 특수 패널
# 자재: 외함 + 차단기 + 동관단자 + N.P(3T×40×200) + 잡자재비 + ASSEMBLY
# E.T, P-COVER, COATING, INSULATOR, BUS-BAR 등 불포함

# 동관단자 (Copper Tube Terminal)
TERMINAL_LUG_LENGTH_MM = 140  # 동관단자 길이 (상단/하단 각 140mm 추가)
TERMINAL_LUG_WEIGHT_KG = 0.45  # 동관단자 1개당 무게 (kg)
# 가격: PRICE_BUSBAR_PER_KG 기준 중량 산출 (수량=총KG, 단위=KG)

# W (폭) 디폴트 — 고AF 단품
SINGLE_BREAKER_W_400AF = 700  # mm
SINGLE_BREAKER_W_600AF = 800  # mm
SINGLE_BREAKER_W_800AF = 800  # mm

# H (높이) 공식: 차단기H + 동관단자(140+140) + 전선여유(상+하)
# 400AF 차단기H=257, 600/800AF 차단기H=280
SINGLE_BREAKER_CABLE_CLEARANCE: dict[str, tuple[int, int]] = {
    "400AF": (200, 200),   # 상단 200mm + 하단 200mm
    "600AF": (450, 250),   # 상단 450mm + 하단 250mm
    "800AF": (600, 280),   # 상단 600mm + 하단 280mm
}

# D (깊이) 디폴트 — 고AF 단품
SINGLE_BREAKER_D_400AF = 250  # mm
SINGLE_BREAKER_D_600_800AF = 300  # mm

# 잡자재비 — 고AF 단품 (400~800AF 동일)
SINGLE_BREAKER_MISC_PRICE = 28300  # 원

# ASSEMBLY CHARGE — 고AF 단품
SINGLE_BREAKER_ASSEMBLY_400AF = 70000  # 원
SINGLE_BREAKER_ASSEMBLY_600_800AF = 100000  # 원

# ============================================================
# Breaker Dimensions (mm)
# ============================================================
SMALL_BREAKER_FACE_TO_FACE_MM = 40  # 소형 차단기 마주보기
SMALL_BREAKER_AF = 32  # 소형 차단기 프레임
SMALL_BREAKER_ONLY_WIDTH_MM = 500  # 분기 전부 소형(2P 20~30A)일 때 폭 (대표님 피드백)
SMALL_BREAKER_CURRENT_RANGE = (20, 30)  # 소형 차단기 전류 범위 (A)

# ============================================================
# Excel Symbols & Text
# ============================================================
EXCEL_MULTIPLY_SYMBOL = "×"  # 곱셈 기호 (엑셀 셀 표기)
EXCEL_TOTAL_TEXT = "합  계"  # 합계 표기
EXCEL_SUBTOTAL_TEXT = "소  계"  # 소계 표기
EXCEL_ASSEMBLY_CHARGE_TEXT = "조립비"  # 조립비 표기

# 합계/소계 변종 정규식 (대소문자 불문)
TOTAL_SUBTOTAL_PATTERN = r"(?i)^(total|sub[-\s]?total|합계|소계|합\s*계|소\s*계)$"

# ============================================================
# Field Name Aliases (키 정규화)
# ============================================================
# Breaker 관련
BREAKER_CURRENT_ALIASES = ["current_a", "current", "ampere", "at"]
BREAKER_FRAME_ALIASES = ["frame_af", "frame", "af"]
BREAKER_POLES_ALIASES = ["poles", "pole", "p"]

# Enclosure 관련
ENCLOSURE_WIDTH_ALIASES = ["width_mm", "width", "w"]
ENCLOSURE_HEIGHT_ALIASES = ["height_mm", "height", "h"]
ENCLOSURE_DEPTH_ALIASES = ["depth_mm", "depth", "d"]

# ============================================================
# Error Messages (표준 메시지 템플릿)
# ============================================================
ERROR_MSG_MISSING_FIELD = "{field} 필드가 누락되었습니다"
ERROR_MSG_INVALID_VALUE = "{field} 값이 유효하지 않습니다: {value}"
ERROR_MSG_OUT_OF_RANGE = (
    "{field} 값이 범위를 벗어났습니다: {value} (기대값: {expected})"
)
ERROR_MSG_CATALOG_NOT_FOUND = "{item_type} 카탈로그를 찾을 수 없습니다: {params}"

# ============================================================
# Tax & Currency
# ============================================================
VAT_RATE = 0.10  # 부가세율 10%
KRW_CURRENCY_SYMBOL = "원"  # 통화 기호

# ============================================================
# Accessory Prices (부속자재 단가) - Phase VII-3
# ============================================================
# E.T (Earth Terminal) Prices by AF
PRICE_ET_50_125AF = 4500
PRICE_ET_200_250AF = 5500
PRICE_ET_400AF = 12000
PRICE_ET_600_800AF = 18000

# N.T (Neutral Terminal)
PRICE_NT = 3000

# N.P (Name Plate)
PRICE_NP_CARD_HOLDER = 800  # 일반 견적 (분기 있음)
PRICE_NP_CARD_HOLDER_MAIN_ONLY = 1500  # 메인차단기만
PRICE_NP_3T_40_200 = 4000

# Other Accessories
PRICE_COATING = 5000
PRICE_BREAKER_SUPPORT = 1200  # 차단기지지대
PRICE_ELB_SUPPORT = 500  # ELB지지대

# INSULATOR Prices by AF
PRICE_INSULATOR_50_250AF = 1100
PRICE_INSULATOR_400_800AF = 4400

# Busbar
# NOTE: 부스바는 원자재라 가격변동이 심함 - 대표님이 알려줄 때마다 조정
# 2026-03-09 기준: 31,500원/kg (이전: 31,000원/kg) - 원자재 상승
PRICE_BUSBAR_PER_KG = 31500  # 31,500원/kg

# ============================================================
# Calculation Coefficients (계산 계수) - Phase VII-3
# ============================================================
# MAIN BUS-BAR Weight Coefficients (메인 부스바 중량 계수)
# 공식: (W × H) × coefficient
BUSBAR_COEFF_20_250A = 0.000007
BUSBAR_COEFF_300_400A = 0.000013
BUSBAR_COEFF_500_800A = 0.000015

# BUS-BAR (분기용) Weight Coefficients (분기 부스바 중량 계수)
# 공식: (W × H) × coefficient
# 출처: 부스바 산출공식.txt (대표님 정의)
BRANCH_BUSBAR_COEFF_20_250A = 0.0000045
BRANCH_BUSBAR_COEFF_300_400A = 0.000007
BRANCH_BUSBAR_COEFF_500_800A = 0.000009

# Busbar Thickness & Width Specs
BUSBAR_SPEC_3T_15 = "3T*15"  # ~125AF
BUSBAR_SPEC_5T_20 = "5T*20"  # ~250AF
BUSBAR_SPEC_6T_30 = "6T*30"  # ~400AF
BUSBAR_SPEC_8T_40 = "8T*40"  # ~800AF

# Busbar Weight for Main-Only with Busbar Option
BUSBAR_WEIGHT_400AF_OPTION = 5.0  # kg
BUSBAR_WEIGHT_600_800AF_OPTION = 8.0  # kg

# P-COVER Calculation
PCOVER_AREA_DIVISOR = 90000  # (W*H) / 90000
PCOVER_PRICE_MULTIPLIER = 3200  # * 3200
PCOVER_MIN_PRICE = 12000  # 최소 가격 12,000원 (대표님 피드백 2024-12-10)

# Custom Enclosure (주문제작함)
ENCLOSURE_CUSTOM_VOLUME_DIVISOR = 1000  # mm³ to cm³
ENCLOSURE_CUSTOM_VOLUME_MULTIPLIER = 10  # / 10
ENCLOSURE_CUSTOM_PRICE_PER_UNIT = 150  # * 150원

# ============================================================
# Miscellaneous Materials (잡자재비 계산) - Phase VII-3
# ============================================================
MISC_BASE_PRICE = 7000  # 기본값
MISC_H_INCREMENT_PER_100MM = 1500  # 100mm당 추가 (실측 보정: 1000→1500, CLAUDE_KNOWLEDGE 14.3)
MISC_ACCESSORY_INCREMENT = 10000  # 부속자재 1개당 추가
MISC_MAX_PRICE = 55000  # 최대 금액 (실측 보정: 40000→55000, 대형반+STEEL P-COVER 반영)
MISC_BUSBAR_OPTION_400_800AF = 15000  # 부스바 처리 옵션 추가 (메인차단기만)

# ============================================================
# Assembly Charge (조립비 계산) - Phase VII-3
# ============================================================
# Assembly Charge (Main Only) - 메인차단기만 있는 경우
ASSEMBLY_MAIN_ONLY_50_250AF = 15000
ASSEMBLY_MAIN_ONLY_400AF = 20000
ASSEMBLY_MAIN_ONLY_600_800AF = 30000

# Assembly Charge (Main Only with Busbar Option) - 부스바 처리 옵션 추가
ASSEMBLY_MAIN_ONLY_BUSBAR_400AF = 40000  # 부스바 옵션 추가 인건비
ASSEMBLY_MAIN_ONLY_BUSBAR_600_800AF = 70000  # 부스바 옵션 추가 인건비

# ============================================================
# Assembly Charge (CEO 규칙 2024-12-05 수정)
# ============================================================
# 공식: 기본가격 + ((외함H - 기준H) / 100) × H당추가금액
# SIE-32/32GRHS 대부분인 경우 추가 인건비 적용

# 50~100AF (기준: W600×H700)
ASSEMBLY_BASE_H_50_100AF = 700  # mm
ASSEMBLY_BASE_PRICE_50_100AF = 50000
ASSEMBLY_H_INCREMENT_50_100AF = 15000  # H 100mm당 추가
ASSEMBLY_SIE_BONUS_50_100AF = 10000  # SIE-32/32GRHS 대부분인 경우

# 125~250AF (기준: W700×H800)
ASSEMBLY_BASE_H_125_250AF = 800  # mm
ASSEMBLY_BASE_PRICE_125_250AF = 60000
ASSEMBLY_H_INCREMENT_125_250AF = 15000  # H 100mm당 추가
ASSEMBLY_SIE_BONUS_125_250AF = 10000  # SIE-32/32GRHS 대부분인 경우

# 400AF (기준: W800×H1200)
ASSEMBLY_BASE_H_400AF = 1200  # mm
ASSEMBLY_BASE_PRICE_400AF = 130000
ASSEMBLY_H_INCREMENT_400AF = 20000  # H 100mm당 추가
ASSEMBLY_SIE_BONUS_400AF = 15000  # SIE-32/32GRHS 대부분인 경우

# 600~800AF (기준: W900×H1600)
ASSEMBLY_BASE_H_600_800AF = 1600  # mm
ASSEMBLY_BASE_PRICE_600_800AF = 250000
ASSEMBLY_H_INCREMENT_600_800AF = 40000  # H 100mm당 추가
ASSEMBLY_SIE_BONUS_600_800AF = 15000  # SIE-32/32GRHS 대부분인 경우

# SIE 보너스 적용 조건 (대표님 피드백 2024-12-10)
# - 외함 600×700 이상 AND 소형 14개 이상일 때만 적용
SIE_BONUS_MIN_ENCLOSURE_W = 600  # SIE 보너스 적용 최소 폭 (mm)
SIE_BONUS_MIN_ENCLOSURE_H = 700  # SIE 보너스 적용 최소 높이 (mm)
SIE_BONUS_MIN_SMALL_BREAKER_COUNT = 14  # SIE 보너스 적용 최소 소형 개수

# DEPRECATED: 이전 차단기 수량 기반 계산 (더 이상 사용하지 않음)
ASSEMBLY_BASE_PRICE = 50000  # Legacy
ASSEMBLY_PER_BREAKER_100AF = 2000  # Legacy
ASSEMBLY_PER_BREAKER_250AF = 3000  # Legacy
ASSEMBLY_PER_BREAKER_400AF = 5000  # Legacy
ASSEMBLY_PER_BREAKER_800AF = 6000  # Legacy
ASSEMBLY_H_INCREMENT_PER_100MM = 15000  # Legacy - 50~250AF 기준값

# ============================================================
# Rounding Utility (라운딩 함수) - Phase VII-3
# ============================================================


def apply_rounding(value: float, decimal_places: int = 1) -> float:
    """
    Apply SSOT rounding policy (HALF_EVEN: 은행가 반올림)

    Args:
        value: 반올림할 값
        decimal_places: 소수점 자리수 (기본 1자리)

    Returns:
        float: 반올림된 값

    Example:
        >>> apply_rounding(1.25, 1)
        1.2  # HALF_EVEN: 1.25 → 1.2 (짝수로 반올림)
        >>> apply_rounding(1.35, 1)
        1.4  # HALF_EVEN: 1.35 → 1.4 (짝수로 반올림)
    """
    d = Decimal(str(value))
    quantize_str = "0." + "0" * (decimal_places - 1) + "1" if decimal_places > 0 else "1"
    return float(d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_EVEN))


# ============================================================
# File Paths (Knowledge Base)
# ============================================================
KNOWLEDGE_DIR_NAME = "temp_basic_knowledge"
CORE_RULES_FILENAME = "core_rules.json"
FORMULAS_FILENAME = "formulas.json"

# ============================================================
# Catalog Settings
# ============================================================
MAX_CATALOG_SEARCH_DIFF_MM = 500  # 카탈로그 검색 최대 오차 (mm)
CATALOG_MATCH_TOLERANCE = 50  # 매칭 허용 오차 (mm)

# ============================================================
# Timeout & Performance
# ============================================================
API_RESPONSE_TIMEOUT_MS = 200  # API 응답 목표 시간 (p95)
HEALTH_CHECK_TIMEOUT_MS = 50  # Health 체크 목표 시간

# ============================================================
# Validation Constants
# ============================================================
MIN_BRANCH_BREAKERS = 1  # 최소 분기 차단기 수량
MIN_CLEARANCE_MM = 5.0  # 최소 간섭 거리

# Phase Balance (Count-Based) - 개수 기반 상평형
PHASES = ["R", "S", "T"]  # N상 제외, 배치 의사결정 대상 3상
PHASE_BALANCE_MODE = "count"  # 개수 기반 (amp/weighted 폐기)
MAX_COUNT_DIFF = 1  # R/S/T 개수 최대 허용 차이
TARGET_COUNT_DIFF = 0  # 목표: 완전 균등
PHASE_LABEL_NORMALIZER = {
    "r": "R",
    "s": "S",
    "t": "T",
    "R": "R",
    "S": "S",
    "T": "T",
}  # 대소문자 정규화

# DEPRECATED: 전류 기반 상평형 (사용 금지)
MAX_PHASE_IMBALANCE_PERCENT = 4.0  # DEPRECATED: amp-weighted 폐기, count-based만 사용

# Breaker AF-Pole Combination Validation
VALID_AF_VALUES = [32, 50, 60, 100, 125, 200, 225, 250, 400, 600, 800]  # 유효한 AF 값
MIN_AF_FOR_3P_4P = 50  # 3P/4P 차단기는 50AF부터 허용
SMALL_BREAKER_MAX_POLES = 2  # 소형 차단기(32AF)는 2P만 허용

# AF별 허용 극수 (MANDATORY 검증)
VALID_AF_POLE_COMBINATIONS = {
    32: [2],  # 소형 (SIE-32, SIB-32, 32GRHS, BS-32)
    50: [2, 3, 4],
    60: [2, 3, 4],
    100: [2, 3, 4],
    125: [2, 3, 4],
    200: [2, 3, 4],
    225: [2, 3, 4],
    250: [2, 3, 4],
    400: [3, 4],  # 400AF부터는 2P 없음
    600: [3, 4],
    800: [3, 4],
}

# Unit of Measurement (UOM) Normalization
UOM_PATTERN_MM = r"^\s*(\d+(?:\.\d+)?)\s*(mm|MM|밀리미터)?\s*$"  # mm 단위
UOM_PATTERN_CM = r"^\s*(\d+(?:\.\d+)?)\s*(cm|CM|센티미터)\s*$"  # cm 단위
UOM_PATTERN_INCH = r"^\s*(\d+(?:\.\d+)?)\s*(in|inch|inches|인치)?\s*$"  # inch 단위

# Unit Conversion Factors (to mm)
UOM_CM_TO_MM = 10.0
UOM_INCH_TO_MM = 25.4

# ============================================================
# Excel Layout Constants
# ============================================================
EXCEL_BLANK_ROWS_DEFAULT = 5  # 기본 공백 행 수
EXCEL_BLANK_ROWS_THRESHOLD_35 = 35  # 35열 이상 시 공백 3행
EXCEL_BLANK_ROWS_THRESHOLD_40 = 40  # 40열 이상 시 공백 2행
EXCEL_BLANK_ROWS_MEDIUM = 3  # 중간 크기 공백
EXCEL_BLANK_ROWS_SMALL = 2  # 작은 크기 공백

# ============================================================
# Document Validation (Doc Lint Guard)
# ============================================================
# Required fields for each document type (used by doc_lint_guard.py)
REQUIRED_FIELDS = {
    "cover": [
        ("cover_data.project.title", "cover_data.project.title"),
        ("cover_data.project.client", "cover_data.project.client"),
        ("cover_data.financial.total", "cover_data.financial.total"),
        ("cover_data.signature.prepared_by", "cover_data.signature.prepared_by"),
    ],
    "placement": [
        ("phase_imbalance_pct", "phase_imbalance_pct"),
        ("clearances_violation", "clearances_violation"),
        ("thermal_violation", "thermal_violation"),
    ],
    "enclosure": [
        ("selected_sku.sku", "selected_sku.sku"),
        ("selected_sku.fit_score", "selected_sku.fit_score"),
    ],
    "format": [
        ("named_ranges.total", "named_ranges.total"),
        ("format_lint.errors", "format_lint.errors"),
    ],
}

# ============================================================
# Spatial/Clearance Constants (2.5D Spatial Assistant)
# ============================================================
# Panel dimensions (mm)
PANEL_PITCH_MM = 45  # Standard panel rail pitch
PANEL_WIDTH_MM = 600  # Standard panel width
PANEL_HEIGHT_MM = 1200  # Standard panel height
PANEL_DEPTH_MM = 250  # Standard panel depth

# Clearance requirements (mm)
VERTICAL_CLEARANCE_MM = 600  # Min vertical clearance for service
HORIZONTAL_CLEARANCE_MM = 50  # Min horizontal clearance
SERVICE_DEPTH_MM = 200  # Service access depth

# ============================================================
# Infrastructure Constants (JWKS, RLS, Evidence, S3)
# ============================================================
# JWKS (JSON Web Key Set) - jwks_sop.py
DEFAULT_CACHE_TTL = 3600  # JWKS cache TTL in seconds (1 hour)
DEFAULT_MAX_RETRIES = 4  # JWKS fetch max retry attempts
DEFAULT_BACKOFF_SECONDS = [30, 60, 120, 300]  # JWKS exponential backoff strategy

# RLS (Row Level Security) - rls_loader.py
DEFAULT_POLICY_FILE = "kpew_policies.sql"  # Default RLS policy file name

# Evidence & Paths
EVIDENCE_DIR = Path(
    "out/evidence/EvidencePack_v2/ci/jwks_failures"
)  # JWKS failure evidence directory
RLS_POLICIES_BASE_DIR = (
    "core/ssot/rls"  # RLS policies directory (relative to package root)
)

# S3 Storage (Phase XII)
S3_URL_TTL_SECONDS = 900  # Pre-signed URL expiration time (15 minutes)

# PDF Policy (Phase XII) - Enforced validation requirements
PDF_POLICY = {
    "page_size": "A4",  # Required page size (210×297mm ±0.5mm)
    "margin_mm": 10,  # Minimum margin on all sides (mm)
    "font": "MalgunGothic",  # Required Korean font family (or NanumGothic/NanumMyeongjo)
    "footer_required": True,  # Evidence Footer must be present
}

# ============================================================
# Excel Styles (excel_styles.py)
# ============================================================
# NOTE: openpyxl objects (Font, Alignment, Border, PatternFill) cannot be defined here
# as constants because they need openpyxl import. The style objects will remain in
# excel_styles.py but documented here for reference.
#
# Defined in engine/excel_styles.py:
# - DEFAULT_FONT = Font(name="맑은고딕", size=12, bold=False)
# - BOLD_FONT = Font(name="맑은고딕", size=12, bold=True)
# - ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
# - ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
# - ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
# - THIN_BORDER = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
# - GRAY_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
# - NO_FILL = PatternFill(fill_type=None)
#
# These cannot be migrated to SSOT as they are openpyxl objects, not primitive constants

# ============================================================
# Model Defaults (engine/models.py)
# ============================================================
DEFAULT_ENCLOSURE_SIZE = 700 * 1450  # W*H (mm²) - Default enclosure size

# ============================================================
# Quality Gates (infra/quality_gate.py)
# ============================================================
# NOTE: Quality gate list definitions (ENCLOSURE_GATES, BREAKER_PLACEMENT_GATES, etc.)
# use QualityGate objects which are defined in quality_gate.py. These list definitions
# reference SSOT threshold constants and cannot be moved here.
#
# The individual thresholds are already in SSOT:
# - FIT_SCORE_THRESHOLD, PHASE_BALANCE_THRESHOLD, etc.
#
# Gate lists defined in infra/quality_gate.py:
# - ENCLOSURE_GATES (uses FIT_SCORE_THRESHOLD, IP_RATING_THRESHOLD, DOOR_CLEARANCE_THRESHOLD)
# - BREAKER_PLACEMENT_GATES (uses PHASE_BALANCE_THRESHOLD, CLEARANCE_VIOLATIONS_THRESHOLD)
# - ESTIMATE_FORMAT_GATES (uses FORMULA_PRESERVATION_THRESHOLD, NAMED_RANGE_DAMAGE_THRESHOLD)
# - DOC_LINT_GATES (uses LINT_ERRORS_THRESHOLD, POLICY_VIOLATIONS_THRESHOLD)

# ============================================================
# Error Codes (errors/error_codes.py)
# ============================================================
# NOTE: ERROR_CODE_MAP is a dict that maps error code strings to ErrorCode objects
# defined in errors/error_codes.py. This map references local objects and cannot
# be migrated to SSOT. It is documented here for completeness.
#
# Defined in errors/error_codes.py:
# - ERROR_CODE_MAP = { "INP-001": INP_001, "BUG-001": BUG_001, ... }
#
# This is a legitimate local constant that should be excluded from SSOT checks

# ============================================================
# RAG System Constants (rag/config.py에서 SSOT 통합)
# ============================================================
# Chunking Settings
RAG_CHUNK_SIZE = 512  # 청킹 토큰 크기
RAG_CHUNK_OVERLAP = 50  # 청크 간 오버랩

# ChromaDB Settings
RAG_COLLECTION_NAME = "kis_knowledge"  # ChromaDB 컬렉션명

# Embedding Model Settings
RAG_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RAG_EMBEDDING_DIMENSION = 384  # MiniLM 출력 차원

# Search Settings
RAG_DEFAULT_TOP_K = 5  # 기본 검색 결과 수
RAG_MAX_TOP_K = 20  # 최대 검색 결과 수
RAG_SIMILARITY_THRESHOLD = 0.7  # 유사도 임계값
RAG_RRF_K = 60  # Reciprocal Rank Fusion k 파라미터

# Korean Stopwords for Search
RAG_STOPWORDS = frozenset([
    "의", "가", "이", "은", "들", "는", "좀", "잘", "걍", "과", "도", "를", "으로", "자",
    "에", "와", "한", "하다", "것", "등", "및", "때", "수", "있다", "없다", "되다",
])

# ============================================================
# Cache Constants (services/cache.py에서 SSOT 통합)
# ============================================================
CATALOG_CACHE_TTL = 900  # 15분 (카탈로그 캐시 TTL)
PRICE_CACHE_TTL = 300  # 5분 (가격 캐시 TTL)
METRICS_WINDOW_SIZE = 1000  # 메트릭 윈도우 크기

# ============================================================
# Supabase Storage Constants (services에서 SSOT 통합)
# ============================================================
# Document Service
DOCUMENT_BUCKET = "estimates"  # Supabase Storage 버킷명 (견적서)
DOCUMENT_SIGNED_URL_EXPIRY = 600  # 10분 (prod: 300, staging: 600)

# Evidence Service
EVIDENCE_BUCKET = "evidence"  # Supabase Storage 버킷명 (증거팩)
EVIDENCE_PACK_PREFIX = "evidence_packs"  # 증거팩 경로 접두사
EVIDENCE_SIGNED_URL_EXPIRY = 600  # 10분

# ============================================================
# Validation Constants (services/validation_service.py에서 SSOT 통합)
# ============================================================
# NOTE: PHASE_BALANCE_THRESHOLD is already defined at line 64 (value: 4.0)
# DUPLICATE REMOVED - LAW-02 SSOT violation fix
MAGNET_REQUIRED_ACCESSORIES = ["fuseholder", "terminal_block", "pvc_duct", "cable_wire"]
TIMER_REQUIRED_ACCESSORIES = ["cable_wire"]

# ============================================================
# AI Chat Constants (api/routes/ai_chat.py에서 SSOT 통합)
# ============================================================
AI_MODELS = {
    "claude-opus": {
        "name": "Claude 4.5 Opus",
        "description": "복잡한 분석과 창의적 작업에 최적",
        "provider": "anthropic",
    },
    "gemini-pro": {
        "name": "Gemini 3 Pro",
        "description": "빠른 응답과 멀티모달 처리",
        "provider": "google",
    },
    "gpt-thinking": {
        "name": "GPT 5.1 Thinking",
        "description": "심층 추론과 단계별 사고",
        "provider": "openai",
    },
}

# ============================================================
# Fallback & Defaults (CatalogService)
# ============================================================
FALLBACK_ENCLOSURE_SIZES = [
    (500, 600, 150), (500, 700, 150),
    (600, 700, 200), (600, 800, 200), (600, 900, 200),
    (700, 1000, 200), (700, 1200, 200), (700, 1400, 200),
    (800, 1600, 250), (800, 1800, 250),
    (1000, 2000, 300)
]
FALLBACK_ENCLOSURE_PRICE_FACTOR_INDOOR = 1.2
FALLBACK_ENCLOSURE_PRICE_FACTOR_OUTDOOR = 2.5
FALLBACK_ENCLOSURE_DIVISOR = 10000

# ============================================================
# 고객 미수금 관련 상수 (Customer Receivables)
# ============================================================

# 미수금 업데이트 모드
RECEIVABLE_UPDATE_MODE_AUTO = "auto"  # 자동 업데이트
RECEIVABLE_UPDATE_MODE_MANUAL = "manual"  # 수동 업데이트

# 미수금 한도 경고 임계값 (%)
RECEIVABLE_WARNING_THRESHOLD = 80  # 신용한도의 80% 도달 시 경고
RECEIVABLE_CRITICAL_THRESHOLD = 100  # 신용한도 초과 시 치명적 경고

# 미수금 관련 오류 코드
ERROR_CODE_RECEIVABLE_OVERFLOW = "E_RECV_001"  # 신용한도 초과
ERROR_CODE_RECEIVABLE_UPDATE_FAILED = "E_RECV_002"  # 업데이트 실패

# ============================================================
# Item Classification Keywords (품목 분류 키워드)
# ============================================================
# 차단기 모델명 키워드 (MCCB, ELB 계열)
BREAKER_MODEL_KEYWORDS = (
    "MCCB", "ELB",
    "SBE", "SBS", "SEE", "SES", "SIE", "SIB",  # 상도
    "ABN", "ABS", "EBN", "EBS"  # LS
)

# 부속자재 제외 키워드 (차단기로 오인되지 않도록 제외)
# 예: "ELB지지대"는 ELB 키워드 포함하지만 부속자재임
ACCESSORY_EXCLUDE_KEYWORDS = (
    "지지대", "지지", "SUPPORT", "HOLDER",
    "BAR", "COVER", "INSULATOR",
    "CHARGE", "COATING"
)

