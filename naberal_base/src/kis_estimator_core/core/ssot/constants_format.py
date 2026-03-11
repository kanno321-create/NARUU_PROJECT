"""
SSOT Format Constants - 견적서/표지/조건 포맷 상수 (Spec Kit 절대준수)

절대 원칙:
- 모든 표지/견적/조건/단위/공식 상수는 여기서만 정의
- 매직 리터럴 금지 (숫자, 문자열, 셀 주소 등)
- 변경 시 이 파일만 수정

원본 출처:
- 절대코어파일/견적서장성법V1.0.txt (대표님 작성 실무 문서)
- 절대코어파일/견적서표지작성법.txt (대표님 작성 실무 문서)
"""

# ============================================================
# Sheet Names (엑셀 시트명)
# ============================================================
SHEET_COVER = "표지"  # 표지 시트
SHEET_QUOTE = "견적서"  # 견적서 시트
SHEET_CONDITIONS = "견적조건"  # 견적조건 시트 (optional)

# ============================================================
# Cover Fields (표지 필드 - Cell References)
# ============================================================
# 기본 정보
COVER_DATE_CELL = "C3"  # 날짜 (형식: YYYY년 MM월 DD일)
COVER_CUSTOMER_CELL = "C5"  # 거래처명
COVER_PROJECT_CELL = "C7"  # 건명

# 분전반 정보 시작 행
COVER_PANEL_START_ROW = 17  # 분전반 정보 시작 행 (B17부터)
COVER_PANEL_NAME_COL = "B"  # 분전반명 컬럼
COVER_PANEL_SIZE_COL = "D"  # 외함 사이즈 컬럼
COVER_PANEL_UNIT_COL = "F"  # 단위 컬럼
COVER_PANEL_QTY_COL = "G"  # 수량 컬럼
COVER_PANEL_PRICE_COL = "H"  # 단가 컬럼 (=+견적서!G[소계행])
COVER_PANEL_AMOUNT_COL = "I"  # 금액 컬럼 (=H*G)
COVER_PANEL_NOTE_COL = "J"  # 특이사항 컬럼

# 합계/부가세
COVER_TOTAL_TEXT = "합   계"  # 합계 표기 (공백 3개)
COVER_SUBTOTAL_UNIT = "식"  # 소계 단위
COVER_VAT_MULTIPLIER = 1.1  # 부가세 포함 (×1.1)

# NOTE 섹션
COVER_NOTE_TEMPLATE = "< NOTE > 1. 차단기: {breaker_brand}, 외함: {enclosure_spec}"

# ============================================================
# Quote Tab Fields (견적서 탭 필드 - Cell References)
# ============================================================
# 헤더 정보
QUOTE_PANEL_NAME_CELL = "B1"  # 분전반명 (견적조건 1)
QUOTE_ENCLOSURE_TYPE_CELL = "B3"  # 외함 종류 및 재질 (견적조건 5, 9)

# 견적 항목 시작 행
QUOTE_ITEMS_START_ROW = 3  # 외함부터 시작 (B3~)

# 견적 항목 컬럼
QUOTE_COL_ITEM = "B"  # 품목
QUOTE_COL_SPEC = "C"  # 규격
QUOTE_COL_UNIT = "E"  # 단위
QUOTE_COL_QTY = "F"  # 수량
QUOTE_COL_PRICE = "G"  # 단가
QUOTE_COL_AMOUNT = "H"  # 금액 (수식: =F*G)

# 소계/합계 표기
QUOTE_SUBTOTAL_TEXT = "소  계"  # 소계 (공백 2개)
QUOTE_TOTAL_TEXT = "합  계"  # 합계 (공백 2개)
QUOTE_TOTAL_UNIT = "식"  # 합계 단위

# 견적 공백 규칙 (견적조건 8)
QUOTE_BLANK_ROWS_DEFAULT = 5  # 기본 공백 행 수
QUOTE_BLANK_ROWS_35_PLUS = 3  # 총 열 수 ≥ 35일 때
QUOTE_BLANK_ROWS_40_PLUS = 2  # 총 열 수 ≥ 40일 때

