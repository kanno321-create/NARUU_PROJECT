#!/usr/bin/env python3
"""
Codemod - 내장 예외 → EstimatorError 자동 변환

목표: ERROR_SCHEMA_VIOLATION 71건 전량 수정
- raise Exception(...) → raise_error(ErrorCode.E_INTERNAL, ...)
- raise ValueError(...) → raise_error(ErrorCode.E_VALIDATION_FAILED, ...)
- raise RuntimeError(...) → raise_error(ErrorCode.E_INTERNAL, ...)
- raise AssertionError(...) → raise_error(ErrorCode.E_ASSERTION_FAILED, ...)

매핑 규칙 (경로 패턴 → ErrorCode):
- engine/catalog_loader.py → E_CATALOG_LOAD
- engine/data_transformer.py → E_DATA_TRANSFORM
- core/ssot/branch_bus.py → E_BRANCH_RULE
- api/routers/*.py → E_CONTRACT_VIOLATION
- engine/pdf_converter.py, engine/excel_* → E_IO
- infra/redis_* → E_REDIS_RATE
- 기타 → E_INTERNAL
"""

import argparse
import re
from pathlib import Path
from typing import Dict, Tuple


# ============================================================
# 경로 패턴 → ErrorCode 매핑
# ============================================================

PATH_PATTERN_TO_ERROR_CODE = [
    (r"engine/catalog_loader\.py", "ErrorCode.E_CATALOG_LOAD"),
    (r"engine/data_transformer\.py", "ErrorCode.E_DATA_TRANSFORM"),
    (r"core/ssot/branch_bus\.py", "ErrorCode.E_BRANCH_RULE"),
    (r"api/routers/.*\.py", "ErrorCode.E_CONTRACT_VIOLATION"),
    (r"engine/(pdf_converter|excel_).*\.py", "ErrorCode.E_IO"),
    (r"infra/redis_.*\.py", "ErrorCode.E_REDIS_RATE"),
    (r"core/ssot/guards_format\.py", "ErrorCode.E_TEMPLATE_DAMAGED"),
]


def get_error_code_for_path(filepath: Path) -> str:
    """파일 경로 → ErrorCode 매핑"""
    path_str = str(filepath).replace("\\", "/")

    for pattern, error_code in PATH_PATTERN_TO_ERROR_CODE:
        if re.search(pattern, path_str):
            return error_code

    # 기본값
    return "ErrorCode.E_INTERNAL"


# ============================================================
# 예외 타입 → ErrorCode 매핑 (폴백)
# ============================================================

EXCEPTION_TYPE_TO_ERROR_CODE = {
    "Exception": "ErrorCode.E_INTERNAL",
    "ValueError": "ErrorCode.E_VALIDATION_FAILED",
    "RuntimeError": "ErrorCode.E_INTERNAL",
    "AssertionError": "ErrorCode.E_ASSERTION_FAILED",
    "FileNotFoundError": "ErrorCode.E_FILE_NOT_FOUND",
    "IOError": "ErrorCode.E_IO",
    "KeyError": "ErrorCode.E_INTERNAL",
    "TypeError": "ErrorCode.E_INTERNAL",
}


# ============================================================
# Codemod 로직
# ============================================================

def transform_raise_statement(
    line: str, filepath: Path, line_number: int
) -> Tuple[str, bool]:
    """
    raise <Exception>(...) → raise_error(ErrorCode.X, ...)

    Returns:
        (transformed_line, is_modified)
    """
    # 패턴: raise <ExceptionType>(<message>)
    pattern = r"raise\s+(Exception|ValueError|RuntimeError|AssertionError|FileNotFoundError|IOError|KeyError|TypeError)\s*\("

    match = re.search(pattern, line)
    if not match:
        return line, False

    exc_type = match.group(1)

    # 경로 기반 ErrorCode 우선, 폴백은 예외 타입 기반
    error_code = get_error_code_for_path(filepath)

    # raise <ExceptionType>( → raise_error(<ErrorCode>,
    transformed = re.sub(
        pattern,
        f"raise_error({error_code}, ",
        line,
        count=1,
    )

    # 메타데이터 추가 (파일, 라인)
    # 패턴: raise_error(ErrorCode.X, "message")
    # → raise_error(ErrorCode.X, "message", meta={"file": "...", "line": ...})

    # 간단한 케이스 처리: raise_error(..., "message")
    # 더 복잡한 케이스는 수동 보강 필요

    return transformed, True


