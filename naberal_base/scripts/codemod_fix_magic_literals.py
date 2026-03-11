"""
Codemod: Fix MAGIC_LITERAL violations - migrate to SSOT constants

절대 원칙:
- 모든 magic literals는 /core/ssot/constants_format.py에서 import
- 하드코딩된 단위 문자열 ("EA", "KG", "M", "식", "면") → UNIT_* 상수
- 하드코딩된 계산 (600*765, 700*1450) → 테스트는 명시적 상수로, 코드는 SSOT 상수
"""

import sys
from pathlib import Path
from typing import List, Tuple


# 단위 문자열 → SSOT 상수 매핑
UNIT_REPLACEMENTS = {
    '"EA"': "UNIT_ACCESSORY",  # 범용 단위 (부속자재)
    "'EA'": "UNIT_ACCESSORY",
    '"KG"': "UNIT_BUSBAR",
    "'KG'": "UNIT_BUSBAR",
    '"M"': "UNIT_COATING",
    "'M'": "UNIT_COATING",
    '"식"': "UNIT_ASSEMBLY",
    "'식'": "UNIT_ASSEMBLY",
    '"면"': "UNIT_ENCLOSURE",
    "'면'": "UNIT_ENCLOSURE",
}

# 파일별 대상 magic literals
FILE_TARGETS = {
    "data_transformer.py": ['"EA"', '"식"'],
    "excel_generator.py": ['"면"', '"식"'],
    "models.py": ['"식"', "700*1450"],
}


def add_ssot_import(filepath: Path) -> Tuple[str, bool]:
    """파일에 SSOT import 추가 (아직 없으면)"""
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    # SSOT import가 이미 있는지 확인
    has_ssot_import = any("from src.kis_estimator_core.core.ssot.constants_format import" in ln for ln in lines)
    if has_ssot_import:
        return content, False

    # import 삽입 위치 찾기 (마지막 import 후 or docstring 후)
    insert_idx = 0
    in_docstring = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Docstring 처리
        if '"""' in stripped or "'''" in stripped:
            in_docstring = not in_docstring
            if not in_docstring:
                insert_idx = i + 1
            continue
        # import 라인
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_idx = i + 1

    # SSOT import 추가
    ssot_import = "from src.kis_estimator_core.core.ssot.constants_format import (\n    UNIT_ACCESSORY,\n    UNIT_BUSBAR,\n    UNIT_COATING,\n    UNIT_ASSEMBLY,\n    UNIT_ENCLOSURE,\n)"
    lines.insert(insert_idx, ssot_import)
    lines.insert(insert_idx + 1, "")  # 공백 추가

    new_content = "\n".join(lines)
    return new_content, True


def replace_magic_literals(filepath: Path, targets: List[str]) -> Tuple[str, int]:
    """파일 내 magic literals를 SSOT 상수로 교체"""
    content = filepath.read_text(encoding="utf-8")
    changes = 0

    for literal in targets:
        if literal in UNIT_REPLACEMENTS:
            replacement = UNIT_REPLACEMENTS[literal]
            count = content.count(literal)
            if count > 0:
                content = content.replace(literal, replacement)
                changes += count
                print(f"  - {literal} → {replacement} ({count}회)")

        # 특수 케이스: 700*1450 (models.py 기본 크기)
        elif literal == "700*1450":
            # DEFAULT_ENCLOSURE_SIZE 상수로 추출
            if "DEFAULT_ENCLOSURE_SIZE" not in content:
                # 상수 정의 추가 (imports 후)
                lines = content.split("\n")
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("from ") or line.strip().startswith("import "):
                        insert_idx = i + 1
                lines.insert(insert_idx + 1, "")
                lines.insert(insert_idx + 2, "# Default enclosure size (Spec Kit: extract magic literal)")
                lines.insert(insert_idx + 3, "DEFAULT_ENCLOSURE_SIZE = 700 * 1450  # W*H (mm²)")
                lines.insert(insert_idx + 4, "")
                content = "\n".join(lines)
                changes += 1
                print(f"  - Added DEFAULT_ENCLOSURE_SIZE constant")

            # 사용처 교체
            content = content.replace("700*1450", "DEFAULT_ENCLOSURE_SIZE")
            changes += 1
            print(f"  - 700*1450 → DEFAULT_ENCLOSURE_SIZE")

    return content, changes


