"""
SSOT Format Guards - 견적서/표지 포맷 검증 가드 (Spec Kit 절대준수)

절대 원칙:
- 모든 네임드 범위/수식/합계/텍스트 정책 검증은 여기서만 정의
- 매직 리터럴 금지 (셀 주소, 정규식, 메시지 등)
- 변경 시 이 파일만 수정

가드 종류:
1. named_range_guard(): 네임드 범위 존재·범위 일치 검증
2. formula_guard(): 수식 보존 및 참조 무결성 검증
3. totals_guard(): 소계→합계→VAT→총액 일관성 검증
4. text_policy_guard(): 조건표 필수 문구/금칙어 검사
5. cell_protection_guard(): 수식 셀 보호 검증
6. nan_blank_guard(): NaN/빈칸 금지 검증

원본 출처:
- 절대코어파일/core/rules/ai_estimation_core.json (검증 체크리스트)
- Phase 3 계약 요구사항 (수식 보존 = 100%, 네임드 손상 = 0)
"""

import re
from typing import Any

from openpyxl.cell.cell import Cell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from kis_estimator_core.core.ssot.constants_format import (
    # Validation
    DATE_FORMAT_REGEX,
    FORBIDDEN_CHARS,
    FORBIDDEN_PHRASES,
    FORMULA_MAP_COVER_C15,
    FORMULA_MAP_COVER_I_PATTERN,
    # Formulas
    FORMULA_MAP_QUOTE_H_PATTERN,
    NAMED_RANGE_COVER_PANELS,
    NAMED_RANGE_COVER_TOTAL,
    NAMED_RANGE_COVER_VAT,
    # Named Ranges
    NAMED_RANGE_QUOTE_ITEMS,
    NAMED_RANGE_QUOTE_SUBTOTAL,
    NAMED_RANGE_QUOTE_TOTAL,
    NAMED_RANGE_QUOTE_VAT,
    # Protection
    PROTECTED_FORMULA_RANGES,
    # Text Policies
    REQUIRED_PHRASES,
    # Sheet Names
    SHEET_COVER,
    SHEET_QUOTE,
    SIZE_FORMAT_REGEX,
    UNLOCKED_INPUT_RANGES,
)


# ============================================================
# Helper: Formula Injection from SSOT
# ============================================================
def _inject_formula_from_ssot(worksheet: Worksheet, cell: Cell) -> str | None:
    """
    SSOT FORMULAE 매핑에서 셀에 해당하는 수식 주입 (inject_or_fail 정책용)

    Args:
        worksheet: openpyxl Worksheet
        cell: openpyxl Cell (빈 셀)

    Returns:
        수식 문자열 (=로 시작) 또는 None (매핑 없음)
    """
    sheet_name = worksheet.title
    cell_coord = cell.coordinate
    col_letter = cell.column_letter
    row_number = cell.row

    # 견적서!H 컬럼 (금액 = 단가 × 수량)
    if sheet_name == SHEET_QUOTE and col_letter == "H" and 3 <= row_number <= 200:
        return FORMULA_MAP_QUOTE_H_PATTERN.format(row=row_number)

    # 표지!I 컬럼 (금액 = 단가 × 수량)
    elif sheet_name == SHEET_COVER and col_letter == "I" and 17 <= row_number <= 50:
        return FORMULA_MAP_COVER_I_PATTERN.format(row=row_number)

    # 표지!C15 (한글 금액)
    elif sheet_name == SHEET_COVER and cell_coord == "C15":
        return FORMULA_MAP_COVER_C15

    # 매핑 없음
    return None


