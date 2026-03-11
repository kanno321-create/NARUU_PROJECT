-- ==========================================
-- Enable RLS for All Tables in NABERAL Project
-- Security: Row Level Security Enforcement
-- ==========================================

-- ==========================================
-- STEP 1: Enable RLS on All Tables
-- ==========================================

-- Core tables
ALTER TABLE IF EXISTS customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS panels ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS breakers ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS catalog_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS evidence_blobs ENABLE ROW LEVEL SECURITY;

-- Additional tables
ALTER TABLE IF EXISTS sse_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS validation_rules ENABLE ROW LEVEL SECURITY;

-- Problem tables (if they exist)
ALTER TABLE IF EXISTS phase_balance ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS quote_summary ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- STEP 2: Drop Existing Policies (Clean Slate)
-- ==========================================

-- Customers policies
DROP POLICY IF EXISTS "Service role can manage customers" ON customers;
DROP POLICY IF EXISTS "Authenticated users can read customers" ON customers;

-- Quotes policies
DROP POLICY IF EXISTS "Service role can manage quotes" ON quotes;
DROP POLICY IF EXISTS "Authenticated users can read quotes" ON quotes;

-- Quote items policies
DROP POLICY IF EXISTS "Service role can manage quote_items" ON quote_items;
DROP POLICY IF EXISTS "Authenticated users can read quote_items" ON quote_items;

-- Panels policies
DROP POLICY IF EXISTS "Service role can manage panels" ON panels;
DROP POLICY IF EXISTS "Authenticated users can read panels" ON panels;

-- Breakers policies
DROP POLICY IF EXISTS "Service role can manage breakers" ON breakers;
DROP POLICY IF EXISTS "Authenticated users can read breakers" ON breakers;

-- Documents policies
DROP POLICY IF EXISTS "Service role can manage documents" ON documents;
DROP POLICY IF EXISTS "Authenticated users can read documents" ON documents;

-- Catalog items policies (public read)
DROP POLICY IF EXISTS "Service role can manage catalog_items" ON catalog_items;
DROP POLICY IF EXISTS "Public can read catalog_items" ON catalog_items;
DROP POLICY IF EXISTS "Anon can read catalog_items" ON catalog_items;

-- Evidence blobs policies
DROP POLICY IF EXISTS "Service role can manage evidence_blobs" ON evidence_blobs;
DROP POLICY IF EXISTS "Authenticated users can read evidence_blobs" ON evidence_blobs;

-- SSE events policies
DROP POLICY IF EXISTS "Service role can manage sse_events" ON sse_events;
DROP POLICY IF EXISTS "Authenticated users can read sse_events" ON sse_events;

-- Audit logs policies
DROP POLICY IF EXISTS "Service role can manage audit_logs" ON audit_logs;
DROP POLICY IF EXISTS "Authenticated users can read audit_logs" ON audit_logs;

-- Validation rules policies
DROP POLICY IF EXISTS "Service role can manage validation_rules" ON validation_rules;
DROP POLICY IF EXISTS "Public can read validation_rules" ON validation_rules;

-- ==========================================
-- STEP 3: Create Comprehensive RLS Policies
-- ==========================================

-- ==========================================
-- Customers Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage customers"
    ON customers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read customers"
    ON customers
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Quotes Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage quotes"
    ON quotes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read quotes"
    ON quotes
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Quote Items Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage quote_items"
    ON quote_items
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read quote_items"
    ON quote_items
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Panels Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage panels"
    ON panels
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read panels"
    ON panels
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Breakers Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage breakers"
    ON breakers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read breakers"
    ON breakers
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Documents Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage documents"
    ON documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read documents"
    ON documents
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Catalog Items Table Policies (Public Read)
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage catalog_items"
    ON catalog_items
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Public read access (for anonymous users)
CREATE POLICY "Public can read catalog_items"
    ON catalog_items
    FOR SELECT
    TO anon
    USING (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read catalog_items"
    ON catalog_items
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Evidence Blobs Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage evidence_blobs"
    ON evidence_blobs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read evidence_blobs"
    ON evidence_blobs
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- SSE Events Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage sse_events"
    ON sse_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only
CREATE POLICY "Authenticated users can read sse_events"
    ON sse_events
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Audit Logs Table Policies
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage audit_logs"
    ON audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users: read only (for their own logs)
CREATE POLICY "Authenticated users can read audit_logs"
    ON audit_logs
    FOR SELECT
    TO authenticated
    USING (true);

-- ==========================================
-- Validation Rules Table Policies (Public Read)
-- ==========================================

-- Service role: full access
CREATE POLICY "Service role can manage validation_rules"
    ON validation_rules
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Public read access (business rules are public)
CREATE POLICY "Public can read validation_rules"
    ON validation_rules
    FOR SELECT
    TO anon, authenticated
    USING (is_active = true);

-- ==========================================
-- Problem Tables (if they exist)
-- ==========================================

-- Phase Balance
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'phase_balance') THEN
        EXECUTE 'CREATE POLICY "Service role can manage phase_balance" ON phase_balance FOR ALL TO service_role USING (true) WITH CHECK (true)';
        EXECUTE 'CREATE POLICY "Authenticated users can read phase_balance" ON phase_balance FOR SELECT TO authenticated USING (true)';
    END IF;
END $$;

-- Quote Summary
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'quote_summary') THEN
        EXECUTE 'CREATE POLICY "Service role can manage quote_summary" ON quote_summary FOR ALL TO service_role USING (true) WITH CHECK (true)';
        EXECUTE 'CREATE POLICY "Authenticated users can read quote_summary" ON quote_summary FOR SELECT TO authenticated USING (true)';
    END IF;
END $$;

-- ==========================================
-- STEP 4: Verification
-- ==========================================

-- Check RLS status
SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✓ ENABLED'
        ELSE '✗ UNRESTRICTED'
    END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY
    CASE WHEN rowsecurity = true THEN 1 ELSE 0 END,
    tablename;

-- Count policies per table
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Check for UNRESTRICTED tables
SELECT
    COUNT(*) as unrestricted_tables
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false;

-- If unrestricted_tables = 0, SUCCESS!
