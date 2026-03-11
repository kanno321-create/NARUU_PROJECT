"""create verb_plans table

Revision ID: 20251125_verb_plans
Revises: 20251123_estimates_table
Create Date: 2025-11-25 17:30:00.000000

Purpose: Create verb_plans table for VerbSpec Plan Repository
- Stores VerbSpec lists for estimates
- Separate from epdl_plans (which stores full EPDL plans)
- Required by plan_repo.py
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251125_verb_plans'
down_revision = '20251123_estimates_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create verb_plans table"""
    op.create_table(
        'verb_plans',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('plan_id', sa.String(100), nullable=False, unique=True, index=True, comment='EST-YYYYMMDDHHMMSS'),

        # Plan Content
        sa.Column('specs_json', sa.Text(), nullable=False, comment='VerbSpec list JSON'),
        sa.Column('specs_count', sa.Integer(), nullable=False, server_default='0', comment='Number of specs'),

        # Validation Status
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps (SB-01: TIMESTAMPTZ with UTC)
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),

        sa.PrimaryKeyConstraint('id'),
        schema='kis_beta'
    )

    # Indexes for fast lookup
    op.create_index('idx_verb_plans_plan_id', 'verb_plans', ['plan_id'], unique=True, schema='kis_beta')
    op.create_index('idx_verb_plans_created_at', 'verb_plans', [sa.text('created_at DESC')], schema='kis_beta')
    op.create_index('idx_verb_plans_is_valid', 'verb_plans', ['is_valid'],
                    postgresql_where=sa.text('is_valid = true'), schema='kis_beta')

    # Trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_verb_plans_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc', now());
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER trg_verb_plans_updated_at
        BEFORE UPDATE ON kis_beta.verb_plans
        FOR EACH ROW
        EXECUTE FUNCTION update_verb_plans_updated_at();
    """)


def downgrade() -> None:
    """Drop verb_plans table"""
    op.execute("DROP TRIGGER IF EXISTS trg_verb_plans_updated_at ON kis_beta.verb_plans CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS update_verb_plans_updated_at() CASCADE;")
    op.drop_table('verb_plans', schema='kis_beta')
