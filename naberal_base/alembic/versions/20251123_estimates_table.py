"""Add estimates table for FIX-4 Pipeline results storage

Revision ID: 20251123_estimates_table
Revises: 20251109_add_catalog_name
Create Date: 2025-11-23 12:00:00

This migration adds estimates table for /v1/estimates* endpoints:
- Store estimate request and response as JSONB
- Track total_price and status
- Enable retrieval via GET /v1/estimates/{estimate_id}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251123_estimates_table'
down_revision = '20251109_add_catalog_name'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create estimates table for FIX-4 Pipeline results storage

    Schema Design:
    - id: VARCHAR primary key (EST-YYYYMMDD-NNNN format)
    - customer_name: Client name/organization
    - request_json: JSONB with original EstimateRequest
    - response_json: JSONB with full EstimateResponse
    - total_price: INTEGER for quick sorting/filtering
    - status: COMPLETED (default) or DRAFT
    - Timestamps: created_at, updated_at (always UTC)
    """
    op.create_table(
        'estimates',
        sa.Column('id', sa.String(50), primary_key=True, comment='Estimate ID (EST-YYYYMMDD-NNNN format)'),

        # Estimate Data
        sa.Column('customer_name', sa.Text, nullable=False, comment='Customer/Client name'),
        sa.Column('request_json', postgresql.JSONB, nullable=False, comment='Original EstimateRequest payload'),
        sa.Column('response_json', postgresql.JSONB, nullable=False, comment='Full EstimateResponse with all pipeline results'),
        sa.Column('total_price', sa.BigInteger, nullable=True, comment='Total estimated price (KRW)'),

        # Workflow Status
        sa.Column('status', sa.String(20), nullable=False, server_default='COMPLETED', comment='DRAFT, COMPLETED, or APPROVED'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),

        # Indexes
        sa.Index('ix_estimates_customer_name', 'customer_name'),
        sa.Index('ix_estimates_status', 'status'),
        sa.Index('ix_estimates_created_at', 'created_at'),
        sa.Index('ix_estimates_total_price', 'total_price'),

        # Constraints
        sa.CheckConstraint("status IN ('DRAFT', 'COMPLETED', 'APPROVED')", name='ck_estimates_status'),
        sa.CheckConstraint("id ~ '^EST-[0-9]{8}-[0-9]{4}$'", name='ck_estimates_id_format'),

        schema='kis_beta',
        comment='FIX-4 Pipeline: Estimate storage table with request/response JSONB'
    )

    # Auto-update updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kis_beta.update_estimates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc', now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_estimates_updated_at
        BEFORE UPDATE ON kis_beta.estimates
        FOR EACH ROW
        EXECUTE FUNCTION kis_beta.update_estimates_updated_at();
    """)


def downgrade():
    """
    Remove estimates table

    Rollback safe: All data will be lost.
    RTO: < 10 minutes (no data migration required)
    """
    op.execute("DROP TRIGGER IF EXISTS trigger_estimates_updated_at ON kis_beta.estimates;")
    op.execute("DROP FUNCTION IF EXISTS kis_beta.update_estimates_updated_at();")
    op.drop_table('estimates', schema='kis_beta')
