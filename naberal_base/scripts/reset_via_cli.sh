#!/bin/bash
# Supabase CLI를 통한 데이터베이스 초기화
#
# Required environment variables:
#   DB_PASSWORD    - PostgreSQL password
#   DB_HOST        - Database host
#   SUPABASE_URL   - Supabase project URL
#   SUPABASE_KEY   - Supabase service role key

set -euo pipefail

if [ -z "${DB_PASSWORD:-}" ]; then
    echo "[ERROR] DB_PASSWORD not set"
    exit 1
fi

if [ -z "${DB_HOST:-}" ]; then
    echo "[ERROR] DB_HOST not set"
    exit 1
fi

if [ -z "${SUPABASE_URL:-}" ]; then
    echo "[ERROR] SUPABASE_URL not set"
    exit 1
fi

if [ -z "${SUPABASE_KEY:-}" ]; then
    echo "[ERROR] SUPABASE_KEY not set"
    exit 1
fi

DB_USER="${DB_USER:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

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
