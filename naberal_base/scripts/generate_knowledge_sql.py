#!/usr/bin/env python3
"""Generate PostgreSQL INSERT statements from knowledge files.

CRITICAL:
- Use actual newlines (not \\n)
- Preserve UTF-8 encoding
- Escape single quotes only
"""

import json
from pathlib import Path
from datetime import datetime

def to_postgres_json(data):
    """Convert Python dict to PostgreSQL-safe JSON string."""
    return json.dumps(data, ensure_ascii=False).replace("'", "''")

def generate_sql():
    """Generate complete SQL file with proper encoding."""

    output_dir = Path("knowledge_consolidation/output")
    sql_file = Path("scripts/insert_knowledge_data.sql")

    # Open with explicit UTF-8 encoding
    with sql_file.open('w', encoding='utf-8', newline='\n') as f:
        # Write header with actual newline
        f.write("-- Knowledge Data Load\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- Total: 276 records (108 breakers + 165 enclosures + 3 metadata)\n\n")

        total_count = 0

        # === BREAKERS ===
        breakers_file = output_dir / "breakers.json"
        with breakers_file.open('r', encoding='utf-8') as bf:
            breakers_data = json.load(bf)

        f.write(f"-- BREAKERS ({len(breakers_data['catalog']['items'])} items)\n\n")

        for item in breakers_data['catalog']['items']:
            sku = f"{item['brand']}-{item['model']}"
            name = f"{item['brand']} {item['model']} {item['poles']}P"

            spec = {
                'model': item['model'],
                'brand': item['brand'],
                'category': item['category'],
                'series': item['series'],
                'type': item['type'],
                'poles': item['poles'],
                'frame_AF': item['frame_AF'],
                'compact': item.get('compact', False),
                'size_mm': item['size_mm'],
                'ampere': item['ampere'],
                'capacity_kA': item.get('capacity_kA')
            }

            # Use first ampere for price
            price = item['price'][0] if isinstance(item['price'], list) else item['price']

            spec_json = to_postgres_json(spec)
            meta_json = to_postgres_json({'source': 'breakers.json'})

            f.write(
                f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) "
                f"VALUES ('breaker', '{sku}', '{name}', '{spec_json}'::jsonb, {price}, 'KRW', true, '{meta_json}'::jsonb) "
                f"ON CONFLICT (sku) DO NOTHING;\n"
            )
            total_count += 1

        f.write("\n")

        # === ENCLOSURES ===
        enclosures_file = output_dir / "enclosures.json"
        with enclosures_file.open('r', encoding='utf-8') as ef:
            enclosures_data = json.load(ef)

        items = enclosures_data['hds_catalog']['standard']['items']
        f.write(f"-- ENCLOSURES ({len(items)} items)\n\n")

        for item in items:
            sku = item['model']
            name = item['model']

            spec = {
                'model': item['model'],
                'category': item['category'],
                'material': item['material'],
                'thickness_mm': item['thickness_mm'],
                'install_location': item['install_location'],
                'size_mm': item['size_mm'],
                'grade': item.get('grade', 'standard')
            }

            spec_json = to_postgres_json(spec)
            meta_json = to_postgres_json({'source': 'enclosures.json'})

            f.write(
                f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) "
                f"VALUES ('enclosure', '{sku}', '{name}', '{spec_json}'::jsonb, {item['price']}, 'KRW', true, '{meta_json}'::jsonb) "
                f"ON CONFLICT (sku) DO NOTHING;\n"
            )
            total_count += 1

        f.write("\n")

        # === METADATA FILES ===
        f.write("-- METADATA (3 items)\n\n")

        metadata_files = [
            ('standards', 'standards.json'),
            ('formulas', 'formulas.json'),
            ('accessory_rules', 'accessories.json')
        ]

        for kind, filename in metadata_files:
            filepath = output_dir / filename
            with filepath.open('r', encoding='utf-8') as mf:
                metadata = json.load(mf)

            # Use meta.version as SKU
            sku = f"{kind}_v{metadata['meta']['version']}"
            name = metadata['meta']['description']

            # Remove meta from spec to avoid duplication
            spec_data = {k: v for k, v in metadata.items() if k != 'meta'}
            spec_json = to_postgres_json(spec_data)
            meta_json = to_postgres_json(metadata['meta'])

            f.write(
                f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) "
                f"VALUES ('{kind}', '{sku}', '{name}', '{spec_json}'::jsonb, 0, 'KRW', true, '{meta_json}'::jsonb) "
                f"ON CONFLICT (sku) DO NOTHING;\n"
            )
            total_count += 1

        f.write("\n")
        f.write(f"-- Total records: {total_count}\n")

    print(f"[OK] Generated {sql_file}")
    print(f"   Total records: {total_count}")
    print(f"   Encoding: UTF-8")
    print(f"   Newlines: LF (\\n)")

    # Verify first 10 lines
    with sql_file.open('r', encoding='utf-8') as f:
        lines = f.readlines()[:10]
        print(f"\n[PREVIEW] First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2}: {line.rstrip()[:80]}")

if __name__ == "__main__":
    generate_sql()
