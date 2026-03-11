-- ==========================================
-- KIS Estimator Database Schema - Idempotent Update
-- Safe to run multiple times
-- ==========================================

-- Enable extensions (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;

-- ==========================================
-- CREATE TABLES (IF NOT EXISTS)
-- ==========================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Quotes (main estimates)
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    totals JSONB NOT NULL DEFAULT '{"subtotal": 0, "tax": 0, "total": 0}'::jsonb,
    currency VARCHAR(3) NOT NULL DEFAULT 'KRW',
    evidence_sha VARCHAR(64),
    idempotency_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Quote items (line items)
CREATE TABLE IF NOT EXISTS quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE NOT NULL,
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('enclosure', 'breaker_main', 'breaker_branch', 'accessory')),
    name VARCHAR(255) NOT NULL,
    qty INTEGER NOT NULL CHECK (qty > 0),
    unit_price DECIMAL(15, 2),
    amount DECIMAL(15, 2),
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Panels (electrical panels)
CREATE TABLE IF NOT EXISTS panels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    enclosure_sku VARCHAR(100),
    fit_score DECIMAL(3, 2) CHECK (fit_score >= 0 AND fit_score <= 1),
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Breakers (circuit breakers)
CREATE TABLE IF NOT EXISTS breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    panel_id UUID REFERENCES panels(id) ON DELETE CASCADE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('main', 'branch', 'earth_leakage', 'surge_protector')),
    poles INTEGER NOT NULL CHECK (poles IN (1, 2, 3, 4)),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    qty INTEGER NOT NULL CHECK (qty > 0),
    brand VARCHAR(100),
    phase CHAR(1) CHECK (phase IN ('R', 'S', 'T')),
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Documents (generated PDFs, Excel files)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE NOT NULL,
    kind VARCHAR(10) NOT NULL CHECK (kind IN ('pdf', 'xlsx', 'svg')),
    path TEXT NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Catalog items (product catalog)
CREATE TABLE IF NOT EXISTS catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL CHECK (kind IN ('enclosure', 'breaker', 'accessory')),
    name VARCHAR(255) NOT NULL,
    specs JSONB NOT NULL,
    unit_price DECIMAL(15, 2) NOT NULL CHECK (unit_price >= 0),
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- Evidence blobs (audit trail)
CREATE TABLE IF NOT EXISTS evidence_blobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE NOT NULL,
    stage VARCHAR(50) NOT NULL,
    hash VARCHAR(64) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

-- ==========================================
-- CREATE INDEXES (IF NOT EXISTS)
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company);

CREATE INDEX IF NOT EXISTS idx_quotes_customer_id ON quotes(customer_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_idempotency_key ON quotes(idempotency_key);

CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON quote_items(quote_id);

CREATE INDEX IF NOT EXISTS idx_panels_quote_id ON panels(quote_id);

CREATE INDEX IF NOT EXISTS idx_breakers_panel_id ON breakers(panel_id);

CREATE INDEX IF NOT EXISTS idx_documents_quote_id ON documents(quote_id);

CREATE INDEX IF NOT EXISTS idx_catalog_items_kind ON catalog_items(kind);

CREATE INDEX IF NOT EXISTS idx_evidence_blobs_quote_id ON evidence_blobs(quote_id);

-- ==========================================
-- CREATE TRIGGERS (IF NOT EXISTS)
-- ==========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for customers
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for quotes
DROP TRIGGER IF EXISTS update_quotes_updated_at ON quotes;
CREATE TRIGGER update_quotes_updated_at
    BEFORE UPDATE ON quotes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for quote_items
DROP TRIGGER IF EXISTS update_quote_items_updated_at ON quote_items;
CREATE TRIGGER update_quote_items_updated_at
    BEFORE UPDATE ON quote_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for panels
DROP TRIGGER IF EXISTS update_panels_updated_at ON panels;
CREATE TRIGGER update_panels_updated_at
    BEFORE UPDATE ON panels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for breakers
DROP TRIGGER IF EXISTS update_breakers_updated_at ON breakers;
CREATE TRIGGER update_breakers_updated_at
    BEFORE UPDATE ON breakers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for catalog_items
DROP TRIGGER IF EXISTS update_catalog_items_updated_at ON catalog_items;
CREATE TRIGGER update_catalog_items_updated_at
    BEFORE UPDATE ON catalog_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- VERIFICATION
-- ==========================================

-- List all tables
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- List all indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
