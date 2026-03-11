#!/usr/bin/env python3
"""
Spec Kit Compliance Audit - 목업/더미/빈파일/규정위반 자동 점검

절대 원칙:
- 목업/더미/스텁/샘플/플레이스홀더 파일/코드 금지
- 빈 파일(0 byte) 및 실질 빈 파일(<3 non-comment lines) 금지
- SSOT/LAW/AI금지6항 위반 감지
- UI 목업 패턴(와이어프레임/임시 자산) 금지

출력:
- findings.jsonl: 위반 사항 목록 (file, rule, line, snippet, sha256)
- report.md: 카테고리별 요약 + Top 10 위반
- EvidencePack_spec_kit_audit.zip: 증거팩 (report, findings, 의심 파일, 로그)
- SHA256SUMS.txt: 무결성 해시 업데이트

Exit Codes:
- 0: findings = 0 (PASS)
- 2: findings > 0 (FAIL)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


# ============================================================
# 규칙 정의 (Rule Definitions)
# ============================================================

# 1) 목업/더미 파일명 패턴
MOCKUP_FILENAME_PATTERNS = [
    r"mock",
    r"dummy",
    r"stub",
    r"sample",
    r"placeholder",
    r"temp[-_]",
    r"example",
    r"test[-_]data",
    r"fixture",  # tests/fixtures/** 제외됨 (별도 처리)
    r"fake",
    r"wireframe",
    r"prototype",
]

# 2) 목업/더미 코드 패턴
MOCKUP_CODE_PATTERNS = [
    r"#\s*(TODO|FIXME|STUB|MOCK|DUMMY|PLACEHOLDER|SAMPLE)",
    r"raise\s+NotImplementedError",
    r"pass\s*#.*mock",
    r"return\s+None\s*#.*stub",
    r"def\s+\w+\(.*\):\s*pass\s*$",  # 빈 함수
]

# 3) UI 목업 패턴 (CSS/HTML)
UI_MOCKUP_PATTERNS = [
    r"\.wireframe",
    r"\.placeholder-\w+",
    r"background:\s*#(ccc|ddd|eee);.*placeholder",
    r"lorem\s+ipsum",
    r"<!-- TODO: replace with real -->",
]

# 4) SSOT 위반: 잘못된 임포트 경로
SSOT_IMPORT_VIOLATIONS = [
    r"from\s+(?!src\.kis_estimator_core\.core\.ssot).*\s+import\s+(SHEET_QUOTE|SHEET_COVER|FORMULA_MAP_)",
]

# 5) 매직 리터럴 검출 (가격/단위/수식 키)
MAGIC_LITERAL_PATTERNS = [
    r"\d{3,}\s*\*\s*\d+",  # 큰 숫자 계산 (예: 20000*kg)
    r"['\"](?:EA|KG|M|면|식)['\"]",  # 하드코딩된 단위
]

# 6) 에러 스키마 위반 (AppError 잘못된 사용)
ERROR_SCHEMA_VIOLATIONS = [
    r"raise\s+Exception\(",  # 맨손 Exception
    r"raise\s+ValueError\(",  # 도메인 에러 아닌 ValueError
    r"raise\s+RuntimeError\(",  # 도메인 에러 아닌 RuntimeError
]

# Allowlist: 경고만 하고 FAIL 카운트 안 함
ALLOWLIST_PATHS = [
    "tests/fixtures/**",
    "tests/e2e/test_pipeline_full.py",  # 테스트 파일 자체는 예외
    "scripts/audit_spec_kit.py",  # 자기 자신
]

# MAGIC_LITERAL whitelist: SSOT 파일은 상수 정의 장소이므로 제외
MAGIC_LITERAL_WHITELIST = [
    "src/kis_estimator_core/core/ssot/**",  # SSOT 파일은 상수 정의 목적
]


# ============================================================
# 유틸리티 함수
# ============================================================

def sha256_file(filepath: Path) -> str:
    """파일의 SHA256 해시 계산"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def is_allowlisted(filepath: Path, base_dir: Path) -> bool:
    """Allowlist 경로 확인 (tests/fixtures/** 등)"""
    rel_path = filepath.relative_to(base_dir)
    for pattern in ALLOWLIST_PATHS:
        if rel_path.match(pattern):
            return True
    return False


def count_non_comment_lines(filepath: Path) -> int:
    """코드 파일의 실질 라인 수 계산 (주석/공백 제외)"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return 0

    count = 0
    in_multiline_comment = False
    for line in lines:
        stripped = line.strip()
        # Python 멀티라인 주석 처리
        if '"""' in stripped or "'''" in stripped:
            in_multiline_comment = not in_multiline_comment
            continue
        if in_multiline_comment:
            continue
        # 주석 및 공백 제외
        if not stripped or stripped.startswith("#"):
            continue
        count += 1
    return count


