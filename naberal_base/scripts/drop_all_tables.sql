-- ============================================================================
-- NABERAL Project - Drop All Existing Tables
-- ⚠️ WARNING: This will DELETE ALL DATA in public schema
-- ============================================================================
-- Use this only if you want to start fresh with a clean database

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS evidence_blobs CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS breakers CASCADE;
DROP TABLE IF EXISTS panels CASCADE;
DROP TABLE IF EXISTS quote_items CASCADE;
DROP TABLE IF EXISTS quotes CASCADE;
DROP TABLE IF EXISTS catalog_items CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Drop any remaining indexes explicitly (if not cascaded)
DROP INDEX IF EXISTS idx_customers_name;
DROP INDEX IF EXISTS idx_customers_company;
DROP INDEX IF EXISTS idx_quotes_customer_id;
DROP INDEX IF EXISTS idx_quotes_status;
DROP INDEX IF EXISTS idx_quotes_idempotency_key;
DROP INDEX IF EXISTS idx_quote_items_quote_id;
DROP INDEX IF EXISTS idx_panels_quote_id;
DROP INDEX IF EXISTS idx_breakers_panel_id;
DROP INDEX IF EXISTS idx_documents_quote_id;
DROP INDEX IF EXISTS idx_catalog_items_kind;
DROP INDEX IF EXISTS idx_evidence_blobs_quote_id;

-- Verify all tables are dropped
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- If the above query returns 0 rows, you're ready for fresh migration
