#!/usr/bin/env python3
"""
Import normalization script
Replaces 'from src.kis_estimator_core' with 'from kis_estimator_core'
"""
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    try:
        content = filepath.read_text(encoding="utf-8")
        original = content
        content = re.sub(r'\bfrom src\.kis_estimator_core\b', 'from kis_estimator_core', content)
        content = re.sub(r'\bfrom src\.kis_erp_core\b', 'from kis_erp_core', content)
        if content != original:
            filepath.write_text(content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error: {filepath}: {e}")
        return False

root = Path(__file__).parent.parent
changed = []
for py in (root / "tests").rglob("*.py"):
    if fix_imports_in_file(py):
        changed.append(py)
        print(f"Fixed: {py.relative_to(root)}")
for py in (root / "src").rglob("*.py"):
    if fix_imports_in_file(py):
        changed.append(py)
        print(f"Fixed: {py.relative_to(root)}")
print(f"\nTotal: {len(changed)}")
