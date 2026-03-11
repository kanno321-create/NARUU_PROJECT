#!/usr/bin/env bash
# check_openapi.sh — OpenAPI Contract Verification Wrapper
# Purpose: Shell wrapper for verify_openapi_diff.py (PROD Release Verify Pack)
# Usage: bash scripts/check_openapi.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo "OpenAPI Contract Verification"
echo "========================================="

# Check if OpenAPI snapshot exists
if [ ! -f "dist/contract/openapi_v1.0.0.json" ]; then
    echo "[ERROR] OpenAPI snapshot not found: dist/contract/openapi_v1.0.0.json"
    echo "   Run: python scripts/extract_openapi.py"
    exit 1
fi

echo "[OK] OpenAPI snapshot found"

# Set PYTHONPATH to include both project root and src
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/src"

# Run verification script
echo "Running verify_openapi_diff.py..."
python scripts/verify_openapi_diff.py

echo "========================================="
echo "[PASS] OpenAPI Contract Verification Complete"
echo "========================================="
exit 0
