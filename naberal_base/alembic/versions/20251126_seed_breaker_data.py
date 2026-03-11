"""Seed breaker data for integration tests

Revision ID: 20251126_seed_breaker_data
Revises: 20251125_catalog_columns
Create Date: 2025-11-26 12:00:00

Purpose: Add real breaker models required by integration tests
- SBS-404: Sangdo 4P 400AF 표준형 (main breaker)
- SBE-103: Sangdo 3P 100AF 경제형 (main breaker)
- ABN-53: LS 3P 50AF 경제형 (branch breaker)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251126_seed_breaker_data'
down_revision = '20251125_catalog_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed breaker data for CI integration tests"""
    # Insert breaker models used by tests
    op.execute("""
        INSERT INTO shared.catalog_items (
            sku, category, kind, brand, series, model, name,
            spec, width_mm, height_mm, depth_mm, price, search_keywords
        ) VALUES
        -- SBS-404: Sangdo 4P 400AF 표준형 (main breaker for tests)
        (
            'SBS-404', 'breaker', 'MCCB', 'Sangdo', '표준형', 'SBS-404', 'Sangdo SBS-404 4P 400AF',
            '{"poles": 4, "ampere": [300, 350, 400], "frame_AF": 400, "capacity_kA": [35.0], "size_mm": [187, 257, 109], "type": "Standard"}'::jsonb,
            187, 257, 109, 140000, ARRAY['SBS-404', '400AF', '4P', 'Sangdo', '표준형', 'MCCB']
        ),
        -- SBE-103: Sangdo 3P 100AF 경제형 (alternative main breaker)
        (
            'SBE-103', 'breaker', 'MCCB', 'Sangdo', '경제형', 'SBE-103', 'Sangdo SBE-103 3P 100AF',
            '{"poles": 3, "ampere": [60, 75, 100], "frame_AF": 100, "capacity_kA": [14.0], "size_mm": [75, 130, 60], "type": "Economy"}'::jsonb,
            75, 130, 60, 17500, ARRAY['SBE-103', '100AF', '3P', 'Sangdo', '경제형', 'MCCB']
        ),
        -- ABN-53: LS 3P 50AF 경제형 (branch breaker for tests)
        (
            'ABN-53', 'breaker', 'MCCB', 'LS', '경제형', 'ABN-53', 'LS ABN-53 3P 50AF',
            '{"poles": 3, "ampere": [20, 30, 40, 50], "frame_AF": 50, "capacity_kA": [14.0], "size_mm": [75, 130, 60], "type": "Economy"}'::jsonb,
            75, 130, 60, 31900, ARRAY['ABN-53', '50AF', '3P', 'LS', '경제형', 'MCCB']
        ),
        -- ABE-53: LS 3P 50AF 경제형 ELB (optional)
        (
            'ABE-53', 'breaker', 'ELB', 'LS', '경제형', 'ABE-53', 'LS ABE-53 3P 50AF ELB',
            '{"poles": 3, "ampere": [20, 30, 40, 50], "frame_AF": 50, "capacity_kA": [14.0], "size_mm": [75, 130, 60], "type": "Economy"}'::jsonb,
            75, 130, 60, 45000, ARRAY['ABE-53', '50AF', '3P', 'LS', '경제형', 'ELB']
        ),
        -- SBE-102: Sangdo 2P 100AF 경제형 (2P variant)
        (
            'SBE-102', 'breaker', 'MCCB', 'Sangdo', '경제형', 'SBE-102', 'Sangdo SBE-102 2P 100AF',
            '{"poles": 2, "ampere": [60, 75, 100], "frame_AF": 100, "capacity_kA": [14.0], "size_mm": [50, 130, 60], "type": "Economy"}'::jsonb,
            50, 130, 60, 12500, ARRAY['SBE-102', '100AF', '2P', 'Sangdo', '경제형', 'MCCB']
        )
        ON CONFLICT (sku) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove seeded breaker data"""
    op.execute("""
        DELETE FROM shared.catalog_items
        WHERE sku IN ('SBS-404', 'SBE-103', 'ABN-53', 'ABE-53', 'SBE-102');
    """)
