"""create catalog_items table

Revision ID: 20251018_catalog_items
Revises: (latest)
Create Date: 2025-10-18 15:00:00.000000

Purpose: Create catalog_items table for product catalog management
- Supports breakers and enclosures
- Includes dimensions, pricing, and search metadata
- Enables real catalog API testing
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251018_catalog_items'
down_revision = '001_kpew_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create catalog_items table"""
    op.create_table(
        'catalog_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),  # 'breaker' or 'enclosure'
        sa.Column('kind', sa.String(50), nullable=False, index=True),  # MCCB, ELB, etc.

        # Basic info
        sa.Column('brand', sa.String(100), nullable=False, index=True),
        sa.Column('series', sa.String(100), nullable=True),  # 경제형, 표준형
        sa.Column('model', sa.String(100), nullable=False, index=True),

        # Specifications (JSONB for flexibility)
        sa.Column('spec', postgresql.JSONB(), nullable=False, server_default='{}'),
        # Breaker specs: poles, current_a, frame_af, breaking_capacity_ka
        # Enclosure specs: type, material, width_mm, height_mm, depth_mm

        # Dimensions (for all items)
        sa.Column('width_mm', sa.Integer(), nullable=True),
        sa.Column('height_mm', sa.Integer(), nullable=True),
        sa.Column('depth_mm', sa.Integer(), nullable=True),

        # Pricing
        sa.Column('price', sa.Integer(), nullable=False),  # 견적가 (원)

        # Metadata
        sa.Column('search_keywords', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('source_line', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),

        sa.PrimaryKeyConstraint('id'),
        schema='shared'
    )

    # Indexes for fast querying
    op.create_index('idx_catalog_items_category', 'catalog_items', ['category'], schema='shared')
    op.create_index('idx_catalog_items_kind', 'catalog_items', ['kind'], schema='shared')
    op.create_index('idx_catalog_items_brand', 'catalog_items', ['brand'], schema='shared')
    op.create_index('idx_catalog_items_model', 'catalog_items', ['model'], schema='shared')
    op.create_index('idx_catalog_items_sku', 'catalog_items', ['sku'], unique=True, schema='shared')

    # GIN index for search_keywords array
    op.create_index(
        'idx_catalog_items_search_keywords',
        'catalog_items',
        ['search_keywords'],
        postgresql_using='gin',
        schema='shared'
    )

    # Trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_catalog_items_updated_at
        BEFORE UPDATE ON shared.catalog_items
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop catalog_items table"""
    op.drop_table('catalog_items', schema='shared')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
