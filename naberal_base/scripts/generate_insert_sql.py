#!/usr/bin/env python3
"""Generate INSERT SQL for knowledge files"""
import json
from pathlib import Path

KNOWLEDGE_DIR = Path("knowledge_consolidation/output")

def generate_sql():
    """Generate INSERT SQL"""

    with open('scripts/insert_knowledge.sql', 'w', encoding='utf-8') as sql_file:
        sql_file.write("-- Insert knowledge data into shared.catalog_items\n\n")

        # Load breakers (first 20 items for test)
        with open(KNOWLEDGE_DIR / 'breakers.json', 'r', encoding='utf-8') as f:
            breakers_data = json.load(f)

        sql_file.write("-- Breakers\n")
        for i, item in enumerate(breakers_data['catalog']['items'][:20]):
            spec = json.dumps({
                'model': item['model'],
                'brand': item['brand'],
                'poles': item['poles'],
                'frame_AF': item.get('frame_AF'),
                'size_mm': item.get('size_mm', []),
            }).replace("'", "''")

            meta = json.dumps({'source': 'breakers.json'}).replace("'", "''")

            sku = f"{item['brand']}-{item['model']}"
            name = f"{item['brand']} {item['model']} {item['poles']}P {item.get('frame_AF')}AF"

            sql_file.write(f"""
INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', '{sku}', '{name}', '{spec}'::jsonb, 0.0, 'KRW', true, '{meta}'::jsonb)
ON CONFLICT (sku) DO NOTHING;
""")

        # Load enclosures (first 20 items)
        with open(KNOWLEDGE_DIR / 'enclosures.json', 'r', encoding='utf-8') as f:
            enclosures_data = json.load(f)

        sql_file.write("\n-- Enclosures\n")
        # enclosures.json has different structure
        items = enclosures_data.get('catalog', {}).get('items', enclosures_data.get('items', []))
        for item in items[:20]:
            spec = json.dumps({
                'width': item.get('width'),
                'height': item.get('height'),
                'depth': item.get('depth'),
                'type': item.get('type'),
                'material': item.get('material'),
            }).replace("'", "''")

            meta = json.dumps({'source': 'enclosures.json'}).replace("'", "''")

            sku = item.get('sku', '')
            name = f"{sku} {item.get('type', '')} {item.get('material', '')}"
            price = item.get('price', 0.0)

            sql_file.write(f"""
INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('enclosure', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta}'::jsonb)
ON CONFLICT (sku) DO NOTHING;
""")

        # Load accessories
        with open(KNOWLEDGE_DIR / 'accessories.json', 'r', encoding='utf-8') as f:
            accessories_data = json.load(f)

        sql_file.write("\n-- Accessories (Magnets)\n")
        magnets_items = accessories_data.get('magnets', {}).get('items', accessories_data.get('magnets', {}).get('catalog', []))
        for item in magnets_items[:10]:
            spec = json.dumps({
                'capacity': item['capacity'],
                'size_mm': item.get('size_mm', []),
                'type': 'magnet',
            }).replace("'", "''")

            meta = json.dumps({'source': 'accessories.json', 'bundle_required': True}).replace("'", "''")

            sku = f"MC-{item['capacity']}"
            name = f"Magnet MC-{item['capacity']} {item['capacity']}A"
            price = item.get('price', 0.0)

            sql_file.write(f"""
INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('accessory', '{sku}', '{name}', '{spec}'::jsonb, {price}, 'KRW', true, '{meta}'::jsonb)
ON CONFLICT (sku) DO NOTHING;
""")

    print("[OK] Generated scripts/insert_knowledge.sql")
    print("[*] You can run this SQL in Supabase Dashboard SQL Editor")

if __name__ == "__main__":
    generate_sql()
