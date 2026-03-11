-- ==========================================
-- Expose ERP Schema to Supabase API
-- Supabase API에서 ERP 스키마 접근 가능하도록 설정
-- ==========================================

-- ERP 스키마에 대한 사용 권한 부여
GRANT USAGE ON SCHEMA erp TO anon;
GRANT USAGE ON SCHEMA erp TO authenticated;
GRANT USAGE ON SCHEMA erp TO service_role;

-- 모든 ERP 테이블에 대한 권한 부여 (SELECT, INSERT, UPDATE, DELETE)
GRANT ALL ON ALL TABLES IN SCHEMA erp TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA erp TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA erp TO service_role;

-- 시퀀스에 대한 권한 부여
GRANT ALL ON ALL SEQUENCES IN SCHEMA erp TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA erp TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA erp TO service_role;

-- 새로 생성되는 테이블에 대한 기본 권한 설정
ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON TABLES TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA erp GRANT ALL ON SEQUENCES TO service_role;

-- ==========================================
-- 중요: 이 마이그레이션 외에도 Supabase Dashboard에서
-- 다음 설정이 필요합니다:
--
-- Project Settings > API > Data API Settings > Exposed schemas
-- 에서 'erp' 스키마를 추가해야 합니다.
-- ==========================================

-- RLS 활성화 (보안을 위해)
-- 참고: RLS 정책은 개발 단계에서는 일단 모든 접근 허용

-- customers 테이블 RLS
ALTER TABLE erp.customers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to customers" ON erp.customers;
CREATE POLICY "Allow all access to customers" ON erp.customers
    FOR ALL USING (true) WITH CHECK (true);

-- products 테이블 RLS
ALTER TABLE erp.products ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to products" ON erp.products;
CREATE POLICY "Allow all access to products" ON erp.products
    FOR ALL USING (true) WITH CHECK (true);

-- sales 테이블 RLS
ALTER TABLE erp.sales ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to sales" ON erp.sales;
CREATE POLICY "Allow all access to sales" ON erp.sales
    FOR ALL USING (true) WITH CHECK (true);

-- sale_items 테이블 RLS
ALTER TABLE erp.sale_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to sale_items" ON erp.sale_items;
CREATE POLICY "Allow all access to sale_items" ON erp.sale_items
    FOR ALL USING (true) WITH CHECK (true);

-- purchases 테이블 RLS
ALTER TABLE erp.purchases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to purchases" ON erp.purchases;
CREATE POLICY "Allow all access to purchases" ON erp.purchases
    FOR ALL USING (true) WITH CHECK (true);

-- purchase_items 테이블 RLS
ALTER TABLE erp.purchase_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to purchase_items" ON erp.purchase_items;
CREATE POLICY "Allow all access to purchase_items" ON erp.purchase_items
    FOR ALL USING (true) WITH CHECK (true);

-- tax_invoices 테이블 RLS
ALTER TABLE erp.tax_invoices ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to tax_invoices" ON erp.tax_invoices;
CREATE POLICY "Allow all access to tax_invoices" ON erp.tax_invoices
    FOR ALL USING (true) WITH CHECK (true);

-- quotations 테이블 RLS
ALTER TABLE erp.quotations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to quotations" ON erp.quotations;
CREATE POLICY "Allow all access to quotations" ON erp.quotations
    FOR ALL USING (true) WITH CHECK (true);

-- quotation_items 테이블 RLS
ALTER TABLE erp.quotation_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to quotation_items" ON erp.quotation_items;
CREATE POLICY "Allow all access to quotation_items" ON erp.quotation_items
    FOR ALL USING (true) WITH CHECK (true);

-- payments 테이블 RLS
ALTER TABLE erp.payments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to payments" ON erp.payments;
CREATE POLICY "Allow all access to payments" ON erp.payments
    FOR ALL USING (true) WITH CHECK (true);

-- inventory 테이블 RLS
ALTER TABLE erp.inventory ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to inventory" ON erp.inventory;
CREATE POLICY "Allow all access to inventory" ON erp.inventory
    FOR ALL USING (true) WITH CHECK (true);

-- inventory_movements 테이블 RLS
ALTER TABLE erp.inventory_movements ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to inventory_movements" ON erp.inventory_movements;
CREATE POLICY "Allow all access to inventory_movements" ON erp.inventory_movements
    FOR ALL USING (true) WITH CHECK (true);

-- warehouses 테이블 RLS
ALTER TABLE erp.warehouses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to warehouses" ON erp.warehouses;
CREATE POLICY "Allow all access to warehouses" ON erp.warehouses
    FOR ALL USING (true) WITH CHECK (true);

-- employees 테이블 RLS
ALTER TABLE erp.employees ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to employees" ON erp.employees;
CREATE POLICY "Allow all access to employees" ON erp.employees
    FOR ALL USING (true) WITH CHECK (true);

-- departments 테이블 RLS
ALTER TABLE erp.departments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to departments" ON erp.departments;
CREATE POLICY "Allow all access to departments" ON erp.departments
    FOR ALL USING (true) WITH CHECK (true);

-- bank_accounts 테이블 RLS
ALTER TABLE erp.bank_accounts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to bank_accounts" ON erp.bank_accounts;
CREATE POLICY "Allow all access to bank_accounts" ON erp.bank_accounts
    FOR ALL USING (true) WITH CHECK (true);

-- product_categories 테이블 RLS
ALTER TABLE erp.product_categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to product_categories" ON erp.product_categories;
CREATE POLICY "Allow all access to product_categories" ON erp.product_categories
    FOR ALL USING (true) WITH CHECK (true);

-- 출력 메시지
DO $$
BEGIN
    RAISE NOTICE 'ERP schema permissions and RLS policies have been configured.';
    RAISE NOTICE 'IMPORTANT: You must also add "erp" to Exposed Schemas in Supabase Dashboard:';
    RAISE NOTICE '  Project Settings > API > Data API Settings > Exposed schemas';
END $$;
