#!/usr/bin/env python3
"""
Generate COMPLETE INSERT SQL for Supabase - FIXED VERSION
Properly handles PostgreSQL JSON escaping
"""
import json
from pathlib import Path

KNOWLEDGE_DIR = Path('knowledge_consolidation/output')

def to_postgres_json(data):
    """Convert Python dict to PostgreSQL-safe JSON"""
    return json.dumps(data, ensure_ascii=False).replace("'", "''")

def escape_sql(text):
    """Escape single quotes for SQL"""
    return str(text).replace("'", "''")

def main():
    total = 0

    with open('scripts/insert_knowledge_complete.sql', 'w', encoding='utf-8') as f:
        f.write("-- COMPLETE Knowledge Data Load\\n\\n")

        # 1. Breakers
        print("[*] Breakers...")
        with open(KNOWLEDGE_DIR / 'breakers.json', 'r', encoding='utf-8') as bf:
            breakers = json.load(bf)

        items = breakers['catalog']['items']
        f.write(f"-- BREAKERS ({len(items)} items)\\n\\n")

        for item in items:
            spec = to_postgres_json({
                'model': item['model'],
                'brand': item['brand'],
                'category': item['category'],
                'series': item['series'],
                'type': item['type'],
                'poles': item['poles'],
                'frame_AF': item.get('frame_AF'),
                'compact': item.get('compact', False),
                'size_mm': item.get('size_mm', []),
                'ampere': item.get('ampere', []),
                'capacity_kA': item.get('capacity_kA'),
            })

            meta = to_postgres_json({"source": "breakers.json"})
            sku = f"{item['brand']}-{escape_sql(item['model'])}"
            name = f"{item['brand']} {escape_sql(item['model'])} {item['poles']}P"
            price = item.get('price', 0)
            if isinstance(price, list):
                price = price[0]

            f.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('breaker', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta}'::jsonb) ON CONFLICT (sku) DO NOTHING;\\n")

        total += len(items)
        print(f"[OK] {len(items)} breakers")

        # 2. Enclosures
        print("[*] Enclosures...")
        with open(KNOWLEDGE_DIR / 'enclosures.json', 'r', encoding='utf-8') as ef:
            enclosures = json.load(ef)

        items = enclosures.get('hds_catalog', {}).get('standard', {}).get('items', [])
        f.write(f"\\n-- ENCLOSURES ({len(items)} items)\\n\\n")

        for item in items:
            spec = to_postgres_json({
                'model': item['model'],
                'category': item['category'],
                'material': item['material'],
                'thickness_mm': item.get('thickness_mm'),
                'install_location': item.get('install_location'),
                'size_mm': item.get('size_mm', []),
                'custom_required': item.get('custom_required', False),
                'grade': item.get('grade'),
            })

            meta = to_postgres_json({"source": "enclosures.json"})
            sku = f"ENC-{escape_sql(item['model'])}"
            name = f"{escape_sql(item['model'])} {item['material']}"
            price = item.get('price', 0)

            f.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('enclosure', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta}'::jsonb) ON CONFLICT (sku) DO NOTHING;\\n")

        total += len(items)
        print(f"[OK] {len(items)} enclosures")

        # 3. Accessories
        print("[*] Accessories...")
        with open(KNOWLEDGE_DIR / 'accessories.json', 'r', encoding='utf-8') as af:
            acc = json.load(af)

        f.write("\\n-- ACCESSORIES\\n\\n")

        spec = to_postgres_json({
            'magnets': acc.get('magnets', {}),
            'timers': acc.get('timers', {}),
            'bom_bundles': acc.get('bom_bundles', {}),
            'layout_rules': acc.get('layout_rules', {}),
            'magnet_layout': acc.get('magnet_layout', {}),
            'pbl_dependency': acc.get('pbl_dependency', {}),
        })

        meta = to_postgres_json({"source": "accessories.json", "signed_by": "CEO"})
        f.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('accessory_rules', 'ACC-RULES-V1.0.0', 'Accessories Rules v1.0.0 (CEO Signed)', '{spec}'::jsonb, 0, 'KRW', true, '{meta}'::jsonb) ON CONFLICT (sku) DO NOTHING;\\n")

        total += 1
        print("[OK] 1 accessory rule set")

        # 4. Formulas
        print("[*] Formulas...")
        with open(KNOWLEDGE_DIR / 'formulas.json', 'r', encoding='utf-8') as ff:
            formulas = json.load(ff)

        f.write("\\n-- FORMULAS\\n\\n")

        spec = to_postgres_json({
            'enclosure': formulas.get('enclosure', {}),
            'busbar': formulas.get('busbar', {}),
        })

        meta = to_postgres_json({"source": "formulas.json"})
        f.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('formulas', 'FORMULA-V1.0.0', 'Calculation Formulas v1.0.0', '{spec}'::jsonb, 0, 'KRW', true, '{meta}'::jsonb) ON CONFLICT (sku) DO NOTHING;\\n")

        total += 1
        print("[OK] 1 formula set")

        # 5. Standards
        print("[*] Standards...")
        with open(KNOWLEDGE_DIR / 'standards.json', 'r', encoding='utf-8') as sf:
            standards = json.load(sf)

        f.write("\\n-- STANDARDS\\n\\n")

        spec = to_postgres_json({
            'IEC61439': standards.get('IEC61439', {}),
            'KS_C_4510': standards.get('KS_C_4510', {}),
        })

        meta = to_postgres_json({"source": "standards.json"})
        f.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('standards', 'STANDARDS-V1.0.0', 'IEC61439 + KS C 4510', '{spec}'::jsonb, 0, 'KRW', true, '{meta}'::jsonb) ON CONFLICT (sku) DO NOTHING;\\n")

        total += 1
        print("[OK] 1 standard set")

        f.write(f"\\n-- TOTAL: {total} records\\n")

    print(f"\\n[OK] SQL Generated: {total} total records")
    print("[*] File: scripts/insert_knowledge_complete.sql")

if __name__ == '__main__':
    main()
