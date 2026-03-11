#!/usr/bin/env python3
"""
Supabase Database Reset via psycopg2
"""
import psycopg2
import sys

DB_URL = "postgresql://postgres:rhkdskatit1@db.cgqukhmqnndwdbmkmjrn.supabase.co:5432/postgres"

RESET_SQL = """
-- 1. Drop existing tables
DROP TABLE IF EXISTS shared.catalog_items CASCADE;
DROP TABLE IF EXISTS public.catalog_items CASCADE;

-- 2. Create schema
CREATE SCHEMA IF NOT EXISTS shared;

-- 3. Create table with UNIQUE constraint
CREATE TABLE shared.catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,
    name TEXT NOT NULL,
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    unit_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'KRW',
    is_active BOOLEAN NOT NULL DEFAULT true,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Create indexes
CREATE INDEX idx_catalog_items_kind ON shared.catalog_items(kind);
CREATE INDEX idx_catalog_items_sku ON shared.catalog_items(sku);
CREATE INDEX idx_catalog_items_specs ON shared.catalog_items USING GIN(specs);

-- 5. Disable RLS
ALTER TABLE shared.catalog_items DISABLE ROW LEVEL SECURITY;

-- 6. Grant permissions
GRANT ALL ON shared.catalog_items TO postgres;
GRANT ALL ON shared.catalog_items TO anon;
GRANT ALL ON shared.catalog_items TO authenticated;
GRANT ALL ON shared.catalog_items TO service_role;
"""

VERIFY_SQL = """
SELECT
    conname AS constraint_name,
    contype AS constraint_type
FROM pg_constraint
WHERE conrelid = 'shared.catalog_items'::regclass;
"""

def main():
    try:
        print("[*] Connecting to Supabase...")
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[*] Executing reset SQL...")
        cursor.execute(RESET_SQL)

        print("[*] Verifying constraints...")
        cursor.execute(VERIFY_SQL)
        constraints = cursor.fetchall()

        print("\n[OK] Database reset complete!")
        print("\nConstraints created:")
        for name, ctype in constraints:
            type_name = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY'}.get(ctype, ctype)
            print(f"  - {name}: {type_name}")

        cursor.close()
        conn.close()

        print("\n[*] Next: Run scripts/insert_knowledge_complete.sql")
        return 0

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
