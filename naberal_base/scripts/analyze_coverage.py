#!/usr/bin/env python
"""Parse coverage.xml and generate coverage audit report."""

import xml.etree.ElementTree as ET

def main():
    tree = ET.parse('coverage.xml')
    root = tree.getroot()

    # Parse all classes (files) from all packages
    modules = []
    for pkg in root.findall('.//package'):
        pkg_name = pkg.get('name', '.')
        for cls in pkg.findall('.//class'):
            filename = cls.get('filename')
            line_rate = float(cls.get('line-rate', 0))
            coverage = line_rate * 100

            # Count lines from line elements
            lines = cls.findall('.//line')
            lines_valid = len(lines)
            lines_covered = sum(1 for line in lines if int(line.get('hits', 0)) > 0)
            uncovered = lines_valid - lines_covered

            # Build full path
            if pkg_name != '.':
                full_path = f"{pkg_name}/{filename}".replace('\\', '/')
            else:
                full_path = filename.replace('\\', '/')

            # Filter for api/ and src/
            if lines_valid > 0 and (full_path.startswith('api/') or full_path.startswith('src/')):
                modules.append({
                    'file': full_path,
                    'coverage': coverage,
                    'lines': lines_valid,
                    'uncovered': uncovered
                })

    # Sort by coverage (ascending)
    modules.sort(key=lambda x: x['coverage'])

    # Print <60% modules
    print('=' * 80)
    print('MODULES WITH <60% COVERAGE (Priority for Improvement)')
    print('=' * 80)

    below_60 = [m for m in modules if m['coverage'] < 60]

    # Categorize by type
    api_modules = [m for m in below_60 if m['file'].startswith('api/')]
    engine_modules = [m for m in below_60 if 'engine/' in m['file']]
    infra_modules = [m for m in below_60 if 'infra/' in m['file']]
    ssot_modules = [m for m in below_60 if 'ssot/' in m['file']]
    other_modules = [m for m in below_60 if m not in api_modules + engine_modules + infra_modules + ssot_modules]

    def print_category(name, modules):
        if not modules:
            return
        print(f"\n{name} ({len(modules)} modules)")
        print('-' * 80)
        for m in modules[:10]:  # Top 10 per category
            print(f"  {m['coverage']:5.1f}% | {m['lines']:4d} lines | {m['uncovered']:4d} miss | {m['file']}")

    print_category("API Layer", api_modules)
    print_category("FIX-4 Engine", engine_modules)
    print_category("Infrastructure", infra_modules)
    print_category("SSOT/Core", ssot_modules)
    print_category("Other", other_modules)

    # Summary
    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print(f"Total modules analyzed: {len(modules)}")
    if len(modules) > 0:
        print(f"Modules <60%: {len(below_60)} ({len(below_60)/len(modules)*100:.1f}%)")
        print(f"Modules 60-80%: {len([m for m in modules if 60 <= m['coverage'] < 80])}")
        print(f"Modules 80%+: {len([m for m in modules if m['coverage'] >= 80])}")
        print(f"Average coverage: {sum(m['coverage'] for m in modules)/len(modules):.2f}%")
    else:
        print("No modules found in coverage data")

    # Top 10 worst modules
    print('\n' + '=' * 80)
    print('TOP 10 CRITICAL MODULES (<60% Coverage, High LOC)')
    print('=' * 80)
    critical = sorted(below_60, key=lambda x: (x['coverage'], -x['lines']))[:10]
    for i, m in enumerate(critical, 1):
        print(f"{i:2d}. {m['coverage']:5.1f}% | {m['lines']:4d} lines | {m['file']}")

if __name__ == '__main__':
    main()
