"""Add quotes table for Phase X Quote Lifecycle

Revision ID: 20251027_quotes_table
Revises: 20251018_catalog_items
Create Date: 2025-10-27 13:30:00

This migration adds quotes table for /v1/quotes* endpoints:
- Store quote items, client, terms_ref, totals
- Track approval workflow (status, approved_at, approved_by)
- Evidence hash for audit trail (SHA256)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251027_quotes_table'
down_revision = '20251018_catalog_items'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create quotes table for Phase X Quote Lifecycle & Approval Pack

    Schema Design:
    - id: UUID primary key
    - items_json: JSONB array of quote line items
    - client: Client name/organization
    - terms_ref: Payment terms reference (optional)
    - totals_json: JSONB object with subtotal, discount, vat, total
    - status: DRAFT (default) or APPROVED
    - evidence_hash: SHA256 hash for integrity verification
    - Timestamps: created_at, updated_at (always UTC)
    - Approval metadata: approved_at, approved_by
    """
    op.create_table(
        'quotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Quote Data
        sa.Column('items_json', postgresql.JSONB, nullable=False, comment='Array of quote line items [{sku, quantity, unit_price, uom, discount_tier}, ...]'),
        sa.Column('client', sa.Text, nullable=False, comment='Client name or organization'),
        sa.Column('terms_ref', sa.Text, nullable=True, comment='Payment terms reference (e.g., NET30, NET60)'),
        sa.Column('totals_json', postgresql.JSONB, nullable=False, comment='Calculated totals {subtotal, discount, vat, total, currency}'),

        # Workflow Status
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT', comment='DRAFT or APPROVED'),

        # Evidence & Audit
        sa.Column('evidence_hash', sa.String(64), nullable=False, comment='SHA256 hash of items_json for integrity'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),

        # Approval Metadata
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='Approval timestamp (UTC)'),
        sa.Column('approved_by', sa.String(100), nullable=True, comment='Approver identifier (email or username)'),

        # Indexes
        sa.Index('ix_quotes_status', 'status'),
        sa.Index('ix_quotes_client', 'client'),
        sa.Index('ix_quotes_created_at', 'created_at'),
        sa.Index('ix_quotes_evidence_hash', 'evidence_hash'),

        # Constraints
        sa.CheckConstraint("status IN ('DRAFT', 'APPROVED')", name='ck_quotes_status'),
        sa.CheckConstraint("char_length(evidence_hash) = 64", name='ck_quotes_evidence_hash_length'),

        schema='kis_beta',
        comment='Phase X: Quote lifecycle table with SSOT-based approval workflow'
    )

    # Auto-update updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kis_beta.update_quotes_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc', now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_quotes_updated_at
        BEFORE UPDATE ON kis_beta.quotes
        FOR EACH ROW
        EXECUTE FUNCTION kis_beta.update_quotes_updated_at();
    """)

    # Evidence log: approval audit trail (separate table for compliance)
    op.create_table(
        'quote_approval_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('quote_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References quotes.id'),
        sa.Column('actor', sa.String(100), nullable=False, comment='Approver identifier'),
        sa.Column('action', sa.String(20), nullable=False, comment='APPROVE or REJECT (future)'),
        sa.Column('comment', sa.Text, nullable=True, comment='Optional approval comment'),
        sa.Column('old_status', sa.String(20), nullable=False, comment='Status before action'),
        sa.Column('new_status', sa.String(20), nullable=False, comment='Status after action'),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),

        sa.ForeignKeyConstraint(['quote_id'], ['kis_beta.quotes.id'], name='fk_quote_approval_audit_quote_id'),
        sa.Index('ix_quote_approval_audit_quote_id', 'quote_id'),
        sa.Index('ix_quote_approval_audit_timestamp', 'timestamp'),

        schema='kis_beta',
        comment='Phase X: Quote approval audit log (immutable evidence trail)'
    )


def downgrade():
    """
    Remove quotes table and approval audit log

    Rollback safe: All data will be lost.
    RTO: < 10 minutes (no data migration required)
    """
    op.execute("DROP TRIGGER IF EXISTS trigger_quotes_updated_at ON kis_beta.quotes;")
    op.execute("DROP FUNCTION IF EXISTS kis_beta.update_quotes_updated_at();")
    op.drop_table('quote_approval_audit', schema='kis_beta')
    op.drop_table('quotes', schema='kis_beta')
