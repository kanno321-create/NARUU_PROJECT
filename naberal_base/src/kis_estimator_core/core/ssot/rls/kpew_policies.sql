-- ==========================================================================
-- RLS Policies for K-PEW Tables (SB-02 Compliance)
-- ==========================================================================
-- Purpose: Row-level security policies for EPDL plans, execution history, and evidence
-- Loaded by: src/kis_estimator_core/infra/rls_loader.py
-- Applied: Phase H+1 완료 (2025-11-28) - created_by column migration included
-- Migration: alembic/versions/20251128_epdl_created_by.py
-- ==========================================================================

-- ============================================================================
-- 1. ENABLE RLS ON ALL K-PEW TABLES
-- ============================================================================
ALTER TABLE IF EXISTS epdl_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS execution_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS evidence_packs ENABLE ROW LEVEL SECURITY;


-- ============================================================================
-- 2. SERVICE ROLE POLICIES (Full CRUD Access)
-- ============================================================================
-- Service role needs full access for backend operations (workflow orchestration)

CREATE POLICY IF NOT EXISTS "service_role_all_epdl_plans"
  ON epdl_plans
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "service_role_all_execution_history"
  ON execution_history
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "service_role_all_evidence_packs"
  ON evidence_packs
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);


-- ============================================================================
-- 3. AUTHENTICATED USER POLICIES (Read-Only, Own Data)
-- ============================================================================
-- Authenticated users can only read their own estimation data
-- Phase H+1 완료 (2025-11-28): created_by column added via migration

CREATE POLICY IF NOT EXISTS "user_read_own_epdl_plans"
  ON epdl_plans
  FOR SELECT
  TO authenticated
  USING (
    -- Phase H+1 완료: User can only read their own plans
    auth.uid()::text = created_by
  );

CREATE POLICY IF NOT EXISTS "user_read_own_execution_history"
  ON execution_history
  FOR SELECT
  TO authenticated
  USING (
    -- Phase H+1 완료: Check if estimate_id belongs to user's plans
    estimate_id IN (
      SELECT estimate_id
      FROM epdl_plans
      WHERE created_by = auth.uid()::text
    )
  );

CREATE POLICY IF NOT EXISTS "user_read_own_evidence_packs"
  ON evidence_packs
  FOR SELECT
  TO authenticated
  USING (
    -- Phase H+1 완료: Check if estimate_id belongs to user's plans
    estimate_id IN (
      SELECT estimate_id
      FROM epdl_plans
      WHERE created_by = auth.uid()::text
    )
  );


-- ============================================================================
-- 4. ANONYMOUS ROLE (No Access - Default Deny)
-- ============================================================================
-- No policies for 'anon' role = complete denial of access
-- This ensures unauthenticated users cannot access any K-PEW data


-- ============================================================================
-- 5. VERIFICATION QUERIES
-- ============================================================================
-- Use these queries to verify RLS is working correctly after applying policies

-- Check RLS is enabled:
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename IN ('epdl_plans', 'execution_history', 'evidence_packs')
--   AND schemaname = 'kis_beta';
-- Expected: rowsecurity = t for all tables

-- Check policies exist:
-- SELECT schemaname, tablename, policyname, roles, cmd
-- FROM pg_policies
-- WHERE tablename IN ('epdl_plans', 'execution_history', 'evidence_packs')
--   AND schemaname = 'kis_beta'
-- ORDER BY tablename, policyname;
-- Expected: 9 policies (3 service_role + 3 authenticated + 3 implicit deny for anon)

-- Test service role access (should succeed):
-- SET ROLE service_role;
-- SELECT COUNT(*) FROM epdl_plans;
-- Expected: Returns count without error

-- Test authenticated user access (Phase H+1 완료 - now works with created_by):
-- SET ROLE authenticated;
-- SELECT COUNT(*) FROM epdl_plans;
-- Expected: Returns count of user's own plans (created_by = auth.uid()::text)

-- Test anonymous access (should fail):
-- SET ROLE anon;
-- SELECT COUNT(*) FROM epdl_plans;
-- Expected: ERROR or 0 rows


-- ============================================================================
-- ROLLBACK PROCEDURE
-- ============================================================================
-- To remove all RLS policies (emergency rollback):
--
-- DROP POLICY IF EXISTS "service_role_all_epdl_plans" ON epdl_plans;
-- DROP POLICY IF EXISTS "service_role_all_execution_history" ON execution_history;
-- DROP POLICY IF EXISTS "service_role_all_evidence_packs" ON evidence_packs;
-- DROP POLICY IF EXISTS "user_read_own_epdl_plans" ON epdl_plans;
-- DROP POLICY IF EXISTS "user_read_own_execution_history" ON execution_history;
-- DROP POLICY IF EXISTS "user_read_own_evidence_packs" ON evidence_packs;
--
-- ALTER TABLE epdl_plans DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE execution_history DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE evidence_packs DISABLE ROW LEVEL SECURITY;
