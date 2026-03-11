#!/usr/bin/env python3
"""
Generate COMPLETE INSERT SQL for Supabase from ALL knowledge files
NO MOCKUP - 100% REAL DATA from knowledge_consolidation/output/
"""
import json
from pathlib import Path

KNOWLEDGE_DIR = Path('knowledge_consolidation/output')

def escape_sql(text):
    """Escape single quotes for SQL"""
    return str(text).replace("'", "''")

def generate_complete_sql():
    """Generate COMPLETE SQL with ALL data"""

    total_records = 0

    with open('scripts/insert_knowledge_complete.sql', 'w', encoding='utf-8') as sql_file:
        sql_file.write("-- ══════════════════════════════════════════════════════════════\n")
        sql_file.write("-- COMPLETE Knowledge Data Load (NO MOCKUP)\n")
        sql_file.write("-- Source: knowledge_consolidation/output/*.json\n")
        sql_file.write("-- ══════════════════════════════════════════════════════════════\n\n")

        # ═══ 1. BREAKERS (ALL) ═══
        print("[*] Processing breakers.json...")
        with open(KNOWLEDGE_DIR / 'breakers.json', 'r', encoding='utf-8') as f:
            breakers_data = json.load(f)

        breaker_count = len(breakers_data['catalog']['items'])
        sql_file.write(f"-- ═══ 1. BREAKERS ({breaker_count} items) ═══\n\n")

        for item in breakers_data['catalog']['items']:
            spec = json.dumps({
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
            }, ensure_ascii=False).replace("'", "''")

            sku = f"{item['brand']}-{escape_sql(item['model'])}"
            name = f"{item['brand']} {escape_sql(item['model'])} {item['poles']}P"
            price = item.get('price', 0)
            if isinstance(price, list):
                price = price[0]

            meta_json = '{"source": "breakers.json"}'.replace('"', '\\"')
            sql_file.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('breaker', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta_json}'::jsonb) ON CONFLICT (sku) DO NOTHING;\n")

        total_records += breaker_count
        print(f"[OK] Breakers: {breaker_count} items")

        # ═══ 2. ENCLOSURES (ALL) ═══
        print("[*] Processing enclosures.json...")
        with open(KNOWLEDGE_DIR / 'enclosures.json', 'r', encoding='utf-8') as f:
            enclosures_data = json.load(f)

        enclosure_items = enclosures_data.get('hds_catalog', {}).get('standard', {}).get('items', [])
        enclosure_count = len(enclosure_items)

        sql_file.write(f"\n-- ═══ 2. ENCLOSURES ({enclosure_count} items) ═══\n\n")

        for item in enclosure_items:
            spec = json.dumps({
                'model': item['model'],
                'category': item['category'],
                'material': item['material'],
                'thickness_mm': item.get('thickness_mm'),
                'install_location': item.get('install_location'),
                'size_mm': item.get('size_mm', []),
                'custom_required': item.get('custom_required', False),
                'grade': item.get('grade'),
            }, ensure_ascii=False).replace("'", "''")

            sku = f"ENC-{escape_sql(item['model'])}"
            name = f"{escape_sql(item['model'])} {item['material']}"
            price = item.get('price', 0)

            meta_json = '{"source": "enclosures.json"}'.replace('"', '\\"')
            sql_file.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('enclosure', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta_json}'::jsonb) ON CONFLICT (sku) DO NOTHING;\n")

        total_records += enclosure_count
        print(f"[OK] Enclosures: {enclosure_count} items")

        # ═══ 3. ACCESSORIES ═══
        print("[*] Processing accessories.json...")
        with open(KNOWLEDGE_DIR / 'accessories.json', 'r', encoding='utf-8') as f:
            accessories_data = json.load(f)

        sql_file.write("\n-- ═══ 3. ACCESSORIES (rules and bundles) ═══\n\n")

        acc_spec = json.dumps({
            'magnets': accessories_data.get('magnets', {}),
            'timers': accessories_data.get('timers', {}),
            'bom_bundles': accessories_data.get('bom_bundles', {}),
            'layout_rules': accessories_data.get('layout_rules', {}),
            'magnet_layout': accessories_data.get('magnet_layout', {}),
            'pbl_dependency': accessories_data.get('pbl_dependency', {}),
        }, ensure_ascii=False).replace("'", "''")

        meta_json = '{"source": "accessories.json", "signed_by": "CEO"}'.replace('"', '\\"')
        sql_file.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('accessory_rules', 'ACC-RULES-V1.0.0', 'Accessories Rules v1.0.0 (CEO Signed)', '{acc_spec}'::jsonb, 0, 'KRW', true, '{meta_json}'::jsonb) ON CONFLICT (sku) DO NOTHING;\n")

        total_records += 1
        print("[OK] Accessories: 1 rule set")

        # ═══ 4. FORMULAS ═══
        print("[*] Processing formulas.json...")
        with open(KNOWLEDGE_DIR / 'formulas.json', 'r', encoding='utf-8') as f:
            formulas_data = json.load(f)

        sql_file.write("\n-- ═══ 4. FORMULAS ═══\n\n")

        formula_spec = json.dumps({
            'enclosure': formulas_data.get('enclosure', {}),
            'busbar': formulas_data.get('busbar', {}),
        }, ensure_ascii=False).replace("'", "''")

        meta_json = '{"source": "formulas.json"}'.replace('"', '\\"')
        sql_file.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('formulas', 'FORMULA-V1.0.0', 'Calculation Formulas v1.0.0', '{formula_spec}'::jsonb, 0, 'KRW', true, '{meta_json}'::jsonb) ON CONFLICT (sku) DO NOTHING;\n")

        total_records += 1
        print("[OK] Formulas: 1 formula set")

        # ═══ 5. STANDARDS ═══
        print("[*] Processing standards.json...")
        with open(KNOWLEDGE_DIR / 'standards.json', 'r', encoding='utf-8') as f:
            standards_data = json.load(f)

        sql_file.write("\n-- ═══ 5. STANDARDS ═══\n\n")

        standards_spec = json.dumps({
            'IEC61439': standards_data.get('IEC61439', {}),
            'KS_C_4510': standards_data.get('KS_C_4510', {}),
        }, ensure_ascii=False).replace("'", "''")

        meta_json = '{"source": "standards.json"}'.replace('"', '\\"')
        sql_file.write(f"INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta) VALUES ('standards', 'STANDARDS-V1.0.0', 'IEC61439 + KS C 4510', '{standards_spec}'::jsonb, 0, 'KRW', true, '{meta_json}'::jsonb) ON CONFLICT (sku) DO NOTHING;\n")

        total_records += 1
        print("[OK] Standards: 1 standard set")

        # ═══ SUMMARY ═══
        sql_file.write("\n-- ══════════════════════════════════════════════════════════════\n")
        sql_file.write("-- SUMMARY\n")
        sql_file.write("-- ══════════════════════════════════════════════════════════════\n")
        sql_file.write(f"-- Breakers:     {breaker_count} items\n")
        sql_file.write(f"-- Enclosures:   {enclosure_count} items\n")
        sql_file.write("-- Accessories:  1 rule set (CEO signed)\n")
        sql_file.write("-- Formulas:     1 formula set\n")
        sql_file.write("-- Standards:    1 standard set\n")
        sql_file.write(f"-- TOTAL:        {total_records} records\n")
        sql_file.write("-- ══════════════════════════════════════════════════════════════\n")

    print("\n" + "="*70)
    print("[OK] COMPLETE SQL GENERATED")
    print("="*70)
    print(f"[*] Total Records: {total_records}")
    print(f"   - Breakers:     {breaker_count}")
    print(f"   - Enclosures:   {enclosure_count}")
    print("   - Accessories:  1 rule set")
    print("   - Formulas:     1 set")
    print("   - Standards:    1 set")
    print("="*70)
    print("[*] File: scripts/insert_knowledge_complete.sql")
    print("[*] Execute in Supabase Dashboard SQL Editor")
    print("="*70)

if __name__ == '__main__':
    generate_complete_sql()