# ============================================================
# Required Materials (필수 자재 - 견적조건 7)
# ============================================================
# E.T (Earth Terminal)
MATERIAL_ET_NAME = "E.T"
MATERIAL_ET_UNIT = "EA"
MATERIAL_ET_PRICE_50_250AF = 4500  # 50~250AF
MATERIAL_ET_PRICE_400AF = 12000  # 400AF
MATERIAL_ET_PRICE_600_800AF = 18000  # 600~800AF
MATERIAL_ET_QTY_PER_BREAKERS = 12  # 차단기 12개당 E.T 1개

# N.T (Neutral Terminal)
MATERIAL_NT_NAME = "N.T"
MATERIAL_NT_UNIT = "EA"
MATERIAL_NT_QTY = 1
MATERIAL_NT_PRICE = 3000

# N.P (Name Plate)
MATERIAL_NP_CARD_HOLDER_NAME = "CARD HOLDER"
MATERIAL_NP_CARD_HOLDER_UNIT = "EA"
MATERIAL_NP_CARD_HOLDER_PRICE = 800
MATERIAL_NP_3T_NAME = "3T×40×200"
MATERIAL_NP_3T_UNIT = "EA"
MATERIAL_NP_3T_PRICE = 4000

# MAIN BUS-BAR
# NOTE: 부스바는 원자재라 가격변동이 심함 - 대표님이 알려줄 때마다 조정
# 2026-02-06 기준: 31,000원/kg (이전: 22,000원/kg) - 원자재 상승
MATERIAL_MAIN_BUSBAR_NAME = "MAIN BUS-BAR"
MATERIAL_MAIN_BUSBAR_UNIT = "kg"
MATERIAL_MAIN_BUSBAR_PRICE_PER_KG = 31000
MATERIAL_BUSBAR_SPEC_50_125AF = "3T×15"
MATERIAL_BUSBAR_SPEC_200_250AF = "5T×20"
MATERIAL_BUSBAR_SPEC_400AF = "6T×30"
MATERIAL_BUSBAR_SPEC_600_800AF = "8T×40"

# BUS-BAR (분기용)
# NOTE: 메인과 동일 단가 적용 (2026-02-06 기준: 31,000원/kg) - 원자재 상승
MATERIAL_BRANCH_BUSBAR_NAME = "BUS-BAR"
MATERIAL_BRANCH_BUSBAR_UNIT = "kg"
MATERIAL_BRANCH_BUSBAR_PRICE_PER_KG = 31000

# COATING
MATERIAL_COATING_NAME = "COATING"
MATERIAL_COATING_SPEC = "PVC(20mm)"
MATERIAL_COATING_UNIT = "M"
MATERIAL_COATING_QTY = 1
MATERIAL_COATING_PRICE = 5000

# P-COVER
MATERIAL_PCOVER_NAME = "P-COVER"
MATERIAL_PCOVER_SPEC = "아크릴(PC)"
MATERIAL_PCOVER_UNIT = "EA"
MATERIAL_PCOVER_FORMULA_DIVISOR = 90000  # (W×H) ÷ 90,000
MATERIAL_PCOVER_FORMULA_MULTIPLIER = 3200  # × 3,200원

# 차단기지지대 (400AF 이상만)
MATERIAL_BREAKER_SUPPORT_NAME = "차단기지지대"
MATERIAL_BREAKER_SUPPORT_UNIT = "EA"
MATERIAL_BREAKER_SUPPORT_PRICE = 1200
MATERIAL_BREAKER_SUPPORT_MIN_AF = 400  # 400AF 이상만
MATERIAL_BREAKER_SUPPORT_DIVISOR = 35  # 분기차단기 총길이 ÷ 35 + 2

# ELB지지대
MATERIAL_ELB_SUPPORT_NAME = "ELB지지대"
MATERIAL_ELB_SUPPORT_UNIT = "EA"
MATERIAL_ELB_SUPPORT_PRICE = 500
# 소형차단기 모델명 (SIE-32, SIB-32, 32GRHS, BS-32)
MATERIAL_ELB_SUPPORT_SMALL_MODELS = ["SIE-32", "SIB-32", "SBW-32", "32GRHS", "BS-32"]

