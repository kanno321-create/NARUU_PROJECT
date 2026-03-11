-- ==========================================
-- Enable RLS for NABERAL KIS Estimator Tables
-- 실행: Supabase SQL Editor에서 실행
-- ==========================================

-- 1. RLS 활성화 (모든 테이블)
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.panels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.breakers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_blobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.phase_balance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sse_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_rules ENABLE ROW LEVEL SECURITY;

-- 2. 기본 정책 생성 (인증된 사용자만 접근)
-- Customers 테이블
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

-- Quotes 테이블 (자신의 견적만)
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

-- Quote Items (자신의 견적 항목만)
CREATE POLICY "Users can view own quote items"
ON public.quote_items FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.quotes
        WHERE quotes.id = quote_items.quote_id
        AND quotes.user_id = auth.uid()
    )
);

-- Catalog Items (모든 사용자 읽기 가능)
CREATE POLICY "Anyone can view catalog"
ON public.catalog_items FOR SELECT
TO authenticated
USING (true);

-- Evidence Blobs (자신의 증거만)
CREATE POLICY "Users can view own evidence"
ON public.evidence_blobs FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.quotes
        WHERE quotes.id = evidence_blobs.quote_id
        AND quotes.user_id = auth.uid()
    )
);

-- 3. Service Role 예외 (백엔드 API용)
-- service_role 키는 모든 RLS 우회
-- anon 키는 RLS 정책 적용

-- 4. 확인 쿼리
SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✅ RLS Enabled'
        ELSE '❌ RLS Disabled'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 5. 정책 확인
SELECT
    tablename,
    policyname,
    permissive,
    cmd as action
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ==========================================
-- 주의사항:
-- 1. 개발 중에는 service_role 키 사용
-- 2. 프로덕션에서는 anon 키 + RLS 정책 필수
-- 3. auth.uid()는 로그인한 사용자 ID
-- ==========================================