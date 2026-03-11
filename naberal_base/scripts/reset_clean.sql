-- ══════════════════════════════════════════════════════════════
-- DATABASE RESET - CLEAN VERSION
-- ══════════════════════════════════════════════════════════════

-- 1. 기존 테이블 삭제
DROP TABLE IF EXISTS shared.catalog_items CASCADE;
DROP TABLE IF EXISTS public.catalog_items CASCADE;

-- 2. shared 스키마 생성
CREATE SCHEMA IF NOT EXISTS shared;

-- 3. catalog_items 테이블 생성 (UNIQUE 제약조건 포함)
CREATE TABLE shared.catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,
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

-- 5. RLS 비활성화
ALTER TABLE shared.catalog_items DISABLE ROW LEVEL SECURITY;

-- 6. 권한 설정
GRANT ALL ON shared.catalog_items TO postgres;
GRANT ALL ON shared.catalog_items TO anon;
GRANT ALL ON shared.catalog_items TO authenticated;
GRANT ALL ON shared.catalog_items TO service_role;

-- 7. 확인
SELECT 'Reset Complete' AS status;
