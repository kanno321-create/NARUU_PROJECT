"""Add atomic estimate ID sequence generation

Revision ID: 20251128_estimate_id_sequence
Revises: 20251126_seed_breaker_data
Create Date: 2025-11-28 12:00:00

KIS-011: DB 기반 견적 ID 시퀀스 구현
- estimate_id_counters 테이블: 날짜별 카운터 관리
- next_estimate_id() 함수: 원자적 ID 생성 (동시성 안전)
- Format: EST-YYYYMMDD-NNNN (0001~9999)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251128_estimate_id_sequence'
down_revision = '20251126_seed_breaker_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create atomic estimate ID generation system

    Components:
    1. estimate_id_counters table - tracks daily sequence
    2. next_estimate_id() function - atomic ID generation
    """
    # 1. Create counter table for daily sequences
    op.create_table(
        'estimate_id_counters',
        sa.Column('date_key', sa.String(8), primary_key=True,
                  comment='Date in YYYYMMDD format'),
        sa.Column('last_seq', sa.Integer, nullable=False, default=0,
                  comment='Last used sequence number (0-9999)'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("timezone('utc', now())")),
        schema='kis_beta',
        comment='KIS-011: Daily estimate ID sequence counters'
    )

    # 2. Create atomic next_estimate_id function
    op.execute("""
        CREATE OR REPLACE FUNCTION kis_beta.next_estimate_id()
        RETURNS VARCHAR(20)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_date_key VARCHAR(8);
            v_next_seq INTEGER;
            v_estimate_id VARCHAR(20);
        BEGIN
            -- Get today's date in YYYYMMDD format (UTC)
            v_date_key := to_char(timezone('utc', now()), 'YYYYMMDD');

            -- Atomic upsert: insert new date or increment existing
            INSERT INTO kis_beta.estimate_id_counters (date_key, last_seq, updated_at)
            VALUES (v_date_key, 1, timezone('utc', now()))
            ON CONFLICT (date_key)
            DO UPDATE SET
                last_seq = kis_beta.estimate_id_counters.last_seq + 1,
                updated_at = timezone('utc', now())
            RETURNING last_seq INTO v_next_seq;

            -- Check daily limit (9999)
            IF v_next_seq > 9999 THEN
                RAISE EXCEPTION 'Daily estimate limit exceeded (9999) for date %', v_date_key
                    USING ERRCODE = 'P0001';
            END IF;

            -- Format: EST-YYYYMMDD-NNNN
            v_estimate_id := 'EST-' || v_date_key || '-' || LPAD(v_next_seq::TEXT, 4, '0');

            RETURN v_estimate_id;
        END;
        $$;

        COMMENT ON FUNCTION kis_beta.next_estimate_id() IS
            'KIS-011: Generate next atomic estimate ID (EST-YYYYMMDD-NNNN format)';
    """)

    # 3. Grant execute permission
    op.execute("""
        GRANT EXECUTE ON FUNCTION kis_beta.next_estimate_id() TO PUBLIC;
    """)


def downgrade() -> None:
    """
    Remove estimate ID sequence system

    Rollback safe: Counter data will be lost, but existing estimate IDs preserved.
    """
    op.execute("DROP FUNCTION IF EXISTS kis_beta.next_estimate_id();")
    op.drop_table('estimate_id_counters', schema='kis_beta')
