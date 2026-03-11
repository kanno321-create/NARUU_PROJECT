#!/usr/bin/env python3
"""quality_gate.py의 QualityGate 생성자에 description 추가"""
from pathlib import Path
import re

ROOT = Path(__file__).parent.parent
file_path = ROOT / "src" / "kis_estimator_core" / "infra" / "quality_gate.py"

lines = file_path.read_text(encoding='utf-8').splitlines()

# 수정할 라인들
fixes = [
    (386, 'test_gte', 'Value must be >= threshold'),
    (387, 'test_lte', 'Value must be <= threshold'),
    (388, 'test_eq', 'Value must equal threshold'),
    (389, 'test_neq', 'Value must not equal threshold'),
    (419, 'critical_value', 'Critical value must be >= threshold'),
    (422, 'warning_value', 'Warning value must be >= threshold'),
]

for line_num, gate_name, desc in fixes:
    target_line = lines[line_num - 1]

    # QualityGate(...) 패턴 찾기
    if 'QualityGate(' in target_line and 'description=' not in target_line:
        # critical=True 또는 critical=False 앞에 description 삽입
        if 'critical=True' in target_line:
            new_line = target_line.replace(
                'critical=True',
                f'description="{desc}", critical=True'
            )
        elif 'critical=False' in target_line:
            new_line = target_line.replace(
                'critical=False',
                f'description="{desc}", critical=False'
            )
        else:
            # critical 인자가 마지막이 아닌 경우
            new_line = target_line.replace(
                'operator="',
                f'description="{desc}", operator="'
            )

        lines[line_num - 1] = new_line
        print(f'Fixed line {line_num}: {gate_name}')

file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'\nTotal 6 QualityGate descriptions added!')
