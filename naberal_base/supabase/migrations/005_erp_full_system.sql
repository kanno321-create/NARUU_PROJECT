-- ==========================================
-- ERP Full System Migration
-- 이지판매재고관리 2015 완전 호환 스키마
-- ==========================================

-- ERP 스키마 생성
CREATE SCHEMA IF NOT EXISTS erp;

-- ==========================================
-- 1. 기초 데이터 테이블
-- ==========================================

-- 부서
CREATE TABLE IF NOT EXISTS erp.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES erp.departments(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 사원
CREATE TABLE IF NOT EXISTS erp.employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    department_id UUID REFERENCES erp.departments(id),
    position VARCHAR(50),
    hire_date DATE,
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 거래처
CREATE TABLE IF NOT EXISTS erp.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    ceo_name VARCHAR(50),
    business_number VARCHAR(12),
    business_type VARCHAR(100),
    business_category VARCHAR(100),
    address TEXT,
    phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(100),
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    customer_type VARCHAR(20) CHECK (customer_type IN ('매출처', '매입처', '겸용')),
    grade VARCHAR(20) DEFAULT 'Normal' CHECK (grade IN ('VIP', 'Gold', 'Silver', 'Normal')),
    credit_limit DECIMAL(15,2) DEFAULT 0,
    payment_terms INTEGER DEFAULT 30,
    memo TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 창고
CREATE TABLE IF NOT EXISTS erp.warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location TEXT,
    manager_id UUID REFERENCES erp.employees(id),
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 상품 카테고리
CREATE TABLE IF NOT EXISTS erp.product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES erp.product_categories(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 상품
CREATE TABLE IF NOT EXISTS erp.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    spec VARCHAR(100),
    detail_spec VARCHAR(200),
    unit VARCHAR(20) DEFAULT 'EA',
    category_id UUID REFERENCES erp.product_categories(id),
    purchase_price DECIMAL(15,2) DEFAULT 0,
    sale_price DECIMAL(15,2) DEFAULT 0,
    cost_price DECIMAL(15,2) DEFAULT 0,
    vat_type VARCHAR(20) DEFAULT '과세' CHECK (vat_type IN ('과세', '면세', '영세')),
    safety_stock INTEGER DEFAULT 0,
    default_warehouse_id UUID REFERENCES erp.warehouses(id),
    is_active BOOLEAN DEFAULT true,
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 은행계좌
CREATE TABLE IF NOT EXISTS erp.bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_name VARCHAR(50) NOT NULL,
    account_number VARCHAR(30) NOT NULL,
    account_holder VARCHAR(50) NOT NULL,
    account_type VARCHAR(20) DEFAULT '보통예금',
    initial_balance DECIMAL(15,2) DEFAULT 0,
    current_balance DECIMAL(15,2) DEFAULT 0,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(bank_name, account_number)
);

-- 계정과목
CREATE TABLE IF NOT EXISTS erp.account_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) CHECK (account_type IN ('자산', '부채', '자본', '수익', '비용')),
    parent_code VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 2. 매출 관리
-- ==========================================

-- 매출
CREATE TABLE IF NOT EXISTS erp.sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_number VARCHAR(20) UNIQUE NOT NULL,
    sale_date DATE NOT NULL,
    customer_id UUID REFERENCES erp.customers(id) NOT NULL,
    employee_id UUID REFERENCES erp.employees(id),
    warehouse_id UUID REFERENCES erp.warehouses(id),
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    cost_amount DECIMAL(15,2) DEFAULT 0,
    profit_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'completed', 'cancelled')),
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 매출상세
CREATE TABLE IF NOT EXISTS erp.sale_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID REFERENCES erp.sales(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    product_code VARCHAR(30),
    product_name VARCHAR(100),
    spec VARCHAR(100),
    unit VARCHAR(20),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(15,2) DEFAULT 0,
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    cost_price DECIMAL(15,2) DEFAULT 0,
    profit DECIMAL(15,2) DEFAULT 0,
    memo TEXT,
    sort_order INTEGER DEFAULT 0
);

-- ==========================================
-- 3. 매입 관리
-- ==========================================

-- 매입
CREATE TABLE IF NOT EXISTS erp.purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_number VARCHAR(20) UNIQUE NOT NULL,
    purchase_date DATE NOT NULL,
    supplier_id UUID REFERENCES erp.customers(id) NOT NULL,
    employee_id UUID REFERENCES erp.employees(id),
    warehouse_id UUID REFERENCES erp.warehouses(id),
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'completed', 'cancelled')),
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 매입상세
CREATE TABLE IF NOT EXISTS erp.purchase_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_id UUID REFERENCES erp.purchases(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    product_code VARCHAR(30),
    product_name VARCHAR(100),
    spec VARCHAR(100),
    unit VARCHAR(20),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(15,2) DEFAULT 0,
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    memo TEXT,
    sort_order INTEGER DEFAULT 0
);

