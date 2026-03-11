-- ============================================================================
-- OPTION 1: MATERIALIZED VIEW 적용 (권장)
-- 성능 우선, 수동 REFRESH 필요
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

-- Create unique indexes (required for CONCURRENTLY refresh)
CREATE UNIQUE INDEX idx_quote_summary_id ON estimator.quote_summary(id);
CREATE UNIQUE INDEX idx_phase_balance_panel_id ON estimator.phase_balance(panel_id);

-- Create additional indexes
CREATE INDEX idx_quote_summary_status ON estimator.quote_summary(status);
CREATE INDEX idx_quote_summary_created_at ON estimator.quote_summary(created_at DESC);
CREATE INDEX idx_phase_balance_panel_name ON estimator.phase_balance(panel_name);

-- Create refresh function
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
GRANT EXECUTE ON FUNCTION estimator.refresh_summary_views() TO authenticated, anon;

-- Initial refresh
REFRESH MATERIALIZED VIEW estimator.quote_summary;
REFRESH MATERIALIZED VIEW estimator.phase_balance;

-- ============================================================================
-- ACCESS CONTROL via SECURITY DEFINER functions
-- ============================================================================

-- Secure SELECT function for quote_summary
CREATE OR REPLACE FUNCTION estimator.get_quote_summary(p_quote_id UUID DEFAULT NULL)
RETURNS TABLE (
    id UUID,
    status TEXT,
    customer_name TEXT,
    company TEXT,
    total_amount TEXT,
    currency TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    panel_count BIGINT,
    item_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Check authorization (example: service_role or authenticated)
    IF auth.role() NOT IN ('service_role', 'authenticated') THEN
        RAISE EXCEPTION 'Unauthorized';
    END IF;

    RETURN QUERY
    SELECT
        qs.id,
        qs.status,
        qs.customer_name,
        qs.company,
        qs.total_amount,
        qs.currency,
        qs.created_at,
        qs.updated_at,
        qs.panel_count,
        qs.item_count
    FROM estimator.quote_summary qs
    WHERE (p_quote_id IS NULL OR qs.id = p_quote_id);
END;
$$;

-- Secure SELECT function for phase_balance
CREATE OR REPLACE FUNCTION estimator.get_phase_balance(p_panel_id UUID DEFAULT NULL)
RETURNS TABLE (
    panel_id UUID,
    panel_name TEXT,
    phase_r_load NUMERIC,
    phase_s_load NUMERIC,
    phase_t_load NUMERIC,
    breaker_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Check authorization
    IF auth.role() NOT IN ('service_role', 'authenticated') THEN
        RAISE EXCEPTION 'Unauthorized';
    END IF;

    RETURN QUERY
    SELECT
        pb.panel_id,
        pb.panel_name,
        pb.phase_r_load,
        pb.phase_s_load,
        pb.phase_t_load,
        pb.breaker_count
    FROM estimator.phase_balance pb
    WHERE (p_panel_id IS NULL OR pb.panel_id = p_panel_id);
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION estimator.get_quote_summary(UUID) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION estimator.get_phase_balance(UUID) TO authenticated, anon;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check materialized views exist
SELECT
    schemaname,
    matviewname,
    matviewowner
FROM pg_matviews
WHERE schemaname = 'estimator'
  AND matviewname IN ('quote_summary', 'phase_balance');

-- Test refresh function
SELECT estimator.refresh_summary_views();

-- Test select functions
SELECT * FROM estimator.get_quote_summary();
SELECT * FROM estimator.get_phase_balance();