# INSULATOR
MATERIAL_INSULATOR_NAME = "INSULATOR"
MATERIAL_INSULATOR_SPEC = "EPOXY 40×40"
MATERIAL_INSULATOR_UNIT = "EA"
# 메인차단기 AF별 INSULATOR 단가 (CLAUDE.md 기준)
MATERIAL_INSULATOR_PRICE_50_250AF = 1100   # 50~250AF: 1,100원
MATERIAL_INSULATOR_PRICE_400_800AF = 4400  # 400~800AF: 4,400원
MATERIAL_INSULATOR_PRICE = 1100  # 기본값 (하위호환)
MATERIAL_INSULATOR_QTY_PER_SUPPORT = 4  # 지지대 1개당 4개

# 잡자재비
MATERIAL_MISC_NAME = "잡자재비"
MATERIAL_MISC_UNIT = "식"
MATERIAL_MISC_QTY = 1
MATERIAL_MISC_BASE_PRICE = 7000
MATERIAL_MISC_PER_100MM_H = 1000  # H값 100mm 증가마다 +1,000원
MATERIAL_MISC_PER_ACCESSORY = 10000  # 부속자재 1개당 +10,000원
MATERIAL_MISC_MAX_PRICE = 40000

# ASSEMBLY CHARGE (조립비)
MATERIAL_ASSEMBLY_NAME = "ASSEMBLY CHARGE"
MATERIAL_ASSEMBLY_UNIT = "식"
MATERIAL_ASSEMBLY_QTY = 1
# 인건비 계산식 (별도 정의 필요)

# ============================================================
# Accessories (부속자재 - 견적조건 11)
# ============================================================
# MG.CONTACTOR (마그네트)
ACC_MAGNET_NAME = "MG.CONTACTOR"
ACC_MAGNET_UNIT = "EA"

# FUSEHOLDER
ACC_FUSEHOLDER_NAME = "FUSEHOLDER"
ACC_FUSEHOLDER_SPEC = "4/W"
ACC_FUSEHOLDER_UNIT = "EA"
ACC_FUSEHOLDER_QTY_PER_MAGNET = 1
ACC_FUSEHOLDER_PRICE = 4000

# TERMINAL BLOCK
ACC_TERMINAL_BLOCK_NAME = "TERMINAL BLOCK"
ACC_TERMINAL_BLOCK_SPEC = "600V"
ACC_TERMINAL_BLOCK_UNIT = "EA"
ACC_TERMINAL_BLOCK_QTY_PER_MAGNET = 3  # 중요: 3개 (1개 아님)
ACC_TERMINAL_BLOCK_PRICE = 4000

# PVC DUCT
ACC_PVC_DUCT_NAME = "PVC"
ACC_PVC_DUCT_SPEC = "DUCT"
ACC_PVC_DUCT_UNIT = "EA"
ACC_PVC_DUCT_QTY_PER_MAGNET = 2  # 상단 1개 + 하단 1개
ACC_PVC_DUCT_PRICE = 3000

# CABLE/WIRE
ACC_CABLE_WIRE_NAME = "CABLE/WIRE"
ACC_CABLE_WIRE_SPEC = "KIV"
ACC_CABLE_WIRE_UNIT = "식"
ACC_CABLE_WIRE_QTY_PER_MAGNET = 2  # 중요: 2개 (1식 아님)
ACC_CABLE_WIRE_PRICE = 25000

# 마그네트 인건비
ACC_MAGNET_LABOR_COST = 20000  # 마그네트 1개당

# PBL (ON/OFF 스위치)
ACC_PBL_NAME = "PBL"
ACC_PBL_SPEC = "ON/OFF"
ACC_PBL_UNIT = "EA"
ACC_PBL_QTY_PER_MAGNET = 2
ACC_PBL_PRICE = 4000

# TIMER (24H)
ACC_TIMER_NAME = "TIMER"
ACC_TIMER_SPEC = "24H"
ACC_TIMER_UNIT = "EA"
ACC_TIMER_PRICE = 26000
ACC_TIMER_LABOR_COST = 12000  # 타이머 1개당

# V/A-METER (전압/전류계)
ACC_VA_METER_NAME = "V/A-METER"
ACC_VA_METER_UNIT = "EA"
ACC_VA_METER_QTY = 2
ACC_VA_METER_PRICE = 24000

ACC_VS_AS_NAME = "VS/AS"
ACC_VS_AS_UNIT = "EA"
ACC_VS_AS_QTY = 2
ACC_VS_AS_PRICE = 12000