-- ==========================================
-- 4. 재고 관리
-- ==========================================

-- 재고
CREATE TABLE IF NOT EXISTS erp.inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    warehouse_id UUID REFERENCES erp.warehouses(id) NOT NULL,
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    avg_cost DECIMAL(15,2) DEFAULT 0,
    last_in_date DATE,
    last_out_date DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(product_id, warehouse_id)
);

-- 입출고내역
CREATE TABLE IF NOT EXISTS erp.inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_number VARCHAR(20) UNIQUE NOT NULL,
    movement_date DATE NOT NULL,
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('입고', '출고', '이동', '조정')),
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    from_warehouse_id UUID REFERENCES erp.warehouses(id),
    to_warehouse_id UUID REFERENCES erp.warehouses(id),
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(15,2) DEFAULT 0,
    reference_type VARCHAR(20),
    reference_id UUID,
    memo TEXT,
    created_by UUID REFERENCES erp.employees(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 재고조정
CREATE TABLE IF NOT EXISTS erp.inventory_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adjustment_number VARCHAR(20) UNIQUE NOT NULL,
    adjustment_date DATE NOT NULL,
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    warehouse_id UUID REFERENCES erp.warehouses(id) NOT NULL,
    before_quantity INTEGER NOT NULL,
    after_quantity INTEGER NOT NULL,
    adjustment_quantity INTEGER GENERATED ALWAYS AS (after_quantity - before_quantity) STORED,
    reason TEXT,
    approved_by UUID REFERENCES erp.employees(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 5. 수금/지급 관리
-- ==========================================

-- 수금/지급
CREATE TABLE IF NOT EXISTS erp.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_number VARCHAR(20) UNIQUE NOT NULL,
    payment_date DATE NOT NULL,
    customer_id UUID REFERENCES erp.customers(id) NOT NULL,
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('수금', '지급')),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('현금', '카드', '계좌이체', '어음', '기타')),
    bank_account_id UUID REFERENCES erp.bank_accounts(id),
    amount DECIMAL(15,2) NOT NULL,
    reference_type VARCHAR(20),
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('scheduled', 'pending', 'completed', 'cancelled')),
    due_date DATE,
    completed_date DATE,
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 6. 금융 관리
-- ==========================================

-- 현금출납
CREATE TABLE IF NOT EXISTS erp.cash_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_number VARCHAR(20) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    entry_type VARCHAR(20) NOT NULL CHECK (entry_type IN ('입금', '출금')),
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2),
    account_code VARCHAR(10),
    customer_id UUID REFERENCES erp.customers(id),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 은행거래내역
CREATE TABLE IF NOT EXISTS erp.bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_number VARCHAR(20) UNIQUE NOT NULL,
    bank_account_id UUID REFERENCES erp.bank_accounts(id) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('입금', '출금', '이체')),
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2),
    counterparty VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 7. 어음 관리
-- ==========================================

-- 어음
CREATE TABLE IF NOT EXISTS erp.notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_number VARCHAR(30) UNIQUE NOT NULL,
    note_type VARCHAR(20) NOT NULL CHECK (note_type IN ('받을어음', '지급어음')),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    issuer VARCHAR(100) NOT NULL,
    drawer VARCHAR(100),
    bank_name VARCHAR(50),
    customer_id UUID REFERENCES erp.customers(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'collected', 'dishonored', 'cancelled')),
    collected_date DATE,
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 8. 세금계산서
-- ==========================================

-- 세금계산서
CREATE TABLE IF NOT EXISTS erp.tax_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(30) UNIQUE NOT NULL,
    invoice_type VARCHAR(20) NOT NULL CHECK (invoice_type IN ('매출', '매입')),
    issue_date DATE NOT NULL,
    customer_id UUID REFERENCES erp.customers(id) NOT NULL,
    supply_amount DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    reference_type VARCHAR(20),
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'issued', 'sent', 'confirmed', 'cancelled')),
    nts_confirm_number VARCHAR(50),
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 9. 문서 관리
-- ==========================================

-- 견적서
CREATE TABLE IF NOT EXISTS erp.quotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_number VARCHAR(20) UNIQUE NOT NULL,
    quotation_date DATE NOT NULL,
    valid_until DATE,
    customer_id UUID REFERENCES erp.customers(id) NOT NULL,
    employee_id UUID REFERENCES erp.employees(id),
    project_name VARCHAR(200),
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'expired')),
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 견적서 상세
CREATE TABLE IF NOT EXISTS erp.quotation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_id UUID REFERENCES erp.quotations(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES erp.products(id),
    product_code VARCHAR(30),
    product_name VARCHAR(100) NOT NULL,
    spec VARCHAR(100),
    unit VARCHAR(20),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(15,2) DEFAULT 0,
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    memo TEXT,
    sort_order INTEGER DEFAULT 0
);

