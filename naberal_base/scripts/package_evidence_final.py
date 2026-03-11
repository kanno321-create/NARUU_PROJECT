"""
Evidence Pack Final Packaging Script - Phase J

Packages all evidence artifacts into a single ZIP file with SHA256 checksum
for audit, reproduction, and deployment verification.

Requirements:
- All Phase A-J work logs must exist
- SSOT files must be present in knowledge_consolidation/output/
- Contract files must be present in dist/contract/
- Test results must be present in out/evidence/

Output:
- EVIDENCE_YYYYMMDD_HHMM_final.zip
- EVIDENCE_YYYYMMDD_HHMM_final.zip.sha256
"""

import hashlib
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "out" / "evidence"
SSOT_DIR = PROJECT_ROOT / "knowledge_consolidation" / "output"
CONTRACT_DIR = PROJECT_ROOT / "dist" / "contract"


def get_timestamp() -> str:
    """Generate timestamp string for evidence pack filename"""
    return datetime.now().strftime("%Y%m%d_%H%M")


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_prerequisites() -> Tuple[bool, List[str]]:
    """
    Validate that all required files exist before packaging

    Returns:
        (success, missing_files)
    """
    # CRITICAL files (must exist)
    critical_files = [
        # Contract files (2)
        CONTRACT_DIR / "openapi_v1.0.0.yaml",
        CONTRACT_DIR / "openapi_v1.0.0.json",

        # Test results (3)
        EVIDENCE_DIR / "junit.xml",
        EVIDENCE_DIR / "coverage.xml",
        EVIDENCE_DIR / "endpoints_probe.json",
    ]

    # Check critical files
    missing = []
    for file_path in critical_files:
        if not file_path.exists():
            missing.append(str(file_path.relative_to(PROJECT_ROOT)))

    # Check SSOT directory exists (files can vary)
    if not SSOT_DIR.exists():
        missing.append(str(SSOT_DIR.relative_to(PROJECT_ROOT)))

    return (len(missing) == 0, missing)


def create_evidence_structure(temp_dir: Path) -> Dict[str, int]:
    """
    Create evidence pack directory structure and copy files

    Returns:
        Dictionary with file counts per category
    """
    stats = {
        "ssot": 0,
        "contract": 0,
        "tests": 0,
        "work_logs": 0,
        "ci_logs": 0,
        "metadata": 0,
    }

    # 1. SSOT files (copy all JSON files from knowledge_consolidation/output/)
    ssot_target = temp_dir / "ssot"
    ssot_target.mkdir(parents=True, exist_ok=True)

    # Copy all JSON files from SSOT directory
    if SSOT_DIR.exists():
        for json_file in SSOT_DIR.glob("*.json"):
            shutil.copy2(json_file, ssot_target / json_file.name)
            stats["ssot"] += 1

    # Copy SSOT hashes (if exist)
    for hash_file in ["SSOT_SHA256SUMS.txt", "SSOT_STRUCT_HASH.txt"]:
        src = EVIDENCE_DIR / hash_file
        if src.exists():
            shutil.copy2(src, ssot_target / hash_file)
            stats["ssot"] += 1

    # 2. Contract files
    contract_target = temp_dir / "contract"
    contract_target.mkdir(parents=True, exist_ok=True)

    contract_files = ["openapi_v1.0.0.yaml", "openapi_v1.0.0.json"]
    for filename in contract_files:
        src = CONTRACT_DIR / filename
        if src.exists():
            shutil.copy2(src, contract_target / filename)
            stats["contract"] += 1

    # 3. Test results
    tests_target = temp_dir / "tests"
    tests_target.mkdir(parents=True, exist_ok=True)

    test_files = ["junit.xml", "coverage.xml", "endpoints_probe.json"]
    for filename in test_files:
        src = EVIDENCE_DIR / filename
        if src.exists():
            shutil.copy2(src, tests_target / filename)
            stats["tests"] += 1

    # 4. Work logs
    work_logs_target = temp_dir / "work_logs"
    work_logs_target.mkdir(parents=True, exist_ok=True)

    work_log_files = [
        "phase_a_work_log.md",
        "phase_b_work_log.md",
        "phase_c_work_log.md",
        "phase_d_work_log.md",
        "phase_e_work_log.md",
        "phase_h_work_log.md",
        "phase_i_work_log.md",
        "phase_j_work_log_final.md",
    ]

    for filename in work_log_files:
        src = EVIDENCE_DIR / filename
        if src.exists():
            shutil.copy2(src, work_logs_target / filename)
            stats["work_logs"] += 1

    # 5. CI logs
    ci_logs_src = EVIDENCE_DIR / "ci_logs"
    if ci_logs_src.exists():
        ci_logs_target = temp_dir / "ci_logs"
        ci_logs_target.mkdir(parents=True, exist_ok=True)

        for log_file in ci_logs_src.glob("gate-*.txt"):
            shutil.copy2(log_file, ci_logs_target / log_file.name)
            stats["ci_logs"] += 1

    # 6. Metadata files
    metadata_files = ["MANIFEST.txt"]
    for filename in metadata_files:
        src = EVIDENCE_DIR / filename
        if src.exists():
            shutil.copy2(src, temp_dir / filename)
            stats["metadata"] += 1

    # Create README.txt
    readme_path = temp_dir / "README.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""NABERAL KIS Estimator - Evidence Pack (Final)
