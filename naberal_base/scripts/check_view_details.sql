-- ==========================================
-- VIEW 상세 정보 확인
-- phase_balance와 quote_summary가 VIEW인지 TABLE인지 확인
-- ==========================================

-- 1. 객체 타입 확인
SELECT
    c.relname as object_name,
    CASE c.relkind
        WHEN 'r' THEN '📋 TABLE'
        WHEN 'v' THEN '👁️ VIEW'
        WHEN 'm' THEN '📊 MATERIALIZED VIEW'
    END as object_type,
    n.nspname as schema_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
AND c.relname IN ('phase_balance', 'quote_summary')
ORDER BY c.relname;

-- 2. VIEW 정의 확인 (만약 VIEW라면)
SELECT
    viewname,
    definition
FROM pg_views
WHERE schemaname = 'public'
AND viewname IN ('phase_balance', 'quote_summary');

-- 3. 만약 TABLE이라면 RLS 상태 확인
SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✅ RLS ENABLED'
        ELSE '❌ RLS DISABLED (UNRESTRICTED)'
    END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('phase_balance', 'quote_summary');

-- 4. 해결 방법 제안
SELECT '💡 해결 방법' as solution_title;

SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_views
            WHERE schemaname = 'public'
            AND viewname IN ('phase_balance', 'quote_summary')
        )
        THEN 'VIEW는 RLS를 직접 적용할 수 없습니다. 대신 다음 방법을 사용하세요:
1) VIEW의 기반 테이블에 RLS 적용
2) VIEW를 SECURITY DEFINER 함수로 대체
3) VIEW 대신 MATERIALIZED VIEW 사용 (RLS 적용 가능)'
        ELSE 'TABLE입니다. 아래 명령어로 RLS를 활성화하세요:
ALTER TABLE public.phase_balance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_summary ENABLE ROW LEVEL SECURITY;'
    END as recommendation;