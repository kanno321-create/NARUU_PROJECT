#!/usr/bin/env python3
"""Load knowledge via raw SQL (bypass PostgREST cache)"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv('.env.supabase')

KNOWLEDGE_DIR = Path("knowledge_consolidation/output")
DB_URL = os.getenv('SUPABASE_DB_URL')

def load_all():
    """Load all knowledge files"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Load breakers
    with open(KNOWLEDGE_DIR / 'breakers.json', 'r', encoding='utf-8') as f:
        breakers_data = json.load(f)

    breakers_items = []
    for item in breakers_data['catalog']['items'][:10]:  # Test with 10 items first
        breakers_items.append((
            'breaker',
            f"{item['brand']}-{item['model']}",
            f"{item['brand']} {item['model']} {item['poles']}P {item.get('frame_AF')}AF",
            json.dumps({
                'model': item['model'],
                'brand': item['brand'],
                'poles': item['poles'],
                'frame_AF': item.get('frame_AF'),
            }),
            0.0,
            'KRW',
            True,
            json.dumps({'source': 'breakers.json'})
        ))

    # Insert
    execute_values(
        cur,
        """
        INSERT INTO shared.catalog_items
        (kind, sku, name, spec, unit_price, currency, is_active, meta)
        VALUES %s
        ON CONFLICT (sku) DO NOTHING
        """,
        breakers_items
    )

    conn.commit()
    print(f"[OK] Loaded {len(breakers_items)} breakers")

    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        load_all()
        print("[SUCCESS] Knowledge loaded")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