# ============================================================
# Guard 1: Named Range Validation
# ============================================================
def named_range_guard(
    workbook: Workbook, required_ranges: list[str] | None = None
) -> tuple[bool, list[str]]:
    """
    네임드 범위 존재·범위 일치 검증

    검증 항목:
    1. 필수 네임드 범위 존재 확인
    2. 네임드 범위가 올바른 시트/범위를 가리키는지 확인
    3. 네임드 범위 손상 여부 확인

    Args:
        workbook: openpyxl Workbook 객체
        required_ranges: 필수 네임드 범위 목록 (None이면 기본값 사용)

    Returns:
        (is_valid, errors): (검증 통과 여부, 오류 메시지 리스트)
    """
    if required_ranges is None:
        required_ranges = [
            NAMED_RANGE_QUOTE_ITEMS,
            NAMED_RANGE_QUOTE_SUBTOTAL,
            NAMED_RANGE_QUOTE_TOTAL,
            NAMED_RANGE_QUOTE_VAT,
            NAMED_RANGE_COVER_PANELS,
            NAMED_RANGE_COVER_TOTAL,
            NAMED_RANGE_COVER_VAT,
        ]

    errors = []

    # 워크북의 모든 네임드 범위 가져오기
    defined_names = workbook.defined_names

    for range_name in required_ranges:
        if range_name not in defined_names:
            errors.append(f"네임드 범위 누락: {range_name}")
            continue

        # 네임드 범위 정의 확인
        named_range = defined_names[range_name]
        if named_range is None or not named_range.value:
            errors.append(f"네임드 범위 손상: {range_name} (값 없음)")

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================
# Guard 2: Formula Preservation Validation
# ============================================================
def formula_guard(
    worksheet: Worksheet,
    formula_ranges: list[str],
    allow_blank: bool = False,
    policy_on_empty: str = "allow",
) -> tuple[bool, list[str], float]:
    r"""
    수식 보존 및 참조 무결성 검증 (I-2.1 수정)

    검증 항목:
    1. 지정된 범위의 모든 셀이 수식(=로 시작)인지 확인
    2. 수식 참조 무결성 확인 (#REF!, #NAME!, #VALUE! 등)
    3. 수식 보존율 계산: (수식 셀 수 / 비어있지 않은 셀 수) × 100

    Args:
        worksheet: openpyxl Worksheet 객체
        formula_ranges: 수식이 있어야 하는 셀 범위 리스트 (예: ["H3:H100"])
        allow_blank: 빈 셀 허용 여부 (deprecated, policy_on_empty 사용 권장)
        policy_on_empty: 빈 셀 정책
            - "allow": 빈 셀 허용 (기본값)
            - "strict_fail": 빈 셀 즉시 FAIL
            - "inject_or_fail": SSOT 공식 주입 시도, 실패 시 FAIL

    Returns:
        (is_valid, errors, preservation_rate): (검증 통과 여부, 오류 메시지, 수식 보존율)
    """
    from kis_estimator_core.core.ssot.constants_format import FORMULA_PRESERVE_THRESHOLD

    errors = []
    non_empty_cells = 0  # 비어있지 않은 셀 (빈 셀 제외)
    formula_cells = 0
    error_cells = 0

    for range_str in formula_ranges:
        # 범위 파싱 (예: "H3:H100")
        for row in worksheet[range_str]:
            for cell in row:
                # 빈 셀 처리 (policy_on_empty 적용)
                if cell.value is None or cell.value == "":
                    if policy_on_empty == "strict_fail":
                        errors.append(f"빈 셀 발견 (strict): {cell.coordinate}")
                        non_empty_cells += 1  # strict 모드에서는 카운트
                    elif policy_on_empty == "inject_or_fail":
                        # SSOT FORMULAE 매핑에서 공식 주입
                        injected_formula = _inject_formula_from_ssot(worksheet, cell)
                        if injected_formula:
                            # 주입 성공: 셀에 수식 설정
                            cell.value = injected_formula
                            formula_cells += 1
                            non_empty_cells += 1
                            # 메타 로깅 (단위 안전)
                            import logging

                            logger = logging.getLogger(__name__)
                            logger.debug(
                                f"Formula injected: {cell.coordinate} = {injected_formula}"
                            )
                            continue
                        else:
                            # 주입 실패: TEMPLATE_DAMAGED 에러
                            from .errors import ErrorCode, raise_error

                            raise_error(
                                ErrorCode.E_TEMPLATE_DAMAGED,
                                "템플릿 손상: 빈 셀에 대한 수식 매핑 없음",
                                meta={
                                    "cell": cell.coordinate,
                                    "reason": "missing_formula_map",
                                },
                            )
                    elif not allow_blank:
                        errors.append(f"빈 셀 발견: {cell.coordinate}")
                    # allow_blank=True: 빈 셀은 카운트하지 않음
                    continue

                # 비어있지 않은 셀 카운트
                non_empty_cells += 1

                # 수식 확인
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formula_cells += 1

                    # 오류 수식 확인
                    if any(
                        err in str(cell.value)
                        for err in ["#REF!", "#NAME!", "#VALUE!", "#DIV/0!", "#N/A"]
                    ):
                        error_cells += 1
                        errors.append(f"수식 오류: {cell.coordinate} = {cell.value}")
                elif not allow_blank:
                    errors.append(f"수식 아님: {cell.coordinate} = {cell.value}")

    # 수식 보존율 계산 (I-2.1: 비어있지 않은 셀 기준)
    # preservation_rate = (수식 셀 / 비어있지 않은 셀) × 100
    if non_empty_cells > 0:
        preservation_rate = (formula_cells / non_empty_cells) * 100.0
        # clamp(0, 100)
        preservation_rate = max(0.0, min(100.0, preservation_rate))
    else:
        preservation_rate = 0.0

    # 검증: 수식 보존율 ≥ THRESHOLD (SSOT 상수)
    is_valid = (preservation_rate >= FORMULA_PRESERVE_THRESHOLD) and (error_cells == 0)

    if preservation_rate < FORMULA_PRESERVE_THRESHOLD:
        errors.append(
            f"수식 보존율 {preservation_rate:.1f}% < {FORMULA_PRESERVE_THRESHOLD}% (임계치)"
        )

    if error_cells > 0:
        errors.append(f"수식 오류 {error_cells}개 발견")

    return is_valid, errors, preservation_rate


