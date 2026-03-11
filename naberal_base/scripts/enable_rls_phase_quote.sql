-- ============================================================================
-- RLS for phase_balance and quote_summary
-- Strategy: Convert VIEWs to MATERIALIZED VIEWs or TABLEs
-- ============================================================================

-- ============================================================================
-- OPTION 1: MATERIALIZED VIEW (권장 - 성능 우선)
-- ============================================================================

-- Drop existing views
DROP VIEW IF EXISTS estimator.v_quote_summary CASCADE;
DROP VIEW IF EXISTS estimator.v_phase_balance CASCADE;

-- Create materialized views
CREATE MATERIALIZED VIEW estimator.quote_summary AS
SELECT
    q.id,
    q.status,
    c.name as customer_name,
    c.company,
    q.totals->>'total' as total_amount,
    q.currency,
    q.created_at,
    q.updated_at,
    COUNT(DISTINCT p.id) as panel_count,
    COUNT(DISTINCT qi.id) as item_count
FROM estimator.quotes q
LEFT JOIN estimator.customers c ON q.customer_id = c.id
LEFT JOIN estimator.panels p ON p.quote_id = q.id
LEFT JOIN estimator.quote_items qi ON qi.quote_id = q.id
GROUP BY q.id, c.name, c.company;

CREATE MATERIALIZED VIEW estimator.phase_balance AS
SELECT
    p.id as panel_id,
    p.name as panel_name,
    SUM(CASE WHEN b.phase = 'R' THEN b.capacity * b.qty ELSE 0 END) as phase_r_load,
    SUM(CASE WHEN b.phase = 'S' THEN b.capacity * b.qty ELSE 0 END) as phase_s_load,
    SUM(CASE WHEN b.phase = 'T' THEN b.capacity * b.qty ELSE 0 END) as phase_t_load,
    COUNT(*) as breaker_count
FROM estimator.panels p
LEFT JOIN estimator.breakers b ON b.panel_id = p.id
GROUP BY p.id, p.name;

-- Create indexes on materialized views
CREATE UNIQUE INDEX idx_quote_summary_id ON estimator.quote_summary(id);
CREATE INDEX idx_quote_summary_status ON estimator.quote_summary(status);
CREATE INDEX idx_quote_summary_created_at ON estimator.quote_summary(created_at DESC);

CREATE UNIQUE INDEX idx_phase_balance_panel_id ON estimator.phase_balance(panel_id);
CREATE INDEX idx_phase_balance_panel_name ON estimator.phase_balance(panel_name);

-- Enable RLS on materialized views
ALTER MATERIALIZED VIEW estimator.quote_summary OWNER TO postgres;
ALTER MATERIALIZED VIEW estimator.phase_balance OWNER TO postgres;

-- Note: MATERIALIZED VIEWs cannot have RLS directly
-- Instead, create wrapper functions with SECURITY DEFINER

-- Refresh function (call after data changes)
CREATE OR REPLACE FUNCTION estimator.refresh_summary_views()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY estimator.quote_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY estimator.phase_balance;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION estimator.refresh_summary_views() TO authenticated;

-- ============================================================================
-- OPTION 2: Real TABLE with triggers (실시간성 우선)
-- ============================================================================

/*
-- Drop existing views
DROP VIEW IF EXISTS estimator.v_quote_summary CASCADE;
DROP VIEW IF EXISTS estimator.v_phase_balance CASCADE;

-- Create real tables
CREATE TABLE estimator.quote_summary (
    id UUID PRIMARY KEY,
    status TEXT,
    customer_name TEXT,
    company TEXT,
    total_amount TEXT,
    currency TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    panel_count BIGINT,
    item_count BIGINT
);

CREATE TABLE estimator.phase_balance (
    panel_id UUID PRIMARY KEY,
    panel_name TEXT,
    phase_r_load NUMERIC,
    phase_s_load NUMERIC,
    phase_t_load NUMERIC,
    breaker_count BIGINT
);

-- Enable RLS
ALTER TABLE estimator.quote_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE estimator.phase_balance ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own quote summaries"
    ON estimator.quote_summary FOR SELECT
    USING (auth.uid() = id::uuid OR auth.role() = 'service_role');

CREATE POLICY "Users can view phase balance for their quotes"
    ON estimator.phase_balance FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM estimator.panels p
            JOIN estimator.quotes q ON p.quote_id = q.id
            WHERE p.id = phase_balance.panel_id
              AND (auth.uid() = q.id::uuid OR auth.role() = 'service_role')
        )
    );

-- Create refresh function with triggers
CREATE OR REPLACE FUNCTION estimator.refresh_quote_summary()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM estimator.quote_summary WHERE id = COALESCE(NEW.id, OLD.id);

    INSERT INTO estimator.quote_summary
    SELECT
        q.id,
        q.status,
        c.name as customer_name,
        c.company,
        q.totals->>'total' as total_amount,
        q.currency,
        q.created_at,
        q.updated_at,
        COUNT(DISTINCT p.id) as panel_count,
        COUNT(DISTINCT qi.id) as item_count
    FROM estimator.quotes q
    LEFT JOIN estimator.customers c ON q.customer_id = c.id
    LEFT JOIN estimator.panels p ON p.quote_id = q.id
    LEFT JOIN estimator.quote_items qi ON qi.quote_id = q.id
    WHERE q.id = COALESCE(NEW.id, OLD.id)
    GROUP BY q.id, c.name, c.company;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION estimator.refresh_phase_balance()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM estimator.phase_balance WHERE panel_id = COALESCE(NEW.panel_id, OLD.panel_id);

    INSERT INTO estimator.phase_balance
    SELECT
        p.id as panel_id,
        p.name as panel_name,
        SUM(CASE WHEN b.phase = 'R' THEN b.capacity * b.qty ELSE 0 END) as phase_r_load,
        SUM(CASE WHEN b.phase = 'S' THEN b.capacity * b.qty ELSE 0 END) as phase_s_load,
        SUM(CASE WHEN b.phase = 'T' THEN b.capacity * b.qty ELSE 0 END) as phase_t_load,
        COUNT(*) as breaker_count
    FROM estimator.panels p
    LEFT JOIN estimator.breakers b ON b.panel_id = p.id
    WHERE p.id = COALESCE(NEW.panel_id, OLD.panel_id)
    GROUP BY p.id, p.name;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers
CREATE TRIGGER trg_refresh_quote_summary
AFTER INSERT OR UPDATE OR DELETE ON estimator.quotes
FOR EACH ROW EXECUTE FUNCTION estimator.refresh_quote_summary();

CREATE TRIGGER trg_refresh_phase_balance
AFTER INSERT OR UPDATE OR DELETE ON estimator.breakers
FOR EACH ROW EXECUTE FUNCTION estimator.refresh_phase_balance();
*/

-- ============================================================================
-- VERIFY RLS STATUS
-- ============================================================================

SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'estimator'
  AND tablename IN ('quote_summary', 'phase_balance')
ORDER BY tablename;
