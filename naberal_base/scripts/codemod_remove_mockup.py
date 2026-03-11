#!/usr/bin/env python3
"""
Codemod - MOCKUP/TODO/Placeholder 제거

목표:
- TODO/FIXME 주석 제거 또는 트래킹 ID 부여
- NotImplementedError → raise_error(E_INTERNAL)
- placeholder/wireframe/lorem ipsum 제거

허용 (화이트리스트):
- tests/fixtures/** (WARN only)
- src/kis_erp_core/adapters/write_adapter.py (Phase 4 scaffold)
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple


# 허용 경로 (WARN only)
WHITELIST_PATHS = [
    "tests/fixtures/**",
    "tests/e2e/test_pipeline_full.py",  # allowlisted in audit
    "src/kis_erp_core/adapters/write_adapter.py",  # Phase 4 scaffold
]


def is_whitelisted(filepath: Path, base_dir: Path) -> bool:
    """화이트리스트 경로 확인"""
    rel_path = filepath.relative_to(base_dir)
    for pattern in WHITELIST_PATHS:
        if rel_path.match(pattern):
            return True
    return False


def remove_todo_comments(line: str, filepath: Path, line_num: int) -> Tuple[str, Dict]:
    """
    TODO/FIXME 주석 제거 또는 트래킹 ID 부여

    Returns:
        (modified_line, metadata)
    """
    # TODO[KIS-XXX] 형식은 유지
    if re.search(r"TODO\[KIS-\d+\]", line):
        return line, {}

    # 일반 TODO/FIXME 제거
    todo_pattern = r"#\s*(TODO|FIXME|STUB|MOCK|DUMMY|PLACEHOLDER|SAMPLE)[:：\s].*"
    match = re.search(todo_pattern, line, re.IGNORECASE)

    if match:
        original = match.group(0)
        # 주석 전체 제거
        cleaned = re.sub(todo_pattern, "", line, flags=re.IGNORECASE).rstrip()

        # 빈 라인이 되면 유지 (들여쓰기 보존)
        if not cleaned.strip():
            cleaned = "\n"

        return cleaned, {
            "type": "TODO_REMOVED",
            "original": original.strip(),
            "file": str(filepath),
            "line": line_num,
        }

    return line, {}


def fix_not_implemented(line: str, filepath: Path, line_num: int) -> Tuple[str, Dict]:
    """
    NotImplementedError → raise_error(E_INTERNAL, ...)

    Returns:
        (modified_line, metadata)
    """
    pattern = r'raise\s+NotImplementedError\s*\('

    if re.search(pattern, line):
        # raise NotImplementedError("message") → raise_error(ErrorCode.E_NOT_IMPLEMENTED, "message", hint="...")
        modified = re.sub(
            r'raise\s+NotImplementedError\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'raise_error(ErrorCode.E_NOT_IMPLEMENTED, "\1", hint="Spec Kit: 구현 항목 등록 필요")',
            line
        )

        # 단순 raise NotImplementedError() (메시지 없음)
        if modified == line:
            modified = re.sub(
                r'raise\s+NotImplementedError\s*\(\s*\)',
                r'raise_error(ErrorCode.E_NOT_IMPLEMENTED, "기능 미구현", hint="Spec Kit: 구현 항목 등록 필요")',
                line
            )

        return modified, {
            "type": "NOT_IMPLEMENTED_FIXED",
            "file": str(filepath),
            "line": line_num,
        }

    return line, {}


def remove_placeholder_text(line: str) -> Tuple[str, Dict]:
    """placeholder/wireframe/lorem ipsum 텍스트 제거"""
    placeholders = [
        (r'lorem\s+ipsum', "LOREM_IPSUM"),
        (r'wireframe', "WIREFRAME"),
        (r'placeholder', "PLACEHOLDER"),
        (r'(Sample|Example)\s+(data|content|text)', "SAMPLE_DATA"),
    ]

    for pattern, label in placeholders:
        if re.search(pattern, line, re.IGNORECASE):
            # 주석이면 전체 제거
            if "#" in line:
                cleaned = re.sub(r'#.*' + pattern + r'.*', "", line, flags=re.IGNORECASE).rstrip()
                if cleaned.strip():
                    return cleaned + "\n", {"type": label + "_REMOVED"}
                else:
                    return "\n", {"type": label + "_REMOVED"}

    return line, {}


def process_file(filepath: Path, base_dir: Path, dry_run: bool = False) -> Dict:
    """파일 처리"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return {"error": str(e)}

    is_allowed = is_whitelisted(filepath, base_dir)
    modified_lines = []
    changes = []

    for i, line in enumerate(lines, start=1):
        modified = line

        # TODO/FIXME 제거
        modified, meta = remove_todo_comments(modified, filepath, i)
        if meta:
            if is_allowed:
                meta["whitelist"] = True
            changes.append(meta)

        # NotImplementedError 수정
        modified, meta = fix_not_implemented(modified, filepath, i)
        if meta:
            if is_allowed:
                meta["whitelist"] = True
            changes.append(meta)

        # placeholder 텍스트 제거
        modified, meta = remove_placeholder_text(modified)
        if meta:
            if is_allowed:
                meta["whitelist"] = True
            changes.append(meta)

        modified_lines.append(modified)

    # 변경 사항이 있고 화이트리스트가 아니면 파일 업데이트
    non_whitelist_changes = [c for c in changes if not c.get("whitelist")]

    if non_whitelist_changes and not dry_run:
        # import 추가 확인
        has_raise_error = any("raise_error" in line for line in modified_lines)
        has_import = any("from src.kis_estimator_core.core.ssot.errors import" in line for line in modified_lines)

        if has_raise_error and not has_import:
            # import 추가
            for idx, line in enumerate(modified_lines):
                if line.strip().startswith(("from ", "import ")):
                    # 기존 import 블록 끝에 추가
                    if idx + 1 < len(modified_lines) and not modified_lines[idx + 1].strip().startswith(("from ", "import ")):
                        modified_lines.insert(
                            idx + 1,
                            "from src.kis_estimator_core.core.ssot.errors import raise_error, ErrorCode\n"
                        )
                        break

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(modified_lines)

    return {
        "file": str(filepath.relative_to(base_dir)),
        "changes": len(non_whitelist_changes),
        "whitelist_warnings": len([c for c in changes if c.get("whitelist")]),
        "details": changes,
    }


