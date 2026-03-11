"""Add K-PEW tables for Plan-First Estimation Workflow

Revision ID: 001_kpew_tables
Revises:
Create Date: 2025-10-04 12:00:00

This migration adds three core tables for K-PEW (KIS Plan-First Estimation Workflow):
1. epdl_plans - Stores EPDL (Estimation Plan DSL) plans from LLM
2. execution_history - Tracks 8-stage execution history
3. evidence_packs - Stores SHA256 evidence and artifacts
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_kpew_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================================
    # EPDL Plans Storage
    # ============================================================================
    op.create_table(
        'epdl_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('estimate_id', sa.String(100), nullable=False, unique=True, comment='EST-20251004120000'),

        # Plan Content
        sa.Column('plan_json', postgresql.JSONB, nullable=False, comment='Full EPDL plan'),
        sa.Column('plan_hash', sa.String(64), nullable=False, comment='SHA256(plan_json) for integrity'),

        # LLM Metadata
        sa.Column('llm_provider', sa.String(50), comment='"claude-3.5-sonnet", "gpt-4"'),
        sa.Column('llm_model', sa.String(100)),
        sa.Column('prompt_tokens', sa.Integer),
        sa.Column('completion_tokens', sa.Integer),
        sa.Column('llm_latency_ms', sa.Integer),

        # Validation Status
        sa.Column('schema_version', sa.String(10), server_default='0.9', comment='EPDL schema version'),
        sa.Column('is_valid', sa.Boolean, server_default='false'),
        sa.Column('validation_errors', postgresql.JSONB, comment='Array of schema validation errors'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),
        sa.Column('validated_at', sa.TIMESTAMP(timezone=True)),

        # Constraints
        sa.CheckConstraint('length(plan_hash) = 64', name='chk_plan_hash_len')
    )

    # Indexes for epdl_plans
    op.create_index('idx_epdl_plans_estimate_id', 'epdl_plans', ['estimate_id'])
    op.create_index('idx_epdl_plans_created_at', 'epdl_plans', [sa.text('created_at DESC')])
    op.create_index('idx_epdl_plans_is_valid', 'epdl_plans', ['is_valid'], postgresql_where=sa.text('is_valid = true'))

    # ============================================================================
    # Execution History (8 Stages)
    # ============================================================================
    op.create_table(
        'execution_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('estimate_id', sa.String(100), nullable=False, comment='FK to epdl_plans.estimate_id'),
        sa.Column('execution_order', sa.Integer, autoincrement=True),

        # Stage Info
        sa.Column('stage_number', sa.Integer, nullable=False, comment='0~7 (K-PEW 8 stages)'),
        sa.Column('stage_name', sa.String(50), nullable=False, comment='"Pre-Validation", "Enclosure", etc'),

        # Status
        sa.Column('status', sa.String(20), nullable=False, comment='"success", "warning", "error", "blocked"'),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('duration_ms', sa.Integer),

        # Errors & Warnings
        sa.Column('error_codes', postgresql.ARRAY(sa.String(20)), comment='["INP-001", "ENC-002"]'),
        sa.Column('blocking_errors', postgresql.JSONB, comment='Array of EstimatorError objects'),
        sa.Column('warnings', postgresql.ARRAY(sa.Text)),

        # Stage Output
        sa.Column('stage_output', postgresql.JSONB, comment='Stage-specific results'),
        sa.Column('quality_gate_passed', sa.Boolean),
        sa.Column('quality_gate_details', postgresql.JSONB),

        # Evidence Reference
        sa.Column('evidence_pack_id', postgresql.UUID(as_uuid=True), comment='FK to evidence_packs.id'),

        # Retry Info
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('retry_reason', sa.Text),

        # Constraints
        sa.CheckConstraint('stage_number BETWEEN 0 AND 7', name='chk_stage_number'),
        sa.CheckConstraint("status IN ('success', 'warning', 'error', 'blocked')", name='chk_status')
    )

    # Indexes for execution_history
    op.create_index('idx_exec_history_estimate_id', 'execution_history', ['estimate_id'])
    op.create_index('idx_exec_history_stage', 'execution_history', ['stage_number'])
    op.create_index('idx_exec_history_status', 'execution_history', ['status'])

    # ============================================================================
    # Evidence Packs (SHA256 + Artifacts)
    # ============================================================================
    op.create_table(
        'evidence_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('estimate_id', sa.String(100), nullable=False),
        sa.Column('stage_number', sa.Integer, nullable=False),

        # Evidence Content
        sa.Column('input_hash', sa.String(64), nullable=False, comment='SHA256(input_json)'),
        sa.Column('output_hash', sa.String(64), nullable=False, comment='SHA256(output_json)'),
        sa.Column('input_json', postgresql.JSONB, nullable=False, comment='Stage input'),
        sa.Column('output_json', postgresql.JSONB, nullable=False, comment='Stage output'),

        # Metrics
        sa.Column('metrics_json', postgresql.JSONB, comment='Performance metrics'),
        sa.Column('validation_json', postgresql.JSONB, comment='Validation results'),

        # Visual Artifacts
        sa.Column('visual_svg_path', sa.Text, comment='Path to SVG diagram'),
        sa.Column('visual_pdf_path', sa.Text, comment='Path to PDF report'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("timezone('utc', now())")),

        # Constraints
        sa.CheckConstraint('length(input_hash) = 64', name='chk_input_hash_len'),
        sa.CheckConstraint('length(output_hash) = 64', name='chk_output_hash_len')
    )

    # Indexes for evidence_packs
    op.create_index('idx_evidence_packs_estimate_id', 'evidence_packs', ['estimate_id'])
    op.create_index('idx_evidence_packs_stage', 'evidence_packs', ['stage_number'])

    # ============================================================================
    # Foreign Key Constraints
    # ============================================================================
    op.create_foreign_key(
        'fk_exec_history_epdl_plan',
        'execution_history', 'epdl_plans',
        ['estimate_id'], ['estimate_id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_exec_history_evidence',
        'execution_history', 'evidence_packs',
        ['evidence_pack_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_evidence_epdl_plan',
        'evidence_packs', 'epdl_plans',
        ['estimate_id'], ['estimate_id'],
        ondelete='CASCADE'
    )

    # ============================================================================
    # Extend existing estimates table (if exists)
    # ============================================================================
    # Note: This is optional and only runs if 'estimates' table exists
    # Adds K-PEW columns to track dual-mode operation (legacy vs plan-first)

    # Check if table exists before altering
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'estimates' in inspector.get_table_names():
        try:
            # Add columns for K-PEW integration
            op.add_column('estimates', sa.Column('kpew_enabled', sa.Boolean, server_default='false', comment='K-PEW mode enabled'))
            op.add_column('estimates', sa.Column('plan_id', postgresql.UUID(as_uuid=True), comment='FK to epdl_plans.id'))
            op.add_column('estimates', sa.Column('execution_mode', sa.String(20), server_default='legacy', comment='"legacy" or "kpew"'))

            # Add foreign key to epdl_plans
            op.create_foreign_key(
                'fk_estimates_plan',
                'estimates', 'epdl_plans',
                ['plan_id'], ['id'],
                ondelete='SET NULL'
            )

            # Add index for K-PEW enabled estimates
            op.create_index(
                'idx_estimates_kpew_enabled',
                'estimates',
                ['kpew_enabled'],
                postgresql_where=sa.text('kpew_enabled = true')
            )

            print("[OK] Extended 'estimates' table with K-PEW columns")
        except Exception as e:
            print(f"[WARN] Could not extend 'estimates' table: {e}")
            print("   This is expected if columns already exist or table structure differs")
    else:
        print("[INFO] 'estimates' table does not exist yet - skipping extension")


def downgrade():
    # ============================================================================
    # Drop K-PEW extensions from estimates (if they exist)
    # ============================================================================
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'estimates' in inspector.get_table_names():
        try:
            op.drop_constraint('fk_estimates_plan', 'estimates', type_='foreignkey')
            op.drop_index('idx_estimates_kpew_enabled', 'estimates')
            op.drop_column('estimates', 'execution_mode')
            op.drop_column('estimates', 'plan_id')
            op.drop_column('estimates', 'kpew_enabled')
            print("[OK] Removed K-PEW columns from 'estimates' table")
        except Exception as e:
            print(f"[WARN] Could not remove K-PEW columns from 'estimates': {e}")

    # ============================================================================
    # Drop foreign keys first (to avoid constraint violations)
    # ============================================================================
    op.drop_constraint('fk_exec_history_epdl_plan', 'execution_history', type_='foreignkey')
    op.drop_constraint('fk_exec_history_evidence', 'execution_history', type_='foreignkey')
    op.drop_constraint('fk_evidence_epdl_plan', 'evidence_packs', type_='foreignkey')

    # ============================================================================
    # Drop tables in reverse order
    # ============================================================================
    op.drop_table('evidence_packs')
    op.drop_table('execution_history')
    op.drop_table('epdl_plans')

    print("[OK] Dropped all K-PEW tables")