ACC_VA_FUSEHOLDER_QTY = 3
ACC_VA_TERMINAL_BLOCK_QTY = 2
ACC_VA_PVC_DUCT_QTY = 3
ACC_VA_CABLE_WIRE_PRICE = 30000

# 3CT부스바용
ACC_3CT_BUSBAR_NAME = "3CT부스바용"
ACC_3CT_BUSBAR_UNIT = "EA"
ACC_3CT_BUSBAR_QTY = 1

# SPD (서지보호장치)
ACC_SPD_NAME = "SPD직결형"
ACC_SPD_SPEC = "40kA"
ACC_SPD_UNIT = "EA"
ACC_SPD_QTY = 1
ACC_SPD_PRICE = 50000
ACC_SPD_CABLE_WIRE_PRICE = 15000

# 계량기 (단상)
ACC_METER_1P_NAME = "계량기"
ACC_METER_1P_UNIT = "EA"
ACC_METER_1P_CABLE_WIRE_PRICE = 15000

# 계량기 (3상)
ACC_METER_3P_NAME = "계량기"
ACC_METER_3P_UNIT = "EA"
ACC_METER_3P_CABLE_WIRE_PRICE = 18000

# CT계량기
ACC_CT_METER_NAME = "CT계량기"
ACC_CT_METER_SPEC = "3상4선식"
ACC_CT_METER_UNIT = "EA"
ACC_CT_METER_PRICE = 23000
ACC_CT_METER_FUSEHOLDER_QTY = 3
ACC_CT_METER_TERMINAL_BLOCK_QTY = 1
ACC_CT_METER_TERMINAL_BLOCK_PRICE = 3000

# ============================================================
# Unit of Measure (단위 기입표)
# ============================================================
UNIT_ENCLOSURE = "면"  # 외함 및 SUSCOVER
UNIT_BREAKER = "EA"  # 차단기
UNIT_ET = "EA"  # E.T
UNIT_NT = "EA"  # N.T
UNIT_NP = "EA"  # N.P
UNIT_MAIN_BUSBAR = "kg"  # MAIN BUS-BAR
UNIT_BRANCH_BUSBAR = "kg"  # BUS-BAR
UNIT_BUSBAR = "kg"  # BUS-BAR (generic)
UNIT_COATING = "M"  # COATING
UNIT_PCOVER = "EA"  # P-COVER
UNIT_BREAKER_SUPPORT = "EA"  # 차단기지지대
UNIT_ELB_SUPPORT = "EA"  # ELB지지대
UNIT_INSULATOR = "EA"  # INSULATOR
UNIT_MISC = "식"  # 잡자재비
UNIT_ASSEMBLY = "식"  # ASSEMBLY CHARGE
UNIT_CABLE_WIRE = "식"  # CABLE/WIRE
UNIT_ACCESSORY = "EA"  # 모든 부속자재
UNIT_LABOR = "식"  # 운임비/설치비

# ============================================================
# Formulas (수식 템플릿)
# ============================================================
# 금액 수식 (단가 × 수량)
FORMULA_AMOUNT = "={price_col}{row}*{qty_col}{row}"  # 예: =G3*F3

# 소계 수식 (SUM)
FORMULA_SUBTOTAL = "=SUM({amount_col}{start_row}:{amount_col}{end_row})"

# 합계 수식 (소계 × 수량)
FORMULA_TOTAL = "={subtotal_amount}*{total_qty}"

# 부가세 포함 (합계 × 1.1)
FORMULA_VAT_INCLUDED = "={total_amount}*1.1"

# P-COVER 단가 수식
FORMULA_PCOVER_PRICE = "=(({width}*{height})/90000)*3200"

# 잡자재비 수식
FORMULA_MISC_PRICE = (
    "=7000+ROUNDDOWN(({height}-600)/100,0)*1000+{accessory_count}*10000"
)

# ============================================================
# Cell Formula Mapping (셀별 수식 매핑 - inject_or_fail 정책용)
# ============================================================
# 견적서!H 컬럼 (금액 = 단가 × 수량)
# 동적 범위: H3~H200 → "=G{row}*F{row}"
FORMULA_MAP_QUOTE_H_PATTERN = "=G{row}*F{row}"  # 견적서!H{row} 수식