def detect_shared_dup(files: List[Path], base_dir: Path) -> List[Dict]:
    """공유 중복 감지: 동일 함수명/상수명이 2개 이상 파일에 존재"""
    symbol_locations = defaultdict(list)
    findings = []

    # Python 키워드 및 1-2글자 심볼 제외
    EXCLUDED_SYMBOLS = {"def", "class", "if", "for", "import", "from", "return", "yield", "async", "await"}

    for filepath in files:
        if filepath.suffix not in [".py"]:
            continue

        # old_engine 디렉토리 제외 (레거시 중복 허용)
        if "old_engine" in str(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # 함수/클래스/상수 정의 추출
        for match in re.finditer(r"^(def|class|[A-Z_]+\s*=)", content, re.MULTILINE):
            symbol = match.group(0).split()[0]

            # 제외 조건
            if symbol in EXCLUDED_SYMBOLS:
                continue
            if len(symbol) <= 2:  # 1-2글자 심볼 제외
                continue

            symbol_locations[symbol].append(str(filepath.relative_to(base_dir)))

    # 2개 이상 위치에 존재하는 심볼
    for symbol, locations in symbol_locations.items():
        unique_locations = list(set(locations))

        # tests/** 내부 중복은 허용 (테스트 상수)
        if all("tests" in loc for loc in unique_locations):
            continue

        if len(unique_locations) >= 2:
            findings.append({
                "rule": "SHARED_DUP",
                "symbol": symbol,
                "locations": unique_locations,
                "count": len(unique_locations),
            })

    return findings


def detect_magic_literals(filepath: Path, base_dir: Path) -> List[Dict]:
    """매직 리터럴 감지: 하드코딩된 가격/단위/수식 키 (≥2회 사용)"""
    findings = []

    # MAGIC_LITERAL_WHITELIST 체크 (SSOT 파일 제외)
    rel_path = filepath.relative_to(base_dir)
    for pattern in MAGIC_LITERAL_WHITELIST:
        if rel_path.match(pattern):
            return findings  # SSOT 파일은 스킵

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return findings

    # 패턴별 출현 횟수 카운트
    literal_counts = defaultdict(int)
    for pattern in MAGIC_LITERAL_PATTERNS:
        for match in re.finditer(pattern, content):
            literal_counts[match.group(0)] += 1

    # 2회 이상 사용된 리터럴
    for literal, count in literal_counts.items():
        if count >= 2:
            findings.append({
                "file": str(filepath.relative_to(base_dir)),
                "rule": "MAGIC_LITERAL",
                "literal": literal,
                "count": count,
                "snippet": literal,
                "sha256": sha256_file(filepath),
            })

    return findings


# ============================================================
# 메인 스캔 로직
# ============================================================

def scan_repository(base_dir: Path) -> Tuple[List[Dict], List[str]]:
    """저장소 전체 스캔 - 규칙별 위반 사항 검출"""
    findings = []
    warnings = []

    # 포함 디렉토리
    include_dirs = ["src", "core", "engine", "api", "tests"]
    # 제외 디렉토리
    exclude_dirs = ["dist", ".git", "node_modules", "__pycache__", ".venv", "venv", "build"]

    # 파일 목록 수집
    all_files = []
    for include_dir in include_dirs:
        dir_path = base_dir / include_dir
        if not dir_path.exists():
            continue
        for root, dirs, files in os.walk(dir_path):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                filepath = Path(root) / file
                all_files.append(filepath)

    # 1) 빈 파일 검사 (0 byte or <3 non-comment lines)
    for filepath in all_files:
        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        # 0 byte 파일
        if filepath.stat().st_size == 0:
            finding = {
                "file": str(rel_path),
                "rule": "BLANK_FILE_ZERO_BYTE",
                "line": 0,
                "snippet": "(empty file)",
                "sha256": sha256_file(filepath),
            }
            if is_allowed:
                warnings.append(f"[WARN] {rel_path}: BLANK_FILE_ZERO_BYTE (allowlisted)")
            else:
                findings.append(finding)
            continue

        # 코드 파일 실질 빈 파일 검사 (<3 non-comment lines)
        if filepath.suffix in [".py", ".js", ".ts", ".jsx", ".tsx"]:
            non_comment_lines = count_non_comment_lines(filepath)
            if non_comment_lines < 3:
                finding = {
                    "file": str(rel_path),
                    "rule": "BLANK_FILE_INSUFFICIENT_CODE",
                    "line": 0,
                    "snippet": f"(only {non_comment_lines} non-comment lines)",
                    "sha256": sha256_file(filepath),
                }
                if is_allowed:
                    warnings.append(f"[WARN] {rel_path}: BLANK_FILE_INSUFFICIENT_CODE (allowlisted)")
                else:
                    findings.append(finding)

    # 2) 목업/더미 파일명 패턴
    for filepath in all_files:
        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        for pattern in MOCKUP_FILENAME_PATTERNS:
            if re.search(pattern, filepath.name, re.IGNORECASE):
                finding = {
                    "file": str(rel_path),
                    "rule": "MOCKUP_FILENAME",
                    "line": 0,
                    "snippet": f"filename matches '{pattern}'",
                    "sha256": sha256_file(filepath),
                }
                if is_allowed:
                    warnings.append(f"[WARN] {rel_path}: MOCKUP_FILENAME (allowlisted)")
                else:
                    findings.append(finding)
                break  # 첫 번째 패턴만 기록

    # 3) 목업/더미 코드 패턴
    for filepath in all_files:
        if filepath.suffix not in [".py", ".js", ".ts", ".jsx", ".tsx"]:
            continue

        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines, start=1):
            for pattern in MOCKUP_CODE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    finding = {
                        "file": str(rel_path),
                        "rule": "MOCKUP_CODE",
                        "line": i,
                        "snippet": line.strip()[:100],
                        "sha256": sha256_file(filepath),
                    }
                    if is_allowed:
                        warnings.append(f"[WARN] {rel_path}:{i}: MOCKUP_CODE (allowlisted)")
                    else:
                        findings.append(finding)
                    break  # 첫 번째 패턴만 기록

    # 4) UI 목업 패턴 (CSS/HTML)
    for filepath in all_files:
        if filepath.suffix not in [".css", ".html", ".htm"]:
            continue

        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines, start=1):
            for pattern in UI_MOCKUP_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    finding = {
                        "file": str(rel_path),
                        "rule": "UI_MOCKUP_PATTERN",
                        "line": i,
                        "snippet": line.strip()[:100],
                        "sha256": sha256_file(filepath),
                    }
                    if is_allowed:
                        warnings.append(f"[WARN] {rel_path}:{i}: UI_MOCKUP_PATTERN (allowlisted)")
                    else:
                        findings.append(finding)
                    break

    # 5) SSOT 임포트 위반
    for filepath in all_files:
        if filepath.suffix != ".py":
            continue

        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines, start=1):
            for pattern in SSOT_IMPORT_VIOLATIONS:
                if re.search(pattern, line):
                    finding = {
                        "file": str(rel_path),
                        "rule": "SSOT_IMPORT_VIOLATION",
                        "line": i,
                        "snippet": line.strip()[:100],
                        "sha256": sha256_file(filepath),
                    }
                    if is_allowed:
                        warnings.append(f"[WARN] {rel_path}:{i}: SSOT_IMPORT_VIOLATION (allowlisted)")
                    else:
                        findings.append(finding)

    # 6) 매직 리터럴 검출
    for filepath in all_files:
        if filepath.suffix != ".py":
            continue

        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        magic_findings = detect_magic_literals(filepath, base_dir)
        for finding in magic_findings:
            if is_allowed:
                warnings.append(f"[WARN] {finding['file']}: MAGIC_LITERAL (allowlisted)")
            else:
                findings.append(finding)

    # 7) 에러 스키마 위반
    for filepath in all_files:
        if filepath.suffix != ".py":
            continue

        rel_path = filepath.relative_to(base_dir)
        is_allowed = is_allowlisted(filepath, base_dir)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines, start=1):
            for pattern in ERROR_SCHEMA_VIOLATIONS:
                if re.search(pattern, line):
                    finding = {
                        "file": str(rel_path),
                        "rule": "ERROR_SCHEMA_VIOLATION",
                        "line": i,
                        "snippet": line.strip()[:100],
                        "sha256": sha256_file(filepath),
                    }
                    if is_allowed:
                        warnings.append(f"[WARN] {rel_path}:{i}: ERROR_SCHEMA_VIOLATION (allowlisted)")
                    else:
                        findings.append(finding)

    # 8) 공유 중복 검출 (전역)
    shared_dup_findings = detect_shared_dup(all_files, base_dir)
    for finding in shared_dup_findings:
        # 공유 중복은 파일 단위가 아니므로 allowlist 적용 안 함
        findings.append(finding)

    return findings, warnings


