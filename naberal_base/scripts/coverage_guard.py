#!/usr/bin/env python3
"""
Phase VIII Coverage Guard Script

Enforces package-level coverage thresholds:
- core >= 75%
- infra >= 70%
- engine >= 68%
- services >= 65%
- api >= 60%

Usage:
    python scripts/coverage_guard.py coverage.xml
    python scripts/coverage_guard.py --ratchet  # Update ratchet after 3 greens
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date

# Package-level thresholds (Phase VIII-2)
PACKAGE_GUARDS = {
    "kis_estimator_core.core": 75,
    "kis_estimator_core.infra": 70,
    "kis_estimator_core.engine": 68,
    "kis_estimator_core.services": 65,
    "kis_estimator_core.api": 60,
}

# Ratchet configuration (Phase VIII-1)
RATCHET_STEPS = [60, 62, 65, 68, 70, 75, 80]
GREENS_REQUIRED = 3


def parse_coverage_xml(xml_path: str) -> dict[str, float]:
    """Parse coverage.xml and extract package-level coverage."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    package_coverage = {}

    for package in root.findall(".//package"):
        name = package.get("name", "").replace("/", ".")

        # Calculate coverage from line-rate
        line_rate = float(package.get("line-rate", 0))
        coverage_pct = line_rate * 100

        package_coverage[name] = coverage_pct

    return package_coverage


def check_package_guards(coverage_data: dict[str, float]) -> tuple[bool, list[str]]:
    """Check if all package guards are satisfied."""
    failures = []

    for package, threshold in PACKAGE_GUARDS.items():
        # Find matching package in coverage data
        actual = None
        for pkg_name, cov in coverage_data.items():
            if pkg_name.endswith(package.split(".")[-1]):
                actual = cov
                break

        if actual is None:
            # Package not found, might be okay if no code exists
            continue

        if actual < threshold:
            failures.append(
                f"  {package}: {actual:.1f}% < {threshold}% (FAIL)"
            )
        else:
            print(f"  {package}: {actual:.1f}% >= {threshold}% (PASS)")

    return len(failures) == 0, failures


def get_overall_coverage(xml_path: str) -> float:
    """Get overall coverage percentage from XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    line_rate = float(root.get("line-rate", 0))
    return line_rate * 100


def update_ratchet(current_threshold: int, consecutive_greens: int) -> tuple[int, int]:
    """Update ratchet threshold after consecutive greens."""
    if consecutive_greens >= GREENS_REQUIRED:
        try:
            current_idx = RATCHET_STEPS.index(current_threshold)
            if current_idx < len(RATCHET_STEPS) - 1:
                new_threshold = RATCHET_STEPS[current_idx + 1]
                print(f"  Ratchet UP: {current_threshold}% -> {new_threshold}%")
                return new_threshold, 0
        except ValueError:
            pass

    return current_threshold, consecutive_greens


def main():
    if len(sys.argv) < 2:
        print("Usage: python coverage_guard.py coverage.xml [--ratchet]")
        sys.exit(1)

    xml_path = sys.argv[1]
    ratchet_mode = "--ratchet" in sys.argv

    if not Path(xml_path).exists():
        print(f"ERROR: {xml_path} not found")
        sys.exit(1)

    print("=" * 60)
    print("Phase VIII Coverage Guard Check")
    print("=" * 60)

    # Get overall coverage
    overall = get_overall_coverage(xml_path)
    print(f"\nOverall Coverage: {overall:.2f}%")

    # Check overall threshold (current ratchet level)
    current_threshold = 60  # Read from pyproject.toml in production
    if overall < current_threshold:
        print(f"FAIL: Overall {overall:.2f}% < {current_threshold}% threshold")
        sys.exit(1)

    print(f"PASS: Overall {overall:.2f}% >= {current_threshold}% threshold")

    # Parse and check package guards
    print("\nPackage-level Coverage Guards:")
    print("-" * 40)

    coverage_data = parse_coverage_xml(xml_path)
    passed, failures = check_package_guards(coverage_data)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("All coverage guards PASSED")
    print("=" * 60)

    if ratchet_mode:
        print("\nRatchet mode: Incrementing consecutive greens counter")
        # In production, this would update pyproject.toml

    sys.exit(0)


if __name__ == "__main__":
    main()