# 표지!I 컬럼 (금액 = 단가 × 수량)
# 동적 범위: I17~I50 → "=H{row}*G{row}"
FORMULA_MAP_COVER_I_PATTERN = "=H{row}*G{row}"  # 표지!I{row} 수식

# 표지!C15 (한글 금액)
FORMULA_MAP_COVER_C15 = "=NUMBERSTRING(I18,1)"  # 표지!C15 수식 (합계 행 +1)

# ============================================================
# Named Ranges (네임드 범위)
# ============================================================
# 견적서 시트
NAMED_RANGE_QUOTE_ITEMS = "견적항목"  # 견적 항목 범위
NAMED_RANGE_QUOTE_SUBTOTAL = "소계"  # 소계 셀
NAMED_RANGE_QUOTE_TOTAL = "합계"  # 합계 셀
NAMED_RANGE_QUOTE_VAT = "부가세포함"  # 부가세 포함 셀

# 표지 시트
NAMED_RANGE_COVER_PANELS = "분전반목록"  # 분전반 목록 범위
NAMED_RANGE_COVER_TOTAL = "표지합계"  # 표지 합계 셀
NAMED_RANGE_COVER_VAT = "표지부가세"  # 표지 부가세 셀

# ============================================================
# Validation Rules (검증 규칙)
# ============================================================
# 날짜 형식
DATE_FORMAT_REGEX = r"^\d{4}년\s+\d{1,2}월\s+\d{1,2}일$"

# 사이즈 형식 (W*H*D 또는 W×H×D)
SIZE_FORMAT_REGEX = r"^\d+[*×]\d+[*×]\d+$"

# 금지 문자
FORBIDDEN_CHARS = ["<", ">", "|", ":", "\\", "/", "?", "*"]

# 필수 필드 (표지)
REQUIRED_COVER_FIELDS = [
    "date",
    "customer",
    "panel_name",
    "size",
    "unit",
    "qty",
    "price",
]

# 필수 필드 (견적서)
REQUIRED_QUOTE_FIELDS = ["item", "unit", "qty", "price"]

# ============================================================
# Conditions Sheet Fields (조건 시트 필드 - Cell References)
# ============================================================
CONDITIONS_TITLE_CELL = "B2"  # 제목: "견적조건"
CONDITIONS_START_ROW = 4  # 조건 항목 시작 행
CONDITIONS_ITEM_COL = "B"  # 조건 번호 컬럼
CONDITIONS_DESC_COL = "C"  # 조건 설명 컬럼
CONDITIONS_ROW_HEIGHT = 25  # 조건 항목 행 높이 (pt)

# ============================================================
# Conditions (견적조건 - 견적조건표.txt)
# ============================================================
CONDITION_1_PANEL_NAME = (
    "분전반명: 판넬명 없으면 '분전반' 표기, 2개 이상 시 '분전반1', '분전반2'"
)
CONDITION_2_ENCLOSURE_QTY = "외함 수량: 일반 1면, 초과 시 분할"
CONDITION_3_MAIN_QTY = "메인차단기 수량: 일반 1개, 예외 가능"
CONDITION_4_BREAKER_SPEC = "차단기 스펙: POLE → AF → AT → kA 순서"
CONDITION_5_PANEL_SPEC = "속판제작: 고객이 외함 보유 시 '속판제작' 기입"
CONDITION_6_BRANCH_TYPES = "분기차단기: 여러 종류 95%, 종류별 1열씩"
CONDITION_7_REQUIRED_MATERIALS = "필수 자재: E.T, N.T, N.P, MAIN BUS-BAR, BUS-BAR, COATING, P-COVER, 차단기지지대, ELB지지대, INSULATOR, 잡자재비, ASSEMBLY CHARGE"
CONDITION_8_BLANK_ROWS = "견적 공백: <35열=5행, ≥35열=3행, ≥40열=2행"
CONDITION_9_매입함 = "매입함: 벽체 매입, 도어 없음, SUSCOVER 별도"
CONDITION_10_MULTI_PANELS = "분전반 2종류 이상: 합계 하단 1열 공란 후 반복"
CONDITION_11_ACCESSORIES = "부속자재: MG.CONTACTOR, FUSEHOLDER, TERMINAL BLOCK, PVC, CABLE/WIRE, PBL, TIMER, V/A-METER, SPD, 계량기, CT계량기"