# ============================================================
# 리포트 생성
# ============================================================

def generate_report(findings: List[Dict], warnings: List[str], output_dir: Path) -> Path:
    """리포트 생성 (report.md)"""
    report_path = output_dir / "report.md"

    # 카테고리별 집계
    category_counts = defaultdict(int)
    for finding in findings:
        category_counts[finding.get("rule", "UNKNOWN")] += 1

    # Top 10 위반 파일
    file_counts = defaultdict(int)
    for finding in findings:
        if "file" in finding:
            file_counts[finding["file"]] += 1
    top_10_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # 리포트 작성
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Spec Kit Compliance Audit Report\n\n")
        f.write(f"**Timestamp**: {datetime.now().isoformat()}\n\n")
        f.write(f"**Total Violations**: {len(findings)}\n\n")
        f.write(f"**Total Warnings** (allowlisted): {len(warnings)}\n\n")

        f.write("## Category Summary\n\n")
        f.write("| Rule | Count |\n")
        f.write("|------|-------|\n")
        for rule, count in sorted(category_counts.items()):
            f.write(f"| {rule} | {count} |\n")
        f.write("\n")

        f.write("## Top 10 Violating Files\n\n")
        f.write("| File | Violations |\n")
        f.write("|------|------------|\n")
        for filepath, count in top_10_files:
            f.write(f"| {filepath} | {count} |\n")
        f.write("\n")

        if warnings:
            f.write("## Warnings (Allowlisted)\n\n")
            for warning in warnings[:20]:  # 상위 20개만
                f.write(f"- {warning}\n")
            f.write("\n")

        f.write("## All Violations (Sample)\n\n")
        for finding in findings[:50]:  # 상위 50개만
            f.write(f"### {finding.get('rule', 'UNKNOWN')}\n")
            f.write(f"- **File**: {finding.get('file', 'N/A')}\n")
            f.write(f"- **Line**: {finding.get('line', 'N/A')}\n")
            f.write(f"- **Snippet**: `{finding.get('snippet', 'N/A')}`\n")
            f.write(f"- **SHA256**: {finding.get('sha256', 'N/A')}\n\n")

    return report_path


