#!/usr/bin/env bash
# check_ssot_hash.sh — SSOT Integrity Verification Wrapper
# Purpose: Shell wrapper for verify_ssot_hash.py (PROD Release Verify Pack)
# Usage: bash scripts/check_ssot_hash.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo "SSOT Integrity Verification"
echo "========================================="

# Check if SSOT JSON files exist
echo "Checking SSOT JSON files..."
MISSING=0
for file in estimates standards formulas enclosures breakers accessories; do
    if [ ! -f "knowledge_consolidation/output/${file}.json" ]; then
        echo "[ERROR] Missing: knowledge_consolidation/output/${file}.json"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "[FAIL] Some SSOT JSON files are missing"
    exit 1
fi

echo "[OK] All 6 SSOT JSON files exist"

# Generate SHA256 checksums
echo "Generating SHA256 checksums..."
mkdir -p out/evidence
cd knowledge_consolidation/output
sha256sum *.json | sort > ../../out/evidence/SSOT_SHA256SUMS.txt
cd ../..
echo "[OK] SHA256 checksums generated"

# Run verification script
echo "Running verify_ssot_hash.py..."
python scripts/verify_ssot_hash.py

echo "========================================="
echo "[PASS] SSOT Integrity Verification Complete"
echo "========================================="
exit 0