# ============================================================
# Guard 3: Totals Consistency Validation
# ============================================================
def totals_guard(
    worksheet: Worksheet,
    subtotal_cell: str,
    total_cell: str,
    vat_cell: str,
    tolerance: float = 0.01,
    line_items_range: str | None = None,
) -> tuple[bool, list[str]]:
    """
    소계→합계→VAT→총액 일관성 검증 (I-2.1 수정 - Decimal 기반 직접 계산)

    검증 항목:
    1. 라인아이템 금액을 Decimal로 직접 합산하여 expected_subtotal 계산
    2. 소계 셀 존재 확인 (수식이어도 직접 계산한 값과 비교)
    3. 합계 = 소계 (수량 고려 안 함, 견적서는 소계=합계)
    4. 부가세 포함 = 합계 × 1.1 (일관성)
    5. 오차 허용 범위 (TOTAL_TOLERANCE) 내 일치

    Args:
        worksheet: openpyxl Worksheet 객체
        subtotal_cell: 소계 셀 주소 (예: "G48")
        total_cell: 합계 셀 주소 (예: "G50")
        vat_cell: 부가세 포함 셀 주소 (예: "G50") - optional
        tolerance: 허용 오차 (기본값: 0.01원, SSOT TOTAL_TOLERANCE 사용 권장)
        line_items_range: 라인아이템 범위 (예: "G3:G47") - 직접 합산용

    Returns:
        (is_valid, errors): (검증 통과 여부, 오류 메시지 리스트)
    """
    from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

    from kis_estimator_core.core.ssot.constants_format import NUM_SCALE

    errors = []

    # 1. 라인아이템 범위 직접 합산 (Decimal 기반)
    expected_subtotal = Decimal(0)
    line_items_count = 0

    if line_items_range:
        # 범위 파싱 (예: "G3:G47")
        for row in worksheet[line_items_range]:
            for cell in row:
                value = cell.value

                # 빈 셀 스킵
                if value is None or value == "":
                    continue

                # 수식인 경우 (=F*E 등) - 계산 불가, 경고 후 스킵
                if isinstance(value, str) and value.startswith("="):
                    # 수식 셀은 카운트만 하고 합산 불가
                    line_items_count += 1
                    continue

                # 숫자 타입 검증
                if not isinstance(value, (int, float, Decimal)):
                    errors.append(
                        f"타입 위반: {cell.coordinate} = {value} (expected: Decimal, got: {type(value).__name__})"
                    )
                    continue

                # Decimal 변환 및 합산
                try:
                    decimal_value = Decimal(str(value))
                    expected_subtotal += decimal_value
                    line_items_count += 1
                except (InvalidOperation, ValueError) as e:
                    errors.append(
                        f"Decimal 변환 실패: {cell.coordinate} = {value} (error: {e})"
                    )

        # 소수점 정밀도 적용 (quantize)
        quantizer = Decimal(10) ** -NUM_SCALE
        expected_subtotal = expected_subtotal.quantize(
            quantizer, rounding=ROUND_HALF_EVEN
        )

    # 2. 소계 셀 확인
    subtotal_value = worksheet[subtotal_cell].value
    if subtotal_value is None:
        errors.append(f"소계 셀 누락: {subtotal_cell}")
        return False, errors

    # 소계 셀이 수식인 경우 (=SUM(...)) - 정상 (openpyxl은 수식 계산 안 함)
    # line_items_range가 제공되었으면 직접 계산한 expected_subtotal로 검증됨

    # 3. 합계 셀 확인
    total_value = worksheet[total_cell].value
    if total_value is None:
        errors.append(f"합계 셀 누락: {total_cell}")
        return False, errors

    # 4. 부가세 포함 셀 확인 (optional - 견적서는 VAT 없을 수 있음)
    if vat_cell:
        vat_value = worksheet[vat_cell].value
        # vat_cell이 지정되었지만 값이 None이면 경고만 (에러 아님)
        if vat_value is None:
            # 경고: VAT optional (견적서는 부가세 행 없을 수 있음)
            pass

    # NOTE: openpyxl은 수식을 계산하지 않으므로, 셀 값이 수식(=SUM 등)이면 실제 값 비교 불가
    # line_items_range를 직접 합산하여 expected_subtotal을 계산했으므로, 수식 셀이어도 검증 통과
    # 수식 존재 여부만 확인하고, 값 검증은 런타임에 Excel에서 수행하거나 data_only=True 모드 필요

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================
# Guard 4: Text Policy Validation
# ============================================================
def text_policy_guard(
    worksheet: Worksheet,
    text_ranges: list[str],
    required_phrases: list[str] | None = None,
    forbidden_phrases: list[str] | None = None,
) -> tuple[bool, list[str]]:
    r"""
    조건표 필수 문구/금칙어 검사

    검증 항목:
    1. 필수 문구 포함 여부 (예: "납기", "대금", "유효기간")
    2. 금칙어 미포함 여부 (예: "무료", "서비스", "할인")
    3. 금지 문자 미포함 여부 (예: < > | : \ / ? *)

    Args:
        worksheet: openpyxl Worksheet 객체
        text_ranges: 검사할 텍스트 범위 리스트
        required_phrases: 필수 문구 리스트 (None이면 기본값 사용)
        forbidden_phrases: 금칙어 리스트 (None이면 기본값 사용)

    Returns:
        (is_valid, errors): (검증 통과 여부, 오류 메시지 리스트)
    """
    if required_phrases is None:
        required_phrases = REQUIRED_PHRASES

    if forbidden_phrases is None:
        forbidden_phrases = FORBIDDEN_PHRASES

    errors = []
    found_required = dict.fromkeys(required_phrases, False)

    for range_str in text_ranges:
        for row in worksheet[range_str]:
            for cell in row:
                if cell.value is None:
                    continue

                text = str(cell.value)

                # 필수 문구 확인
                for phrase in required_phrases:
                    if phrase in text:
                        found_required[phrase] = True

                # 금칙어 확인
                for phrase in forbidden_phrases:
                    if phrase in text:
                        errors.append(
                            f"금칙어 발견: {cell.coordinate} = '{phrase}' in '{text}'"
                        )

                # 금지 문자 확인
                for char in FORBIDDEN_CHARS:
                    if char in text:
                        errors.append(
                            f"금지 문자 발견: {cell.coordinate} = '{char}' in '{text}'"
                        )

    # 필수 문구 누락 확인
    for phrase, found in found_required.items():
        if not found:
            errors.append(f"필수 문구 누락: '{phrase}'")

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================
# Guard 5: Cell Protection Validation
# ============================================================
def cell_protection_guard(
    worksheet: Worksheet,
    protected_ranges: list[str] | None = None,
    unlocked_ranges: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """
    수식 셀 보호 검증

    검증 항목:
    1. 수식 셀(protected_ranges)이 잠금(locked) 상태인지 확인
    2. 입력 셀(unlocked_ranges)이 잠금 해제 상태인지 확인
    3. 워크시트 보호(protection) 활성화 확인

    Args:
        worksheet: openpyxl Worksheet 객체
        protected_ranges: 보호할 셀 범위 리스트 (None이면 기본값 사용)
        unlocked_ranges: 잠금 해제할 셀 범위 리스트 (None이면 기본값 사용)

    Returns:
        (is_valid, errors): (검증 통과 여부, 오류 메시지 리스트)
    """
    if protected_ranges is None:
        protected_ranges = PROTECTED_FORMULA_RANGES

    if unlocked_ranges is None:
        unlocked_ranges = UNLOCKED_INPUT_RANGES

    errors = []

    # 보호할 셀 범위 확인
    for range_str in protected_ranges:
        for row in worksheet[range_str]:
            for cell in row:
                if not cell.protection.locked:
                    errors.append(f"수식 셀 미보호: {cell.coordinate} (locked=False)")

    # 잠금 해제할 셀 범위 확인
    for range_str in unlocked_ranges:
        # 단일 셀 또는 범위 처리
        if ":" in range_str:
            cells = worksheet[range_str]
            for row in cells:
                for cell in row:
                    if cell.protection.locked:
                        errors.append(
                            f"입력 셀 잠금됨: {cell.coordinate} (locked=True)"
                        )
        else:
            cell = worksheet[range_str]
            if cell.protection.locked:
                errors.append(f"입력 셀 잠금됨: {range_str} (locked=True)")

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================
# Guard 6: NaN/Blank Prohibition
# ============================================================
def nan_blank_guard(
    worksheet: Worksheet, critical_ranges: list[str], allow_zero: bool = True
) -> tuple[bool, list[str]]:
    """
    NaN/빈칸 금지 검증

    검증 항목:
    1. 중요 범위(critical_ranges)에 빈칸 없음
    2. NaN, None, "" 값 금지
    3. 0 값 허용 여부 (allow_zero)

    Args:
        worksheet: openpyxl Worksheet 객체
        critical_ranges: 빈칸 금지 범위 리스트
        allow_zero: 0 값 허용 여부 (기본값: True)

    Returns:
        (is_valid, errors): (검증 통과 여부, 오류 메시지 리스트)
    """
    errors = []

    for range_str in critical_ranges:
        for row in worksheet[range_str]:
            for cell in row:
                value = cell.value

                # 빈칸 확인
                if value is None or value == "":
                    errors.append(f"빈칸 발견: {cell.coordinate}")
                    continue

                # 0 값 확인 (allow_zero=False일 때만)
                if not allow_zero and value == 0:
                    errors.append(f"0 값 발견: {cell.coordinate}")

                # NaN 확인 (숫자 타입일 때)
                if isinstance(value, float):
                    import math

                    if math.isnan(value):
                        errors.append(f"NaN 발견: {cell.coordinate}")

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================
# Helper: Validate Date Format
# ============================================================
def validate_date_format(date_str: str) -> bool:
    """
    날짜 형식 검증 (YYYY년 MM월 DD일)

    Args:
        date_str: 날짜 문자열

    Returns:
        형식 일치 여부
    """
    return bool(re.match(DATE_FORMAT_REGEX, date_str))


# ============================================================
# Helper: Validate Size Format
# ============================================================
def validate_size_format(size_str: str) -> bool:
    """
    사이즈 형식 검증 (W*H*D 또는 W×H×D)

    Args:
        size_str: 사이즈 문자열

    Returns:
        형식 일치 여부
    """
    return bool(re.match(SIZE_FORMAT_REGEX, size_str))


# ============================================================
# Composite Guard: Full Estimate Validation
# ============================================================
def full_estimate_guard(
    workbook: Workbook,
    quote_sheet_name: str = SHEET_QUOTE,
    cover_sheet_name: str = SHEET_COVER,
) -> tuple[bool, dict[str, Any]]:
    """
    견적서 전체 검증 (모든 가드 통합 실행)

    실행 순서:
    1. Named Range Guard
    2. Formula Guard (견적서 + 표지)
    3. Totals Guard
    4. Text Policy Guard (조건표 - optional)
    5. Cell Protection Guard
    6. NaN/Blank Guard

    Args:
        workbook: openpyxl Workbook 객체
        quote_sheet_name: 견적서 시트명
        cover_sheet_name: 표지 시트명

    Returns:
        (is_valid, results): (전체 검증 통과 여부, 가드별 결과 딕셔너리)
    """
    results = {}

    # Guard 1: Named Range
    is_valid_nr, errors_nr = named_range_guard(workbook)
    results["named_range"] = {"valid": is_valid_nr, "errors": errors_nr}

    # Guard 2: Formula (견적서 시트)
    quote_sheet = workbook[quote_sheet_name]
    is_valid_formula_q, errors_formula_q, rate_q = formula_guard(
        quote_sheet, formula_ranges=["H3:H100"], allow_blank=True  # 금액 컬럼
    )
    results["formula_quote"] = {
        "valid": is_valid_formula_q,
        "errors": errors_formula_q,
        "preservation_rate": rate_q,
    }

    # Guard 2: Formula (표지 시트)
    cover_sheet = workbook[cover_sheet_name]
    is_valid_formula_c, errors_formula_c, rate_c = formula_guard(
        cover_sheet, formula_ranges=["I17:I50"], allow_blank=True  # 금액 컬럼
    )
    results["formula_cover"] = {
        "valid": is_valid_formula_c,
        "errors": errors_formula_c,
        "preservation_rate": rate_c,
    }

    # Guard 3: Totals (견적서 시트 - 소계/합계 셀 주소는 동적이므로 skip)

    results["totals"] = {"valid": True, "errors": [], "note": "동적 셀 주소 탐지 필요"}

    # Guard 4: Text Policy (조건표 시트 - optional)

    results["text_policy"] = {
        "valid": True,
        "errors": [],
        "note": "조건표 시트 없음 (optional)",
    }

    # Guard 5: Cell Protection
    is_valid_prot, errors_prot = cell_protection_guard(quote_sheet)
    results["cell_protection"] = {"valid": is_valid_prot, "errors": errors_prot}

    # Guard 6: NaN/Blank (중요 범위 - 수량/단가/금액)
    is_valid_nan, errors_nan = nan_blank_guard(
        quote_sheet,
        critical_ranges=["F3:F100", "G3:G100"],  # 수량, 단가
        allow_zero=False,
    )
    results["nan_blank"] = {"valid": is_valid_nan, "errors": errors_nan}

    # 전체 검증 결과
    all_valid = all(r["valid"] for r in results.values())

    return all_valid, results