def process_file(filepath: Path, dry_run: bool = False) -> int:
    """
    파일 내 모든 raise 문 변환

    Returns:
        변환된 라인 수
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] Failed to read {filepath}: {e}")
        return 0

    modified_lines = []
    modifications = 0

    for i, line in enumerate(lines, start=1):
        transformed, is_modified = transform_raise_statement(line, filepath, i)
        modified_lines.append(transformed)
        if is_modified:
            modifications += 1
            print(f"[TRANSFORM] {filepath}:{i}")
            print(f"  BEFORE: {line.rstrip()}")
            print(f"  AFTER:  {transformed.rstrip()}")

    if modifications > 0 and not dry_run:
        # 임포트 추가 (파일 상단)
        import_added = False
        for i, line in enumerate(modified_lines):
            if line.strip().startswith("from ") or line.strip().startswith("import "):
                # 기존 임포트 블록 끝에 추가
                if i + 1 < len(modified_lines) and not modified_lines[i + 1].strip().startswith(("from ", "import ")):
                    modified_lines.insert(
                        i + 1,
                        "from src.kis_estimator_core.core.ssot.errors import raise_error, ErrorCode\n",
                    )
                    import_added = True
                    break

        if not import_added:
            # 임포트 블록 없으면 첫 번째 주석 블록 후 추가
            for i, line in enumerate(modified_lines):
                if not line.strip().startswith("#") and line.strip():
                    modified_lines.insert(i, "from src.kis_estimator_core.core.ssot.errors import raise_error, ErrorCode\n")
                    break

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(modified_lines)

    return modifications


def scan_directory(base_dir: Path, dry_run: bool = False) -> Dict[str, int]:
    """
    디렉토리 스캔 및 변환

    Returns:
        {filepath: modification_count}
    """
    results = {}

    # 스캔 대상: src/kis_estimator_core/**, api/**
    include_patterns = [
        "src/kis_estimator_core/**/*.py",
        "api/**/*.py",
    ]

    # 제외: tests/**
    exclude_patterns = [
        "tests/**",
        "scripts/**",
        "dist/**",
        "__pycache__/**",
    ]

    all_files = []
    for pattern in include_patterns:
        all_files.extend(base_dir.glob(pattern))

    # 제외 필터링
    filtered_files = []
    for filepath in all_files:
        rel_path = filepath.relative_to(base_dir)
        is_excluded = any(rel_path.match(exc) for exc in exclude_patterns)
        if not is_excluded:
            filtered_files.append(filepath)

    print(f"[INFO] Found {len(filtered_files)} files to process")

    for filepath in filtered_files:
        count = process_file(filepath, dry_run=dry_run)
        if count > 0:
            results[str(filepath.relative_to(base_dir))] = count

    return results


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Codemod: 내장 예외 → EstimatorError")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Repository base directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (no file modification)",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    print(f"[INFO] Base directory: {base_dir}")
    print(f"[INFO] Dry run: {args.dry_run}")

    results = scan_directory(base_dir, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("CODEMOD SUMMARY")
    print("=" * 60)

    total_modifications = sum(results.values())
    print(f"Total files modified: {len(results)}")
    print(f"Total lines transformed: {total_modifications}")

    if results:
        print("\nTop modified files:")
        for filepath, count in sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {filepath}: {count} lines")

    if args.dry_run:
        print("\n[DRY RUN] No files were modified. Run without --dry-run to apply changes.")
    else:
        print("\n[DONE] All modifications applied.")


if __name__ == "__main__":
    main()