def fix_test_literals(filepath: Path) -> Tuple[str, int]:
    """테스트 파일의 magic literals 수정 (명시적 상수)"""
    content = filepath.read_text(encoding="utf-8")
    changes = 0

    # 600*765, 600*800, 600*1000 → 테스트 상수
    test_sizes = {
        "600*765": "TEST_SIZE_1",
        "600*800": "TEST_SIZE_2",
        "600*1000": "TEST_SIZE_3",
    }

    # 상수 정의 추가
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            insert_idx = i + 1

    # 이미 정의되어 있는지 확인
    if "TEST_SIZE_1" not in content:
        lines.insert(insert_idx + 1, "")
        lines.insert(insert_idx + 2, "# Test size constants (Spec Kit: no magic literals)")
        lines.insert(insert_idx + 3, "TEST_SIZE_1 = 600 * 765  # W*H (mm²)")
        lines.insert(insert_idx + 4, "TEST_SIZE_2 = 600 * 800")
        lines.insert(insert_idx + 5, "TEST_SIZE_3 = 600 * 1000")
        lines.insert(insert_idx + 6, "")
        content = "\n".join(lines)
        changes += 3
        print(f"  - Added TEST_SIZE constants")

    # 사용처 교체
    for literal, constant in test_sizes.items():
        count = content.count(literal)
        if count > 0:
            content = content.replace(literal, constant)
            changes += count
            print(f"  - {literal} → {constant} ({count}회)")

    # "EA" → UNIT_ACCESSORY (test에서도 SSOT import)
    if '"EA"' in content:
        content, added_import = add_ssot_import(filepath)
        if added_import:
            print(f"  - Added SSOT import")
        content = content.replace('"EA"', "UNIT_ACCESSORY")
        changes += content.count("UNIT_ACCESSORY")
        print(f"  - \"EA\" → UNIT_ACCESSORY")

    return content, changes


def main() -> int:
    base_dir = Path(__file__).parent.parent

    print("[INFO] Starting MAGIC_LITERAL fix...")
    print(f"[INFO] Base directory: {base_dir}")

    total_changes = 0

    # 1) 엔진 파일 수정
    engine_dir = base_dir / "src" / "kis_estimator_core" / "engine"
    for filename, targets in FILE_TARGETS.items():
        filepath = engine_dir / filename
        if not filepath.exists():
            print(f"[SKIP] {filename} (not found)")
            continue

        print(f"\n[FIX] {filename}")

        # SSOT import 추가
        content, added_import = add_ssot_import(filepath)
        if added_import:
            print(f"  - Added SSOT import")
            filepath.write_text(content, encoding="utf-8")

        # Magic literals 교체
        content, changes = replace_magic_literals(filepath, targets)
        filepath.write_text(content, encoding="utf-8")
        total_changes += changes

    # 2) 테스트 파일 수정
    test_files = [
        base_dir / "tests" / "core" / "test_ssot_phase3_smoke.py",
        base_dir / "tests" / "integration" / "test_phase3_ssot.py",
        base_dir / "tests" / "unit" / "test_estimate_formatter.py",
    ]

    for filepath in test_files:
        if not filepath.exists():
            continue

        print(f"\n[FIX] {filepath.name}")
        content, changes = fix_test_literals(filepath)
        filepath.write_text(content, encoding="utf-8")
        total_changes += changes

    print(f"\n[RESULT] Total changes: {total_changes}")

    # Summary
    summary_path = base_dir / "dist" / "codemod_magic_summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"MAGIC_LITERAL Fix Summary\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Total changes: {total_changes}\n\n")
        f.write(f"Engine files modified:\n")
        for filename in FILE_TARGETS.keys():
            f.write(f"  - {filename}\n")
        f.write(f"\nTest files modified:\n")
        for fp in test_files:
            if fp.exists():
                f.write(f"  - {fp.name}\n")

    print(f"\n[OUTPUT] Summary: {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
