-- I-3.4: verb_plans table for VerbSpec storage
-- Migration: 20251015_verb_plans
-- Purpose: Store VerbSpec lists for Plan→Execute flow

-- Create verb_plans table
CREATE TABLE IF NOT EXISTS verb_plans (
    plan_id VARCHAR(64) PRIMARY KEY,
    specs_json JSONB NOT NULL,
    specs_count INTEGER NOT NULL DEFAULT 0,
    is_valid BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    CONSTRAINT valid_specs_count CHECK (specs_count >= 0)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_verb_plans_created_at ON verb_plans(created_at DESC);

-- RLS policies (if needed)
ALTER TABLE verb_plans ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY IF NOT EXISTS "Service role full access on verb_plans"
    ON verb_plans
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comments
COMMENT ON TABLE verb_plans IS 'I-3.4: VerbSpec storage for Plan→Execute flow';
COMMENT ON COLUMN verb_plans.plan_id IS 'Estimate ID (EST-YYYYMMDDHHMMSS)';
COMMENT ON COLUMN verb_plans.specs_json IS 'VerbSpec list in JSON format';
COMMENT ON COLUMN verb_plans.specs_count IS 'Number of VerbSpecs in the list';
COMMENT ON COLUMN verb_plans.is_valid IS 'Schema validation status';
COMMENT ON COLUMN verb_plans.created_at IS 'Creation timestamp (UTC)';
COMMENT ON COLUMN verb_plans.updated_at IS 'Last update timestamp (UTC)';