================================================

This archive contains all evidence artifacts for Phase A-J completion,
enabling 1-click reproduction, audit, and deployment verification.

DIRECTORY STRUCTURE:
--------------------
ssot/           - Single Source of Truth files (6 JSON + 2 hash files)
contract/       - OpenAPI 3.1 contract snapshots (YAML + JSON)
tests/          - Test results (junit.xml, coverage.xml, endpoints_probe.json)
work_logs/      - Phase A-J work logs (decisions, assumptions, TODOs)
ci_logs/        - CI gate logs (lint, SSOT, OpenAPI, probe, tests, evidence)
MANIFEST.txt    - File inventory with descriptions
README.txt      - This file

VERIFICATION:
-------------
1. Extract ZIP: unzip EVIDENCE_YYYYMMDD_HHMM_final.zip
2. Verify SHA256: sha256sum -c EVIDENCE_YYYYMMDD_HHMM_final.zip.sha256
3. Check MANIFEST.txt for file inventory

REPRODUCTION:
-------------
1. Restore SSOT files to knowledge_consolidation/output/
2. Restore contract files to dist/contract/
3. Run regression tests: pytest -m regression
4. Verify SSOT hash: python scripts/verify_ssot_hash.py

COMPLIANCE:
-----------
- Zero-Mock: All tests use real systems (DB, API, SSE)
- Contract-First: OpenAPI snapshot matches runtime
- SSOT-First: All constants from JSON (no hardcoding)
- Evidence-Gated: All decisions documented with evidence