-- 발주서
CREATE TABLE IF NOT EXISTS erp.purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(20) UNIQUE NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE,
    supplier_id UUID REFERENCES erp.customers(id) NOT NULL,
    employee_id UUID REFERENCES erp.employees(id),
    warehouse_id UUID REFERENCES erp.warehouses(id),
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'confirmed', 'received', 'cancelled')),
    memo TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 발주서 상세
CREATE TABLE IF NOT EXISTS erp.purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES erp.purchase_orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES erp.products(id) NOT NULL,
    product_code VARCHAR(30),
    product_name VARCHAR(100),
    spec VARCHAR(100),
    unit VARCHAR(20),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(15,2) DEFAULT 0,
    supply_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    memo TEXT,
    sort_order INTEGER DEFAULT 0
);

-- ==========================================
-- 10. 급여 관리
-- ==========================================

-- 수당/공제 항목
CREATE TABLE IF NOT EXISTS erp.payroll_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('수당', '공제')),
    calculation_type VARCHAR(20) DEFAULT '고정' CHECK (calculation_type IN ('고정', '비율', '계산식')),
    is_taxable BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 급여 내역
CREATE TABLE IF NOT EXISTS erp.payroll (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_number VARCHAR(20) UNIQUE NOT NULL,
    employee_id UUID REFERENCES erp.employees(id) NOT NULL,
    pay_year INTEGER NOT NULL,
    pay_month INTEGER NOT NULL CHECK (pay_month BETWEEN 1 AND 12),
    base_salary DECIMAL(15,2) DEFAULT 0,
    total_allowance DECIMAL(15,2) DEFAULT 0,
    total_deduction DECIMAL(15,2) DEFAULT 0,
    net_pay DECIMAL(15,2) DEFAULT 0,
    payment_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'paid')),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(employee_id, pay_year, pay_month)
);

-- 급여 상세
CREATE TABLE IF NOT EXISTS erp.payroll_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_id UUID REFERENCES erp.payroll(id) ON DELETE CASCADE NOT NULL,
    payroll_item_id UUID REFERENCES erp.payroll_items(id) NOT NULL,
    amount DECIMAL(15,2) NOT NULL DEFAULT 0
);

-- ==========================================
-- 11. 회계 관리
-- ==========================================

-- 분개장
CREATE TABLE IF NOT EXISTS erp.journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_number VARCHAR(20) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT,
    reference_type VARCHAR(20),
    reference_id UUID,
    customer_id UUID REFERENCES erp.customers(id),
    total_debit DECIMAL(15,2) DEFAULT 0,
    total_credit DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'posted', 'approved', 'void')),
    created_by UUID REFERENCES erp.employees(id),
    approved_by UUID REFERENCES erp.employees(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 분개 상세
CREATE TABLE IF NOT EXISTS erp.journal_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID REFERENCES erp.journal_entries(id) ON DELETE CASCADE NOT NULL,
    account_code VARCHAR(10) NOT NULL,
    account_name VARCHAR(100),
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    description TEXT,
    sort_order INTEGER DEFAULT 0
);

-- ==========================================
-- 12. 카드 관리
-- ==========================================

-- 카드매출
CREATE TABLE IF NOT EXISTS erp.card_sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_date DATE NOT NULL,
    card_company VARCHAR(50) NOT NULL,
    approval_number VARCHAR(30),
    amount DECIMAL(15,2) NOT NULL,
    fee_rate DECIMAL(5,2) DEFAULT 0,
    fee_amount DECIMAL(15,2) DEFAULT 0,
    net_amount DECIMAL(15,2) DEFAULT 0,
    deposit_date DATE,
    status VARCHAR(20) DEFAULT 'approved' CHECK (status IN ('approved', 'deposited', 'cancelled')),
    reference_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 인덱스
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_erp_customers_code ON erp.customers(code);
CREATE INDEX IF NOT EXISTS idx_erp_customers_name ON erp.customers(name);
CREATE INDEX IF NOT EXISTS idx_erp_customers_type ON erp.customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_erp_products_code ON erp.products(code);
CREATE INDEX IF NOT EXISTS idx_erp_products_name ON erp.products(name);
CREATE INDEX IF NOT EXISTS idx_erp_sales_date ON erp.sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_erp_sales_customer ON erp.sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_erp_purchases_date ON erp.purchases(purchase_date);
CREATE INDEX IF NOT EXISTS idx_erp_purchases_supplier ON erp.purchases(supplier_id);
CREATE INDEX IF NOT EXISTS idx_erp_inventory_product ON erp.inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_erp_payments_date ON erp.payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_erp_payments_customer ON erp.payments(customer_id);
CREATE INDEX IF NOT EXISTS idx_erp_tax_invoices_date ON erp.tax_invoices(issue_date);
CREATE INDEX IF NOT EXISTS idx_erp_tax_invoices_customer ON erp.tax_invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_erp_quotations_date ON erp.quotations(quotation_date);
CREATE INDEX IF NOT EXISTS idx_erp_quotations_customer ON erp.quotations(customer_id);

