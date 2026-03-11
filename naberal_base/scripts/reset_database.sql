-- ══════════════════════════════════════════════════════════════
-- DATABASE RESET SCRIPT
-- 완전 초기화 후 재배포
-- ══════════════════════════════════════════════════════════════

-- 1. 기존 테이블 모두 삭제
DROP TABLE IF EXISTS shared.catalog_items CASCADE;
DROP TABLE IF EXISTS public.catalog_items CASCADE;

-- 2. shared 스키마 재생성 (존재하지 않을 경우)
CREATE SCHEMA IF NOT EXISTS shared;

-- 3. catalog_items 테이블 생성 (UNIQUE 제약조건 포함)
CREATE TABLE shared.catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,  -- ⭐ UNIQUE 제약조건 추가
    name TEXT NOT NULL,
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    unit_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'KRW',
    is_active BOOLEAN NOT NULL DEFAULT true,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. 인덱스 생성
CREATE INDEX idx_catalog_items_kind ON shared.catalog_items(kind);
CREATE INDEX idx_catalog_items_sku ON shared.catalog_items(sku);
CREATE INDEX idx_catalog_items_specs ON shared.catalog_items USING GIN(specs);
CREATE INDEX idx_catalog_items_meta ON shared.catalog_items USING GIN(meta);

-- 5. RLS (Row Level Security) 비활성화 (일단 데이터 로드 테스트)
ALTER TABLE shared.catalog_items DISABLE ROW LEVEL SECURITY;

-- 6. 권한 설정
GRANT ALL ON shared.catalog_items TO postgres;
GRANT ALL ON shared.catalog_items TO anon;
GRANT ALL ON shared.catalog_items TO authenticated;
GRANT ALL ON shared.catalog_items TO service_role;

-- 7. 확인
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'catalog_items';

-- 8. 제약조건 확인
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    CASE contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'c' THEN 'CHECK'
    END AS constraint_description
FROM pg_constraint
WHERE conrelid = 'shared.catalog_items'::regclass;

-- ══════════════════════════════════════════════════════════════
-- 초기화 완료
-- 다음: scripts/insert_knowledge_complete.sql 실행
-- ══════════════════════════════════════════════════════════════
