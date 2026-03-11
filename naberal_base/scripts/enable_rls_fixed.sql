-- ==========================================
-- Enable RLS for NABERAL KIS Estimator Tables (수정본)
-- VIEW 제외, 실제 테이블만 RLS 적용
-- 실행: Supabase SQL Editor에서 실행
-- ==========================================

-- 0. 먼저 테이블/뷰 타입 확인
SELECT
    c.relname as name,
    CASE c.relkind
        WHEN 'r' THEN '📋 TABLE'
        WHEN 'v' THEN '👁️ VIEW'
        WHEN 'm' THEN '📊 MATERIALIZED VIEW'
    END as type,
    CASE
        WHEN c.relkind = 'r' THEN 'RLS 적용 가능'
        ELSE 'RLS 적용 불가 (VIEW)'
    END as rls_applicable
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
AND c.relname IN (
    'customers', 'quotes', 'quote_items', 'panels',
    'breakers', 'documents', 'catalog_items', 'evidence_blobs',
    'phase_balance', 'quote_summary', 'sse_events', 'audit_logs',
    'validation_rules'
)
ORDER BY c.relkind, c.relname;

-- 1. RLS 활성화 (실제 테이블만)
-- VIEW는 자동 제외됨
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN (
            'customers', 'quotes', 'quote_items', 'panels',
            'breakers', 'documents', 'catalog_items', 'evidence_blobs',
            'sse_events', 'audit_logs', 'validation_rules'
        )
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl.tablename);
        RAISE NOTICE '✅ RLS enabled for table: %', tbl.tablename;
    END LOOP;
END $$;

-- 2. 기본 정책 생성 (인증된 사용자만 접근)

-- Customers 테이블
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'customers') THEN
        -- 기존 정책 삭제
        DROP POLICY IF EXISTS "Users can view all customers" ON public.customers;
        DROP POLICY IF EXISTS "Users can insert customers" ON public.customers;
        DROP POLICY IF EXISTS "Users can update customers" ON public.customers;

        -- 새 정책 생성
        CREATE POLICY "Users can view all customers"
        ON public.customers FOR SELECT
        TO authenticated
        USING (true);

        CREATE POLICY "Users can insert customers"
        ON public.customers FOR INSERT
        TO authenticated
        WITH CHECK (true);

        CREATE POLICY "Users can update customers"
        ON public.customers FOR UPDATE
        TO authenticated
        USING (true)
        WITH CHECK (true);

        RAISE NOTICE '✅ Policies created for: customers';
    END IF;
END $$;

-- Quotes 테이블 (자신의 견적만 - user_id 컬럼이 있다면)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'quotes'
        AND column_name = 'user_id'
    ) THEN
        -- 기존 정책 삭제
        DROP POLICY IF EXISTS "Users can view own quotes" ON public.quotes;
        DROP POLICY IF EXISTS "Users can create quotes" ON public.quotes;
        DROP POLICY IF EXISTS "Users can update own quotes" ON public.quotes;

        -- 새 정책 생성
        CREATE POLICY "Users can view own quotes"
        ON public.quotes FOR SELECT
        TO authenticated
        USING (auth.uid() = user_id);

        CREATE POLICY "Users can create quotes"
        ON public.quotes FOR INSERT
        TO authenticated
        WITH CHECK (auth.uid() = user_id);

        CREATE POLICY "Users can update own quotes"
        ON public.quotes FOR UPDATE
        TO authenticated
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);

        RAISE NOTICE '✅ User-specific policies created for: quotes';
    ELSE
        -- user_id 컬럼이 없으면 모든 인증 사용자 접근 가능
        DROP POLICY IF EXISTS "Authenticated users can access quotes" ON public.quotes;

        CREATE POLICY "Authenticated users can access quotes"
        ON public.quotes FOR ALL
        TO authenticated
        USING (true)
        WITH CHECK (true);

        RAISE NOTICE '⚠️ No user_id column in quotes - using general authenticated policy';
    END IF;
END $$;

-- Quote Items (quotes 테이블과 연계)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'quote_items') THEN
        DROP POLICY IF EXISTS "Users can view quote items" ON public.quote_items;

        CREATE POLICY "Users can view quote items"
        ON public.quote_items FOR SELECT
        TO authenticated
        USING (true);  -- 일단 인증된 사용자는 모두 볼 수 있게 설정

        RAISE NOTICE '✅ Policy created for: quote_items';
    END IF;
END $$;

-- Catalog Items (모든 사용자 읽기 가능)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'catalog_items') THEN
        DROP POLICY IF EXISTS "Anyone can view catalog" ON public.catalog_items;

        CREATE POLICY "Anyone can view catalog"
        ON public.catalog_items FOR SELECT
        TO authenticated
        USING (true);

        RAISE NOTICE '✅ Read-only policy created for: catalog_items';
    END IF;
END $$;

-- Evidence Blobs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'evidence_blobs') THEN
        DROP POLICY IF EXISTS "Authenticated users can access evidence" ON public.evidence_blobs;

        CREATE POLICY "Authenticated users can access evidence"
        ON public.evidence_blobs FOR ALL
        TO authenticated
        USING (true)
        WITH CHECK (true);

        RAISE NOTICE '✅ Policy created for: evidence_blobs';
    END IF;
END $$;

-- 3. RLS 상태 최종 확인
SELECT
    '📊 RLS Status Report' as report_title;

SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✅ RLS Enabled'
        ELSE '❌ RLS Disabled'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'customers', 'quotes', 'quote_items', 'panels',
    'breakers', 'documents', 'catalog_items', 'evidence_blobs',
    'sse_events', 'audit_logs', 'validation_rules'
)
ORDER BY tablename;

-- 4. VIEW 확인 (RLS 불가)
SELECT
    '👁️ Views (RLS 불가)' as info;

SELECT
    viewname as name,
    '👁️ VIEW - RLS 적용 불가' as note
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN ('phase_balance', 'quote_summary')
ORDER BY viewname;

-- 5. 정책 목록
SELECT
    '📋 Active RLS Policies' as report_title;

SELECT
    tablename,
    policyname,
    cmd as action,
    CASE
        WHEN permissive::text = 'YES' OR permissive::text = 'true' THEN '✅ PERMISSIVE'
        ELSE '🚫 RESTRICTIVE'
    END as type
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ==========================================
-- 실행 결과 해석:
-- 1. TABLE: RLS 활성화 성공
-- 2. VIEW: RLS 적용 불가 (phase_balance, quote_summary)
-- 3. 정책이 생성되지 않은 테이블은 모든 접근 차단됨
--
-- 중요:
-- - service_role 키: RLS 무시 (백엔드용)
-- - anon 키: RLS 정책 적용 (프론트엔드용)
-- ==========================================