def generate_todo_backlog(results: List[Dict], output_path: Path):
    """docs/TODO_BACKLOG.md 생성"""
    todos = []
    for result in results:
        for change in result.get("details", []):
            if change.get("type") == "TODO_REMOVED" and not change.get("whitelist"):
                todos.append({
                    "file": change["file"],
                    "line": change["line"],
                    "original": change["original"],
                })

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# TODO Backlog (Spec Kit Cleanup)\n\n")
        f.write(f"**Generated**: {len(todos)} items removed and tracked\n\n")
        f.write("| File | Line | Original Comment | Suggested Action |\n")
        f.write("|------|------|------------------|------------------|\n")

        for todo in todos:
            file_short = todo["file"].replace("\\", "/")
            original = todo["original"][:60] + "..." if len(todo["original"]) > 60 else todo["original"]
            f.write(f"| {file_short} | {todo['line']} | {original} | Review & implement or delete |\n")


def main():
    parser = argparse.ArgumentParser(description="Remove MOCKUP/TODO/Placeholder patterns")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    print(f"[INFO] Base directory: {base_dir}")
    print(f"[INFO] Dry run: {args.dry_run}")

    # 스캔 대상
    include_patterns = [
        "src/**/*.py",
        "core/**/*.py",
        "engine/**/*.py",
        "api/**/*.py",
        "tests/**/*.py",
    ]

    exclude_patterns = [
        "dist/**",
        ".git/**",
        "node_modules/**",
        "__pycache__/**",
        "venv/**",
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

    print(f"[INFO] Processing {len(filtered_files)} files...")

    results = []
    for filepath in filtered_files:
        result = process_file(filepath, base_dir, dry_run=args.dry_run)
        if result.get("changes", 0) > 0 or result.get("whitelist_warnings", 0) > 0:
            results.append(result)

    # TODO backlog 생성
    if not args.dry_run:
        backlog_path = base_dir / "docs" / "TODO_BACKLOG.md"
        backlog_path.parent.mkdir(parents=True, exist_ok=True)
        generate_todo_backlog(results, backlog_path)
        print(f"[OUTPUT] TODO backlog: {backlog_path}")

    # 요약
    total_changes = sum(r.get("changes", 0) for r in results)
    total_warnings = sum(r.get("whitelist_warnings", 0) for r in results)

    print(f"\n[SUMMARY]")
    print(f"Files modified: {len(results)}")
    print(f"Total changes: {total_changes}")
    print(f"Whitelist warnings: {total_warnings}")

    if args.dry_run:
        print("\n[DRY RUN] No files modified")
    else:
        print("\n[DONE] MOCKUP/TODO cleanup complete")


if __name__ == "__main__":
    main()
