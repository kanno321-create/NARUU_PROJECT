#!/usr/bin/env python3
"""Simple Supabase Schema Deployment

Requires environment variables:
  DB_PASSWORD  - PostgreSQL password (required)
  DB_HOST      - Database host (required)
  DB_USER      - Database user (default: postgres)
  DB_PORT      - Database port (default: 5432)
  DB_NAME      - Database name (default: postgres)
"""
import os
import psycopg2
from pathlib import Path

DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD must be set")
if not DB_HOST:
    raise RuntimeError("DB_HOST must be set")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Read schema
schema_sql = Path('db/schema.sql').read_text(encoding='utf-8')

print(f"[*] Schema size: {len(schema_sql)} bytes")
print("[*] Connecting to Supabase...")

try:
    conn = psycopg2.connect(DB_URL, connect_timeout=10)
    cur = conn.cursor()

    print("[*] Executing schema SQL...")
    cur.execute(schema_sql)
    conn.commit()

    print("[OK] Schema deployed!")

    # Verify
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('estimator', 'shared')
        ORDER BY table_schema, table_name
    """)

    tables = cur.fetchall()
    print(f"\n[*] Deployed Tables ({len(tables)}):")
    for schema, table in tables:
        print(f"  [OK] {schema}.{table}")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Deployment complete!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
