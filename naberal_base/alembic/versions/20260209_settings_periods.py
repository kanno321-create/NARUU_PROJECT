"""settings and business periods tables

Revision ID: 20260209_settings
Revises: 20260208_accounting_tables
Create Date: 2026-02-09 12:00:00

LEAN ERP Phase 3-B: 환경설정 단순화
- erp_settings: 단일행 JSONB 설정 저장소
- erp_business_periods: 월별 마감 추적
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = '20260209_settings'
down_revision = '20260208_accounting_tables'
branch_labels = None
depends_on = None

SCHEMA = 'kis_beta'


def upgrade() -> None:
    # ========== 1. 환경설정 (Single-Row JSONB Config) ==========
    op.create_table(
        'erp_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('settings', JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"), comment='시스템 설정 JSONB'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        schema=SCHEMA
    )

    # Insert default settings row
    op.execute(f"""
        INSERT INTO {SCHEMA}.erp_settings (settings) VALUES (
            '{{"fiscal_year_start_month": 1, "tax_rate": 10.0, "currency": "KRW", "decimal_places": 0, "voucher_number_format": "{{TYPE}}-{{YYYYMMDD}}-{{SEQ:04d}}", "order_number_format": "PO-{{YYYYMMDD}}-{{SEQ:04d}}", "statement_number_format": "{{TYPE}}-{{YYYYMMDD}}-{{SEQ:04d}}", "cost_method": "moving_average", "allow_negative_stock": false, "low_stock_alert": true}}'::jsonb
        )
    """)

    # ========== 2. 사업장 마감 (Monthly Close Tracking) ==========
    op.create_table(
        'erp_business_periods',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('year', sa.Integer, nullable=False, comment='연도'),
        sa.Column('month', sa.Integer, nullable=False, comment='월'),
        sa.Column('is_closed', sa.Boolean, server_default='false', comment='마감 여부'),
        sa.Column('closed_at', sa.TIMESTAMP(timezone=True), comment='마감일시'),
        sa.Column('closed_by', UUID(as_uuid=True), comment='마감자 ID'),
        sa.Column('notes', sa.Text, comment='비고'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.UniqueConstraint('year', 'month', name='uq_erp_business_periods_year_month'),
        schema=SCHEMA
    )
    op.create_index('ix_erp_business_periods_year', 'erp_business_periods', ['year'], schema=SCHEMA)
    op.create_index('ix_erp_business_periods_closed', 'erp_business_periods', ['is_closed'], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table('erp_business_periods', schema=SCHEMA)
    op.drop_table('erp_settings', schema=SCHEMA)
