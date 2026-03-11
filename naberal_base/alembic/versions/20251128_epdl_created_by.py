"""Add created_by column to epdl_plans for RLS policies

Revision ID: 20251128_epdl_created_by
Revises: 20251128_estimate_id_sequence
Create Date: 2025-11-28 15:00:00

Phase H+1: RLS created_by column addition
This migration adds the created_by column to epdl_plans table
to enable proper Row-Level Security policies.

The created_by column stores the user's auth.uid() from Supabase Auth JWT.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251128_epdl_created_by'
down_revision = '20251128_estimate_id_sequence'
branch_labels = None
depends_on = None


def upgrade():
    """Add created_by column to epdl_plans table for RLS support."""

    # Add created_by column to epdl_plans
    # This stores the user ID from Supabase Auth (auth.uid()::text)
    op.add_column(
        'epdl_plans',
        sa.Column(
            'created_by',
            sa.String(36),  # UUID string format
            nullable=True,  # Nullable for existing records
            comment='User ID from Supabase Auth (auth.uid())'
        )
    )

    # Create index for efficient RLS policy lookups
    op.create_index(
        'idx_epdl_plans_created_by',
        'epdl_plans',
        ['created_by'],
        postgresql_where=sa.text('created_by IS NOT NULL')
    )

    print("[OK] Added 'created_by' column to epdl_plans table")
    print("[OK] Created index 'idx_epdl_plans_created_by' for RLS lookups")
    print("[INFO] Apply kpew_policies.sql to enable user-based RLS")


def downgrade():
    """Remove created_by column from epdl_plans table."""

    # Drop index first
    op.drop_index('idx_epdl_plans_created_by', 'epdl_plans')

    # Drop column
    op.drop_column('epdl_plans', 'created_by')

    print("[OK] Removed 'created_by' column from epdl_plans table")
