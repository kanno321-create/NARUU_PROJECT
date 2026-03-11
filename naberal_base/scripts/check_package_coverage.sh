#!/bin/bash
# Check Package-Level Coverage
# Part of Coverage Policy enforcement

set -e

# Force UTF-8 for emoji support (Windows compatibility)
export PYTHONIOENCODING=utf-8

echo "========================================="
echo "Package-Level Coverage Check"
echo "========================================="
echo ""

if [ ! -f "coverage.xml" ]; then
    echo "[ERROR] coverage.xml not found. Run pytest with --cov first."
    exit 1
fi

# Parse coverage.xml for package-level coverage
python -c "
import xml.etree.ElementTree as ET

tree = ET.parse('coverage.xml')
root = tree.getroot()

packages = {}

for pkg in root.findall('.//package'):
    pkg_name = pkg.attrib.get('name', '.')
    line_rate = float(pkg.attrib.get('line-rate', 0)) * 100

    # Map package names to friendly names
    if 'core' in pkg_name or pkg_name.endswith('ssot'):
        category = 'core'
    elif 'infra' in pkg_name:
        category = 'infra'
    elif 'engine' in pkg_name:
        category = 'engine'
    elif 'kpew' in pkg_name:
        category = 'kpew'
    elif 'api' in pkg_name or pkg_name == '.':
        category = 'api'
    else:
        category = 'other'

    if category not in packages:
        packages[category] = []
    packages[category].append((pkg_name, line_rate))

# Calculate category averages
print('Package Coverage Summary:')
print('=' * 60)

guards = {
    'core': 75.0,
    'infra': 70.0,
    'engine': 68.0,
    'kpew': 65.0,
    'api': 60.0,
    'other': 60.0,
}

for category in sorted(packages.keys()):
    pkgs = packages[category]
    avg = sum(cov for _, cov in pkgs) / len(pkgs)
    guard = guards.get(category, 60.0)
    status = '✅ PASS' if avg >= guard else '❌ FAIL'

    print(f'{category:10s}: {avg:5.1f}% (guard: {guard:.1f}%) {status}')

    # Show individual packages if detailed
    if len(pkgs) > 1 and avg < guard:
        for pkg_name, cov in sorted(pkgs, key=lambda x: x[1]):
            if cov < guard:
                print(f'  - {pkg_name}: {cov:.1f}% (below guard)')

print('=' * 60)

# Overall coverage (Phase VIII: 라쳇 상향 66%)
overall_rate = float(root.attrib.get('line-rate', 0)) * 100
overall_guard = 66.0  # Phase VIII: 2025-11-28 라쳇 상향 (CLAUDE.md)
overall_status = '✅ PASS' if overall_rate >= overall_guard else '❌ FAIL'
print(f'Overall    : {overall_rate:5.1f}% (guard: {overall_guard:.1f}%) {overall_status}')
print('')

# Exit with failure if any category fails
failed = [cat for cat, pkgs in packages.items()
          if sum(cov for _, cov in pkgs) / len(pkgs) < guards.get(cat, 60.0)]

if failed or overall_rate < overall_guard:
    print('[FAIL] Coverage guards not met')
    if failed:
        print(f\"Failed categories: {', '.join(failed)}\")
    if overall_rate < overall_guard:
        print(f'Overall coverage below guard: {overall_rate:.1f}% < {overall_guard:.1f}%')
    exit(1)
else:
    print('[PASS] All coverage guards met ✅')
"

echo ""
echo "========================================="
echo "Package Coverage Check Complete"
echo "========================================="
