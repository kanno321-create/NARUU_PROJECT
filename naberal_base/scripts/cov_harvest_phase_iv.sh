#!/usr/bin/env bash
# Phase IV: Coverage Harvest with DB Process Isolation
# FIX: Use `coverage run` directly + separate COVERAGE_FILE per lane

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/out/evidence"
mkdir -p "$OUT"

echo "[Phase IV Harvest] Starting coverage collection with DB process isolation..."

# Clean old coverage data
rm -f .coverage .coverage.* "$OUT/.coverage.*" || true

# ① Unit/Regression Tests (Zero-Mock, no DB) — separate coverage file
echo "[1/2] Unit/Regression Lane (Zero-Mock, exclude tests/integration)..."
export COVERAGE_FILE="$OUT/.coverage.unit"
coverage erase || true
coverage run --source=api,src/kis_estimator_core -m pytest tests/unit tests/regression -q | tee "$OUT/cov_unit_regression.log"

# ② DB Integration Tests (all integration tests including data_transformer) — separate coverage file
echo "[2/2] DB Integration Lane (all tests/integration/*, process isolated)..."
export COVERAGE_FILE="$OUT/.coverage.db"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
coverage erase || true
coverage run --source=api,src/kis_estimator_core -m pytest tests/integration -q | tee "$OUT/db_lane.log"

# ③ Combine & Report
echo "[Phase IV Harvest] Combining coverage data..."
coverage combine "$OUT/.coverage.unit" "$OUT/.coverage.db"

echo "[Phase IV Harvest] Generating coverage.xml..."
coverage xml -o "$OUT/coverage_phase_IV.xml"

echo "[Phase IV Harvest] Final Coverage Report:"
echo "============================================="
coverage report -m --fail-under=70 | tee "$OUT/cov_harvest_phase_iv.log"

echo ""
echo "[Phase IV Harvest] Complete! Artifacts:"
echo "  - $OUT/coverage_phase_IV.xml"
echo "  - $OUT/cov_harvest_phase_iv.log"
echo "  - $OUT/cov_unit_regression.log"
echo "  - $OUT/db_lane.log"
