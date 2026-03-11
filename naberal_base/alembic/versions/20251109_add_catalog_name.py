"""Add name column to shared.catalog_items

Revision ID: 20251109_add_catalog_name
Revises: 20251027_quotes_table
Create Date: 2025-11-09 16:00:00

Purpose: Add missing 'name' column to catalog_items table
- Fixes UndefinedColumnError during backend cache initialization
- Uses server_default to handle existing rows
- Schema: shared (per CI error logs: relation "shared.catalog_items")
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251109_add_catalog_name'
down_revision = '20251027_quotes_table'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add name column to shared.catalog_items (idempotent)

    - Column: name (TEXT, NOT NULL, server_default='')
    - server_default ensures existing rows get '' without explicit UPDATE
    - Backend cache initialization requires this column
    - Idempotent: Skips if column already exists
    """
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('catalog_items', schema='shared')]

    if 'name' not in columns:
        op.add_column(
            'catalog_items',
            sa.Column('name', sa.Text(), nullable=False, server_default=''),
            schema='shared'
        )


def downgrade():
    """
    Remove name column from shared.catalog_items

    Rollback safe: Column data will be lost
    """
    op.drop_column('catalog_items', 'name', schema='shared')
