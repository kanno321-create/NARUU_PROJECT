#!/usr/bin/env python3
"""
Load Knowledge Files to Supabase
Loads consolidated knowledge from knowledge_consolidation/output/ into shared.catalog_items
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv('.env.supabase')

KNOWLEDGE_DIR = Path("knowledge_consolidation/output")

def load_breakers(supabase):
    """Load breakers into catalog_items"""
    file_path = KNOWLEDGE_DIR / "breakers.json"

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('catalog', {}).get('items', [])
    catalog_items = []

    for item in items:
        catalog_item = {
            'kind': 'breaker',
            'sku': f"{item['brand']}-{item['model']}",
            'name': f"{item['brand']} {item['model']} {item['poles']}P {item.get('frame_AF')}AF",
            'spec': {
                'model': item['model'],
                'brand': item['brand'],
                'category': item.get('category'),
                'poles': item['poles'],
                'frame_AF': item.get('frame_AF'),
                'size_mm': item.get('size_mm', []),
                'type': item.get('type'),
                'series': item.get('series'),
            },
            'unit_price': 0.0,
            'currency': 'KRW',
            'is_active': True,
            'meta': {
                'compact': item.get('compact', False),
                'source': 'breakers.json',
            }
        }
        catalog_items.append(catalog_item)

    # Insert
    response = supabase.table('catalog_items').upsert(catalog_items, on_conflict='sku').execute()
    print(f"  [OK] Loaded {len(catalog_items)} breakers")
    return len(catalog_items)


def load_enclosures(supabase):
    """Load enclosures into catalog_items"""
    file_path = KNOWLEDGE_DIR / "enclosures.json"

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('catalog', {}).get('items', [])
    catalog_items = []

    for item in items:
        sku = item.get('sku', '')

        catalog_item = {
            'kind': 'enclosure',
            'sku': sku,
            'name': f"{sku} {item.get('type', '')} {item.get('material', '')}",
            'spec': {
                'width': item.get('width'),
                'height': item.get('height'),
                'depth': item.get('depth'),
                'type': item.get('type'),
                'material': item.get('material'),
                'thickness': item.get('thickness'),
            },
            'unit_price': item.get('price', 0.0),
            'currency': 'KRW',
            'is_active': True,
            'meta': {
                'ip_rating': item.get('ip_rating'),
                'source': 'enclosures.json',
            }
        }
        catalog_items.append(catalog_item)

    # Insert
    response = supabase.table('catalog_items').upsert(catalog_items, on_conflict='sku').execute()
    print(f"  [OK] Loaded {len(catalog_items)} enclosures")
    return len(catalog_items)


def load_accessories(supabase):
    """Load accessories into catalog_items"""
    file_path = KNOWLEDGE_DIR / "accessories.json"

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    catalog_items = []

    # Load magnets
    magnets = data.get('magnets', {}).get('catalog', [])
    for item in magnets:
        catalog_item = {
            'kind': 'accessory',
            'sku': f"MC-{item['capacity']}",
            'name': f"Magnet MC-{item['capacity']} {item['capacity']}A",
            'spec': {
                'capacity': item['capacity'],
                'size_mm': item.get('size_mm', []),
                'type': 'magnet',
            },
            'unit_price': item.get('price', 0.0),
            'currency': 'KRW',
            'is_active': True,
            'meta': {
                'bundle_required': True,
                'source': 'accessories.json',
            }
        }
        catalog_items.append(catalog_item)

    # Load timers
    timers = data.get('timers', {}).get('catalog', [])
    for item in timers:
        catalog_item = {
            'kind': 'accessory',
            'sku': f"TIMER-{item['type']}",
            'name': f"Timer {item['type']}",
            'spec': {
                'type': item['type'],
                'size_mm': item.get('size_mm', []),
            },
            'unit_price': item.get('price', 0.0),
            'currency': 'KRW',
            'is_active': True,
            'meta': {
                'bundle_required': True,
                'source': 'accessories.json',
            }
        }
        catalog_items.append(catalog_item)

    # Insert
    response = supabase.table('catalog_items').upsert(catalog_items, on_conflict='sku').execute()
    print(f"  [OK] Loaded {len(catalog_items)} accessories")
    return len(catalog_items)


def main():
    """Main function"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY not found")
        sys.exit(1)

    print(f"[*] Loading knowledge files to Supabase")
    print(f"[*] Target: {supabase_url}")
    print()

    try:
        supabase = create_client(supabase_url, supabase_key)

        print("[*] Loading knowledge files...")
        breakers_count = load_breakers(supabase)
        enclosures_count = load_enclosures(supabase)
        accessories_count = load_accessories(supabase)

        total = breakers_count + enclosures_count + accessories_count

        print(f"\n[SUCCESS] Total: {total} items loaded")
        print(f"  - Breakers: {breakers_count}")
        print(f"  - Enclosures: {enclosures_count}")
        print(f"  - Accessories: {accessories_count}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
