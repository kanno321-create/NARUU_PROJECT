"""Add is_active, currency, meta columns to shared.catalog_items

Revision ID: 20251125_catalog_columns
Revises: 20251125_verb_plans
Create Date: 2025-11-25 20:30:00

Purpose: Remove hardcoded values from API by adding DB columns
- is_active: Boolean flag for item availability (default true)
- currency: Currency code for pricing (default 'KRW')
- meta: JSONB field for extensible metadata (default '{}')

This eliminates hardcoding in api/routers/catalog.py:
- Line 110, 204: true AS is_active → SELECT is_active
- Line 109, 203: 'KRW' AS currency → SELECT currency
- Line 111, 205: '{}'::jsonb AS meta → SELECT meta
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251125_catalog_columns'
down_revision = '20251125_verb_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add is_active, currency, meta columns to shared.catalog_items (idempotent)

    Safe for existing data:
    - server_default ensures existing rows get default values
    - nullable=False after default application prevents future NULLs
    - Idempotent: Skips if columns/indexes already exist
    """
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('catalog_items', schema='shared')]
    indexes = [idx['name'] for idx in inspector.get_indexes('catalog_items', schema='shared')]

    # Add is_active column (active items by default)
    if 'is_active' not in columns:
        op.add_column(
            'catalog_items',
            sa.Column(
                'is_active',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true'),
                comment='Item availability flag (true=active, false=archived)'
            ),
            schema='shared'
        )

    # Add currency column (KRW by default)
    if 'currency' not in columns:
        op.add_column(
            'catalog_items',
            sa.Column(
                'currency',
                sa.String(length=3),
                nullable=False,
                server_default='KRW',
                comment='Price currency code (ISO 4217: KRW, USD, etc)'
            ),
            schema='shared'
        )

    # Add meta column (empty JSONB by default)
    if 'meta' not in columns:
        op.add_column(
            'catalog_items',
            sa.Column(
                'meta',
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
                comment='Extensible metadata (tags, features, etc)'
            ),
            schema='shared'
        )

    # Create index on is_active for common WHERE clauses
    if 'ix_catalog_items_is_active' not in indexes:
        op.create_index(
            'ix_catalog_items_is_active',
            'catalog_items',
            ['is_active'],
            schema='shared'
        )


def downgrade() -> None:
    """
    Remove is_active, currency, meta columns from shared.catalog_items

    WARNING: Data loss! Column values will be permanently deleted.
    """
    # Drop index first
    op.drop_index('ix_catalog_items_is_active', table_name='catalog_items', schema='shared')

    # Drop columns
    op.drop_column('catalog_items', 'meta', schema='shared')
    op.drop_column('catalog_items', 'currency', schema='shared')
    op.drop_column('catalog_items', 'is_active', schema='shared')
