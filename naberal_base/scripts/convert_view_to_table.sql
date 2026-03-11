-- ==========================================
-- VIEW를 TABLE로 변환하거나 보안 함수로 대체
-- NABERAL Project - RLS 적용 가능하도록 수정
-- ==========================================

-- 옵션 1: VIEW를 MATERIALIZED VIEW로 변환 (RLS 적용 가능)
-- ==========================================

-- phase_balance를 MATERIALIZED VIEW로 변환
DROP VIEW IF EXISTS public.phase_balance CASCADE;

CREATE MATERIALIZED VIEW public.phase_balance AS
-- 여기에 원본 VIEW 정의를 넣어야 함
-- 예시:
SELECT
    quote_id,
    phase,
    SUM(load_amps) as total_amps,
    COUNT(*) as breaker_count
FROM public.quote_items
GROUP BY quote_id, phase;

-- MATERIALIZED VIEW에 인덱스 추가
CREATE UNIQUE INDEX idx_phase_balance_quote_phase
ON public.phase_balance(quote_id, phase);

-- MATERIALIZED VIEW에 RLS 활성화 (가능!)
ALTER MATERIALIZED VIEW public.phase_balance ENABLE ROW LEVEL SECURITY;

-- 정책 생성
CREATE POLICY "Users can view phase balance"
ON public.phase_balance FOR SELECT
TO authenticated
USING (true);

-- 리프레시 권한 설정
GRANT SELECT ON public.phase_balance TO authenticated;


-- 옵션 2: SECURITY DEFINER 함수로 대체
-- ==========================================

-- phase_balance를 함수로 대체
CREATE OR REPLACE FUNCTION get_phase_balance(p_quote_id UUID DEFAULT NULL)
RETURNS TABLE (
    quote_id UUID,
    phase VARCHAR,
    total_amps NUMERIC,
    breaker_count INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER  -- 함수 소유자 권한으로 실행
SET search_path = public
AS $$
BEGIN
    -- 사용자 권한 확인
    IF NOT EXISTS (
        SELECT 1 FROM public.quotes
        WHERE id = p_quote_id
        AND (
            -- 여기에 접근 권한 로직 추가
            user_id = auth.uid()  -- 자신의 견적만
            OR
            EXISTS (  -- 또는 관리자
                SELECT 1 FROM auth.users
                WHERE id = auth.uid()
                AND raw_user_meta_data->>'role' = 'admin'
            )
        )
    ) THEN
        RAISE EXCEPTION 'Access denied';
    END IF;

    RETURN QUERY
    SELECT
        qi.quote_id,
        qi.phase,
        SUM(qi.load_amps) as total_amps,
        COUNT(*)::INTEGER as breaker_count
    FROM public.quote_items qi
    WHERE p_quote_id IS NULL OR qi.quote_id = p_quote_id
    GROUP BY qi.quote_id, qi.phase;
END;
$$;

-- 함수 실행 권한 부여
GRANT EXECUTE ON FUNCTION get_phase_balance TO authenticated;


-- 옵션 3: 실제 TABLE로 변환 + 트리거로 자동 업데이트
-- ==========================================

-- 1. VIEW 삭제
DROP VIEW IF EXISTS public.phase_balance CASCADE;

-- 2. 실제 TABLE 생성
CREATE TABLE public.phase_balance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    quote_id UUID REFERENCES public.quotes(id) ON DELETE CASCADE,
    phase VARCHAR(10),
    total_amps NUMERIC(10,2),
    breaker_count INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(quote_id, phase)
);

-- 3. RLS 활성화
ALTER TABLE public.phase_balance ENABLE ROW LEVEL SECURITY;

-- 4. RLS 정책 생성
CREATE POLICY "Users can view own phase balance"
ON public.phase_balance FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.quotes
        WHERE quotes.id = phase_balance.quote_id
        AND quotes.user_id = auth.uid()
    )
);

-- 5. 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_phase_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- quote_items가 변경되면 phase_balance 재계산
    DELETE FROM public.phase_balance
    WHERE quote_id = COALESCE(NEW.quote_id, OLD.quote_id);

    INSERT INTO public.phase_balance (quote_id, phase, total_amps, breaker_count)
    SELECT
        quote_id,
        phase,
        SUM(load_amps),
        COUNT(*)
    FROM public.quote_items
    WHERE quote_id = COALESCE(NEW.quote_id, OLD.quote_id)
    GROUP BY quote_id, phase;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_phase_balance
AFTER INSERT OR UPDATE OR DELETE ON public.quote_items
FOR EACH ROW
EXECUTE FUNCTION update_phase_balance();


-- quote_summary도 동일하게 처리
-- ==========================================

-- VIEW 삭제
DROP VIEW IF EXISTS public.quote_summary CASCADE;

-- TABLE 생성
CREATE TABLE public.quote_summary (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    quote_id UUID REFERENCES public.quotes(id) ON DELETE CASCADE UNIQUE,
    total_price NUMERIC(12,2),
    total_items INTEGER,
    enclosure_count INTEGER,
    breaker_count INTEGER,
    accessory_count INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 활성화
ALTER TABLE public.quote_summary ENABLE ROW LEVEL SECURITY;

-- RLS 정책
CREATE POLICY "Users can view own quote summary"
ON public.quote_summary FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.quotes
        WHERE quotes.id = quote_summary.quote_id
        AND quotes.user_id = auth.uid()
    )
);

-- 트리거 함수
CREATE OR REPLACE FUNCTION update_quote_summary()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM public.quote_summary
    WHERE quote_id = COALESCE(NEW.quote_id, OLD.quote_id);

    INSERT INTO public.quote_summary (
        quote_id, total_price, total_items,
        enclosure_count, breaker_count, accessory_count
    )
    SELECT
        q.id,
        COALESCE(SUM(qi.unit_price * qi.quantity), 0),
        COALESCE(COUNT(qi.id), 0),
        COUNT(DISTINCT p.id),
        COUNT(DISTINCT CASE WHEN qi.item_type = 'breaker' THEN qi.id END),
        COUNT(DISTINCT CASE WHEN qi.item_type = 'accessory' THEN qi.id END)
    FROM public.quotes q
    LEFT JOIN public.quote_items qi ON q.id = qi.quote_id
    LEFT JOIN public.panels p ON q.id = p.quote_id
    WHERE q.id = COALESCE(NEW.quote_id, OLD.quote_id)
    GROUP BY q.id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_quote_summary
AFTER INSERT OR UPDATE OR DELETE ON public.quote_items
FOR EACH ROW
EXECUTE FUNCTION update_quote_summary();


-- 최종 확인
-- ==========================================
SELECT
    tablename,
    CASE
        WHEN rowsecurity = true THEN '✅ RLS ENABLED'
        ELSE '❌ RLS DISABLED'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('phase_balance', 'quote_summary')
ORDER BY tablename;

-- ==========================================
-- 권장사항:
-- 1. 실시간 집계가 중요하면: 옵션 3 (TABLE + 트리거)
-- 2. 성능이 중요하면: 옵션 1 (MATERIALIZED VIEW)
-- 3. 복잡한 권한 로직이 필요하면: 옵션 2 (SECURITY DEFINER 함수)
-- ==========================================