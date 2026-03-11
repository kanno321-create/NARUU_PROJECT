-- ==========================================
-- Add Missing Tables to NABERAL Project
-- Only creates tables that don't exist yet
-- ==========================================

-- Check which tables are missing
SELECT
    t.table_name,
    CASE WHEN EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = t.table_name
    ) THEN '✓ EXISTS' ELSE '✗ MISSING' END as status
FROM (
    VALUES
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
) AS t(table_name);

-- ==========================================
-- SSE Events table (for Server-Sent Events)
-- ==========================================
CREATE TABLE IF NOT EXISTS sse_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    seq INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sse_events_quote_id ON sse_events(quote_id);
CREATE INDEX IF NOT EXISTS idx_sse_events_created_at ON sse_events(created_at);

COMMENT ON TABLE sse_events IS 'Server-Sent Events for real-time progress updates';

-- ==========================================
-- Audit Logs table (for system audit trail)
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

COMMENT ON TABLE audit_logs IS 'System-wide audit trail for compliance and security';

-- ==========================================
-- Validation Rules table (for business rules)
-- ==========================================
CREATE TABLE IF NOT EXISTS validation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    rule_config JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_validation_rules_type ON validation_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_validation_rules_active ON validation_rules(is_active);

COMMENT ON TABLE validation_rules IS 'Business validation rules for estimates';

-- Add trigger for validation_rules
DROP TRIGGER IF EXISTS update_validation_rules_updated_at ON validation_rules;
CREATE TRIGGER update_validation_rules_updated_at
    BEFORE UPDATE ON validation_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- Verification
-- ==========================================

-- Final count
SELECT
    COUNT(*) as total_tables,
    COUNT(CASE WHEN schemaname = 'public' THEN 1 END) as public_tables
FROM pg_tables
WHERE schemaname = 'public';

-- List all tables in public schema
SELECT
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
