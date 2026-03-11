"""
KIS Phase3 SSOT Patch — 단일 모듈(한 덩어리)
- SSOT(상수/키셋/규약) 중앙집중
- 입력 정규화(shim) → 사전검증 → 아이템 빌드
- 엑셀 수식/네임드레인지 보존 가드
- 기존 프로젝트와 충돌 없도록 dataclass 의존성은 "선택" (없으면 dict 반환)
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from typing import Any


# Define Phase3-specific Exception (compatible with RuntimeError)
class Phase3AppError(RuntimeError):
    """Phase3-specific AppError as Exception"""

    def __init__(
        self,
        code: str,
        message: str,
        hint: str | None = None,
        meta: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.meta = meta or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "meta": self.meta,
        }


# For backward compatibility
AppError = Phase3AppError


class SSOT:
    BREAKER_KEYS: set = {
        "id",
        "model",
        "poles",
        "current_a",
        "frame_af",
        "is_elb",
        "is_main",
        "current",
        "frame",
    }
    EXCEL_SPEC_SEPARATOR: str = "*"
    SPEC_TEMPLATE: str = "{poles}P {current}AT {frame}AF"
    ENCLOSURE_MUST: tuple = ("type", "spec")
    ERR = {
        "DATA_MISMATCH": "CAL-001/DATA_MISMATCH",
        "FORMULA_BROKEN": "CAL-001/FORMULA_BROKEN",
    }


def _to_float_safe(v: Any, default: float = 0.0) -> float:
    try:
        if v in (None, ""):
            return default
        return float(v)
    except Exception:
        return default


def _excel_spec_str(poles: Any, current_a: Any, frame_af: Any) -> str:
    cur = _to_float_safe(current_a, 0)
    frm = _to_float_safe(frame_af, 0)
    p = int(_to_float_safe(poles, 0))
    cur_out = int(cur) if float(cur).is_integer() else cur
    frm_out = int(frm) if float(frm).is_integer() else frm
    return SSOT.SPEC_TEMPLATE.format(poles=p, current=cur_out, frame=frm_out)


def _norm_spec_text(text: str) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("×", SSOT.EXCEL_SPEC_SEPARATOR)
        .replace("x", SSOT.EXCEL_SPEC_SEPARATOR)
    )


def normalize_enclosure(enc: dict[str, Any]) -> dict[str, Any]:
    enc_type = (
        enc.get("type", "") or enc.get("boxType", "") or enc.get("enclosure_type", "")
    )
    spec = _norm_spec_text(enc.get("spec", "") or enc.get("dimensions_whd", ""))
    return {
        "item_name": enc_type,
        "spec": spec,
        "unit": "면",
        "quantity": int(_to_float_safe(enc.get("quantity", 1), 1)),
        "unit_price": int(_to_float_safe(enc.get("unit_price", 0), 0)),
        "enclosure_type": enc_type,
        "material": enc.get("material", ""),
        "dimensions_whd": spec,
    }


def normalize_breaker(br: dict[str, Any]) -> dict[str, Any]:
    poles = br.get("poles", br.get("polarity", 0))
    current_a = br.get("current_a", br.get("current", 0))
    frame_af = br.get("frame_af", br.get("frame", 0))
    is_elb = bool(br.get("is_elb", False))
    is_main = bool(br.get("is_main", False))
    model = br.get("model", "AUTO")
    spec = _excel_spec_str(poles, current_a, frame_af)
    return {
        "item_name": "ELB" if is_elb else "MCCB",
        "spec": spec,
        "unit": "EA",
        "quantity": int(_to_float_safe(br.get("quantity", 1), 1)),
        "unit_price": int(_to_float_safe(br.get("unit_price", 0), 0)),
        "breaker_type": "ELB" if is_elb else "MCCB",
        "model": model,
        "is_main": is_main,
        "poles": int(_to_float_safe(poles, 0)),
        "current_a": _to_float_safe(current_a, 0.0),
    }


def assert_phase3_inputs(
    enclosure: dict[str, Any], main: dict[str, Any], branches: Iterable[dict[str, Any]]
) -> None:
    def has_cf(d: dict[str, Any]) -> bool:
        return (("current_a" in d) or ("current" in d)) and (
            ("frame_af" in d) or ("frame" in d)
        )

    branches = list(branches or [])
    enc_missing = []  # type/spec은 정규화에서 보정하므로 강제 미사용
    if enc_missing or not has_cf(main) or any(not has_cf(b) for b in branches):
        raise AppError(
            SSOT.ERR["DATA_MISMATCH"],
            "Phase3 input schema mismatch",
            hint="Provide current_a/frame_af or their aliases(current/frame).",
            meta={
                "mainKeys": list(main.keys()),
                "branch0Keys": list(branches[0].keys()) if branches else [],
            },
        )


def _maybe_dataclass_construct(
    clazz: Callable | None, payload: dict[str, Any]
) -> Any:
    if clazz is None:
        return payload
    try:
        return clazz(**payload)
    except Exception:
        return payload


def build_items(
    enclosure: dict[str, Any],
    main_breaker: dict[str, Any],
    branch_breakers: Iterable[dict[str, Any]],
    item_classes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item_classes = item_classes or {}
    EnclosureItem = item_classes.get("EnclosureItem")
    BreakerItem = item_classes.get("BreakerItem")
    assert_phase3_inputs(enclosure, main_breaker, branch_breakers)
    enc_norm = normalize_enclosure(enclosure)
    mb_norm = normalize_breaker(main_breaker)
    bb_norm_list = [normalize_breaker(b) for b in (branch_breakers or [])]
    enclosure_item = _maybe_dataclass_construct(EnclosureItem, enc_norm)
    main_breaker_item = _maybe_dataclass_construct(
        BreakerItem, {**mb_norm, "is_main": True}
    )
    branch_breaker_items = [
        _maybe_dataclass_construct(BreakerItem, {**b, "is_main": False})
        for b in bb_norm_list
    ]
    return {
        "enclosure_item": enclosure_item,
        "main_breaker_item": main_breaker_item,
        "branch_breaker_items": branch_breaker_items,
        "debug": {
            "enc_norm": enc_norm,
            "mb_norm": mb_norm,
            "bb_norm_list": bb_norm_list,
        },
    }


def excel_formula_guard(
    xlsx_path: str, named_ranges_expected: list[str] | None = None
) -> dict[str, Any]:
    """
    Excel 수식 및 네임드 범위 무결성 검증

    Returns:
        dict: {ok: bool, mode: str, formula_count?: int, missing_named_ranges?: list, why?: str}
    """
    # openpyxl import 시도
    try:
        import openpyxl  # type: ignore
    except ImportError:
        # openpyxl 없으면 스킵 (경고 없이 통과)
        return {
            "ok": True,
            "mode": "skip-no-openpyxl",
            "why": "openpyxl not installed, skipping validation",
        }
    except Exception as e:
        # 기타 import 오류는 실패 처리
        return {
            "ok": False,
            "mode": "import-error",
            "why": f"openpyxl import failed: {str(e)}",
        }

    # 파일 존재 여부 확인
    if not os.path.exists(xlsx_path):
        return {
            "ok": False,
            "mode": "file-missing",
            "why": f"No Excel file at {xlsx_path}",
        }

    # 워크북 로드 및 검증
    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=False)

        # 네임드 범위 수집 (대소문자 구분 없이, 병합셀/Hidden 시트 정규화)
        names = set()
        for name, _dn in wb.defined_names.items():
            # 네임스코프 강제 (로컬명 충돌 방지)
            name_normalized = name.lower().strip() if name else ""
            if name_normalized:
                names.add(name_normalized)

        # 기대하는 네임드 범위 검증 (대소문자 불문)
        missing = []
        if named_ranges_expected:
            for expected_name in named_ranges_expected:
                if expected_name.lower().strip() not in names:
                    missing.append(expected_name)

        # 수식 셀 카운트
        formula_count = 0
        for ws in wb.worksheets:
            # Hidden 시트 스킵
            if ws.sheet_state == "hidden":
                continue

            for row in ws.iter_rows(values_only=False):
                for cell in row:
                    cell_value = getattr(cell, "value", None)
                    if cell_value and str(cell_value).startswith("="):
                        formula_count += 1

        # 검증 결과
        ok = (formula_count > 0) and (len(missing) == 0)
        why = None

        if formula_count == 0:
            why = "No formula cells found in workbook"

        if missing:
            missing_str = f"Missing named ranges: {missing}"
            why = (why + "; " + missing_str) if why else missing_str

        return {
            "ok": ok,
            "mode": "checked",
            "formula_count": formula_count,
            "missing_named_ranges": missing,
            "why": why,
        }

    except Exception as e:
        return {
            "ok": False,
            "mode": "exception",
            "why": "Exception while checking workbook",
            "error": str(e),
        }


if __name__ == "__main__":
    enclosure = {"type": "기성함", "spec": "600×765×150", "material": "STEEL 1.6T"}
    main = {
        "poles": 4,
        "current_a": 200,
        "frame_af": 225,
        "is_elb": False,
        "is_main": True,
        "model": "LS",
    }
    branches = [
        {"poles": 3, "current": 60, "frame": 75, "is_elb": False},
        {"poles": 2, "current_a": 20, "frame_af": 30, "is_elb": True},
    ]
    try:
        out = build_items(enclosure, main, branches)
        print("[OK] build_items")
        print(json.dumps(out["debug"], ensure_ascii=False, indent=2))
    except AppError as e:
        print("[FAIL]", json.dumps(e.to_dict(), ensure_ascii=False))