-- ==========================================
-- 트리거: updated_at 자동 갱신
-- ==========================================

CREATE OR REPLACE FUNCTION erp.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 적용
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'erp'
        AND column_name = 'updated_at'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON erp.%I;
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON erp.%I
            FOR EACH ROW EXECUTE FUNCTION erp.update_updated_at();
        ', t, t, t, t);
    END LOOP;
END $$;

-- ==========================================
-- 시퀀스: 자동 번호 생성
-- ==========================================

CREATE SEQUENCE IF NOT EXISTS erp.sale_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.purchase_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.payment_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.quotation_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.order_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.movement_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.adjustment_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.invoice_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.note_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.entry_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.journal_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.payroll_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.cash_entry_number_seq START 1;
CREATE SEQUENCE IF NOT EXISTS erp.bank_transaction_number_seq START 1;

-- 번호 생성 함수
CREATE OR REPLACE FUNCTION erp.generate_number(prefix TEXT, seq_name TEXT)
RETURNS TEXT AS $$
DECLARE
    next_val INTEGER;
BEGIN
    EXECUTE format('SELECT nextval(''erp.%I'')', seq_name) INTO next_val;
    RETURN prefix || '-' || to_char(CURRENT_DATE, 'YYYY') || '-' || lpad(next_val::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- RLS 정책 (기본)
-- ==========================================

ALTER TABLE erp.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp.sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp.purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp.inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp.payments ENABLE ROW LEVEL SECURITY;

-- 기본 정책: 인증된 사용자 모두 접근 가능
CREATE POLICY erp_customers_policy ON erp.customers FOR ALL USING (true);
CREATE POLICY erp_products_policy ON erp.products FOR ALL USING (true);
CREATE POLICY erp_sales_policy ON erp.sales FOR ALL USING (true);
CREATE POLICY erp_purchases_policy ON erp.purchases FOR ALL USING (true);
CREATE POLICY erp_inventory_policy ON erp.inventory FOR ALL USING (true);
CREATE POLICY erp_payments_policy ON erp.payments FOR ALL USING (true);

-- ==========================================
-- 초기 데이터
-- ==========================================

-- 기본 부서
INSERT INTO erp.departments (code, name) VALUES
('DEPT001', '경영지원팀'),
('DEPT002', '영업팀'),
('DEPT003', '생산팀'),
('DEPT004', '구매팀'),
('DEPT005', '회계팀')
ON CONFLICT (code) DO NOTHING;

-- 기본 창고
INSERT INTO erp.warehouses (code, name, is_default) VALUES
('WH001', '본사 창고', true),
('WH002', '공장 창고', false),
('WH003', '외주 창고', false)
ON CONFLICT (code) DO NOTHING;

-- 기본 계정과목
INSERT INTO erp.account_codes (code, name, account_type) VALUES
('101', '현금', '자산'),
('102', '보통예금', '자산'),
('103', '매출채권', '자산'),
('104', '재고자산', '자산'),
('201', '매입채무', '부채'),
('202', '미지급금', '부채'),
('301', '자본금', '자본'),
('401', '매출', '수익'),
('402', '매출할인', '수익'),
('501', '매입', '비용'),
('502', '급여', '비용'),
('503', '임차료', '비용'),
('504', '소모품비', '비용')
ON CONFLICT (code) DO NOTHING;

-- 기본 급여항목
INSERT INTO erp.payroll_items (code, name, item_type, is_taxable) VALUES
('A001', '기본급', '수당', true),
('A002', '식대', '수당', false),
('A003', '교통비', '수당', false),
('A004', '직책수당', '수당', true),
('A005', '야근수당', '수당', true),
('D001', '국민연금', '공제', false),
('D002', '건강보험', '공제', false),
('D003', '고용보험', '공제', false),
('D004', '소득세', '공제', false),
('D005', '지방소득세', '공제', false)
ON CONFLICT (code) DO NOTHING;

-- ==========================================
-- 완료 확인
-- ==========================================

SELECT 'ERP Schema Migration Complete' as status,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'erp') as table_count;