# ============================================================
# Text Policies (조건표 필수 문구/금칙어)
# ============================================================
# 필수 문구 (견적조건)
REQUIRED_PHRASES = [
    "납기",
    "대금",
    "유효기간",
]

# 금칙어 (견적조건)
FORBIDDEN_PHRASES = [
    "무료",
    "서비스",
    "할인",
]

# ============================================================
# Excel Protection (셀 보호)
# ============================================================
# 보호할 셀 범위 (수식 셀)
PROTECTED_FORMULA_RANGES = [
    "H3:H100",  # 견적서 금액 컬럼 (수식)
    "I17:I50",  # 표지 금액 컬럼 (수식)
]

# 잠금 해제할 셀 범위 (입력 셀)
UNLOCKED_INPUT_RANGES = [
    "C3",  # 날짜
    "C5",  # 거래처
    "C7",  # 건명
    "F3:F100",  # 수량
    "G3:G100",  # 단가
]

# ============================================================
# Validation Thresholds (I-2.1 검증 임계치)
# ============================================================
# 수식 보존율 임계치
FORMULA_PRESERVE_THRESHOLD = 95.0  # 최소 95% 보존 필요

# 숫자 정밀도
NUM_PRECISION = 12  # Decimal precision
NUM_SCALE = 4  # Decimal scale (소수점 자리)
NUM_ROUND = "HALF_EVEN"  # 반올림 정책 (은행가 반올림)

# 통화 및 단위
CURRENCY = "KRW"  # 한국 원화
UOM_POLICY = "STRICT"  # 단위 정책 (STRICT: 혼합 금지)

# 합계 검증 허용 오차
TOTAL_TOLERANCE = 0.01  # 1원 오차 허용

# 수식 토큰 (보존율 계산 시 무시할 문자)
FORMULA_WHITESPACE_TOKENS = [" ", "\t", "\n", "\r"]  # 공백 문자
FORMULA_OPERATORS = ["=", "+", "-", "*", "/", "(", ")", ",", ":"]  # 연산자

# ============================================================
# PDF Generation Constants (PDF 생성 상수)
# ============================================================
# 폰트
PDF_FONT_DEFAULT = "Helvetica"  # 기본 폰트 (영문)
PDF_FONT_KOREAN = "NanumGothic"  # 한글 폰트
PDF_FONT_SIZE_TITLE = 20  # 제목 폰트 크기
PDF_FONT_SIZE_SUBTITLE = 14  # 부제목 폰트 크기
PDF_FONT_SIZE_NORMAL = 12  # 본문 폰트 크기
PDF_FONT_SIZE_SMALL = 9  # 작은 텍스트 폰트 크기
PDF_FONT_SIZE_FOOTER = 8  # Footer 폰트 크기

# Footer
PDF_FOOTER_TEMPLATE = (
    "Build:{build_tag}  Hash:{git_hash}  DocHash:{doc_hash}  TS:{timestamp}"
)
PDF_FOOTER_POSITION_X_MM = 200  # Footer X 위치 (mm)
PDF_FOOTER_POSITION_Y_MM = 10  # Footer Y 위치 (mm)

# Page Layout
PDF_PAGE_WIDTH_MM = 210  # A4 폭 (mm)
PDF_PAGE_HEIGHT_MM = 297  # A4 높이 (mm)
PDF_MARGIN_MM = 20  # 여백 (mm)
PDF_DPI_MIN = 300  # 최소 DPI

# Conditions List (조건 시트 항목 순서)
CONDITIONS_ITEMS = [
    "CONDITION_1_PANEL_NAME",
    "CONDITION_2_ENCLOSURE_QTY",
    "CONDITION_3_MAIN_QTY",
    "CONDITION_4_BREAKER_SPEC",
    "CONDITION_5_PANEL_SPEC",
    "CONDITION_6_BRANCH_TYPES",
    "CONDITION_7_REQUIRED_MATERIALS",
    "CONDITION_8_BLANK_ROWS",
    "CONDITION_9_매입함",
    "CONDITION_10_MULTI_PANELS",
]
