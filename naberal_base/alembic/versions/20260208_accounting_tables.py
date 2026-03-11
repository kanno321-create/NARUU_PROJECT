"""Add accounting tables: Chart of Accounts + Journal Entries (Double-Entry)

Revision ID: 20260208_accounting_tables
Revises: 20260206_nw_oauth_tokens
Create Date: 2026-02-08 12:00:00

LEAN ERP Phase 1-1: 복식부기 기반 회계 엔진
- erp_accounts: 계정과목 (Chart of Accounts) - 한국 중소제조업 표준
- erp_journal_entries: 분개장 헤더
- erp_journal_items: 분개항목 (차변/대변)
- next_journal_no(): 분개번호 자동 생성 함수
- 기본 계정과목 시드 데이터 (약 40개)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20260208_accounting_tables'
down_revision = '20260206_nw_oauth_tokens'
branch_labels = None
depends_on = None

SCHEMA = 'kis_beta'


def upgrade() -> None:
    # ========== 1. 계정과목 (Chart of Accounts) ==========
    op.create_table(
        'erp_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('account_code', sa.String(20), unique=True, nullable=False, comment='계정코드'),
        sa.Column('account_name', sa.String(100), nullable=False, comment='계정명'),
        sa.Column('account_type', sa.String(20), nullable=False, comment='유형(asset/liability/equity/revenue/expense)'),
        sa.Column('parent_id', UUID(as_uuid=True), comment='상위계정 ID'),
        sa.Column('is_group', sa.Boolean, server_default='false', comment='그룹 계정 여부'),
        sa.Column('balance_direction', sa.String(10), nullable=False, comment='잔액방향(debit/credit)'),
        sa.Column('description', sa.String(255), comment='설명'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_accounts_type', 'erp_accounts', ['account_type'], schema=SCHEMA)
    op.create_index('ix_erp_accounts_parent', 'erp_accounts', ['parent_id'], schema=SCHEMA)
    op.create_index('ix_erp_accounts_code', 'erp_accounts', ['account_code'], schema=SCHEMA)

    # Self-referencing FK for tree structure
    op.create_foreign_key(
        'fk_erp_accounts_parent',
        'erp_accounts', 'erp_accounts',
        ['parent_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # ========== 2. 분개장 (Journal Entries) ==========
    op.create_table(
        'erp_journal_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entry_number', sa.String(20), unique=True, nullable=False, comment='분개번호'),
        sa.Column('entry_date', sa.Date, nullable=False, comment='분개일자'),
        sa.Column('narration', sa.String(500), nullable=False, comment='적요'),
        sa.Column('voucher_id', UUID(as_uuid=True), comment='연결 전표 ID'),
        sa.Column('total_debit', sa.Numeric(15, 2), server_default='0', comment='차변 합계'),
        sa.Column('total_credit', sa.Numeric(15, 2), server_default='0', comment='대변 합계'),
        sa.Column('status', sa.String(15), server_default="'draft'", comment='상태(draft/posted/cancelled)'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )
    op.create_index('ix_erp_journal_entries_date', 'erp_journal_entries', ['entry_date'], schema=SCHEMA)
    op.create_index('ix_erp_journal_entries_voucher', 'erp_journal_entries', ['voucher_id'], schema=SCHEMA)
    op.create_index('ix_erp_journal_entries_status', 'erp_journal_entries', ['status'], schema=SCHEMA)

    # FK to vouchers (optional link)
    op.create_foreign_key(
        'fk_erp_journal_voucher',
        'erp_journal_entries', 'erp_vouchers',
        ['voucher_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # ========== 3. 분개항목 (Journal Items) ==========
    op.create_table(
        'erp_journal_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('journal_entry_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_journal_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey(f'{SCHEMA}.erp_accounts.id'), nullable=False),
        sa.Column('debit', sa.Numeric(15, 2), server_default='0', comment='차변'),
        sa.Column('credit', sa.Numeric(15, 2), server_default='0', comment='대변'),
        sa.Column('customer_id', UUID(as_uuid=True), comment='거래처 ID (선택)'),
        sa.Column('description', sa.String(255), comment='적요'),
        schema=SCHEMA
    )
    op.create_index('ix_erp_journal_items_entry', 'erp_journal_items', ['journal_entry_id'], schema=SCHEMA)
    op.create_index('ix_erp_journal_items_account', 'erp_journal_items', ['account_id'], schema=SCHEMA)

    # FK to customers (optional)
    op.create_foreign_key(
        'fk_erp_journal_items_customer',
        'erp_journal_items', 'erp_customers',
        ['customer_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

    # CHECK: debit >= 0 AND credit >= 0
    op.execute(f"""
        ALTER TABLE {SCHEMA}.erp_journal_items
        ADD CONSTRAINT chk_journal_item_positive
        CHECK (debit >= 0 AND credit >= 0)
    """)

    # CHECK: debit or credit must be > 0 (not both zero)
    op.execute(f"""
        ALTER TABLE {SCHEMA}.erp_journal_items
        ADD CONSTRAINT chk_journal_item_nonzero
        CHECK (debit > 0 OR credit > 0)
    """)

    # CHECK: only one of debit/credit can be > 0
    op.execute(f"""
        ALTER TABLE {SCHEMA}.erp_journal_items
        ADD CONSTRAINT chk_journal_item_exclusive
        CHECK (NOT (debit > 0 AND credit > 0))
    """)

    # ========== 4. 분개번호 자동생성 함수 ==========
    op.execute(f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.next_journal_no()
        RETURNS VARCHAR(20)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_date_str VARCHAR(8);
            v_seq INTEGER;
            v_result VARCHAR(20);
        BEGIN
            v_date_str := to_char(CURRENT_DATE, 'YYYYMMDD');

            SELECT COALESCE(MAX(CAST(SUBSTRING(entry_number FROM 12 FOR 4) AS INTEGER)), 0) + 1
            INTO v_seq
            FROM {SCHEMA}.erp_journal_entries
            WHERE entry_number LIKE 'JE-' || v_date_str || '-%';

            v_result := 'JE-' || v_date_str || '-' || LPAD(v_seq::TEXT, 4, '0');
            RETURN v_result;
        END;
        $$;
    """)

    # ========== 5. 기본 계정과목 시드 데이터 (한국 중소제조업 표준) ==========
    op.execute(f"""
        INSERT INTO {SCHEMA}.erp_accounts (account_code, account_name, account_type, is_group, balance_direction, description) VALUES
        -- 자산 (Assets)
        ('1000', '자산', 'asset', true, 'debit', '자산 총계'),
        ('1010', '현금', 'asset', false, 'debit', '보유 현금'),
        ('1020', '보통예금', 'asset', false, 'debit', '은행 보통예금'),
        ('1030', '당좌예금', 'asset', false, 'debit', '은행 당좌예금'),
        ('1100', '매출채권', 'asset', false, 'debit', '외상매출금 (미수금)'),
        ('1110', '받을어음', 'asset', false, 'debit', '받을어음'),
        ('1200', '상품', 'asset', false, 'debit', '판매용 상품 재고'),
        ('1210', '원재료', 'asset', false, 'debit', '제조용 원재료'),
        ('1220', '제품', 'asset', false, 'debit', '완성 제품 재고'),
        ('1300', '선급금', 'asset', false, 'debit', '선급금'),
        ('1310', '선급비용', 'asset', false, 'debit', '선급비용'),
        ('1400', '부가세대급금', 'asset', false, 'debit', '매입 부가세'),
        ('1500', '비품', 'asset', false, 'debit', '사무용 비품'),
        ('1510', '차량운반구', 'asset', false, 'debit', '차량'),

        -- 부채 (Liabilities)
        ('2000', '부채', 'liability', true, 'credit', '부채 총계'),
        ('2100', '매입채무', 'liability', false, 'credit', '외상매입금 (미지급금)'),
        ('2110', '지급어음', 'liability', false, 'credit', '지급어음'),
        ('2200', '미지급금', 'liability', false, 'credit', '기타 미지급금'),
        ('2210', '미지급비용', 'liability', false, 'credit', '미지급비용'),
        ('2300', '예수금', 'liability', false, 'credit', '원천징수 예수금'),
        ('2400', '부가세예수금', 'liability', false, 'credit', '매출 부가세'),
        ('2500', '단기차입금', 'liability', false, 'credit', '1년 이내 차입금'),
        ('2600', '장기차입금', 'liability', false, 'credit', '1년 초과 차입금'),

        -- 자본 (Equity)
        ('3000', '자본', 'equity', true, 'credit', '자본 총계'),
        ('3100', '자본금', 'equity', false, 'credit', '출자금/자본금'),
        ('3200', '이익잉여금', 'equity', false, 'credit', '누적 이익잉여금'),
        ('3300', '당기순이익', 'equity', false, 'credit', '당기 순이익'),

        -- 수익 (Revenue)
        ('4000', '수익', 'revenue', true, 'credit', '수익 총계'),
        ('4100', '상품매출', 'revenue', false, 'credit', '상품 판매 수익'),
        ('4200', '제품매출', 'revenue', false, 'credit', '제품 판매 수익'),
        ('4300', '용역매출', 'revenue', false, 'credit', '서비스/용역 수익'),
        ('4900', '잡이익', 'revenue', false, 'credit', '기타 영업외 수익'),

        -- 비용 (Expenses)
        ('5000', '비용', 'expense', true, 'credit', '비용 총계'),
        ('5100', '상품매입', 'expense', false, 'debit', '상품 매입 원가'),
        ('5200', '원재료매입', 'expense', false, 'debit', '원재료 매입'),
        ('5300', '급여', 'expense', false, 'debit', '직원 급여'),
        ('5310', '상여금', 'expense', false, 'debit', '상여금'),
        ('5320', '퇴직급여', 'expense', false, 'debit', '퇴직급여 충당'),
        ('5400', '복리후생비', 'expense', false, 'debit', '복리후생비'),
        ('5500', '임차료', 'expense', false, 'debit', '사무실/공장 임대료'),
        ('5510', '수도광열비', 'expense', false, 'debit', '수도/전기/가스'),
        ('5520', '통신비', 'expense', false, 'debit', '전화/인터넷'),
        ('5600', '소모품비', 'expense', false, 'debit', '사무/공장 소모품'),
        ('5610', '수선비', 'expense', false, 'debit', '수리/유지보수'),
        ('5700', '운반비', 'expense', false, 'debit', '배송/운반비'),
        ('5710', '차량유지비', 'expense', false, 'debit', '차량 유지비'),
        ('5800', '접대비', 'expense', false, 'debit', '거래처 접대비'),
        ('5810', '광고선전비', 'expense', false, 'debit', '광고/마케팅'),
        ('5900', '감가상각비', 'expense', false, 'debit', '유형자산 감가상각'),
        ('5910', '세금과공과', 'expense', false, 'debit', '세금/공과금'),
        ('5920', '보험료', 'expense', false, 'debit', '보험료'),
        ('5990', '잡손실', 'expense', false, 'debit', '기타 영업외 비용')
        ON CONFLICT (account_code) DO NOTHING;
    """)

    # Set parent_id for child accounts
    op.execute(f"""
        UPDATE {SCHEMA}.erp_accounts c
        SET parent_id = p.id
        FROM {SCHEMA}.erp_accounts p
        WHERE p.account_code IN ('1000', '2000', '3000', '4000', '5000')
        AND c.account_code LIKE SUBSTRING(p.account_code FROM 1 FOR 1) || '%'
        AND c.account_code != p.account_code
        AND c.parent_id IS NULL;
    """)


def downgrade() -> None:
    op.execute(f"DROP FUNCTION IF EXISTS {SCHEMA}.next_journal_no()")
    op.drop_table('erp_journal_items', schema=SCHEMA)
    op.drop_table('erp_journal_entries', schema=SCHEMA)
    op.drop_table('erp_accounts', schema=SCHEMA)
