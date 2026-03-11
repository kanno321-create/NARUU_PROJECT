#!/usr/bin/env bash
# Phase LOCKIN75: Coverage Harvest & Combine All Test Suites (no-abort policy)
# Purpose: Measure true project-wide coverage by harvesting all test runs
# Gate: overall ≥75.0% (Phase LOCKIN75 locked threshold)

set -euo pipefail

echo "═══════════════════════════════════════════════════════════════════════"
echo "Phase LOCKIN75: Coverage Harvest & Combine (No-Abort Policy)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Clean previous coverage data
echo "[CLEAN] Removing previous coverage data..."
rm -rf .coverage* coverage.xml htmlcov 2>/dev/null || true
mkdir -p htmlcov

# Set PYTHONPATH
export PYTHONPATH=.:src
echo "[ENV] PYTHONPATH=$PYTHONPATH"
echo ""

# Test suites to harvest (including Phase XVI, XVI-B, XVII, and XIX-B)
PHASES=(
    "tests/unit"
    "tests/integration"
    "tests/phase_x"
    "tests/phase_xiv"
    "tests/phase_xv"
    "tests/phase_xvi"
    "tests/phase_xvi_int"
    "tests/phase_xvii"
    "tests/phase_xixb"
)

echo "[HARVEST] Starting coverage harvest from ${#PHASES[@]} test suites..."
echo ""

# Harvest coverage from each phase
for p in "${PHASES[@]}"; do
    if [ -d "$p" ]; then
        echo "[HARVEST] Running tests in $p..."
        pytest "$p" \
            --cov=api --cov=kis_estimator_core \
            --cov-report=xml --cov-report=html:htmlcov --cov-report=term-missing \
            --cov-append --maxfail=0 --durations=25 2>&1 | tail -50 || true
        echo ""
    else
        echo "[HARVEST] Directory $p not found, skipping..."
    fi
done

echo "[HARVEST] Combining coverage data..."
echo ""

# Combine coverage data using Python
python - <<'PY'
import coverage
import sys

try:
    cov = coverage.Coverage(data_file='.coverage')
    cov.load()
    cov.combine(strict=False)  # strict=False to allow missing files
    cov.save()
    cov.xml_report(outfile='coverage.xml')
    cov.html_report(directory='htmlcov')
    print("[OK] combined coverage.xml and htmlcov/ written")
except Exception as e:
    print(f"[ERROR] Coverage combine failed: {e}")
    sys.exit(1)
PY

echo ""
echo "[HARVEST] Checking coverage gate (≥75.0% for Phase LOCKIN75)..."
echo ""

# Check coverage percentage and gate
python - <<'PY'
import xml.etree.ElementTree as ET
import sys
import json
import time
import os

try:
    root = ET.parse('coverage.xml').getroot()
    pct = round(float(root.attrib['line-rate']) * 100, 2)
    print(f"[COVERAGE] {pct}%")

    # Phase LOCKIN75 gate: ≥75.0% (locked threshold)
    ok = pct >= 75.0

    # Write gate result (Phase LOCKIN75)
    os.makedirs("out/evidence/lockin75", exist_ok=True)

    with open("out/evidence/lockin75/coverage_gate.json", "w") as f:
        json.dump({
            "coverage": pct,
            "gate": 75.0,
            "status": "PASS" if ok else "FAIL",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }, f, ensure_ascii=False, indent=2)

    if ok:
        print(f"[GATE] PASS (coverage {pct}% >= 75.0%)")
        sys.exit(0)
    else:
        print(f"[GATE] FAIL (coverage {pct}% < 75.0%)")
        print("")
        print("RCA (Root Cause Analysis):")
        print("1. Phase LOCKIN75 requires ≥75% coverage (ratchet locked)")
        print("2. Check which modules have <75% coverage in coverage.xml")
        print("3. Top 10 least-covered modules:")

        # Print top 10 least-covered modules
        import xml.etree.ElementTree as ET
        root = ET.parse('coverage.xml').getroot()
        packages = root.findall('.//package')

        modules = []
        for pkg in packages:
            classes = pkg.findall('.//class')
            for cls in classes:
                name = cls.attrib.get('name', 'unknown')
                line_rate = float(cls.attrib.get('line-rate', 0))
                modules.append((name, line_rate * 100))

        modules.sort(key=lambda x: x[1])  # Sort by coverage asc
        for i, (name, cov) in enumerate(modules[:10], 1):
            print(f"   {i}. {name}: {cov:.1f}%")

        sys.exit(2)
except Exception as e:
    print(f"[ERROR] Coverage gate check failed: {e}")
    sys.exit(1)
PY

echo ""
echo "[HARVEST] Done."
echo "═══════════════════════════════════════════════════════════════════════"
