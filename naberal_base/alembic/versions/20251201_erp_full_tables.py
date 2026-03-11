"""Create complete ERP tables for EasyPanme feature parity

Revision ID: 20251201_erp_full_tables
Revises: 20251128_epdl_created_by
Create Date: 2025-12-01 12:00:00

ERP 전체 테이블 생성:
- 거래처, 상품, 사원, 부서
- 전표(매출/매입/수금/지급/지출), 전표상세
- 재고, 재고조정, 재고이동
- 은행계좌, 신용카드, 어음
- 기초이월 (재고/잔액/현금)
- 세금계산서
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '20251201_erp_full_tables'
down_revision = '20251128_epdl_created_by'
branch_labels = None
depends_on = None

SCHEMA = 'kis_beta'


def upgrade() -> None:
    # ========== 1. 자사정보 (Company) ==========
    op.create_table(
        'erp_company',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('business_number', sa.String(20), nullable=False, unique=True, comment='사업자등록번호'),
        sa.Column('name', sa.String(100), nullable=False, comment='상호명'),
        sa.Column('ceo', sa.String(50), nullable=False, comment='대표자명'),
        sa.Column('address', sa.String(255)),
        sa.Column('tel', sa.String(20)),
        sa.Column('fax', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('business_type', sa.String(50), comment='업태'),
        sa.Column('business_item', sa.String(100), comment='종목'),
        sa.Column('bank_info', JSONB, comment='계좌정보'),
        sa.Column('logo_path', sa.String(255)),
        sa.Column('stamp_path', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 2. 부서 (Department) ==========
    op.create_table(
        'erp_departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(20), unique=True, comment='부서코드'),
        sa.Column('name', sa.String(50), nullable=False, comment='부서명'),
        sa.Column('parent_id', UUID(as_uuid=True), comment='상위부서'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 3. 사원 (Employee) ==========
    op.create_table(
        'erp_employees',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('emp_no', sa.String(20), unique=True, comment='사원번호'),
        sa.Column('name', sa.String(50), nullable=False, comment='사원명'),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_departments.id')),
        sa.Column('position', sa.String(30), comment='직위'),
        sa.Column('tel', sa.String(20)),
        sa.Column('mobile', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('hire_date', sa.Date),
        sa.Column('resign_date', sa.Date),
        sa.Column('status', sa.String(20), default='active', comment='상태'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 4. 거래처 (Customer) ==========
    op.create_table(
        'erp_customers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(20), unique=True, comment='거래처코드'),
        sa.Column('name', sa.String(100), nullable=False, comment='거래처명'),
        sa.Column('type', sa.String(10), nullable=False, comment='유형(매출/매입/겸용)'),
        sa.Column('business_number', sa.String(20), comment='사업자등록번호'),
        sa.Column('ceo', sa.String(50), comment='대표자명'),
        sa.Column('contact', sa.String(50), comment='담당자'),
        sa.Column('address', sa.String(255)),
        sa.Column('tel', sa.String(20)),
        sa.Column('fax', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('mobile', sa.String(20)),
        sa.Column('credit_limit', sa.Numeric(15, 2), default=0, comment='여신한도'),
        sa.Column('payment_terms', sa.String(50), comment='결제조건'),
        sa.Column('bank_info', JSONB, comment='계좌정보'),
        sa.Column('employee_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_employees.id'), comment='담당사원'),
        sa.Column('memo', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_customers_name', 'erp_customers', ['name'], schema=SCHEMA)
    op.create_index('ix_erp_customers_type', 'erp_customers', ['type'], schema=SCHEMA)

    # ========== 5. 상품 (Product) ==========
    op.create_table(
        'erp_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(50), unique=True, comment='상품코드'),
        sa.Column('name', sa.String(100), nullable=False, comment='상품명'),
        sa.Column('category', sa.String(30), comment='카테고리'),
        sa.Column('unit', sa.String(10), default='EA', comment='단위'),
        sa.Column('spec', sa.String(100), comment='규격'),
        sa.Column('manufacturer', sa.String(50), comment='제조사'),
        sa.Column('unit_cost', sa.Numeric(15, 2), default=0, comment='원가'),
        sa.Column('sale_price', sa.Numeric(15, 2), default=0, comment='판매가'),
        sa.Column('stock_qty', sa.Numeric(15, 2), default=0, comment='재고수량'),
        sa.Column('min_stock', sa.Numeric(15, 2), default=0, comment='최소재고'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_products_name', 'erp_products', ['name'], schema=SCHEMA)
    op.create_index('ix_erp_products_category', 'erp_products', ['category'], schema=SCHEMA)

    # ========== 6. 은행계좌 (BankAccount) ==========
    op.create_table(
        'erp_bank_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('account_no', sa.String(30), nullable=False, comment='계좌번호'),
        sa.Column('bank_name', sa.String(30), nullable=False, comment='은행명'),
        sa.Column('account_name', sa.String(50), comment='계좌명'),
        sa.Column('holder_name', sa.String(50), comment='예금주'),
        sa.Column('balance', sa.Numeric(15, 2), default=0, comment='잔액'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 7. 신용카드 (CreditCard) ==========
    op.create_table(
        'erp_credit_cards',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('card_number', sa.String(20), nullable=False, comment='카드번호(마스킹)'),
        sa.Column('card_name', sa.String(50), comment='카드명'),
        sa.Column('card_company', sa.String(30), comment='카드사'),
        sa.Column('holder_name', sa.String(50), comment='명의자'),
        sa.Column('expire_date', sa.String(7), comment='유효기간(MM/YY)'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 8. 전표 (Voucher) ==========
    op.create_table(
        'erp_vouchers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('voucher_no', sa.String(20), unique=True, nullable=False, comment='전표번호'),
        sa.Column('voucher_type', sa.String(10), nullable=False, comment='유형(sales/purchase/receipt/payment/expense)'),
        sa.Column('voucher_date', sa.Date, nullable=False, comment='전표일자'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id')),
        sa.Column('employee_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_employees.id'), comment='담당자'),
        sa.Column('supply_amount', sa.Numeric(15, 2), default=0, comment='공급가액'),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0, comment='부가세'),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0, comment='합계금액'),
        sa.Column('paid_amount', sa.Numeric(15, 2), default=0, comment='수금/지급액'),
        sa.Column('unpaid_amount', sa.Numeric(15, 2), default=0, comment='미수/미지급액'),
        sa.Column('payment_method', sa.String(20), comment='결제방법'),
        sa.Column('bank_account_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_bank_accounts.id')),
        sa.Column('status', sa.String(15), default='draft', comment='상태(draft/confirmed/cancelled)'),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_vouchers_date', 'erp_vouchers', ['voucher_date'], schema=SCHEMA)
    op.create_index('ix_erp_vouchers_type', 'erp_vouchers', ['voucher_type'], schema=SCHEMA)
    op.create_index('ix_erp_vouchers_customer', 'erp_vouchers', ['customer_id'], schema=SCHEMA)
    op.create_index('ix_erp_vouchers_status', 'erp_vouchers', ['status'], schema=SCHEMA)

    # ========== 9. 전표상세 (VoucherItem) ==========
    op.create_table(
        'erp_voucher_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_vouchers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seq', sa.Integer, default=1, comment='순번'),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_products.id')),
        sa.Column('product_name', sa.String(100), comment='상품명'),
        sa.Column('spec', sa.String(100), comment='규격'),
        sa.Column('unit', sa.String(10), default='EA'),
        sa.Column('quantity', sa.Numeric(15, 2), default=1, comment='수량'),
        sa.Column('unit_price', sa.Numeric(15, 2), default=0, comment='단가'),
        sa.Column('supply_price', sa.Numeric(15, 2), default=0, comment='공급가'),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0, comment='부가세'),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0, comment='합계'),
        sa.Column('memo', sa.String(255)),
        schema=SCHEMA
    )
    op.create_index('ix_erp_voucher_items_voucher', 'erp_voucher_items', ['voucher_id'], schema=SCHEMA)

    # ========== 10. 재고이동 (InventoryMovement) ==========
    op.create_table(
        'erp_inventory_movements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('movement_date', sa.Date, nullable=False, comment='이동일자'),
        sa.Column('movement_type', sa.String(10), nullable=False, comment='유형(in/out/adjust)'),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_products.id'), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 2), nullable=False, comment='수량'),
        sa.Column('unit_cost', sa.Numeric(15, 2), default=0, comment='단가'),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_vouchers.id'), comment='연결전표'),
        sa.Column('reason', sa.String(100), comment='사유'),
        sa.Column('before_qty', sa.Numeric(15, 2), comment='이동전수량'),
        sa.Column('after_qty', sa.Numeric(15, 2), comment='이동후수량'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_inv_mov_date', 'erp_inventory_movements', ['movement_date'], schema=SCHEMA)
    op.create_index('ix_erp_inv_mov_product', 'erp_inventory_movements', ['product_id'], schema=SCHEMA)

    # ========== 11. 재고조정 (StockAdjustment) ==========
    op.create_table(
        'erp_stock_adjustments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('adjustment_no', sa.String(20), unique=True, comment='조정번호'),
        sa.Column('adjustment_date', sa.Date, nullable=False, comment='조정일자'),
        sa.Column('adjustment_type', sa.String(10), nullable=False, comment='유형(increase/decrease/set)'),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_products.id'), nullable=False),
        sa.Column('before_qty', sa.Numeric(15, 2), default=0, comment='조정전수량'),
        sa.Column('adjustment_qty', sa.Numeric(15, 2), nullable=False, comment='조정수량'),
        sa.Column('after_qty', sa.Numeric(15, 2), default=0, comment='조정후수량'),
        sa.Column('reason', sa.String(200), nullable=False, comment='조정사유'),
        sa.Column('employee_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_employees.id')),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 12. 어음 (Note) ==========
    op.create_table(
        'erp_notes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('note_no', sa.String(30), unique=True, comment='어음번호'),
        sa.Column('note_type', sa.String(10), nullable=False, comment='유형(receivable/payable)'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id')),
        sa.Column('issue_date', sa.Date, nullable=False, comment='발행일'),
        sa.Column('maturity_date', sa.Date, nullable=False, comment='만기일'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='금액'),
        sa.Column('bank_name', sa.String(30), comment='은행명'),
        sa.Column('status', sa.String(15), default='active', comment='상태(active/collected/discounted/cancelled)'),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_vouchers.id')),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_notes_maturity', 'erp_notes', ['maturity_date'], schema=SCHEMA)
    op.create_index('ix_erp_notes_type', 'erp_notes', ['note_type'], schema=SCHEMA)

    # ========== 13. 세금계산서 (TaxInvoice) ==========
    op.create_table(
        'erp_tax_invoices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('invoice_no', sa.String(30), unique=True, comment='세금계산서번호'),
        sa.Column('invoice_type', sa.String(10), nullable=False, comment='유형(sales/purchase)'),
        sa.Column('issue_date', sa.Date, nullable=False, comment='작성일자'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id')),
        sa.Column('supply_amount', sa.Numeric(15, 2), default=0, comment='공급가액'),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0, comment='세액'),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0, comment='합계'),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_vouchers.id')),
        sa.Column('nts_confirm_no', sa.String(50), comment='국세청승인번호'),
        sa.Column('status', sa.String(15), default='draft', comment='상태(draft/issued/sent/cancelled)'),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 14. 기초이월 - 재고 (StockCarryover) ==========
    op.create_table(
        'erp_stock_carryovers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fiscal_year', sa.Integer, nullable=False, comment='회계연도'),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_products.id'), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 2), nullable=False, comment='이월수량'),
        sa.Column('unit_cost', sa.Numeric(15, 2), nullable=False, comment='원가'),
        sa.Column('total_value', sa.Numeric(15, 2), nullable=False, comment='이월금액'),
        sa.Column('carryover_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 15. 기초이월 - 잔액 (BalanceCarryover) ==========
    op.create_table(
        'erp_balance_carryovers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fiscal_year', sa.Integer, nullable=False, comment='회계연도'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id'), nullable=False),
        sa.Column('balance_type', sa.String(15), nullable=False, comment='유형(receivable/payable)'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='이월금액'),
        sa.Column('carryover_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 16. 기초이월 - 현금 (CashCarryover) ==========
    op.create_table(
        'erp_cash_carryovers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fiscal_year', sa.Integer, nullable=False, comment='회계연도'),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_bank_accounts.id'), comment='계좌(NULL=현금)'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='이월금액'),
        sa.Column('carryover_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 17. 거래명세서 (Statement) ==========
    op.create_table(
        'erp_statements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('statement_no', sa.String(20), unique=True, comment='거래명세서번호'),
        sa.Column('statement_date', sa.Date, nullable=False, comment='작성일자'),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id'), nullable=False),
        sa.Column('supply_amount', sa.Numeric(15, 2), default=0, comment='공급가액'),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0, comment='부가세'),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0, comment='합계'),
        sa.Column('status', sa.String(15), default='draft', comment='상태'),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 18. 거래명세서-전표 연결 ==========
    op.create_table(
        'erp_statement_vouchers',
        sa.Column('statement_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_statements.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('voucher_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_vouchers.id'), primary_key=True),
        schema=SCHEMA
    )

    # ========== 19. 발주서 (PurchaseOrder) ==========
    op.create_table(
        'erp_purchase_orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_no', sa.String(20), unique=True, comment='발주번호'),
        sa.Column('order_date', sa.Date, nullable=False, comment='발주일자'),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_customers.id'), nullable=False),
        sa.Column('delivery_date', sa.Date, comment='납기일'),
        sa.Column('total_amount', sa.Numeric(15, 2), default=0, comment='합계금액'),
        sa.Column('status', sa.String(15), default='draft', comment='상태(draft/sent/confirmed/received/cancelled)'),
        sa.Column('memo', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # ========== 20. 발주서 상세 ==========
    op.create_table(
        'erp_purchase_order_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_purchase_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seq', sa.Integer, default=1),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_products.id')),
        sa.Column('product_name', sa.String(100)),
        sa.Column('spec', sa.String(100)),
        sa.Column('unit', sa.String(10), default='EA'),
        sa.Column('quantity', sa.Numeric(15, 2), default=1),
        sa.Column('unit_price', sa.Numeric(15, 2), default=0),
        sa.Column('amount', sa.Numeric(15, 2), default=0),
        sa.Column('memo', sa.String(255)),
        schema=SCHEMA
    )

    # ========== 21. 전표번호 시퀀스 함수 ==========
    op.execute(f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.next_voucher_no(p_type VARCHAR)
        RETURNS VARCHAR(20)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_prefix VARCHAR(2);
            v_date_str VARCHAR(8);
            v_seq INTEGER;
            v_result VARCHAR(20);
        BEGIN
            v_prefix := CASE p_type
                WHEN 'sales' THEN 'SL'
                WHEN 'purchase' THEN 'PU'
                WHEN 'receipt' THEN 'RC'
                WHEN 'payment' THEN 'PM'
                WHEN 'expense' THEN 'EX'
                ELSE 'VO'
            END;
            v_date_str := to_char(CURRENT_DATE, 'YYYYMMDD');

            SELECT COALESCE(MAX(CAST(SUBSTRING(voucher_no FROM 12 FOR 4) AS INTEGER)), 0) + 1
            INTO v_seq
            FROM {SCHEMA}.erp_vouchers
            WHERE voucher_no LIKE v_prefix || '-' || v_date_str || '-%';

            v_result := v_prefix || '-' || v_date_str || '-' || LPAD(v_seq::TEXT, 4, '0');
            RETURN v_result;
        END;
        $$;
    """)

    # ========== 22. 재고 업데이트 트리거 ==========
    op.execute(f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.update_product_stock()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF NEW.movement_type = 'in' THEN
                    UPDATE {SCHEMA}.erp_products SET stock_qty = stock_qty + NEW.quantity, updated_at = NOW() WHERE id = NEW.product_id;
                ELSIF NEW.movement_type = 'out' THEN
                    UPDATE {SCHEMA}.erp_products SET stock_qty = stock_qty - NEW.quantity, updated_at = NOW() WHERE id = NEW.product_id;
                ELSIF NEW.movement_type = 'adjust' THEN
                    UPDATE {SCHEMA}.erp_products SET stock_qty = NEW.after_qty, updated_at = NOW() WHERE id = NEW.product_id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER trg_update_stock
        AFTER INSERT ON {SCHEMA}.erp_inventory_movements
        FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.update_product_stock();
    """)


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS trg_update_stock ON {SCHEMA}.erp_inventory_movements")
    op.execute(f"DROP FUNCTION IF EXISTS {SCHEMA}.update_product_stock()")
    op.execute(f"DROP FUNCTION IF EXISTS {SCHEMA}.next_voucher_no(VARCHAR)")

    tables = [
        'erp_purchase_order_items', 'erp_purchase_orders',
        'erp_statement_vouchers', 'erp_statements',
        'erp_cash_carryovers', 'erp_balance_carryovers', 'erp_stock_carryovers',
        'erp_tax_invoices', 'erp_notes',
        'erp_stock_adjustments', 'erp_inventory_movements',
        'erp_voucher_items', 'erp_vouchers',
        'erp_credit_cards', 'erp_bank_accounts',
        'erp_products', 'erp_customers', 'erp_employees', 'erp_departments',
        'erp_company'
    ]
    for table in tables:
        op.drop_table(table, schema=SCHEMA)
