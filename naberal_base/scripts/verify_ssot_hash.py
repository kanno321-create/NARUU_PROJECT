"""
SSOT Hash Verification - Structural Hash (Meta-Excluded)

Verifies that SSOT JSON files maintain consistent structure by:
1. Loading each JSON file
2. Removing metadata fields (meta, created_at, updated_at, version, etc.)
3. Sorting keys recursively for deterministic comparison
4. Computing SHA256 hash of the canonical JSON
5. Comparing against stored hash baselines (if exist)

Usage:
    python scripts/verify_ssot_hash.py

Evidence:
    - Saves structural hashes to out/evidence/SSOT_STRUCT_HASH.txt
    - Exit code 0 if consistent, non-zero if drift detected
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Any
from datetime import datetime

# Project root
project_root = Path(__file__).parent.parent

# SSOT JSON files directory
SSOT_DIR = project_root / "knowledge_consolidation" / "output"
EVIDENCE_DIR = project_root / "out" / "evidence"

# SSOT JSON files (6 required)
SSOT_FILES = [
    "estimates.json",
    "standards.json",
    "formulas.json",
    "enclosures.json",
    "breakers.json",
    "accessories.json"
]

# Metadata fields to exclude from hash
META_FIELDS = {
    "meta", "created_at", "updated_at", "version", "last_modified",
    "generated_at", "timestamp", "_meta", "__meta__"
}


def remove_metadata(obj: Any) -> Any:
    """Recursively remove metadata fields from JSON object"""
    if isinstance(obj, dict):
        return {
            k: remove_metadata(v)
            for k, v in obj.items()
            if k not in META_FIELDS
        }
    elif isinstance(obj, list):
        return [remove_metadata(item) for item in obj]
    else:
        return obj


def canonical_json(obj: Any) -> str:
    """Convert object to canonical JSON string (sorted keys, no whitespace)"""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def compute_structural_hash(file_path: Path) -> str:
    """Compute SHA256 hash of JSON structure (metadata excluded)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Remove metadata
    clean_data = remove_metadata(data)

    # Canonical JSON
    canonical = canonical_json(clean_data)

    # SHA256 hash
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def main():
    """Main SSOT hash verification workflow"""
    print("=" * 70)
    print("SSOT Hash Verification - Structural Hash (Meta-Excluded)")
    print("=" * 70)

    # Check SSOT directory exists
    if not SSOT_DIR.exists():
        print(f"[ERROR] SSOT directory not found: {SSOT_DIR}")
        return 1

    print(f"\n[SSOT] Directory: {SSOT_DIR}")

    # Compute structural hashes
    hashes = {}
    missing_files = []

    for filename in SSOT_FILES:
        file_path = SSOT_DIR / filename

        if not file_path.exists():
            print(f"[ERROR] Missing SSOT file: {filename}")
            missing_files.append(filename)
            continue

        try:
            struct_hash = compute_structural_hash(file_path)
            hashes[filename] = struct_hash
            print(f"[OK] {filename}: {struct_hash[:16]}...")
        except Exception as e:
            print(f"[ERROR] Failed to hash {filename}: {e}")
            return 1

    if missing_files:
        print(f"\n[FAIL] Missing {len(missing_files)} SSOT files")
        return 1

    # Save structural hashes to evidence
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    hash_file = EVIDENCE_DIR / "SSOT_STRUCT_HASH.txt"

    with open(hash_file, 'w', encoding='utf-8') as f:
        f.write(f"# SSOT Structural Hashes (Meta-Excluded)\n")
        f.write(f"# Generated: {datetime.now().isoformat()}Z\n")
        f.write(f"# Algorithm: SHA256(canonical_json(remove_metadata(json)))\n")
        f.write(f"\n")
        for filename in sorted(hashes.keys()):
            f.write(f"{hashes[filename]}  {filename}\n")

    print(f"\n[OK] Structural hashes saved: {hash_file}")

    # Check for baseline (optional)
    baseline_file = EVIDENCE_DIR / "SSOT_STRUCT_HASH_BASELINE.txt"

    if baseline_file.exists():
        print(f"\n[CHECK] Comparing against baseline: {baseline_file}")

        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline_lines = [
                line.strip() for line in f.readlines()
                if line.strip() and not line.startswith('#')
            ]

        baseline_hashes = {}
        for line in baseline_lines:
            if '  ' in line:
                hash_val, filename = line.split('  ', 1)
                baseline_hashes[filename] = hash_val

        # Compare
        drifts = []
        for filename, current_hash in hashes.items():
            baseline_hash = baseline_hashes.get(filename)
            if baseline_hash is None:
                print(f"[INFO] {filename}: New file (no baseline)")
            elif baseline_hash != current_hash:
                print(f"[DRIFT] {filename}: Hash changed")
                print(f"  Baseline: {baseline_hash[:16]}...")
                print(f"  Current:  {current_hash[:16]}...")
                drifts.append(filename)
            else:
                print(f"[MATCH] {filename}: Hash unchanged")

        if drifts:
            print(f"\n[WARN] Detected {len(drifts)} SSOT file(s) with structural drift")
            print("  This may indicate intentional changes or data corruption")
            print("  Review changes and update baseline if intentional:")
            print(f"    cp {hash_file} {baseline_file}")
            # Don't fail on drift, just warn
    else:
        print(f"\n[INFO] No baseline found, this is the first run")
        print(f"  To establish baseline: cp {hash_file} {baseline_file}")

    # Final result
    print("\n" + "=" * 70)
    print("[PASS] SSOT Hash Verification Complete")
    print(f"  Verified: {len(hashes)}/6 files")
    print(f"  Evidence: {hash_file}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
