#!/usr/bin/env python3
"""Simple Supabase Schema Deployment"""
import psycopg2
from pathlib import Path

# Direct connection string
DB_URL = "postgresql://postgres:rhkdskatit1@db.jijifnzcoxglafvjltwn.supabase.co:5432/postgres"

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
