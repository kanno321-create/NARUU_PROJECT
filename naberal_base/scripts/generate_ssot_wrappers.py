#!/usr/bin/env python3
"""
SSOT Wrapper Generator

Reads 6 JSON files from knowledge_consolidation/output/
Removes meta fields and generates typed Python constants.

Output: src/kis_estimator_core/core/ssot/generated.py

Phase B: SSOT Unification (JSON → Code Generation)
LAW-02: No SSOT violations - single source only
LAW-03: No hardcoding - constants from JSON only
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


# SSOT JSON file paths (6 files)
SSOT_DIR = Path("knowledge_consolidation/output")
SSOT_FILES = [
    "accessories.json",
    "breakers.json",
    "enclosures.json",
    "estimates.json",
    "formulas.json",
    "standards.json",
]

# Output path
OUTPUT_FILE = Path("src/kis_estimator_core/core/ssot/generated.py")


def load_json_without_meta(filepath: Path) -> Dict[str, Any]:
    """Load JSON and remove meta field."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Remove meta field
    if "meta" in data:
        del data["meta"]

    return data


def compute_struct_hash(data: Dict[str, Any]) -> str:
    """
    Compute structural hash (meta-excluded, sorted).

    This hash is used for SSOT-Hash Gate in CI.
    """
    # Sort keys recursively for consistent hashing
    sorted_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(sorted_json.encode("utf-8")).hexdigest()


def dict_to_python_literal(obj: Any, indent: int = 0) -> str:
    """Convert dict/list to Python literal string."""
    ind = "    " * indent

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = ["{"]
        for k, v in obj.items():
            # Quote string keys
            key_str = f'"{k}"' if isinstance(k, str) else str(k)
            val_str = dict_to_python_literal(v, indent + 1)
            lines.append(f'{ind}    {key_str}: {val_str},')
        lines.append(f'{ind}}}')
        return "\n".join(lines)

    elif isinstance(obj, list):
        if not obj:
            return "[]"
        if all(isinstance(x, (int, float, str, bool, type(None))) for x in obj):
            # Simple list - one line
            return repr(obj)
        # Complex list - multi-line
        lines = ["["]
        for item in obj:
            val_str = dict_to_python_literal(item, indent + 1)
            lines.append(f'{ind}    {val_str},')
        lines.append(f'{ind}]')
        return "\n".join(lines)

    elif isinstance(obj, str):
        # Escape quotes and newlines
        return repr(obj)

    else:
        # int, float, bool, None
        return repr(obj)


def generate_ssot_wrappers() -> None:
    """Generate src/.../ssot/generated.py from 6 JSON files."""

    print("=" * 60)
    print("SSOT Wrapper Generator - Phase B")
    print("=" * 60)

    # Load all JSON files
    ssot_data = {}
    struct_hashes = {}

    for filename in SSOT_FILES:
        filepath = SSOT_DIR / filename
        print(f"\nLoading: {filepath}")

        if not filepath.exists():
            print(f"  [ERROR] File not found: {filepath}")
            continue

        data = load_json_without_meta(filepath)
        struct_hash = compute_struct_hash(data)

        # Store data with key = filename without extension
        key = filename.replace(".json", "").upper()
        ssot_data[key] = data
        struct_hashes[key] = struct_hash

        print(f"  [OK] Loaded: {len(json.dumps(data))} bytes")
        print(f"  [HASH] Struct Hash: {struct_hash[:16]}...")

    # Generate Python code
    print(f"\n{'=' * 60}")
    print(f"Generating: {OUTPUT_FILE}")
    print(f"{'=' * 60}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Header
        f.write('"""\n')
        f.write("SSOT Generated Constants\n\n")
        f.write("WARNING: This file is AUTO-GENERATED.\n")
        f.write("Do NOT edit manually. Run scripts/generate_ssot_wrappers.py instead.\n\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Source: {SSOT_DIR}\n")
        f.write(f"Files: {len(SSOT_FILES)}\n\n")
        f.write("LAW-02: SSOT Single Source - No duplication\n")
        f.write("LAW-03: No Hardcoding - Import from here only\n")
        f.write('"""\n\n')

        f.write("from typing import Dict, List, Any\n\n")
        f.write("# SSOT Version\n")
        f.write('SSOT_VERSION = "1.0.0"\n\n')

        # Struct hashes
        f.write("# Structural Hashes (meta-excluded, sorted)\n")
        f.write("# Used for SSOT-Hash Gate in CI\n")
        f.write("SSOT_STRUCT_HASHES: Dict[str, str] = {\n")
        for key, hash_val in struct_hashes.items():
            f.write(f'    "{key}": "{hash_val}",\n')
        f.write("}\n\n")

        # Generate constants for each JSON
        for key, data in ssot_data.items():
            f.write(f"# {'=' * 56}\n")
            f.write(f"# {key}\n")
            f.write(f"# {'=' * 56}\n\n")

            # Generate as typed constant
            f.write(f"{key}: Dict[str, Any] = ")
            f.write(dict_to_python_literal(data, indent=0))
            f.write("\n\n")

        # Footer
        f.write("# All SSOT data in one dict\n")
        f.write("ALL_SSOT: Dict[str, Dict[str, Any]] = {\n")
        for key in ssot_data.keys():
            f.write(f'    "{key}": {key},\n')
        f.write("}\n")

    print(f"[OK] Generated: {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size:,} bytes")

    # Save struct hashes to evidence
    evidence_file = Path("out/evidence/SSOT_STRUCT_HASH.txt")
    evidence_file.parent.mkdir(parents=True, exist_ok=True)

    with open(evidence_file, "w", encoding="utf-8") as f:
        f.write("# SSOT Structural Hashes (meta-excluded, sorted)\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        for key, hash_val in struct_hashes.items():
            f.write(f"{hash_val}  {key}\n")

    print(f"[OK] Evidence: {evidence_file}")

    print(f"\n{'=' * 60}")
    print("[OK] SSOT Wrapper Generation COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    generate_ssot_wrappers()
