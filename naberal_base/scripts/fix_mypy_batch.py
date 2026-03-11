#!/usr/bin/env python3
"""
Mypy 에러 일괄 수정 스크립트
130개 에러를 카테고리별로 체계적으로 수정
"""

import re
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "kis_estimator_core"

def read_error_file() -> List[str]:
    """mypy 에러 파일 읽기"""
    error_file = ROOT / "out" / "evidence" / "mypy_errors_full.txt"
    with open(error_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if " error: " in line]

def parse_error(line: str) -> Tuple[str, int, str, str]:
    """에러 파싱: (파일, 라인, 에러코드, 메시지)"""
    match = re.match(r"([^:]+):(\d+): error: (.+?) \[(.+?)\]", line)
    if match:
        file_path = match.group(1).replace("\\", "/")
        line_num = int(match.group(2))
        message = match.group(3)
        code = match.group(4)
        return (file_path, line_num, code, message)
    return ("", 0, "", "")

def fix_union_attr_none_check(file_path: Path, line_num: int, error_msg: str):
    """union-attr 에러: None 체크 추가"""
    lines = file_path.read_text(encoding="utf-8").splitlines()

    # Line is 1-indexed
    target_line = lines[line_num - 1]

    # self.engine이 None일 수 있음
    if "self.engine" in target_line and ".connect()" in target_line:
        indent = len(target_line) - len(target_line.lstrip())
        check_line = " " * indent + "if self.engine is None:"
        return_line = " " * (indent + 4) + "return False"

        # 함수 시작 찾기
        func_start = line_num - 1
        while func_start > 0 and not lines[func_start].strip().startswith("def "):
            func_start -= 1

        # None 체크 삽입
        lines.insert(func_start + 2, check_line)  # 함수 선언 다음 줄
        lines.insert(func_start + 3, return_line)

        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    return False

def fix_var_annotated(file_path: Path, line_num: int, error_msg: str):
    """var-annotated 에러: 타입 어노테이션 추가"""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    target_line = lines[line_num - 1]

    # errors = [] → errors: list[str] = []
    if "errors = []" in target_line:
        new_line = target_line.replace("errors = []", "errors: list[str] = []")
        lines[line_num - 1] = new_line
        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    # warnings = [] → warnings: list[str] = []
    if "warnings = []" in target_line:
        new_line = target_line.replace("warnings = []", "warnings: list[str] = []")
        lines[line_num - 1] = new_line
        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    # details = {} → details: dict[str, Any] = {}
    if "details = {}" in target_line:
        # from typing import Any 확인
        if "from typing import" not in "\n".join(lines[:20]):
            # import 추가
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i + 1, "from typing import Any, Dict")
                    break

        new_line = target_line.replace("details = {}", "details: Dict[str, Any] = {}")
        lines[line_num - 1] = new_line
        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    return False

def fix_return_value_sequence(file_path: Path, line_num: int):
    """return-value 에러: list → Sequence"""
    lines = file_path.read_text(encoding="utf-8").splitlines()

    # 함수 시그니처 찾기
    func_line = line_num - 1
    while func_line > 0 and not lines[func_line].strip().startswith("def "):
        func_line -= 1

    # -> list[...] → -> Sequence[...]
    if "-> list[" in lines[func_line]:
        lines[func_line] = lines[func_line].replace("-> list[", "-> Sequence[")

        # from typing import Sequence 확인
        if "from typing import" not in "\n".join(lines[:20]):
            for i, line in enumerate(lines):
                if line.startswith("from typing import"):
                    if "Sequence" not in line:
                        lines[i] = line.replace("import ", "import Sequence, ")
                    break

        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    return False

def main():
    """메인 실행"""
    errors = read_error_file()

    print(f"총 {len(errors)}개 에러 발견")

    # 카테고리별 카운트
    categories = {}
    for error_line in errors:
        _, _, code, _ = parse_error(error_line)
        categories[code] = categories.get(code, 0) + 1

    print("\n=== 에러 카테고리 ===")
    for code, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"{code:20s}: {count}개")

    # 파일별로 수정
    fixed_count = 0
    for error_line in errors:
        file_rel, line_num, code, message = parse_error(error_line)
        if not file_rel:
            continue

        # 절대 경로로 변환
        file_path = ROOT / "src" / file_rel
        if not file_path.exists():
            continue

        # 에러 타입별 수정
        fixed = False
        if code == "union-attr":
            fixed = fix_union_attr_none_check(file_path, line_num, message)
        elif code == "var-annotated":
            fixed = fix_var_annotated(file_path, line_num, message)
        elif code == "return-value" and "Sequence" in message:
            fixed = fix_return_value_sequence(file_path, line_num)

        if fixed:
            fixed_count += 1
            print(f"✅ Fixed: {file_rel}:{line_num} [{code}]")

    print(f"\n총 {fixed_count}개 에러 자동 수정 완료")
    print("남은 에러는 수동 검토 필요")

if __name__ == "__main__":
    main()