def generate_findings_jsonl(findings: List[Dict], output_dir: Path) -> Path:
    """findings.jsonl 생성"""
    findings_path = output_dir / "findings.jsonl"
    with open(findings_path, "w", encoding="utf-8") as f:
        for finding in findings:
            f.write(json.dumps(finding, ensure_ascii=False) + "\n")
    return findings_path


def create_evidence_pack(findings_path: Path, report_path: Path, output_dir: Path) -> Path:
    """EvidencePack_spec_kit_audit.zip 생성"""
    pack_path = output_dir / "EvidencePack_spec_kit_audit.zip"
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(findings_path, arcname="findings.jsonl")
        zf.write(report_path, arcname="report.md")
        # TODO: 의심 파일 첨부 (상위 10개)
    return pack_path


def update_sha256sums(pack_path: Path, findings_path: Path, report_path: Path, base_dir: Path):
    """SHA256SUMS.txt 업데이트"""
    sha256sums_path = base_dir / "SHA256SUMS.txt"

    # 기존 SHA256SUMS.txt 읽기
    existing_hashes = {}
    if sha256sums_path.exists():
        with open(sha256sums_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) == 2:
                        existing_hashes[parts[1]] = parts[0]

    # 새 파일 해시 추가
    new_files = {
        str(pack_path.relative_to(base_dir)): sha256_file(pack_path),
        str(findings_path.relative_to(base_dir)): sha256_file(findings_path),
        str(report_path.relative_to(base_dir)): sha256_file(report_path),
    }

    # 병합
    existing_hashes.update(new_files)

    # 재작성
    with open(sha256sums_path, "w", encoding="utf-8") as f:
        for filepath in sorted(existing_hashes.keys()):
            f.write(f"{existing_hashes[filepath]}  {filepath}\n")


# ============================================================
# CLI 진입점
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Spec Kit Compliance Audit")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Repository base directory (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist/audit"),
        help="Output directory for audit results (default: dist/audit)",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Starting Spec Kit Compliance Audit...")
    print(f"[INFO] Base directory: {base_dir}")
    print(f"[INFO] Output directory: {output_dir}")

    # 스캔 실행
    findings, warnings = scan_repository(base_dir)

    print(f"\n[RESULT] Total violations: {len(findings)}")
    print(f"[RESULT] Total warnings (allowlisted): {len(warnings)}")

    # 리포트 생성
    findings_path = generate_findings_jsonl(findings, output_dir)
    report_path = generate_report(findings, warnings, output_dir)
    pack_path = create_evidence_pack(findings_path, report_path, output_dir)

    print(f"\n[OUTPUT] Findings: {findings_path}")
    print(f"[OUTPUT] Report: {report_path}")
    print(f"[OUTPUT] EvidencePack: {pack_path}")

    # SHA256SUMS 업데이트
    update_sha256sums(pack_path, findings_path, report_path, base_dir)
    print(f"[OUTPUT] SHA256SUMS.txt updated")

    # Exit code 결정
    if len(findings) > 0:
        print(f"\n[FAIL] Spec Kit Compliance Audit FAILED: {len(findings)} violations found")
        sys.exit(2)
    else:
        print(f"\n[PASS] Spec Kit Compliance Audit PASSED: No violations found")
        sys.exit(0)


if __name__ == "__main__":
    main()
