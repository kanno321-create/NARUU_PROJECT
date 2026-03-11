-- Check existing schema in NABERAL Supabase project
-- Run this in Supabase SQL Editor

-- 1. Check all user tables
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'auth', 'storage', 'extensions', 'graphql_public', 'realtime', 'supabase_functions', 'supabase_migrations')
ORDER BY schemaname, tablename;

-- 2. Check all indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'auth', 'storage', 'extensions', 'graphql_public', 'realtime', 'supabase_functions', 'supabase_migrations')
ORDER BY schemaname, tablename, indexname;

-- 3. Check table row counts
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- 4. Check if specific tables exist
SELECT
    table_name,
    CASE WHEN EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = t.table_name
    ) THEN 'EXISTS' ELSE 'NOT EXISTS' END as status
FROM (
    VALUES
        ('customers'),
        ('quotes'),
        ('quote_items'),
        ('panels'),
        ('breakers'),
        ('documents'),
        ('catalog_items'),
        ('evidence_blobs')
) AS t(table_name);
