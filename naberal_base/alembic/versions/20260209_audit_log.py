"""audit log table

Revision ID: 20260209_audit
Revises: 20260209_settings
Create Date: 2026-02-09 13:00:00

LEAN ERP Phase 5: 감사추적
- erp_audit_log: 모든 전표/설정 변경 기록
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

from alembic import op

revision = '20260209_audit'
down_revision = '20260209_settings'
branch_labels = None
depends_on = None

SCHEMA = 'kis_beta'


def upgrade() -> None:
    op.create_table(
        'erp_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('table_name', sa.String(100), nullable=False, comment='변경 테이블'),
        sa.Column('record_id', sa.String(100), nullable=False, comment='변경 레코드 ID'),
        sa.Column('action', sa.String(20), nullable=False, comment='INSERT/UPDATE/DELETE'),
        sa.Column('changed_by', sa.String(200), comment='변경자'),
        sa.Column('changed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column('old_values', JSONB, comment='변경 전 값'),
        sa.Column('new_values', JSONB, comment='변경 후 값'),
        sa.Column('ip_address', sa.String(45), comment='IP 주소'),
        sa.Column('description', sa.Text, comment='변경 설명'),
        schema=SCHEMA
    )
    op.create_index('ix_erp_audit_log_table', 'erp_audit_log', ['table_name'], schema=SCHEMA)
    op.create_index('ix_erp_audit_log_record', 'erp_audit_log', ['record_id'], schema=SCHEMA)
    op.create_index('ix_erp_audit_log_action', 'erp_audit_log', ['action'], schema=SCHEMA)
    op.create_index('ix_erp_audit_log_changed_at', 'erp_audit_log', ['changed_at'], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table('erp_audit_log', schema=SCHEMA)
