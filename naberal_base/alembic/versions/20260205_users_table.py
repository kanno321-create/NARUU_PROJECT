"""Add users table for persistent authentication

Revision ID: 20260205_users_table
Revises: 20251201_erp_full_tables
Create Date: 2026-02-05 12:00:00

This migration adds users table for persistent authentication:
- Replace in-memory user storage with PostgreSQL
- Support bcrypt password hashing
- Role-based access control (CEO, MANAGER, STAFF)
- Default CEO account seeding
"""
from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext
import os

# revision identifiers, used by Alembic.
revision = '20260205_users_table'
down_revision = '20251201_erp_full_tables'
branch_labels = None
depends_on = None

# bcrypt context for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade():
    """
    Create users table for persistent authentication

    Schema Design:
    - id: UUID primary key
    - username: Unique username (lowercase)
    - name: Display name
    - hashed_password: bcrypt hashed password
    - role: CEO, MANAGER, STAFF
    - status: ACTIVE, INACTIVE, SUSPENDED
    - Timestamps: created_at, updated_at, last_login
    """
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, comment='User ID (UUID)'),

        # User Identity
        sa.Column('username', sa.String(50), nullable=False, unique=True, comment='Username (lowercase, unique)'),
        sa.Column('name', sa.String(100), nullable=False, comment='Display name'),
        sa.Column('hashed_password', sa.String(255), nullable=False, comment='bcrypt hashed password'),

        # Role & Status
        sa.Column('role', sa.String(20), nullable=False, server_default='staff', comment='User role: ceo, manager, staff'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', comment='User status: active, inactive, suspended'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('last_login', sa.TIMESTAMP(timezone=True), nullable=True, comment='Last login timestamp'),

        # Indexes
        sa.Index('ix_users_username', 'username', unique=True),
        sa.Index('ix_users_role', 'role'),
        sa.Index('ix_users_status', 'status'),

        # Constraints
        sa.CheckConstraint("role IN ('ceo', 'manager', 'staff')", name='ck_users_role'),
        sa.CheckConstraint("status IN ('active', 'inactive', 'suspended')", name='ck_users_status'),

        schema='kis_beta',
        comment='Users table for persistent JWT authentication'
    )

    # Auto-update updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kis_beta.update_users_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc', now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_users_updated_at
        BEFORE UPDATE ON kis_beta.users
        FOR EACH ROW
        EXECUTE FUNCTION kis_beta.update_users_updated_at();
    """)

    # Seed default CEO account
    import uuid
    ceo_id = str(uuid.uuid4())
    default_password = os.getenv("CEO_DEFAULT_PASSWORD", "Ceo@Secure#2024!")
    hashed_password = pwd_context.hash(default_password)

    op.execute(f"""
        INSERT INTO kis_beta.users (id, username, name, hashed_password, role, status)
        VALUES ('{ceo_id}', 'ceo', '대표이사', '{hashed_password}', 'ceo', 'active')
        ON CONFLICT (username) DO NOTHING;
    """)


def downgrade():
    """
    Remove users table

    Rollback safe: All user data will be lost.
    """
    op.execute("DROP TRIGGER IF EXISTS trigger_users_updated_at ON kis_beta.users;")
    op.execute("DROP FUNCTION IF EXISTS kis_beta.update_users_updated_at();")
    op.drop_table('users', schema='kis_beta')
