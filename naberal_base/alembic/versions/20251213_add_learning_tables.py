"""Add learning tables for AI Self-Learning System

Revision ID: 20251213_learning
Revises: 20251201_erp_full_tables
Create Date: 2025-12-13

Phase XIII - AI Self-Learning System
- estimate_modification_audit: CEO 견적 수정 이력
- learning_patterns: 감지된 패턴 저장
- ceo_preferences: CEO 선호도 프로파일
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20251213_learning'
down_revision = '20251201_erp_full_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create learning tables for AI Self-Learning System."""

    # 1. 견적 수정 감사 테이블 (Estimate Modification Audit)
    op.create_table(
        'estimate_modification_audit',
        sa.Column('modification_id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('estimate_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),  # CEO ID
        sa.Column('before_snapshot', JSONB, nullable=False),  # 수정 전 전체 데이터
        sa.Column('after_snapshot', JSONB, nullable=False),   # 수정 후 전체 데이터
        sa.Column('diff', JSONB, nullable=False),             # JSON Patch format diff
        sa.Column('modified_fields', sa.ARRAY(sa.Text), nullable=False),  # {price, brand, layout}
        sa.Column('reason', sa.Text, nullable=True),          # 수정 사유 (선택)
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column('evidence_hash', sa.String(64), nullable=False),  # SHA256
        schema='estimator'
    )

    # 인덱스 생성 (estimate_modification_audit)
    op.create_index('idx_mod_audit_estimate', 'estimate_modification_audit',
                    ['estimate_id'], schema='estimator')
    op.create_index('idx_mod_audit_user', 'estimate_modification_audit',
                    ['user_id'], schema='estimator')
    op.create_index('idx_mod_audit_timestamp', 'estimate_modification_audit',
                    [sa.text('timestamp DESC')], schema='estimator')

    # 2. 학습된 패턴 테이블 (Learning Patterns)
    op.create_table(
        'learning_patterns',
        sa.Column('pattern_id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('category', sa.String(50), nullable=False),  # PRICE_ADJUSTMENT, BRAND_PREFERENCE, etc.
        sa.Column('condition', JSONB, nullable=False),         # {breaker_af: "100AF", pole: "4P"}
        sa.Column('action', JSONB, nullable=False),            # {use_brand: "LS산전", discount: 0.05}
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.00 ~ 1.00
        sa.Column('occurrences', sa.Integer, nullable=False, server_default='1'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column('evidence_hashes', sa.ARRAY(sa.Text), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name='chk_pattern_confidence'),
        sa.CheckConstraint(
            "category IN ('PRICE_ADJUSTMENT', 'BRAND_PREFERENCE', 'LAYOUT_RULE', 'MATERIAL_SWAP')",
            name='chk_pattern_category'
        ),
        schema='estimator'
    )

    # 인덱스 생성 (learning_patterns)
    op.create_index('idx_pattern_category', 'learning_patterns',
                    ['category'], schema='estimator')
    op.create_index('idx_pattern_confidence', 'learning_patterns',
                    [sa.text('confidence DESC')], schema='estimator')
    op.create_index('idx_pattern_last_seen', 'learning_patterns',
                    [sa.text('last_seen DESC')], schema='estimator')

    # 3. CEO 선호도 테이블 (CEO Preferences)
    op.create_table(
        'ceo_preferences',
        sa.Column('preference_id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(50), nullable=False),   # CEO ID
        sa.Column('category', sa.String(50), nullable=False),  # BRAND, PRICE, LAYOUT, MATERIAL
        sa.Column('key', sa.String(200), nullable=False),      # "preferred_brand_4P_100AF"
        sa.Column('value', JSONB, nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.00 ~ 1.00
        sa.Column('sample_size', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint('user_id', 'category', 'key', name='uq_pref_user_category_key'),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name='chk_pref_confidence'),
        sa.CheckConstraint(
            "category IN ('BRAND', 'PRICE', 'LAYOUT', 'MATERIAL')",
            name='chk_pref_category'
        ),
        schema='estimator'
    )

    # 인덱스 생성 (ceo_preferences)
    op.create_index('idx_pref_user', 'ceo_preferences',
                    ['user_id'], schema='estimator')
    op.create_index('idx_pref_category', 'ceo_preferences',
                    ['category'], schema='estimator')
    op.create_index('idx_pref_confidence', 'ceo_preferences',
                    [sa.text('confidence DESC')], schema='estimator')


def downgrade() -> None:
    """Drop learning tables."""

    # Drop indexes first
    op.drop_index('idx_pref_confidence', table_name='ceo_preferences', schema='estimator')
    op.drop_index('idx_pref_category', table_name='ceo_preferences', schema='estimator')
    op.drop_index('idx_pref_user', table_name='ceo_preferences', schema='estimator')

    op.drop_index('idx_pattern_last_seen', table_name='learning_patterns', schema='estimator')
    op.drop_index('idx_pattern_confidence', table_name='learning_patterns', schema='estimator')
    op.drop_index('idx_pattern_category', table_name='learning_patterns', schema='estimator')

    op.drop_index('idx_mod_audit_timestamp', table_name='estimate_modification_audit', schema='estimator')
    op.drop_index('idx_mod_audit_user', table_name='estimate_modification_audit', schema='estimator')
    op.drop_index('idx_mod_audit_estimate', table_name='estimate_modification_audit', schema='estimator')

    # Drop tables
    op.drop_table('ceo_preferences', schema='estimator')
    op.drop_table('learning_patterns', schema='estimator')
    op.drop_table('estimate_modification_audit', schema='estimator')
