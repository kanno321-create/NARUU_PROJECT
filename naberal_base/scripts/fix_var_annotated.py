#!/usr/bin/env python3
"""var-annotated 에러 일괄 수정"""
import re
from pathlib import Path

# 에러 파일 읽기
ROOT = Path(__file__).parent.parent
errors_file = ROOT / "out" / "evidence" / "mypy_errors_full.txt"
errors = errors_file.read_text(encoding='utf-8')

# var-annotated 에러만 추출
var_errors = [line for line in errors.split('\n') if 'var-annotated' in line]

fixed_count = 0

for error_line in var_errors:
    match = re.match(r'([^:]+):(\d+):', error_line)
    if not match:
        continue

    file_path_rel = match.group(1).replace('\\', '/')
    line_num = int(match.group(2))

    # src/ 경로로 변환
    file_path = ROOT / "src" / file_path_rel
    if not file_path.exists():
        continue

    lines = file_path.read_text(encoding='utf-8').splitlines()
    target_line = lines[line_num - 1]

    # 수정
    modified = False
    new_line = target_line

    if 'errors = []' in target_line and 'list[' not in target_line:
        new_line = target_line.replace('errors = []', 'errors: list[str] = []')
        modified = True
    elif 'warnings = []' in target_line and 'list[' not in target_line:
        new_line = target_line.replace('warnings = []', 'warnings: list[str] = []')
        modified = True
    elif 'details = {}' in target_line and 'dict[' not in target_line:
        new_line = target_line.replace('details = {}', 'details: dict[str, Any] = {}')
        modified = True
    elif 'accessories = []' in target_line and 'List[' not in target_line:
        new_line = target_line.replace('accessories = []', 'accessories: List[AccessoryItem] = []')
        modified = True
    elif 'breaker_inputs = []' in target_line and 'list[' not in target_line:
        new_line = target_line.replace('breaker_inputs = []', 'breaker_inputs: list[dict] = []')
        modified = True
    elif 'pick_step = ' in target_line and ':' not in target_line.split('pick_step')[0]:
        new_line = target_line.replace('pick_step = ', 'pick_step: dict[str, Any] = ')
        modified = True
    elif 'place_step = ' in target_line and ':' not in target_line.split('place_step')[0]:
        new_line = target_line.replace('place_step = ', 'place_step: dict[str, Any] = ')
        modified = True

    if modified:
        lines[line_num - 1] = new_line
        file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        fixed_count += 1
        print(f'Fixed: {file_path.name}:{line_num}')

print(f'\nTotal var-annotated errors fixed!')