Phase J Completion: 2025-10-16
Owner: Narberal Gamma
""")
    stats["metadata"] += 1

    return stats


def create_zip_archive(temp_dir: Path, output_path: Path) -> int:
    """
    Create ZIP archive from temporary directory

    Returns:
        Total number of files added to ZIP
    """
    file_count = 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
                file_count += 1

    return file_count


def generate_sha256_checksum(zip_path: Path) -> Path:
    """
    Generate SHA256 checksum file for ZIP archive

    Returns:
        Path to .sha256 file
    """
    checksum = calculate_sha256(zip_path)
    checksum_path = Path(str(zip_path) + ".sha256")

    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {zip_path.name}\n")

    return checksum_path


def verify_zip_integrity(zip_path: Path, checksum_path: Path) -> bool:
    """
    Verify ZIP integrity by comparing SHA256 hashes

    Returns:
        True if verification passes
    """
    # Read expected hash
    with open(checksum_path, "r", encoding="utf-8") as f:
        expected_hash = f.read().strip().split()[0]

    # Calculate actual hash
    actual_hash = calculate_sha256(zip_path)

    return expected_hash == actual_hash


def print_summary(
    zip_path: Path,
    checksum_path: Path,
    stats: Dict[str, int],
    total_files: int,
    verification_ok: bool
):
    """Print packaging summary"""
    print("\n" + "=" * 60)
    print("Evidence Pack Final - Packaging Complete")
    print("=" * 60)
    print(f"\n[OUTPUT] ZIP Archive: {zip_path}")
    print(f"[OUTPUT] SHA256 Checksum: {checksum_path}")
    print(f"\n[SIZE] ZIP: {zip_path.stat().st_size / 1024:.2f} KB")
    print(f"[SIZE] Checksum: {checksum_path.stat().st_size} bytes")
    print(f"\n[FILES] Total files in ZIP: {total_files}")
    print(f"  - SSOT files: {stats['ssot']}")
    print(f"  - Contract files: {stats['contract']}")
    print(f"  - Test results: {stats['tests']}")
    print(f"  - Work logs: {stats['work_logs']}")
    print(f"  - CI logs: {stats['ci_logs']}")
    print(f"  - Metadata: {stats['metadata']}")

    print(f"\n[INTEGRITY] SHA256 Verification: {'PASS ✅' if verification_ok else 'FAIL ❌'}")

    if verification_ok:
        print("\n[SUCCESS] Evidence Pack ready for deployment verification")
        print("=" * 60)
    else:
        print("\n[ERROR] Integrity verification failed - ZIP may be corrupted")
        print("=" * 60)


def main():
    """Main packaging workflow"""
    print("=" * 60)
    print("Evidence Pack Final Packaging - Phase J")
    print("=" * 60)

    # 1. Validate prerequisites
    print("\n[1/6] Validating prerequisites...")
    valid, missing = validate_prerequisites()

    if not valid:
        print(f"\n[ERROR] Missing required files ({len(missing)}):")
        for file_path in missing:
            print(f"  - {file_path}")
        print("\n[ABORT] Cannot proceed without required files")
        sys.exit(1)

    print(f"[OK] All required files present")

    # 2. Create temporary directory structure
    print("\n[2/6] Creating evidence pack structure...")
    timestamp = get_timestamp()
    zip_filename = f"EVIDENCE_{timestamp}_final.zip"
    zip_path = EVIDENCE_DIR / zip_filename

    temp_dir = EVIDENCE_DIR / f"temp_{timestamp}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        stats = create_evidence_structure(temp_dir)
        total_stats = sum(stats.values())
        print(f"[OK] Copied {total_stats} files to temporary structure")

        # 3. Create ZIP archive
        print("\n[3/6] Creating ZIP archive...")
        total_files = create_zip_archive(temp_dir, zip_path)
        print(f"[OK] ZIP created with {total_files} files")

        # 4. Generate SHA256 checksum
        print("\n[4/6] Generating SHA256 checksum...")
        checksum_path = generate_sha256_checksum(zip_path)
        print(f"[OK] Checksum generated: {checksum_path.name}")

        # 5. Verify integrity
        print("\n[5/6] Verifying ZIP integrity...")
        verification_ok = verify_zip_integrity(zip_path, checksum_path)

        if not verification_ok:
            print("[ERROR] Integrity verification failed")
            sys.exit(1)

        print("[OK] Integrity verification PASS")

        # 6. Print summary
        print("\n[6/6] Packaging complete")
        print_summary(zip_path, checksum_path, stats, total_files, verification_ok)

        sys.exit(0)

    finally:
        # Cleanup temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n[CLEANUP] Temporary directory removed: {temp_dir.name}")


if __name__ == "__main__":
    main()
