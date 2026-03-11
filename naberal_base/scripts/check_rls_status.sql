-- ==========================================
-- Check RLS Status for All Tables
-- NABERAL Project Security Audit
-- ==========================================

-- Check RLS status for all tables in public schema
SELECT
    schemaname,
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✓ ENABLED'
        ELSE '✗ UNRESTRICTED'
    END as rls_status,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY
    CASE WHEN rowsecurity = true THEN 1 ELSE 0 END,
    tablename;

-- Count UNRESTRICTED tables
SELECT
    COUNT(CASE WHEN rowsecurity = false THEN 1 END) as unrestricted_count,
    COUNT(CASE WHEN rowsecurity = true THEN 1 END) as enabled_count,
    COUNT(*) as total_tables
FROM pg_tables
WHERE schemaname = 'public';

-- List all RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Check if specific tables have RLS enabled
SELECT
    t.table_name,
    CASE
        WHEN pt.rowsecurity = true THEN '✓ ENABLED'
        ELSE '✗ UNRESTRICTED'
    END as status
FROM (
    VALUES
        ('phase_balance'),
        ('quote_summary'),
        ('customers'),
        ('quotes'),
        ('quote_items'),
        ('panels'),
        ('breakers'),
        ('documents'),
        ('catalog_items'),
        ('evidence_blobs'),
        ('sse_events'),
        ('audit_logs'),
        ('validation_rules')
) AS t(table_name)
LEFT JOIN pg_tables pt ON pt.tablename = t.table_name AND pt.schemaname = 'public'
ORDER BY
    CASE WHEN pt.rowsecurity = true THEN 1 ELSE 0 END,
    t.table_name;
