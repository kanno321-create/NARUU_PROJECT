#!/bin/bash
# Supabase CLI를 통한 데이터베이스 초기화

SUPABASE_URL="https://cgqukhmqnndwdbmkmjrn.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNncXVraG1xbm5kd2RibWttanJuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTIwNTkyMSwiZXhwIjoyMDc0NzgxOTIxfQ.-olqMJ5sx_LofEGqlePOMK0MnFJT-LLg3_ll0IR3yj4"
DB_URL="postgresql://postgres:rhkdskatit1@db.cgqukhmqnndwdbmkmjrn.supabase.co:5432/postgres"

echo "[*] Connecting to Supabase database..."

psql "$DB_URL" << 'SQL'
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
    spec JSONB NOT NULL DEFAULT '{}'::jsonb,
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
CREATE INDEX idx_catalog_items_spec ON shared.catalog_items USING GIN(spec);

-- 5. Disable RLS
ALTER TABLE shared.catalog_items DISABLE ROW LEVEL SECURITY;

-- 6. Grant permissions
GRANT ALL ON shared.catalog_items TO postgres, anon, authenticated, service_role;

-- 7. Verify
SELECT 'Table created successfully' as status;
SELECT conname, contype FROM pg_constraint WHERE conrelid = 'shared.catalog_items'::regclass;
SQL

echo "[OK] Database reset complete"
