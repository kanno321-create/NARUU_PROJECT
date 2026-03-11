"""
OpenAPI Diff Verification - Contract Snapshot vs Runtime

Verifies that the OpenAPI snapshot (dist/contract/openapi_v1.0.0.json)
matches the runtime-generated spec from FastAPI app.

Contract-First principle: Snapshot is authoritative, runtime must match.

Usage:
    python scripts/verify_openapi_diff.py

Evidence:
    - Saves diff result to out/evidence/openapi_diff_result.json
    - Exit code 0 if Diff=0, non-zero otherwise
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.main import app


def normalize_spec(spec: dict) -> dict:
    """Normalize OpenAPI spec for comparison (remove non-deterministic fields)"""
    # Remove fields that may vary between runs
    normalized = json.loads(json.dumps(spec))  # Deep copy

    # No normalization needed for now (all fields should be deterministic)
    # Future: Add normalization if needed (e.g., timestamps, UUIDs)

    return normalized


def compare_specs(snapshot: dict, runtime: dict) -> tuple[bool, list[str]]:
    """
    Compare snapshot vs runtime OpenAPI specs

    Returns:
        (is_equal, differences)
    """
    differences = []

    # Compare top-level keys
    snapshot_keys = set(snapshot.keys())
    runtime_keys = set(runtime.keys())

    if snapshot_keys != runtime_keys:
        missing_in_runtime = snapshot_keys - runtime_keys
        extra_in_runtime = runtime_keys - snapshot_keys

        if missing_in_runtime:
            differences.append(f"Keys missing in runtime: {missing_in_runtime}")
        if extra_in_runtime:
            differences.append(f"Extra keys in runtime: {extra_in_runtime}")

    # Compare common keys
    for key in snapshot_keys & runtime_keys:
        if snapshot[key] != runtime[key]:
            differences.append(f"Mismatch in '{key}': snapshot != runtime")

            # Detailed comparison for paths
            if key == "paths":
                snapshot_paths = set(snapshot["paths"].keys())
                runtime_paths = set(runtime["paths"].keys())

                if snapshot_paths != runtime_paths:
                    missing = snapshot_paths - runtime_paths
                    extra = runtime_paths - snapshot_paths

                    if missing:
                        differences.append(f"  Paths missing in runtime: {missing}")
                    if extra:
                        differences.append(f"  Extra paths in runtime: {extra}")

    is_equal = len(differences) == 0
    return is_equal, differences


def main():
    """Main diff verification workflow"""
    print("=" * 70)
    print("OpenAPI Diff Verification - Snapshot vs Runtime")
    print("=" * 70)

    # Load snapshot (authoritative)
    snapshot_path = project_root / "dist" / "contract" / "openapi_v1.0.0.json"

    if not snapshot_path.exists():
        print(f"[ERROR] Snapshot not found: {snapshot_path}")
        print("   Run: python scripts/extract_openapi.py")
        return 1

    print(f"\n[SNAPSHOT] Loading snapshot: {snapshot_path}")
    with open(snapshot_path, encoding="utf-8") as f:
        snapshot_spec = json.load(f)

    # Generate runtime spec
    print("[RUNTIME] Generating runtime spec from FastAPI app...")
    runtime_spec = app.openapi()

    # Apply T4 metadata enhancement to runtime spec (same as extract script)
    if "/v1/estimate" in runtime_spec.get("paths", {}):
        if "post" in runtime_spec["paths"]["/v1/estimate"]:
            post_spec = runtime_spec["paths"]["/v1/estimate"]["post"]
            post_spec["x-kis-alias-of"] = "/v1/estimate/plan"
            post_spec["x-kis-sunset-days"] = 90
            post_spec["x-kis-migration-guide"] = {
                "old": "POST /v1/estimate",
                "new": "POST /v1/estimate/plan",
                "breaking_changes": False,
                "request_schema": "UNCHANGED",
                "response_schema": "UNCHANGED"
            }

    # Normalize specs
    snapshot_norm = normalize_spec(snapshot_spec)
    runtime_norm = normalize_spec(runtime_spec)

    # Compare
    print("\n[COMPARE] Comparing specs...")
    is_equal, differences = compare_specs(snapshot_norm, runtime_norm)

    # Results
    result = {
        "verified_at": datetime.now().isoformat() + "Z",
        "rebuild_phase": "T4",
        "snapshot_path": str(snapshot_path),
        "diff_equal": is_equal,
        "differences_count": len(differences),
        "differences": differences,
        "snapshot_size": snapshot_path.stat().st_size,
        "runtime_endpoints": len(runtime_spec.get("paths", {})),
        "snapshot_endpoints": len(snapshot_spec.get("paths", {}))
    }

    # Save evidence
    evidence_dir = project_root / "out" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence_path = evidence_dir / "openapi_diff_result.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Evidence saved: {evidence_path}")

    # Print results
    print("\n" + "=" * 70)
    if is_equal:
        print("[PASS] Snapshot == Runtime (Diff=0)")
        print("   Contract is consistent between snapshot and runtime")
        return 0
    else:
        print("[FAIL] Snapshot != Runtime")
        print(f"   Found {len(differences)} difference(s):")
        for diff in differences:
            print(f"     - {diff}")
        print("\n   ACTION REQUIRED:")
        print("   1. Review differences above")
        print("   2. If runtime is correct, regenerate snapshot:")
        print("      python scripts/extract_openapi.py")
        print("   3. If snapshot is correct, fix runtime to match")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
